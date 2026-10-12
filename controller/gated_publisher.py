"""P1-ENG-LOOP-001 §3.3：加载时快照、会话帧环与发布最终门。

两件事，合起来保证「追平期间零写入、被拒帧零写入」：

1. **加载时快照（AD3-1 / AC-3 修订 1）**：会话给每段的 `FrameRepository` 注入
   自己的 `image_loader`，对每个帧文件**只读一次字节**，算 JPEG sha、记加载时刻
   （本机 monotonic + Unix），把字节复制进会话帧环，再解码交给跟踪器；元数据取
   **该次 `FrameRepository.load` 返回的 `FrameBundle.metadata` 完整值**，在 bundle
   交给 init/update 之前绑定到同一 `frame_id`/sha。本模块不在 loader 里另读一份
   JSON 冒充 bundle 元数据；重复加载同一帧不覆盖已有信任根，哈希不等即
   `FrameIdentityChanged`。
2. **发布最终门（AR2-1 / AC-3 修订 1）**：`GatedPublisher` 在写桥前重核五项
   （关联帧、盘上 JPEG 哈希、盘上元数据完整值、`latest.json` 帧差、两条截止），
   通过才写并记 `WRITTEN`，否则丢弃并记 `PUBLISH_REJECTED(reason)`。收据文件是
   **唯一**发布证据；`TrackLoop` 运行日志里的 `published_*` 只是调用意图。

`GatedPublisher` 的观测与云台通道从不抛出到 `TrackLoop` 里：门失败只记收据并置
`fatal_reason`，由会话在 `process_available` 返回后 finalize 该段进入 `REINIT_REQUIRED(同名)`。

**机身通道（R-B8 / AC-19）**：`body_command` 只由冻结的 `TrackLoop._body_step` 调用。
`velocity_world` 走门控通道，与同帧合格 `WRITTEN` 观测绑定；没写出时抛
`BodyCommandNotWritten`，让 `_body_step` 走冻结合同的「一次显式 hold 回退」，运行日志因此
如实记下「意图是速度、实际写的是 hold」。`hold`（规划器判停、无观测、规划器异常、写失败回退）
不由图像推出运动，走**无观测安全通道**：不绑帧、不过门，照写并记 `body_safety_hold` 收据；
底层写失败记 `WRITE_FAILED` 收据后原样抛出（回退再失败即由 `_body_step` fail-closed）。
段 finalize 之后两条机身通道都不再写、不记收据（AC-4）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import shutil
import time
from typing import Any, Callable, Mapping, Sequence

from .sensor_protocol import SENSOR_FRAME_SCHEMA_V3, validate_system_monotonic_frame


MANIFEST_SCHEMA = "tethered-frame-manifest/v1"

#: 收据 `outcome` 闭集。`MUTED_DROPPED` 是播种瞬态里被静音丢弃的一次尝试；
#: `WRITE_FAILED` 是机身通道底层写出抛错（R-B8：写入/失败都留收据）；发布证据只数 `WRITTEN`。
RECEIPT_OUTCOMES: tuple[str, ...] = (
    "WRITTEN", "PUBLISH_REJECTED", "MUTED_DROPPED", "WRITE_FAILED",
    # P1-ENG-FASTFIX-001 §3.2（末尾追加，既有成员与位次不变）：捕获模式仅时序类命中时只丢弃本帧发布、不致命。
    "PUBLISH_DROPPED",
)

#: `body_command` 只装与同帧观测绑定的门控速度；`body_safety_hold` 是无观测安全通道上的
#: 显式 hold（不绑帧，`frame_id` 为空），两者分开计，安全 hold 不能冒充门控速度（AC-19）。
#: P1-ENG-CAPTURE-001 IR-9（AC-9 修订 1）：捕获模式预测窗口云台单列 `predicted_look_at`，只在闭集末尾追加
#: （既有成员与位次不变）；分析按该通道计 AC-18/24，不混算观测 `look_at`。
RECEIPT_CHANNELS: tuple[str, ...] = (
    "observation", "look_at", "body_command", "body_safety_hold", "slew_look_at",
    "predicted_look_at",
)

RECEIPTS_FILE = "publish-receipts.jsonl"

#: P1-ENG-LOOP-002 A3：显式 `hold_body()` 收据的 `detail.reason` 闭集（段起点 / 进入转向捕获 / 捕获失败）。
EXPLICIT_HOLD_REASONS: tuple[str, ...] = ("loop_start", "acquiring", "acquire_failed")

# --- P1-ENG-FASTFIX-001 §3.1/§3.2（G1；K1/K2）：捕获模式分级门与按最新帧结算 ------------------------------

#: 收据层原因（不是 `PUBLISH_REJECT_REASONS` 成员）：同帧较早通道已被时序丢弃，其后通道不再求值、不写。
DROPPED_WITH_FRAME = "dropped_with_frame"
#: 分级门命中级别：完整性类任一命中 → 现行致命；只有时序类命中 → 只丢弃本帧发布。
LEVEL_INTEGRITY = "integrity"
LEVEL_TEMPORAL = "temporal"
#: 按最新帧一次结算的结果闭集（§3.2 表）。
SETTLE_PUBLISHED = "PUBLISHED"
SETTLE_DROPPED = "DROPPED"
SETTLE_FATAL = "FATAL"
SETTLE_WRITE_FAILED = "WRITE_FAILED"
SETTLE_NO_ATTEMPT = "NO_ATTEMPT"
SETTLE_OUTCOMES: tuple[str, ...] = (SETTLE_PUBLISHED, SETTLE_DROPPED, SETTLE_FATAL, SETTLE_WRITE_FAILED, SETTLE_NO_ATTEMPT)


class BodyCommandNotWritten(RuntimeError):
    """门控机身速度没有写出（静音、无同帧关联或发布门拒收）；收据已记。"""

    def __init__(self, outcome: str, reason: str | None):
        super().__init__(f"body velocity not written: {outcome}({reason})")
        self.outcome = outcome
        self.reason = reason


class FrameIdentityChanged(ValueError):
    """同一 `frame_id` 的字节或元数据与既有信任根不符（§3.3 加载时快照）。"""

    def __init__(self, frame_id: int, detail: str):
        super().__init__(f"frame {frame_id} identity changed: {detail}")
        self.frame_id = int(frame_id)
        self.detail = detail


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class FrameSnapshot:
    """一帧的信任根：被实际处理的那些字节，加上它们的加载时刻。"""

    frame_id: int
    image_path: Path
    metadata_path: Path
    image_sha256: str
    metadata: Mapping[str, Any]
    capture_monotonic_s: float | None
    capture_unix_s: float | None
    load_monotonic_s: float
    load_unix_s: float
    copy_path: Path
    load_sequence: int


class FrameSnapshotRing:
    """会话帧环：加载时复制字节 + 绑定元数据 + 有界淘汰（可钉住在途查询帧）。

    `expect(frame_id)` 由 `SnapshotRepository` 在每次 `load` 前调用，使 loader
    知道当前读的是哪一帧；`bind` 在 `FrameBundle` 交给跟踪器之前把该次 load 返回的
    元数据完整值绑定到同一帧。
    """

    def __init__(
        self,
        ring_directory: Path,
        *,
        capacity: int,
        decode: Callable[[Path], Any] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        unix: Callable[[], float] = time.time,
    ):
        if capacity <= 0:
            raise ValueError("frame ring capacity must be positive")
        self.directory = Path(ring_directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.capacity = int(capacity)
        self._decode = decode
        self._monotonic = monotonic
        self._unix = unix
        self._snapshots: dict[int, FrameSnapshot] = {}
        self._pinned: set[int] = set()
        self._pending: dict[str, Any] | None = None
        self._expected: int | None = None
        self._sequence = 0
        self.last_loaded_frame_id: int | None = None
        self.identity_conflicts: list[tuple[int, str]] = []
        #: P1-ENG-FASTFIX-001 §3.5（G5）：为 True（只在捕获会话）时 loader 另记同源 monotonic 标记
        #: `m_read0`（读字节前）与 `m_dec`（解码完）；`m_L` 即 `load_monotonic_s`。缺省 False = 现行时钟读取次数不变。
        self.record_marks = False
        self.load_marks: dict[int, dict[str, float | None]] = {}

    # --- 加载路径 ---------------------------------------------------------

    def expect(self, frame_id: int) -> None:
        self._expected = int(frame_id)

    def image_loader(self, path: Path) -> Any:
        """注入给 `FrameRepository` 的 loader：**只读一次字节**，复制，再解码。"""
        if self._expected is None:
            raise RuntimeError("frame ring loader used without expect()")
        frame_id = self._expected
        marks: dict[str, float | None] | None = None
        if self.record_marks:
            marks = {"m_read0": float(self._monotonic()), "m_L": None, "m_dec": None}
            self.load_marks[frame_id] = marks
            while len(self.load_marks) > 8:
                self.load_marks.pop(next(iter(self.load_marks)))
        payload = Path(path).read_bytes()
        digest = sha256_bytes(payload)
        copy_path = self.directory / Path(path).name
        copy_path.write_bytes(payload)
        self._pending = {
            "frame_id": frame_id,
            "image_path": Path(path),
            "image_sha256": digest,
            "copy_path": copy_path,
            "load_monotonic_s": float(self._monotonic()),
            "load_unix_s": float(self._unix()),
        }
        if marks is None:
            return self._decode_bytes(copy_path, payload)
        marks["m_L"] = self._pending["load_monotonic_s"]
        decoded = self._decode_bytes(copy_path, payload)
        marks["m_dec"] = float(self._monotonic())
        return decoded

    def _decode_bytes(self, copy_path: Path, payload: bytes) -> Any:
        if self._decode is not None:
            return self._decode(copy_path)
        from .track_loop import load_cv_image  # 延迟导入：无 cv2 的测试不触发

        return load_cv_image(copy_path)

    def bind(
        self,
        frame_id: int,
        metadata_path: Path,
        metadata: Mapping[str, Any],
    ) -> FrameSnapshot:
        """把该次 load 的元数据完整值绑到刚读的字节上；重复加载不覆盖信任根。"""
        pending = self._pending
        self._pending = None
        self._expected = None
        if pending is None or pending["frame_id"] != int(frame_id):
            raise RuntimeError("frame ring bind without a matching load")
        capture_monotonic = _numeric(metadata.get("capture_monotonic_s"))
        capture_unix = _numeric(metadata.get("capture_unix_s"))
        existing = self._snapshots.get(int(frame_id))
        if existing is not None:
            if existing.image_sha256 != pending["image_sha256"]:
                self.identity_conflicts.append((int(frame_id), "image_sha256"))
                raise FrameIdentityChanged(frame_id, "image bytes differ from snapshot")
            if dict(existing.metadata) != dict(metadata):
                self.identity_conflicts.append((int(frame_id), "metadata"))
                raise FrameIdentityChanged(frame_id, "metadata differs from snapshot")
            # 信任根保持第一次加载的那一份（含其加载时刻）。
            self.last_loaded_frame_id = int(frame_id)
            return existing
        self._sequence += 1
        snapshot = FrameSnapshot(
            frame_id=int(frame_id),
            image_path=pending["image_path"],
            metadata_path=Path(metadata_path),
            image_sha256=pending["image_sha256"],
            metadata=dict(metadata),
            capture_monotonic_s=capture_monotonic,
            capture_unix_s=capture_unix,
            load_monotonic_s=pending["load_monotonic_s"],
            load_unix_s=pending["load_unix_s"],
            copy_path=pending["copy_path"],
            load_sequence=self._sequence,
        )
        self._snapshots[snapshot.frame_id] = snapshot
        self.last_loaded_frame_id = snapshot.frame_id
        self._evict()
        return snapshot

    # --- 查询与钉住 -------------------------------------------------------

    def snapshot(self, frame_id: int) -> FrameSnapshot | None:
        return self._snapshots.get(int(frame_id))

    def latest_snapshot(self) -> FrameSnapshot | None:
        if self.last_loaded_frame_id is None:
            return None
        return self._snapshots.get(self.last_loaded_frame_id)

    def pin(self, frame_id: int) -> None:
        """在途查询的配对帧：淘汰不得动它（AC-8 修订 1）。"""
        self._pinned.add(int(frame_id))

    def unpin(self, frame_id: int) -> None:
        self._pinned.discard(int(frame_id))
        self._evict()

    @property
    def pinned(self) -> frozenset[int]:
        return frozenset(self._pinned)

    def _evict(self) -> None:
        while len(self._snapshots) > self.capacity:
            candidates = [
                snapshot
                for snapshot in self._snapshots.values()
                if snapshot.frame_id not in self._pinned
            ]
            if not candidates:
                return
            oldest = min(candidates, key=lambda item: item.load_sequence)
            self._snapshots.pop(oldest.frame_id, None)
            oldest.copy_path.unlink(missing_ok=True)


def verify_frame_identity(
    frames_directory: Path, snapshot: FrameSnapshot
) -> str | None:
    """重读盘上两个成员文件并与信任根比较。

    返回 `None` 表示身份一致；否则返回 `bundle_missing` / `metadata_invalid` /
    `image_identity_changed`（AC-3 修订 1：缺失、非法 schema/id/时钟、合法但身份
    变化三者分开）。发布最终门与角色 A/B 的返回检查点共用这一个判据。
    """
    frame_id = snapshot.frame_id
    image_path = Path(frames_directory) / f"frame_{frame_id:010d}.jpg"
    metadata_path = Path(frames_directory) / f"frame_{frame_id:010d}.json"
    try:
        disk_digest = sha256_bytes(image_path.read_bytes())
    except OSError:
        return "bundle_missing"
    if disk_digest != snapshot.image_sha256:
        return "image_identity_changed"
    try:
        disk_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "bundle_missing"
    except (json.JSONDecodeError, ValueError, OSError):
        return "metadata_invalid"
    if not isinstance(disk_metadata, dict):
        return "metadata_invalid"
    if disk_metadata.get("schema_version") != SENSOR_FRAME_SCHEMA_V3:
        return "metadata_invalid"
    if _frame_id_of(disk_metadata) != frame_id:
        return "metadata_invalid"
    try:
        validate_system_monotonic_frame(disk_metadata, context=f"frame {frame_id}")
    except ValueError:
        return "metadata_invalid"
    if disk_metadata != dict(snapshot.metadata):
        return "image_identity_changed"
    return None


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


class SnapshotRepository:
    """`FrameRepository` 的会话包装：不改冻结核心，只在 load 前后挂快照。"""

    def __init__(self, repository: Any, ring: FrameSnapshotRing):
        self._repository = repository
        self.ring = ring

    @property
    def runtime(self) -> Path:
        return self._repository.runtime

    @property
    def frames_directory(self) -> Path:
        return self._repository.frames_directory

    def latest_frame_id(self) -> int:
        return self._repository.latest_frame_id()

    def frame_paths(self, frame_id: int) -> tuple[Path, Path]:
        return self._repository.frame_paths(frame_id)

    def dump_frame(self, frame_id: int, destination: Path) -> Path:
        return self._repository.dump_frame(frame_id, destination)

    def load(self, frame_id: int):
        self.ring.expect(frame_id)
        try:
            bundle = self._repository.load(frame_id)
        except BaseException:
            self.ring._pending = None
            self.ring._expected = None
            raise
        self.ring.bind(frame_id, bundle.metadata_path, bundle.metadata)
        return bundle


@dataclass
class PublishReceipt:
    sequence: int
    channel: str
    outcome: str
    frame_id: int | None
    reason: str | None
    track_id: str | None
    at_unix_s: float
    at_monotonic_s: float
    detail: dict[str, Any] = field(default_factory=dict)

    def as_record(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "channel": self.channel,
            "outcome": self.outcome,
            "frame_id": self.frame_id,
            "reason": self.reason,
            "track_id": self.track_id,
            "at_unix_s": self.at_unix_s,
            "at_monotonic_s": self.at_monotonic_s,
            "detail": self.detail,
        }


class GatedPublisher:
    """可静音发布器 + 发布最终门（§3.3）。接口与 `RuntimePublisher` 相同。

    `hold_body` / `set_nadir` **永远透传**（静音只针对由图像推出的观测与控制）。
    """

    def __init__(
        self,
        publisher: Any,
        ring: FrameSnapshotRing,
        *,
        frames_directory: Path,
        receipts_path: Path,
        k_pub: int,
        t_pub_s: float,
        t_stall_s: float,
        track_id: str,
        monotonic: Callable[[], float] = time.monotonic,
        unix: Callable[[], float] = time.time,
        hold_receipts: bool = False,
        classified: bool = False,
        n_drop: int | None = None,
    ):
        self._publisher = publisher
        #: P1-ENG-FASTFIX-001 G1：True（只在捕获模式）= 门控通道改用全量求值的分级门 `_gate_classified`，时序类命中
        #: 只丢弃本帧发布并按最新帧结算 streak；False（缺省，兼容模式与段式路径）= 现行 `_gate` 首命中、首拒即致命。
        self.classified = bool(classified)
        if self.classified and (isinstance(n_drop, bool) or not isinstance(n_drop, int) or n_drop < 1):
            raise ValueError("classified publishing needs n_drop ≥ 1")
        self.n_drop = n_drop
        self.drop_streak = 0
        self._frame_ctx: dict[str, Any] | None = None
        #: 时序升级（`streak ≥ N_drop`）记录；非 None 即本次拆载体属「时序升级」（G2 唯一入口）。
        self.escalation: dict[str, Any] | None = None
        self.last_settle: dict[str, Any] | None = None
        #: P1-ENG-LOOP-002 A3：为 True 时显式 `hold_body()` 补写 `body_safety_hold` 收据（常驻会话开启；
        #: 缺省 False = LOOP-001 段式路径逐字不变）。
        self.hold_receipts = bool(hold_receipts)
        self._ring = ring
        self._frames_directory = Path(frames_directory)
        self._receipts_path = Path(receipts_path)
        self._receipts_path.parent.mkdir(parents=True, exist_ok=True)
        self.k_pub = int(k_pub)
        self.t_pub_s = float(t_pub_s)
        self.t_stall_s = float(t_stall_s)
        self.track_id = track_id
        self._monotonic = monotonic
        self._unix = unix
        self.muted = True
        self.closed = False
        self.accepted_frame_id: int | None = None
        self.last_published_frame_id: int | None = None
        self.fatal_reason: str | None = None
        self.receipts: list[PublishReceipt] = []
        self._sequence = 0
        #: P1-ENG-ACQ-001 §3.7：已用过无观测转向通道的 `designation_id`（每个至多一次）。
        self._slewed_designations: set[int] = set()
        #: R1-2（§3.8、IR-22）：最后一条实际写入 `gimbal_command.json` 的指令点——伺服 `look_at` 与
        #: 转向 `slew_look_at` 共用同一云台通道，只在 `WRITTEN` 时推进；拒绝、静音与写失败不动它。
        self.last_gimbal_point_world_m: tuple[float, float, float] | None = None

    # --- 静音与终止 -------------------------------------------------------

    def mute(self) -> None:
        self.muted = True
        self.accepted_frame_id = None

    def unmute(self) -> None:
        """播种结束、第一次 `process_available()` 之前放行。"""
        self.muted = False

    def finalize(self) -> None:
        """段 finalize：此后任何写入尝试都不再发生，收据零新增（AC-4）。"""
        self.closed = True
        self.muted = True
        self.accepted_frame_id = None

    @property
    def publishing(self) -> bool:
        return not self.closed and not self.muted

    def written_receipts(self) -> list[PublishReceipt]:
        return [item for item in self.receipts if item.outcome == "WRITTEN"]

    # --- 透传通道 ---------------------------------------------------------

    def hold_body(self, reason: str = "loop_start") -> Any:
        """显式 hold：永远透传。`hold_receipts` 开启时沿用 `body_safety_hold` 通道补写收据（通道闭集不变），
        `detail.reason` 取闭集 {`loop_start`, `acquiring`, `acquire_failed`}；`TrackLoop` 段起点的无参调用即
        `loop_start`。写失败同样留 `WRITE_FAILED` 收据后抛出；`finalize` 之后不再新增收据。"""
        if reason not in EXPLICIT_HOLD_REASONS:
            raise ValueError(f"explicit hold reason {reason!r} outside {EXPLICIT_HOLD_REASONS}")
        if not self.hold_receipts or self.closed:
            return self._publisher.hold_body()
        detail = {
            "mode": "hold",
            "reason": reason,
            "explicit": True,
            "accepted_frame_id": self.accepted_frame_id,
        }
        try:
            path = self._publisher.hold_body()
        except Exception as error:
            self._append(
                "body_safety_hold", "WRITE_FAILED", None, "write_failed", self.track_id,
                dict(detail, error=repr(error)),
            )
            raise
        self._append("body_safety_hold", "WRITTEN", None, None, self.track_id, detail)
        return path

    def set_nadir(self) -> Any:
        return self._publisher.set_nadir()

    # --- 门控通道 ---------------------------------------------------------

    def observation(
        self,
        frame_id: int,
        track_id: str,
        box_norm: Sequence[float],
        confidence: float,
    ) -> Any:
        # AC-3 修订 1：每次尝试先清关联，成功写入才重建。
        self.accepted_frame_id = None
        if self.closed:
            return None
        if self.muted:
            self._append(
                "observation", "MUTED_DROPPED", frame_id, None, track_id, {}
            )
            return None
        if self.classified:
            # FASTFIX §3.1/§3.2：全量求值；完整性 → 致命，仅时序 → 本帧 `PUBLISH_DROPPED`（不致命、不写）。
            self._ctx_attempt()
            verdict, reason, detail = self._classified_verdict(int(frame_id))
            if verdict != "PASS":
                self._classified_refusal("observation", verdict, int(frame_id), reason, track_id, detail)
                return None
        else:
            reason, detail = self._gate(int(frame_id))
            if reason is not None:
                self._append(
                    "observation", "PUBLISH_REJECTED", frame_id, reason, track_id, detail
                )
                self._set_fatal(reason)
                return None
        path = self._publisher.observation(frame_id, track_id, box_norm, confidence)
        self.accepted_frame_id = int(frame_id)
        self.last_published_frame_id = int(frame_id)
        self._append("observation", "WRITTEN", frame_id, None, track_id, detail)
        if self._frame_ctx is not None:
            self._frame_ctx["qualified_written"] = True
            self._frame_ctx["observation_written"] = True
        return path

    def look_at(self, point_world_m: Sequence[float]) -> Any:
        before = len(self.receipts)
        path = self._derived("look_at", lambda: self._publisher.look_at(point_world_m))
        if any(item.channel == "look_at" and item.outcome == "WRITTEN" for item in self.receipts[before:]):
            self.last_gimbal_point_world_m = _point3(point_world_m)
        return path

    def predicted_look_at(
        self, frame_id: int, point_world_m: Sequence[float], *, valid_until_frame: int | None = None
    ) -> Any:
        """P1-ENG-CAPTURE-001 C6：预测窗口内的云台 look_at（授权表行 7；无同帧观测）。

        过同一发布最终门（以该处理帧 `frame_id` 重核快照/身份/`latest` 帧差/截止），拒绝即留收据并终止（与观测同
        口径）；写入留 `predicted_look_at` 收据。不建立同帧关联（之后的速度命令仍须同帧观测，否则 `orphan_control`）。"""
        self.accepted_frame_id = None
        if self.closed:
            return None
        detail: dict[str, Any] = {
            "point_world_m": [float(v) for v in point_world_m],
            "valid_until_frame": valid_until_frame,
        }
        if self.muted:
            self._append("predicted_look_at", "MUTED_DROPPED", frame_id, None, self.track_id, detail)
            return None
        if self.classified:
            self._ctx_attempt()
            verdict, reason, gate_detail = self._classified_verdict(int(frame_id))
            detail.update(gate_detail)
            if verdict != "PASS":
                self._classified_refusal("predicted_look_at", verdict, int(frame_id), reason, self.track_id, detail)
                return None
        else:
            reason, gate_detail = self._gate(int(frame_id))
            detail.update(gate_detail)
            if reason is not None:
                self._append("predicted_look_at", "PUBLISH_REJECTED", frame_id, reason, self.track_id, detail)
                self._set_fatal(reason)
                return None
        path = self._publisher.look_at(point_world_m)
        self._append("predicted_look_at", "WRITTEN", frame_id, None, self.track_id, detail)
        self.last_gimbal_point_world_m = _point3(point_world_m)
        if self._frame_ctx is not None:
            self._frame_ctx["qualified_written"] = True
        return path

    def clear_association(self) -> None:
        """P1-ENG-ACQ-001 §3.7：进入转向捕获时撤销同帧关联；此后速度指令无同帧观测即 `orphan_control`。"""
        self.accepted_frame_id = None

    def slew_look_at(self, point_world_m: Sequence[float], designation_id: int) -> Any:
        """§3.7 无同帧观测的转向通道：只在 `designate` 返回 `TRACK_ENDED` 且已由人确认后使用；
        每个 `designation_id` 至多一次（第二次 `PUBLISH_REJECTED(slew_repeated)`，不写桥）；不要求同帧观测、
        不过帧门（世界点来自 k 帧位姿 + 指定框，不是新图像推出的观测）；写入与拒绝都留收据。"""
        if self.closed:
            return None
        detail = {"designation_id": int(designation_id), "point_world_m": [float(v) for v in point_world_m]}
        if self.muted:
            self._append("slew_look_at", "MUTED_DROPPED", None, None, self.track_id, detail)
            return None
        if int(designation_id) in self._slewed_designations:
            self._append("slew_look_at", "PUBLISH_REJECTED", None, "slew_repeated", self.track_id, detail)
            return None
        self._slewed_designations.add(int(designation_id))
        path = self._publisher.look_at(point_world_m)
        self._append("slew_look_at", "WRITTEN", None, None, self.track_id, detail)
        self.last_gimbal_point_world_m = _point3(point_world_m)
        return path

    def body_command(self, command: Any) -> Any:
        """机身命令（只由 `TrackLoop._body_step` 调用）：hold 走安全通道，速度走门控通道。"""
        if getattr(command, "mode", None) == "hold":
            return self._safety_hold(command)
        if self.closed:
            return None
        detail = {
            "mode": getattr(command, "mode", None),
            "reason": getattr(command, "reason", None),
            "velocity_world_mps": list(getattr(command, "velocity_world_mps", ()) or ()),
        }
        path = self._derived(
            "body_command",
            lambda: self._publisher.body_command(command),
            extra=detail,
            record_write_failure=True,
        )
        if path is None:
            last = self.receipts[-1] if self.receipts else None
            raise BodyCommandNotWritten(
                last.outcome if last is not None else "NOT_WRITTEN",
                last.reason if last is not None else None,
            )
        return path

    def _safety_hold(self, command: Any) -> Any:
        """无观测安全通道：显式 hold 不绑帧、不过门；写入与失败都留收据。"""
        if self.closed:
            return None
        detail = {
            "mode": "hold",
            "reason": getattr(command, "reason", None),
            "accepted_frame_id": self.accepted_frame_id,
        }
        try:
            path = self._publisher.body_command(command)
        except Exception as error:
            self._append(
                "body_safety_hold", "WRITE_FAILED", None, "write_failed", self.track_id,
                dict(detail, error=repr(error)),
            )
            if self._frame_ctx is not None:
                self._frame_ctx["write_failed"] = True
            raise
        self._append("body_safety_hold", "WRITTEN", None, None, self.track_id, detail)
        return path

    def _derived(
        self,
        channel: str,
        write: Callable[[], Any],
        *,
        extra: Mapping[str, Any] | None = None,
        record_write_failure: bool = False,
    ) -> Any:
        """衍生控制：必须有同帧关联，且写前沿用该帧重核身份与截止。"""
        if self.closed:
            return None
        extra = dict(extra or {})
        frame_id = self.accepted_frame_id
        ctx = self._frame_ctx
        if self.classified and not self.muted and ctx is not None and ctx["dropped"]:
            # FASTFIX §3.2：同帧较早通道已被时序丢弃 → 其后云台/速度不再求值、不写（不是 orphan_control）。
            drop_detail = dict(extra, partial_after_observation=bool(ctx["observation_written"]))
            self._append(channel, "PUBLISH_DROPPED", ctx["frame_id"], DROPPED_WITH_FRAME, self.track_id, drop_detail)
            return None
        if self.muted or frame_id is None:
            if not self.muted:
                self._append(
                    channel, "PUBLISH_REJECTED", None, "orphan_control", self.track_id, extra
                )
                self._set_fatal("orphan_control")
            else:
                self._append(channel, "MUTED_DROPPED", None, None, self.track_id, extra)
            return None
        if self.classified:
            verdict, reason, detail = self._classified_verdict(frame_id)
            detail = dict(detail, **extra)
            if verdict != "PASS":
                if verdict == "DROP":
                    # 观测已 WRITTEN 后越线：收据不回改、不撤销已写桥文件、不声称跨桥文件原子性。
                    detail["partial_after_observation"] = True
                self._classified_refusal(channel, verdict, frame_id, reason, self.track_id, detail)
                return None
        else:
            reason, detail = self._gate(frame_id)
            detail = dict(detail, **extra)
            if reason is not None:
                # AC-3 修订 1：观测已 WRITTEN 的收据不回改；本次拒绝单独记录并终止段。
                self._append(
                    channel, "PUBLISH_REJECTED", frame_id, reason, self.track_id, detail
                )
                self._set_fatal(reason)
                return None
        if record_write_failure:
            try:
                path = write()
            except Exception as error:
                self._append(
                    channel, "WRITE_FAILED", frame_id, "write_failed", self.track_id,
                    dict(detail, error=repr(error)),
                )
                if self._frame_ctx is not None:
                    self._frame_ctx["write_failed"] = True
                raise
        else:
            path = write()
        self._append(channel, "WRITTEN", frame_id, None, self.track_id, detail)
        return path

    def _set_fatal(self, reason: str) -> None:
        if self.fatal_reason is None:
            self.fatal_reason = reason
        if self._frame_ctx is not None:
            # FASTFIX §3.2：本帧任一致命（完整性命中、真实 orphan_control）→ 帧结算 FATAL（与 streak 无关）。
            self._frame_ctx["fatal"] = True

    # --- FASTFIX §3.1/§3.2：帧上下文、分级门与按最新帧结算 ---------------------------------------

    def begin_frame(self, frame_id: int) -> None:
        """捕获分支在每个本批最新帧处理开始调用（旧帧不开上下文、不发命令、不计 streak）。"""
        self._frame_ctx = {
            "frame_id": int(frame_id),
            "attempted": False,
            "dropped": False,
            "temporal_reasons": [],
            "qualified_written": False,
            "observation_written": False,
            "write_failed": False,
            "fatal": False,
            "gate_evals": [],
        }

    def settle_frame(self, frame_id: int) -> dict[str, Any] | None:
        """最新帧末尾一次结算：FATAL（完整性，与 streak 无关）> WRITE_FAILED（不计不清，含混合降级帧）> DROPPED（+1）>
        PUBLISHED（只它清零）> NO_ATTEMPT（不变）。`streak ≥ N_drop` → 以本帧第一个时序原因名 `_set_fatal` 并记升级。"""
        ctx, self._frame_ctx = self._frame_ctx, None
        if ctx is None or ctx["frame_id"] != int(frame_id):
            return None
        if ctx["fatal"]:
            outcome = SETTLE_FATAL
        elif ctx["write_failed"]:
            # C1-2（AC-3、§3.2）：本帧任一底层写失败（含降级帧的 HOLD 写失败）→ 不计 streak、不清零、不升级；
            # 降级事实另记 `dropped`，写失败照现行上抛 fail-closed。
            outcome = SETTLE_WRITE_FAILED
        elif ctx["dropped"]:
            outcome = SETTLE_DROPPED
            self.drop_streak += 1
        elif ctx["qualified_written"]:
            outcome = SETTLE_PUBLISHED
            self.drop_streak = 0
        else:
            outcome = SETTLE_NO_ATTEMPT
        escalated = False
        if (
            outcome == SETTLE_DROPPED
            and self.n_drop is not None
            and self.drop_streak >= self.n_drop
            and self.fatal_reason is None
        ):
            reason = ctx["temporal_reasons"][0]
            self._set_fatal(reason)
            self.escalation = {"frame_id": int(frame_id), "reason": reason, "streak": self.drop_streak, "n_drop": self.n_drop}
            escalated = True
        settle = {
            "frame_id": int(frame_id),
            "outcome": outcome,
            "streak": self.drop_streak,
            "escalated": escalated,
            "temporal_reasons": list(ctx["temporal_reasons"]),
            "gate_evals": list(ctx["gate_evals"]),
            "attempted": ctx["attempted"],
            "dropped": bool(ctx["dropped"]),
        }
        self.last_settle = settle
        return settle

    def _ctx_attempt(self) -> None:
        if self._frame_ctx is not None:
            self._frame_ctx["attempted"] = True

    def _classified_verdict(self, frame_id: int) -> tuple[str, str | None, dict[str, Any]]:
        """→ (`PASS`/`DROP`/`REJECT`, 原因, detail)。完整性任一命中 → REJECT（原因 = 表序第一个完整性命中）；
        只有时序命中 → DROP（原因 = 第一个时序命中）；`detail.hits` 列全部命中。"""
        hits, detail = self._gate_classified(frame_id)
        detail["hits"] = [dict(hit) for hit in hits]
        if self._frame_ctx is not None and "load_elapsed_s" in detail:
            self._frame_ctx["gate_evals"].append(detail["load_elapsed_s"])
        integrity = [hit for hit in hits if hit["level"] == LEVEL_INTEGRITY]
        if integrity:
            return "REJECT", integrity[0]["reason"], detail
        if hits:
            return "DROP", hits[0]["reason"], detail
        return "PASS", None, detail

    def _classified_refusal(
        self, channel: str, verdict: str, frame_id: int, reason: str | None, track_id: str | None, detail: Mapping[str, Any]
    ) -> None:
        if verdict == "REJECT":
            self._append(channel, "PUBLISH_REJECTED", frame_id, reason, track_id, detail)
            self._set_fatal(reason)  # type: ignore[arg-type]
            return
        self._append(channel, "PUBLISH_DROPPED", frame_id, reason, track_id, detail)
        if self._frame_ctx is not None:
            self._frame_ctx["dropped"] = True
            self._frame_ctx["temporal_reasons"].append(reason)

    def _gate_classified(self, frame_id: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """§3.1 全量求值（不首命中返回）：逐项收集命中；快照缺失、`latest.json` 不可读即刻按完整性结束（后续项无法求值）。
        两条截止与采集年龄用同一次 `monotonic()`/`unix()` 读数（与现行 `_gate` 同在身份与帧差核验之后读取）。"""
        detail: dict[str, Any] = {"frame_id": frame_id}
        hits: list[dict[str, Any]] = []
        snapshot = self._ring.snapshot(frame_id)
        if snapshot is None:  # 步 1
            hits.append({"reason": "bundle_missing", "level": LEVEL_INTEGRITY, "step": "1"})
            return hits, detail
        detail["snapshot_sha256"] = snapshot.image_sha256
        if self._ring.last_loaded_frame_id != frame_id:  # 步 2
            detail["last_loaded_frame_id"] = self._ring.last_loaded_frame_id
            hits.append({"reason": "catchup_stale", "level": LEVEL_TEMPORAL, "step": "2", "stale_by": "not_latest_loaded"})
        identity = verify_frame_identity(self._frames_directory, snapshot)  # 步 3（不因步 2 跳过）
        detail["identity"] = identity or "verified"
        if identity is not None:
            hits.append({"reason": identity, "level": LEVEL_INTEGRITY, "step": "3"})
        try:  # 步 4a
            manifest = json.loads((self._frames_directory / "latest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = None
        latest = manifest.get("frame_id") if isinstance(manifest, dict) and manifest.get("schema_version") == MANIFEST_SCHEMA else None
        if isinstance(latest, bool) or not isinstance(latest, int):
            hits.append({"reason": "bundle_missing", "level": LEVEL_INTEGRITY, "step": "4a"})
            return hits, detail
        detail["latest_frame_id"] = latest
        delta = latest - frame_id
        detail["frame_delta"] = delta
        if delta < 0:  # 步 4b
            hits.append({"reason": "frame_rollback", "level": LEVEL_INTEGRITY, "step": "4b"})
        if delta > self.k_pub:  # 步 4c
            hits.append({"reason": "catchup_stale", "level": LEVEL_TEMPORAL, "step": "4c", "stale_by": "frame_delta"})
        now_monotonic = float(self._monotonic())
        now_unix = float(self._unix())
        elapsed = now_monotonic - snapshot.load_monotonic_s
        detail["load_elapsed_s"] = elapsed
        if elapsed < 0.0:  # 步 5a
            hits.append({"reason": "publish_expired", "level": LEVEL_INTEGRITY, "step": "5a", "expired_by": "negative_elapsed"})
        elif elapsed > self.t_pub_s:  # 步 5b
            hits.append({"reason": "publish_expired", "level": LEVEL_TEMPORAL, "step": "5b", "expired_by": "load_elapsed"})
        capture_unix = snapshot.capture_unix_s
        if capture_unix is None:  # 步 5c
            hits.append({"reason": "metadata_invalid", "level": LEVEL_INTEGRITY, "step": "5c", "capture_unix_missing": True})
            return hits, detail
        age = now_unix - capture_unix
        detail["capture_age_s"] = age
        if age < 0.0:  # 步 5d
            detail["capture_age_negative"] = True
            hits.append({"reason": "metadata_invalid", "level": LEVEL_INTEGRITY, "step": "5d", "capture_age_negative": True})
        elif age > self.t_stall_s:  # 步 5e
            hits.append({"reason": "publish_expired", "level": LEVEL_INTEGRITY, "step": "5e", "expired_by": "capture_age"})
        return hits, detail

    def _append(
        self,
        channel: str,
        outcome: str,
        frame_id: int | None,
        reason: str | None,
        track_id: str | None,
        detail: Mapping[str, Any],
    ) -> None:
        self._sequence += 1
        receipt = PublishReceipt(
            sequence=self._sequence,
            channel=channel,
            outcome=outcome,
            frame_id=None if frame_id is None else int(frame_id),
            reason=reason,
            track_id=track_id,
            at_unix_s=float(self._unix()),
            at_monotonic_s=float(self._monotonic()),
            detail=dict(detail),
        )
        self.receipts.append(receipt)
        with self._receipts_path.open("a", encoding="utf-8") as handle:
            json.dump(receipt.as_record(), handle, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()

    # --- 五项核验 ---------------------------------------------------------

    def _gate(self, frame_id: int) -> tuple[str | None, dict[str, Any]]:
        detail: dict[str, Any] = {"frame_id": frame_id}
        snapshot = self._ring.snapshot(frame_id)
        # ① 快照存在且是最近一次加载的帧。
        if snapshot is None:
            return "bundle_missing", detail
        detail["snapshot_sha256"] = snapshot.image_sha256
        if self._ring.last_loaded_frame_id != frame_id:
            detail["last_loaded_frame_id"] = self._ring.last_loaded_frame_id
            return "catchup_stale", detail
        # ②③ 盘上 JPEG 字节与元数据完整值。
        identity = verify_frame_identity(self._frames_directory, snapshot)
        detail["identity"] = identity or "verified"
        if identity is not None:
            return identity, detail
        # ④ `latest.json` 帧差。
        try:
            manifest = json.loads(
                (self._frames_directory / "latest.json").read_text(encoding="utf-8")
            )
        except FileNotFoundError:
            return "bundle_missing", detail
        except (json.JSONDecodeError, ValueError, OSError):
            return "bundle_missing", detail
        if not isinstance(manifest, dict) or manifest.get("schema_version") != MANIFEST_SCHEMA:
            return "bundle_missing", detail
        latest = manifest.get("frame_id")
        if isinstance(latest, bool) or not isinstance(latest, int):
            return "bundle_missing", detail
        detail["latest_frame_id"] = latest
        delta = latest - frame_id
        detail["frame_delta"] = delta
        if delta < 0:
            return "frame_rollback", detail
        if delta > self.k_pub:
            return "catchup_stale", detail
        # ⑤ 两条截止：本机 monotonic 的处理耗时，与采集时刻的墙钟年龄。
        elapsed = float(self._monotonic()) - snapshot.load_monotonic_s
        detail["load_elapsed_s"] = elapsed
        if elapsed < 0.0 or elapsed > self.t_pub_s:
            return "publish_expired", detail
        capture_unix = snapshot.capture_unix_s
        if capture_unix is None:
            return "metadata_invalid", detail
        age = float(self._unix()) - capture_unix
        detail["capture_age_s"] = age
        if age < 0.0:
            # 未来的采集时刻不是「新鲜」，是坏元数据。
            return "metadata_invalid", detail
        if age > self.t_stall_s:
            return "publish_expired", detail
        return None, detail


def _point3(point_world_m: Sequence[float]) -> tuple[float, float, float]:
    return (float(point_world_m[0]), float(point_world_m[1]), float(point_world_m[2]))


def _frame_id_of(metadata: Mapping[str, Any]) -> int | None:
    value = metadata.get("frame_id")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def copy_frame_bundle(
    frames_directory: Path, frame_id: int, destination: Path
) -> tuple[Path, Path]:
    """诊断用：把一帧的两个成员文件按原字节复制出去（不改原件）。"""
    destination.mkdir(parents=True, exist_ok=True)
    stem = f"frame_{frame_id:010d}"
    image = frames_directory / f"{stem}.jpg"
    metadata = frames_directory / f"{stem}.json"
    image_copy = destination / image.name
    metadata_copy = destination / metadata.name
    shutil.copy2(image, image_copy)
    shutil.copy2(metadata, metadata_copy)
    return image_copy, metadata_copy
