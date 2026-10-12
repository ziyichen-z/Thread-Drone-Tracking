from __future__ import annotations

from dataclasses import dataclass
import importlib
import math
from pathlib import Path
import sys
import tarfile
import time
from typing import Any, Mapping, Sequence

from .reanchor import Candidate, ReanchorConfig, _resolve_project_path, verify_file, world_los
from .trackers import BoxNorm, clip_box_norm, image_size, pixels_to_norm


class CropInvalid(ValueError):
    pass


def verify_extracted_source(archive: Path, source_dir: Path) -> None:
    """Prove that imported source bytes are exactly those in the pinned archive."""
    archive_files: dict[Path, tuple[int, str]] = {}
    with tarfile.open(archive, mode="r:gz") as handle:
        for member in handle.getmembers():
            parts = Path(member.name).parts
            if not parts or parts[0] != source_dir.name:
                raise ValueError("DINOv2 archive root mismatch")
            relative = Path(*parts[1:])
            if member.isdir():
                continue
            if not member.isfile() or not relative.parts:
                raise ValueError("DINOv2 archive contains unsupported entries")
            stream = handle.extractfile(member)
            if stream is None:
                raise ValueError("DINOv2 archive member is unreadable")
            import hashlib
            digest = hashlib.sha256()
            size = 0
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(chunk)
                digest.update(chunk)
            archive_files[relative] = (size, digest.hexdigest())
    disk_files = {
        path.relative_to(source_dir)
        for path in source_dir.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    if disk_files != set(archive_files):
        raise ValueError("DINOv2 extracted source file set mismatch")
    for relative, (size, digest) in archive_files.items():
        verify_file(
            source_dir / relative,
            size_bytes=size,
            sha256=digest,
            label=f"DINOv2 source {relative}",
        )


class DinoV2Embedder:
    def __init__(self, config: ReanchorConfig):
        appearance = config.appearance
        source = appearance["source"]
        weights = appearance["weights"]
        archive = _resolve_project_path(source["archive_path"], "appearance.source.archive_path")
        source_dir = _resolve_project_path(source["directory"], "appearance.source.directory")
        license_path = source_dir / str(source["license_path"])
        weight_path = _resolve_project_path(weights["path"], "appearance.weights.path")
        verify_file(archive, size_bytes=source["archive_size_bytes"], sha256=source["archive_sha256"], label="DINOv2 source archive")
        verify_extracted_source(archive, source_dir)
        verify_file(license_path, size_bytes=source["license_size_bytes"], sha256=source["license_sha256"], label="DINOv2 LICENSE")
        verify_file(weight_path, size_bytes=weights["size_bytes"], sha256=weights["sha256"], label="DINOv2 weights")
        if str(source_dir) not in sys.path:
            sys.path.insert(0, str(source_dir))
        import torch
        import torchvision
        from PIL import Image
        from torchvision.transforms import InterpolationMode

        runtime = config.raw["runtime"]
        if torch.__version__.split("+", 1)[0] != runtime["torch_pin"]:
            raise RuntimeError("DINOv2 torch pin mismatch")
        if torchvision.__version__.split("+", 1)[0] != runtime["torchvision_pin"]:
            raise RuntimeError("DINOv2 torchvision pin mismatch")
        backbones = importlib.import_module("dinov2.hub.backbones")
        transforms_module = importlib.import_module("dinov2.data.transforms")
        if not Path(backbones.__file__).resolve().is_relative_to(source_dir):
            raise RuntimeError("DINOv2 module was not imported from the pinned local source")
        model = backbones.dinov2_vits14(pretrained=False)
        state = torch.load(weight_path, map_location="cpu", weights_only=True)
        model.load_state_dict(state, strict=True)
        self.model = model.eval().to(str(runtime["device"]))
        preprocessing = appearance["preprocessing"]
        self.transform = transforms_module.make_classification_eval_transform(
            crop_size=int(preprocessing["crop_px"]),
            resize_size=int(preprocessing["resize_px"]),
            interpolation=InterpolationMode.BICUBIC,
        )
        self.torch = torch
        self.Image = Image
        self.minimum_side = int(appearance["preprocessing"]["minimum_crop_side_px"])
        self.dimensions = int(appearance["embedding_dimensions"])
        self.device = str(runtime["device"])

    def embed(self, bgr_image: Any, box_norm: Sequence[float]) -> tuple[float, ...]:
        box = clip_box_norm(box_norm)
        if box is None:
            raise CropInvalid("CROP_INVALID")
        width, height = image_size(bgr_image)
        x, y, w, h = box
        left, top = max(0, int(math.floor(x * width))), max(0, int(math.floor(y * height)))
        right, bottom = min(width, int(math.ceil((x + w) * width))), min(height, int(math.ceil((y + h) * height)))
        if right - left < self.minimum_side or bottom - top < self.minimum_side:
            raise CropInvalid("CROP_INVALID")
        crop = bgr_image[top:bottom, left:right]
        rgb = crop[:, :, ::-1].copy()
        tensor = self.transform(self.Image.fromarray(rgb, mode="RGB")).unsqueeze(0).to(self.device)
        if not bool(self.torch.isfinite(tensor).all()):
            raise CropInvalid("CROP_INVALID")
        with self.torch.no_grad():
            output = self.model.forward_features(tensor)["x_norm_clstoken"][0]
        if output.numel() != self.dimensions or not bool(self.torch.isfinite(output).all()):
            raise RuntimeError("EMBED_INVALID")
        norm = self.torch.linalg.vector_norm(output)
        if not bool(self.torch.isfinite(norm)) or float(norm) <= 0.0:
            raise RuntimeError("EMBED_INVALID")
        return tuple(float(value) for value in (output / norm).cpu())

    @staticmethod
    def cosine(left: Sequence[float], right: Sequence[float]) -> float:
        if len(left) != len(right) or not left:
            raise ValueError("embedding dimensions mismatch")
        value = sum(float(a) * float(b) for a, b in zip(left, right))
        if not math.isfinite(value):
            raise RuntimeError("EMBED_INVALID")
        return max(-1.0, min(1.0, value))


@dataclass(frozen=True)
class ProposalBatch:
    boxes_norm: tuple[BoxNorm, ...]
    confidences: tuple[float, ...]
    detector_latency_ms: float


class YoloeProposer:
    def __init__(self, config: ReanchorConfig):
        detector = config.detector
        path = _resolve_project_path(detector["path"], "detector.path")
        verify_file(path, size_bytes=detector["size_bytes"], sha256=detector["sha256"], label="YOLOE weights")
        import numpy as np
        import ultralytics
        from ultralytics import YOLOE
        from ultralytics.models.yolo.yoloe import YOLOEVPSegPredictor

        if ultralytics.__version__ != config.raw["runtime"]["ultralytics_pin"]:
            raise RuntimeError("YOLOE ultralytics pin mismatch")
        self.model = YOLOE(str(path))
        self.predictor = YOLOEVPSegPredictor
        self.np = np
        self.device = str(config.raw["runtime"]["device"])
        self.imgsz = int(detector["image_size_px"])
        self.threshold = float(config.parameters["detector_threshold"])
        self.prompted = False

    def initialize(self, image: Any, box_norm: Sequence[float]) -> None:
        width, height = image_size(image)
        x, y, w, h = clip_box_norm(box_norm) or (_ for _ in ()).throw(ValueError("invalid prompt box"))
        prompts = {
            "bboxes": self.np.array([[x * width, y * height, (x + w) * width, (y + h) * height]], dtype=self.np.float32),
            "cls": self.np.array([0], dtype=self.np.int64),
        }
        self.model.predict(source=image, refer_image=image, visual_prompts=prompts, predictor=self.predictor, imgsz=self.imgsz, conf=self.threshold, device=self.device, verbose=False)
        self.prompted = True

    def propose(self, image: Any) -> ProposalBatch:
        if not self.prompted:
            raise RuntimeError("YOLOE visual prompt is not initialized")
        started = time.perf_counter()
        results = self.model.predict(source=image, imgsz=self.imgsz, conf=self.threshold, device=self.device, verbose=False)
        elapsed = (time.perf_counter() - started) * 1000.0
        if not results or results[0].boxes is None:
            return ProposalBatch((), (), elapsed)
        width, height = image_size(image)
        xyxy = results[0].boxes.xyxy.detach().cpu().tolist()
        conf = results[0].boxes.conf.detach().cpu().tolist()
        boxes: list[BoxNorm] = []
        scores: list[float] = []
        for raw_box, raw_score in zip(xyxy, conf):
            normalized = pixels_to_norm((raw_box[0], raw_box[1], raw_box[2] - raw_box[0], raw_box[3] - raw_box[1]), width, height)
            score = float(raw_score)
            if normalized is not None and math.isfinite(score) and 0.0 <= score <= 1.0:
                boxes.append(normalized)
                scores.append(score)
        return ProposalBatch(tuple(boxes), tuple(scores), elapsed)


def build_candidates(
    batch: ProposalBatch,
    image: Any,
    metadata: Mapping[str, Any],
    embedder: DinoV2Embedder,
    anchor_embedding: Sequence[float],
    anchor_los: Sequence[float],
    *,
    basis_tolerance: float,
    quaternion_tolerance: float,
) -> tuple[tuple[Candidate, ...], int]:
    candidates: list[Candidate] = []
    crop_invalid = 0
    for index, (box, confidence) in enumerate(zip(batch.boxes_norm, batch.confidences)):
        try:
            embedding = embedder.embed(image, box)
        except CropInvalid:
            crop_invalid += 1
            continue
        los = world_los(box, metadata, basis_tolerance=basis_tolerance, quaternion_tolerance=quaternion_tolerance)
        cosine = embedder.cosine(anchor_embedding, embedding)
        dot = max(-1.0, min(1.0, sum(float(a) * float(b) for a, b in zip(anchor_los, los))))
        candidates.append(Candidate(index, box, confidence, cosine, los, math.acos(dot)))
    return tuple(candidates), crop_invalid
