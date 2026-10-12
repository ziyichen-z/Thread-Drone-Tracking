#!/usr/bin/env python3
"""AC-4：分层抽样、叠加框面板与判定统计（纯离线、零 Play、零模型）。

三个阶段互不合并，顺序由合同固定：

1. `plan`——按种子与配额从指令逐行文件抽样，把**种子、各层定义与配额、
   分母、实取数与逐张清单**写进 `docs/evidence/P1-ENG-ASSET-001-label-audit.md`；
   该文件必须先提交，再进第 2 步。
2. `panels`——运行时解析该文件的 `git status --porcelain`（须为空）与
   `git log -1 --format=%H`，写入 `panel-receipt.json`；不满足即写失败收据
   `QUOTA_FILE_DIRTY`，不生成任何面板。面板每张只画该行的框与 surface，
   原图另存副本；逐张 `overlay_sha256` 回填清单。
3. `stats`——**只读** `docs/unity-test-log.md` 的
   `UT-P1-ENG-ASSET-001-label-audit` 条目（`OFFLINE_VISUAL_CHECK`，判定原文由
   接受/辅助角色代录），统计逐层计数：「不确定」单独计数、不计为对，空层不
   计为通过。本模块不写 Unity 日志，也不复制判定原文。

分层（按优先序归层，每行只属第一个命中层，合同 AC-4）：

    S1 `color_status != VERIFIED`
    S2 `uniqueness_status ∈ {AMBIGUOUS_SAME_CLASS, WILDCARD_UNKNOWN_CLASS,
                             UNIQUE_CLASS_COLOR, UNIQUE_RELATION}`
    S3 `short_side_px < 32`
    S4 `uniqueness_status = UNIQUE_CLASS ∧ short_side_px ≥ 64`

层内按 `SHA-256(seed‖frame_id‖object_id)` 升序取样，每对象每层 ≤ 2 行，
层不足额时留空不回填。
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Iterable, Iterator

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_asset import receipts  # noqa: E402
from tools.eng_asset.receipts import InputManifest, QuotaFileDirty, ReceiptWriter  # noqa: E402

WORK_ID = receipts.WORK_ID
EVIDENCE_DIR = Path("docs/evidence")
AUDIT_FILENAME = f"{WORK_ID}-label-audit.md"
UNITY_LOG_PATH = Path("docs/unity-test-log.md")
UNITY_LOG_ENTRY = f"UT-{WORK_ID}-label-audit"
PANEL_RECEIPT_NAME = "panel-receipt.json"
# AC-4 修订 1 / AC-6 修订 1（2026-09-08 实现期裁定）：面板唯一落点移出
# `runtime/`——DATA-001 附录 A 把 `runtime` 当枚举根并断言其下每个 jpg 恰匹配
# 一个 pattern，派生面板落在那里必然 zero-match。收据与指令逐行文件仍在
# `runtime/eng-asset/<work-id>/`（其余本地 A2 路径不变）。
PANEL_ROOT = Path("outputs/eng-asset") / WORK_ID
RELOCATE_RULING = "AC-4 修订 1 / AC-6 修订 1（提案「待裁定」节，2026-09-08 实现期裁定）"
PANEL_RECEIPT_SCHEMA = "p1-eng-asset-001/panel-receipt/v1"
RECEIPTS_SUBDIR = receipts.RECEIPTS_DIRNAME

DEFAULT_SEED = f"{WORK_ID}-label-audit-2026-09-08"
STRATA: tuple[str, ...] = ("S1", "S2", "S3", "S4")
DEFAULT_QUOTAS: dict[str, int] = {"S1": 20, "S2": 15, "S3": 15, "S4": 10}
PER_OBJECT_CAP = 2
MAX_PANELS = 60

S2_STATUSES: frozenset[str] = frozenset(
    {"AMBIGUOUS_SAME_CLASS", "WILDCARD_UNKNOWN_CLASS", "UNIQUE_CLASS_COLOR", "UNIQUE_RELATION"}
)
SMALL_SIDE_PX = 32.0
LARGE_SIDE_PX = 64.0

VERDICTS: tuple[str, ...] = ("对", "错", "不确定")
ERROR_TYPES: tuple[str, ...] = ("类别错", "颜色错", "框不紧或截断", "遮挡误判", "车辆缺失或幻影")

STRATUM_DEFINITIONS: dict[str, str] = {
    "S1": "`color_status != VERIFIED`（目标对象在 S5 的颜色未验证）",
    "S2": "`uniqueness_status ∈ {AMBIGUOUS_SAME_CLASS, WILDCARD_UNKNOWN_CLASS, UNIQUE_CLASS_COLOR, UNIQUE_RELATION}`",
    "S3": "`short_side_px < 32`",
    "S4": "`uniqueness_status = UNIQUE_CLASS ∧ short_side_px ≥ 64`",
}


class PanelError(RuntimeError):
    """面板阶段的前置条件失败（缺依赖、缺图像、超面板上限、缺种子/配额行等）。

    **不继承 `EngAssetError`，也不携带失败收据闭集的 `reason`**（R1@K4 F3）：这些病因
    不在合同 §3 表 B 的闭集内，借用 `OUTPUT_PATH_FORBIDDEN` 会把「先跑 plan 后跑
    inventory」这种次序错误记成原件保护事件，误导操作员与停点核对。这类失败因此不写失败
    收据，只抛错并由 `finally` 清理未发布的 staging；若确需为其留收据，按 AC-6 修订 2 的
    路由在报告 §7 请接受角色追加 token，实现角色不自行扩大闭集。
    """

    def __init__(self, message: str, offending: Iterable[Any] = ()) -> None:
        super().__init__(message)
        self.offending = list(offending)


def _clear_directory(path: Path) -> None:
    """清空（并保留）一个 staging 目录：只删文件与空目录，不碰其他路径。"""
    path = Path(path)
    if path.exists():
        for item in sorted(path.rglob("*"), reverse=True):
            item.unlink() if item.is_file() else item.rmdir()
    path.mkdir(parents=True, exist_ok=True)


def resolve_panel_dir(repo_root: Path, panel_root: Path | None = None) -> Path:
    """面板与原图副本的落点（AC-4 修订 1 之后唯一合法写出目的地）。"""
    root = Path(panel_root) if panel_root is not None else Path(repo_root) / PANEL_ROOT
    return root / "panel"


def sample_key(seed: str, frame_id: str, object_id: str) -> str:
    return hashlib.sha256(f"{seed}{frame_id}{object_id}".encode("utf-8")).hexdigest()


def stratum_of(row: dict[str, Any], color_status: str | None) -> str | None:
    """按优先序归层；每行只属第一个命中层，不命中则不入层。"""
    if color_status is not None and color_status != "VERIFIED":
        return "S1"
    if row["uniqueness_status"] in S2_STATUSES:
        return "S2"
    side = row.get("short_side_px")
    if side is not None and side < SMALL_SIDE_PX:
        return "S3"
    if row["uniqueness_status"] == "UNIQUE_CLASS" and side is not None and side >= LARGE_SIDE_PX:
        return "S4"
    return None


def iter_instruction_rows(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


@dataclass
class SamplePlan:
    seed: str
    quotas: dict[str, int]
    denominators: dict[str, int]
    denominator_objects: dict[str, int]
    selected: list[dict[str, Any]]

    @property
    def taken(self) -> dict[str, int]:
        counts = {stratum: 0 for stratum in STRATA}
        for row in self.selected:
            counts[row["stratum"]] += 1
        return counts


def plan_sample(
    rows: Iterable[dict[str, Any]],
    color_status_by_object: dict[str, str],
    *,
    seed: str = DEFAULT_SEED,
    quotas: dict[str, int] | None = None,
) -> SamplePlan:
    """分层 + 层内确定性取样（AC-4）。返回的清单顺序 = 层序 → 抽样键升序。"""
    quotas = dict(quotas or DEFAULT_QUOTAS)
    pools: dict[str, list[dict[str, Any]]] = {stratum: [] for stratum in STRATA}
    objects: dict[str, set[str]] = {stratum: set() for stratum in STRATA}
    for row in rows:
        stratum = stratum_of(row, color_status_by_object.get(row["object_id"]))
        if stratum is None:
            continue
        pools[stratum].append(row)
        objects[stratum].add(row["object_id"])

    selected: list[dict[str, Any]] = []
    for stratum in STRATA:
        pool = sorted(
            pools[stratum], key=lambda item: sample_key(seed, item["frame_id"], item["object_id"])
        )
        per_object: dict[str, int] = {}
        taken = 0
        for row in pool:
            if taken >= quotas[stratum]:
                break
            if per_object.get(row["object_id"], 0) >= PER_OBJECT_CAP:
                continue
            per_object[row["object_id"]] = per_object.get(row["object_id"], 0) + 1
            taken += 1
            selected.append(
                {
                    "panel_index": len(selected) + 1,
                    "stratum": stratum,
                    "frame_id": row["frame_id"],
                    "object_id": row["object_id"],
                    "split": row["split"],
                    "uniqueness_status": row["uniqueness_status"],
                    "surface": row["surface"],
                    "short_side_px": row["short_side_px"],
                    "visible_norm_xywh": row["visible_norm_xywh"],
                    "sample_key": sample_key(seed, row["frame_id"], row["object_id"]),
                }
            )
    if len(selected) > MAX_PANELS:
        raise PanelError(f"抽样行数 {len(selected)} 超过面板上限 {MAX_PANELS}")
    return SamplePlan(
        seed=seed,
        quotas=quotas,
        denominators={stratum: len(pools[stratum]) for stratum in STRATA},
        denominator_objects={stratum: len(objects[stratum]) for stratum in STRATA},
        selected=selected,
    )


# --- label-audit.md 渲染与解析 -------------------------------------------

AUDIT_HEADER = f"# {WORK_ID} — 分层标签抽查（AC-4）"
SEED_LINE = "- 抽样种子（seed）：`{seed}`"
QUOTA_LINE = "- 配额（S1/S2/S3/S4）：`{quotas}`"
PANEL_TABLE_HEADER = (
    "| panel_index | stratum | split | frame_id | object_id | uniqueness_status | "
    "short_side_px | surface | overlay_sha256 |"
)
PANEL_TABLE_RULE = "|---|---|---|---|---|---|---|---|---|"
PENDING = "(pending)"


def render_audit_document(
    plan: SamplePlan,
    *,
    instructions_sha256: str,
    instruction_rows: int,
    overlay_sha256: dict[int, str] | None = None,
    panel_receipt_sha256: str | None = None,
    statistics_block: str | None = None,
    render_fix_receipt: str | None = None,
) -> str:
    overlay_sha256 = overlay_sha256 or {}
    taken = plan.taken
    lines = [
        AUDIT_HEADER,
        "",
        "本文件是 AC-4 的抽样契约与面板清单：**种子与配额必须先提交**，面板生成器",
        "在运行时解析本文件的 `git status --porcelain`（须为空）与",
        "`git log -1 --format=%H` 并写入 `panel-receipt.json`。本文件只存面板、分层",
        "统计与 Unity 日志条目指针，**不复制用户判定原文**（原文由接受/辅助角色代录进",
        f"`{UNITY_LOG_PATH.as_posix()}` 的 `{UNITY_LOG_ENTRY}` 条目，标 `OFFLINE_VISUAL_CHECK`，零 Play）。",
        "",
        "## 1. 抽样参数",
        "",
        SEED_LINE.format(seed=plan.seed),
        QUOTA_LINE.format(quotas="/".join(str(plan.quotas[s]) for s in STRATA)),
        f"- 抽样单位：指令逐行文件的一行 (帧, 对象)；域 = 对账域全部 {instruction_rows} 行",
        f"- 指令逐行文件 SHA-256：`{instructions_sha256}`",
        f"- 层内取样序：`SHA-256(seed‖frame_id‖object_id)` 升序；每对象每层 ≤ {PER_OBJECT_CAP} 行；"
        "层不足额时留空不回填",
        f"- 唯一图片总数上限：{MAX_PANELS}",
        "",
        "## 2. 分层定义、分母与实取数",
        "",
        "| 层 | 定义（按优先序归层，每行只属第一个命中层） | 分母（行） | 分母（去重对象） | 配额 | 实取 |",
        "|---|---|---|---|---|---|",
    ]
    for stratum in STRATA:
        lines.append(
            f"| {stratum} | {STRATUM_DEFINITIONS[stratum]} | {plan.denominators[stratum]} | "
            f"{plan.denominator_objects[stratum]} | {plan.quotas[stratum]} | {taken[stratum]} |"
        )
    lines += [
        "",
        f"合计实取 {len(plan.selected)} 行（上限 {MAX_PANELS}）。",
        "",
        "## 3. 面板清单",
        "",
        PANEL_TABLE_HEADER,
        PANEL_TABLE_RULE,
    ]
    for row in plan.selected:
        side = "" if row["short_side_px"] is None else f"{row['short_side_px']:.1f}"
        surface = row["surface"] if row["surface"] else NO_UNIQUE_PROGRAM_CELL
        digest = overlay_sha256.get(row["panel_index"], PENDING)
        lines.append(
            f"| {row['panel_index']} | {row['stratum']} | {row['split']} | `{row['frame_id']}` | "
            f"`{row['object_id']}` | {row['uniqueness_status']} | {side} | {surface} | `{digest}` |"
        )
    lines += [
        "",
        "## 4. 面板收据",
        "",
        f"- `panel-receipt.json` SHA-256：`{panel_receipt_sha256 or PENDING}`（首次生成收据，原字节保留）",
        (
            f"- 当前叠加图由 `{render_fix_receipt}` 记录的 AC-4 修订 2 重绘产出"
            "（移除插图、原帧完整、标题置于帧外；样本身份与原图副本不变）。"
            if render_fix_receipt
            else "- 当前叠加图为首次生成版本。"
        ),
        f"- 面板与原图副本落本地 `{(PANEL_ROOT / 'panel').as_posix()}/`（git 忽略）。",
        "",
        "## 5. 用户判定统计",
        "",
        "判定原文落点：`" + UNITY_LOG_PATH.as_posix() + "` 的 `" + UNITY_LOG_ENTRY + "` 条目"
        "（`OFFLINE_VISUAL_CHECK`，零 Play，由接受/辅助角色代录）。代录表列："
        "`| panel_index | 类别 | 颜色 | 框 | 错误类型 |`，判定取 `"
        + "` / `".join(VERDICTS)
        + "`，错误类型多选自闭集 `"
        + "` / `".join(ERROR_TYPES)
        + "`。",
        "",
        statistics_block or "**尚未取得用户判定**：本节由 `python3 -m tools.eng_asset.label_panel stats` "
        "只读该条目后回填；未判定不得计为通过，空层不计为通过。",
        "",
    ]
    return "\n".join(lines) + "\n"


def parse_audit_parameters(text: str) -> tuple[str, dict[str, int]]:
    """从已提交的 label-audit.md 解析种子与配额（生成器的唯一参数来源）。"""
    seed_match = re.search(r"抽样种子（seed）：`([^`]+)`", text)
    quota_match = re.search(r"配额（S1/S2/S3/S4）：`([0-9]+/[0-9]+/[0-9]+/[0-9]+)`", text)
    if not seed_match or not quota_match:
        raise PanelError("label-audit.md 缺少种子或配额行，无法生成面板")
    values = [int(part) for part in quota_match.group(1).split("/")]
    return seed_match.group(1), dict(zip(STRATA, values))


def parse_audit_panels(text: str) -> list[dict[str, Any]]:
    """解析清单 §3「面板清单」表：用户实际看到的冻结身份映射（C1-2）。

    统计必须按本表的 `panel_index → frame_id/object_id/stratum/surface/overlay_sha256`
    核对，不能用「重建计划的索引数量相等」代替身份相等。
    """
    panels: list[dict[str, Any]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped[1:-1].split("|")]
        if len(cells) != 9 or not cells[0].isdigit():
            continue
        panels.append(
            {
                "panel_index": int(cells[0]),
                "stratum": cells[1].strip("`"),
                "split": cells[2].strip("`"),
                "frame_id": cells[3].strip("`"),
                "object_id": cells[4].strip("`"),
                "uniqueness_status": cells[5].strip("`"),
                "surface": cells[7].strip("`"),
                "overlay_sha256": cells[8].strip("`"),
            }
        )
    return panels


def frozen_identity_mismatches(
    frozen: list[dict[str, Any]], plan: SamplePlan
) -> list[dict[str, Any]]:
    """冻结清单与重建计划逐条比身份；数量相等但对象不同也必须报出。"""
    problems: list[dict[str, Any]] = []
    rebuilt = {row["panel_index"]: row for row in plan.selected}
    if sorted(item["panel_index"] for item in frozen) != sorted(rebuilt):
        problems.append(
            {
                "problem": "PANEL_INDEX_SET_DIFFERS_FROM_MANIFEST",
                "manifest": sorted(item["panel_index"] for item in frozen),
                "rebuilt": sorted(rebuilt),
            }
        )
        return problems
    for item in frozen:
        row = rebuilt[item["panel_index"]]
        expected_surface = row["surface"] if row["surface"] else NO_UNIQUE_PROGRAM_CELL
        actual = {
            "frame_id": row["frame_id"],
            "object_id": row["object_id"],
            "stratum": row["stratum"],
            "surface": expected_surface,
        }
        recorded = {key: item[key] for key in ("frame_id", "object_id", "stratum", "surface")}
        if actual != recorded:
            problems.append(
                {
                    "problem": "PANEL_IDENTITY_DIFFERS_FROM_MANIFEST",
                    "panel_index": item["panel_index"],
                    "manifest": recorded,
                    "rebuilt": actual,
                }
            )
    return problems


def git_output(args: list[str], repo_root: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise PanelError(f"git {' '.join(args)} 失败：{result.stderr.strip()}")
    return result.stdout


def quota_file_commit(audit_path: Path, repo_root: Path) -> str:
    """种子/配额文件必须已提交且工作树干净，否则 `QUOTA_FILE_DIRTY`。"""
    rel = receipts.relative_to_root(audit_path, repo_root)
    porcelain = git_output(["status", "--porcelain", "--", rel], repo_root).strip()
    if porcelain:
        raise QuotaFileDirty(
            f"配额/种子文件有未提交改动：{rel}", offending=[{"path": rel, "porcelain": porcelain}]
        )
    commit = git_output(["log", "-1", "--format=%H", "--", rel], repo_root).strip()
    if not commit:
        raise QuotaFileDirty(
            f"配额/种子文件尚未提交：{rel}", offending=[{"path": rel, "porcelain": "<untracked>"}]
        )
    return commit


# --- 面板生成 -------------------------------------------------------------

BOX_OUTLINE = (255, 64, 0)
CAPTION_BG = (0, 0, 0)
CAPTION_FG = (255, 255, 255)
# 标题带高度：画布在原帧之外增加的边带（AC-4 修订 2；原帧像素零覆盖）。
CAPTION_HEIGHT = 16
# 无唯一程序时的标题占位符（ASCII：默认位图字体不含中文字形）。
NO_PROGRAM_CAPTION = "(no unique program)"
# 清单表格里 surface 为 null 时的单元格文本（与 render_audit_document 一致）。
NO_UNIQUE_PROGRAM_CELL = "（无唯一程序）"


def _load_pillow():
    """Pillow 只负责解码/编码；缺依赖 fail-closed，不降级成不画框的副本。"""
    try:
        from PIL import Image, ImageDraw  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - 依赖缺失路径
        raise PanelError(
            "面板生成需要 Pillow；本仓库已有 `.venv-yoloe`（Pillow 12.3.0）可用，"
            "例如 `.venv-yoloe/bin/python -m tools.eng_asset.label_panel panels`。"
            "本项不下载任何依赖。"
        ) from exc
    return Image, ImageDraw


def panel_layout(width: int, height: int, band: int = CAPTION_HEIGHT) -> dict[str, Any]:
    """画布布局：原帧整幅下移 `band` 像素，标题带占据帧外的顶部边带。

    AC-4 修订 2：原帧不缩放、不裁剪、不被任何叠加物覆盖；画布加边带后，框与原帧
    同步平移同一偏移量。本函数是纯算术，无需图像库，供具名回归直接核对。
    """
    return {
        "canvas": (width, height + band),
        "frame_origin": (0, band),
        "offset": (0, band),
    }


def translated_box(
    box_norm: list[float] | None, width: int, height: int, offset: tuple[int, int]
) -> tuple[float, ...] | None:
    """归一化 top-left xywh → 画布像素坐标（含与原帧相同的平移）。"""
    if not box_norm:
        return None
    x0 = box_norm[0] * width + offset[0]
    y0 = box_norm[1] * height + offset[1]
    return (x0, y0, x0 + box_norm[2] * width, y0 + box_norm[3] * height)


def draw_panel(source: Path, destination: Path, row: dict[str, Any]) -> None:
    """只画该行的框与 surface，且**不覆盖原帧任何像素**（AC-4 修订 2）。

    首版把标题栏画在图内、并对小目标叠加放大插图；接受侧裁定「插图覆盖了原图的大部分
    区域，原坐标框最后被画在已替换的像素上」不满足 AC-4。本版最小修复：画布在原帧上方
    加一条边带放标题，原帧整幅粘贴、不缩放不裁剪，框按同一偏移平移后叠加。
    """
    Image, ImageDraw = _load_pillow()
    with Image.open(source) as handle:
        frame = handle.convert("RGB")
    width, height = frame.size
    layout = panel_layout(width, height)
    canvas = Image.new("RGB", layout["canvas"], CAPTION_BG)
    canvas.paste(frame, layout["frame_origin"])
    draw = ImageDraw.Draw(canvas)
    caption = (
        f"#{row['panel_index']} [{row['stratum']}] {row['object_id']} | "
        f"{row['uniqueness_status']} | {row['surface'] or NO_PROGRAM_CAPTION}"
    )
    # 标题用 PIL 默认位图字体绘制，非 ASCII 会渲染成方块，故占位符取 ASCII；
    # surface 本身由 tier1_lang.render 产出，是英文表面形。
    draw.text((2, 2), caption, fill=CAPTION_FG)
    corners = translated_box(row["visible_norm_xywh"], width, height, layout["offset"])
    if corners is not None:
        draw.rectangle(list(corners), outline=BOX_OUTLINE, width=2)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # 叠加图是对已压缩原帧的二次编码。质量 95 + `subsampling=0`（4:4:4）保住色度边缘：
    # 默认 4:2:0 会在标题带与原帧的强色度跳变处产生数十级偏差，正好落在判框的边界上。
    canvas.save(destination, format="JPEG", quality=95, subsampling=0)


def image_sha_index(inventory_payload: dict[str, Any]) -> dict[str, str]:
    """S1 `records[].sha256`：面板读图时按此核验字节（AC-1 释义）。"""
    return {
        record["path"]: record["sha256"]
        for record in inventory_payload["records"]
        if record["kind"] == "image"
    }


# --- 判定统计（只读 Unity 日志条目）--------------------------------------


VERDICT_SCHEMA_LINE = "Schema: p1-eng-asset-001/verdicts/v1"
VERDICT_STATUS_LINE = "Status: OFFLINE_VISUAL_CHECK"
VERDICT_MANIFEST_LINE = "Panel manifest: docs/evidence/P1-ENG-ASSET-001-label-audit.md"
VERDICT_STATE_PREFIX = "Judgment state:"
VERDICT_STATES = ("PENDING", "COMPLETE")
VERDICT_TABLE_SECTION = "### 结构化判定"
VERDICT_FREETEXT_SECTION = "### 用户判定原文"
VERDICT_TABLE_HEADER = "| panel_index | 类别 | 颜色 | 框 | 错误类型 |"
VERDICT_TABLE_RULE = "|---|---|---|---|---|"


def _fail(problems: list[dict[str, Any]]) -> None:
    raise receipts.VerdictFormatMismatch(
        "代录机读格式 v1 不满足：" + "；".join(str(item.get("problem")) for item in problems),
        offending=problems,
    )


def read_unity_verdicts(
    path: Path, entry: str = UNITY_LOG_ENTRY, *, expected_indices: list[int] | None = None
) -> list[dict[str, Any]]:
    """严格解析代录机读格式 v1；任一不符即 `VERDICT_FORMAT_MISMATCH`（AC-4 修订 3）。

    只消费 `### 结构化判定` 的结构化表；`### 用户判定原文` 存逐字反馈，不解析。
    没有「静默丢行」「缺失当不确定」「残缺表出部分统计」的分支：要么整表合法并返回
    与清单逐项相等的判定，要么抛异常由调用方写失败收据。
    """
    problems: list[dict[str, Any]] = []
    if not Path(path).is_file():
        _fail([{"problem": "ENTRY_LOG_MISSING", "path": receipts.relative_to_root(Path(path))}])
    lines = Path(path).read_text(encoding="utf-8").splitlines()

    heading = f"## {entry}"
    starts = [i for i, line in enumerate(lines) if line.strip() == heading]
    if len(starts) != 1:
        _fail([{"problem": "ENTRY_MISSING_OR_DUPLICATED", "count": len(starts), "heading": heading}])
    begin = starts[0]
    stop = len(lines)
    for index in range(begin + 1, len(lines)):
        stripped = lines[index].lstrip()
        if stripped.startswith("## ") or (stripped.startswith("# ") and not stripped.startswith("## ")):
            stop = index
            break
    body = lines[begin + 1 : stop]
    offset = begin + 2  # 1-based 行号

    def numbered(local: int) -> int:
        return offset + local

    for required in (VERDICT_SCHEMA_LINE, VERDICT_STATUS_LINE, VERDICT_MANIFEST_LINE):
        if sum(1 for line in body if line.strip() == required) != 1:
            problems.append({"problem": "REQUIRED_LINE_MISSING_OR_DUPLICATED", "line_text": required})
    states = [line.strip() for line in body if line.strip().startswith(VERDICT_STATE_PREFIX)]
    if len(states) != 1 or states[0].split(":", 1)[1].strip() not in VERDICT_STATES:
        problems.append({"problem": "JUDGMENT_STATE_INVALID", "found": states})
    if problems:
        _fail(problems)
    state = states[0].split(":", 1)[1].strip()
    if state != "COMPLETE":
        _fail([{"problem": "JUDGMENT_STATE_NOT_COMPLETE", "found": state}])

    section_starts = [i for i, line in enumerate(body) if line.strip() == VERDICT_TABLE_SECTION]
    if len(section_starts) != 1:
        _fail([{"problem": "TABLE_SECTION_MISSING_OR_DUPLICATED", "count": len(section_starts)}])
    table_begin = section_starts[0]
    table_stop = len(body)
    for index in range(table_begin + 1, len(body)):
        if body[index].lstrip().startswith("#"):
            table_stop = index
            break
    block = [(index, body[index]) for index in range(table_begin + 1, table_stop)]
    content = [(index, line) for index, line in block if line.strip()]
    if len(content) < 2:
        _fail([{"problem": "TABLE_MISSING", "line": numbered(table_begin)}])
    if content[0][1].strip() != VERDICT_TABLE_HEADER:
        _fail([{"problem": "TABLE_HEADER_MISMATCH", "line": numbered(content[0][0]), "found": content[0][1].strip()}])
    if content[1][1].strip() != VERDICT_TABLE_RULE:
        _fail([{"problem": "TABLE_RULE_MISMATCH", "line": numbered(content[1][0]), "found": content[1][1].strip()}])

    rows: list[dict[str, Any]] = []
    seen: list[int] = []
    for index, line in content[2:]:
        number = numbered(index)
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            problems.append({"problem": "ROW_NOT_A_TABLE_ROW", "line": number, "found": stripped})
            continue
        cells = [cell.strip() for cell in stripped[1:-1].split("|")]
        if len(cells) != 5:
            problems.append({"problem": "ROW_COLUMN_COUNT", "line": number, "columns": len(cells)})
            continue
        raw_index, verdicts, errors = cells[0], cells[1:4], cells[4]
        if any("`" in cell for cell in cells):
            problems.append({"problem": "BACKTICK_NOT_ALLOWED", "line": number})
            continue
        if not raw_index.isdigit() or raw_index != str(int(raw_index)) or int(raw_index) < 1:
            problems.append({"problem": "PANEL_INDEX_MALFORMED", "line": number, "found": raw_index})
            continue
        panel_index = int(raw_index)
        if any(verdict not in VERDICTS for verdict in verdicts):
            problems.append({"problem": "VERDICT_VALUE_INVALID", "line": number, "found": verdicts})
            continue
        error_types: list[str] = []
        if errors:
            if any(separator in errors for separator in (",", "，", "/", ";", "；")):
                problems.append({"problem": "ERROR_SEPARATOR_INVALID", "line": number, "found": errors})
                continue
            error_types = [item.strip() for item in errors.split("、")]
            if any(item not in ERROR_TYPES for item in error_types):
                problems.append({"problem": "ERROR_TYPE_UNKNOWN", "line": number, "found": errors})
                continue
            if len(set(error_types)) != len(error_types):
                problems.append({"problem": "ERROR_TYPE_DUPLICATED", "line": number, "found": errors})
                continue
            if error_types != [item for item in ERROR_TYPES if item in error_types]:
                problems.append({"problem": "ERROR_TYPE_ORDER", "line": number, "found": errors})
                continue
        seen.append(panel_index)
        rows.append(
            {
                "panel_index": panel_index,
                "class": verdicts[0],
                "color": verdicts[1],
                "box": verdicts[2],
                "error_types": error_types,
                "line": number,
            }
        )
    if problems:
        _fail(problems)
    if seen != sorted(seen):
        _fail([{"problem": "PANEL_INDEX_NOT_ASCENDING", "found": seen}])
    if len(set(seen)) != len(seen):
        duplicates = sorted({value for value in seen if seen.count(value) > 1})
        _fail([{"problem": "PANEL_INDEX_DUPLICATED", "found": duplicates}])
    if expected_indices is not None and seen != list(expected_indices):
        _fail(
            [
                {
                    "problem": "PANEL_INDEX_SET_MISMATCH",
                    "missing": sorted(set(expected_indices) - set(seen)),
                    "unexpected": sorted(set(seen) - set(expected_indices)),
                    "rows": len(seen),
                    "manifest_rows": len(list(expected_indices)),
                }
            ]
        )
    return rows


def statistics(plan: SamplePlan, verdicts: list[dict[str, Any]]) -> dict[str, Any]:
    """逐层计数；「不确定」单独计数、不计为对，空层不计为通过。"""
    by_index = {row["panel_index"]: row for row in verdicts}
    per_stratum: dict[str, Any] = {}
    for stratum in STRATA:
        panels = [row for row in plan.selected if row["stratum"] == stratum]
        judged = [by_index[row["panel_index"]] for row in panels if row["panel_index"] in by_index]
        aspect_counts = {
            aspect: {verdict: sum(1 for row in judged if row[aspect] == verdict) for verdict in VERDICTS}
            for aspect in ("class", "color", "box")
        }
        error_counts = {
            name: sum(1 for row in judged if name in row["error_types"]) for name in ERROR_TYPES
        }
        per_stratum[stratum] = {
            "panels": len(panels),
            "judged": len(judged),
            # AC-4 修订 3 之后 unjudged 恒为 0：索引集合与清单逐项相等是解析前置，
            # 不相等根本不会走到这里（失败退出）。保留该列以便核对轮直接看见 0。
            "unjudged": len(panels) - len(judged),
            "empty_stratum": len(panels) == 0,
            "aspects": aspect_counts,
            "error_types": error_counts,
        }
    return {
        "entry": UNITY_LOG_ENTRY,
        "entry_path": UNITY_LOG_PATH.as_posix(),
        "verdicts_found": len(verdicts),
        "panels": len(plan.selected),
        "per_stratum": per_stratum,
        "note": "n ≤ 60 的描述性抽查，不构成审计通过或 F1–F4 结论；"
        "「不确定」单独计数、不计为对；空层不计为通过；未判定面板计入 unjudged。",
    }


def render_statistics_block(stats: dict[str, Any]) -> str:
    if not stats["verdicts_found"]:
        return (
            "**尚未取得用户判定**："
            f"`{stats['entry_path']}` 中未找到 `{stats['entry']}` 条目的判定表；"
            "未判定不得计为通过，空层不计为通过。"
        )
    lines = [
        f"判定来源条目：`{stats['entry']}`（`{stats['entry_path']}`，只读）。",
        "",
        "| 层 | 面板 | 已判定 | 未判定 | 类别 对/错/不确定 | 颜色 对/错/不确定 | 框 对/错/不确定 |",
        "|---|---|---|---|---|---|---|",
    ]
    for stratum in STRATA:
        item = stats["per_stratum"][stratum]
        cells = []
        for aspect in ("class", "color", "box"):
            counts = item["aspects"][aspect]
            cells.append("/".join(str(counts[verdict]) for verdict in VERDICTS))
        lines.append(
            f"| {stratum} | {item['panels']} | {item['judged']} | {item['unjudged']} | "
            + " | ".join(cells)
            + " |"
        )
    errors = stats["per_stratum"]
    totals = {
        name: sum(errors[stratum]["error_types"][name] for stratum in STRATA) for name in ERROR_TYPES
    }
    lines += [
        "",
        "错误类型合计（多选）：" + "；".join(f"{name} {count}" for name, count in totals.items()),
        "",
        stats["note"],
    ]
    return "\n".join(lines)


# --- 阶段驱动 -------------------------------------------------------------


def _load_color_status(
    artifact_root: Path, attempt: str, manifest: InputManifest
) -> dict[str, str]:
    path = artifact_root / "field_catalog" / attempt / "field_catalog.json"
    manifest.record(path, source="首次读取现算")
    payload = json.loads(path.read_text(encoding="utf-8"))["payload"]
    return {key: value["color_status"] for key, value in payload["objects"].items()}


def _instructions_path(local_root: Path) -> Path:
    path = local_root / "instructions.ndjson.gz"
    if not path.is_file():
        raise PanelError(f"指令逐行文件缺失：{path}；先运行 tools.eng_asset.inventory run")
    return path


def build_plan(
    *,
    artifact_root: Path,
    attempt: str,
    local_root: Path,
    manifest: InputManifest,
    seed: str,
    quotas: dict[str, int] | None,
) -> tuple[SamplePlan, Path, int]:
    instructions = _instructions_path(local_root)
    manifest.record(instructions, source="本项 A2 派生工件（首次读取现算）")
    color_status = _load_color_status(artifact_root, attempt, manifest)
    rows = list(iter_instruction_rows(instructions))
    plan = plan_sample(rows, color_status, seed=seed, quotas=quotas)
    return plan, instructions, len(rows)


def stage_plan(
    *,
    repo_root: Path = PROJECT_ROOT,
    artifact_root: Path | None = None,
    attempt: str = "attempt-2",
    local_root: Path | None = None,
    evidence_dir: Path | None = None,
    seed: str = DEFAULT_SEED,
    quotas: dict[str, int] | None = None,
) -> dict[str, Any]:
    """阶段 1：写种子/配额/分母/清单到 label-audit.md（提交后才能生成面板）。"""
    repo_root = Path(repo_root)
    artifact_root = Path(artifact_root) if artifact_root else repo_root / "runtime/dist-data"
    local = Path(local_root) if local_root else repo_root / receipts.LOCAL_ROOT
    evidence = Path(evidence_dir) if evidence_dir else repo_root / EVIDENCE_DIR
    writer = ReceiptWriter(local, repo_root)
    manifest = InputManifest(repo_root=repo_root)
    started = time.monotonic()
    try:
        plan, instructions, row_count = build_plan(
            artifact_root=artifact_root,
            attempt=attempt,
            local_root=local,
            manifest=manifest,
            seed=seed,
            quotas=quotas,
        )
        document = render_audit_document(
            plan,
            instructions_sha256=receipts.sha256_file(instructions),
            instruction_rows=row_count,
        )
        audit_path = receipts.assert_output_allowed(evidence / AUDIT_FILENAME, repo_root)
        # A2 写出闭集不含额外的计划文件：抽样清单只落 label-audit.md，
        # 计划本身由种子/配额确定性复算，不另存中间态。
        # C1-1：输入核验必须先于发布——失败时本次不得留下任何已发布的派生工件。
        after = manifest.recompute()
        mismatches = manifest.diff(after)
        if mismatches:
            raise receipts.InputHashChanged("执行前后输入清单不符", offending=mismatches)
        writer.save_input_manifest("panel-plan", manifest, after, mismatches, successful=True)
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(document, encoding="utf-8")
        writer.write_run_receipt(
            "panel-plan",
            started=started,
            outputs=[receipts.output_record(audit_path)],
            extra={
                "seed": plan.seed,
                "quotas": plan.quotas,
                "denominators": plan.denominators,
                "taken": plan.taken,
                "panels": len(plan.selected),
            },
        )
        return {"plan": plan, "audit_path": audit_path}
    except receipts.EngAssetError as exc:
        after = manifest.recompute() if manifest.entries else {}
        writer.save_input_manifest("panel-plan", manifest, after, manifest.diff(after), successful=False)
        # F3：只为闭集内的真实病因写失败收据（与 panel / render-fix / stats 同口径）；
        # `PanelError` 已不属 `EngAssetError`，不会走到这里。
        if isinstance(
            exc, (QuotaFileDirty, receipts.InputHashChanged, receipts.OutputPathForbidden)
        ) and exc.reason in receipts.FAILURE_REASONS:
            writer.write_failure_receipt("panel-plan", exc.reason, exc.offending, message=str(exc))
        raise


def stage_panels(
    *,
    repo_root: Path = PROJECT_ROOT,
    artifact_root: Path | None = None,
    attempt: str = "attempt-2",
    local_root: Path | None = None,
    evidence_dir: Path | None = None,
    panel_root: Path | None = None,
) -> dict[str, Any]:
    """阶段 2：核验配额文件已提交且干净 → 生成面板 → 回填 overlay_sha256。"""
    repo_root = Path(repo_root)
    artifact_root = Path(artifact_root) if artifact_root else repo_root / "runtime/dist-data"
    local = Path(local_root) if local_root else repo_root / receipts.LOCAL_ROOT
    evidence = Path(evidence_dir) if evidence_dir else repo_root / EVIDENCE_DIR
    writer = ReceiptWriter(local, repo_root)
    manifest = InputManifest(repo_root=repo_root)
    started = time.monotonic()
    audit_path = evidence / AUDIT_FILENAME
    created_staging: Path | None = None
    # F5：本地收据根与面板根在任何写入前一并检查。
    receipts.assert_output_allowed(local, repo_root)
    try:
        if not audit_path.is_file():
            raise QuotaFileDirty(
                f"配额/种子文件不存在：{receipts.relative_to_root(audit_path, repo_root)}",
                offending=[receipts.relative_to_root(audit_path, repo_root)],
            )
        commit = quota_file_commit(audit_path, repo_root)
        manifest.record(audit_path, source="首次读取现算")
        seed, quotas = parse_audit_parameters(audit_path.read_text(encoding="utf-8"))
        plan, instructions, row_count = build_plan(
            artifact_root=artifact_root,
            attempt=attempt,
            local_root=local,
            manifest=manifest,
            seed=seed,
            quotas=quotas,
        )

        inventory_path = artifact_root / "inventory" / attempt / "inventory.json"
        manifest.record(inventory_path, source="首次读取现算")
        sha_index = image_sha_index(
            json.loads(inventory_path.read_text(encoding="utf-8"))["payload"]
        )

        panel_dir = receipts.assert_output_allowed(
            resolve_panel_dir(repo_root, panel_root), repo_root
        )
        original_dir = panel_dir / "original"
        # C1-1：先落 staging，全部输入核验通过后再整体发布；中途失败时既有面板原样保留。
        # F5：staging 变量只在路径检查通过后绑定，`finally` 才有东西可清理；被拒的禁写根
        # 下即使同名目录存在也绝不触碰。
        staging = receipts.assert_output_allowed(panel_dir.parent / ".staging-panel", repo_root)
        created_staging = staging
        _clear_directory(staging)
        staged_panel = staging / "panel"
        staged_original = staged_panel / "original"
        staged_panel.mkdir(parents=True, exist_ok=True)
        staged_original.mkdir(parents=True, exist_ok=True)
        overlays: dict[int, str] = {}
        panel_records: list[dict[str, Any]] = []
        for row in plan.selected:
            source = repo_root / row["frame_id"]
            if not source.is_file():
                raise PanelError(f"归档帧缺失：{row['frame_id']}")
            declared = sha_index.get(row["frame_id"])
            entry = manifest.record(
                source, source="S1 records[].sha256" if declared else "首次读取现算", sha256=declared
            )
            index = row["panel_index"]
            destination = staged_panel / f"panel-{index:03d}.jpg"
            draw_panel(source, destination, row)
            shutil.copyfile(source, staged_original / f"panel-{index:03d}-original.jpg")
            digest = receipts.sha256_file(destination)
            overlays[index] = digest
            panel_records.append(
                {
                    "panel_index": index,
                    "stratum": row["stratum"],
                    "frame_id": row["frame_id"],
                    "object_id": row["object_id"],
                    "source_sha256": entry.sha256,
                    "overlay_sha256": digest,
                    "overlay_bytes": destination.stat().st_size,
                }
            )

        after = manifest.recompute()
        mismatches = manifest.diff(after)
        if mismatches:
            raise receipts.InputHashChanged("执行前后输入清单不符", offending=mismatches)

        # 核验通过才发布：先整体检查全部目的地（含收据落点），再逐件发布（F5）。
        for destination in (panel_dir, original_dir, local / PANEL_RECEIPT_NAME):
            receipts.assert_output_allowed(destination, repo_root)
        panel_dir.mkdir(parents=True, exist_ok=True)
        original_dir.mkdir(parents=True, exist_ok=True)
        for staged_file in sorted(staged_panel.glob("*.jpg")):
            staged_file.replace(panel_dir / staged_file.name)
        for staged_file in sorted(staged_original.glob("*.jpg")):
            staged_file.replace(original_dir / staged_file.name)
        _clear_directory(staging)

        receipt_document = {
            "schema_version": PANEL_RECEIPT_SCHEMA,
            "work_id": WORK_ID,
            "utc": receipts.utc_stamp(),
            "quota_file": receipts.relative_to_root(audit_path, repo_root),
            "quota_file_commit": commit,
            "quota_file_porcelain_empty": True,
            "seed": seed,
            "quotas": quotas,
            "input_manifest_sha256": receipts.sha256_file(writer.manifest_path())
            if writer.manifest_path().is_file()
            else None,
            "panels": panel_records,
        }
        panel_receipt = receipts.assert_output_allowed(local / PANEL_RECEIPT_NAME, repo_root)
        panel_receipt.write_text(
            json.dumps(receipt_document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        audit_path.write_text(
            render_audit_document(
                plan,
                instructions_sha256=receipts.sha256_file(instructions),
                instruction_rows=row_count,
                overlay_sha256=overlays,
                panel_receipt_sha256=receipts.sha256_file(panel_receipt),
            ),
            encoding="utf-8",
        )
        writer.save_input_manifest("panel", manifest, after, mismatches, successful=True)
        writer.write_run_receipt(
            "panel",
            started=started,
            outputs=[receipts.output_record(audit_path), receipts.output_record(panel_receipt)],
            extra={
                "quota_file_commit": commit,
                "panels": len(panel_records),
                "panel_bytes": sum(item["overlay_bytes"] for item in panel_records),
                "local_dir_bytes": sum(
                    item.stat().st_size for item in local.rglob("*") if item.is_file()
                ),
            },
        )
        return {"plan": plan, "panels": panel_records, "quota_file_commit": commit}
    except receipts.EngAssetError as exc:
        after = manifest.recompute() if manifest.entries else {}
        writer.save_input_manifest("panel", manifest, after, manifest.diff(after), successful=False)
        if exc.reason in receipts.FAILURE_REASONS and isinstance(exc, (QuotaFileDirty, receipts.InputHashChanged, receipts.OutputPathForbidden)):
            writer.write_failure_receipt("panel", exc.reason, exc.offending, message=str(exc))
        raise
    finally:
        # 未发布的 staging 一律清理，但只清理**本次实际创建**的那一个（F5）。
        if created_staging is not None and created_staging.exists():
            _clear_directory(created_staging)
            created_staging.rmdir()


def stage_relocate(
    *,
    repo_root: Path = PROJECT_ROOT,
    local_root: Path | None = None,
    panel_root: Path | None = None,
    evidence_dir: Path | None = None,
) -> dict[str, Any]:
    """AC-4 修订 1：把同一批面板与原图副本搬到新落点，逐文件核对后再删旧件。

    不重新抽样、不重新渲染、不增加看图轮次：文件名、逐文件字节与 SHA-256、
    `panel_index` / `frame_id` / `object_id` / `stratum` / `surface` / 种子与配额
    全部不变。`panel-receipt.json` 与既有执行收据**原字节保留**，不改写成
    「在新位置生成」；迁移本身另写 `receipts/run-relocate-<utc>.json`。
    任一文件核对不相等即 fail-closed：保留源副本、写失败收据、不删旧件。
    """
    repo_root = Path(repo_root)
    local = Path(local_root) if local_root else repo_root / receipts.LOCAL_ROOT
    evidence = Path(evidence_dir) if evidence_dir else repo_root / EVIDENCE_DIR
    destination = receipts.assert_output_allowed(
        resolve_panel_dir(repo_root, panel_root), repo_root
    )
    source = local / "panel"
    writer = ReceiptWriter(local, repo_root)
    started = time.monotonic()

    if not source.is_dir():
        raise PanelError(f"旧落点不存在，无可迁移面板：{source}")
    sources = sorted(item for item in source.rglob("*.jpg") if item.is_file())
    if not sources:
        raise PanelError(f"旧落点没有 jpg 可迁移：{source}")

    before = [
        {
            "old_path": receipts.relative_to_root(item, repo_root),
            "new_path": receipts.relative_to_root(destination / item.relative_to(source), repo_root),
            "bytes": item.stat().st_size,
            "sha256": receipts.sha256_file(item),
        }
        for item in sources
    ]

    # 1) 先复制并逐文件核对，旧件一个都不删。
    mismatches: list[dict[str, Any]] = []
    for item, record in zip(sources, before):
        target = destination / item.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item, target)
        actual_bytes, actual_sha = target.stat().st_size, receipts.sha256_file(target)
        if (actual_bytes, actual_sha) != (record["bytes"], record["sha256"]):
            mismatches.append(
                {
                    "path": record["new_path"],
                    "expected": {"bytes": record["bytes"], "sha256": record["sha256"]},
                    "actual": {"bytes": actual_bytes, "sha256": actual_sha},
                }
            )
    if mismatches:
        # 失败原因取既有闭集里语义最贴的一个：搬运后字节/哈希与源不符。
        writer.write_failure_receipt(
            "relocate", "INPUT_HASH_CHANGED", mismatches, message="迁移后逐文件核对不相等，保留源副本"
        )
        raise receipts.InputHashChanged("迁移后逐文件核对不相等", offending=mismatches)

    # 2) 全部相等才移除旧落点的派生图片（归档原图不在此列，从未被触碰）。
    for item in sources:
        item.unlink()
    for directory in sorted((d for d in source.rglob("*") if d.is_dir()), reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()
    if source.is_dir() and not any(source.iterdir()):
        source.rmdir()

    after = [
        {
            "path": record["new_path"],
            "bytes": (repo_root / record["new_path"]).stat().st_size,
            "sha256": receipts.sha256_file(repo_root / record["new_path"]),
        }
        for record in before
    ]
    if [(r["bytes"], r["sha256"]) for r in before] != [(r["bytes"], r["sha256"]) for r in after]:
        raise receipts.InputHashChanged("迁移后复核不相等", offending=after)
    panel_receipt = local / PANEL_RECEIPT_NAME
    document_extra = {
        "ruling": RELOCATE_RULING,
        "old_root": receipts.relative_to_root(source, repo_root),
        "new_root": receipts.relative_to_root(destination, repo_root),
        "mapping": before,
        "counts": {"before": len(before), "after": len(after)},
        "bytes": {
            "before": sum(record["bytes"] for record in before),
            "after": sum(record["bytes"] for record in after),
        },
        "panel_receipt_sha256_preserved": receipts.sha256_file(panel_receipt)
        if panel_receipt.is_file()
        else None,
        "old_root_jpg_remaining": len(list(source.rglob("*.jpg"))) if source.is_dir() else 0,
        "resampled": False,
        "rerendered": False,
        "extra_viewing_rounds": 0,
    }
    receipt = writer.write_run_receipt("relocate", started=started, outputs=[], extra=document_extra)

    # 3) 清单指向新落点与迁移收据（只改这一行，不重渲染逐张清单）。
    audit_path = evidence / AUDIT_FILENAME
    if audit_path.is_file():
        text = audit_path.read_text(encoding="utf-8")
        old_line = f"- 面板与原图副本落本地 `{receipts.LOCAL_ROOT.as_posix()}/panel/`（git 忽略）。"
        new_line = (
            f"- 面板与原图副本落本地 `{receipts.relative_to_root(destination, repo_root)}/`（git 忽略）；"
            f"按 {RELOCATE_RULING} 自 `{receipts.relative_to_root(source, repo_root)}/` 原字节迁移，"
            f"迁移收据 `{receipts.relative_to_root(receipt, repo_root)}`。"
        )
        if old_line in text:
            audit_path.write_text(text.replace(old_line, new_line), encoding="utf-8")

    return {
        "moved": len(before),
        "receipt": receipts.relative_to_root(receipt, repo_root),
        "new_root": document_extra["new_root"],
        "bytes": document_extra["bytes"],
    }


def stage_render_fix(
    *,
    repo_root: Path = PROJECT_ROOT,
    artifact_root: Path | None = None,
    attempt: str = "attempt-2",
    local_root: Path | None = None,
    evidence_dir: Path | None = None,
    panel_root: Path | None = None,
) -> dict[str, Any]:
    """AC-4 修订 2：只重绘叠加图，样本身份与原图副本一律不动。

    底图取**已存在的原图副本**（`panel/original/*.jpg`），不重新读归档、不重新抽样、
    不增加看图轮次。配额文件须已提交且干净，运行时绑定其提交（与首次生成同一前置）。
    """
    repo_root = Path(repo_root)
    artifact_root = Path(artifact_root) if artifact_root else repo_root / "runtime/dist-data"
    local = Path(local_root) if local_root else repo_root / receipts.LOCAL_ROOT
    evidence = Path(evidence_dir) if evidence_dir else repo_root / EVIDENCE_DIR
    panel_dir = receipts.assert_output_allowed(resolve_panel_dir(repo_root, panel_root), repo_root)
    writer = ReceiptWriter(local, repo_root)
    manifest = InputManifest(repo_root=repo_root)
    started = time.monotonic()
    audit_path = evidence / AUDIT_FILENAME
    created_staging: Path | None = None
    receipts.assert_output_allowed(local, repo_root)
    try:
        commit = quota_file_commit(audit_path, repo_root)
        manifest.record(audit_path, source="首次读取现算")
        seed, quotas = parse_audit_parameters(audit_path.read_text(encoding="utf-8"))
        plan, instructions, row_count = build_plan(
            artifact_root=artifact_root,
            attempt=attempt,
            local_root=local,
            manifest=manifest,
            seed=seed,
            quotas=quotas,
        )
        panel_receipt = local / PANEL_RECEIPT_NAME
        previous = {}
        if panel_receipt.is_file():
            document = json.loads(panel_receipt.read_text(encoding="utf-8"))
            previous = {item["panel_index"]: item for item in document["panels"]}

        staging = receipts.assert_output_allowed(panel_dir.parent / ".staging-render", repo_root)
        created_staging = staging
        _clear_directory(staging)
        records: list[dict[str, Any]] = []
        for row in plan.selected:
            index = row["panel_index"]
            overlay = panel_dir / f"panel-{index:03d}.jpg"
            original = panel_dir / "original" / f"panel-{index:03d}-original.jpg"
            if not original.is_file():
                raise PanelError(f"原图副本缺失，无法只重绘叠加图：{original}")
            before = (
                {"bytes": overlay.stat().st_size, "sha256": receipts.sha256_file(overlay)}
                if overlay.is_file()
                else None
            )
            # C1-5：重绘实际读取的 60 张原图副本必须登记为本阶段输入。
            original_sha = manifest.record(original, source="本项 A2 原图副本（首次读取现算）").sha256
            # C1-1：重绘先落 staging，核验通过后才覆盖既有叠加图。
            staged_overlay = staging / overlay.name
            draw_panel(original, staged_overlay, row)
            records.append(
                {
                    "panel_index": index,
                    "stratum": row["stratum"],
                    "frame_id": row["frame_id"],
                    "object_id": row["object_id"],
                    "surface": row["surface"],
                    "original_sha256": original_sha,
                    "original_sha256_unchanged": original_sha
                    == receipts.sha256_file(original),
                    "original_registered_as_input": True,
                    "source_sha256_from_generation": previous.get(index, {}).get("source_sha256"),
                    "before": before,
                    "after": {
                        "bytes": staged_overlay.stat().st_size,
                        "sha256": receipts.sha256_file(staged_overlay),
                    },
                }
            )

        relocate = sorted((local / RECEIPTS_SUBDIR).glob("run-relocate-*.json"))
        extra = {
            "ruling": "AC-4 修订 2（提案「待裁定」补充裁定，2026-09-08）",
            "quota_file": receipts.relative_to_root(audit_path, repo_root),
            "quota_file_commit": commit,
            "seed": seed,
            "quotas": quotas,
            "panels": records,
            "identity_unchanged": {
                "panel_index_frame_object_surface": True,
                "seed_and_quotas": True,
                "original_copies_rewritten": 0,
                "resampled": False,
                "extra_viewing_rounds": 0,
            },
            "prior_receipts": {
                "panel_receipt": receipts.relative_to_root(panel_receipt, repo_root)
                if panel_receipt.is_file()
                else None,
                "panel_receipt_sha256_preserved": receipts.sha256_file(panel_receipt)
                if panel_receipt.is_file()
                else None,
                "relocate_receipt": receipts.relative_to_root(relocate[-1], repo_root)
                if relocate
                else None,
            },
            "renderer": {
                "inset_removed": True,
                "caption_outside_frame": True,
                "caption_band_px": CAPTION_HEIGHT,
                "source_frame_scaled_or_cropped": False,
            },
        }
        after = manifest.recompute()
        mismatches = manifest.diff(after)
        if mismatches:
            raise receipts.InputHashChanged("执行前后输入清单不符", offending=mismatches)
        # 核验通过才发布：staging → 覆盖既有叠加图（原图副本一律不动）。
        for staged_file in sorted(staging.glob("*.jpg")):
            staged_file.replace(panel_dir / staged_file.name)
        _clear_directory(staging)
        receipt = writer.write_run_receipt("render-fix", started=started, outputs=[], extra=extra)
        writer.save_input_manifest("render-fix", manifest, after, mismatches, successful=True)

        audit_path.write_text(
            render_audit_document(
                plan,
                instructions_sha256=receipts.sha256_file(instructions),
                instruction_rows=row_count,
                overlay_sha256={item["panel_index"]: item["after"]["sha256"] for item in records},
                panel_receipt_sha256=receipts.sha256_file(panel_receipt)
                if panel_receipt.is_file()
                else None,
                render_fix_receipt=receipts.relative_to_root(receipt, repo_root),
            ),
            encoding="utf-8",
        )
        return {
            "panels": len(records),
            "receipt": receipts.relative_to_root(receipt, repo_root),
            "quota_file_commit": commit,
        }
    except receipts.EngAssetError as exc:
        if exc.reason in receipts.FAILURE_REASONS and isinstance(
            exc, (QuotaFileDirty, receipts.InputHashChanged, receipts.OutputPathForbidden)
        ):
            writer.write_failure_receipt("render-fix", exc.reason, exc.offending, message=str(exc))
        raise
    finally:
        if created_staging is not None and created_staging.exists():
            _clear_directory(created_staging)
            created_staging.rmdir()


def stage_stats(
    *,
    repo_root: Path = PROJECT_ROOT,
    artifact_root: Path | None = None,
    attempt: str = "attempt-2",
    local_root: Path | None = None,
    evidence_dir: Path | None = None,
    unity_log: Path | None = None,
    panel_root: Path | None = None,
) -> dict[str, Any]:
    """阶段 3：只读 Unity 日志条目出统计；格式不合即失败退出（AC-4 修订 3）。

    失败时只新增 `receipts/failure-stats-<utc>.json`（reason
    `VERDICT_FORMAT_MISMATCH`，offending 记问题与行号），**不写成功收据、不覆盖已有
    统计/清单/日志**，也不把错误转换成「不确定」或全零结果。
    """
    repo_root = Path(repo_root)
    artifact_root = Path(artifact_root) if artifact_root else repo_root / "runtime/dist-data"
    local = Path(local_root) if local_root else repo_root / receipts.LOCAL_ROOT
    evidence = Path(evidence_dir) if evidence_dir else repo_root / EVIDENCE_DIR
    log_path = Path(unity_log) if unity_log else repo_root / UNITY_LOG_PATH
    writer = ReceiptWriter(local, repo_root)
    manifest = InputManifest(repo_root=repo_root)
    started = time.monotonic()
    audit_path = evidence / AUDIT_FILENAME
    # C1-2：清单快照先于任何解析/重建，快照即用户实际所看那一版的字节。
    manifest_text = audit_path.read_text(encoding="utf-8")
    manifest_snapshot = {
        "path": receipts.relative_to_root(audit_path, repo_root),
        "bytes": audit_path.stat().st_size,
        "sha256": receipts.sha256_file(audit_path),
    }
    seed, quotas = parse_audit_parameters(manifest_text)
    frozen_panels = parse_audit_panels(manifest_text)
    plan, instructions, row_count = build_plan(
        artifact_root=artifact_root,
        attempt=attempt,
        local_root=local,
        manifest=manifest,
        seed=seed,
        quotas=quotas,
    )
    # C1-2：按冻结清单核对身份，并把面板收据、所采用的重绘收据与 60 张叠加图
    # 一并登记为本阶段输入——「索引数量相等」不能替代身份相等。
    panel_receipt = local / PANEL_RECEIPT_NAME
    if panel_receipt.is_file():
        manifest.record(panel_receipt, source="本项 A2 面板收据（首次读取现算）")
    render_fix = (
        sorted((local / RECEIPTS_SUBDIR).glob("run-render-fix-*.json"))
        if (local / RECEIPTS_SUBDIR).is_dir()
        else []
    )
    render_fix_reference: str | None = None
    if render_fix:
        manifest.record(render_fix[-1], source="本项 A2 重绘收据（首次读取现算）")
        render_fix_reference = receipts.relative_to_root(render_fix[-1], repo_root)

    identity_problems = frozen_identity_mismatches(frozen_panels, plan)
    panel_dir = resolve_panel_dir(repo_root, panel_root)
    for item in frozen_panels:
        overlay = panel_dir / f"panel-{item['panel_index']:03d}.jpg"
        if not overlay.is_file():
            identity_problems.append(
                {"problem": "OVERLAY_MISSING", "panel_index": item["panel_index"],
                 "path": receipts.relative_to_root(overlay, repo_root)}
            )
            continue
        digest = manifest.record(overlay, source="用户所看叠加图（首次读取现算）").sha256
        recorded = item["overlay_sha256"]
        # F2：占位或缺失的身份不得放行——清单是「用户所看那一批」的唯一身份依据。
        if len(recorded) != 64 or any(ch not in "0123456789abcdef" for ch in recorded.lower()):
            identity_problems.append(
                {
                    "problem": "MANIFEST_OVERLAY_SHA_MISSING_OR_PLACEHOLDER",
                    "panel_index": item["panel_index"],
                    "manifest": recorded,
                }
            )
            continue
        if digest != recorded:
            identity_problems.append(
                {
                    "problem": "OVERLAY_SHA_DIFFERS_FROM_MANIFEST",
                    "panel_index": item["panel_index"],
                    "manifest": recorded,
                    "actual": digest,
                }
            )
    if not frozen_panels:
        identity_problems.append({"problem": "MANIFEST_PANEL_TABLE_MISSING"})
    if identity_problems:
        writer.write_failure_receipt(
            "stats", "INPUT_HASH_CHANGED", identity_problems,
            message="统计所依据的面板身份与用户所看清单不一致，未产出统计",
        )
        raise receipts.InputHashChanged(
            "面板身份与冻结清单不一致", offending=identity_problems
        )

    # expected 取**冻结清单**的索引，不取重建计划。
    expected = [item["panel_index"] for item in frozen_panels]
    # F1：Unity 日志与其它不变输入同一登记点/同一 before-after-union，`verdict_source`
    # 取登记条目而不是事后现算——否则解析后被改动的日志仍会以「新字节」写进成功收据。
    log_entry = manifest.record(log_path, source="Unity 代录条目（首次读取现算，只读）")
    try:
        verdicts = read_unity_verdicts(log_path, expected_indices=expected)
    except receipts.VerdictFormatMismatch as exc:
        writer.write_failure_receipt("stats", exc.reason, exc.offending, message=str(exc))
        raise

    stats = statistics(plan, verdicts)
    # overlay SHA 取**已核对过实际字节**的冻结清单值，来源收据同时写入清单。
    overlays = {item["panel_index"]: item["overlay_sha256"] for item in frozen_panels}

    # 写出前做唯一一次输入核验：不变输入逐条相等，且清单自读入以来未被他人改动。
    after = manifest.recompute()
    mismatches = manifest.diff(after)
    current = {
        "path": manifest_snapshot["path"],
        "bytes": audit_path.stat().st_size,
        "sha256": receipts.sha256_file(audit_path),
    }
    if current != manifest_snapshot:
        mismatches = mismatches + [
            {"path": manifest_snapshot["path"], "before": manifest_snapshot, "after": current}
        ]
    if mismatches:
        # 输入变化时只出失败收据：既有统计原样保留，不写成功收据、不改写清单。
        writer.save_input_manifest("audit-stats", manifest, after, mismatches, successful=False)
        writer.write_failure_receipt(
            "stats", "INPUT_HASH_CHANGED", mismatches, message="统计执行期间输入发生变化，未写出统计"
        )
        raise receipts.InputHashChanged("统计执行期间输入发生变化", offending=mismatches)

    writer.save_input_manifest("audit-stats", manifest, after, mismatches, successful=True)
    audit_path.write_text(
        render_audit_document(
            plan,
            instructions_sha256=receipts.sha256_file(instructions),
            instruction_rows=row_count,
            overlay_sha256=overlays,
            panel_receipt_sha256=receipts.sha256_file(panel_receipt)
            if panel_receipt.is_file()
            else None,
            statistics_block=render_statistics_block(stats),
            render_fix_receipt=render_fix_reference,
        ),
        encoding="utf-8",
    )
    writer.write_run_receipt(
        "stats",
        started=started,
        outputs=[receipts.output_record(audit_path)],
        extra={
            "statistics": stats,
            "verdict_source": {
                "path": log_entry.path,
                "bytes": log_entry.bytes,
                "sha256": log_entry.sha256,
                "rows": len(verdicts),
                "note": "取自 InputManifest 的登记条目（实际解析的字节），非写出后现算",
            },
            # 读入的清单快照与写出的清单分开记录：前者是本次统计所依据的面板身份，
            # 后者是本次产出，二者本就不同，不得混为一条 before/after。
            "panel_manifest_read": manifest_snapshot,
            "panel_manifest_written": receipts.output_record(audit_path),
            "overlay_source_receipt": render_fix_reference,
        },
    )
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("plan", "panels", "relocate", "render-fix", "stats"))
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--quotas", default=None, help="形如 20/15/15/10")
    args = parser.parse_args(argv)
    quotas = None
    if args.quotas:
        quotas = dict(zip(STRATA, (int(part) for part in args.quotas.split("/"))))
    if args.command == "plan":
        result = stage_plan(seed=args.seed, quotas=quotas)
        plan = result["plan"]
        print(
            json.dumps(
                {
                    "seed": plan.seed,
                    "quotas": plan.quotas,
                    "denominators": plan.denominators,
                    "denominator_objects": plan.denominator_objects,
                    "taken": plan.taken,
                    "panels": len(plan.selected),
                    "audit_path": receipts.relative_to_root(result["audit_path"]),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "panels":
        result = stage_panels()
        print(
            json.dumps(
                {
                    "panels": len(result["panels"]),
                    "quota_file_commit": result["quota_file_commit"],
                    "bytes": sum(item["overlay_bytes"] for item in result["panels"]),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "relocate":
        print(json.dumps(stage_relocate(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "render-fix":
        print(json.dumps(stage_render_fix(), ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(stage_stats(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
