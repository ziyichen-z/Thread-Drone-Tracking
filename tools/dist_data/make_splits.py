#!/usr/bin/env python3
"""S4 切分冻结（提案 §2.5，AR1-3 / AR2-2 / BC-DATA-2）。

切分原子 = 复制族 ∪ pHash 近重复并簇后的连通分量；留出物体按整数算术
`k_c = max(1, (3n+5)//10)` 抽取；test 用**全枚举 + 字典序目标向量**唯一
确定；D3 与 dev 按冻结的机械谓词与整数比较确定。四块（train ∣ dev ∣ test ∣
D3）在原子级两两互斥，并附机械泄漏断言。

BC-DATA-2：覆盖统计一律从 `pre_split_floor_eligible(f)` 派生；可指派 atom
< 2 → `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA`，> 20 →
`SPLIT_ENUMERATION_LIMIT_EXCEEDED`，二者都保全已有工件、不执行 S8。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import itertools
import math
from typing import Any, Iterable, Protocol, Sequence

from tools.dist_data import contract
from tools.dist_data.artifacts import DistDataError, deterministic_sort_key

STAGE = 4

SPLIT_TRAIN = "train"
SPLIT_DEV = "dev"
SPLIT_TEST = "test"
SPLIT_D3 = "d3"
SPLITS: tuple[str, ...] = (SPLIT_TRAIN, SPLIT_DEV, SPLIT_TEST, SPLIT_D3)


class SplitError(DistDataError):
    """S4 切分失败（一律 fail-closed）。"""


class SplitTerminal(DistDataError):
    """BC-DATA-2 的收束终态（保全工件、不执行 S8）。"""

    def __init__(self, terminal: str, detail: str) -> None:
        super().__init__(f"{terminal}：{detail}")
        self.terminal = terminal
        self.detail = detail


# --- pHash（§2.5 冻结参数） ----------------------------------------------
class GraySource(Protocol):
    """按帧提供 `PHASH_RESIZE × PHASH_RESIZE` 灰度矩阵的适配器。"""

    def gray_matrix(self, frame_id: str, size: int) -> Sequence[Sequence[float]]:
        ...


def _dct_1d(values: Sequence[float]) -> list[float]:
    """DCT-II（未归一化常数不影响阈值比较，但保留标准 √ 因子以便复核对齐）。"""
    n = len(values)
    output: list[float] = []
    for k in range(n):
        total = 0.0
        for index, value in enumerate(values):
            total += value * math.cos(math.pi * (index + 0.5) * k / n)
        scale = math.sqrt(1.0 / n) if k == 0 else math.sqrt(2.0 / n)
        output.append(scale * total)
    return output


def dct_2d(matrix: Sequence[Sequence[float]]) -> list[list[float]]:
    """可分离 2D DCT-II（先行后列）。"""
    rows = [_dct_1d(list(row)) for row in matrix]
    size = len(rows)
    columns = [_dct_1d([rows[r][c] for r in range(size)]) for c in range(len(rows[0]))]
    return [[columns[c][r] for c in range(len(columns))] for r in range(size)]


def phash(matrix: Sequence[Sequence[float]]) -> int:
    """32×32 DCT → 左上 8×8 → 中位数阈值 → 64 bit。"""
    size = contract.PHASH_RESIZE
    if len(matrix) != size or any(len(row) != size for row in matrix):
        raise SplitError(f"pHash 需要 {size}×{size} 灰度矩阵")
    transformed = dct_2d(matrix)
    keep = contract.PHASH_DCT_KEEP
    coefficients = [transformed[r][c] for r in range(keep) for c in range(keep)]
    ordered = sorted(coefficients)
    middle = len(ordered) // 2
    median = (ordered[middle - 1] + ordered[middle]) / 2.0
    bits = 0
    for index, value in enumerate(coefficients):
        if value > median:
            bits |= 1 << index
    return bits


def hamming(left: int, right: int) -> int:
    return (left ^ right).bit_count()


# --- 原子（复制族 ∪ 近重复并簇） -----------------------------------------
class _UnionFind:
    def __init__(self, items: Iterable[str]) -> None:
        self._parent = {item: item for item in items}

    def find(self, item: str) -> str:
        root = item
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[item] != root:
            self._parent[item], item = root, self._parent[item]
        return root

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self._parent[max(left_root, right_root)] = min(left_root, right_root)


# `atom_id` 连接符：单个空格（族 id 不含空格）。
ATOM_ID_JOINER = " "


def atom_id_for(family_ids: Sequence[str]) -> str:
    """`atom_id` = 分量内成员族 id 升序连接串的 SHA-256。"""
    joined = ATOM_ID_JOINER.join(sorted(family_ids))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def merge_atoms(
    family_of_frame: dict[str, str], phash_of_frame: dict[str, int]
) -> dict[str, Any]:
    """按 pHash 近重复（Hamming ≤ 8）把复制族并成最终原子（BC-DATA-26 有界表示）。

    研究与 split 语义不变：pHash、`PHASH_NEAR_DUPLICATE_HAMMING`、按
    `(left_frame_id, right_frame_id)` 字典序的跨族**全对**比较、并查集连通分量、
    `atom_id` 与 `near_duplicate_pair_count` 全部逐字保留——每一对合格 pair 仍被
    计数，只是**不再驻留**。

    接受轮 29 在真实归档上实测：全量 `near_duplicate_pairs` 有 2,663,282 对、占
    S4 manifest 512,888,211 B，随合格 pair 数二次增长，违反 BC-DATA-25 §33.2(4)
    「小型摘要留在 manifest」与 (5) 有界消费。该成员从未被冻结为研究输出，也没有
    生产消费者，故删除；manifest 改存 `near_duplicate_union_witnesses`：同序遍历
    时**首次**连接两个不同 family 分量的那一对。witness 数恰为
    `family_count − atom_count`，每对满足跨族与阈值条件；按同顺序重放
    （`replay_union_witnesses`）必须重建完全相同的 family→atom 分量——本函数在
    返回前对这两条不变量自检，任一不成立即 `SplitError`（fail-closed）。
    """
    families = sorted(set(family_of_frame.values()))
    union = _UnionFind(families)
    frames = sorted(phash_of_frame)
    pair_count = 0
    witnesses: list[list[str]] = []
    for left, right in itertools.combinations(frames, 2):
        family_left = family_of_frame[left]
        family_right = family_of_frame[right]
        if family_left == family_right:
            continue
        if (
            hamming(phash_of_frame[left], phash_of_frame[right])
            <= contract.PHASH_NEAR_DUPLICATE_HAMMING
        ):
            pair_count += 1
            # 只有首次连接两个不同分量的 pair 才是 witness；其余合格 pair 只计数。
            if union.find(family_left) != union.find(family_right):
                union.union(family_left, family_right)
                witnesses.append([left, right])
    atoms = _atoms_of(union, families)

    # BC-DATA-26 (3) 的两条不变量在生产路径上自检，不靠调用方。
    if len(witnesses) != len(families) - len(atoms):
        raise SplitError(
            f"union witness 数 {len(witnesses)} ≠ family_count − atom_count = "
            f"{len(families)} − {len(atoms)}"
        )
    replayed = replay_union_witnesses(family_of_frame, witnesses)
    if replayed != atoms:
        raise SplitError("按同顺序重放 union witnesses 未重建相同的 family→atom 分量")
    return {
        "atoms": atoms,
        "near_duplicate_pair_count": pair_count,
        "near_duplicate_union_witnesses": witnesses,
    }


def _atoms_of(union: _UnionFind, families: Sequence[str]) -> dict[str, list[str]]:
    """并查集分量 → `{atom_id: 升序成员族}`（键升序）。"""
    components: dict[str, list[str]] = {}
    for family in families:
        components.setdefault(union.find(family), []).append(family)
    atoms = {atom_id_for(members): sorted(members) for members in components.values()}
    return {atom: atoms[atom] for atom in sorted(atoms)}


def replay_union_witnesses(
    family_of_frame: dict[str, str], witnesses: Sequence[Sequence[str]]
) -> dict[str, list[str]]:
    """按 manifest 记录的顺序重放 union witnesses，重建 family→atom 分量。

    只做并查集合并，不再比较 pHash：witness 的跨族与阈值条件由
    `merge_atoms` 在记录时保证，重放只证明「这些 pair 就足以决定最终分量」。
    每对必须是两个**不同**分量的首次连接，否则 fail-closed——一对冗余 witness
    就意味着记录方不再受 family 数约束。
    """
    families = sorted(set(family_of_frame.values()))
    union = _UnionFind(families)
    for index, pair in enumerate(witnesses):
        if len(pair) != 2:
            raise SplitError(f"union witness #{index} 不是二元组：{pair!r}")
        left, right = pair
        if left not in family_of_frame or right not in family_of_frame:
            raise SplitError(f"union witness #{index} 引用了未知帧：{pair!r}")
        family_left, family_right = family_of_frame[left], family_of_frame[right]
        if family_left == family_right or union.find(family_left) == union.find(family_right):
            raise SplitError(
                f"union witness #{index} 未连接两个不同的 family 分量：{pair!r}"
            )
        union.union(family_left, family_right)
    return _atoms_of(union, families)


# --- 留出物体（对象级，先于任何表达生成） --------------------------------
def held_out_objects(object_ids: Sequence[str]) -> dict[str, Any]:
    """按类整数算术抽取留出物体；抽取顺序由冻结 seed 的哈希唯一化。"""
    per_class: dict[str, list[str]] = {}
    for object_id in object_ids:
        class_word = contract.class_for_scene_object(object_id)
        if class_word is None:
            continue
        per_class.setdefault(class_word, []).append(object_id)
    selection: dict[str, list[str]] = {}
    for class_word in sorted(per_class):
        members = sorted(per_class[class_word])
        count = contract.held_out_count(len(members))
        ordered = sorted(
            members, key=lambda item: deterministic_sort_key(contract.HELDOUT_SEED, item)
        )
        selection[class_word] = sorted(ordered[:count])
    held_out = sorted(item for members in selection.values() for item in members)
    return {
        "per_class": selection,
        "per_class_counts": {
            class_word: len(members) for class_word, members in sorted(selection.items())
        },
        "class_sizes": {
            class_word: len(members) for class_word, members in sorted(per_class.items())
        },
        "held_out_object_ids": held_out,
        "total": len(held_out),
    }


# --- 三互斥集 + train/dev 内分 -------------------------------------------
@dataclass
class AtomSummary:
    """S4 可见量（允许用于指派）：帧数、站位簇集合、出现对象集合、布局类、用途类资格。

    **不可见量**（唯一性计数、颜色可靠性、审计结果、任何模型输出与难度信号）
    一律不得进入本结构。
    """

    atom_id: str
    families: list[str] = field(default_factory=list)
    layout_classes: list[str] = field(default_factory=list)
    floor_eligible_frames: list[str] = field(default_factory=list)
    non_floor_frames: list[str] = field(default_factory=list)
    station_keys: list[str] = field(default_factory=list)
    object_ids: list[str] = field(default_factory=list)
    d3_eligible: bool = False

    @property
    def key(self) -> tuple[bytes, bytes]:
        return deterministic_sort_key(contract.SPLIT_SEED, self.atom_id)

    @property
    def floor_frame_count(self) -> int:
        return len(self.floor_eligible_frames)


def _subset_vector(
    subset: Sequence[AtomSummary], total_floor_frames: int
) -> tuple[int, int, int, tuple[tuple[bytes, bytes], ...]]:
    layout_classes = {layout for atom in subset for layout in atom.layout_classes}
    v1 = 0 if len(subset) >= contract.SPLIT_MIN_ATOMS else 1
    # 「两个布局类都有代表」：只有一类有 floor-eligible 原子时 v2 恒为 1，
    # 对所有候选同罚、不构成歧义（§2.5）。
    v2 = 0 if len(layout_classes) >= 2 else 1
    test_frames = sum(atom.floor_frame_count for atom in subset)
    v3 = abs(contract.SPLIT_TEST_FRAME_TARGET_DENOMINATOR * test_frames - total_floor_frames)
    v4 = tuple(sorted(atom.key for atom in subset))
    return (v1, v2, v3, v4)


def choose_test_atoms(atoms: Sequence[AtomSummary]) -> list[AtomSummary]:
    """test 指派 = 全枚举非空真子集 + 字典序目标向量最小（唯一解）。"""
    count = len(atoms)
    if count < contract.SPLIT_MIN_ATOMS:
        raise SplitTerminal(
            "INSUFFICIENT_SYMBOLIC_GROUNDING_DATA",
            f"可指派 atom 只有 {count} 个（< {contract.SPLIT_MIN_ATOMS}）",
        )
    if count > contract.SPLIT_MAX_ATOMS:
        raise SplitTerminal(
            "SPLIT_ENUMERATION_LIMIT_EXCEEDED",
            f"可指派 atom {count} 个（> {contract.SPLIT_MAX_ATOMS}），全枚举不予执行",
        )
    total_floor_frames = sum(atom.floor_frame_count for atom in atoms)
    best_vector = None
    best_subset: list[AtomSummary] = []
    indices = range(count)
    for size in range(1, count):  # 非空真子集
        for combination in itertools.combinations(indices, size):
            subset = [atoms[index] for index in combination]
            vector = _subset_vector(subset, total_floor_frames)
            if best_vector is None or vector < best_vector:
                best_vector = vector
                best_subset = subset
    return sorted(best_subset, key=lambda atom: atom.key)


def choose_d3_holdout(remaining: Sequence[AtomSummary]) -> AtomSummary | None:
    """D3 holdout = 满足机械谓词的剩余原子中 key 最小者；无满足者返回 None。"""
    candidates = sorted(
        [atom for atom in remaining if atom.d3_eligible], key=lambda atom: atom.key
    )
    return candidates[0] if candidates else None


def split_dev(train_side: Sequence[AtomSummary]) -> tuple[list[AtomSummary], list[AtomSummary]]:
    """dev = train 侧原子按 key 升序累加帧数、首次满足 `20·dev ≥ 3·total` 的最短前缀。"""
    ordered = sorted(train_side, key=lambda atom: atom.key)
    total = sum(atom.floor_frame_count for atom in ordered)
    dev: list[AtomSummary] = []
    accumulated = 0
    for atom in ordered:
        dev.append(atom)
        accumulated += atom.floor_frame_count
        if contract.DEV_FRACTION_DENOMINATOR * accumulated >= (
            contract.DEV_FRACTION_NUMERATOR * total
        ):
            break
    dev_ids = {atom.atom_id for atom in dev}
    train = [atom for atom in ordered if atom.atom_id not in dev_ids]
    return train, dev


def sample_roles_from_entries(entries: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """由 S3 catalog 记录装配逐 `(frame_id, object_id)` 角色（BC-DATA-19）。

    唯一调用点是 `assign_splits` 自身（复核轮 2 F11）：装配在 S4 内部完成，
    调用方只交 catalog 记录，既不能漏传角色，也不能交一份与 catalog 不一致
    的角色表。
    """
    roles: list[dict[str, Any]] = []
    for entry in entries:
        for item in entry.get("objects", []):
            exposure = item.get("exposure")
            if exposure not in ("referent", "distractor", "absent"):
                continue  # occluder_only 等非语言域对象不进 exposure（BC-DATA-16）
            roles.append(
                {
                    "frame_id": entry["frame_id"],
                    "object_id": item["object_id"],
                    "role": exposure,
                }
            )
    roles.sort(key=lambda item: (item["frame_id"], item["object_id"]))
    return roles


def assign_atoms(atoms: Sequence[AtomSummary]) -> dict[str, Any]:
    """原子级四块指派 + 连带规则 + 泄漏断言（**不含**逐 sample 角色）。

    `assign_splits` 与流式路径共用同一实现，保证两条路的 split 语义逐字相同；
    角色装配仍不可绕过——流式侧只能经 `assign_splits_streaming` 取角色。
    """
    floor_atoms = [atom for atom in atoms if atom.floor_frame_count > 0]
    test_atoms = choose_test_atoms(floor_atoms)
    test_ids = {atom.atom_id for atom in test_atoms}
    remaining = [atom for atom in floor_atoms if atom.atom_id not in test_ids]
    d3_atom = choose_d3_holdout(remaining)
    d3_ids = {d3_atom.atom_id} if d3_atom else set()
    train_side = [atom for atom in remaining if atom.atom_id not in d3_ids]
    train_atoms, dev_atoms = split_dev(train_side)

    assignment: dict[str, list[AtomSummary]] = {
        SPLIT_TRAIN: train_atoms,
        SPLIT_DEV: dev_atoms,
        SPLIT_TEST: test_atoms,
        SPLIT_D3: [d3_atom] if d3_atom else [],
    }
    dropped: list[str] = []
    frames_by_split: dict[str, list[str]] = {}
    for split, members in assignment.items():
        frames: list[str] = []
        for atom in members:
            frames.extend(atom.floor_eligible_frames)
            if split in (SPLIT_TEST, SPLIT_D3):
                dropped.extend(atom.non_floor_frames)
            else:
                frames.extend(atom.non_floor_frames)
        frames_by_split[split] = sorted(frames)
    non_floor_atoms = [atom for atom in atoms if atom.floor_frame_count == 0]
    for atom in non_floor_atoms:
        frames_by_split[SPLIT_TRAIN].extend(atom.non_floor_frames)
    frames_by_split[SPLIT_TRAIN] = sorted(set(frames_by_split[SPLIT_TRAIN]))
    leakage = assert_no_leakage(assignment, frames_by_split)
    return {
        "assignment": assignment,
        "frames_by_split": frames_by_split,
        "dropped": sorted(set(dropped)),
        "leakage": leakage,
        "split_of_frame": {
            frame: split for split, frames in frames_by_split.items() for frame in frames
        },
    }


def assign_splits_streaming(
    atoms: Sequence[AtomSummary], entries: Iterable[dict[str, Any]]
) -> tuple[Any, Any]:
    """流式指派：一遍扫描既产出有序角色行，又累加汇总（BC-DATA-25 (4)(5)）。

    → `(summary_callable, roles_iterator)`。角色仍**只能**由本函数产出，调用方
    无从漏传或另造一份与 catalog 不一致的角色表（复核轮 2 F11 的不可绕过性在
    流式路径同样成立）。汇总在行流耗尽后才成立，故以零参可调用返回。

    行序：S3 entry 按 `frame_id` 升序、entry 内对象按 `object_id` 升序，故
    encounter order 已等于 `(frame_id, object_id)` 排序，不需要全表排序。
    该不变量在此**断言**，一旦上游改序即 fail-closed，不会静默产出乱序工件。
    """
    base = assign_atoms(atoms)
    split_of_frame = base["split_of_frame"]
    accumulator = ExposureAccumulator()
    state: dict[str, Any] = {"previous": None}

    def _rows():
        for entry in entries:
            frame_id = entry["frame_id"]
            split = split_of_frame.get(frame_id)
            if split is None:
                continue
            for item in entry.get("objects", []):
                exposure = item.get("exposure")
                if exposure not in ("referent", "distractor", "absent"):
                    continue  # occluder_only 等非语言域对象不进 exposure（BC-DATA-16）
                key = (frame_id, item["object_id"])
                if state["previous"] is not None and key < state["previous"]:
                    raise SplitError(
                        "sample_roles 行流乱序："
                        f"{key} 出现在 {state['previous']} 之后；BC-DATA-25 (1) 要求"
                        "逐 (frame_id, object_id) 有序，上游 entry/对象排序被改动"
                    )
                state["previous"] = key
                row = {
                    "frame_id": frame_id,
                    "object_id": item["object_id"],
                    "role": exposure,
                    "split": split,
                }
                accumulator.add(row)
                yield row

    def _summary() -> dict[str, Any]:
        """与 `assign_splits` 的非 `sample_roles` 键**逐字同名同义**。"""
        assignment = base["assignment"]
        return {
            "exposure_matrix": accumulator.result(),
            "atom_assignment": {
                split: sorted(atom.atom_id for atom in members)
                for split, members in assignment.items()
            },
            "family_assignment": {
                split: sorted({family for atom in members for family in atom.families})
                for split, members in assignment.items()
            },
            "frames": base["frames_by_split"],
            "dropped_frames": base["dropped"],
            "d3_holdout_empty": not assignment[SPLIT_D3],
            "leakage_assertions": base["leakage"],
            "frame_counts": {
                split: len(frames) for split, frames in base["frames_by_split"].items()
            },
        }

    return _summary, _rows()


def assign_splits(
    atoms: Sequence[AtomSummary],
    catalog_entries: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """四块原子级指派 + 连带规则 + 机械泄漏断言。

    BC-DATA-19 / BC-DATA-2：`splits` 载荷必须**自带**逐 `(frame_id, object_id)`
    四集角色与逐对象 × 四集 exposure 汇总——不能只在 G0 报告里出现。

    角色由本函数**内部**从 S3 catalog 记录派生（`sample_roles_from_entries`），
    `catalog_entries` 是必填参数：调用方无从漏传，也无从传一份与 catalog
    不一致的角色表。带空默认值的可选角色参数已删除——成员名存在不等于
    生产路径上被装配，那正是复核轮 2 F11 的形态。

    原子指派、连带规则与泄漏断言**只有** `assign_atoms()` 一份实现（复核轮
    6 F22）：本函数只在该共享 base 上装配不可绕过的 sample roles，流式路径
    在同一 base 上产出角色行与汇总。平行复制的同构逻辑已删除，两条路的
    split 语义因此是结构性相同，而不是靠等价回归事后兜住。
    """
    base = assign_atoms(atoms)
    assignment = base["assignment"]
    frames_by_split = base["frames_by_split"]
    leakage = base["leakage"]
    split_of_frame = base["split_of_frame"]
    per_frame_object_roles = sample_roles_from_entries(catalog_entries)
    sample_roles = [
        {
            "frame_id": item["frame_id"],
            "object_id": item["object_id"],
            "role": item["role"],
            "split": split_of_frame[item["frame_id"]],
        }
        for item in per_frame_object_roles
        if item["frame_id"] in split_of_frame
    ]
    sample_roles.sort(key=lambda item: (item["frame_id"], item["object_id"]))
    return {
        "sample_roles": sample_roles,
        "exposure_matrix": exposure_matrix(sample_roles),
        "atom_assignment": {
            split: sorted(atom.atom_id for atom in members)
            for split, members in assignment.items()
        },
        "family_assignment": {
            split: sorted({family for atom in members for family in atom.families})
            for split, members in assignment.items()
        },
        "frames": frames_by_split,
        "dropped_frames": base["dropped"],
        "d3_holdout_empty": not assignment[SPLIT_D3],
        "leakage_assertions": leakage,
        "frame_counts": {split: len(frames) for split, frames in frames_by_split.items()},
    }


def assert_no_leakage(
    assignment: dict[str, Sequence[AtomSummary]], frames_by_split: dict[str, list[str]]
) -> dict[str, Any]:
    """四集在原子/谱系/帧三层两两交集为空；断言失败即停机。"""
    problems: list[str] = []
    for left, right in itertools.combinations(SPLITS, 2):
        atom_overlap = {atom.atom_id for atom in assignment[left]} & {
            atom.atom_id for atom in assignment[right]
        }
        if atom_overlap:
            problems.append(f"原子级交集 {left}∩{right}: {sorted(atom_overlap)}")
        family_overlap = {family for atom in assignment[left] for family in atom.families} & {
            family for atom in assignment[right] for family in atom.families
        }
        if family_overlap:
            problems.append(f"谱系级交集 {left}∩{right}: {sorted(family_overlap)}")
        frame_overlap = set(frames_by_split[left]) & set(frames_by_split[right])
        if frame_overlap:
            problems.append(f"帧级交集 {left}∩{right}: {sorted(frame_overlap)[:5]}")
    if problems:
        raise SplitError("机械泄漏断言失败：\n  " + "\n  ".join(problems))
    return {"pairwise_disjoint": True, "checked_pairs": len(list(itertools.combinations(SPLITS, 2)))}


def assert_held_out_never_referenced(
    held_out_ids: Iterable[str], training_candidates: Iterable[dict[str, Any]]
) -> None:
    """留出物体永不作训练指称目标、永不出现在任何训练表达文本中。"""
    held = set(held_out_ids)
    offenders: list[str] = []
    for candidate in training_candidates:
        # BC-DATA-17：target 与 resolved ref **两侧对称**——留出物体永不作训练
        # 指称目标，也永不出现在任何训练表达文本中（含关系的 ref 名词）。
        if candidate.get("object_id") in held:
            offenders.append(f"target={candidate['object_id']}")
        reference = candidate.get("resolved_reference_object_id")
        if reference in held and reference is not None:
            offenders.append(f"ref={reference}")
    if offenders:
        raise SplitError(f"留出物体出现在训练表达中：{sorted(offenders)[:5]}")


# --- exposure 矩阵（AR2-2 / BC-DATA-2） -----------------------------------
class ExposureAccumulator:
    """BC-DATA-25 (5)：逐行累加 exposure 汇总，避免驻留全部 `sample_roles`。

    结果与 `exposure_matrix(全表)` 逐字段等价（由
    `test_streamed_splits_preserves_all_sample_roles_and_exposure_counts` 钉死）。
    """

    def __init__(self) -> None:
        self._table: dict[str, dict[str, dict[str, int]]] = {}
        self._count = 0

    def add(self, item: dict[str, Any]) -> None:
        if item["split"] not in SPLITS:
            raise SplitError(f"未知 split {item['split']!r}")
        if item["role"] not in ("referent", "distractor", "absent"):
            raise SplitError(f"未知 exposure 角色 {item['role']!r}")
        per_object = self._table.setdefault(
            item["object_id"],
            {split: {"referent": 0, "distractor": 0, "absent": 0} for split in SPLITS},
        )
        per_object[item["split"]][item["role"]] += 1
        self._count += 1

    def result(self) -> dict[str, Any]:
        return {
            "per_object": {key: self._table[key] for key in sorted(self._table)},
            "sample_count": self._count,
            "wording": _EXPOSURE_WORDING,
        }


_EXPOSURE_WORDING = (
    "留出对象上的结果只能表述为「从未作为训练指称目标的对象」分层；"
    "禁止写成「未见物体/unseen object 泛化」。"
)


def exposure_matrix(
    per_sample_roles: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    """逐 sample 角色记录 → 逐对象 × 四集 exposure 表。

    `per_sample_roles` 每项：`{"frame_id", "object_id", "split", "role"}`，
    `role ∈ {referent, distractor, absent}`；BC-DATA-2 要求逐 sample 记录
    与四集汇总同时保存，不得省略 dev/D3。
    """
    table: dict[str, dict[str, dict[str, int]]] = {}
    for item in per_sample_roles:
        if item["split"] not in SPLITS:
            raise SplitError(f"未知 split {item['split']!r}")
        if item["role"] not in ("referent", "distractor", "absent"):
            raise SplitError(f"未知 exposure 角色 {item['role']!r}")
        per_object = table.setdefault(
            item["object_id"],
            {split: {"referent": 0, "distractor": 0, "absent": 0} for split in SPLITS},
        )
        per_object[item["split"]][item["role"]] += 1
    return {
        "per_object": {object_id: table[object_id] for object_id in sorted(table)},
        "sample_count": len(per_sample_roles),
        "wording": _EXPOSURE_WORDING,
    }
