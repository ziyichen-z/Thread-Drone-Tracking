"""P1-ENG-CAPTURE-001 AC-17/AC-19 基线臂：只在基线源导出（本提案 `ACCEPTED` 裁定提交上的 `controller/`）上运行。

* 基线源由 git 运行时解析（`common.accepted_base_commit()`），并核其 `controller/` 与 F18 记载的 10-08 Play 代码
  提交逐字节等价（`common.controller_equivalent`），不等价即拒绝（不手写 SHA）。
* 导出为独立包 `controller_base`（不复用已改变的新管理器）；`per_class` + `pose`（旧 AABB 补偿），检测来自本次
  per_class 缓存（替身 `model_loader`，零加载）；以点击点在 k 帧包含框作 `designate(box, k)` 输入。
* 本模块不读真值；逐帧只产出基线臂自身的 (frame_id, pointer ok, 框, 原因) 供 `replay.score_*` 评分。
"""

from __future__ import annotations

import importlib
from pathlib import Path
import sys
from typing import Any, Callable, Iterable, Mapping, Sequence

from tools.eng_capture.common import accepted_base_commit, controller_equivalent, export_controller, play_code_commit

PACKAGE = "controller_base"


class BaselineSourceRejected(RuntimeError):
    """基线源不可解析或与 F18 Play 代码不等价。"""


def prepare_baseline_package(root: Path) -> tuple[Path, dict[str, str]]:
    """导出基线源到 `root/controller_base`（`root/config` 只读链接仓库 config/）；返回 (包根, 身份)。"""
    accepted = accepted_base_commit()
    play = play_code_commit()
    if accepted is None or play is None:
        raise BaselineSourceRejected("cannot resolve the accepted ruling commit or the F18 Play commit from git")
    if not controller_equivalent(accepted, play):
        raise BaselineSourceRejected(f"controller/ at {accepted} differs from the F18 Play code {play}")
    root = Path(root)
    export_controller(accepted, root / PACKAGE)
    from tools.eng_capture.common import PROJECT_ROOT  # noqa: PLC0415

    config_link = root / "config"
    if not config_link.exists():
        config_link.symlink_to(PROJECT_ROOT / "config")
    # 导出包的 `PROJECT_ROOT` = 导出根：规格里按相对路径解析的权重与冻结文件也以只读符号链接指回仓库原件
    # （基线源照旧按规格核 sha/体积；不复制、不改原件）。
    link_spec_relative_files(root, PROJECT_ROOT / "config" / "det-assoc-v1.models.json", PROJECT_ROOT)
    return root, {"accepted_commit": accepted, "play_code_commit": play, "equivalent": "controller/ byte-identical"}


def link_spec_relative_files(root: Path, spec_path: Path, project_root: Path) -> list[Path]:
    """规格 `weights.path` 与 `freeze.path` 中的相对路径 → 在 `root` 下建同名只读符号链接指向 `project_root` 原件。"""
    import json  # noqa: PLC0415

    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    links = []
    for section in ("weights", "freeze"):
        relative = Path(spec[section]["path"])
        if relative.is_absolute():
            continue
        link = Path(root) / relative
        if not link.exists():
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(Path(project_root) / relative)
        links.append(link)
    return links


def load_baseline_modules(root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(root))
    try:
        return {name: importlib.import_module(f"{PACKAGE}.{name}") for name in ("det_assoc_tracker", "resident_core", "trackers")}
    finally:
        sys.path.remove(str(root))


def containing_box(entry: Any, x_px: float, y_px: float, width: int, height: int) -> tuple[float, float, float, float] | None:
    """k 帧 tracked 行中包含点击点的框（多个时取中心最近者）；无 → None。"""
    best: tuple[float, tuple[float, float, float, float]] | None = None
    for row in entry.rows("tracked"):
        x, y, w, h = row.box_norm
        if x * width <= x_px <= (x + w) * width and y * height <= y_px <= (y + h) * height:
            distance = ((x + w / 2) * width - x_px) ** 2 + ((y + h / 2) * height - y_px) ** 2
            if best is None or distance < best[0]:
                best = (distance, tuple(row.box_norm))
    return None if best is None else best[1]


def run_baseline_arm(
    modules: Mapping[str, Any],
    frames: Iterable[Any],
    *,
    spec_path: Path,
    model_loader: Callable[[Path], Any],
    clicks: Sequence[Mapping[str, Any]] = (),
    device: str = "cpu",
) -> list[dict[str, Any]]:
    """逐帧 `step` + `pointer_result`；点击帧处理完后 `designate(包含框, k)`（指针自下一帧生效）。

    `frames` 的元素须有 `frame_id`、`image`（可为缓存帧替身）、`metadata`。返回逐帧记录。"""
    dat = modules["det_assoc_tracker"]
    tracker = dat.DetAssocTracker(spec_path=spec_path, device=device, model_loader=model_loader, mode="resident", gmc_source="pose")
    by_frame: dict[int, list[Mapping[str, Any]]] = {}
    for click in clicks:
        by_frame.setdefault(int(click["frame_id"]), []).append(click)
    records: list[dict[str, Any]] = []

    def no_level2(k: int, box: Sequence[float], h: int) -> Any:
        reanchor = importlib.import_module(f"{PACKAGE}.reanchor")
        return reanchor.ReplayResult("RESEED_DISCARDED_MISSING_FRAME", "level2_not_run_in_replay", k, None, 0, 0.0, None)

    for frame in frames:
        tracker.step(frame.image, frame.frame_id, frame.metadata)
        result = tracker.pointer_result(frame.frame_id)
        record = {
            "frame_id": frame.frame_id,
            "ok": bool(result.ok),
            "box_norm": None if result.box_norm is None else [float(v) for v in result.box_norm],
            "reason": result.reason,
            "pointer": tracker.pointer(),
            "designations": [],
        }
        for click in by_frame.get(frame.frame_id, []):
            entry = tracker.history(frame.frame_id)
            width = int(frame.metadata.get("width", 640))
            height = int(frame.metadata.get("height", 480))
            box = containing_box(entry, float(click["x_px"]), float(click["y_px"]), width, height)
            if box is None:
                record["designations"].append({"label": click.get("label"), "result": "NO_CONTAINING_BOX"})
                continue
            designation = tracker.core.designate(box, frame.frame_id, no_level2)
            record["designations"].append({"label": click.get("label"), **designation.as_record()})
        records.append(record)
    return records
