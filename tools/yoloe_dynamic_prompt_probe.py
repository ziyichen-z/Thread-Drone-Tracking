from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import tempfile
import time
from typing import Any


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def box_count(results: Any) -> int:
    if not results:
        return 0
    boxes = getattr(results[0], "boxes", None)
    return 0 if boxes is None else len(boxes)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_error(exc: Exception) -> str:
    message = re.sub(r"\x1b\[[0-9;]*m", "", str(exc))
    return message.split("\n\n    Arguments received:", maxsplit=1)[0].strip()


def timed(callable_object):
    started = time.perf_counter()
    result = callable_object()
    return result, time.perf_counter() - started


def exported_reprompt_attempt(
    model_factory,
    exported_path: Path,
    source: Path,
    reference: Path,
    prompts: dict[str, Any],
    predictor,
    args: argparse.Namespace,
) -> dict[str, Any]:
    try:
        exported_model = model_factory(str(exported_path))
    except Exception as exc:
        return {
            "supported": False,
            "failure_stage": "load_export",
            "error_type": type(exc).__name__,
            "error": clean_error(exc),
        }

    try:
        results, seconds = timed(lambda: exported_model.predict(
            source=str(source),
            refer_image=str(reference),
            visual_prompts=prompts,
            predictor=predictor,
            imgsz=args.imgsz,
            conf=args.confidence,
            device=args.device,
            verbose=False,
        ))
        return {
            "supported": True,
            "seconds": seconds,
            "box_count": box_count(results),
        }
    except Exception as exc:
        return {
            "supported": False,
            "failure_stage": "dynamic_prompt_predict",
            "error_type": type(exc).__name__,
            "error": clean_error(exc),
        }


def run(args: argparse.Namespace) -> dict[str, Any]:
    try:
        import numpy as np
        import onnx
        import onnxruntime
        import torch
        import ultralytics
        from ultralytics import YOLO, YOLOE
        from ultralytics.models.yolo.yoloe import YOLOEVPSegPredictor
    except ImportError as exc:
        raise SystemExit(
            "YOLOE probe dependencies are missing. Install Ultralytics and its platform-specific "
            "PyTorch/TensorRT dependencies in an isolated environment. Original error: " + str(exc)
        ) from exc

    reference = Path(args.reference).resolve()
    source = Path(args.source).resolve()
    reprompt_reference = Path(args.reprompt_reference or args.reference).resolve()
    if not reference.is_file() or not source.is_file() or not reprompt_reference.is_file():
        raise SystemExit(
            "--reference, --source, and --reprompt-reference must point to existing images"
        )

    prompts = {
        "bboxes": np.array([args.prompt_box], dtype=np.float32),
        "cls": np.array([0], dtype=np.int64),
    }
    reprompt_box = args.reprompt_box or args.prompt_box
    reprompt_prompts = {
        "bboxes": np.array([reprompt_box], dtype=np.float32),
        "cls": np.array([0], dtype=np.int64),
    }
    prompt_sha256 = sha256(reference)
    reprompt_sha256 = sha256(reprompt_reference)
    reprompt_differs = (
        prompt_sha256 != reprompt_sha256
        or [float(value) for value in reprompt_box]
        != [float(value) for value in args.prompt_box]
    )
    report: dict[str, Any] = {
        "schema_version": "yoloe-dynamic-prompt-probe/v1",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "ultralytics": ultralytics.__version__,
        "torch": torch.__version__,
        "onnx": onnx.__version__,
        "onnxruntime": onnxruntime.__version__,
        "cuda_available": torch.cuda.is_available(),
        "model": args.model,
        "reference": str(reference),
        "source": str(source),
        "reference_sha256": prompt_sha256,
        "source_sha256": sha256(source),
        "prompt_box_xyxy_px": args.prompt_box,
        "reprompt_reference": str(reprompt_reference),
        "reprompt_reference_sha256": reprompt_sha256,
        "reprompt_box_xyxy_px": reprompt_box,
        "reprompt_differs_from_export_prompt": reprompt_differs,
        "export_format": args.export_format,
    }

    model, load_seconds = timed(lambda: YOLOE(args.model))
    prompted_results, prompted_seconds = timed(lambda: model.predict(
        source=str(source),
        refer_image=str(reference),
        visual_prompts=prompts,
        predictor=YOLOEVPSegPredictor,
        imgsz=args.imgsz,
        conf=args.confidence,
        device=args.device,
        verbose=False,
    ))
    cached_results, cached_seconds = timed(lambda: model.predict(
        source=str(source),
        imgsz=args.imgsz,
        conf=args.confidence,
        device=args.device,
        verbose=False,
    ))
    report["pytorch"] = {
        "model_load_seconds": load_seconds,
        "prompted_inference_seconds": prompted_seconds,
        "cached_prompt_inference_seconds": cached_seconds,
        "prompted_box_count": box_count(prompted_results),
        "cached_prompt_box_count": box_count(cached_results),
    }

    exported_path, export_seconds = timed(lambda: model.export(
        format=args.export_format,
        imgsz=args.imgsz,
        device=args.device,
    ))
    exported_path = Path(str(exported_path)).resolve()
    report["export"] = {
        "path": str(exported_path),
        "seconds": export_seconds,
        "exists": exported_path.exists(),
    }

    static_model = YOLO(str(exported_path))
    static_results, static_seconds = timed(lambda: static_model.predict(
        source=str(source),
        imgsz=args.imgsz,
        conf=args.confidence,
        device=args.device,
        verbose=False,
    ))
    report["exported_static_inference"] = {
        "seconds": static_seconds,
        "box_count": box_count(static_results),
    }

    attempts = {
        "load_as_yoloe": exported_reprompt_attempt(
            YOLOE,
            exported_path,
            source,
            reprompt_reference,
            reprompt_prompts,
            YOLOEVPSegPredictor,
            args,
        ),
        "load_as_generic_yolo": exported_reprompt_attempt(
            YOLO,
            exported_path,
            source,
            reprompt_reference,
            reprompt_prompts,
            YOLOEVPSegPredictor,
            args,
        ),
    }
    dynamic_supported = any(attempt["supported"] for attempt in attempts.values())
    report["exported_dynamic_reprompt"] = {
        "supported": dynamic_supported,
        "attempts": attempts,
    }

    if not reprompt_differs:
        report["conclusion"] = "inconclusive_reprompt_was_not_distinct"
    elif dynamic_supported:
        report["conclusion"] = "standard_export_accepts_runtime_visual_prompts"
    else:
        report["conclusion"] = (
            "standard_export_bakes_prompt_and_requires_per-target_export_or_custom_split_graph"
        )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure YOLOE visual prompting before and after ONNX/TensorRT export."
    )
    parser.add_argument("--model", default="yoloe-11s-seg.pt")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument(
        "--prompt-box",
        nargs=4,
        type=float,
        metavar=("X1", "Y1", "X2", "Y2"),
        required=True,
    )
    parser.add_argument(
        "--reprompt-reference",
        help="Reference image used after export; defaults to --reference.",
    )
    parser.add_argument(
        "--reprompt-box",
        nargs=4,
        type=float,
        metavar=("X1", "Y1", "X2", "Y2"),
        help="A distinct post-export prompt box; defaults to --prompt-box.",
    )
    parser.add_argument("--export-format", choices=("onnx", "engine"), default="onnx")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--confidence", type=float, default=0.01)
    parser.add_argument("--device", default=None)
    parser.add_argument("--output", default="runtime/yoloe_dynamic_prompt_probe.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run(args)
    output = Path(args.output).resolve()
    atomic_json(output, report)
    print(json.dumps(report, indent=2))
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
