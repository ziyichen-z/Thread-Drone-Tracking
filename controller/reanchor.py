from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import threading
import time
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

from .trackers import BoxNorm, TrackerPlugin, TrackerResult, clip_box_norm


SCHEMA_VERSION = "tethered-detector-reanchor/v1"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "detector-reanchor.models.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"{label} keys mismatch; missing={missing}, extra={extra}")


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0.0):
        raise ValueError(f"{label} must be finite" + (" and positive" if positive else ""))
    return result


def _digest(value: Any, label: str) -> str:
    text = str(value)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return text


def _resolve_project_path(value: Any, label: str) -> Path:
    text = str(value)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must be a project-relative path")
    resolved = (PROJECT_ROOT / path).resolve()
    if not resolved.is_relative_to(PROJECT_ROOT):
        raise ValueError(f"{label} resolves outside the project")
    return resolved


@dataclass(frozen=True)
class ReanchorConfig:
    path: Path
    raw: Mapping[str, Any]
    sha256: str

    @property
    def parameters(self) -> Mapping[str, Any]:
        return _mapping(self.raw["parameters"], "parameters")

    @property
    def detector(self) -> Mapping[str, Any]:
        return _mapping(self.raw["detector"], "detector")

    @property
    def appearance(self) -> Mapping[str, Any]:
        return _mapping(self.raw["appearance"], "appearance")

    @property
    def tracker_factory(self) -> Mapping[str, Any]:
        return _mapping(self.raw["tracker_factory"], "tracker_factory")

    def identity(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "carrier": self.raw["carrier"],
            "config_path": str(self.path),
            "config_sha256": self.sha256,
            "runtime": dict(_mapping(self.raw["runtime"], "runtime")),
            "detector": dict(self.detector),
            "appearance": dict(self.appearance),
            "tracker_factory": dict(self.tracker_factory),
            "parameters": dict(self.parameters),
        }


def load_reanchor_config(path: Path = DEFAULT_CONFIG) -> ReanchorConfig:
    path = Path(path).resolve()
    value = json.loads(path.read_text(encoding="utf-8"))
    root = _mapping(value, "config")
    _strict_keys(
        root,
        {
            "schema_version",
            "carrier",
            "runtime",
            "detector",
            "appearance",
            "tracker_factory",
            "parameters",
        },
        "config",
    )
    if root["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"unsupported reanchor config {root['schema_version']!r}")
    if root["carrier"] != "minimal-triple-gated-re-anchor":
        raise ValueError("unexpected carrier")
    runtime = _mapping(root["runtime"], "runtime")
    _strict_keys(runtime, {"torch_pin", "torchvision_pin", "ultralytics_pin", "device"}, "runtime")
    if dict(runtime) != {
        "torch_pin": "2.13.0",
        "torchvision_pin": "0.28.0",
        "ultralytics_pin": "8.4.104",
        "device": "cpu",
    }:
        raise ValueError("runtime pins differ from the accepted design")
    detector = _mapping(root["detector"], "detector")
    _strict_keys(
        detector,
        {
            "name", "path", "size_bytes", "sha256", "predictor",
            "score_contract", "box_contract", "image_size_px",
        },
        "detector",
    )
    if (
        detector["name"] != "yoloe-11s-seg"
        or detector["predictor"] != "ultralytics.models.yolo.yoloe.YOLOEVPSegPredictor"
        or detector["score_contract"] != "Results.boxes.conf"
        or detector["box_contract"] != "Results.boxes.xyxy"
        or int(detector["image_size_px"]) != 640
    ):
        raise ValueError("detector contract differs from the accepted design")
    appearance = _mapping(root["appearance"], "appearance")
    _strict_keys(
        appearance,
        {
            "name", "variant", "embedding_contract", "embedding_dimensions",
            "source", "weights", "preprocessing",
        },
        "appearance",
    )
    source = _mapping(appearance["source"], "appearance.source")
    _strict_keys(
        source,
        {
            "repository", "commit", "tree_url", "archive_url", "archive_path",
            "archive_size_bytes", "archive_sha256", "directory",
            "license_spdx", "license_path", "license_size_bytes",
            "license_sha256", "license_statement_url", "excluded_variants",
        },
        "appearance.source",
    )
    commit = str(source["commit"])
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("appearance.source.commit must be a full lowercase Git SHA")
    if source["license_spdx"] != "Apache-2.0":
        raise ValueError("DINOv2 code and standard weights must be Apache-2.0")
    if (
        appearance["name"] != "dinov2_vits14"
        or appearance["variant"] != "LVD142M-no-registers-backbone"
        or appearance["embedding_contract"] != "forward_features.x_norm_clstoken"
        or int(appearance["embedding_dimensions"]) != 384
        or source["repository"] != "https://github.com/facebookresearch/dinov2"
        or commit != "7764ea0f912e53c92e82eb78a2a1631e92725fc8"
        or source["archive_url"]
        != f"https://codeload.github.com/facebookresearch/dinov2/tar.gz/{commit}"
    ):
        raise ValueError("DINOv2 identity differs from the accepted design")
    excluded = source["excluded_variants"]
    if not isinstance(excluded, list) or set(excluded) != {
        "XRay-DINO", "Cell-DINO", "Channel-Adaptive-DINO"
    }:
        raise ValueError("special nonstandard DINO variants must be explicitly excluded")
    weights = _mapping(appearance["weights"], "appearance.weights")
    _strict_keys(weights, {"url", "path", "size_bytes", "sha256"}, "appearance.weights")
    if weights["url"] != "https://dl.fbaipublicfiles.com/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth":
        raise ValueError("DINOv2 weight URL differs from the accepted design")
    preprocessing = _mapping(appearance["preprocessing"], "appearance.preprocessing")
    _strict_keys(
        preprocessing,
        {
            "id", "input", "resize_px", "crop_px", "interpolation",
            "antialias", "mean", "std", "minimum_crop_side_px",
        },
        "appearance.preprocessing",
    )
    if (
        preprocessing["input"] != "PIL-RGB-uint8"
        or preprocessing["interpolation"] != "BICUBIC"
        or preprocessing["antialias"] != "PIL-fixed"
        or int(preprocessing["resize_px"]) != 256
        or int(preprocessing["crop_px"]) != 224
        or list(preprocessing["mean"]) != [0.485, 0.456, 0.406]
        or list(preprocessing["std"]) != [0.229, 0.224, 0.225]
        or int(preprocessing["minimum_crop_side_px"]) != 2
    ):
        raise ValueError("DINOv2 preprocessing contract mismatch")
    factory = _mapping(root["tracker_factory"], "tracker_factory")
    _strict_keys(factory, {"name", "spec", "model_dir"}, "tracker_factory")
    if factory["name"] != "nanotrack-v2":
        raise ValueError("reanchor tracker factory must be nanotrack-v2")
    if (
        factory["spec"] != "config/nanotrack-v2.models.json"
        or factory["model_dir"] != "runtime/models/nanotrack-v2"
    ):
        raise ValueError("reanchor tracker factory identity mismatch")
    params = _mapping(root["parameters"], "parameters")
    required_params = {
        "cadence_s", "detector_threshold", "reid_threshold", "ambiguity_margin",
        "agree_iou_threshold", "disagree_rounds", "round_consistency_rad",
        "motion_base_rad", "motion_rate_rad_s", "target_speed_heuristic_mps",
        "minimum_range_heuristic_m", "maximum_result_age_s",
        "minimum_reseed_interval_rounds", "frame_buffer_s", "catchup_timeout_s",
        "consecutive_failure_limit", "worker_timeout_s", "worker_join_timeout_s",
        "cadence_completion_minimum", "basis_tolerance", "quaternion_tolerance",
    }
    _strict_keys(params, required_params, "parameters")
    for key, raw in params.items():
        _number(raw, f"parameters.{key}", positive=True)
    expected_params = {
        "cadence_s": 2.0,
        "detector_threshold": 0.25,
        "reid_threshold": 0.5,
        "ambiguity_margin": 0.1,
        "agree_iou_threshold": 0.3,
        "disagree_rounds": 2,
        "round_consistency_rad": 0.05,
        "motion_base_rad": 0.1,
        "motion_rate_rad_s": 0.5,
        "target_speed_heuristic_mps": 4.0,
        "minimum_range_heuristic_m": 8.0,
        "maximum_result_age_s": 2.0,
        "minimum_reseed_interval_rounds": 2,
        "frame_buffer_s": 6.0,
        "catchup_timeout_s": 2.0,
        "consecutive_failure_limit": 3,
        "worker_timeout_s": 10.0,
        "worker_join_timeout_s": 1.0,
        "cadence_completion_minimum": 0.8,
        "basis_tolerance": 0.001,
        "quaternion_tolerance": 0.001,
    }
    if any(float(params[key]) != expected for key, expected in expected_params.items()):
        raise ValueError("parameters differ from the accepted frozen values")
    if int(params["disagree_rounds"]) != 2 or int(params["consecutive_failure_limit"]) != 3:
        raise ValueError("frozen integer parameters mismatch")
    if not 0.0 < float(params["cadence_completion_minimum"]) <= 1.0:
        raise ValueError("cadence completion minimum must be in (0,1]")
    for mapping, prefix in ((detector, "detector"), (source, "appearance.source"), (weights, "appearance.weights")):
        for key in tuple(mapping):
            if key.endswith("sha256"):
                _digest(mapping[key], f"{prefix}.{key}")
    return ReanchorConfig(path, dict(root), sha256_file(path))


def verify_file(path: Path, *, size_bytes: int, sha256: str, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{label} is missing: {path}")
    actual_size = path.stat().st_size
    if actual_size != int(size_bytes):
        raise ValueError(f"{label} size mismatch: expected {size_bytes}, got {actual_size}")
    actual_hash = sha256_file(path)
    if actual_hash != sha256:
        raise ValueError(f"{label} SHA-256 mismatch: expected {sha256}, got {actual_hash}")


Vector3 = tuple[float, float, float]


def _vector(metadata: Mapping[str, Any], key: str) -> Vector3:
    value = metadata.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 3:
        raise ValueError(f"{key} must contain three values")
    result = tuple(_number(part, f"{key}[{index}]") for index, part in enumerate(value))
    return result  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(float(a) * float(b) for a, b in zip(left, right))


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _normalize(vector: Sequence[float], label: str) -> Vector3:
    length = _norm(vector)
    if not math.isfinite(length) or length <= 0.0:
        raise ValueError(f"{label} must have finite nonzero norm")
    return tuple(float(value) / length for value in vector)  # type: ignore[return-value]


def _rotate_quaternion(vector: Vector3, quaternion: Sequence[float]) -> Vector3:
    x, y, z, w = (float(value) for value in quaternion)
    vx, vy, vz = vector
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)
    return (
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    )


def validate_camera_basis(
    metadata: Mapping[str, Any],
    *,
    basis_tolerance: float = 0.001,
    quaternion_tolerance: float = 0.001,
) -> tuple[Vector3, Vector3, Vector3]:
    right = _vector(metadata, "camera_right_world")
    up = _vector(metadata, "camera_up_world")
    forward = _vector(metadata, "camera_forward_world")
    for name, vector in (("right", right), ("up", up), ("forward", forward)):
        if abs(_norm(vector) - 1.0) > basis_tolerance:
            raise ValueError(f"camera {name} basis is not normalized")
    if any(abs(_dot(a, b)) > basis_tolerance for a, b in ((right, up), (right, forward), (up, forward))):
        raise ValueError("camera basis is not orthogonal")
    quaternion = metadata.get("camera_rotation_xyzw")
    if not isinstance(quaternion, Sequence) or isinstance(quaternion, (str, bytes)) or len(quaternion) != 4:
        raise ValueError("camera_rotation_xyzw must contain four values")
    q = tuple(_number(value, f"camera_rotation_xyzw[{index}]") for index, value in enumerate(quaternion))
    if abs(_norm(q) - 1.0) > quaternion_tolerance:
        raise ValueError("camera quaternion is not normalized")
    expected = (
        _rotate_quaternion((1.0, 0.0, 0.0), q),
        _rotate_quaternion((0.0, 1.0, 0.0), q),
        _rotate_quaternion((0.0, 0.0, 1.0), q),
    )
    for actual, calculated, label in zip((right, up, forward), expected, ("right", "up", "forward")):
        if _norm(tuple(a - b for a, b in zip(actual, calculated))) > quaternion_tolerance:
            raise ValueError(f"camera quaternion/{label} basis mismatch")
    return right, up, forward


def world_los(
    box_norm: Sequence[float],
    metadata: Mapping[str, Any],
    *,
    basis_tolerance: float = 0.001,
    quaternion_tolerance: float = 0.001,
) -> Vector3:
    box = clip_box_norm(box_norm)
    if box is None:
        raise ValueError("box is invalid")
    width = int(metadata.get("width", 0))
    height = int(metadata.get("height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("frame dimensions must be positive")
    intrinsics = _mapping(metadata.get("intrinsics_px"), "intrinsics_px")
    fx = _number(intrinsics.get("fx"), "intrinsics_px.fx", positive=True)
    fy = _number(intrinsics.get("fy"), "intrinsics_px.fy", positive=True)
    cx = _number(intrinsics.get("cx"), "intrinsics_px.cx")
    cy = _number(intrinsics.get("cy"), "intrinsics_px.cy")
    right, up, forward = validate_camera_basis(
        metadata,
        basis_tolerance=basis_tolerance,
        quaternion_tolerance=quaternion_tolerance,
    )
    x, y, w, h = box
    u = (x + 0.5 * w) * width
    v = (y + 0.5 * h) * height
    return _normalize(
        tuple(
            ((u - cx) / fx) * right[index]
            - ((v - cy) / fy) * up[index]
            + forward[index]
            for index in range(3)
        ),
        "world LOS",
    )


def angular_distance(left: Sequence[float], right: Sequence[float]) -> float:
    return math.acos(max(-1.0, min(1.0, _dot(_normalize(left, "left"), _normalize(right, "right")))))


def box_iou(left: Sequence[float], right: Sequence[float]) -> float:
    a = clip_box_norm(left)
    b = clip_box_norm(right)
    if a is None or b is None:
        return 0.0
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    intersection = max(0.0, min(ax + aw, bx + bw) - max(ax, bx)) * max(
        0.0, min(ay + ah, by + bh) - max(ay, by)
    )
    union = aw * ah + bw * bh - intersection
    return 0.0 if union <= 0.0 else intersection / union


def valid_replay_box(box_norm: Sequence[float] | None) -> bool:
    if (
        box_norm is None
        or isinstance(box_norm, (str, bytes))
        or len(box_norm) != 4
    ):
        return False
    try:
        x, y, width, height = (float(value) for value in box_norm)
    except (TypeError, ValueError):
        return False
    return (
        all(math.isfinite(value) for value in (x, y, width, height))
        and x >= 0.0
        and y >= 0.0
        and width > 0.0
        and height > 0.0
        and x + width <= 1.0
        and y + height <= 1.0
    )


@dataclass(frozen=True)
class Candidate:
    index: int
    box_norm: BoxNorm
    detector_confidence: float
    reid_cosine: float
    world_los: Vector3
    motion_angle_rad: float


@dataclass(frozen=True)
class GateAnchor:
    los_world: Vector3
    capture_monotonic_s: float


@dataclass(frozen=True)
class RoundDecision:
    outcome: str
    winner: Candidate | None
    margin: float | None
    tentative: tuple[Candidate, ...]
    trigger_reseed: bool
    reset_disagree: bool


class TripleGateState:
    def __init__(self, config: ReanchorConfig):
        p = config.parameters
        self.detector_threshold = float(p["detector_threshold"])
        self.reid_threshold = float(p["reid_threshold"])
        self.margin_threshold = float(p["ambiguity_margin"])
        self.agree_iou_threshold = float(p["agree_iou_threshold"])
        self.motion_base_rad = float(p["motion_base_rad"])
        self.motion_rate_rad_s = float(p["motion_rate_rad_s"])
        self.round_consistency_rad = float(p["round_consistency_rad"])
        self.disagree_rounds_required = int(p["disagree_rounds"])
        self.minimum_reseed_interval_rounds = int(p["minimum_reseed_interval_rounds"])
        self.anchor: GateAnchor | None = None
        self._disagree_count = 0
        self._previous_winner: Candidate | None = None
        self._previous_capture_s: float | None = None
        self._round_index = 0
        self._last_reseed_round = -10**9

    @property
    def disagree_count(self) -> int:
        return self._disagree_count

    def set_anchor(self, los_world: Vector3, capture_monotonic_s: float) -> None:
        self.anchor = GateAnchor(_normalize(los_world, "anchor"), _number(capture_monotonic_s, "capture_monotonic_s"))

    def evaluate(
        self,
        candidates: Sequence[Candidate],
        *,
        sot_box_norm: Sequence[float] | None,
        capture_monotonic_s: float,
        class_candidate_count: int | None = None,
        crop_invalid_count: int = 0,
        lost: bool = False,
    ) -> RoundDecision:
        self._round_index += 1
        capture = _number(capture_monotonic_s, "capture_monotonic_s")
        if self.anchor is None:
            raise RuntimeError("motion anchor is unavailable")
        passed = [
            candidate
            for candidate in candidates
            if candidate.detector_confidence >= self.detector_threshold
            and candidate.reid_cosine >= self.reid_threshold
            and candidate.motion_angle_rad
            <= min(math.pi, self.motion_base_rad + self.motion_rate_rad_s * max(0.0, capture - self.anchor.capture_monotonic_s))
        ]
        tentative = tuple(candidate for candidate in candidates if candidate not in passed)
        if not passed:
            self._disagree_count = 0
            self._previous_winner = None
            self._previous_capture_s = None
            if crop_invalid_count and (class_candidate_count or 0) > 0:
                return RoundDecision("TENTATIVE_CROP_INVALID", None, None, tentative, False, True)
            if (class_candidate_count if class_candidate_count is not None else len(candidates)) == 0:
                return RoundDecision("NO_CANDIDATE", None, None, tentative, False, True)
            return RoundDecision("TENTATIVE", None, None, tentative, False, True)
        ranked = sorted(
            passed,
            key=lambda item: (
                -item.reid_cosine,
                -item.detector_confidence,
                item.motion_angle_rad,
                item.index,
            ),
        )
        margin = ranked[0].reid_cosine - ranked[1].reid_cosine if len(ranked) >= 2 else None
        if margin is not None and margin < self.margin_threshold:
            self._disagree_count = 0
            self._previous_winner = None
            self._previous_capture_s = None
            return RoundDecision("AMBIGUOUS", ranked[0], margin, tuple(ranked), False, True)
        winner = ranked[0]
        if not lost and sot_box_norm is not None and box_iou(winner.box_norm, sot_box_norm) >= self.agree_iou_threshold:
            self.set_anchor(winner.world_los, capture)
            self._disagree_count = 0
            self._previous_winner = None
            self._previous_capture_s = None
            return RoundDecision("AGREE", winner, margin, tentative, False, True)
        consistent = True
        if self._previous_winner is not None and self._previous_capture_s is not None:
            dt = max(0.0, capture - self._previous_capture_s)
            consistent = angular_distance(winner.world_los, self._previous_winner.world_los) <= (
                self.motion_rate_rad_s * dt + self.round_consistency_rad
            )
        self._disagree_count = self._disagree_count + 1 if consistent else 1
        self._previous_winner = winner
        self._previous_capture_s = capture
        spacing_ok = self._round_index - self._last_reseed_round >= self.minimum_reseed_interval_rounds
        trigger = (lost or self._disagree_count >= self.disagree_rounds_required) and spacing_ok
        return RoundDecision("DISAGREE", winner, margin, tentative, trigger, False)

    def reseed_succeeded(self, los_world: Vector3, capture_monotonic_s: float) -> None:
        self.set_anchor(los_world, capture_monotonic_s)
        self._last_reseed_round = self._round_index
        self._disagree_count = 0
        self._previous_winner = None
        self._previous_capture_s = None


@dataclass(frozen=True)
class BufferedFrame:
    frame_id: int
    capture_monotonic_s: float
    image: Any
    metadata: Mapping[str, Any]
    sot_box_norm: BoxNorm | None


class FrameHistory:
    def __init__(self, duration_s: float):
        self.duration_s = _number(duration_s, "duration_s", positive=True)
        self._frames: deque[BufferedFrame] = deque()

    def append(self, frame: BufferedFrame) -> None:
        if self._frames and frame.frame_id <= self._frames[-1].frame_id:
            raise ValueError("frame history ids must be strictly increasing")
        if (
            self._frames
            and frame.capture_monotonic_s
            <= self._frames[-1].capture_monotonic_s
        ):
            raise ValueError("frame history capture times must be strictly increasing")
        image = frame.image.copy() if hasattr(frame.image, "copy") else frame.image
        flags = getattr(image, "flags", None)
        if flags is not None:
            try:
                flags.writeable = False
            except Exception:
                pass
        frozen = BufferedFrame(
            frame.frame_id,
            _number(frame.capture_monotonic_s, "capture_monotonic_s"),
            image,
            _freeze_mapping(frame.metadata),
            frame.sot_box_norm,
        )
        self._frames.append(frozen)
        cutoff = frozen.capture_monotonic_s - self.duration_s
        while self._frames and self._frames[0].capture_monotonic_s < cutoff:
            self._frames.popleft()

    @property
    def head_frame_id(self) -> int | None:
        return self._frames[-1].frame_id if self._frames else None

    def get(self, frame_id: int) -> BufferedFrame | None:
        return next((frame for frame in self._frames if frame.frame_id == frame_id), None)

    def after_through(self, start_exclusive: int, end_inclusive: int) -> tuple[BufferedFrame, ...]:
        frames = tuple(frame for frame in self._frames if start_exclusive < frame.frame_id <= end_inclusive)
        expected = tuple(range(start_exclusive + 1, end_inclusive + 1))
        if tuple(frame.frame_id for frame in frames) != expected:
            raise FileNotFoundError("replay intermediate frame missing")
        return frames

    def snapshot(self) -> "FrameHistory":
        clone = FrameHistory(self.duration_s)
        clone._frames = deque(self._frames)
        return clone


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        {str(key): _freeze_value(item) for key, item in value.items()}
    )


@dataclass(frozen=True)
class ReplayResult:
    event: str
    tracker: TrackerPlugin | None
    source_frame_id: int
    head_frame_id: int | None
    replay_count: int
    elapsed_ms: float
    last_result: TrackerResult | None
    reason: str | None = None


def replay_tracker(
    tracker_factory: Callable[[], TrackerPlugin],
    history: FrameHistory,
    *,
    source_frame_id: int,
    source_box_norm: Sequence[float],
    target_head_frame_id: int,
    maximum_source_age_s: float,
    catchup_timeout_s: float,
    monotonic: Callable[[], float] = time.monotonic,
) -> ReplayResult:
    started = monotonic()
    source = history.get(source_frame_id)
    if source is None:
        return ReplayResult("RESEED_DISCARDED_MISSING_FRAME", None, source_frame_id, None, 0, 0.0, None, "source_frame_missing")
    head = history.get(target_head_frame_id)
    if head is None:
        return ReplayResult("RESEED_DISCARDED_MISSING_FRAME", None, source_frame_id, None, 0, 0.0, None, "target_frame_missing")
    if head.capture_monotonic_s - source.capture_monotonic_s > maximum_source_age_s:
        return ReplayResult("RESEED_DISCARDED_STALE", None, source_frame_id, None, 0, 0.0, None, "source_result_too_old")
    try:
        tracker = tracker_factory()
        if not valid_replay_box(source_box_norm):
            return ReplayResult("RESEED_DISCARDED_INVALID_BOX", None, source_frame_id, None, 0, (monotonic() - started) * 1000.0, None, "invalid_source_box")
        if not tracker.init(source.image, source_box_norm):
            return ReplayResult("RESEED_FAILED", None, source_frame_id, None, 0, (monotonic() - started) * 1000.0, None, "tracker_init_failed")
        replay_count = 0
        last_result: TrackerResult | None = TrackerResult(clip_box_norm(source_box_norm), True, 1.0, "placeholder")
        for frame in history.after_through(source_frame_id, target_head_frame_id):
            if monotonic() - started > catchup_timeout_s:
                return ReplayResult("RESEED_DISCARDED_NOT_CONVERGED", None, source_frame_id, frame.frame_id - 1, replay_count, (monotonic() - started) * 1000.0, last_result, "catchup_timeout")
            last_result = tracker.update(frame.image)
            replay_count += 1
            if not last_result.ok or not valid_replay_box(last_result.box_norm):
                return ReplayResult("RESEED_DISCARDED_INVALID_BOX", None, source_frame_id, frame.frame_id, replay_count, (monotonic() - started) * 1000.0, last_result, "invalid_replay_box")
        return ReplayResult("RESEED_READY", tracker, source_frame_id, target_head_frame_id, replay_count, (monotonic() - started) * 1000.0, last_result)
    except FileNotFoundError:
        return ReplayResult("RESEED_DISCARDED_MISSING_FRAME", None, source_frame_id, None, 0, (monotonic() - started) * 1000.0, None, "intermediate_frame_missing")
    except Exception as exception:
        return ReplayResult("RESEED_FAILED", None, source_frame_id, None, 0, (monotonic() - started) * 1000.0, None, f"{type(exception).__name__}")


@dataclass(frozen=True)
class WorkerMessage:
    event: str
    payload: Any
    started_monotonic_s: float
    completed_monotonic_s: float | None
    reason: str | None = None


class SingleFlightWorker:
    """One daemon worker, zero queue. Persistence remains main-thread owned."""

    def __init__(
        self,
        *,
        timeout_s: float,
        failure_limit: int,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        self.timeout_s = _number(timeout_s, "timeout_s", positive=True)
        self.failure_limit = int(failure_limit)
        self.monotonic = monotonic
        self._thread: threading.Thread | None = None
        self._result: WorkerMessage | None = None
        self._lock = threading.Lock()
        self._started: float | None = None
        self._timed_out = False
        self._restart_used = False
        self._dead_permanently = False
        self.consecutive_failures = 0

    @property
    def busy(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def submit(self, function: Callable[[], Any]) -> WorkerMessage:
        with self._lock:
            if self._dead_permanently:
                now = self.monotonic()
                return WorkerMessage("WORKER_RESTART_EXHAUSTED", None, now, now, "worker_restart_budget_exhausted")
            if self._thread is not None:
                now = self.monotonic()
                return WorkerMessage("ROUND_SKIPPED_BUSY", None, now, now, "single_in_flight")
            self._result = None
            self._timed_out = False
            self._started = self.monotonic()

            def target() -> None:
                try:
                    payload = function()
                    message = WorkerMessage("ROUND_COMPLETE", payload, self._started or 0.0, self.monotonic())
                except BaseException as exception:
                    message = WorkerMessage("ROUND_FAILED", None, self._started or 0.0, self.monotonic(), type(exception).__name__)
                with self._lock:
                    self._result = message

            self._thread = threading.Thread(target=target, name="reanchor-worker", daemon=True)
            self._thread.start()
            return WorkerMessage("ROUND_STARTED", None, self._started, None)

    def poll(self) -> WorkerMessage | None:
        with self._lock:
            thread = self._thread
            if thread is None:
                return None
            now = self.monotonic()
            if thread.is_alive():
                if self._started is not None and now - self._started > self.timeout_s and not self._timed_out:
                    self._timed_out = True
                    self.consecutive_failures += 1
                    return WorkerMessage("ROUND_TIMEOUT", None, self._started, now, "worker_still_alive")
                return None
            message = self._result or WorkerMessage("WORKER_DIED", None, self._started or now, now, "no_result")
            self._thread = None
            self._result = None
            if self._timed_out:
                return WorkerMessage(
                    "ROUND_FAILED_AFTER_TIMEOUT",
                    None,
                    message.started_monotonic_s,
                    message.completed_monotonic_s,
                    "completed_after_timeout",
                )
            if message.event == "ROUND_COMPLETE":
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
                if message.event == "WORKER_DIED" and not self._restart_used:
                    self._restart_used = True
                    message = WorkerMessage("WORKER_DIED_RESTART_ALLOWED", None, message.started_monotonic_s, message.completed_monotonic_s, message.reason)
                elif message.event == "WORKER_DIED":
                    self._dead_permanently = True
                    self.consecutive_failures = self.failure_limit
            return message

    @property
    def fail_closed(self) -> bool:
        return self.consecutive_failures >= self.failure_limit

    @property
    def timed_out_alive(self) -> bool:
        return self._timed_out and self.busy

    def close(self, join_timeout_s: float) -> bool:
        thread = self._thread
        if thread is None:
            return True
        thread.join(_number(join_timeout_s, "join_timeout_s", positive=True))
        return not thread.is_alive()
