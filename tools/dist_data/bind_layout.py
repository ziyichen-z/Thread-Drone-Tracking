#!/usr/bin/env python3
"""S2 布局绑定与历史交叉验证（提案 §2.3，AR1-2 / AR2-3 / BC-DATA-3）。

逐采集族解析归档场景字节（fail-closed 三级优先），由 S0 钉死的基础几何
逆施 default relocations、再正施该布局类的 relocations，产出逐布局类的
实例 AABB 表与 relocation/removal/phantom 标记；随后用 §2.4 投影器对归档
真值框做历史布局交叉验证。

BC-DATA-3：交叉验证**只用**能以归档 distractor id 恰一映射到静态目录对象
的真值框；动态 target 的二维框只作 blocker，其 `target_world_*_m` 只参加
中心落框率检查，不构造 AABB、不进静态 IoU 中位数。
"""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Any, Iterable, Sequence

from tools.dist_data import contract, project_boxes, roots
from tools.dist_data.artifacts import (
    ArtifactStore,
    DistDataError,
    sha256_file,
)

STAGE = 2

BINDING_BOUND = "BOUND"
BINDING_UNBOUND = "EXCLUDED_UNBOUND_SCENARIO"
BINDING_INVALID = "INVALID"

# §2.3 第 1 步：run/归档目录内嵌快照的文件名，按优先级求值。
EMBEDDED_SNAPSHOT_NAMES: tuple[str, ...] = ("scenario.json", "scenario_config.json")
MANIFEST_NAME = "manifest.json"

# BC-DATA-12（接受轮 6）：内嵌快照候选必须属于归档提供者闭集。
# 该精确路径是运行时的**可变**覆盖文件，**永久禁止**充当内嵌快照——
# 即使将来 `SCENARIO_BYTE_PROVIDERS` 放宽也不得命中。
FORBIDDEN_SNAPSHOT_PATHS: frozenset[str] = frozenset({"runtime/scenario_config.json"})
# `config/*.json` 只能在 manifest 声明 SHA 与字节完全相等时作 provider，
# **永不**因祖先关系成为内嵌快照（§2.3：当前 config 不得充当历史布局来源）。
SNAPSHOT_EXCLUDED_PREFIXES: tuple[str, ...] = ("config/",)


def is_allowed_embedded_snapshot(relative_path: str) -> bool:
    """候选是否可充当 `embedded_snapshot`（BC-DATA-12 的闭集判据）。"""
    if relative_path in FORBIDDEN_SNAPSHOT_PATHS:
        return False
    if relative_path.startswith(SNAPSHOT_EXCLUDED_PREFIXES):
        return False
    return any(
        roots._compiled(pattern).match(relative_path)
        for pattern in roots.SCENARIO_BYTE_PROVIDERS
    )


class LayoutError(DistDataError):
    """S2 布局绑定失败（一律 fail-closed）。"""


# --- 基础几何 -------------------------------------------------------------
def load_base_geometry(repo_root: Path) -> dict[str, Any]:
    """读取 S0 哈希钉死的基础几何，并断言身份与规模。"""
    path = Path(repo_root) / contract.BASE_GEOMETRY_PATH
    if not path.exists():
        raise LayoutError(f"基础几何缺失：{path}")
    digest = sha256_file(path)
    if digest != contract.BASE_GEOMETRY_SHA256:
        raise LayoutError(
            f"基础几何字节改变：实测 {digest}，S0 钉死 {contract.BASE_GEOMETRY_SHA256}"
        )
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_version") != contract.BASE_GEOMETRY_SCHEMA:
        raise LayoutError(f"基础几何 schema 不符：{document.get('schema_version')}")
    if len(document.get("instances", [])) != contract.BASE_GEOMETRY_INSTANCE_COUNT:
        raise LayoutError(
            f"基础几何实例数不符：{len(document.get('instances', []))} != "
            f"{contract.BASE_GEOMETRY_INSTANCE_COUNT}"
        )
    if not document.get("scene_adjustments_applied"):
        raise LayoutError("基础几何不是 default 布局的已调整后几何（§2.3 前提不成立）")
    return document


def xz_center(instance: dict[str, Any]) -> tuple[float, float]:
    return (
        (instance["min_x_m"] + instance["max_x_m"]) / 2.0,
        (instance["min_z_m"] + instance["max_z_m"]) / 2.0,
    )


def xz_half_diagonal(instance: dict[str, Any]) -> float:
    half_x = (instance["max_x_m"] - instance["min_x_m"]) / 2.0
    half_z = (instance["max_z_m"] - instance["min_z_m"]) / 2.0
    return (half_x * half_x + half_z * half_z) ** 0.5


def match_tolerance(entry: dict[str, Any], prefab_instances: Sequence[dict[str, Any]]) -> float:
    """`T_match(entry) = match_tolerance_m + 该 prefab 类实例 XZ 半对角线最大值`。"""
    base = float(entry.get("match_tolerance_m", 0.0))
    if not prefab_instances:
        return base
    return base + max(xz_half_diagonal(instance) for instance in prefab_instances)


def _prefab_instances(
    instances: Iterable[dict[str, Any]], prefab_name: str
) -> list[dict[str, Any]]:
    return [
        instance
        for instance in instances
        if contract.prefab_base_name(instance["scene_object_name"]) == prefab_name
    ]


def _unique_match(
    instances: Sequence[dict[str, Any]],
    entry: dict[str, Any],
    point: tuple[float, float],
    *,
    where: str,
    tolerance_override: float | None = None,
) -> dict[str, Any] | None:
    """§2.3 匹配合同：恰一个候选落入 T_match；零个返回 None，多个硬错误。"""
    prefab = entry["prefab_name"]
    candidates = _prefab_instances(instances, prefab)
    tolerance = (
        match_tolerance(entry, candidates)
        if tolerance_override is None
        else tolerance_override
    )
    hits = [
        instance
        for instance in candidates
        if ((xz_center(instance)[0] - point[0]) ** 2 + (xz_center(instance)[1] - point[1]) ** 2)
        ** 0.5
        <= tolerance
    ]
    if len(hits) > 1:
        raise LayoutError(
            f"{where}：relocation 匹配到 {len(hits)} 个候选（要求恰一个）"
            f" prefab={prefab} point={point} T_match={tolerance}"
        )
    return hits[0] if hits else None


def _translate(instance: dict[str, Any], dx: float, dz: float) -> dict[str, Any]:
    """整体平移 AABB（pivot 无关，y 范围不变）。"""
    moved = dict(instance)
    moved["min_x_m"] = instance["min_x_m"] + dx
    moved["max_x_m"] = instance["max_x_m"] + dx
    moved["min_z_m"] = instance["min_z_m"] + dz
    moved["max_z_m"] = instance["max_z_m"] + dz
    return moved


def unadjusted_base(
    base_instances: Sequence[dict[str, Any]], default_relocations: Sequence[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """逆施 default relocations，得到未调整基础几何与 phantom 候选清单。"""
    instances = [dict(instance) for instance in base_instances]
    phantoms: list[dict[str, Any]] = []
    for entry in default_relocations:
        if entry.get("remove_from_scene"):
            original = (
                float(entry["original_xz_m"]["x"]),
                float(entry["original_xz_m"]["z"]),
            )
            # BC-DATA-18：判断「原实例仍存在」时**只**允许 AABB 中心距
            # `original_xz_m` ≤ `match_tolerance_m` 的同 prefab 实例——再加类内
            # 半对角线会让邻居冒充被移除实例，静默吞掉 phantom 登记（fail-open）。
            present = _unique_match(
                instances,
                entry,
                original,
                where="逆施 default removal",
                tolerance_override=float(entry.get("match_tolerance_m", 0.0)),
            )
            if present is None:
                # §2.3 (a)：default 移除且实例不在基础几何中 → phantom 候选。
                # 候选随身携带**本条目**的 `match_tolerance_m`：同一实例在两份
                # 归档 config 中的 `original_xz_m` 是同一存档量，正施侧判断
                # 「本布局类是否移除了它自己」时只能用这个容差（复核轮 2 F13）。
                phantoms.append(
                    {
                        "prefab_name": entry["prefab_name"],
                        "original_xz_m": {"x": original[0], "z": original[1]},
                        "match_tolerance_m": float(entry.get("match_tolerance_m", 0.0)),
                    }
                )
            continue
        new_position = (
            float(entry["new_position_m"]["x"]),
            float(entry["new_position_m"]["z"]),
        )
        original = (float(entry["original_xz_m"]["x"]), float(entry["original_xz_m"]["z"]))
        moved = _unique_match(instances, entry, new_position, where="逆施 default relocation")
        if moved is None:
            raise LayoutError(
                f"逆施 default relocation 失败：prefab={entry['prefab_name']} "
                f"在新位置 {new_position} 找不到候选（基础几何应已调整）"
            )
        index = instances.index(moved)
        instances[index] = _translate(
            moved, original[0] - new_position[0], original[1] - new_position[1]
        )
    return instances, phantoms


def apply_layout(
    unadjusted: Sequence[dict[str, Any]],
    relocations: Sequence[dict[str, Any]],
    phantom_candidates: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """正施某布局类的 relocations/removals，并登记 phantom 代理体积。"""
    instances = [dict(instance) for instance in unadjusted]
    marks: dict[str, dict[str, Any]] = {}
    removed: list[str] = []
    self_removed_candidates: list[dict[str, Any]] = []
    for entry in relocations:
        original = (float(entry["original_xz_m"]["x"]), float(entry["original_xz_m"]["z"]))
        target = _unique_match(instances, entry, original, where="正施 relocation")
        if entry.get("remove_from_scene"):
            # §2.3 (b)：该布局类自身移除一个存在的实例 → 该实例在该布局类不存在
            # （从目录与遮挡体中一并移除，不是代理）。实例本就不在未调整几何中
            # 时同样按「不存在」处理，并取消它在本布局类的 phantom 登记。
            if target is not None:
                removed.append(target["scene_object_name"])
                instances.pop(instances.index(target))
            self_removed_candidates.append(
                {
                    "prefab_name": entry["prefab_name"],
                    "original_xz_m": {"x": original[0], "z": original[1]},
                }
            )
            continue
        if target is None:
            raise LayoutError(
                f"正施 relocation 失败：prefab={entry['prefab_name']} "
                f"在原位置 {original} 找不到候选"
            )
        new_position = (
            float(entry["new_position_m"]["x"]),
            float(entry["new_position_m"]["z"]),
        )
        instances[instances.index(target)] = _translate(
            target, new_position[0] - original[0], new_position[1] - original[1]
        )
        marks[target["scene_object_name"]] = {"relocated": True}

    # §2.3 (a)：default 移除且实例不在基础几何中的候选，在**其他布局类**里
    # 登记为 phantom；被本布局类自身字节移除的候选不登记。
    def _self_removed(candidate: dict[str, Any]) -> bool:
        # BC-DATA-18 在逆施侧禁掉的「加类内半对角线」在这里同样禁止（复核轮 2
        # F13）：容差**只**取候选自带的条目值。再加半对角线会让距离在半对角线
        # 内的**另一个**实例冒充被移除实例，静默吞掉 §2.3 (a) 必登记的
        # phantom，方向 fail-open，与 F5(a) 完全同构。缺该字段时按 0.0（恰等）
        # 处理，是最严的那一侧。
        for removal in self_removed_candidates:
            if removal["prefab_name"] != candidate["prefab_name"]:
                continue
            dx = removal["original_xz_m"]["x"] - candidate["original_xz_m"]["x"]
            dz = removal["original_xz_m"]["z"] - candidate["original_xz_m"]["z"]
            tolerance = float(candidate.get("match_tolerance_m", 0.0))
            if (dx * dx + dz * dz) ** 0.5 <= tolerance:
                return True
        return False

    phantoms: list[dict[str, Any]] = []
    for candidate in phantom_candidates:
        if _self_removed(candidate):
            continue
        class_word = contract.class_for_scene_object(candidate["prefab_name"])
        # BC-DATA-10（接受轮 6）：类别未知时立刻硬失败——**在代理构造前、在
        # S2 create-once 工件写盘前**。绝不执行 `None == None` 的所谓同类筛选
        # （那会把 building/prop/未映射实例当同类而借来其包络），也不生成该
        # phantom，更不新增静默跳过或 UNKNOWN 通配代理。
        if class_word is None:
            raise LayoutError(
                f"phantom 代理无法构造：prefab={candidate['prefab_name']!r} 不在 §2.6"
                " 的九类冻结映射内，同类包络不可证"
                "（BC-DATA-10：不得借用 building/prop 或未映射实例的包络）"
            )
        same_class = [
            instance
            for instance in instances
            if contract.class_for_scene_object(instance["scene_object_name"]) == class_word
        ]
        # BC-DATA-11（接受轮 6）：代理尺寸只允许来自该冻结类别在目标布局中
        # **仍存在**实例的逐轴最大半长；集合为空时无法证明包络，硬失败。
        # 「三个半长置 0」不是 fail-closed——零面积体会继续参与遮挡、唯一性
        # 与 F 计算，方向 fail-open，故删除该分支。
        if not same_class:
            raise LayoutError(
                f"phantom 代理无法构造：prefab={candidate['prefab_name']} 的冻结类别"
                f" {class_word!r} 在本布局类中没有存活实例，包络不可证"
                "（BC-DATA-11：不得以零体积代理继续遮挡/唯一性/F 计算）"
            )
        half_x = max(
            (instance["max_x_m"] - instance["min_x_m"]) / 2.0 for instance in same_class
        )
        half_y = max(
            (instance["max_y_m"] - instance["min_y_m"]) / 2.0 for instance in same_class
        )
        half_z = max(
            (instance["max_z_m"] - instance["min_z_m"]) / 2.0 for instance in same_class
        )
        centre_x = candidate["original_xz_m"]["x"]
        centre_z = candidate["original_xz_m"]["z"]
        phantoms.append(
            {
                "scene_object_name": f"phantom:{candidate['prefab_name']}@"
                f"{centre_x:.6f},{centre_z:.6f}",
                "group": "vehicle",
                "phantom": True,
                "class_word": class_word,
                "min_x_m": centre_x - half_x,
                "max_x_m": centre_x + half_x,
                "min_y_m": 0.0,
                "max_y_m": 2.0 * half_y,
                "min_z_m": centre_z - half_z,
                "max_z_m": centre_z + half_z,
            }
        )

    instances.sort(key=lambda instance: instance["scene_object_name"])
    phantoms.sort(key=lambda instance: instance["scene_object_name"])
    return {
        "instances": instances,
        "phantoms": phantoms,
        "relocation_marks": marks,
        "removed": sorted(removed),
    }


# --- 场景字节解析 ---------------------------------------------------------
def build_provider_index(repo_root: Path) -> dict[str, list[str]]:
    """归档字节提供者索引：sha256 → 路径列表（当前 config 只在 sha 相等时入选）。"""
    repo_root = Path(repo_root)
    index: dict[str, list[str]] = {}
    for pattern in roots.SCENARIO_BYTE_PROVIDERS:
        for path in sorted(repo_root.glob(pattern)):
            if not path.is_file():
                continue
            index.setdefault(sha256_file(path), []).append(
                path.relative_to(repo_root).as_posix()
            )
    return index


def _snapshot_in(repo_root: Path, directory: Path) -> dict[str, Any] | None:
    """目录内的**合格**内嵌快照（BC-DATA-12 闭集判据）。"""
    for name in EMBEDDED_SNAPSHOT_NAMES:
        candidate = directory / name
        if not candidate.is_file():
            continue
        relative = candidate.relative_to(repo_root).as_posix()
        if not is_allowed_embedded_snapshot(relative):
            continue  # 不绑定、不遮蔽
        return {
            "status": BINDING_BOUND,
            "source": "embedded_snapshot",
            "path": relative,
            "sha256": sha256_file(candidate),
        }
    return None


def _ancestors(repo_root: Path, start_directory: Path):
    stop = repo_root.resolve()
    directory = start_directory
    while True:
        yield directory
        if directory.resolve() == stop or directory.parent == directory:
            return
        directory = directory.parent


def _unit_ancestors(repo_root: Path, start_directory: Path, unit: str):
    """由近及远遍历，**上界是 source unit 自身**（不得越出到仓库根）。"""
    boundary = (repo_root / unit).resolve()
    directory = start_directory
    while True:
        yield directory
        if directory.resolve() == boundary or directory.parent == directory:
            return
        directory = directory.parent


def _unit_subtree_snapshot(repo_root: Path, unit: str) -> dict[str, Any] | None:
    """source unit 子树内的合格内嵌快照；字节不唯一则不绑定（fail-closed）。"""
    base = repo_root / unit
    if not base.is_dir():
        return None
    found: dict[str, str] = {}
    for name in EMBEDDED_SNAPSHOT_NAMES:
        for candidate in sorted(base.rglob(name)):
            relative = candidate.relative_to(repo_root).as_posix()
            if is_allowed_embedded_snapshot(relative):
                found[relative] = sha256_file(candidate)
    if not found:
        return None
    if len(set(found.values())) != 1:
        return None
    path = sorted(found)[0]
    return {
        "status": BINDING_BOUND,
        "source": "unit_subtree_snapshot",
        "path": path,
        "sha256": found[path],
    }


def _archived_scenario_id(repo_root: Path, frame_relative_path: str, unit: str) -> str | None:
    """归档声明的 `scenario_id`：优先 source unit 的 manifest，其次帧 sidecar。"""
    manifest = repo_root / unit / MANIFEST_NAME
    if manifest.is_file():
        try:
            document = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            document = {}
        value = document.get("scenario_id")
        if isinstance(value, str):
            return value
    sidecar = (repo_root / frame_relative_path).with_suffix(".json")
    if sidecar.is_file():
        try:
            document = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        value = document.get("scenario_id")
        if isinstance(value, str):
            return value
    return None


def resolve_frame_scenario(
    repo_root: Path, frame_relative_path: str, provider_index: dict[str, list[str]]
) -> dict[str, Any]:
    """§2.3 fail-closed 解析，绑定域 = **source unit**（BC-DATA-13）。

    1. source unit 内（及其合格祖先）最近的内嵌快照——合格 = 完整匹配
       `roots.SCENARIO_BYTE_PROVIDERS` 且确为祖先（BC-DATA-12）；
    2. 最近的 `manifest.json` 的 `scenario_config_sha256` → 归档字节提供者。
       单 manifest 内**零个** SHA 视为无声明；**多个互异** SHA 是歧义硬失败，
       不得跳过并继续父级搜索；
    3. 闭集关联：(a) m3 归档/hold → 附录 A root 模板点名的 run 目录；
       (b) 附录 A.2 三族 → 表头点名的 hold provider，前提是归档 `scenario_id`
       恰为 `p1-scene-004`；(c) 其余只读自身归档树，不借同 family 邻居；
    4. 皆无 → `EXCLUDED_UNBOUND_SCENARIO`。
    """
    repo_root = Path(repo_root)
    unit = roots.source_unit_for(frame_relative_path)
    frame_directory = (repo_root / frame_relative_path).parent

    # **单趟**由近及远遍历：同一目录内先快照后 manifest。分两趟（先扫完全部
    # 祖先的快照再回头读 manifest）会让**更远**祖先的合法快照抢在**更近**的
    # 歧义 manifest 之前定案，BC-DATA-13 (v) 的硬失败就永不触发。
    # 搜索上界是 source unit 自身（BC-DATA-13 (c)：只读自身归档树）。
    for directory in _unit_ancestors(repo_root, frame_directory, unit):
        found = _snapshot_in(repo_root, directory)
        if found is not None:
            return {**found, "source_unit": unit}
        manifest = directory / MANIFEST_NAME
        if not manifest.is_file():
            continue
        declared = _manifest_scenario_sha(manifest)  # 多个互异 SHA 在此硬失败
        if declared is None:
            continue  # 零个 SHA = 无声明，继续向上
        providers = provider_index.get(declared)
        if providers:
            return {
                "status": BINDING_BOUND,
                "source": "manifest_sha_match",
                "path": sorted(providers)[0],
                "sha256": declared,
                "source_unit": unit,
            }
        return {
            "status": BINDING_UNBOUND,
            "source": "manifest_sha_unmatched",
            "path": manifest.relative_to(repo_root).as_posix(),
            "sha256": declared,
            "source_unit": unit,
        }

    # BC-DATA-13 (c)：「只读**自身归档树**」——祖先之外，本 unit 子树内的
    # 快照同样属于自身归档树（rerun-stopped-scene-defect 等归档把快照放在
    # 子目录里）。要求子树内的合格快照字节唯一，否则不绑定。
    subtree = _unit_subtree_snapshot(repo_root, unit)
    if subtree is not None:
        return {**subtree, "source_unit": unit}

    # --- 3. 闭集关联 ------------------------------------------------------
    run_directory = roots.associated_run_directory(unit)
    if run_directory is not None:
        run_path = repo_root / run_directory
        found = _snapshot_in(repo_root, run_path)
        if found is not None:
            return {**found, "source": "associated_run_snapshot", "source_unit": unit}
        manifest = run_path / MANIFEST_NAME
        if manifest.is_file():
            declared = _manifest_scenario_sha(manifest)
            providers = provider_index.get(declared) if declared else None
            if providers:
                return {
                    "status": BINDING_BOUND,
                    "source": "associated_run_manifest",
                    "path": providers[0],
                    "sha256": declared,
                    "source_unit": unit,
                }

    family = _family_of_unit(unit)
    if family in roots.SCENE004_FAMILIES:
        provider = repo_root / roots.SCENE004_ARCHIVE_PROVIDER
        scenario_id = _archived_scenario_id(repo_root, frame_relative_path, unit)
        if provider.is_file() and scenario_id == roots.SCENE004_REQUIRED_SCENARIO_ID:
            provider_sha = sha256_file(provider)
            # BC-DATA-13 (b) 后半句「任何**已有** manifest/快照必须与该 provider
            # 字节一致」的检查域由 BC-DATA-20 定为该 source unit 的**整个归档
            # 子树**，不是 unit 根层：真实旁支 manifest（scout-3 的
            # `session/manifest.json`）正在自身子树内，只查根层等于放行潜伏矛盾。
            # 任一显式证人不一致或不可读 → 只使**本 unit** unbound，且不得再由
            # sidecar、点名 provider、父级或邻居回退（§22.2 (4)）。
            conflict = a2_subtree_consistency(repo_root, unit, provider_sha)
            if conflict is not None:
                return {
                    "status": BINDING_UNBOUND,
                    "source": conflict["reason"],
                    "path": conflict["path"],
                    "sha256": conflict["declared_sha256"],
                    "witnesses": conflict["witnesses"],
                    "source_unit": unit,
                }
            return {
                "status": BINDING_BOUND,
                "source": "appendix_a2_archive_provider",
                "path": roots.SCENE004_ARCHIVE_PROVIDER,
                "sha256": provider_sha,
                "source_unit": unit,
            }

    return {
        "status": BINDING_UNBOUND,
        "source": "no_scenario_binding",
        "path": None,
        "sha256": None,
        "source_unit": unit,
    }


def _family_of_unit(unit: str) -> str | None:
    """source unit → 附录 A 的 family 标签（只作报告/关联查表）。"""
    for entry in roots.ROOT_TABLE:
        if entry.kind != roots.KIND_IMAGE or entry.family is None:
            continue
        for probe in (
            f"{unit}/frames/frame_0000000000.jpg",
            f"{unit}/frame_0000000000.jpg",
        ):
            if entry.regex.match(probe):
                # AR2-3：巡览条目的 family 是 `<unit>` 占位，逐会话解析为
                # source unit 末段；占位字符串绝不作为 family 返回。
                return roots.resolve_family(entry, probe)
    return None


def _manifest_declarations(path: Path) -> list[str] | None:
    """manifest 内互异的 `scenario_config_sha256` 声明（升序）。

    返回 `None` 专表**不可读/不可解析**，空列表表示零个声明（= 无声明，
    BC-DATA-13 (v)）；两者在 BC-DATA-20 的一致性检查里后果不同，故必须
    分开。多个互异 SHA 仍是既有的歧义硬失败。
    """
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "scenario_config_sha256" and isinstance(value, str):
                    found.append(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(document)
    unique = sorted(set(found))
    if len(unique) > 1:
        # BC-DATA-13：多个互异 SHA 是歧义**硬失败**，不得跳过并继续父级搜索。
        raise LayoutError(
            f"manifest 内 scenario_config_sha256 不唯一（{len(unique)} 个）："
            f"{path}；歧义不得由父级快照掩盖"
        )
    return unique


def _manifest_scenario_sha(path: Path) -> str | None:
    declarations = _manifest_declarations(path)
    return declarations[0] if declarations else None


def a2_subtree_consistency(
    repo_root: Path, unit: str, provider_sha256: str
) -> dict[str, Any] | None:
    """BC-DATA-20：附录 A.2 关联的字节一致性检查域 = 该 source unit **自身归档子树**。

    §22.2 (1) 边界：只遍历 `repo_root/unit` 及其全部后代；解析后的物理路径
    越出该 root 的一律不入域（不跟随越界链接补证）。不读兄弟 unit、同 family
    邻居或仓库其他位置——本条只澄清 (b)，不扩成全仓扫描。

    §22.2 (2) 证人闭集：子树内任意深度 basename 恰为 `manifest.json` 的归档
    manifest；以及子树内任意深度、满足冻结 `SCENARIO_BYTE_PROVIDERS` /
    `is_allowed_embedded_snapshot` 判据的内嵌快照。其他 JSON、frame sidecar
    与 truth 不因文件名相似进入本集合；sidecar 只保留既有 `scenario_id`
    前置证明职责。

    §22.2 (3) 判据：每份**可读** manifest 的每个非空声明，以及每份合格快照的
    实测字节 SHA，必须全部等于 provider 的实测 SHA。同字节多副本允许；根级、
    祖先或最近文件**没有**覆盖旁支矛盾的优先权，故按相对路径升序统一求值。

    §22.2 (4)：返回 `None` = 域内全部显式证人一致（或不存在显式证人）；否则
    返回确定性的矛盾描述（`reason` / `path` / `declared_sha256` / 排序后的
    `witnesses`），(b) 关联即不成立。
    """
    base = repo_root / unit
    if not base.is_dir():
        return None
    boundary = base.resolve()

    def _inside(path: Path) -> bool:
        try:
            resolved = path.resolve()
        except OSError:
            return False
        return resolved == boundary or boundary in resolved.parents

    # (relative_path, kind, payload)：kind ∈ {manifest, snapshot}
    entries: list[tuple[str, str, Any]] = []
    for candidate in base.rglob(MANIFEST_NAME):
        if not candidate.is_file() or not _inside(candidate):
            continue
        relative = candidate.relative_to(repo_root).as_posix()
        # 歧义（单份 manifest 内多个互异 SHA）在此按既有合同硬失败。
        entries.append((relative, "manifest", _manifest_declarations(candidate)))
    for name in EMBEDDED_SNAPSHOT_NAMES:
        for candidate in base.rglob(name):
            if not candidate.is_file() or not _inside(candidate):
                continue
            relative = candidate.relative_to(repo_root).as_posix()
            if not is_allowed_embedded_snapshot(relative):
                continue
            entries.append((relative, "snapshot", sha256_file(candidate)))

    entries.sort(key=lambda item: (item[0], item[1]))
    witnesses = sorted({relative for relative, _, _ in entries})
    for relative, kind, payload in entries:
        if kind == "manifest":
            if payload is None:
                return {
                    "reason": "appendix_a2_subtree_manifest_unreadable",
                    "path": relative,
                    "declared_sha256": None,
                    "witnesses": witnesses,
                }
            for declared in payload:  # 零个声明 = 无声明，不构成矛盾
                if declared != provider_sha256:
                    return {
                        "reason": "appendix_a2_subtree_manifest_sha_mismatch",
                        "path": relative,
                        "declared_sha256": declared,
                        "witnesses": witnesses,
                    }
        elif payload != provider_sha256:
            return {
                "reason": "appendix_a2_subtree_snapshot_sha_mismatch",
                "path": relative,
                "declared_sha256": payload,
                "witnesses": witnesses,
            }
    return None


def bind_families(
    repo_root: Path, inventory_payload: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """BC-DATA-13：先绑 source unit，再聚合成 `scenario_partition`。

    `family` 只是附录 A 的报告/谱系标签，**不是**「必须只有一个 scenario
    SHA」的绑定域。同一 family 出现多个合法 SHA 时保留为多个 partition，
    不得整族退出；只有无法唯一绑定的 source unit 退出。
    """
    repo_root = Path(repo_root)
    provider_index = build_provider_index(repo_root)

    units: dict[str, dict[str, Any]] = {}
    for record in inventory_payload["records"]:
        if record["kind"] != roots.KIND_IMAGE or record["family"] is None:
            continue
        if record["decision"] != "INCLUDED":
            continue
        unit = roots.source_unit_for(record["path"])
        bucket = units.setdefault(
            unit,
            {
                "source_unit": unit,
                "family": record["family"],
                "layout_class": record["layout_class"],
                "frame_count": 0,
                "resolutions": {},
            },
        )
        bucket["frame_count"] += 1
        resolution = resolve_frame_scenario(repo_root, record["path"], provider_index)
        key = f"{resolution['status']}|{resolution['sha256']}"
        entry = bucket["resolutions"].setdefault(
            key, {"resolution": resolution, "frames": 0}
        )
        entry["frames"] += 1

    for bucket in units.values():
        bound = [
            item
            for item in bucket["resolutions"].values()
            if item["resolution"]["status"] == BINDING_BOUND
        ]
        distinct = {item["resolution"]["sha256"] for item in bound}
        if len(distinct) == 1 and len(bound) == len(bucket["resolutions"]):
            bucket["binding_status"] = BINDING_BOUND
            bucket["scenario_sha256"] = next(iter(distinct))
            bucket["scenario_path"] = bound[0]["resolution"]["path"]
        else:
            # 只有**无法唯一绑定的 source unit** 退出，不牵连同 family 的其他 unit。
            bucket["binding_status"] = BINDING_UNBOUND
            bucket["scenario_sha256"] = None
            bucket["scenario_path"] = None
            bucket["unbound_reason"] = (
                "source unit 内场景字节不唯一" if len(distinct) > 1 else "无可用归档场景字节"
            )
        bucket["resolutions"] = [
            {"key": key, **value} for key, value in sorted(bucket["resolutions"].items())
        ]

    families: dict[str, dict[str, Any]] = {}
    for unit in sorted(units):
        bucket = units[unit]
        family = families.setdefault(
            bucket["family"],
            {
                "family": bucket["family"],
                "layout_class": bucket["layout_class"],
                "source_units": [],
                "partitions": [],
                "frame_count": 0,
            },
        )
        family["source_units"].append(bucket)
        family["frame_count"] += bucket["frame_count"]

    for family in families.values():
        by_sha: dict[str, dict[str, Any]] = {}
        for bucket in family["source_units"]:
            if bucket["binding_status"] != BINDING_BOUND:
                continue
            partition = by_sha.setdefault(
                bucket["scenario_sha256"],
                {
                    "partition_id": f"{family['family']}|{bucket['scenario_sha256']}",
                    "family": family["family"],
                    "scenario_sha256": bucket["scenario_sha256"],
                    "scenario_path": bucket["scenario_path"],
                    "layout_class": bucket["layout_class"],
                    "binding_status": BINDING_BOUND,
                    "source_units": [],
                    "frame_count": 0,
                },
            )
            partition["source_units"].append(bucket["source_unit"])
            partition["frame_count"] += bucket["frame_count"]
        family["partitions"] = [by_sha[sha] for sha in sorted(by_sha)]
        family["unbound_source_units"] = sorted(
            bucket["source_unit"]
            for bucket in family["source_units"]
            if bucket["binding_status"] != BINDING_BOUND
        )
        family["binding_status"] = (
            BINDING_BOUND if family["partitions"] else BINDING_UNBOUND
        )
    return families


def resolve_road_data(
    repo_root: Path, scenario_document: dict[str, Any]
) -> dict[str, Any]:
    """§2.3 `road_data.json` 字节绑定：只接受与归档 sha 哈希相等的字节。"""
    declared = scenario_document.get("road_data_sha256")
    if not declared:
        return {"available": False, "reason": "归档 scenario 无 road_data_sha256"}
    repo_root = Path(repo_root)
    for pattern in roots.ROAD_DATA_PROVIDERS:
        for path in sorted(repo_root.glob(pattern)):
            if path.is_file() and sha256_file(path) == declared:
                return {
                    "available": True,
                    "sha256": declared,
                    "path": path.relative_to(repo_root).as_posix(),
                }
    return {"available": False, "reason": "无哈希相等的 road_data 字节", "sha256": declared}


# --- 历史布局交叉验证（BC-DATA-3） ----------------------------------------
def _pair_sort_key(frame_id: str, object_id: str) -> tuple[bytes, str, str]:
    digest = hashlib.sha256(f"{frame_id}/{object_id}".encode("utf-8")).digest()
    return (digest, frame_id, object_id)


def cross_validate_layout(
    layout_instances: Sequence[dict[str, Any]],
    samples: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """静态目录对象的投影框 vs 归档 distractor 真值框。

    `samples` 每项：`{"frame_id", "camera", "pairs": [{"object_id", "box_px"}]}`；
    调用方只应传入 **id 恰一映射到静态目录对象**的 distractor 对
    （BC-DATA-3：动态 target 既不构造 AABB 也不进本检查）。

    BC-DATA-24 (1)：比较域是 **viewport 裁剪后**的预测框——归档真值框本就裁在
    图像内，两个判据必须同域。50 对下限、centre `>= 0.9`、IoU median `>= 0.5`
    与 SHA 排序全部逐字不变；裁剪不参与选样。
    """
    by_name = {instance["scene_object_name"]: instance for instance in layout_instances}
    candidates: list[tuple[tuple[bytes, str, str], dict[str, Any]]] = []
    for sample in samples:
        for pair in sample["pairs"]:
            object_id = pair["object_id"]
            if object_id not in by_name:
                continue
            candidates.append(
                (
                    _pair_sort_key(sample["frame_id"], object_id),
                    {"sample": sample, "object_id": object_id, "box_px": pair["box_px"]},
                )
            )
    candidates.sort(key=lambda item: item[0])
    selected = [item[1] for item in candidates[: contract.CROSSCHECK_MIN_PAIRS]]
    if len(selected) < contract.CROSSCHECK_MIN_PAIRS:
        return {
            "status": BINDING_INVALID,
            "reason": "可检对不足 50（BC-DATA-3：不以动态 target 补数）",
            "pair_count": len(selected),
            "center_hit_ratio": None,
            "iou_median": None,
        }

    centre_hits = 0
    ious: list[float] = []
    for item in selected:
        camera = item["sample"]["camera"]
        amodal = project_boxes.project_aabb(camera, by_name[item["object_id"]])
        truth_box = item["box_px"]
        if amodal is None:
            ious.append(0.0)
            continue
        # BC-DATA-24 (1)：中心命中与 IoU **都只**用 viewport 裁剪后的预测框，
        # 与已归档的裁剪真值框同域比较。归档 `bbox_xywh_norm` 按项目协议裁在
        # 图像内，拿未裁剪的 amodal 框去比会把 viewport 边界误报成场景漂移：
        # 跑出画面下沿的车辆两框只有下沿不同，IoU 仍 ≈ 0.99999 而中心却掉出
        # 真值框（复核轮 4 F16 的实测指纹，证据 §16.5）。
        # 裁剪只发生在**选样之后**，不参与候选集与前 50 对的排序（BC-DATA-24 (2)）。
        projected = project_boxes.intersect(amodal, camera.viewport())
        if projected is None:
            # 与 viewport 无交集：按 centre miss + IoU 0.0 处理。
            ious.append(0.0)
            continue
        centre = ((projected[0] + projected[2]) / 2.0, (projected[1] + projected[3]) / 2.0)
        if (
            truth_box[0] <= centre[0] <= truth_box[2]
            and truth_box[1] <= centre[1] <= truth_box[3]
        ):
            centre_hits += 1
        ious.append(project_boxes.iou(projected, truth_box))

    centre_ratio = centre_hits / len(selected)
    iou_median = statistics.median(ious)
    passed = (
        centre_ratio >= contract.CROSSCHECK_CENTER_HIT_MIN_RATIO
        and iou_median >= contract.CROSSCHECK_IOU_MEDIAN_MIN
    )
    return {
        "status": BINDING_BOUND if passed else BINDING_INVALID,
        "reason": None if passed else "交叉验证阈值不达（基础场景可能在采集后被改过）",
        "pair_count": len(selected),
        "center_hit_ratio": centre_ratio,
        "iou_median": iou_median,
    }


def target_world_center_hit_ratio(samples: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """BC-DATA-3：m3 动态 target 的 `target_world_*_m` 中心落框率（仅此一项）。"""
    hits = 0
    total = 0
    for sample in samples:
        camera = sample["camera"]
        world = sample["target_world_m"]
        box = sample["truth_box_px"]
        total += 1
        camera_point = camera.to_camera_space(world)
        if camera_point[2] <= contract.NEAR_CLIP_Z_M:
            continue
        pixel = camera.project_camera_point(camera_point)
        if box[0] <= pixel[0] <= box[2] and box[1] <= pixel[1] <= box[3]:
            hits += 1
    ratio = None if total == 0 else hits / total
    return {
        "sample_count": total,
        "center_hit_ratio": ratio,
        "passed": bool(ratio is not None and ratio >= contract.CROSSCHECK_CENTER_HIT_MIN_RATIO),
    }


# --- BC-DATA-23：共用的 truth join + 逐 partition 历史交叉验证 ---------------
CROSSCHECK_NOT_APPLICABLE = "NOT_APPLICABLE_NO_ARCHIVED_FRAME_TRUTH"


class TruthJoinError(DistDataError):
    """归档真值按附录 A 应存在却读不到/join 不上（BC-DATA-23 (4) 硬失败）。"""


def load_frame_truth(
    repo_root: Path, frame_relative: str
) -> tuple[dict[str, Any] | None, str | None]:
    """帧 → `(truth_row, schema_family)`，**S2 与 S3 唯一的 truth join 实现**。

    BC-DATA-23 (3)：两阶段必须共用同一实现，禁止各写一套会漂移的路径规则。
    来源只经 `roots.truth_source_for` 的冻结映射；逐帧 JSON 直接读该文件，
    `.jsonl` 按帧文件名里的整数帧号与行内 `frame_id` 相等匹配。

    无冻结 truth source → `(None, None)`（该帧本就走扫掠代理，不是缺陷）。
    按附录 A 应存在却不可读/不可解析 → `TruthJoinError`；文件在但该帧无行 →
    `(None, schema)`，由调用方按各自合同处置。
    """
    source = roots.truth_source_for(frame_relative)
    if source is None:
        return None, None
    truth_path, schema_family = source
    absolute = Path(repo_root) / truth_path
    if not absolute.is_file():
        # 逐帧真值**部分覆盖**是归档的正常状态（实测 detect-scout1 768 帧只有
        # 705 个 truth 文件），S1 自己也把 `truth_join.present` 记成逐记录的
        # 布尔事实。故「该帧没有真值文件」返回 `(None, schema)` 交调用方按各自
        # 合同处置，**不是** BC-DATA-23 (4) 说的「源字节不可读」——那指的是
        # 文件在、但字节坏或 join 不上。此读法已退回接受角色确认。
        return None, schema_family
    try:
        if truth_path.endswith(".jsonl"):
            index = _frame_index(frame_relative)
            if index is None:
                return None, schema_family
            with absolute.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    if int(row.get("frame_id", -1)) == index:
                        return row, schema_family
            return None, schema_family
        return json.loads(absolute.read_text(encoding="utf-8")), schema_family
    except (OSError, ValueError) as exc:
        raise TruthJoinError(f"归档真值不可解析：{truth_path}（{exc}）") from exc


def _frame_index(frame_relative: str) -> int | None:
    digits = Path(frame_relative).stem.rsplit("_", 1)[-1]
    return int(digits) if digits.isdigit() else None


def _camera_for_frame(repo_root: Path, frame_relative: str):
    """帧相机只由同名 sidecar 的位姿与内参构造（BC-DATA-23 (3)）。"""
    sidecar = (Path(repo_root) / frame_relative).with_suffix(".json")
    if not sidecar.is_file():
        raise TruthJoinError(f"帧 sidecar 不存在：{sidecar}")
    try:
        document = json.loads(sidecar.read_text(encoding="utf-8"))
        return project_boxes.Camera.from_sidecar(document)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise TruthJoinError(f"帧 sidecar 不可用：{sidecar}（{exc}）") from exc


def cross_validate_partition(
    repo_root: Path, instances: Sequence[dict[str, Any]], frame_paths: Sequence[str]
) -> dict[str, Any]:
    """BC-DATA-23：对**一个精确 scenario partition** 做 §2.3 历史交叉验证。

    决定单位是 `(family, scenario_sha256)`；同 partition 的 source unit 合并
    取样，不同 SHA 永不混算（调用方保证分组）。schema 分轨逐字保留：

    - `scouting`：只把非空 distractor bbox 中能以 `distractor_id` **恰一**映射到
      本 partition 静态实例的对交给 `cross_validate_layout`；不足 50 对
      `INVALID`（不以动态 target 补数）。
    - `m3`：只把归档 `target_world_*_m` 与同帧 truth box 交给
      `target_world_center_hit_ratio`，中心命中率须 ≥ 0.9；不构造 target AABB、
      不算 target IoU、不拿它补静态 50 对；零个可检样本同样 `INVALID`。

    全部 INCLUDED 帧都没有冻结逐帧 truth source → `NOT_APPLICABLE_...`，不凭空
    使其 invalid。应存在却读不到/join 不上 → `INVALID` 并记确定性 reason。
    """
    by_name = {instance["scene_object_name"]: instance for instance in instances}
    scouting_samples: list[dict[str, Any]] = []
    m3_samples: list[dict[str, Any]] = []
    frames_with_source = 0
    unmapped_distractors = 0
    try:
        for frame_relative in frame_paths:
            row, schema = load_frame_truth(repo_root, frame_relative)
            if schema is None:
                continue
            frames_with_source += 1
            if row is None:
                continue
            camera = _camera_for_frame(repo_root, frame_relative)
            if schema == "scouting":
                pairs = []
                for item in row.get("distractors") or []:
                    box = item.get("bbox_xywh_norm")
                    object_id = item.get("distractor_id")
                    if not box or not object_id:
                        continue
                    if object_id not in by_name:
                        # id 不能恰一映射到本 partition 静态实例 → 不入检查集。
                        unmapped_distractors += 1
                        continue
                    pairs.append(
                        {
                            "object_id": object_id,
                            "box_px": project_boxes.denormalize_xywh(box, camera),
                        }
                    )
                if pairs:
                    scouting_samples.append(
                        {"frame_id": frame_relative, "camera": camera, "pairs": pairs}
                    )
            elif schema == "m3":
                if not row.get("truth_box_available"):
                    continue
                box_fields = (
                    row.get("truth_box_x"),
                    row.get("truth_box_y"),
                    row.get("truth_box_width"),
                    row.get("truth_box_height"),
                )
                world = (
                    row.get("target_world_x_m"),
                    row.get("target_world_y_m"),
                    row.get("target_world_z_m"),
                )
                if any(value is None for value in box_fields + world):
                    continue
                m3_samples.append(
                    {
                        "camera": camera,
                        "target_world_m": tuple(float(value) for value in world),
                        "truth_box_px": project_boxes.denormalize_xywh(
                            [float(value) for value in box_fields], camera
                        ),
                    }
                )
    except TruthJoinError as exc:
        return {
            "mode": "unavailable",
            "status": BINDING_INVALID,
            "reason": str(exc),
            "pair_count": 0,
            "sample_count": 0,
        }

    if frames_with_source == 0:
        return {
            "mode": "none",
            "status": CROSSCHECK_NOT_APPLICABLE,
            "reason": "本 partition 的 INCLUDED 帧均无冻结逐帧 truth source",
            "pair_count": 0,
            "sample_count": 0,
        }

    if scouting_samples:
        result = cross_validate_layout(instances, scouting_samples)
        return {
            "mode": "scouting",
            "status": result["status"],
            "reason": result["reason"],
            "pair_count": result["pair_count"],
            "sample_count": len(scouting_samples),
            "center_hit_ratio": result["center_hit_ratio"],
            "iou_median": result["iou_median"],
            "unmapped_distractor_pairs": unmapped_distractors,
        }
    if m3_samples:
        result = target_world_center_hit_ratio(m3_samples)
        return {
            "mode": "m3",
            "status": BINDING_BOUND if result["passed"] else BINDING_INVALID,
            "reason": None
            if result["passed"]
            else "m3 target 中心落框率不达 0.9（基础场景可能在采集后被改过）",
            "pair_count": 0,
            "sample_count": result["sample_count"],
            "center_hit_ratio": result["center_hit_ratio"],
            "iou_median": None,
        }
    return {
        "mode": "empty",
        "status": BINDING_INVALID,
        "reason": "有冻结 truth source，但零个可检样本（BC-DATA-23 (4)）",
        "pair_count": 0,
        "sample_count": 0,
        "unmapped_distractor_pairs": unmapped_distractors,
    }


def _frames_by_partition(
    inventory_payload: dict[str, Any], families: dict[str, dict[str, Any]]
) -> dict[str, list[str]]:
    """逐 partition 的 INCLUDED 图像帧路径（只经 S1 冻结记录，不猜路径）。"""
    partition_of_unit: dict[str, str] = {}
    for family in families.values():
        for partition in family["partitions"]:
            for unit in partition["source_units"]:
                partition_of_unit[unit] = partition["partition_id"]
    frames: dict[str, list[str]] = {}
    for record in inventory_payload["records"]:
        if record["kind"] != roots.KIND_IMAGE or record["decision"] != "INCLUDED":
            continue
        identifier = partition_of_unit.get(roots.source_unit_for(record["path"]))
        if identifier is None:
            continue
        frames.setdefault(identifier, []).append(record["path"])
    return {name: sorted(paths) for name, paths in frames.items()}


def default_inverse_premise(
    provider_index: dict[str, list[str]], base_scenario_sha256: str
) -> str:
    """BC-DATA-18：逆施 default 的**唯一**来源 = 基础几何自身的
    `source_scenario_sha256` 对应的唯一 provider。

    禁止取「字典序/首个 BOUND default family」的文档——那会让 default 分歧时
    其他 partition 的几何取决于族的字典序（复核 F5(b)）。
    """
    providers = sorted(provider_index.get(base_scenario_sha256) or [])
    if not providers:
        raise LayoutError(
            "逆施 default 的前提不可证：基础几何的 source_scenario_sha256 "
            f"{base_scenario_sha256} 在归档字节提供者中**没有**任何 provider"
        )
    # 唯一性判据是**字节**，不是路径条数：provider index 以 sha256 为键，
    # 同一 sha 下的多条路径按定义字节相同（真实归档该 sha 有 12 条同字节副本）。
    # 判在条数上会让 S2 在真实归档上必然硬失败，一个 partition 也派生不出来。
    return providers[0]


def build_layout(
    repo_root: Path,
    inventory_attempt: str,
    *,
    inventory: dict[str, Any] | None = None,
    pixels: Any | None = None,
) -> dict[str, Any]:
    """构建 S2 载荷：source unit 绑定 → scenario partition → 逐 partition 几何。

    BC-DATA-13：layout 几何按**精确 scenario SHA** 派生，`layout_class` 只作
    报告分层。BC-DATA-18：逆施 default 的唯一来源是基础几何自身的
    `source_scenario_sha256`；任一 partition 的 relocations 不可证时只使**该**
    partition `INVALID`，不得从字典序首个文档派生其他 partition。
    """
    repo_root = Path(repo_root)
    if inventory is None:
        # 正式路径：经 store 取冻结的 S1 工件（禁行边在此生效）。
        inventory, inventory_ref = ArtifactStore(repo_root).read(
            "inventory", inventory_attempt, requesting_stage=STAGE
        )
        inputs = [inventory_ref.as_reference()]
    else:
        # 只读 preflight 路径：S1 载荷在内存里，不落盘、也没有工件引用。
        # `inputs` 因此显式记为 preflight，绝不伪造一个 attempt/SHA 让它看起来
        # 像是引用了冻结工件。本路径的产物只用于诊断计数，不得当作 S2 工件。
        inputs = [{"kind": "inventory", "source": "in_memory_preflight"}]
    geometry = load_base_geometry(repo_root)
    families = bind_families(repo_root, inventory)
    provider_index = build_provider_index(repo_root)

    # BC-DATA-18：前提只能来自基础几何自己声明的 source scenario。
    premise_path = default_inverse_premise(
        provider_index, geometry["source_scenario_sha256"]
    )
    premise_document = json.loads(
        (repo_root / premise_path).read_text(encoding="utf-8")
    )
    unadjusted, phantom_candidates = unadjusted_base(
        geometry["instances"],
        premise_document.get("scene_adjustments", {}).get("vehicle_relocations", []),
    )

    partitions: dict[str, Any] = {}
    for family in families.values():
        for partition in family["partitions"]:
            identifier = partition["partition_id"]
            record = dict(partition)
            try:
                document = json.loads(
                    (repo_root / partition["scenario_path"]).read_text(encoding="utf-8")
                )
                derived = apply_layout(
                    unadjusted,
                    document.get("scene_adjustments", {}).get("vehicle_relocations", []),
                    phantom_candidates,
                )
            except (LayoutError, OSError, ValueError) as exc:
                # 只使**本** partition INVALID；其他 partition 与 scene-004 不受影响。
                record["binding_status"] = BINDING_INVALID
                record["reason"] = str(exc)
                partitions[identifier] = record
                continue
            record.update(
                {
                    "road_data": resolve_road_data(repo_root, document),
                    "route_world_m": document.get("target", {}).get("route_world_m", []),
                    "instance_count": len(derived["instances"]),
                    "phantom_count": len(derived["phantoms"]),
                    **derived,
                }
            )
            partitions[identifier] = record

    # BC-DATA-23：历史交叉验证在**写 `layout` 之前**、按精确 scenario partition
    # 完成，结果并入 S2 载荷；S3 不重算，也不得先冻结一个「待验证」的 layout。
    # 验证失败同步把该 partition 置 INVALID——一个 partition 失败只使自身
    # INVALID，不毒化同 family 的其他 SHA 或其他 family。
    frames_by_partition = _frames_by_partition(inventory, families)
    cross_validation: dict[str, Any] = {}
    for identifier in sorted(partitions):
        record = partitions[identifier]
        if record["binding_status"] != BINDING_BOUND:
            cross_validation[identifier] = {
                "mode": "skipped",
                "status": record["binding_status"],
                "reason": "partition 未绑定/派生失败，交叉验证不适用",
                "pair_count": 0,
                "sample_count": 0,
            }
            continue
        result = cross_validate_partition(
            repo_root, record["instances"], frames_by_partition.get(identifier, [])
        )
        cross_validation[identifier] = result
        if result["status"] == BINDING_INVALID:
            record["binding_status"] = BINDING_INVALID
            record["reason"] = f"交叉验证不通过：{result['reason']}"

    # P1-VLM-DATA-002 §2.2 第 2 条：巡览族的三项失效条件，与交叉验证同批在
    # **写 layout 之前**完成；一个 partition 失败只使自身 INVALID。像素源
    # 惰性构造——没有巡览族时不碰 Pillow，既有 partition 的路径完全不变。
    survey_validation: dict[str, Any] = {}
    for identifier in sorted(partitions):
        record = partitions[identifier]
        frames = frames_by_partition.get(identifier, [])
        survey_units = sorted(
            {
                unit
                for unit in (roots.source_unit_for(frame) for frame in frames)
                if roots.is_survey_unit(unit)
            }
        )
        if not survey_units:
            continue
        if record["binding_status"] != BINDING_BOUND:
            survey_validation[identifier] = {
                "status": record["binding_status"],
                "reason": "partition 已在上游失效，巡览判定不适用",
            }
            continue
        if pixels is None:
            from tools.dist_data import pixel_source  # noqa: PLC0415 - 惰性

            pixels = pixel_source.ArchivePixelSource(repo_root)
        result = validate_survey_partition(
            repo_root,
            record,
            frames,
            survey_units,
            geometry["instances"],
            pixels,
        )
        survey_validation[identifier] = result
        if result["status"] == BINDING_INVALID:
            record["binding_status"] = BINDING_INVALID
            record["reason"] = f"巡览族失效：{result['reason']}"

    return {
        "stage": STAGE,
        "inputs": inputs,
        "base_geometry_sha256": contract.BASE_GEOMETRY_SHA256,
        "default_inverse_premise": {
            "path": premise_path,
            "sha256": geometry["source_scenario_sha256"],
        },
        "families": {name: families[name] for name in sorted(families)},
        "scenario_partitions": {name: partitions[name] for name in sorted(partitions)},
        # BC-DATA-23 (5)：必有成员，按 partition id 排序；S7/G0 直接读它，
        # 缺成员即硬失败，没有静默空表 fallback。
        "cross_validation": {
            name: cross_validation[name] for name in sorted(cross_validation)
        },
        # P1-VLM-DATA-002 §2.2 第 2 条的逐 partition 判定；无巡览族时为空表。
        "survey_validation": {
            name: survey_validation[name] for name in sorted(survey_validation)
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S2 布局绑定（P1-VLM-DATA-001）")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--inventory-attempt", default="attempt-1")
    parser.add_argument("--attempt", default="attempt-1")
    parser.add_argument("--supersedes", default=None)
    parser.add_argument("--supersession-reason", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    payload = build_layout(repo_root, args.inventory_attempt)
    for name, partition in payload["scenario_partitions"].items():
        print(
            f"partition {name}: {partition['binding_status']} "
            f"帧 {partition.get('frame_count')} 实例 {partition.get('instance_count')} "
            f"phantom {partition.get('phantom_count')}"
        )
    if args.dry_run:
        return 0
    reference = ArtifactStore(repo_root).write(
        "layout",
        args.attempt,
        payload,
        supersedes=args.supersedes,
        supersession_reason=args.supersession_reason,
    )
    print(f"已写入 {reference.path}（sha256 {reference.sha256}）")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


# --- P1-VLM-DATA-002 §2.1(f)/§2.2 第 2 条：停放目标证人与巡览族失效条件 -----
# 本节的三个判定是 S2 的**权威**结论。`tools/run_grounding_survey.py` 的
# `close` 调用同一批函数算临时结论写进 completion，S2 重算，两者不等即硬
# 错误——所以实现只此一份，工具侧没有第二套算法。
# BC-SURVEY-12 冻结的连通性住在合同里（BC-SURVEY-14 把它投影进 S0 哈希面）；
# 本别名只是转发，`red_components` **实际读取**它，不是装饰性常量。
WITNESS_CONNECTIVITY = contract.SURVEY_WITNESS_CONNECTIVITY


def parked_target_visible_box(
    camera: project_boxes.Camera, position_world_m: Sequence[float]
) -> project_boxes.Rect | None:
    """停放目标的 viewport 裁剪后投影框；不在画面内返回 `None`。"""
    amodal = project_boxes.project_aabb(
        camera, contract.parked_target_bounds(position_world_m)
    )
    if amodal is None:
        return None
    return project_boxes.intersect(amodal, camera.viewport())


def _is_red(rgb: tuple[int, int, int]) -> bool:
    """S0 red 色相带 [345°,15°) ∧ S ≥ 0.5 ∧ V ≥ 0.35（§2.1(f)）。"""
    hue, saturation, value = colorsys.rgb_to_hsv(
        rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    )
    if saturation < contract.SURVEY_WITNESS_SATURATION_MIN:
        return False
    if value < contract.SURVEY_WITNESS_VALUE_MIN:
        return False
    return contract.hue_band(hue * 360.0) == "red"


def red_components(
    pixels: Any, frame_id: str, width: int, height: int
) -> list[dict[str, Any]]:
    """整帧 red 掩码的连通分量：`[{area, x0, y0, x1, y1}]`（像素框，右/下开）。

    BC-SURVEY-12 冻结本算法：整幅图扫描、**4-邻接**、右/下开像素框。8-邻接
    与投影框裁窗均被明令禁止（裁窗会让分量的外接框与面积依赖窗口大小，
    从而改变「面积最大者」的选择）。本条只冻结正式数据之前的算法，不声称
    像素门已通过。
    """
    if WITNESS_CONNECTIVITY != 4:
        # 本实现只写了 4-邻接；连通性一旦被改动，必须显式失败而不是继续按 4 跑。
        raise LayoutError(
            f"证人分量连通性被改为 {WITNESS_CONNECTIVITY}；BC-SURVEY-12 冻结为 4-邻接"
        )
    # sidecar 自述的画幅不足以定扫描范围：谎报**偏小**会静默变成左上角裁窗，
    # 而 BC-SURVEY-12 禁止任何裁窗。与真实字节尺寸对账后才扫。
    actual = pixels.dimensions(frame_id)
    if tuple(actual) != (width, height):
        raise LayoutError(
            f"sidecar 画幅与帧字节不符：{frame_id} sidecar {(width, height)}，"
            f"字节 {tuple(actual)}；整帧扫描不得建立在自述尺寸上"
        )
    flat = pixels.crop_rgb(frame_id, (0.0, 0.0, float(width), float(height)))
    if len(flat) != width * height:
        raise LayoutError(
            f"证人判定取到的像素数与画幅不符：{frame_id} 实测 {len(flat)}，"
            f"期望 {width * height}"
        )
    mask = [_is_red(rgb) for rgb in flat]
    labels = [0] * (width * height)
    parent: list[int] = [0]

    def find(node: int) -> int:
        root = node
        while parent[root] != root:
            root = parent[root]
        while parent[node] != root:
            parent[node], node = root, parent[node]
        return root

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)

    for row in range(height):
        base = row * width
        for column in range(width):
            index = base + column
            if not mask[index]:
                continue
            up = labels[index - width] if row and mask[index - width] else 0
            left = labels[index - 1] if column and mask[index - 1] else 0
            if up and left:
                labels[index] = min(up, left)
                union(up, left)
            elif up or left:
                labels[index] = up or left
            else:
                parent.append(len(parent))
                labels[index] = len(parent) - 1

    stats: dict[int, list[int]] = {}
    for row in range(height):
        base = row * width
        for column in range(width):
            label = labels[base + column]
            if not label:
                continue
            root = find(label)
            entry = stats.get(root)
            if entry is None:
                stats[root] = [1, column, row, column + 1, row + 1]
            else:
                entry[0] += 1
                entry[1] = min(entry[1], column)
                entry[2] = min(entry[2], row)
                entry[3] = max(entry[3], column + 1)
                entry[4] = max(entry[4], row + 1)
    return [
        {
            "area": entry[0],
            "box": (float(entry[1]), float(entry[2]), float(entry[3]), float(entry[4])),
        }
        for _root, entry in sorted(stats.items())
    ]


def select_witness_component(
    components: Sequence[dict[str, Any]], visible: project_boxes.Rect
) -> dict[str, Any] | None:
    """BC-SURVEY-12：只保留与投影 visible 框相交的分量，按 `(area, box)` 取最大。

    平手方向被冻结：面积相同时取**字典序较大**的 box。没有相交分量返回
    `None`（调用方按 IoU 0.0 计），不是抛错。
    """
    candidates = [
        component
        for component in components
        if project_boxes.intersect(component["box"], visible) is not None
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda component: (component["area"], component["box"]))


def evaluate_parked_witness(
    frames: Sequence[dict[str, Any]],
    parked_position_world_m: Sequence[float],
    pixels: Any,
) -> dict[str, Any]:
    """§2.1(f) 证人判定；`frames` = 证人视角窗内的 `VALID_SURVEY` 帧。

    每项 `{"frame_id": 仓库相对路径, "sidecar": dict}`。分母 = 投影 visible
    框短边 ≥ 12 px 的帧；不足 50 → `INSUFFICIENT_WITNESS_FRAMES`。
    """
    denominator: list[dict[str, Any]] = []
    for frame in frames:
        camera = project_boxes.Camera.from_sidecar(frame["sidecar"])
        visible = parked_target_visible_box(camera, parked_position_world_m)
        if visible is None:
            continue
        short_side = min(visible[2] - visible[0], visible[3] - visible[1])
        if short_side < contract.SURVEY_WITNESS_MIN_SIDE_PX:
            continue
        denominator.append({**frame, "camera": camera, "visible": visible})

    if len(denominator) < contract.SURVEY_WITNESS_MIN_DENOMINATOR:
        return {
            "verdict": "INSUFFICIENT_WITNESS_FRAMES",
            "denominator": len(denominator),
            "center_hit_ratio": None,
            "iou_median": None,
            "connectivity": WITNESS_CONNECTIVITY,
        }

    centre_hits = 0
    ious: list[float] = []
    for item in denominator:
        camera = item["camera"]
        visible = item["visible"]
        best = select_witness_component(
            red_components(pixels, item["frame_id"], camera.width, camera.height),
            visible,
        )
        if best is None:
            ious.append(0.0)
            continue
        observed = best["box"]
        centre = (
            (visible[0] + visible[2]) / 2.0,
            (visible[1] + visible[3]) / 2.0,
        )
        # BC-SURVEY-15：分量框是**右/下开**的，它的每一个消费者都必须按半开读。
        # 用闭区间会把恰落在右/下边界的中心误记为命中。
        if (
            observed[0] <= centre[0] < observed[2]
            and observed[1] <= centre[1] < observed[3]
        ):
            centre_hits += 1
        ious.append(project_boxes.iou(visible, observed))

    centre_ratio = centre_hits / len(denominator)
    iou_median = statistics.median(ious)
    passed = (
        centre_ratio >= contract.CROSSCHECK_CENTER_HIT_MIN_RATIO
        and iou_median >= contract.CROSSCHECK_IOU_MEDIAN_MIN
    )
    return {
        "verdict": "WITNESS_PASS" if passed else "WITNESS_FAIL",
        "denominator": len(denominator),
        "center_hit_ratio": centre_ratio,
        "iou_median": iou_median,
        "connectivity": WITNESS_CONNECTIVITY,
    }


def survey_audit_report_status(archive_root: Path) -> dict[str, Any]:
    """§2.2 第 2 条第一项：归档内的路线合法性审计报告必须存在且零违规。"""
    path = Path(archive_root) / "session" / "road_scene_audit.json"
    if not path.is_file():
        return {"present": False, "clear": False, "reason": f"缺归档审计报告：{path}"}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"present": True, "clear": False, "reason": f"审计报告不可解析：{exc}"}
    road = int(document.get("road_violation_count", -1))
    obstacle = int(document.get("obstacle_violation_count", -1))
    clear = document.get("status") == "CLEAR" and road == 0 and obstacle == 0
    return {
        "present": True,
        "clear": clear,
        "status": document.get("status"),
        "scenario_id": document.get("scenario_id"),
        "road_violation_count": road,
        "obstacle_violation_count": obstacle,
        "reason": None if clear else "归档审计报告非零违规",
    }


def survey_post_hoc_clearance(
    samples: Sequence[dict[str, Any]],
    anchor_world_m: Sequence[float],
    obstacle_boxes: Sequence[dict[str, float]],
) -> dict[str, Any]:
    """§2.2 第 2 条第三项：事后净空。

    任一 `VALID_SURVEY` 帧的 `camera_position_world_m` 到归档锚点距离
    > 35 m，或落入任一 `B'`，整族 `INVALID`。距离用系留全长 35 m（不是计划
    侧的 33 m 控制余量半径）——事后核验的是物理约束本身。
    """
    anchor = tuple(float(value) for value in anchor_world_m)
    max_distance = 0.0
    tether_violations: list[str] = []
    box_violations: list[dict[str, Any]] = []
    for sample in samples:
        position = tuple(float(value) for value in sample["camera_position_world_m"])
        distance = math.dist(position, anchor)
        max_distance = max(max_distance, distance)
        if distance > contract.SURVEY_TETHER_LENGTH_M:
            tether_violations.append(sample["frame_id"])
        inside = contract.boxes_containing(position, obstacle_boxes)
        if inside:
            box_violations.append({"frame_id": sample["frame_id"], "boxes": inside})
    passed = not tether_violations and not box_violations
    return {
        "passed": passed,
        "sample_count": len(samples),
        "max_tether_distance_m": max_distance,
        "tether_violation_frames": tether_violations[:5],
        "tether_violation_count": len(tether_violations),
        "box_violation_frames": box_violations[:5],
        "box_violation_count": len(box_violations),
        "reason": None if passed else "事后净空违规（系留距离或障碍扩展框）",
    }


def _survey_selection_rows(
    repo_root: Path, archive_root: Path
) -> tuple[dict[int, dict[str, Any]], frozenset[str]]:
    """→ `(frame_id → 行, 证人 id 集合)`；每一行都过 BC-SURVEY-13 的双重校验。

    校验域是 selection 的**全部**行，不只是本 partition 名下的帧：一份带
    非法标签的清单整体不可信。畸形输入 `raise`（不是 `INVALID`）——§2.2
    第 2 条的三项 `INVALID` 是数据判决，不是坏输入的处置。
    """
    archive_root = Path(archive_root)
    path = archive_root / "selection.json"
    if not path.is_file():
        raise LayoutError(f"巡览归档缺 selection.json：{path}")
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_version") != contract.SURVEY_SELECTION_SCHEMA:
        raise LayoutError(f"selection.json schema 不符：{path}")
    session_id = archive_root.name
    try:
        plan = contract.load_pinned_survey_plan(
            repo_root, archive_root / "session" / "manifest.json", session_id=session_id
        )
        survey_ids, witness_ids = contract.survey_plan_view_ids(plan)
    except contract.SurveyContractError as exc:
        raise LayoutError(f"巡览会话 {session_id} 的 plan 钉死校验失败：{exc}") from exc
    legal_ids = survey_ids | witness_ids
    rows: dict[int, dict[str, Any]] = {}
    for entry in document.get("entries", []):
        if "view_id" not in entry:
            raise LayoutError(f"selection 行缺 view_id 键：{entry!r}（{path}）")
        try:
            contract.validate_selection_view_id(
                entry["view_id"], entry.get("class"), legal_ids
            )
        except contract.SurveyContractError as exc:
            raise LayoutError(f"selection 行 view_id 非法：{exc}（{path}）") from exc
        rows[int(entry["frame_id"])] = entry
    return rows, witness_ids


def validate_survey_partition(
    repo_root: Path,
    record: dict[str, Any],
    frame_paths: Sequence[str],
    survey_units: Sequence[str],
    base_instances: Sequence[dict[str, Any]],
    pixels: Any,
) -> dict[str, Any]:
    """§2.2 第 2 条：巡览族的三项失效条件，任一不过即整族 `INVALID`。

    (1) 归档 `session/road_scene_audit.json` 缺失或非零违规；
    (2) 证人 `WITNESS_FAIL` / `INSUFFICIENT_WITNESS_FRAMES`；
    (3) 事后净空：任一 `VALID_SURVEY` 帧相机位置超系留或落入 `B'`。
    """
    repo_root = Path(repo_root)
    obstacle_boxes = contract.expanded_obstacle_boxes(base_instances)
    scenario = json.loads(
        (repo_root / record["scenario_path"]).read_text(encoding="utf-8")
    )
    anchor = scenario["anchor_world_m"]
    anchor_world_m = (float(anchor["x"]), float(anchor["y"]), float(anchor["z"]))
    route = scenario.get("target", {}).get("route_world_m") or []
    if len(route) < 2:
        return {
            "status": BINDING_INVALID,
            "reason": "归档场景字节缺两点停放段 route_world_m",
        }
    parked = (float(route[0]["x"]), float(route[0]["y"]), float(route[0]["z"]))

    audits: dict[str, Any] = {}
    valid_samples: list[dict[str, Any]] = []
    witness_frames: list[dict[str, Any]] = []
    frames_by_unit: dict[str, list[str]] = {}
    for frame in frame_paths:
        unit = roots.source_unit_for(frame)
        if roots.is_survey_unit(unit):
            frames_by_unit.setdefault(unit, []).append(frame)

    for unit in survey_units:
        archive_root = repo_root / unit
        audits[unit] = survey_audit_report_status(archive_root)
        rows, witness_ids = _survey_selection_rows(repo_root, archive_root)
        for frame in sorted(frames_by_unit.get(unit, [])):
            index = int(Path(frame).stem.rsplit("_", 1)[-1])
            row = rows.get(index)
            if row is None or row.get("class") != "VALID_SURVEY":
                continue
            sidecar_path = (repo_root / frame).with_suffix(".json")
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            valid_samples.append(
                {
                    "frame_id": frame,
                    "camera_position_world_m": sidecar["camera_position_world_m"],
                }
            )
            # BC-SURVEY-13：证人资格 = 该会话已复核 plan 的证人视角集合成员，
            # 不是 `w/` 前缀。
            if row["view_id"] in witness_ids:
                witness_frames.append({"frame_id": frame, "sidecar": sidecar})

    unclear = sorted(unit for unit, audit in audits.items() if not audit["clear"])
    if unclear:
        return {
            "status": BINDING_INVALID,
            "reason": f"归档路线合法性审计缺失或非零违规：{unclear}",
            "audits": audits,
        }

    witness = evaluate_parked_witness(witness_frames, parked, pixels)
    # §2.1(f) / §5 条件 3：`close` 写的是**临时**结论，S2 重算为权威，
    # **两者不等即硬错误**。此前只在测试里事后断言相等，生产路径从不读它。
    completion_path = (
        Path(repo_root)
        / roots.SURVEY_STATE_ROOT
        / Path(survey_units[0]).name
        / "completion.json"
    )
    if not completion_path.is_file():
        raise LayoutError(f"巡览会话缺 completion，无法比对临时证人结论：{completion_path}")
    tentative = json.loads(completion_path.read_text(encoding="utf-8")).get(
        "tentative_witness"
    )
    if tentative is None:
        raise LayoutError(
            f"completion 未记录临时证人结论：{completion_path}；"
            "§2.1(f) 要求与 S2 权威结论逐项比对"
        )
    mismatched = [
        key
        for key in ("verdict", "denominator", "center_hit_ratio", "iou_median",
                    "connectivity")
        if tentative.get(key) != witness.get(key)
    ]
    if mismatched:
        raise LayoutError(
            f"临时证人结论与 S2 权威结论不等：{mismatched}；"
            f"close 记 {tentative}，S2 重算 {witness}"
        )
    clearance = survey_post_hoc_clearance(valid_samples, anchor_world_m, obstacle_boxes)
    if witness["verdict"] != "WITNESS_PASS":
        status, reason = BINDING_INVALID, f"证人判定 {witness['verdict']}"
    elif not clearance["passed"]:
        status, reason = BINDING_INVALID, clearance["reason"]
    else:
        status, reason = BINDING_BOUND, None
    return {
        "status": status,
        "reason": reason,
        "audits": audits,
        "witness": witness,
        "post_hoc_clearance": clearance,
        "parked_position_world_m": list(parked),
        "anchor_world_m": list(anchor_world_m),
        "valid_survey_frames": len(valid_samples),
        "witness_frames": len(witness_frames),
    }
