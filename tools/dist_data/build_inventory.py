#!/usr/bin/env python3
"""S1 源清单 inventory（提案 §2.2，AR1-2）。

枚举附录 A 冻结根清单内的全部 jpg 及其 sidecar/truth 文件，对每个文件断言
**恰匹配一个** pattern（零匹配或多匹配即硬错误），折叠 source-frame lineage
组，记录用途类、join 状态与纳入/排除原因码，产出 create-once 工件
`inventory@attempt-k`。

本阶段**不读**任何 S2+ 工件（§2 禁行边）；scenario 绑定只登记采集族，
由 S2 解析。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Iterable

from tools.dist_data import contract, roots
from tools.dist_data.artifacts import (
    ArtifactStore,
    DistDataError,
    canonical_json_bytes,
    sha256_file,
)

STAGE = 1
SIDECAR_REQUIRED_KEYS: tuple[str, ...] = (
    "camera_position_world_m",
    "camera_right_world",
    "camera_up_world",
    "camera_forward_world",
    "intrinsics_px",
    "vertical_fov_deg",
    "width",
    "height",
)

# JPEG SOF 标记（不含 DHT/DAC/RST/SOI/EOI/SOS 等非帧头标记）。
_SOF_MARKERS = frozenset(
    {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
)


class InventoryError(DistDataError):
    """S1 清单构建失败（一律 fail-closed）。"""


def jpeg_dimensions(path: Path) -> tuple[int, int]:
    """纯标准库读取 JPEG 尺寸（避免为 S1 引入图像库依赖）。"""
    with path.open("rb") as handle:
        if handle.read(2) != b"\xff\xd8":
            raise InventoryError(f"不是 JPEG：{path}")
        while True:
            byte = handle.read(1)
            if not byte:
                raise InventoryError(f"JPEG 头截断（未见 SOF）：{path}")
            if byte != b"\xff":
                continue  # 重新同步到下一个标记
            marker_byte = handle.read(1)
            while marker_byte == b"\xff":  # 跳过填充字节
                marker_byte = handle.read(1)
            if not marker_byte:
                raise InventoryError(f"JPEG 头截断（标记缺失）：{path}")
            marker = marker_byte[0]
            if marker == 0x00 or marker == 0x01 or 0xD0 <= marker <= 0xD8:
                continue  # 填充/重启/SOI：无长度字段
            if marker == 0xD9:
                raise InventoryError(f"JPEG 在 SOF 之前就 EOI：{path}")
            length_bytes = handle.read(2)
            if len(length_bytes) != 2:
                raise InventoryError(f"JPEG 段长度截断：{path}")
            length = int.from_bytes(length_bytes, "big")
            if length < 2:
                raise InventoryError(f"JPEG 段长度非法（{length}）：{path}")
            if marker in _SOF_MARKERS:
                payload = handle.read(5)
                if len(payload) != 5:
                    raise InventoryError(f"JPEG SOF 截断：{path}")
                height = int.from_bytes(payload[1:3], "big")
                width = int.from_bytes(payload[3:5], "big")
                return width, height
            if marker == 0xDA:  # SOS：其后是熵编码数据，不再有尺寸段
                raise InventoryError(f"JPEG 无 SOF 段：{path}")
            handle.seek(length - 2, 1)


def _iter_files(repo_root: Path) -> Iterable[Path]:
    for root in roots.ENUMERATION_ROOTS:
        base = repo_root / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file():
                yield path


def assert_empty_dirs(repo_root: Path) -> None:
    """附录 A.3：`runtime/frames/` 断言为空，非空即错。"""
    for relative in roots.MUST_BE_EMPTY_DIRS:
        directory = repo_root / relative
        if not directory.exists():
            continue
        entries = sorted(child.name for child in directory.iterdir())
        if entries:
            raise InventoryError(
                f"{relative} 应为空目录，实测 {len(entries)} 项：{entries[:5]}"
            )


def _sidecar_join(path: Path) -> dict[str, Any]:
    sidecar = path.with_suffix(".json")
    if not sidecar.exists():
        return {"present": False, "complete": False, "missing_keys": list(SIDECAR_REQUIRED_KEYS)}
    try:
        document = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InventoryError(f"sidecar 不可解析：{sidecar}（{exc}）") from exc
    missing = [key for key in SIDECAR_REQUIRED_KEYS if key not in document]
    return {
        "present": True,
        "complete": not missing,
        "missing_keys": missing,
        "schema_version": document.get("schema_version"),
        "scenario_id": document.get("scenario_id"),
        "frame_id": document.get("frame_id"),
    }


def _lineage_primary_rank(usage_class: str) -> int:
    """lineage 组内 primary 的确定性优先级 = 用途类闭集表序。"""
    try:
        return contract.USAGE_CLASSES.index(usage_class)
    except ValueError as exc:  # pragma: no cover - 闭集外用途类已在上游拦截
        raise InventoryError(f"用途类不在闭集内：{usage_class}") from exc


def reconcile_root_manifest(declared: dict[str, Any] | None) -> dict[str, Any]:
    """BC-SURVEY-7：把当前操作表与**实际读到的** S0 `root_manifest` 对账。

    比的是 canonical **字节**，不是 `==`：JSON 解析回来的文档与现场投影在
    数值类型上可能相等而字节不同，而这份文档的全部意义就是字节冻结。
    `declared is None` 是无声明的诊断路径（`preflight` 与手工 CLI），只报告
    不断言；生产 S1 由 `run_pipeline.stage1_inventory` 强制传入。
    """
    current = roots.root_manifest()
    if declared is None:
        return {"asserted": False, "entry_count": len(current["table"])}
    if not isinstance(declared, dict):
        raise InventoryError(
            f"S0 root_manifest 不是对象：{type(declared).__name__}；"
            "坏输入必须落在域内错误上，不能是裸 AttributeError"
        )
    for member in (
        "enumeration_roots",
        "root_excluded_prefixes",
        "must_be_empty_dirs",
        "table",
    ):
        if canonical_json_bytes(declared.get(member)) != canonical_json_bytes(
            current[member]
        ):
            raise InventoryError(
                f"S0 root_manifest 与当前操作表不等：{member}；附录 A 根清单已改"
                "而 S0 未重新发布——须走 supersession 新建 contract attempt，"
                "不得在旧 S0 下枚举"
            )
    if canonical_json_bytes(declared) != canonical_json_bytes(current):
        raise InventoryError("S0 root_manifest 顶层键集与当前操作表不等")
    return {"asserted": True, "entry_count": len(current["table"])}


def reconcile_survey_acquisition(declared: dict[str, Any] | None) -> dict[str, Any]:
    """BC-SURVEY-14：枚举前对账 S0 的 `survey_acquisition` 与当前投影。"""
    current = contract.survey_acquisition()
    if declared is None:
        return {"asserted": False, "constant_count": len(current["constants"])}
    if not isinstance(declared, dict):
        raise InventoryError(
            f"S0 survey_acquisition 不是对象：{type(declared).__name__}"
        )
    if canonical_json_bytes(declared) != canonical_json_bytes(current):
        declared_names = set((declared.get("constants") or {}))
        current_names = set(current["constants"])
        raise InventoryError(
            "S0 survey_acquisition 与当前采集协议投影不等；"
            f"表有而码无 {sorted(declared_names - current_names)[:5]}、"
            f"码有而表无 {sorted(current_names - declared_names)[:5]}；"
            "受管常量改动后必须重新发布 contract attempt"
        )
    return {"asserted": True, "constant_count": len(current["constants"])}


def _survey_plan_view_ids(
    repo_root: Path, unit: str
) -> tuple[frozenset[str], frozenset[str]]:
    """该巡览会话 manifest 所钉、哈希相符的已复核 plan 的合法视角集合。"""
    session_id = unit.rsplit("/", 1)[-1]
    manifest_path = repo_root / unit / "session" / "manifest.json"
    try:
        plan = contract.load_pinned_survey_plan(
            repo_root, manifest_path, session_id=session_id
        )
        return contract.survey_plan_view_ids(plan)
    except contract.SurveyContractError as exc:
        raise InventoryError(f"巡览会话 {unit} 的 plan 钉死校验失败：{exc}") from exc


def _survey_selection(repo_root: Path, unit: str) -> dict[int, dict[str, Any]]:
    """读一个巡览会话的 `selection.json`，返回 `frame_id → 行`。

    缺文件、schema 不符、类不在闭集、`frame_id` 重复一律硬错误——逐帧用途类
    降级不允许「读不到就当全有效」（P1-VLM-DATA-002 §2.1(e)）。
    """
    path = repo_root / unit / "selection.json"
    if not path.is_file():
        raise InventoryError(
            f"巡览会话缺 selection.json：{path}；逐帧用途类无权威来源，拒绝纳入"
        )
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InventoryError(f"selection.json 不可解析：{path}（{exc}）") from exc
    if document.get("schema_version") != contract.SURVEY_SELECTION_SCHEMA:
        raise InventoryError(
            f"selection.json schema 不符：{path} 实测 "
            f"{document.get('schema_version')!r}，要求 "
            f"{contract.SURVEY_SELECTION_SCHEMA!r}"
        )
    survey_ids, witness_ids = _survey_plan_view_ids(repo_root, unit)
    legal_ids = survey_ids | witness_ids
    rows: dict[int, dict[str, Any]] = {}
    for entry in document.get("entries", []):
        frame_id = entry.get("frame_id")
        if not isinstance(frame_id, int) or isinstance(frame_id, bool):
            raise InventoryError(f"selection 行 frame_id 非整数：{entry!r}（{path}）")
        if entry.get("class") not in contract.SURVEY_FRAME_CLASSES:
            raise InventoryError(
                f"selection 行的类不在闭集 {contract.SURVEY_FRAME_CLASSES}："
                f"{entry.get('class')!r}（{path}）"
            )
        # BC-SURVEY-13：`view_id` 必须**在场**（缺键不等于窗外帧），非 `null`
        # 值须过完整语法与已复核 plan 成员校验。
        if "view_id" not in entry:
            raise InventoryError(f"selection 行缺 view_id 键：{entry!r}（{path}）")
        try:
            contract.validate_selection_view_id(
                entry["view_id"], entry["class"], legal_ids
            )
        except contract.SurveyContractError as exc:
            raise InventoryError(f"selection 行 view_id 非法：{exc}（{path}）") from exc
        if frame_id in rows:
            raise InventoryError(f"selection 行 frame_id 重复：{frame_id}（{path}）")
        rows[frame_id] = entry
    return rows


def _survey_frame_id(relative: str) -> int:
    stem = Path(relative).stem
    digits = stem.rsplit("_", 1)[-1]
    if not digits.isdigit():
        raise InventoryError(f"巡览归档帧名不合式（应为 frame_<digits>.jpg）：{relative}")
    return int(digits)


def build_inventory(
    repo_root: Path,
    *,
    survey_sessions: list[dict[str, Any]] | None = None,
    root_manifest: dict[str, Any] | None = None,
    survey_acquisition: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构建 S1 清单载荷（纯函数，除读盘外无副作用）。

    `survey_sessions` 传入 S0 合同的会话表时，S1 断言**实际枚举的会话集合与
    该表逐项相等**（多、少、哈希不符均硬错误，P1-VLM-DATA-002 §2.2 第 4
    条）。传 `None` = 无声明的诊断路径（`preflight`），只报告不断言。
    """
    repo_root = Path(repo_root)
    # BC-SURVEY-7：**枚举前**对账。必须早于 `assert_empty_dirs`——
    # `MUST_BE_EMPTY_DIRS` 本身就是被投影的四个成员之一，不能在未对账的表
    # 下先被消费。
    root_manifest_audit = reconcile_root_manifest(root_manifest)
    # BC-SURVEY-14：S1 在枚举前同样对账采集协议投影。
    acquisition_audit = reconcile_survey_acquisition(survey_acquisition)
    assert_empty_dirs(repo_root)
    selection_cache: dict[str, dict[int, dict[str, Any]]] = {}

    records: list[dict[str, Any]] = []
    unmatched: list[str] = []
    multimatched: list[dict[str, Any]] = []

    for path in _iter_files(repo_root):
        relative = path.relative_to(repo_root).as_posix()
        if roots.is_root_excluded(relative):
            continue
        suffix = path.suffix.lower()
        if suffix == ".jpg":
            kind = roots.KIND_IMAGE
        else:
            matches = [
                entry
                for entry in roots.matching_entries(relative)
                if entry.kind == roots.KIND_TRUTH
            ]
            if not matches:
                continue  # 非图像、非真值 pattern 的文件不入图像清单（§附录 A）
            kind = roots.KIND_TRUTH

        matches = [entry for entry in roots.matching_entries(relative) if entry.kind == kind]
        if not matches:
            unmatched.append(relative)
            continue
        if len(matches) > 1:
            multimatched.append(
                {"path": relative, "patterns": [entry.pattern for entry in matches]}
            )
            continue

        entry = matches[0]
        digest = sha256_file(path)
        # AR2-3：`<unit>` 占位在此解析为 source unit 末段（巡览会话 id）；
        # 占位字符串绝不进入 inventory 记录。
        family = roots.resolve_family(entry, relative)
        usage_class = entry.usage_class
        selection_row: dict[str, Any] | None = None
        if usage_class == "VALID_SURVEY":
            unit = roots.source_unit_for(relative)
            if unit not in selection_cache:
                selection_cache[unit] = _survey_selection(repo_root, unit)
            frame_id = _survey_frame_id(relative)
            selection_row = selection_cache[unit].get(frame_id)
            if selection_row is None:
                raise InventoryError(
                    f"归档帧不在 selection.json 内：{relative}；§2.1(e) 要求归档中"
                    "每个 frame_id 恰一行"
                )
            # 只降不升：pattern 给的是 `VALID_SURVEY`，selection 只能把它降为
            # `PROTOCOL_INVALID`，反向（把 PROTOCOL_INVALID 抬成 VALID）不可能
            # 发生，因为闭集只有这两个值且此处只在为后者时改写。
            if selection_row["class"] == "PROTOCOL_INVALID":
                usage_class = "PROTOCOL_INVALID"
        record: dict[str, Any] = {
            "path": relative,
            "kind": kind,
            "bytes": path.stat().st_size,
            "sha256": digest,
            "pattern": entry.pattern,
            "usage_class": usage_class,
            "family": family,
            "layout_class": entry.layout_class,
            "scenario_binding_family": family,
            "decision": roots.USAGE_DECISION[usage_class],
            "eligibility": dict(roots.USAGE_ELIGIBILITY[usage_class]),
        }
        if selection_row is not None:
            record["survey_selection"] = {
                "view_id": selection_row["view_id"],
                "class": selection_row["class"],
                "reason": selection_row.get("reason"),
            }
        if kind == roots.KIND_IMAGE:
            width, height = jpeg_dimensions(path)
            record["width"] = width
            record["height"] = height
            sidecar = _sidecar_join(path)
            record["sidecar_join"] = sidecar
            truth = roots.truth_source_for(relative)
            record["truth_join"] = {
                "source": truth[0] if truth else None,
                "schema_family": truth[1] if truth else None,
                "present": bool(truth and (repo_root / truth[0]).exists()),
            }
            if record["decision"] == "INCLUDED" and not sidecar["complete"]:
                record["decision"] = "EXCLUDED_NO_POSE"
        records.append(record)

    if unmatched or multimatched:
        raise InventoryError(
            "附录 A 冻结根清单是闭集，S1 要求每个被枚举文件恰匹配一个 pattern。\n"
            f"  零匹配 {len(unmatched)} 个（前 5）：{unmatched[:5]}\n"
            f"  多匹配 {len(multimatched)} 个（前 5）：{multimatched[:5]}\n"
            "  处置：不得静默纳入或跳过；退回接受角色修订附录 A。"
        )

    records.sort(key=lambda record: record["path"])

    # §2.1(e)：归档 jpg 集合与 selection 清单逐 id 一一对应（多、少均硬错误；
    # 「多」已在上面逐帧拦截，此处补「少」的一侧）。
    archived_by_unit: dict[str, set[int]] = {}
    for record in records:
        if record["kind"] != roots.KIND_IMAGE:
            continue
        if "survey_selection" not in record:
            continue
        unit = roots.source_unit_for(record["path"])
        archived_by_unit.setdefault(unit, set()).add(_survey_frame_id(record["path"]))
    for unit, rows in sorted(selection_cache.items()):
        declared = set(rows)
        archived = archived_by_unit.get(unit, set())
        if declared != archived:
            raise InventoryError(
                f"selection 与归档 jpg 集合不一致：{unit}\n"
                f"  清单有而归档无 {sorted(declared - archived)[:5]}\n"
                f"  归档有而清单无 {sorted(archived - declared)[:5]}"
            )

    # §2.2 第 4 条：S0 `survey_sessions` 与实际枚举的会话集合逐项相等。
    enumerated = contract.build_survey_sessions(repo_root)
    survey_audit: dict[str, Any] = {
        "enumerated_session_count": len(enumerated),
        "declared_session_count": None if survey_sessions is None else len(survey_sessions),
        "asserted": survey_sessions is not None,
    }
    if survey_sessions is not None:
        # 先查重：以 `session_id` 为键 dict 化会让重复行被静默覆盖，那样就无法
        # 保证 §2.2 第 4 条要求的「与实际枚举逐项精确相等」（多、少均硬错误）。
        declared_ids = [row.get("session_id") for row in survey_sessions]
        duplicates = sorted(
            {name for name in declared_ids if declared_ids.count(name) > 1}
        )
        if duplicates:
            raise InventoryError(
                f"S0 survey_sessions 有重复会话行：{duplicates}；"
                "逐项相等要求表内每个会话恰一行"
            )
        # 枚举侧按 `session_id` 升序，声明侧同序比对——逐项、按位置。
        declared_sorted = sorted(survey_sessions, key=lambda row: row.get("session_id"))
        if len(declared_sorted) != len(enumerated):
            raise InventoryError(
                f"S0 survey_sessions 行数 {len(declared_sorted)} 与实际枚举 "
                f"{len(enumerated)} 不等"
            )
        for declared, actual in zip(declared_sorted, enumerated):
            if declared.get("session_id") != actual["session_id"]:
                raise InventoryError(
                    "S0 survey_sessions 与实际枚举的巡览会话集合不等："
                    f"表 {declared.get('session_id')!r} vs 盘 {actual['session_id']!r}"
                )
            mismatched = [
                key
                for key in contract.SURVEY_SESSION_ROW_KEYS
                if declared.get(key) != actual.get(key)
            ]
            if mismatched:
                raise InventoryError(
                    f"S0 survey_sessions 行与归档不符：{actual['session_id']}；"
                    f"不符字段 {mismatched}"
                )
            extra_keys = sorted(set(declared) - set(contract.SURVEY_SESSION_ROW_KEYS))
            if extra_keys:
                raise InventoryError(
                    f"S0 survey_sessions 行含闭集外字段：{actual['session_id']} "
                    f"{extra_keys}"
                )

    lineage = _fold_lineage(records)
    return {
        "stage": STAGE,
        "root_manifest_audit": root_manifest_audit,
        "survey_acquisition_audit": acquisition_audit,
        "survey_session_audit": survey_audit,
        # BC-DATA-6：只读 dry-run 须**报告** zero-match / multi-match，而不是
        # 只在违规时抛错。走到这里二者必为 0（否则上面已 fail-closed）。
        "match_audit": {
            "zero_match": len(unmatched),
            "multi_match": len(multimatched),
        },
        "record_count": len(records),
        "image_count": sum(1 for record in records if record["kind"] == roots.KIND_IMAGE),
        "truth_count": sum(1 for record in records if record["kind"] == roots.KIND_TRUTH),
        "records": records,
        "lineage_groups": lineage,
        "decision_histogram": _histogram(records, "decision"),
        "usage_class_histogram": _histogram(records, "usage_class"),
        "family_histogram": _histogram(records, "family"),
    }


def _histogram(records: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        key = str(record.get(field))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _fold_lineage(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """source-frame lineage 组：内容哈希相等的正式/hold/exchange/文档副本折叠为一组。

    primary = 用途类表序最靠前者，同序按路径升序；其余为 duplicates。
    """
    buckets: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record["kind"] != roots.KIND_IMAGE:
            continue
        buckets.setdefault(record["sha256"], []).append(record)
    groups: list[dict[str, Any]] = []
    for digest in sorted(buckets):
        members = sorted(
            buckets[digest],
            key=lambda record: (_lineage_primary_rank(record["usage_class"]), record["path"]),
        )
        primary = members[0]["path"]
        groups.append(
            {
                "lineage_id": digest,
                "primary": primary,
                "duplicates": [record["path"] for record in members[1:]],
                "member_count": len(members),
            }
        )
        for index, record in enumerate(members):
            record["lineage_id"] = digest
            record["lineage_role"] = "primary" if index == 0 else "duplicate"
    return groups


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S1 源清单 inventory（P1-VLM-DATA-001）")
    parser.add_argument("--repo-root", default=".", help="仓库根（默认当前目录）")
    parser.add_argument("--attempt", default="attempt-1", help="create-once attempt id")
    parser.add_argument("--supersedes", default=None, help="被 supersede 的 attempt id")
    parser.add_argument("--supersession-reason", default=None, help="supersession 归因")
    parser.add_argument(
        "--dry-run", action="store_true", help="只打印统计，不写 create-once 工件"
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if not args.dry_run:
        # BC-SURVEY-7/14：未对账就不得发布 create-once 工件。本模块 CLI 手里没有
        # S0 载荷，所以它只允许 `--dry-run` 诊断；生产 S1 走
        # `run_pipeline.stage1_inventory`，它读 contract@attempt 并逐项对账。
        print(
            "错误：本 CLI 不再直接发布 inventory 工件——它无法对账 S0 的 "
            "root_manifest / survey_acquisition。请用 `--dry-run` 做诊断，或走 "
            "`python3 -m tools.dist_data.run_pipeline --run inventory`。",
            file=sys.stderr,
        )
        return 2
    payload = build_inventory(repo_root)
    print(
        f"S1 inventory：记录 {payload['record_count']}（图像 {payload['image_count']}、"
        f"真值 {payload['truth_count']}），lineage 组 {len(payload['lineage_groups'])}"
    )
    audit = payload["match_audit"]
    print(
        f"  恰一匹配审计：zero-match = {audit['zero_match']}，"
        f"multi-match = {audit['multi_match']}"
    )
    for key, value in payload["decision_histogram"].items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
