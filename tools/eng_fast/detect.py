"""检测器层（合同 §3.2、§3.2.1）：T0-bank 视觉提示库与 T0-oracle 同会话参考。

统一输出：每帧 `[[x, y, w, h, score, cls], ...]`（归一化 top-left xywh；评分时类别
无关）。阈值 0.25、`imgsz` 640 取冻结配置 `config/detector-reanchor.models.json`
（只读；权重 sha 与 ultralytics 钉版由冻结的 `YoloeProposer` 核对）。

T0-bank 嵌入：对每张参考帧走与 `YoloeProposer.initialize` 同一条库内路径
（`YOLOE.predict(refer_image=…, visual_prompts=…, predictor=YOLOEVPSegPredictor)`，
其内部 `predictor.get_vpe` → `model(img, vpe=visual, return_vpe=True)` 即
`get_visual_pe(img, visual)`），读出该帧每类嵌入；每类跨参考帧取算术平均后
L2 归一化，`set_classes(["vehicle", "target-primitive"], vpe)` 一次固定。
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Any, Iterable, Mapping, Sequence

from tools.eng_fast import common

BANK_CLASS_INDEX = {"vehicle": 0, "target-primitive": 1}
BANK_CLASS_NAMES = ["vehicle", "target-primitive"]
BANK_FALLBACK = "BANK_FALLBACK_SINGLE_FRAME"


def read_bgr(path: str) -> Any:
    import cv2  # noqa: PLC0415

    image = cv2.imread(str(common.absolute(path)), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"无法读取图像 {path}")
    return image


def frozen_config() -> Any:
    from controller.reanchor import load_reanchor_config  # noqa: PLC0415

    return load_reanchor_config(common.PROJECT_ROOT / "config" / "detector-reanchor.models.json")


def _results_to_rows(results: Any, width: int, height: int, threshold: float) -> list[list[float]]:
    if not results or results[0].boxes is None:
        return []
    boxes = results[0].boxes
    xyxy = boxes.xyxy.detach().cpu().tolist()
    conf = boxes.conf.detach().cpu().tolist()
    cls = boxes.cls.detach().cpu().tolist()
    rows: list[list[float]] = []
    for (x1, y1, x2, y2), score, label in zip(xyxy, conf, cls):
        score = float(score)
        if not math.isfinite(score) or score < threshold:
            continue
        left, top = max(0.0, x1 / width), max(0.0, y1 / height)
        right, bottom = min(1.0, x2 / width), min(1.0, y2 / height)
        if right <= left or bottom <= top:
            continue
        rows.append([left, top, right - left, bottom - top, score, float(int(label))])
    return rows


@dataclass
class Detector:
    """一个已固定类别的 YOLOE 实例；`detect(image)` 返回统一行与毫秒时延（含预处理）。"""

    detector_id: str
    model: Any
    device: str
    imgsz: int
    threshold: float
    identity: dict[str, Any]

    def detect(self, image: Any) -> tuple[list[list[float]], float]:
        height, width = image.shape[:2]
        started = time.perf_counter()
        results = self.model.predict(
            source=image, imgsz=self.imgsz, conf=self.threshold, device=self.device, verbose=False
        )
        elapsed = (time.perf_counter() - started) * 1000.0
        return _results_to_rows(results, width, height, self.threshold), elapsed


def _new_yoloe(config: Any) -> Any:
    """冻结身份核对后新建 YOLOE（复用 `YoloeProposer` 的核对：权重 sha/字节与 ultralytics 钉版）。"""
    from controller.reanchor_models import YoloeProposer  # noqa: PLC0415

    return YoloeProposer(config)


def _frame_vpe(proposer: Any, image: Any, boxes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """一张参考帧 → {bank_class: 嵌入张量(D,)}，走 `YoloeProposer.initialize` 同一库内路径。"""
    import numpy as np  # noqa: PLC0415
    from ultralytics.models.yolo.yoloe import YOLOEVPSegPredictor  # noqa: PLC0415

    height, width = image.shape[:2]
    bboxes, cls = [], []
    for item in boxes:
        x, y, w, h = item["box"]
        bboxes.append([x * width, y * height, (x + w) * width, (y + h) * height])
        cls.append(BANK_CLASS_INDEX[item["bank_class"]])
    prompts = {"bboxes": np.array(bboxes, dtype=np.float32), "cls": np.array(cls, dtype=np.int64)}
    proposer.model.predict(
        source=image,
        refer_image=image,
        visual_prompts=prompts,
        predictor=YOLOEVPSegPredictor,
        imgsz=proposer.imgsz,
        conf=proposer.threshold,
        device=proposer.device,
        verbose=False,
    )
    pe = proposer.model.model.pe.detach().cpu().float()  # (1, n_unique_cls, D)，按类索引升序
    unique = sorted(set(cls))
    if pe.shape[1] != len(unique):
        raise RuntimeError(f"VPE 形状 {tuple(pe.shape)} 与本帧类别 {unique} 不符")
    return {BANK_CLASS_NAMES[label]: pe[0, position].clone() for position, label in enumerate(unique)}


def build_t0_bank(bank: Mapping[str, Any], *, device: str = "cpu", config: Any = None) -> Detector:
    """按 §3.2.1 选出的参考库固定两类嵌入；返回 T0-bank 检测器与嵌入身份。"""
    import torch  # noqa: PLC0415

    config = config or frozen_config()
    proposer = _new_yoloe(config)
    proposer.device = device
    refs = list(bank["vehicle"]) + ([bank["target_primitive"]] if bank.get("target_primitive") else [])
    by_frame: dict[str, list[dict[str, Any]]] = {}
    for ref in refs:
        by_frame.setdefault(ref["frame_id"], []).extend(ref["boxes"])
    per_class: dict[str, list[tuple[int, str, Any]]] = {name: [] for name in BANK_CLASS_NAMES}
    per_frame_classes: dict[str, list[str]] = {}
    for frame_id in sorted(by_frame):
        vpes = _frame_vpe(proposer, read_bgr(frame_id), by_frame[frame_id])
        per_frame_classes[frame_id] = sorted(vpes)
        covered = sum(1 for item in by_frame[frame_id] if item["bank_class"] == "vehicle")
        for name, tensor in vpes.items():
            per_class[name].append((covered, frame_id, tensor))
    present = [name for name in BANK_CLASS_NAMES if per_class[name]]
    if not present:
        raise RuntimeError("参考库为空，无法固定 T0-bank")
    embeddings = []
    for name in present:
        stacked = torch.stack([item[2] for item in per_class[name]], dim=0).mean(dim=0)
        embeddings.append(torch.nn.functional.normalize(stacked, dim=-1))
    vpe = torch.stack(embeddings, dim=0)[None]  # (1, C, D)
    status = "MULTI_FRAME_MEAN"
    device_of_model = next(proposer.model.model.parameters()).device
    try:
        proposer.model.set_classes(list(present), vpe.to(device_of_model))
    except Exception as exc:  # noqa: BLE001 — §3.2.1 预注册回退，报错原文入身份
        status = f"{BANK_FALLBACK}: {type(exc).__name__}: {exc}"
        singles = []
        for name in present:
            # 每类只用「覆盖类别数最多」的那一张参考帧（并列取 frame_id 字典序最小）。
            best = sorted(per_class[name], key=lambda item: (-item[0], item[1]))[0]
            singles.append(torch.nn.functional.normalize(best[2], dim=-1))
        vpe = torch.stack(singles, dim=0)[None]
        proposer.model.set_classes(list(present), vpe.to(device_of_model))
    proposer.model.predictor = None
    identity = {
        "detector_id": "T0-bank",
        "device": device,
        "classes": present,
        "embedding_status": status,
        "embedding_shape": list(vpe.shape),
        "embedding_sha256": common.sha256_bytes(vpe.numpy().astype("float32").tobytes()),
        "per_class_frame_counts": {name: len(per_class[name]) for name in present},
        "per_frame_classes": per_frame_classes,
    }
    return Detector("T0-bank", proposer.model, device, proposer.imgsz, proposer.threshold, identity)


def build_t0_oracle(reference: Mapping[str, Any], *, device: str = "cpu", config: Any = None) -> Detector:
    """DETECT-001 scouting 口径：同会话 `reference.json` 绑定框作单类视觉提示。"""
    config = config or frozen_config()
    proposer = _new_yoloe(config)
    proposer.device = device
    image = read_bgr(reference["image_path"])
    proposer.initialize(image, reference["box_xywh_norm"])
    identity = {
        "detector_id": "T0-oracle",
        "device": device,
        "reference_image": reference["image_path"],
        "reference_image_sha256": common.sha256_file(reference["image_path"]),
        "reference_box_xywh_norm": list(reference["box_xywh_norm"]),
        "embedding_sha256": common.sha256_bytes(
            proposer.model.model.pe.detach().cpu().float().numpy().tobytes()
        ),
    }
    return Detector("T0-oracle", proposer.model, device, proposer.imgsz, proposer.threshold, identity)


def scout_reference(spec: Mapping[str, Any]) -> dict[str, Any]:
    """scout 会话参考：`reference.json` 的框与 `reference-preview.jpg`（sha 须与参考文档一致）。"""
    session = common.absolute(spec["session_dir"])
    reference = common.read_json(session / "reference.json")
    image_path = common.rel(session / "reference-preview.jpg")
    actual = common.sha256_file(image_path)
    if actual != reference["image_sha256"]:
        raise ValueError(f"{spec['source']} 参考图 sha 不符：{actual} ≠ {reference['image_sha256']}")
    return {
        "image_path": image_path,
        "image_sha256": actual,
        "box_xywh_norm": [float(v) for v in reference["box_xywh_norm"]],
        "frame_id": int(reference["frame_id"]),
        "simulation_time_s": float(reference["simulation_time_s"]),
        "reference_json_sha256": common.sha256_file(session / "reference.json"),
    }


def run_frames(detector: Detector, paths: Iterable[str]) -> list[dict[str, Any]]:
    rows = []
    for path in paths:
        dets, elapsed = detector.detect(read_bgr(path))
        rows.append({"path": path, "dets": [[round(v, 7) for v in det] for det in dets], "ms": round(elapsed, 3)})
    return rows
