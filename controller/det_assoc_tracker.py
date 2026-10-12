"""`det-assoc-v1`：在域微调 YOLO11 检测器 + ultralytics ByteTrack/BoT-SORT 关联（P1-ENG-FAST-002 §3.5）。

`TrackerPlugin` 的一个局部备选实现（本场景专用、换目标需重训练），与冻结 NanoTrack-v2 并列；
缺省插件不变（CLI 缺省仍 `csrt`），只有显式 `--tracker det-assoc-v1` 才会用到本模块。

语义（K3）：
- `init(image, box)`：新建关联器；对初始化帧检测一次并调用关联器 `update` **恰一次**；绑定 = 本帧输出
  track 中与初始化框 IoU 最大者（并列取检测分数高者），且 IoU ≥ 0.50；否则返回 False。
- `update(image)`：检测 + 关联一次；绑定 id 在本帧输出 → `ok`（置信度 = 匹配检测分数，来源 `tracker`）；
  绑定 id 在库的 lost 池（buffer 内）→ `lost("bound_track_unmatched")`；否则 → `lost("bound_track_removed")`。
  库自身在 buffer 内把同一 id 找回即恢复 `ok`；**从不**自动改绑新 id（重播种走 LOOP-001 人工确认路径）。
- 调用契约：每处理帧调用一次且按帧序；库 `frame_id` = 已送入帧数（含初始化帧）。

常驻模式（P1-ENG-ACQ-001 §3.1，AR1-3；`mode="resident"`，只由 `create_tracker("det-assoc-v1", resident=True)`
产生）：`step(image, frame_id, metadata)` 每个传感器帧恰一次检测 + 关联并写按 `frame_id` 的历史；
`pointer_result`/`designate`/`follow`/`pointer`/`history` 走无 ultralytics 依赖的 `controller.resident_core`
（与离线线束同一实现）。`compat`（缺省）与 `resident` 方法集互斥，误用抛 `ProtocolMisuse`、不检测。
常驻模式按 `gmc_source ∈ {pose, pose-center, pose-aabb, optflow, none}` 在库 KF 预测后、首轮关联前
（`_pre_first_associate` 子类钩子）施加相机自运动补偿；`pose`（≡ `pose-aabb`，缺省不变）由相邻帧元数据位姿算
纯旋转单应（`controller.pose_gmc`）后取四角 AABB；`pose-center`（P1-ENG-CAPTURE-001 C2）只移中心、宽高不变。

P1-ENG-CAPTURE-001 C1/C3（AR1-2）：`class_policy ∈ {per_class, unify_vehicle}`（构造器缺省 `per_class` 不变）；
`unify_vehicle` = `predict(..., agnostic_nms=True)` 且进关联器前 cls 置 0。常驻 `step` 另把本帧策略后原始检测、
未确认轨迹行、`matched_det_index`、两阶段只读 KF 快照（补偿后首轮关联前的 prior；`update` 返回后的
posterior/prior）写进历史；这些字段只在进程内与会话日志，不进任何桥文件。

真值隔离（AC-8；ACQ-001 AC-9）：本模块只读图像、规格文件与权重及帧元数据中的平台位姿，只导入标准库、
`controller.trackers`/`controller.resident_core`/`controller.pose_gmc` 与 ultralytics/torch/numpy；
不读 S3/S4、不导入 `tools.*` 或任何评估器。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .pose_gmc import GMC_SOURCES, is_pose_source, jacobian, map_point, pose_homography, warp_box_xyxy
from .resident_core import (
    DEFAULT_HISTORY_DEPTH,
    HISTORY_VIEW_COMPAT,
    KF_POSTERIOR,
    KF_PRIOR,
    UNCONFIRMED,
    Designation,
    FrameTracks,
    HistoryEntry,
    KfSnapshot,
    Level2Runner,
    ProtocolMisuse,
    RawDetection,
    ResidentCore,
    ResolverConfig,
    TrackRow,
    make_kf_snapshot,
    repository_level2_runner,
    rows_from_library,
)
from .trackers import MODEL_SPEC_SCHEMA, TrackerPlugin, TrackerResult, clip_box_norm, image_size, sha256_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DET_ASSOC_SPEC = PROJECT_ROOT / "config" / "det-assoc-v1.models.json"
TRACKER_NAME = "det-assoc-v1"
PINNED_ULTRALYTICS = "8.4.104"
BIND_IOU = 0.50
ALGORITHMS = ("bytetrack", "botsort")
REASON_NOT_INITIALIZED = "tracker_not_initialized"
REASON_UNMATCHED = "bound_track_unmatched"
REASON_REMOVED = "bound_track_removed"
REASON_INVALID_BOX = "invalid_tracker_box"
MODES = ("compat", "resident")
COMPAT = "compat"
RESIDENT = "resident"
LEVEL2_TRACKER = "nanotrack-v2"
#: P1-ENG-CAPTURE-001 C1：检测类别策略闭集；构造器缺省 `per_class`（SOT/e1/compat/其他离线工厂不传新值）。
CLASS_POLICIES: tuple[str, ...] = ("per_class", "unify_vehicle")
PER_CLASS = "per_class"
UNIFY_VEHICLE = "unify_vehicle"


def _sha(value: Any, label: str) -> str:
    text = str(value)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return text


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _unit_float(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    number = float(value)
    if not math.isfinite(number) or not 0.0 < number < 1.0:
        raise ValueError(f"{label} must lie in (0, 1)")
    return number


def load_det_assoc_spec(path: Path) -> dict[str, Any]:
    """规格文件字段齐全性校验（缺字段/类型不符 fail-closed，镜像 NanoTrack 规格检查）。"""
    path = Path(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exception:
        raise FileNotFoundError(f"det-assoc-v1 model spec is missing: {path}") from exception
    except json.JSONDecodeError as exception:
        raise ValueError(f"det-assoc-v1 model spec is invalid JSON: {path}") from exception
    if not isinstance(value, Mapping):
        raise ValueError("model spec must be an object")
    spec = dict(value)
    if spec.get("schema_version") != MODEL_SPEC_SCHEMA:
        raise ValueError(f"unsupported det-assoc-v1 model spec schema {spec.get('schema_version')!r}")
    if spec.get("tracker") != TRACKER_NAME:
        raise ValueError("model spec tracker must be 'det-assoc-v1'")
    if spec.get("ultralytics_version") != PINNED_ULTRALYTICS:
        raise ValueError(f"model spec ultralytics_version must be {PINNED_ULTRALYTICS}")
    weights = spec.get("weights")
    if not isinstance(weights, Mapping):
        raise ValueError("model spec.weights must be an object")
    if not isinstance(weights.get("path"), str) or not weights["path"]:
        raise ValueError("model spec.weights.path must be a non-empty string")
    _sha(weights.get("sha256"), "model spec.weights.sha256")
    _positive_int(weights.get("size_bytes"), "model spec.weights.size_bytes")
    freeze = spec.get("freeze")
    if not isinstance(freeze, Mapping) or not isinstance(freeze.get("path"), str):
        raise ValueError("model spec.freeze.path must be a string")
    _sha(freeze.get("sha256"), "model spec.freeze.sha256")
    _positive_int(spec.get("imgsz"), "model spec.imgsz")
    _unit_float(spec.get("conf"), "model spec.conf")
    _unit_float(spec.get("nms_iou"), "model spec.nms_iou")
    classes = spec.get("classes")
    if classes != {"0": "vehicle", "1": "target"}:
        raise ValueError("model spec.classes must be {'0': 'vehicle', '1': 'target'}")
    device = spec.get("device_policy")
    if not isinstance(device, Mapping) or device.get("preferred") not in ("mps", "cpu") or device.get("fallback") != "cpu":
        raise ValueError("model spec.device_policy must be {preferred: mps|cpu, fallback: cpu}")
    association = spec.get("association")
    if not isinstance(association, Mapping) or association.get("algorithm") not in ALGORITHMS:
        raise ValueError("model spec.association.algorithm must be bytetrack or botsort")
    args = association.get("args")
    if not isinstance(args, Mapping) or args.get("tracker_type") != association["algorithm"]:
        raise ValueError("model spec.association.args must be the full frozen tracker args")
    for key in ("track_high_thresh", "track_low_thresh", "new_track_thresh", "track_buffer", "match_thresh", "fuse_score"):
        if key not in args:
            raise ValueError(f"model spec.association.args.{key} is missing")
    return spec


def _verify_file(path: Path, sha256: str, size_bytes: int | None, label: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"det-assoc-v1 {label} is missing: {path}")
    if size_bytes is not None and path.stat().st_size != size_bytes:
        raise ValueError(f"det-assoc-v1 {label} size mismatch: expected {size_bytes}, got {path.stat().st_size}")
    actual = sha256_file(path)
    if actual != sha256:
        raise ValueError(f"det-assoc-v1 {label} SHA-256 mismatch: expected {sha256}, got {actual}")
    return actual


def _default_model_loader(weights_path: Path) -> Any:
    from ultralytics import YOLO  # noqa: PLC0415

    return YOLO(str(weights_path))


def _default_tracker_factory(algorithm: str, args: Mapping[str, Any]) -> Any:
    from ultralytics.trackers import BOTSORT, BYTETracker  # noqa: PLC0415
    from ultralytics.utils import IterableSimpleNamespace  # noqa: PLC0415

    namespace = IterableSimpleNamespace(**dict(args))
    return BOTSORT(args=namespace) if algorithm == "botsort" else BYTETracker(args=namespace)


def apply_pose_warp(tracks: Sequence[Any], homography: Any) -> int:
    """把 3×3 位姿单应施加到库轨迹的 KF 状态（四角 AABB 定位置与尺寸、雅可比转向速度与协方差）。

    BoT-SORT 的 `BOTrack` 状态为 xywh，ByteTrack 的 `STrack` 为 xyah；返回实际改写的轨迹数。"""
    import numpy as np  # noqa: PLC0415

    changed = 0
    for track in tracks:
        mean = getattr(track, "mean", None)
        if mean is None:
            continue
        xywh = hasattr(track, "tlwh_to_xywh")
        xc, yc = float(mean[0]), float(mean[1])
        if xywh:
            w, h = float(mean[2]), float(mean[3])
        else:
            h = float(mean[3])
            w = float(mean[2]) * h
        warped = warp_box_xyxy(homography, (xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2))
        jac = jacobian(homography, xc, yc)
        if warped is None or jac is None:
            continue
        x1, y1, x2, y2 = warped
        nw, nh = max(x2 - x1, 1e-6), max(y2 - y1, 1e-6)
        mean[0], mean[1] = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        if xywh:
            mean[2], mean[3] = nw, nh
        else:
            mean[2], mean[3] = nw / nh, nh
        j = np.asarray(jac, dtype=float)
        mean[4:6] = j @ np.asarray(mean[4:6], dtype=float)
        transform = np.eye(8)
        transform[0:2, 0:2] = j
        transform[4:6, 4:6] = j
        track.covariance = transform @ track.covariance @ transform.T
        changed += 1
    return changed


def apply_pose_center(tracks: Sequence[Any], homography: Any) -> int:
    """C2 只移中心：(xc, yc) ← H(xc, yc)；J = ∂H/∂(u,v)|(xc,yc)；(vx, vy) ← J·(vx, vy)；8×8 变换在位置块与
    速度块放 J、其余单位，P ← T P Tᵀ。宽高与宽高速度不变；`map_point` 为 None 或雅可比不可得时该轨迹不改。"""
    import numpy as np  # noqa: PLC0415

    changed = 0
    for track in tracks:
        mean = getattr(track, "mean", None)
        if mean is None:
            continue
        xc, yc = float(mean[0]), float(mean[1])
        mapped = map_point(homography, xc, yc)
        jac = jacobian(homography, xc, yc)
        if mapped is None or jac is None:
            continue
        mean[0], mean[1] = mapped
        j = np.asarray(jac, dtype=float)
        mean[4:6] = j @ np.asarray(mean[4:6], dtype=float)
        transform = np.eye(8)
        transform[0:2, 0:2] = j
        transform[4:6, 4:6] = j
        track.covariance = transform @ track.covariance @ transform.T
        changed += 1
    return changed


def kf_state(track: Any) -> dict[str, Any] | None:
    """库轨迹 KF 状态 → 纯 Python 深复制（xywh 像素、每帧速度、位置协方差块）；不回写库。

    BoT-SORT `BOTrack` 为 xywh，ByteTrack `STrack` 为 xyah（w = a·h）。无 KF → None；读不出 → `invalid`。"""
    mean = getattr(track, "mean", None)
    covariance = getattr(track, "covariance", None)
    if mean is None or covariance is None:
        return None
    try:
        xc, yc = float(mean[0]), float(mean[1])
        if hasattr(track, "tlwh_to_xywh"):
            w, h = float(mean[2]), float(mean[3])
        else:
            h = float(mean[3])
            w = float(mean[2]) * h
        return {
            "track_id": int(track.track_id),
            "xywh": [xc, yc, w, h],
            "vel": [float(mean[4]), float(mean[5])],
            "pos_cov": [[float(covariance[0][0]), float(covariance[0][1])], [float(covariance[1][0]), float(covariance[1][1])]],
        }
    except (TypeError, IndexError, ValueError, AttributeError):
        return {"track_id": int(getattr(track, "track_id", -1)), "invalid": "kf_unreadable"}


def snapshot_from_state(state: Mapping[str, Any], sensor_frame_id: int, library_frame_id: int, phase: str) -> KfSnapshot:
    if "invalid" in state:
        return make_kf_snapshot(sensor_frame_id, library_frame_id, int(state["track_id"]), phase, None, None, None, forced_invalid=str(state["invalid"]))
    return make_kf_snapshot(sensor_frame_id, library_frame_id, int(state["track_id"]), phase, state["xywh"], state["vel"], state["pos_cov"])


def make_resident_associator(algorithm: str, args: Mapping[str, Any], gmc_source: str) -> Any:
    """常驻关联器：钉版库 BoT-SORT/ByteTrack 的子类，只覆写 `_pre_first_associate`（事实 4）。

    `pose`/`pose-aabb` → 施加 `set_pose_warp` 给出的 3×3 单应（四角 AABB；每帧至多一次、用后即清）；
    `pose-center` → 同一单应只移中心（C2）；`optflow` → 库原 `sparseOptFlow`；`none` → 单位阵（不补偿）。
    冻结参数原样传入，不改 `config/det-assoc-v1.models.json`。

    AR1-2：本帧补偿完成后、首轮关联及任何量测更新前，复制 `strack_pool` 与 `unconfirmed` 的 KF 状态（prior），
    由 `take_prior_snapshots()` 取走（深复制，不回写库）；H 缺失/none/optflow 也在同一阶段复制。"""
    if gmc_source not in GMC_SOURCES:
        raise ValueError(f"gmc_source must be one of {GMC_SOURCES}")
    from ultralytics.trackers import BOTSORT, BYTETracker  # noqa: PLC0415
    from ultralytics.utils import IterableSimpleNamespace  # noqa: PLC0415

    base = BOTSORT if algorithm == "botsort" else BYTETracker

    class ResidentAssociator(base):  # type: ignore[misc, valid-type]
        def __init__(self, namespace: Any):
            super().__init__(namespace)
            self.gmc_source = gmc_source
            self._pose_warp: Any = None
            self.pose_warps_applied = 0
            self._prior_capture: list[dict[str, Any]] | None = None

        def set_pose_warp(self, homography: Any) -> None:
            self._pose_warp = homography

        def take_prior_snapshots(self) -> list[dict[str, Any]] | None:
            """取走本帧 prior（None = 本帧未经过 `_pre_first_associate`）；取后即清。"""
            captured, self._prior_capture = self._prior_capture, None
            return captured

        def _capture_priors(self, strack_pool, unconfirmed) -> None:  # noqa: ANN001
            states = []
            for track in [*strack_pool, *unconfirmed]:
                state = kf_state(track)
                if state is not None:
                    states.append(state)
            self._prior_capture = states

        def _pre_first_associate(self, strack_pool, unconfirmed, img, results_high):  # noqa: ANN001
            homography, self._pose_warp = self._pose_warp, None
            if self.gmc_source == "optflow":
                result = super()._pre_first_associate(strack_pool, unconfirmed, img, results_high)
                self._capture_priors(strack_pool, unconfirmed)
                return result
            if self.gmc_source == "none" or homography is None:
                self._capture_priors(strack_pool, unconfirmed)
                return None
            warp = apply_pose_center if self.gmc_source == "pose-center" else apply_pose_warp
            warp(strack_pool, homography)
            warp(unconfirmed, homography)
            self.pose_warps_applied += 1
            self._capture_priors(strack_pool, unconfirmed)
            return None

    return ResidentAssociator(IterableSimpleNamespace(**dict(args)))


def _detection_records(boxes: Any) -> list[RawDetection]:
    """策略后检测 → `RawDetection`（未裁剪像素框）；兼容库 `Boxes`（`.data`）与测试替身（`.rows`）。"""
    data = getattr(boxes, "data", None)
    if data is not None and hasattr(data, "tolist"):
        rows = data.tolist()
    else:
        rows = list(getattr(boxes, "rows", []) or [])
    records: list[RawDetection] = []
    for index, row in enumerate(rows):
        try:
            values = [float(v) for v in row[:6]]
        except (TypeError, ValueError):
            continue
        if len(values) < 6:
            continue
        records.append(RawDetection(index, (values[0], values[1], values[2], values[3]), values[4], int(values[5])))
    return records


def _unify_classes(boxes: Any) -> Any:
    """C1：进关联器前把类别列置 0（`unify_vehicle`）；库 `Boxes` 改其 numpy 数据，测试替身改 `.rows`。"""
    data = getattr(boxes, "data", None)
    if data is not None and hasattr(data, "shape") and len(getattr(data, "shape", ())) == 2:
        if data.shape[0]:
            data[:, -1] = 0.0
        return boxes
    rows = getattr(boxes, "rows", None)
    if rows is not None:
        boxes.rows = [[*list(row[:5]), 0.0, *list(row[6:])] for row in rows]
    return boxes


def _default_level2_factory() -> TrackerPlugin:
    """第二级一次性 SOT：冻结 `nanotrack-v2`（事实 17；D2 裁定 (j)）。每次指定新建。"""
    from .trackers import create_tracker  # noqa: PLC0415

    return create_tracker(LEVEL2_TRACKER)


def _resolve_device(preferred: str) -> tuple[str, str | None]:
    if preferred == "cpu":
        return "cpu", None
    try:
        import torch  # noqa: PLC0415

        if torch.backends.mps.is_available():
            return "mps", None
    except Exception as exception:  # noqa: BLE001
        return "cpu", f"mps_probe_error:{type(exception).__name__}"
    return "cpu", "mps_unavailable"


def _iou_xyxy(a: Sequence[float], b: Sequence[float]) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


class DetAssocTracker:
    name = TRACKER_NAME
    backend = "ultralytics"
    version = PINNED_ULTRALYTICS

    def __init__(
        self,
        *,
        spec_path: Path = DEFAULT_DET_ASSOC_SPEC,
        device: str | None = None,
        model_loader: Callable[[Path], Any] | None = None,
        tracker_factory: Callable[[str, Mapping[str, Any]], Any] | None = None,
        check_library_version: bool = True,
        mode: str = COMPAT,
        gmc_source: str = "pose",
        history_depth: int = DEFAULT_HISTORY_DEPTH,
        resolver: ResolverConfig | None = None,
        level2_factory: Callable[[], TrackerPlugin] | None = None,
        level2_runner: Level2Runner | None = None,
        capture_hz: float = 5.0,
        class_policy: str = PER_CLASS,
        history_view: str = HISTORY_VIEW_COMPAT,
    ):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        if gmc_source not in GMC_SOURCES:
            raise ValueError(f"gmc_source must be one of {GMC_SOURCES}")
        if class_policy not in CLASS_POLICIES:
            raise ValueError(f"class_policy must be one of {CLASS_POLICIES}")
        self.class_policy = class_policy
        self.mode = mode
        self._spec_path = Path(spec_path).resolve()
        self._spec = load_det_assoc_spec(self._spec_path)
        self._spec_sha256 = sha256_file(self._spec_path)
        root = PROJECT_ROOT
        weights = self._spec["weights"]
        weights_path = Path(weights["path"])
        self._weights_path = weights_path if weights_path.is_absolute() else (root / weights_path)
        self._weights_sha256 = _verify_file(self._weights_path, weights["sha256"], int(weights["size_bytes"]), "weights")
        freeze_path = Path(self._spec["freeze"]["path"])
        self._freeze_path = freeze_path if freeze_path.is_absolute() else (root / freeze_path)
        self._freeze_sha256 = _verify_file(self._freeze_path, self._spec["freeze"]["sha256"], None, "freeze file")
        if check_library_version:
            import ultralytics  # noqa: PLC0415

            if ultralytics.__version__ != PINNED_ULTRALYTICS:
                raise RuntimeError(f"det-assoc-v1 requires ultralytics {PINNED_ULTRALYTICS}, found {ultralytics.__version__}")
        if device is None:
            self._device, self._device_fallback = _resolve_device(self._spec["device_policy"]["preferred"])
        else:
            self._device, self._device_fallback = device, None
        self._imgsz = int(self._spec["imgsz"])
        self._conf = float(self._spec["conf"])
        self._nms_iou = float(self._spec["nms_iou"])
        self._algorithm = str(self._spec["association"]["algorithm"])
        self._tracker_args = dict(self._spec["association"]["args"])
        self._custom_tracker_factory = tracker_factory is not None
        self._tracker_factory = tracker_factory or _default_tracker_factory
        self._model = (model_loader or _default_model_loader)(self._weights_path)
        self._tracker: Any = None
        self._bound_id: int | None = None
        self._last_reason: str | None = None
        # 常驻模式状态（compat 下不建历史）。
        self.gmc_source = gmc_source
        self._core: ResidentCore | None = None
        if mode == RESIDENT:
            config = resolver or ResolverConfig(l_replay_frames=history_depth)
            # IR-1：缺省旧消费视图；只有捕获入口显式传 `history_view="capture"`。
            self._core = ResidentCore(history_depth, config, history_view=history_view)
        self._capture_hz = float(capture_hz)
        self._level2_factory = level2_factory or _default_level2_factory
        self._level2_runner = level2_runner
        self._frame_source: Any = None
        self._last_detections: list[RawDetection] = []
        self._last_step_frame_id: int | None = None
        self._last_step_metadata: Mapping[str, Any] | None = None
        self.detect_calls = 0
        self.pose_warp_skipped = 0

    # --- 内部 ---------------------------------------------------------------

    def _require(self, mode: str, method: str) -> None:
        if self.mode != mode:
            raise ProtocolMisuse(f"{method}() is not available in {self.mode!r} mode (§3.1)")

    @property
    def agnostic_nms(self) -> bool:
        return self.class_policy == UNIFY_VEHICLE

    def _detect(self, image: Any) -> Any:
        """检测一帧 → ultralytics `Boxes`（numpy，库 `track.py` 同一形态）；分数 < conf 已被库过滤。

        `per_class`：调用逐字同修改前（不传 `agnostic_nms`）。`unify_vehicle`：`agnostic_nms=True`，进关联器前 cls 置 0。"""
        self.detect_calls += 1
        if self.class_policy == UNIFY_VEHICLE:
            results = self._model.predict(
                source=image, imgsz=self._imgsz, conf=self._conf, iou=self._nms_iou, device=self._device, verbose=False,
                agnostic_nms=True,
            )
            return _unify_classes(results[0].boxes.cpu().numpy())
        results = self._model.predict(
            source=image, imgsz=self._imgsz, conf=self._conf, iou=self._nms_iou, device=self._device, verbose=False
        )
        return results[0].boxes.cpu().numpy()

    def _step(self, image: Any) -> list[list[float]]:
        boxes = self._detect(image)
        self._last_detections = _detection_records(boxes)
        output = self._tracker.update(boxes, image)
        return [[float(v) for v in row] for row in output.tolist()] if len(output) else []

    def detection_cache_key(self, frame_sha256: str) -> tuple[Any, ...]:
        """§3.1 检测缓存键 = (权重 sha, class_policy, agnostic_nms, imgsz, conf, nms_iou, 帧字节 sha)。"""
        return (self._weights_sha256, self.class_policy, self.agnostic_nms, self._imgsz, self._conf, self._nms_iou, str(frame_sha256))

    def _lost_ids(self) -> set[int]:
        return {int(track.track_id) for track in getattr(self._tracker, "lost_stracks", [])}

    # --- TrackerPlugin -----------------------------------------------------

    def init(self, image: Any, box_norm: Sequence[float]) -> bool:
        self._require(COMPAT, "init")
        clipped = clip_box_norm(box_norm)
        self._bound_id = None
        self._tracker = self._tracker_factory(self._algorithm, self._tracker_args)
        if clipped is None:
            return False
        width, height = image_size(image)
        target = (clipped[0] * width, clipped[1] * height, (clipped[0] + clipped[2]) * width, (clipped[1] + clipped[3]) * height)
        rows = self._step(image)  # 关联器在初始化帧恰调用一次
        best: tuple[float, float, int] | None = None
        for row in rows:
            value = _iou_xyxy(target, row[:4])
            if value < BIND_IOU:
                continue
            key = (value, float(row[5]), -int(row[4]))
            if best is None or key > best:
                best = key
        if best is None:
            return False
        self._bound_id = -best[2]
        return True

    def update(self, image: Any) -> TrackerResult:
        self._require(COMPAT, "update")
        if self._tracker is None or self._bound_id is None:
            return TrackerResult.lost(REASON_NOT_INITIALIZED)
        width, height = image_size(image)
        rows = self._step(image)
        for row in rows:
            if int(row[4]) != self._bound_id:
                continue
            x1, y1, x2, y2 = row[:4]
            box = clip_box_norm((x1 / width, y1 / height, (x2 - x1) / width, (y2 - y1) / height))
            score = float(row[5])
            if box is None or not math.isfinite(score) or not 0.0 <= score <= 1.0:
                return TrackerResult.lost(REASON_INVALID_BOX)
            return TrackerResult(box_norm=box, ok=True, confidence=score, confidence_source="tracker")
        if self._bound_id in self._lost_ids():
            return TrackerResult.lost(REASON_UNMATCHED)
        return TrackerResult.lost(REASON_REMOVED)

    # --- 常驻协议（§3.1；AC-1/AC-2/AC-4）--------------------------------------

    def _make_resident_tracker(self) -> Any:
        if self._custom_tracker_factory:
            return self._tracker_factory(self._algorithm, self._tracker_args)
        return make_resident_associator(self._algorithm, self._tracker_args, self.gmc_source)

    def _pose_homography(self, metadata: Mapping[str, Any]) -> Any:
        if not is_pose_source(self.gmc_source) or self._last_step_metadata is None:
            return None
        try:
            return pose_homography(self._last_step_metadata, metadata)
        except (TypeError, ValueError):
            self.pose_warp_skipped += 1
            return None

    def step(self, image: Any, frame_id: int, metadata: Mapping[str, Any]) -> FrameTracks:
        """每个传感器帧恰一次检测 + 关联（按 `gmc_source` 补偿）→ 写历史 → 返回该帧全部行。"""
        self._require(RESIDENT, "step")
        assert self._core is not None
        if isinstance(frame_id, bool) or not isinstance(frame_id, int):
            raise ProtocolMisuse("step() requires the integer sensor frame_id")
        if self._last_step_frame_id is not None and frame_id <= self._last_step_frame_id:
            raise ProtocolMisuse(f"step frame_id {frame_id} repeats or rolls back {self._last_step_frame_id}")
        if self._tracker is None:
            self._tracker = self._make_resident_tracker()
        homography = self._pose_homography(metadata)
        if homography is not None and hasattr(self._tracker, "set_pose_warp"):
            self._tracker.set_pose_warp(homography)
        width, height = image_size(image)
        removed_before = {int(t.track_id) for t in getattr(self._tracker, "removed_stracks", [])}
        rows = self._step(image)
        removed_after = {int(t.track_id) for t in getattr(self._tracker, "removed_stracks", [])}
        library_frame_id = int(self._tracker.frame_id)
        dropped: list[int] = []
        tracked, lost = rows_from_library(
            rows, list(getattr(self._tracker, "lost_stracks", [])), width, height, dropped=dropped
        )
        take = getattr(self._tracker, "take_prior_snapshots", None)
        prior_states = take() if callable(take) else None
        priors = tuple(
            snapshot_from_state(state, frame_id, library_frame_id, KF_PRIOR) for state in (prior_states or [])
        )
        posts = self._post_snapshots(frame_id, library_frame_id)
        unconfirmed = self._unconfirmed_rows(width, height, library_frame_id, dropped)
        tracked = [self._with_kf(row, posts) for row in tracked]
        lost = [self._with_kf(row, posts) for row in lost]
        unconfirmed = [self._with_kf(row, posts) for row in unconfirmed]
        entry = self._core.record(
            frame_id,
            metadata,
            tracked,
            lost,
            sorted(removed_after - removed_before),
            library_frame_id,
            unconfirmed_rows=unconfirmed,
            raw_detections=tuple(self._last_detections),
            prior_snapshots=priors,
            post_snapshots=posts,
            silently_dropped_ids=dropped,
            priors_available=prior_states is not None,
        )
        self._last_step_frame_id = frame_id
        self._last_step_metadata = dict(metadata)
        return FrameTracks(frame_id, entry.library_frame_id, entry.tracks, entry.removed_ids)

    def _post_snapshots(self, frame_id: int, library_frame_id: int) -> tuple[KfSnapshot, ...]:
        """`update` 返回后 tracked（含未确认）与 lost 的快照：本帧发生量测更新者 posterior，否则 prior。"""
        snapshots: list[KfSnapshot] = []
        for track in [*getattr(self._tracker, "tracked_stracks", []), *getattr(self._tracker, "lost_stracks", [])]:
            state = kf_state(track)
            if state is None:
                continue
            # 本帧匹配/重激活/新建的轨迹 `frame_id` = 库当前帧；未更新（含 lost）者保留旧帧号（mark_lost 不改它）。
            updated = getattr(track, "frame_id", None) == library_frame_id
            snapshots.append(snapshot_from_state(state, frame_id, library_frame_id, KF_POSTERIOR if updated else KF_PRIOR))
        return tuple(snapshots)

    def _unconfirmed_rows(self, width: int, height: int, library_frame_id: int, dropped: list[int]) -> list[TrackRow]:
        rows: list[TrackRow] = []
        for track in getattr(self._tracker, "tracked_stracks", []):
            if getattr(track, "is_activated", True):
                continue
            x1, y1, x2, y2 = (float(v) for v in track.xyxy)
            tracked, _lost = rows_from_library([[x1, y1, x2, y2, int(track.track_id), float(track.score), float(track.cls)]], [], width, height, dropped=dropped)
            if not tracked:
                continue
            index = int(getattr(track, "idx", -1)) if getattr(track, "frame_id", None) == library_frame_id else -1
            base = tracked[0]
            rows.append(TrackRow(base.track_id, base.box_norm, base.score, base.cls, UNCONFIRMED, matched_det_index=index))
        return rows

    @staticmethod
    def _with_kf(row: TrackRow, posts: Sequence[KfSnapshot]) -> TrackRow:
        snapshot = next((snap for snap in posts if snap.track_key == row.track_id), None)
        if snapshot is None:
            return TrackRow(row.track_id, row.box_norm, row.score, row.cls, row.state, row.matched_det_index, row.out_of_frame, None, "kf_unavailable")
        if not snapshot.valid:
            return TrackRow(row.track_id, row.box_norm, row.score, row.cls, row.state, row.matched_det_index, row.out_of_frame, None, snapshot.invalid_reason)
        return TrackRow(row.track_id, row.box_norm, row.score, row.cls, row.state, row.matched_det_index, row.out_of_frame, snapshot, None)

    def prior_snapshots(self, frame_id: int) -> tuple[KfSnapshot, ...] | None:
        """AR1-2 只读：该传感器帧补偿后、首轮关联前的 prior（深复制）；帧不在历史或未提供 → None。"""
        entry = self.history(frame_id)
        if entry is None or not entry.priors_available:
            return None
        return entry.prior_snapshots

    def post_snapshots(self, frame_id: int) -> tuple[KfSnapshot, ...] | None:
        entry = self.history(frame_id)
        return None if entry is None else entry.post_snapshots

    def pointer_result(self, frame_id: int) -> TrackerResult:
        self._require(RESIDENT, "pointer_result")
        assert self._core is not None
        return self._core.pointer_result(frame_id)

    def attach_frame_source(self, repository: Any, *, clock_key: str = "capture_monotonic_s") -> None:
        """第二级帧源 = 载体同一 `FrameRepository`（§3.4.1）；只读。"""
        self._require(RESIDENT, "attach_frame_source")
        assert self._core is not None
        self._frame_source = repository
        self._level2_runner = repository_level2_runner(
            repository,
            self._level2_factory,
            self._core.config,
            maximum_source_age_s=self._core.history_depth / self._capture_hz,
            clock_key=clock_key,
        )

    def designate(self, box_norm: Sequence[float], frame_id_k: int) -> Designation:
        """`designate(box, k)`：同帧历史匹配 → 第二级 k 帧起跟回放；六值闭集。不调用 `init`、不新建关联器。"""
        self._require(RESIDENT, "designate")
        assert self._core is not None
        return self._core.designate(box_norm, frame_id_k, self._level2_runner)

    def resolve_designation(self, box_norm: Sequence[float], frame_id_k: int, designation_id: int) -> Designation:
        """C5 纯解析（判据逐字同 `designate` 两级；第二级照旧注入 runner）；不改指针/coasting/计数。"""
        self._require(RESIDENT, "resolve_designation")
        assert self._core is not None
        return self._core.resolve_designation(box_norm, frame_id_k, self._level2_runner, designation_id)

    def follow(self, track_id: int | None) -> None:
        self._require(RESIDENT, "follow")
        assert self._core is not None
        self._core.follow(track_id)

    def pointer(self) -> int | None:
        self._require(RESIDENT, "pointer")
        assert self._core is not None
        return self._core.pointer()

    def history(self, frame_id: int) -> HistoryEntry | None:
        if self.mode != RESIDENT:
            return None
        assert self._core is not None
        return self._core.history(frame_id)

    @property
    def core(self) -> ResidentCore:
        self._require(RESIDENT, "core")
        assert self._core is not None
        return self._core

    @property
    def associator(self) -> Any:
        return self._tracker

    @property
    def library_frame_id(self) -> int:
        return int(self._tracker.frame_id) if self._tracker is not None else 0

    @property
    def bound_track_id(self) -> int | None:
        return self._bound_id

    def manifest_identity(self) -> Mapping[str, Any]:
        return {
            "name": self.name,
            "backend": self.backend,
            "pinned_version": self.version,
            "ultralytics_version": PINNED_ULTRALYTICS,
            "weights_sha256": self._weights_sha256,
            "spec_sha256": self._spec_sha256,
            "freeze_sha256": self._freeze_sha256,
            "imgsz": self._imgsz,
            "nms_iou": self._nms_iou,
            "score_threshold": self._conf,
            "threshold_source": "spec",
            "device": self._device,
            "device_fallback": self._device_fallback,
            "association": {"algorithm": self._algorithm, "args": dict(self._tracker_args)},
            "bind_iou": BIND_IOU,
            "class_policy": self.class_policy,
            "agnostic_nms": self.agnostic_nms,
            "mode": self.mode,
            "history_depth": self._core.history_depth if self._core is not None else None,
            "gmc_source": self.gmc_source if self.mode == RESIDENT else None,
            "resolver": self._core.config.as_record() if self._core is not None else None,
            "level2": self._level2_identity() if self.mode == RESIDENT else None,
        }

    def _level2_identity(self) -> dict[str, Any]:
        identity: dict[str, Any] = {"tracker": LEVEL2_TRACKER, "model_sha256": None, "t_replay_s": None}
        if self._core is not None:
            identity["t_replay_s"] = self._core.config.t_replay_s
            identity["l_replay_frames"] = self._core.config.l_replay_frames
        if self._level2_factory is _default_level2_factory:
            from .trackers import DEFAULT_NANOTRACK_V2_SPEC, load_nanotrack_v2_spec  # noqa: PLC0415

            try:
                spec = load_nanotrack_v2_spec(DEFAULT_NANOTRACK_V2_SPEC)
                identity["model_sha256"] = {role: spec["models"][role]["sha256"] for role in ("backbone", "neckhead")}
            except (OSError, ValueError):
                identity["model_sha256"] = "spec_unavailable"
        else:
            identity["model_sha256"] = "injected_factory"
        return identity
