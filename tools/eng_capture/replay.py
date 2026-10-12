"""P1-ENG-CAPTURE-001 AC-17/18/19/27：离线回放、故障注入、合成滚转与保真样帧（Mac mini，CAPTURE:A:1 内）。

输入只限 USER-4A 准入原件（`common.ADMITTED_FRAMES` 的原始帧 jpg/json 与位姿字段、`ADMITTED_TRUTH`）；真值只进本文件
`score_` 前缀函数（AC-16 静态检查）。不读旧会话日志、`frames.jsonl`、RECHARTER 导出或其读数。

子命令：
* `check-input`  —— S-A-INPUT：对准入文件现算 sha256 清单，与 `replay-transfer/SHA256SUMS` 对应行比对；帧旁车
  `frame_id`/`simulation_time_s` 与真值行一致；不符即停（零模型）。
* `fidelity`     —— AC-27 合成滚转保真样帧（零推理）：ω=25 转向中一帧、Θ=120° 保持一帧，叠真值多边形。
* `prepare-roll` —— AC-28 六基预登记计划（零模型）：按 IR-7 固定规则列六个 k 与待人登记的原始 k−1 帧（只给帧号与帧字节 sha）。
* `run`          —— 正式回放（基线臂、新臂、故障注入、合成滚转）。启动前强制：保真确认文件（样帧 sha 现核）、
  AC-17 预登记剧本、AC-28 六基剧本、消耗账本逐维核余额（YOLO 加载/推理帧/墙钟/磁盘）；任一不满足即拒绝启动。

评分口径冻结在 AC-17/18/19 原文（同名提案 §4）；待标定参数依赖的读数一律标「暂定（n=…）」。
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import datetime as _dt
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(REPO_ROOT))

from controller import target_manager as tm  # noqa: E402
from controller.pose_gmc import map_point, pose_homography  # noqa: E402
from tools.eng_capture import ledger as capture_ledger  # noqa: E402
from tools.eng_capture.common import ADMITTED_FRAMES, ADMITTED_ROOT, ADMITTED_SUMS, ADMITTED_TRUTH, OUTPUT_ROOT, PROJECT_ROOT  # noqa: E402

LEDGER = capture_ledger.LEDGER
SPEC = PROJECT_ROOT / "config" / "det-assoc-v1.models.json"
CLICK_SCRIPT_SCHEMA = "p1-eng-capture-001-click-script/v1"
#: AC-28（IR-7 新增）：六基点击预登记计划与剧本。
ROLL_PLAN_SCHEMA = "p1-eng-capture-001-roll-base-plan/v1"
ROLL_CLICK_SCHEMA = "p1-eng-capture-001-roll-click-script/v1"
FIDELITY_SCHEMA = "p1-eng-capture-001-fidelity-confirmation/v1"
WINDOW = (557, 600)
PHENOMENON_WINDOW = (559, 565)
INJECTION_START = 561
INJECTION_GAPS = (1, 2, 4, 6)
ROLL_OMEGAS = (15.0, 20.0, 25.0)
ROLL_THETAS = (60.0, 120.0)
ROLL_WARMUP = 8
ROLL_FRAMES = 16
ROLL_BASES = 6
WIDTH, HEIGHT = 640, 480


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frame_paths(frame_id: int, frames: Path = ADMITTED_FRAMES) -> tuple[Path, Path]:
    stem = f"frame_{int(frame_id):010d}"
    return frames / f"{stem}.jpg", frames / f"{stem}.json"


def admitted_frame_ids(frames: Path = ADMITTED_FRAMES) -> list[int]:
    return sorted(int(p.stem.split("_")[1]) for p in frames.glob("frame_*.jpg"))


# --- S-A-INPUT（零模型） --------------------------------------------------------------


def read_sums(path: Path = ADMITTED_SUMS) -> dict[str, str]:
    sums: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, name = line.partition("  ")
        sums[name.strip()] = digest.strip()
    return sums


def score_truth_rows(path: Path = ADMITTED_TRUTH) -> dict[int, dict[str, Any]]:
    """真值行（只供评分与开跑前对齐核对）：frame_id → 行。"""
    rows: dict[int, dict[str, Any]] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[int(row["frame_id"])] = row
    return rows


def score_input_alignment(frames: Path, truth_path: Path) -> list[str]:
    """帧旁车 `frame_id`/`simulation_time_s` 与真值行逐帧一致（不读真值位置字段）。"""
    problems: list[str] = []
    truth = score_truth_rows(truth_path)
    ids = admitted_frame_ids(frames)
    if sorted(truth) != ids:
        problems.append(f"truth frame ids {len(truth)} differ from admitted frames {len(ids)}")
    for frame_id in ids:
        metadata = json.loads(frame_paths(frame_id, frames)[1].read_text(encoding="utf-8"))
        row = truth.get(frame_id)
        if metadata.get("frame_id") != frame_id:
            problems.append(f"frame {frame_id}: sidecar frame_id {metadata.get('frame_id')}")
        if row is None or row.get("simulation_time_s") != metadata.get("simulation_time_s"):
            problems.append(f"frame {frame_id}: simulation_time_s mismatch")
    return problems


def check_input(frames: Path = ADMITTED_FRAMES, truth_path: Path = ADMITTED_TRUTH, sums_path: Path = ADMITTED_SUMS) -> dict[str, Any]:
    """S-A-INPUT：现算 sha256 清单并与 SHA256SUMS 对应行比对 + 帧时刻对齐；返回报告（`ok` 为 False 即 STOP）。"""
    sums = read_sums(sums_path)
    listing: list[dict[str, Any]] = []
    mismatches: list[str] = []
    files = [p for frame_id in admitted_frame_ids(frames) for p in frame_paths(frame_id, frames)] + [Path(truth_path)]
    for path in files:
        relative = str(Path(path).resolve().relative_to(PROJECT_ROOT))
        digest = sha256_file(path)
        expected = sums.get(relative)
        listing.append({"path": relative, "sha256": digest, "bytes": Path(path).stat().st_size, "sums_match": digest == expected})
        if digest != expected:
            mismatches.append(relative)
    alignment = score_input_alignment(frames, truth_path)
    return {
        "check": "S-A-INPUT",
        "files": len(listing),
        "frames": len(admitted_frame_ids(frames)),
        "sha_mismatches": mismatches,
        "alignment_problems": alignment,
        "ok": not mismatches and not alignment,
        "listing": listing,
    }


# --- 合成滚转（AC-19；保真 AC-27） ------------------------------------------------------


def quaternion_multiply(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float, float]:
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def rolled_metadata(metadata: Mapping[str, Any], roll_deg: float) -> dict[str, Any]:
    """相机绕自身前向轴（光轴）滚转 `roll_deg`：q′ = q ⊗ q_z(θ)；right/up 随之转、forward 不变。"""
    half = math.radians(roll_deg) / 2.0
    rotated = quaternion_multiply(metadata["camera_rotation_xyzw"], (0.0, 0.0, math.sin(half), math.cos(half)))
    out = dict(metadata)
    out["camera_rotation_xyzw"] = list(rotated)
    from controller.pose_gmc import rotation_matrix  # noqa: PLC0415

    r = rotation_matrix(out)
    out["camera_right_world"] = [r[0][0], r[1][0], r[2][0]]
    out["camera_up_world"] = [r[0][1], r[1][1], r[2][1]]
    out["camera_forward_world"] = [r[0][2], r[1][2], r[2][2]]
    out["synthetic_roll_deg"] = float(roll_deg)
    return out


def roll_schedule(omega_deg: float, theta_deg: float, sign: int, frames: int = ROLL_FRAMES) -> list[float]:
    """第 i 个变换帧（1..frames）的累计滚转角 = sign·min(ω·i, Θ)：先以 ω°/帧转到 Θ，再保持。"""
    return [sign * min(omega_deg * i, theta_deg) for i in range(1, frames + 1)]


def roll_homography(metadata: Mapping[str, Any], roll_deg: float) -> Any:
    """原帧像素 → 滚转后像素（纯旋转单应，与会话 `pose_gmc` 同一约定）。"""
    return pose_homography(metadata, rolled_metadata(metadata, roll_deg))


def warp_image(image: Any, homography: Any) -> Any:
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    matrix = np.asarray(homography, dtype=float)
    return cv2.warpPerspective(image, matrix, (image.shape[1], image.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def polygon_area(points: Sequence[Sequence[float]]) -> float:
    area = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def clip_polygon(points: Sequence[Sequence[float]], width: float = WIDTH, height: float = HEIGHT) -> list[tuple[float, float]]:
    """Sutherland–Hodgman 裁到画幅矩形。"""
    def clip(polygon, inside, intersect):
        out = []
        for i in range(len(polygon)):
            current, previous = polygon[i], polygon[i - 1]
            if inside(current):
                if not inside(previous):
                    out.append(intersect(previous, current))
                out.append(current)
            elif inside(previous):
                out.append(intersect(previous, current))
        return out

    def at_x(x0):
        return lambda p, q: (x0, p[1] + (q[1] - p[1]) * (x0 - p[0]) / (q[0] - p[0]))

    def at_y(y0):
        return lambda p, q: (p[0] + (q[0] - p[0]) * (y0 - p[1]) / (q[1] - p[1]), y0)

    polygon = [tuple(p) for p in points]
    for inside, intersect in (
        (lambda p: p[0] >= 0.0, at_x(0.0)),
        (lambda p: p[0] <= width, at_x(width)),
        (lambda p: p[1] >= 0.0, at_y(0.0)),
        (lambda p: p[1] <= height, at_y(height)),
    ):
        if not polygon:
            break
        polygon = clip(polygon, inside, intersect)
    return polygon  # type: ignore[return-value]


def point_in_polygon(x: float, y: float, polygon: Sequence[Sequence[float]]) -> bool:
    inside = False
    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-300) + x1:
            inside = not inside
    return inside


def score_truth_geometry(truth_row: Mapping[str, Any], homography: Any | None) -> dict[str, Any] | None:
    """AC-19 冻结口径：真值中心 = H(真值框中心)，真值多边形 = 四角经 H；画内面积 < 50% → 删失。"""
    if not truth_row.get("truth_box_available"):
        return None
    x, y = float(truth_row["truth_box_x"]) * WIDTH, float(truth_row["truth_box_y"]) * HEIGHT
    w, h = float(truth_row["truth_box_width"]) * WIDTH, float(truth_row["truth_box_height"]) * HEIGHT
    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    center = (x + w / 2.0, y + h / 2.0)
    if homography is not None:
        mapped = [map_point(homography, cx, cy) for cx, cy in corners]
        if any(p is None for p in mapped):
            return {"censored": True, "polygon": None, "center": None}
        corners = [tuple(p) for p in mapped]  # type: ignore[misc]
        center = map_point(homography, *center)  # type: ignore[assignment]
    area = polygon_area(corners)
    inside = polygon_area(clip_polygon(corners)) if area > 0 else 0.0
    return {"censored": area <= 0.0 or inside < 0.5 * area, "polygon": [list(p) for p in corners], "center": list(center) if center else None}


def score_roll_bases(truth: Mapping[int, Mapping[str, Any]], frame_ids: Sequence[int], count: int = ROLL_BASES) -> list[int]:
    """真值基选取（IR-7 固定规则，首次正式回放前冻结；真值在此只用于基帧选择）：基帧 k 需 [k−8, k+15] 每帧都在
    准入帧内（连续完整），且 [k−8, k] 每帧真值框可得、全在画内；合格 k 升序后取第 ⌊(i+1)·n/7⌋ 位（零基，i=0…5）。
    返回按规则取到的位次（可能少于 `count` 或含重复）；是否恰为 `count` 个互异基帧由 `roll_base_plan` 判定，
    不足不得缩分母。"""
    ids = set(int(v) for v in frame_ids)
    eligible = []
    for k in sorted(ids):
        if any(f not in ids for f in range(k - ROLL_WARMUP, k + ROLL_FRAMES)):
            continue
        ok = True
        for f in range(k - ROLL_WARMUP, k + 1):
            row = truth.get(f) or {}
            geometry = score_truth_geometry(row, None) if row else None
            if geometry is None or geometry["censored"]:
                ok = False
                break
            x, y = float(row["truth_box_x"]), float(row["truth_box_y"])
            if x < 0 or y < 0 or x + float(row["truth_box_width"]) > 1 or y + float(row["truth_box_height"]) > 1:
                ok = False
                break
        if ok:
            eligible.append(k)
    n = len(eligible)
    if n == 0:
        return []
    return [eligible[(i + 1) * n // (count + 1)] for i in range(count) if (i + 1) * n // (count + 1) < n]


class RollBaseError(RuntimeError):
    """基帧规则未得恰六个互异基帧（AC-28/IR-7：不缩分母、不自动补）。"""


def roll_base_plan(truth: Mapping[int, Mapping[str, Any]], frame_ids: Sequence[int], frames: Path = ADMITTED_FRAMES) -> dict[str, Any]:
    """AC-28 六基预登记计划（零模型）：按固定规则列六个 k 与各自待登记的原始 k−1 帧（帧字节 sha 现算）。
    计划只含帧号与帧字节 sha，不含真值、模型框或评分；点击页只据此显示原图。"""
    bases = score_roll_bases(truth, frame_ids)
    if len(bases) != ROLL_BASES or len(set(bases)) != ROLL_BASES:
        raise RollBaseError(f"roll base rule yielded {bases}; exactly {ROLL_BASES} distinct bases are required")
    entries = []
    for k in bases:
        image, _meta = frame_paths(k - 1, frames)
        entries.append({"base_k": int(k), "frame_id": int(k - 1), "image_sha256": sha256_file(image)})
    return {
        "schema_version": ROLL_PLAN_SCHEMA,
        "rule": "IR-7：[k−8,k+15] 准入连续完整；[k−8,k] 真值框可得且全在画内；合格 k 升序取第 floor((i+1)·n/7) 位，i=0…5，恰六个互异",
        "warmup_frames": ROLL_WARMUP,
        "transform_frames": ROLL_FRAMES,
        "bases": entries,
    }


def draw_polygon_sample(image: Any, polygon: Sequence[Sequence[float]] | None, label: str, destination: Path) -> None:
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    canvas = image.copy()
    if polygon:
        cv2.polylines(canvas, [np.asarray(polygon, dtype=np.int32).reshape(-1, 1, 2)], True, (0, 255, 0), 2)
    cv2.putText(canvas, label, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA)
    destination.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(destination), canvas)


def make_fidelity_samples(output: Path, *, frames: Path = ADMITTED_FRAMES, truth_path: Path = ADMITTED_TRUTH) -> list[dict[str, Any]]:
    """AC-27 合成滚转保真（零推理）：第 1 个真值基上 ω=25 转向中一帧与 Θ=120° 保持一帧（各正负号），叠真值多边形。"""
    import cv2  # noqa: PLC0415

    truth = score_truth_rows(truth_path)
    bases = score_roll_bases(truth, admitted_frame_ids(frames))
    if not bases:
        raise RuntimeError("no eligible roll base frame")
    base = bases[0]
    samples = []
    for sign in (1, -1):
        schedule = roll_schedule(25.0, 120.0, sign)
        for index, tag in ((2, "omega25-turning"), (ROLL_FRAMES, "theta120-hold")):
            frame_id = base + index - 1
            image = cv2.imread(str(frame_paths(frame_id, frames)[0]))
            metadata = json.loads(frame_paths(frame_id, frames)[1].read_text(encoding="utf-8"))
            roll = schedule[index - 1]
            homography = roll_homography(metadata, roll)
            warped = warp_image(image, homography)
            geometry = score_truth_geometry(truth[frame_id], homography)
            name = f"roll-fidelity-{tag}-{'pos' if sign > 0 else 'neg'}-base{base:04d}-frame{frame_id:04d}.png"
            draw_polygon_sample(warped, geometry["polygon"] if geometry else None,
                                f"base {base} frame {frame_id} roll {roll:+.0f}deg  truth polygon (green)", output / name)
            samples.append({"path": str(output / name), "base": base, "frame_id": frame_id, "roll_deg": roll, "tag": tag,
                            "censored": None if geometry is None else geometry["censored"]})
    (output / "roll-fidelity-samples.json").write_text(json.dumps({"bases": bases, "samples": samples}, indent=1) + "\n", encoding="utf-8")
    return samples


# --- 检测缓存与模型包装 ------------------------------------------------------------------


@dataclass
class CacheFrame:
    """缓存帧替身：只带画幅与缓存键（`DetAssocTracker.step` 只读 `shape` 并把它转交模型包装/关联器）。"""

    key: tuple[Any, ...]
    shape: tuple[int, int, int] = (HEIGHT, WIDTH, 3)


class CountingModel:
    """真实模型的一次性加载包装：`loads` 计底层加载次数，`inferences` 计实际提交推理帧。

    C1-5（逐帧共账）：给了 `counter`（`ledger.InflightCounter`）时，每帧在交给模型**之前**原子落盘 +1——中途崩溃/退出
    不丢已提交帧、失败不返还；越过每候选/整批上限的那一帧在推理前拒绝。给了 `deadline_monotonic` 时，超过回放墙钟上限
    （每次 ≤ 30 min）即在下一帧推理前拒绝（S-A-BUDGET）。"""

    def __init__(self, loader: Callable[[Path], Any], *, counter: Any | None = None, deadline_monotonic: float | None = None,
                 clock: Callable[[], float] = time.monotonic):
        self._loader = loader
        self._model: Any = None
        self.counter = counter
        self.deadline_monotonic = deadline_monotonic
        self._clock = clock
        self.loads = 0
        self.inferences = 0

    def load(self, weights_path: Path) -> "CountingModel":
        if self._model is None:
            self.loads += 1
            self._model = self._loader(weights_path)
        return self

    def predict(self, source: Any, **kwargs: Any) -> Any:
        if self.deadline_monotonic is not None and self._clock() > self.deadline_monotonic:
            raise capture_ledger.LedgerRefused("S-A-BUDGET: replay wall clock limit reached; no further inference")
        if self.counter is not None:
            self.counter.add(1)  # 提交前落盘（失败不返还）
        self.inferences += 1
        return self._model.predict(source=source, **kwargs)


class CachedOrLiveModel:
    """缓存帧直接返回缓存检测（零推理）；其余帧交真实/替身模型推理并按缓存键写回。"""

    def __init__(self, cache: dict[tuple[Any, ...], list[list[float]]], live: Any | None, boxes_factory: Callable[[list[list[float]]], Any]):
        self.cache = cache
        self.live = live
        self.boxes_factory = boxes_factory
        self.hits = 0

    def predict(self, source: Any, **kwargs: Any) -> Any:
        if isinstance(source, CacheFrame):
            self.hits += 1
            rows = self.cache.get(source.key)
            if rows is None:
                raise KeyError(f"detection cache miss {source.key}")
            return [_Result(self.boxes_factory(rows))]
        if self.live is None:
            raise RuntimeError("live inference requested without a model")
        return self.live.predict(source=source, **kwargs)


class _Result:
    def __init__(self, boxes: Any):
        self.boxes = boxes


def library_boxes(rows: list[list[float]]) -> Any:
    import torch  # noqa: PLC0415
    from ultralytics.engine.results import Boxes  # noqa: PLC0415

    tensor = torch.tensor(rows, dtype=torch.float32) if rows else torch.zeros((0, 6), dtype=torch.float32)
    return Boxes(tensor, orig_shape=(HEIGHT, WIDTH))


def boxes_rows(boxes: Any) -> list[list[float]]:
    data = getattr(boxes, "data", None)
    rows = data.tolist() if data is not None and hasattr(data, "tolist") else list(getattr(boxes, "rows", []))
    return [[float(v) for v in row[:6]] for row in rows]


@dataclass
class ReplayFrame:
    frame_id: int
    image: Any
    metadata: dict[str, Any]
    image_sha256: str


# --- 新臂（unify_vehicle + pose-center + 目标管理器） ----------------------------------------


@dataclass
class NewArmTrace:
    frames: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)


def run_new_arm(
    frames: Iterable[ReplayFrame],
    *,
    model_loader: Callable[[Path], Any],
    params: tm.CaptureParams,
    config_sha256: str,
    clicks: Sequence[Mapping[str, Any]] = (),
    inputs_path: Path | None = None,
    tracker_factory: Callable[..., Any] | None = None,
    association_exclusion: Callable[[int], set[int]] | None = None,
    ground_plane_y_m: float = 0.2,
) -> NewArmTrace:
    """逐帧 `step` → 本帧待处理的点击（§3.3 ①，提交帧 = 本帧）→ `on_frame(newest=True)`（②–⑤）；记录信念、绑定与效果。

    C1-3 / RR-1：替换请求先于本帧授权处理，同一帧的状态、episode、版本与发出的效果一致（不再另存 `pre_click`）。

    `association_exclusion(frame_id)` 返回本帧禁止参与库关联的键（故障注入「强制对目标开新轨迹」，只在工具里）。"""
    from controller.det_assoc_tracker import DetAssocTracker  # noqa: PLC0415

    tracker = (tracker_factory or DetAssocTracker)(
        spec_path=SPEC, device="cpu", model_loader=model_loader, mode="resident",
        class_policy="unify_vehicle", gmc_source="pose-center", history_view="capture",
    )
    manager = tm.TargetManager(params, mode="capture", config_sha256=config_sha256, inputs=tm.InputsLog(inputs_path),
                               ground_plane_y_m=ground_plane_y_m)
    manager.attach_port(tracker.core)
    by_frame: dict[int, list[Mapping[str, Any]]] = {}
    for click in clicks:
        by_frame.setdefault(int(click["frame_id"]), []).append(click)
    trace = NewArmTrace()
    for frame in frames:
        excluded: set[int] = set()
        if association_exclusion is not None:
            excluded = set(association_exclusion(frame.frame_id))
            _install_exclusion(tracker, excluded)
        tracker.step(frame.image, frame.frame_id, frame.metadata)
        entry = tracker.history(frame.frame_id)
        clicks_done = []
        for click in by_frame.get(frame.frame_id, []):
            # ① 替换请求：本帧已入历史、尚未授权；提交帧（历史头）= 本帧。
            word, commit, _info = manager.click(
                request_id=str(click.get("label") or f"click-{frame.frame_id}"), x_px=float(click["x_px"]), y_px=float(click["y_px"]),
                frame_id=frame.frame_id, image_sha256=frame.image_sha256, actual_image_sha256=frame.image_sha256,
                history=tracker.core.history, head_frame_id=frame.frame_id, ended_ids=tracker.core.ended_ids,
            )
            clicks_done.append({"label": click.get("label"), "result": word, "accepted": bool(commit and commit.accepted)})
        outcome = manager.on_frame(entry, newest=True)
        record = _new_arm_record(frame.frame_id, manager, entry, outcome)
        if clicks_done:
            record["clicks"] = clicks_done
        if association_exclusion is not None:
            record["exclusion"] = _exclusion_record(entry, excluded)
        trace.frames.append(record)
    trace.events = list(manager.events)
    return trace


def _install_exclusion(tracker: Any, excluded: set[int]) -> None:
    """故障注入「强制对目标开新轨迹」（IR-8，只在工具内）：本帧禁止 `excluded` 键参与**全部**能匹配它的库关联阶段——
    首轮与未确认轮经 `get_dists`，低置信度第二轮（库内直接调 `matching.iou_distance`）经 `_second_association`
    包装；被排除行代价置 1.0（高于各轮阈值）。不改冻结关联器参数、不改 controller 关联规则、不调 follow；
    原键照常走库内 predict/补偿/mark_lost，prior 仍在。空集 = 不排除（注入退出）。"""
    associator = tracker.associator
    if associator is None:
        return
    associator.capture_excluded = set(int(v) for v in excluded)
    if getattr(associator, "_capture_exclusion_installed", False):
        return
    import numpy as np  # noqa: PLC0415
    from ultralytics.trackers.utils import matching  # noqa: PLC0415

    def mask(dists, tracks):  # noqa: ANN001
        if not associator.capture_excluded or not len(tracks):
            return dists
        dists = np.array(dists, dtype=float, copy=True)
        for row, track in enumerate(tracks):
            if int(track.track_id) in associator.capture_excluded and dists.shape[1]:
                dists[row, :] = 1.0
        return dists

    original_get_dists = associator.get_dists

    def get_dists(tracks, detections):  # noqa: ANN001
        return mask(original_get_dists(tracks, detections), tracks)

    original_second = associator._second_association  # noqa: SLF001

    def second_association(strack_pool, u_track, detections_second, activated, refind, lost):  # noqa: ANN001
        library_iou = matching.iou_distance

        def iou_distance(atracks, btracks):  # noqa: ANN001
            return mask(library_iou(atracks, btracks), atracks)

        matching.iou_distance = iou_distance
        try:
            return original_second(strack_pool, u_track, detections_second, activated, refind, lost)
        finally:
            matching.iou_distance = library_iou

    associator.get_dists = get_dists
    associator._second_association = second_association  # noqa: SLF001
    associator._capture_exclusion_installed = True


def _exclusion_record(entry: Any, excluded: set[int]) -> dict[str, Any]:
    """注入诊断（不读真值）：本帧被排除键、全部库键的状态与匹配检测索引、被排除键同帧 prior 是否在。"""
    return {
        "excluded": sorted(excluded),
        "rows": {str(row.track_id): {"state": row.state, "matched_det_index": row.matched_det_index} for row in entry.tracks},
        "excluded_prior_present": {str(k): (entry.prior(k) is not None and entry.prior(k).valid) for k in sorted(excluded)},
    }


def force_new_track_report(trace: "NewArmTrace", unperturbed: "NewArmTrace", *, start: int, frames: int) -> dict[str, Any]:
    """IR-8 完成含义核实（不读真值）：注入帧内原绑定键无量测更新（lost 且同帧 prior 在），原键在未扰动臂匹配的那条检测
    被另一库键接走，且该新键随后成为活跃 tracked；否则只记「注入未成立」，不当作已完成用例、不自动再跑。"""
    base = {r["frame_id"]: r for r in unperturbed.frames}
    run = {r["frame_id"]: r for r in trace.frames}
    old_key = (base.get(start) or {}).get("track_key")
    target_index = (base.get(start) or {}).get("matched_det_index")
    per_frame = []
    old_not_updated = True
    new_keys: set[str] = set()
    for f in range(start, start + frames):
        record = (run.get(f) or {}).get("exclusion") or {}
        rows = record.get("rows", {})
        old = rows.get(str(old_key)) if old_key is not None else None
        prior_ok = bool(record.get("excluded_prior_present", {}).get(str(old_key)))
        if old is None or old["state"] == "tracked" or not prior_ok:
            old_not_updated = False
        takers = [k for k, v in rows.items() if k != str(old_key) and target_index is not None and target_index >= 0
                  and v["matched_det_index"] == target_index]
        new_keys.update(takers)
        per_frame.append({"frame_id": f, "excluded": record.get("excluded"), "old_key_row": old, "old_key_prior_present": prior_ok,
                          "target_det_index_unperturbed": (base.get(f) or {}).get("matched_det_index"), "takers": takers})
    activated_later = sorted(
        k for k in new_keys
        if any(((r.get("exclusion") or {}).get("rows", {}).get(k) or {}).get("state") == "tracked" for r in trace.frames if r["frame_id"] >= start)
    )
    after = [f for f in sorted(run) if f >= start + frames]
    exclusion_lifted = all(not ((run[f].get("exclusion") or {}).get("excluded")) for f in after)
    established = old_key is not None and old_not_updated and bool(activated_later)
    return {"old_key": old_key, "target_det_index": target_index, "per_frame": per_frame, "new_keys": sorted(new_keys),
            "new_keys_activated": activated_later, "exclusion_lifted_after": exclusion_lifted,
            "established": established, "status": "INJECTED" if established else "INJECTION_NOT_ESTABLISHED"}


def _new_arm_record(frame_id: int, manager: tm.TargetManager, entry: Any, outcome: Any) -> dict[str, Any]:
    """本帧 ⑤ 之后的状态与本帧效果（同一版本）；另存 C1-2 独立评分所需的策略后原始检测与各键同帧 prior（不读真值）。"""
    belief = manager.belief
    binding = manager.binding
    box = None
    if binding is not None and belief is not None and belief.observation_status == tm.OBSERVED and belief.t0 == frame_id:
        row = entry.row(binding.track_key)
        box = None if row is None else [float(v) for v in row.box_norm]
    priors: dict[str, list[float]] = {}
    for snapshot in entry.prior_snapshots:
        aligned, _reason = tm.same_frame_prior(entry, snapshot.track_key, manager.params)
        if aligned is not None:
            priors[str(aligned.track_key)] = [float(v) for v in aligned.xywh_px]
    prior = None if binding is None else priors.get(str(binding.track_key))
    effect = outcome.effect
    return {
        "frame_id": frame_id,
        "version": manager.version,
        "track_key": None if binding is None else binding.track_key,
        "episode_id": None if binding is None else binding.target_episode_id,
        "relation": None if binding is None else binding.relation,
        "observation": None if belief is None else belief.observation_status,
        "continuity": None if belief is None else belief.continuity_status,
        "age": None if belief is None else belief.age(frame_id),
        "observed_box_norm": box,
        "prior_xywh_px": prior,
        "predicted": None if belief is None or belief.predicted is None else dict(belief.predicted),
        "projection": None if outcome.projection is None else list(outcome.projection),
        "effect": None if effect is None else effect.as_record(),
        "matched_det_index": None if binding is None or entry.row(binding.track_key) is None else entry.row(binding.track_key).matched_det_index,
        "raw_detections_px": [[*(float(v) for v in det.box_px), float(det.conf), float(det.cls)] for det in entry.raw_detections],
        "priors_xywh_px": priors,
    }


# --- 评分（真值只在 score_ 函数） ---------------------------------------------------------


def _iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return 0.0 if union <= 0 else inter / union


def score_truth_box(truth_row: Mapping[str, Any] | None) -> tuple[float, float, float, float] | None:
    if not truth_row or not truth_row.get("truth_box_available") or not truth_row.get("geometrically_visible", True):
        return None
    return (float(truth_row["truth_box_x"]), float(truth_row["truth_box_y"]), float(truth_row["truth_box_width"]), float(truth_row["truth_box_height"]))


def score_new_arm_window(trace: NewArmTrace, truth: Mapping[int, Mapping[str, Any]], params: tm.CaptureParams,
                         window: tuple[int, int] = WINDOW) -> dict[str, Any]:
    """AC-17 新臂判据：557–600 每个真值可见帧上要么 OBSERVED 且绑定框与真值 IoU ≥ 0.5，要么处于
    age ≤ T_repair − 1 的 TENTATIVE 窗口；无 BROKEN、误绑帧 0。RR-1（用户答「修顺序，按提交后状态判」）：记录状态须与
    本帧效果同帧、同版本，否则该帧记 `STATE_EFFECT_INCONSISTENT`（不判通过）。"""
    rows = []
    failures = []
    misbound = 0
    broken = 0
    tentative = 0
    inconsistent = 0
    for record in trace.frames:
        f = record["frame_id"]
        if not window[0] <= f <= window[1]:
            continue
        truth_box = score_truth_box(truth.get(f))
        if truth_box is None:
            continue
        verdict = "FAIL"
        iou = None
        effect = record.get("effect") or {}
        if effect.get("frame_id") != f or "version" not in record or effect.get("version") != record.get("version"):
            # RR-1：按同一提交后状态/效果评分——本帧效果缺失或与记录状态不同版本（混记）→ 不判通过。
            verdict = "STATE_EFFECT_INCONSISTENT"
            inconsistent += 1
        elif record["continuity"] == tm.BROKEN:
            broken += 1
        elif record["observation"] == tm.OBSERVED and record["observed_box_norm"] is not None:
            iou = _iou(record["observed_box_norm"], truth_box)
            if iou >= 0.5:
                verdict = "PASS"
            else:
                misbound += 1
        elif record["continuity"] == tm.TENTATIVE and record["age"] is not None and record["age"] <= params.t_repair - 1:
            verdict = "PASS_TENTATIVE"
            tentative += 1
        if verdict in ("FAIL", "STATE_EFFECT_INCONSISTENT"):
            failures.append(f)
        rows.append({"frame_id": f, "verdict": verdict, "iou": iou, "observation": record["observation"],
                     "continuity": record["continuity"], "age": record["age"], "track_key": record["track_key"]})
    passed = bool(rows) and not failures and broken == 0 and misbound == 0 and inconsistent == 0
    return {"verdict": "PASS" if passed else "FAIL", "evaluated_frames": len(rows), "failures": failures,
            "broken_frames": broken, "misbound_frames": misbound, "state_effect_inconsistent_frames": inconsistent,
            "tentative_frames_provisional": tentative, "rows": rows}


def score_phenomenon_gate(records: Sequence[Mapping[str, Any]], truth: Mapping[int, Mapping[str, Any]],
                          window: tuple[int, int] = PHENOMENON_WINDOW) -> dict[str, Any]:
    """AC-17 现象门：红车点击后在 559–565 帧内至少一帧指针非 ok 且真值可见；否则 S-A-REPRO。"""
    hits = [r["frame_id"] for r in records if window[0] <= r["frame_id"] <= window[1] and not r["ok"]
            and score_truth_box(truth.get(r["frame_id"])) is not None]
    return {"window": list(window), "pointer_not_ok_truth_visible_frames": hits, "reproduced": bool(hits)}


def _px_to_norm(box_px: Sequence[float]) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = (float(v) for v in box_px[:4])
    return (x1 / WIDTH, y1 / HEIGHT, (x2 - x1) / WIDTH, (y2 - y1) / HEIGHT)


def _xywh_center_to_norm(xywh: Sequence[float]) -> tuple[float, float, float, float]:
    xc, yc, w, h = (float(v) for v in xywh)
    return ((xc - w / 2) / WIDTH, (yc - h / 2) / HEIGHT, w / WIDTH, h / HEIGHT)


def score_next_real_observation(frames_by_id: Mapping[int, Mapping[str, Any]], truth: Mapping[int, Mapping[str, Any]],
                                first: int, count: int) -> tuple[int, list[float], float] | None:
    """AC-18 原定义（C1-2）：[first, first+count) 内首个与真值 IoU ≥ 0.5 的**策略后原始检测**（与是否被接受为
    OBSERVED、是否 BROKEN 无关）；同帧多个取 IoU 最大者。→ (帧, 检测像素框, 与真值 IoU) 或 None。"""
    for f in range(first, first + count):
        record = frames_by_id.get(f)
        truth_box = score_truth_box(truth.get(f))
        if record is None or truth_box is None:
            continue
        best = None
        for det in record.get("raw_detections_px") or []:
            iou = _iou(_px_to_norm(det), truth_box)
            if iou >= 0.5 and (best is None or iou > best[1]):
                best = (list(det[:4]), iou)
        if best is not None:
            return f, best[0], best[1]
    return None


def score_injection(trace: NewArmTrace, truth: Mapping[int, Mapping[str, Any]], params: tm.CaptureParams, *,
                    start: int, gap: int) -> dict[str, Any]:
    """AC-18 判定（C1-2 按原文恢复）：下一次真实观测 = 缺口后 T_repair 帧内首个与真值 IoU ≥ 0.5 的**检测**（策略后原始检测，
    不要求被接受）；预测框 = 注入前原绑定键在该帧的**同帧 prior**（修复后也不换为新绑定键的 prior）；IoU ≥ 0.3 → PASS，
    < 0.3 → FAIL；无此检测 → NOT_EVALUABLE（不计通过）；原键在该帧无同帧 prior → 记证据缺失（`iou_verdict =
    EVIDENCE_MISSING`，原因 `original_key_same_frame_prior_missing`；用户 2026-10-10 IR-C2-5 裁定：不编造、不扩
    NOT_EVALUABLE、不从分母去掉、不计通过）。另分列：行 7 帧均有预测 look_at、准时报告、到期后原 ID 重现不续跟、修复。"""
    by_frame = {r["frame_id"]: r for r in trace.frames}
    predicted_frames = [f for f in range(start, start + gap)
                        if (by_frame.get(f) or {}).get("effect", {}) and by_frame[f]["effect"]["gimbal"] == "predicted"]
    row7 = [f for f in range(start, start + gap) if (by_frame.get(f) or {}).get("effect") and by_frame[f]["effect"]["authorization_row"] == 7]
    original = (by_frame.get(start - 1) or {}).get("track_key")
    found = score_next_real_observation(by_frame, truth, start + gap, params.t_repair)
    verdict, iou, reason, predicted_box = "NOT_EVALUABLE", None, None, None
    if original is None:
        reason = "original_key_unknown"
    elif found is None:
        reason = "no_detection_matching_truth_within_t_repair"
    else:
        prior = ((by_frame.get(found[0]) or {}).get("priors_xywh_px") or {}).get(str(original))
        if prior is None:
            verdict, reason = "EVIDENCE_MISSING", "original_key_same_frame_prior_missing"
        else:
            predicted_box = list(prior)
            iou = _iou(_xywh_center_to_norm(prior), _px_to_norm(found[1]))
            verdict = "PASS" if iou >= 0.3 else "FAIL"
    reports = [e for e in trace.events if e.get("type") == "report"]
    broken = [e for e in trace.events if e.get("type") == "continuity" and e.get("reason") == "continuity_broken"]
    repaired = [e for e in trace.events if e.get("kind") == "binding_committed" and e.get("relation") == "CONTINUITY_REPAIR"]
    not_resumed = None
    if broken:
        after = [r for r in trace.frames if r["frame_id"] > broken[0]["frame_id"]]
        not_resumed = all(r.get("continuity") == tm.BROKEN and (r.get("effect") or {}).get("body") != tm.FOLLOW for r in after)
    return {
        "gap": gap,
        "original_key": original,
        "row7_frames": row7,
        "row7_frames_with_predicted_look_at": predicted_frames,
        "all_row7_have_look_at": set(row7) <= set(predicted_frames),
        "iou_verdict": verdict,
        "iou": iou,
        "not_evaluable_reason": reason,
        "next_observation_frame": None if found is None else found[0],
        "next_observation_det_px": None if found is None else found[1],
        "next_observation_truth_iou": None if found is None else found[2],
        "predicted_xywh_px": predicted_box,
        "repairs": [e["frame_id"] for e in repaired],
        "reports_no_new_observation": [e["frame_id"] for e in reports],
        "broken_at": [e["frame_id"] for e in broken],
        "expired_original_not_resumed": not_resumed,
    }


def score_provisional_readings(new_frames: Sequence[Mapping[str, Any]], ac18: Mapping[str, Any],
                               truth: Mapping[int, Mapping[str, Any]], metadata: Mapping[int, Mapping[str, Any]], *,
                               ground_plane_y_m: float = 0.2, window: tuple[int, int] = WINDOW) -> dict[str, Any]:
    """AC-17「另报暂定读数」（零模型，只读已落盘的新臂逐帧记录与 AC-18 结果；不是门，均带 n）：

    * R-1 生存下界：AC-18 删检测各 m 中预测框对下一观测 IoU ≥ 0.3 的最大 m（只计可评缺口；NOT_EVALUABLE 不计通过）；
    * 两种量测点残差：窗口内 OBSERVED 且本帧观测效果的帧上，云台瞄准点 P_center（效果 `aim_point_world_m`）与框底中点
      射线 ∩ 地面（`geolocate.box_ground_intersection`）各自对真值目标世界位置的水平距离（m）；
    * 误 TENTATIVE：进入 TENTATIVE 的次数中，进入帧真值框可见者（原 ID 失配而目标仍可见）。"""
    from controller.geolocate import GeometryRejected, box_ground_intersection  # noqa: PLC0415

    evaluable = {k: v for k, v in ac18.items() if k.startswith("delete_m") and k.endswith("_repair") and v.get("iou_verdict") in ("PASS", "FAIL")}
    survived = [int(v["gap"]) for v in evaluable.values() if v["iou_verdict"] == "PASS"]
    r1 = {"lower_bound_frames": max(survived) if survived else None, "n_evaluable_gaps": len(evaluable),
          "gaps": {k: {"gap": v["gap"], "verdict": v["iou_verdict"], "iou": v.get("iou")} for k, v in sorted(ac18.items()) if k.startswith("delete_m") and k.endswith("_repair")}}

    def horizontal(point: Sequence[float], row: Mapping[str, Any]) -> float:
        return math.hypot(float(point[0]) - float(row["target_world_x_m"]), float(point[2]) - float(row["target_world_z_m"]))

    p_center, bottom, rows = [], [], []
    for record in new_frames:
        f = record["frame_id"]
        effect = record.get("effect") or {}
        row = truth.get(f)
        if not (window[0] <= f <= window[1]) or record.get("pre_click") or record.get("observation") != tm.OBSERVED:
            continue
        if effect.get("frame_id") != f or effect.get("gimbal") != "observed" or not effect.get("aim_point_world_m"):
            continue
        if score_truth_box(row) is None or record.get("observed_box_norm") is None:
            continue
        a = horizontal(effect["aim_point_world_m"], row)
        try:
            b = horizontal(box_ground_intersection(record["observed_box_norm"], metadata[f], ground_plane_y_m).point_world_m, row)
        except (GeometryRejected, ValueError, KeyError):
            b = None
        p_center.append(a)
        if b is not None:
            bottom.append(b)
        rows.append({"frame_id": f, "p_center_m": a, "bottom_center_m": b})

    def stats(values: Sequence[float]) -> dict[str, Any]:
        if not values:
            return {"n": 0}
        ordered = sorted(values)
        return {"n": len(ordered), "median_m": ordered[len(ordered) // 2] if len(ordered) % 2 else (ordered[len(ordered) // 2 - 1] + ordered[len(ordered) // 2]) / 2,
                "max_m": ordered[-1], "mean_m": sum(ordered) / len(ordered)}

    entries, false_entries = [], []
    previous = None
    for record in new_frames:
        current = record.get("continuity")
        if current == tm.TENTATIVE and previous != tm.TENTATIVE:
            entries.append(record["frame_id"])
            if score_truth_box(truth.get(record["frame_id"])) is not None:
                false_entries.append(record["frame_id"])
        previous = current
    return {"provisional": True, "R-1": r1,
            "measurement_point_residuals": {"p_center": stats(p_center), "bottom_center": stats(bottom), "rows": rows},
            "tentative": {"entries": entries, "entries_truth_visible": false_entries, "n_entries": len(entries)}}


def wilson_interval(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float] | None:
    if n <= 0:
        return None
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def score_roll_sequence(outcomes: Sequence[Mapping[str, Any]], geometries: Sequence[Mapping[str, Any] | None],
                        params: tm.CaptureParams) -> dict[str, Any]:
    """AC-19 冻结口径（单序列）：「在目标上」= 有效观测框中心落在真值多边形内；断轨 = 未删失帧上连续 ≥ T_repair
    帧无有效观测，或任一有效观测帧不在目标上（误跟单列并计入）；序列末不足 T_repair 的缺口记右删失。

    `outcomes[i]` = {"valid": bool, "center": (x, y) | None}（基线臂 = 指针 ok；新臂 = OBSERVED）。"""
    gap = 0
    broke = False
    misfollow = False
    right_censored = False
    for outcome, geometry in zip(outcomes, geometries):
        if geometry is None or geometry.get("censored"):
            continue
        if outcome.get("valid"):
            center = outcome.get("center")
            if center is None or not point_in_polygon(center[0], center[1], geometry["polygon"]):
                misfollow = True
                broke = True
            gap = 0
        else:
            gap += 1
            if gap >= params.t_repair:
                broke = True
    if not broke and 0 < gap < params.t_repair:
        right_censored = True
    return {"broken": broke, "misfollow": misfollow, "right_censored_gap": right_censored}


def score_roll_cells(sequences: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """每格（ω, Θ）断轨率与 Wilson 95% 区间；分母 = 热身与旋转首帧均未删失的序列数。"""
    cells: dict[tuple[float, float], dict[str, Any]] = {}
    for seq in sequences:
        key = (seq["omega"], seq["theta"])
        cell = cells.setdefault(key, {"omega": seq["omega"], "theta": seq["theta"], "baseline": [0, 0], "new": [0, 0]})
        if not seq["evaluable"]:
            continue
        for arm in ("baseline", "new"):
            cell[arm][1] += 1
            cell[arm][0] += int(seq[arm]["broken"])
    out = []
    for cell in cells.values():
        row = {"omega": cell["omega"], "theta": cell["theta"]}
        for arm in ("baseline", "new"):
            broken, n = cell[arm]
            row[arm] = {"broken": broken, "n": n, "rate": None if n == 0 else broken / n, "wilson95": wilson_interval(broken, n)}
        b, n = row["baseline"], row["new"]
        row["non_inferior"] = None if b["n"] == 0 or n["n"] == 0 else n["rate"] <= b["rate"]
        out.append(row)
    return sorted(out, key=lambda r: (r["omega"], r["theta"]))


# --- 启动前守卫（AR1-6；CAPTURE:A:1） -------------------------------------------------------


class LaunchRefused(RuntimeError):
    """保真未确认、剧本未预登记、或账本任一维余额不足：拒绝启动（S-A-FIDELITY / S-A-BUDGET）。"""


def load_fidelity_confirmation(path: Path | None, *, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """AC-27 确认文件：结论 consistent、具名确认人、覆盖两类样帧，且每个样帧文件现算 sha 与确认记录一致
    （确认绑定在被看过的那几张图上；文件缺失或被改即拒绝启动）。"""
    if path is None or not Path(path).is_file():
        raise LaunchRefused("S-A-FIDELITY: AC-27 fidelity confirmation file is missing")
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if document.get("schema_version") != FIDELITY_SCHEMA or document.get("conclusion") != "consistent" or not document.get("confirmed_by"):
        raise LaunchRefused("S-A-FIDELITY: fidelity confirmation is not a consistent, attributed confirmation")
    samples = document.get("samples", [])
    kinds = {sample.get("kind") for sample in samples}
    if not {"synthetic_roll", "click_page"} <= kinds:
        raise LaunchRefused("S-A-FIDELITY: confirmation must cover synthetic-roll and click-page samples")
    for sample in samples:
        relative, expected = sample.get("path"), sample.get("sha256")
        if not relative or not expected:
            raise LaunchRefused("S-A-FIDELITY: every confirmed sample needs path and sha256")
        target = Path(relative) if Path(relative).is_absolute() else Path(root) / relative
        if not target.is_file() or sha256_file(target) != expected:
            raise LaunchRefused(f"S-A-FIDELITY: confirmed sample {relative} is missing or changed")
    return document


def load_click_script(path: Path | None) -> tuple[dict[str, Any], str]:
    if path is None or not Path(path).is_file():
        raise LaunchRefused("AC-17: the preregistered click script is missing")
    data = Path(path).read_bytes()
    document = json.loads(data.decode("utf-8"))
    if document.get("schema_version") != CLICK_SCRIPT_SCHEMA or not document.get("registered_by"):
        raise LaunchRefused("AC-17: click script schema/registrant invalid")
    labels = [c.get("label") for c in document.get("clicks", [])]
    if "red_car" not in labels or "static_car" not in labels:
        raise LaunchRefused("AC-17: click script must contain a static_car click and the red_car click")
    red = next(c for c in document["clicks"] if c.get("label") == "red_car")
    if int(red["frame_id"]) != WINDOW[0]:
        raise LaunchRefused("AC-17: the red_car click must be at frame 557")
    return document, hashlib.sha256(data).hexdigest()


def load_roll_click_script(path: Path | None, plan: Mapping[str, Any], *, frames: Path = ADMITTED_FRAMES) -> tuple[dict[str, Any], str]:
    """AC-28 六基点击剧本启动前校验（缺点/错帧/sha 不符 → 拒绝启动；不自动补点、不读真值）。

    `plan` = 运行时按固定规则现算的 `roll_base_plan`；剧本须恰含六个基、与计划逐个同 k、点击帧 = k−1、
    帧字节 sha 与准入原帧现算值一致、坐标有限且在画内、登记人具名。返回 (剧本, 剧本字节 sha256)。"""
    if path is None or not Path(path).is_file():
        raise LaunchRefused("AC-28: the preregistered six-base roll click script is missing")
    data = Path(path).read_bytes()
    try:
        document = json.loads(data.decode("utf-8"))
    except ValueError as exception:
        raise LaunchRefused(f"AC-28: roll click script unreadable ({exception})") from exception
    if document.get("schema_version") != ROLL_CLICK_SCHEMA or not document.get("registered_by"):
        raise LaunchRefused("AC-28: roll click script schema/registrant invalid")
    planned = {int(entry["base_k"]): entry for entry in plan["bases"]}
    clicks = document.get("clicks") or []
    seen: set[int] = set()
    for click in clicks:
        try:
            base_k, frame_id = int(click["base_k"]), int(click["frame_id"])
            x_px, y_px = float(click["x_px"]), float(click["y_px"])
        except (KeyError, TypeError, ValueError) as exception:
            raise LaunchRefused(f"AC-28: malformed roll click {click!r}") from exception
        if base_k not in planned or base_k in seen:
            raise LaunchRefused(f"AC-28: base {base_k} not in the fixed plan or registered twice")
        seen.add(base_k)
        if frame_id != base_k - 1:
            raise LaunchRefused(f"AC-28: base {base_k} click must be on raw frame k−1={base_k - 1}, got {frame_id}")
        actual = sha256_file(frame_paths(frame_id, frames)[0])
        if click.get("image_sha256") != actual or planned[base_k]["image_sha256"] != actual:
            raise LaunchRefused(f"AC-28: frame {frame_id} image sha mismatch")
        if not (math.isfinite(x_px) and math.isfinite(y_px) and 0 <= x_px < WIDTH and 0 <= y_px < HEIGHT):
            raise LaunchRefused(f"AC-28: base {base_k} click point out of frame")
    missing = sorted(set(planned) - seen)
    if missing:
        raise LaunchRefused(f"AC-28: missing roll clicks for bases {missing}")
    return document, hashlib.sha256(data).hexdigest()


def roll_clicks_by_base(document: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    """已校验剧本 → {k: 送入两臂的唯一选择输入}（点击帧 = k−1 原始热身末帧；72 序列复用这六点）。"""
    return {int(c["base_k"]): {"frame_id": int(c["frame_id"]), "x_px": float(c["x_px"]), "y_px": float(c["y_px"]),
                               "label": f"roll_base_{int(c['base_k'])}"} for c in document["clicks"]}


def ledger_balance(ledger_path: Path | None = None, *, candidate: int, loads: int, frames: int) -> dict[str, Any]:
    """启动前逐维核余额（C1-5：整体校验 + 候选归属 + 逐维；缺失/损坏/UNKNOWN/不一致/未结算 → 拒绝，不推余额）。"""
    try:
        ledger = capture_ledger.read(ledger_path or LEDGER)
        return capture_ledger.check_launch(ledger, candidate, {"replay_yolo_loads": loads, "replay_inference_frames": frames,
                                                                "mini_new_disk_bytes": 0})
    except capture_ledger.LedgerRefused as refusal:
        raise LaunchRefused(str(refusal)) from refusal


def planned_inference_frames(frame_count: int, sequences: int) -> int:
    """正式回放推理帧计划：原始 829 × 2 策略 + 合成 2 臂 × 序列 × 16。"""
    return frame_count * 2 + 2 * sequences * ROLL_FRAMES


def launch_preconditions(arguments: Any) -> dict[str, Any]:
    """正式回放启动前全部零模型前置（任一不满足 → `LaunchRefused`，在任何模型加载之前）：AC-27 确认文件（样帧 sha 现核）、
    AC-17 预登记剧本（须为确认记录里那一份）、AC-28 六基剧本（对按规则现算的计划逐基校验）、账本逐维余额。"""
    confirmation = load_fidelity_confirmation(arguments.fidelity_confirmation)
    script, script_sha = load_click_script(arguments.click_script)
    confirmed = (confirmation.get("ac17_click_script") or {}).get("sha256")
    if confirmed is not None and confirmed != script_sha:
        raise LaunchRefused("AC-17: the click script is not the one recorded with the AC-27 confirmation")
    plan = roll_base_plan(score_truth_rows(), admitted_frame_ids())
    roll_script, roll_sha = load_roll_click_script(arguments.roll_click_script, plan)
    ledger_balance(candidate=arguments.candidate, loads=1,
                   frames=planned_inference_frames(len(admitted_frame_ids()), len(ROLL_OMEGAS) * len(ROLL_THETAS) * 2 * ROLL_BASES))
    return {"click_script": script, "click_script_sha256": script_sha, "roll_plan": plan,
            "roll_click_script": roll_script, "roll_click_script_sha256": roll_sha}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-CAPTURE-001 离线回放（AC-17/18/19/27/28）")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check-input", help="S-A-INPUT 准入原件完整性与帧时刻核对（零模型）")
    check.add_argument("--output", type=Path, default=OUTPUT_ROOT / "input-check.json")
    fidelity = sub.add_parser("fidelity", help="AC-27 合成滚转保真样帧（零推理）")
    fidelity.add_argument("--output", type=Path, default=OUTPUT_ROOT / "fidelity")
    prepare = sub.add_parser("prepare-roll", help="AC-28 六基预登记计划（零模型）：按固定规则列六个 k 与原始 k−1 帧")
    prepare.add_argument("--output", type=Path, default=OUTPUT_ROOT / "roll-clicks" / "roll-base-plan.json")
    rescore = sub.add_parser("rescore", help="AC-17 另报暂定读数（零模型，只读已落盘的正式回放目录）")
    rescore.add_argument("--run-dir", type=Path, required=True)
    run = sub.add_parser("run", help="正式回放（需保真确认、两份预登记剧本与账本余额）")
    run.add_argument("--fidelity-confirmation", type=Path, required=True)
    run.add_argument("--click-script", type=Path, required=True)
    run.add_argument("--roll-click-script", type=Path, required=True)
    run.add_argument("--candidate", type=int, required=True)
    run.add_argument("--output", type=Path, default=None)
    arguments = parser.parse_args(argv)
    if arguments.command == "check-input":
        report = check_input()
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        summary = {k: v for k, v in report.items() if k != "listing"}
        print(json.dumps(summary, ensure_ascii=False))
        return 0 if report["ok"] else 3
    if arguments.command == "fidelity":
        samples = make_fidelity_samples(arguments.output)
        print(json.dumps(samples, ensure_ascii=False, indent=1))
        return 0
    if arguments.command == "prepare-roll":
        try:
            plan = roll_base_plan(score_truth_rows(), admitted_frame_ids())
        except RollBaseError as error:
            print(f"ROLL_PLAN_REFUSED: {error}", file=sys.stderr)
            return 4
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({"plan": str(arguments.output), "frame_ids": [b["frame_id"] for b in plan["bases"]]}, ensure_ascii=False))
        return 0
    if arguments.command == "rescore":
        run_dir = Path(arguments.run_dir)
        new_frames = json.loads((run_dir / "new-arm.json").read_text(encoding="utf-8"))["frames"]
        report = json.loads((run_dir / "replay-report.json").read_text(encoding="utf-8"))
        metadata = {f: json.loads(frame_paths(f)[1].read_text(encoding="utf-8")) for f in range(WINDOW[0], WINDOW[1] + 1)
                    if frame_paths(f)[1].is_file()}
        readings = score_provisional_readings(new_frames, report.get("AC-18") or {}, score_truth_rows(), metadata)
        (run_dir / "provisional-readings.json").write_text(json.dumps(readings, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in readings.items() if k != "measurement_point_residuals"} |
                         {"residuals": {k: v for k, v in readings["measurement_point_residuals"].items() if k != "rows"}}, ensure_ascii=False))
        return 0
    os.environ.setdefault("YOLO_OFFLINE", "True")
    os.environ.setdefault("YOLO_AUTOINSTALL", "False")
    try:
        preconditions = launch_preconditions(arguments)
    except (LaunchRefused, RollBaseError) as refusal:
        print(f"LAUNCH_REFUSED: {refusal}", file=sys.stderr)
        return 4
    # 正式回放执行体只在上述前置全部满足后才可达。
    from tools.eng_capture import formal_run  # noqa: PLC0415

    return formal_run.run(arguments, preconditions=preconditions)


if __name__ == "__main__":
    raise SystemExit(main())
