from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence


BoxNorm = tuple[float, float, float, float]
BoxPixels = tuple[float, float, float, float]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NANOTRACK_V2_SPEC = (
    PROJECT_ROOT / "config" / "nanotrack-v2.models.json"
)
DEFAULT_NANOTRACK_V2_MODEL_DIR = (
    PROJECT_ROOT / "runtime" / "models" / "nanotrack-v2"
)
MODEL_SPEC_SCHEMA = "tethered-tracker-models/v1"


@dataclass(frozen=True)
class TrackerResult:
    box_norm: BoxNorm | None
    ok: bool
    confidence: float | None = None
    confidence_source: str = "none"
    reason: str | None = None

    @classmethod
    def lost(cls, reason: str) -> "TrackerResult":
        return cls(None, False, None, "none", reason)


class TrackerPlugin(Protocol):
    name: str
    backend: str
    version: str

    def init(self, image: Any, box_norm: Sequence[float]) -> bool:
        ...

    def update(self, image: Any) -> TrackerResult:
        ...

    def manifest_identity(self) -> Mapping[str, Any]:
        ...


def _finite_box(box: Sequence[float], label: str) -> BoxNorm:
    if len(box) != 4:
        raise ValueError(f"{label} must contain x, y, width, height")
    result = tuple(float(value) for value in box)
    if not all(math.isfinite(value) for value in result):
        raise ValueError(f"{label} must contain only finite values")
    return result  # type: ignore[return-value]


def clip_box_norm(box: Sequence[float]) -> BoxNorm | None:
    x, y, width, height = _finite_box(box, "box_norm")
    if width <= 0.0 or height <= 0.0:
        return None
    left = max(0.0, x)
    top = max(0.0, y)
    right = min(1.0, x + width)
    bottom = min(1.0, y + height)
    if right <= left or bottom <= top:
        return None
    return left, top, right - left, bottom - top


def norm_to_pixels(
    box_norm: Sequence[float],
    image_width: int,
    image_height: int,
) -> BoxPixels:
    if image_width <= 0 or image_height <= 0:
        raise ValueError("image dimensions must be positive")
    clipped = clip_box_norm(box_norm)
    if clipped is None:
        raise ValueError("box_norm is degenerate or outside the image")
    x, y, width, height = clipped
    return (
        x * image_width,
        y * image_height,
        width * image_width,
        height * image_height,
    )


def norm_to_csrt_pixels(
    box_norm: Sequence[float],
    image_width: int,
    image_height: int,
) -> tuple[int, int, int, int]:
    x, y, width, height = norm_to_pixels(
        box_norm, image_width, image_height
    )
    left = max(0, min(image_width - 1, math.floor(x)))
    top = max(0, min(image_height - 1, math.floor(y)))
    right = max(left + 1, min(image_width, math.ceil(x + width - 1e-9)))
    bottom = max(top + 1, min(image_height, math.ceil(y + height - 1e-9)))
    return left, top, right - left, bottom - top


def pixels_to_norm(
    box_pixels: Sequence[float],
    image_width: int,
    image_height: int,
) -> BoxNorm | None:
    if image_width <= 0 or image_height <= 0:
        raise ValueError("image dimensions must be positive")
    x, y, width, height = _finite_box(box_pixels, "box_pixels")
    return clip_box_norm(
        (
            x / image_width,
            y / image_height,
            width / image_width,
            height / image_height,
        )
    )


def pixels_to_norm_unclipped(
    box_pixels: Sequence[float],
    image_width: int,
    image_height: int,
) -> BoxNorm:
    if image_width <= 0 or image_height <= 0:
        raise ValueError("image dimensions must be positive")
    x, y, width, height = _finite_box(box_pixels, "box_pixels")
    return (
        x / image_width,
        y / image_height,
        width / image_width,
        height / image_height,
    )


def image_size(image: Any) -> tuple[int, int]:
    shape = getattr(image, "shape", None)
    if shape is None or len(shape) < 2:
        raise ValueError("tracker image must expose a height/width shape")
    height = int(shape[0])
    width = int(shape[1])
    if width <= 0 or height <= 0:
        raise ValueError("tracker image dimensions must be positive")
    return width, height


def create_csrt_backend(cv2_module: Any) -> Any:
    constructor = getattr(cv2_module, "TrackerCSRT_create", None)
    if callable(constructor):
        return constructor()
    legacy = getattr(cv2_module, "legacy", None)
    constructor = getattr(legacy, "TrackerCSRT_create", None)
    if callable(constructor):
        return constructor()
    raise RuntimeError(
        "installed cv2 does not expose TrackerCSRT_create; "
        "install the pinned opencv-contrib-python package"
    )


class CsrtTracker:
    name = "csrt"
    backend = "opencv"

    def __init__(self, cv2_module: Any | None = None):
        if cv2_module is None:
            try:
                import cv2 as cv2_module
            except ImportError as exception:
                raise RuntimeError(
                    "cv2 is unavailable; activate .venv-track and install "
                    "tools/requirements-track.txt"
                ) from exception
        self._cv2 = cv2_module
        self.version = str(getattr(cv2_module, "__version__", "unknown"))
        self._tracker: Any | None = None

    def init(self, image: Any, box_norm: Sequence[float]) -> bool:
        width, height = image_size(image)
        box_pixels = norm_to_csrt_pixels(box_norm, width, height)
        tracker = create_csrt_backend(self._cv2)
        initialized = tracker.init(image, box_pixels)
        if initialized is False:
            self._tracker = None
            return False
        self._tracker = tracker
        return True

    def update(self, image: Any) -> TrackerResult:
        if self._tracker is None:
            return TrackerResult.lost("tracker_not_initialized")
        width, height = image_size(image)
        try:
            ok, box_pixels = self._tracker.update(image)
        except Exception as exception:
            return TrackerResult.lost(
                f"tracker_update_error:{type(exception).__name__}"
            )
        if not bool(ok):
            return TrackerResult.lost("tracker_reported_failure")
        try:
            box_norm = pixels_to_norm(box_pixels, width, height)
        except (TypeError, ValueError):
            return TrackerResult.lost("invalid_tracker_box")
        if box_norm is None:
            return TrackerResult.lost("invalid_tracker_box")
        return TrackerResult(
            box_norm=box_norm,
            ok=True,
            confidence=1.0,
            confidence_source="placeholder",
        )

    def manifest_identity(self) -> Mapping[str, Any]:
        return {
            "name": self.name,
            "backend": self.backend,
            "pinned_version": self.version,
            "opencv_version": self.version,
            "model_sha256": None,
            "score_threshold": None,
            "threshold_source": "none",
            "preprocessing_id": "opencv-csrt-native",
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _required_string(mapping: Mapping[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}.{key} must be a non-empty string")
    return value


def load_nanotrack_v2_spec(path: Path) -> dict[str, Any]:
    path = Path(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exception:
        raise FileNotFoundError(f"NanoTrack-v2 model spec is missing: {path}") from exception
    except json.JSONDecodeError as exception:
        raise ValueError(f"NanoTrack-v2 model spec is invalid JSON: {path}") from exception
    spec = dict(_required_mapping(value, "model spec"))
    if spec.get("schema_version") != MODEL_SPEC_SCHEMA:
        raise ValueError(
            f"unsupported NanoTrack-v2 model spec schema "
            f"{spec.get('schema_version')!r}"
        )
    if spec.get("tracker") != "nanotrack-v2":
        raise ValueError("model spec tracker must be 'nanotrack-v2'")

    source = _required_mapping(spec.get("source"), "model spec.source")
    for key in (
        "repository",
        "commit",
        "tree_url",
        "license_path",
        "license_url",
        "license_sha256",
    ):
        _required_string(source, key, "model spec.source")
    commit = str(source["commit"])
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise ValueError("model spec.source.commit must be a lowercase 40-character Git SHA")
    if source.get("license_spdx") != "Apache-2.0":
        raise ValueError("NanoTrack-v2 artifact license must be Apache-2.0")
    license_digest = str(source["license_sha256"])
    if len(license_digest) != 64 or any(
        character not in "0123456789abcdef" for character in license_digest
    ):
        raise ValueError(
            "model spec.source.license_sha256 must be a lowercase SHA-256"
        )

    opencv = _required_mapping(spec.get("opencv"), "model spec.opencv")
    for key in (
        "tested_version",
        "package_pin",
        "dnn_backend",
        "dnn_target",
    ):
        _required_string(opencv, key, "model spec.opencv")
    if opencv.get("dnn_backend") != "DNN_BACKEND_DEFAULT":
        raise ValueError("NanoTrack-v2 requires DNN_BACKEND_DEFAULT")
    if opencv.get("dnn_target") != "DNN_TARGET_CPU":
        raise ValueError("NanoTrack-v2 requires DNN_TARGET_CPU")

    preprocessing = _required_mapping(
        spec.get("preprocessing"), "model spec.preprocessing"
    )
    _required_string(preprocessing, "id", "model spec.preprocessing")

    models = _required_mapping(spec.get("models"), "model spec.models")
    for role in ("backbone", "neckhead"):
        model = _required_mapping(models.get(role), f"model spec.models.{role}")
        for key in ("filename", "url", "sha256"):
            _required_string(model, key, f"model spec.models.{role}")
        digest = str(model["sha256"])
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError(
                f"model spec.models.{role}.sha256 must be a lowercase SHA-256"
            )
        size_bytes = model.get("size_bytes")
        if (
            isinstance(size_bytes, bool)
            or not isinstance(size_bytes, int)
            or size_bytes <= 0
        ):
            raise ValueError(
                f"model spec.models.{role}.size_bytes must be positive"
            )
    return spec


def _verify_model_file(path: Path, model: Mapping[str, Any], role: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"NanoTrack-v2 {role} model is missing: {path}")
    expected_size = int(model["size_bytes"])
    actual_size = path.stat().st_size
    if actual_size != expected_size:
        raise ValueError(
            f"NanoTrack-v2 {role} size mismatch: "
            f"expected {expected_size}, got {actual_size}"
        )
    expected_hash = str(model["sha256"])
    actual_hash = sha256_file(path)
    if actual_hash != expected_hash:
        raise ValueError(
            f"NanoTrack-v2 {role} SHA-256 mismatch: "
            f"expected {expected_hash}, got {actual_hash}"
        )
    return actual_hash


def create_nanotrack_backend(
    cv2_module: Any,
    backbone_path: Path,
    neckhead_path: Path,
) -> Any:
    params_constructor = getattr(cv2_module, "TrackerNano_Params", None)
    tracker_constructor = getattr(cv2_module, "TrackerNano_create", None)
    if not callable(params_constructor) or not callable(tracker_constructor):
        raise RuntimeError(
            "installed cv2 does not expose TrackerNano_create/"
            "TrackerNano_Params; install the pinned opencv-contrib-python package"
        )
    params = params_constructor()
    params.backbone = str(backbone_path)
    params.neckhead = str(neckhead_path)
    dnn = getattr(cv2_module, "dnn", None)
    params.backend = int(getattr(dnn, "DNN_BACKEND_DEFAULT", 0))
    params.target = int(getattr(dnn, "DNN_TARGET_CPU", 0))
    return tracker_constructor(params)


class NanoTrackV2Tracker:
    name = "nanotrack-v2"
    backend = "opencv-dnn-default/cpu"

    def __init__(
        self,
        *,
        spec_path: Path = DEFAULT_NANOTRACK_V2_SPEC,
        model_dir: Path = DEFAULT_NANOTRACK_V2_MODEL_DIR,
        cv2_module: Any | None = None,
        backend_factory: Any = create_nanotrack_backend,
    ):
        if cv2_module is None:
            try:
                import cv2 as cv2_module
            except ImportError as exception:
                raise RuntimeError(
                    "cv2 is unavailable; activate .venv-track and install "
                    "tools/requirements-track.txt"
                ) from exception
        self._cv2 = cv2_module
        self.version = str(getattr(cv2_module, "__version__", "unknown"))
        self._spec_path = Path(spec_path).resolve()
        self._model_dir = Path(model_dir).resolve()
        self._spec = load_nanotrack_v2_spec(self._spec_path)
        expected_opencv = str(self._spec["opencv"]["tested_version"])
        if self.version != expected_opencv:
            raise RuntimeError(
                f"NanoTrack-v2 requires OpenCV {expected_opencv}, "
                f"found {self.version}"
            )

        model_paths: dict[str, Path] = {}
        model_hashes: dict[str, str] = {}
        for role in ("backbone", "neckhead"):
            model = self._spec["models"][role]
            model_path = self._model_dir / str(model["filename"])
            model_hashes[role] = _verify_model_file(model_path, model, role)
            model_paths[role] = model_path
        self._model_paths = model_paths
        self._model_hashes = model_hashes
        try:
            self._tracker = backend_factory(
                cv2_module,
                model_paths["backbone"],
                model_paths["neckhead"],
            )
        except Exception as exception:
            raise RuntimeError(
                f"NanoTrack-v2 constructor failed: {type(exception).__name__}"
            ) from exception
        if self._tracker is None:
            raise RuntimeError("NanoTrack-v2 constructor returned no tracker")
        self._initialized = False

    def init(self, image: Any, box_norm: Sequence[float]) -> bool:
        width, height = image_size(image)
        box_pixels = norm_to_csrt_pixels(box_norm, width, height)
        try:
            initialized = self._tracker.init(image, box_pixels)
        except Exception:
            self._initialized = False
            return False
        if initialized is False:
            self._initialized = False
            return False
        self._initialized = True
        return True

    def update(self, image: Any) -> TrackerResult:
        if not self._initialized:
            return TrackerResult.lost("tracker_not_initialized")
        width, height = image_size(image)
        try:
            ok, box_pixels = self._tracker.update(image)
        except Exception as exception:
            return TrackerResult.lost(
                f"tracker_update_error:{type(exception).__name__}"
            )
        if not bool(ok):
            return TrackerResult.lost("tracker_reported_failure")
        try:
            box_norm = pixels_to_norm_unclipped(box_pixels, width, height)
        except (TypeError, ValueError):
            return TrackerResult.lost("invalid_tracker_box")
        try:
            score = float(self._tracker.getTrackingScore())
        except Exception as exception:
            return TrackerResult.lost(
                f"tracker_score_error:{type(exception).__name__}"
            )
        if not math.isfinite(score) or not 0.0 <= score <= 1.0:
            return TrackerResult.lost("invalid_tracker_confidence")
        return TrackerResult(
            box_norm=box_norm,
            ok=True,
            confidence=score,
            confidence_source="tracker",
        )

    def manifest_identity(self) -> Mapping[str, Any]:
        source = self._spec["source"]
        models = self._spec["models"]
        return {
            "name": self.name,
            "backend": self.backend,
            "pinned_version": self.version,
            "opencv_version": self.version,
            "opencv_package_pin": self._spec["opencv"]["package_pin"],
            "dnn_backend": self._spec["opencv"]["dnn_backend"],
            "dnn_target": self._spec["opencv"]["dnn_target"],
            "model_sha256": dict(self._model_hashes),
            "score_threshold": None,
            "threshold_source": "none",
            "preprocessing_id": self._spec["preprocessing"]["id"],
            "model_source": {
                "repository": source["repository"],
                "commit": source["commit"],
                "tree_url": source["tree_url"],
                "license_spdx": source["license_spdx"],
                "license_path": source["license_path"],
                "license_url": source["license_url"],
                "license_sha256": source["license_sha256"],
                "urls": {
                    role: models[role]["url"]
                    for role in ("backbone", "neckhead")
                },
            },
        }


def create_tracker(
    name: str,
    *,
    nanotrack_spec_path: Path = DEFAULT_NANOTRACK_V2_SPEC,
    nanotrack_model_dir: Path = DEFAULT_NANOTRACK_V2_MODEL_DIR,
    cv2_module: Any | None = None,
    det_assoc_spec_path: Path | None = None,
    resident: bool = False,
    **resident_options: Any,
) -> TrackerPlugin:
    if resident and name != "det-assoc-v1":
        raise ValueError("only det-assoc-v1 supports the resident protocol (P1-ENG-ACQ-001 §3.1)")
    if resident_options and not resident:
        raise ValueError("resident options require resident=True")
    if name == "csrt":
        return CsrtTracker(cv2_module)
    if name == "det-assoc-v1":  # P1-ENG-FAST-002 局部备选；只在显式选择时导入
        from .det_assoc_tracker import DEFAULT_DET_ASSOC_SPEC, DetAssocTracker

        if resident:  # P1-ENG-ACQ-001 §3.1：常驻实例只由显式 resident=True 产生
            return DetAssocTracker(
                spec_path=det_assoc_spec_path or DEFAULT_DET_ASSOC_SPEC, mode="resident", **resident_options
            )
        return DetAssocTracker(spec_path=det_assoc_spec_path or DEFAULT_DET_ASSOC_SPEC)
    if name == "nanotrack-v2":
        return NanoTrackV2Tracker(
            spec_path=nanotrack_spec_path,
            model_dir=nanotrack_model_dir,
            cv2_module=cv2_module,
        )
    raise ValueError(f"unknown tracker {name!r}")


class ScriptedTracker:
    """Deterministic fake used to verify failure and sequencing behavior."""

    name = "scripted"
    backend = "test"
    version = "1"

    def __init__(
        self,
        results: Iterable[TrackerResult],
        init_ok: bool = True,
    ):
        self._results = deque(results)
        self._init_ok = init_ok
        self.init_calls: list[BoxNorm] = []
        self.update_calls = 0

    def init(self, image: Any, box_norm: Sequence[float]) -> bool:
        clipped = clip_box_norm(box_norm)
        if clipped is None:
            return False
        self.init_calls.append(clipped)
        return self._init_ok

    def update(self, image: Any) -> TrackerResult:
        self.update_calls += 1
        if not self._results:
            return TrackerResult.lost("script_exhausted")
        return self._results.popleft()

    def manifest_identity(self) -> Mapping[str, Any]:
        return {
            "name": self.name,
            "backend": self.backend,
            "pinned_version": self.version,
        }
