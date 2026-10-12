#!/usr/bin/env python3
"""P1-VLM-DATA-002 巡览采集驱动器（阶段 A；纯 Python，零 C# 改动）。

六个子命令实现提案 §2.1(g) 的表：

    plan / prepare / drive / close / verify / diagnostic

只消费既有桥：`tethered-drone-control/v1` 的机身 `velocity_world` / `hold`
与云台 `look_at_world`、`tethered-frame-manifest/v1`、
`tethered-sensor-frame/v3`、`runtime/road_scene_audit.json`
（`p1-scene-road-audit/v1`）、`check_anchor_placement.strictly_inside_surface`、
`tools/dist_data/project_boxes`。

**几何、净空、证人与归档树的判据一律来自 `tools.dist_data.contract` 与
`tools.dist_data.bind_layout`**，本模块不复制任何一条——S2 的权威判定与
`close` 的临时结论因此不可能各说各话（§2.1(f)）。

授权边界（用户 2026-09-03 §6 授权 #1）：本模块可生成计划/配置身份、执行
至多 3 次零-ID 的 COORD-005 诊断，**不**执行正式采集 Play、不创建
session/run ID、不调用 API/GPU、不改 Unity scene asset 与
`config/scenario.default.json`。
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.check_anchor_placement import strictly_inside_surface  # noqa: E402
from tools.dist_data import bind_layout, contract, project_boxes, roots  # noqa: E402
from tools.dist_data.artifacts import canonical_json_bytes, sha256_file  # noqa: E402

WORK_ID = contract.SURVEY_WORK_ID
PLAN_SCHEMA = contract.SURVEY_PLAN_SCHEMA
DRIVE_LOG_SCHEMA = contract.SURVEY_DRIVE_LOG_SCHEMA
CONTROL_PROTOCOL = contract.SURVEY_CONTROL_PROTOCOL
FRAME_MANIFEST_SCHEMA = contract.SURVEY_FRAME_MANIFEST_SCHEMA
SENSOR_FRAME_SCHEMA = contract.SURVEY_SENSOR_FRAME_SCHEMA
ROAD_AUDIT_SCHEMA = contract.SURVEY_ROAD_AUDIT_SCHEMA

DEFAULT_SCENARIO_PATH = contract.SURVEY_DEFAULT_SCENARIO_PATH
PLAN_DIRECTORY = contract.SURVEY_PLAN_DIRECTORY
ACTIVE_MARKER = contract.SURVEY_ACTIVE_MARKER_FILENAME
RUNTIME_OVERRIDE = contract.SURVEY_RUNTIME_OVERRIDE_FILENAME

# §6 授权 #1/#2 的信封上限（缺项按 0，越界回用户 —— BC-SURVEY-6）。
MAX_FORMAL_PLAY = contract.SURVEY_MAX_FORMAL_PLAY
MAX_PLAN_IDENTITIES = contract.SURVEY_MAX_PLAN_IDENTITIES
MAX_DIAGNOSTIC_PLAY = contract.SURVEY_MAX_DIAGNOSTIC_PLAY

# BC-SURVEY-9：§8 表 2 **只冻结十个锚点的坐标、序号与使用顺序**。表内的
# 覆盖数、`99/101` 与候选生成叙述都是规划估计，不是门也不是可引用证据。
# `plan` 只接受本表内的锚点序号；锚点常量**不豁免** §2.1(c)–(f) 的位置、
# 转场、停放候选、系留与道路审计硬门，正式可达性只由这些门与 §2.4/§5 的
# 预注册终态决定。`recompute_anchor_candidates` 只输出诊断差异，任何不等
# 都不得使 `plan`/pipeline 失败，也不得改写本表。
ANCHOR_TABLE: tuple[tuple[int, float, float], ...] = contract.SURVEY_ANCHOR_TABLE
ANCHOR_Y_M = contract.SURVEY_ANCHOR_Y_M
ANCHOR_INDEX = {index: (x, z) for index, x, z in ANCHOR_TABLE}
# §8 表 2 的候选生成参数（只用于 `recompute_anchor_candidates` 诊断）。
ANCHOR_CANDIDATE_GRID_M = contract.SURVEY_ANCHOR_CANDIDATE_GRID_M
ANCHOR_COVERAGE_RADIUS_M = contract.SURVEY_ANCHOR_COVERAGE_RADIUS_M
# 出生点：锚点正上方 25 m（= default 的 `initial_altitude_m`）。
BIRTH_HEIGHT_M = contract.SURVEY_BIRTH_HEIGHT_M


class SurveyError(RuntimeError):
    """巡览工具的合同违反（一律 fail-closed，绝不静默降级）。"""


def _finite(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise SurveyError(f"{name} 必须有限：{value!r}")
    return result


def _atomic_write_json(path: Path, document: Any) -> Path:
    """原子写 JSON（与 `controller.protocol.atomic_write` 同款语义）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def _create_once_json(path: Path, document: Any, label: str) -> Path:
    """create-once：已存在且字节不同即硬错误，字节相同则幂等返回。"""
    payload = canonical_json_bytes(document)
    if path.exists():
        existing = path.read_bytes()
        if existing != payload:
            raise SurveyError(
                f"create-once 违反：{label} 已存在且字节不同（{path}）；"
                "换身份重来，绝不覆盖"
            )
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".creating")
    if temporary.exists():
        temporary.unlink()
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, path)  # 目标已存在即失败：不覆盖的原子发布
    finally:
        temporary.unlink()
    return path


def _git_head(repo_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or None


# --- 身份 ------------------------------------------------------------------
def plan_identity(anchor: int, plan_version: int, candidate: int) -> str:
    """`p1-vlm-survey-a<k>-p<v>-c<j>`（§2.1(a)）。"""
    if anchor not in ANCHOR_INDEX:
        raise SurveyError(
            f"锚点 {anchor} 不在冻结锚点表（合法序号 {sorted(ANCHOR_INDEX)}）"
        )
    if plan_version not in (1, 2):
        raise SurveyError(f"计划版本只能是 1 或 2（§2.4），收到 {plan_version}")
    if candidate < 1:
        raise SurveyError(f"停放候选序号从 1 起，收到 {candidate}")
    return f"p1-vlm-survey-a{anchor}-p{plan_version}-c{candidate}"


def session_identity(identity: str, index: int) -> str:
    if index < 1:
        raise SurveyError(f"会话序号从 1 起，收到 {index}")
    return f"{identity}-s{index}"


def scenario_path_for(identity: str) -> str:
    return f"config/scenario.{identity}.json"


def plan_path_for(identity: str) -> str:
    return contract.survey_plan_path(identity)


def archive_root_for(session: str) -> str:
    return f"{roots.SURVEY_ARCHIVE_ROOT}/{session}"


def state_root_for(session: str) -> str:
    return f"{roots.SURVEY_STATE_ROOT}/{session}"


# --- 场景与几何输入 --------------------------------------------------------
def load_default_scenario(repo_root: Path) -> dict[str, Any]:
    return json.loads((repo_root / DEFAULT_SCENARIO_PATH).read_text(encoding="utf-8"))


def load_road_data(repo_root: Path, expected_sha256: str) -> dict[str, Any]:
    """按场景声明的 `road_data_sha256` 取路面字节；不符即硬错误。"""
    path = repo_root / "config" / "road_data.json"
    digest = sha256_file(path)
    if digest != expected_sha256:
        raise SurveyError(
            f"road_data.json 哈希不符：实测 {digest}，场景声明 {expected_sha256}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def derived_catalog_vehicles(
    repo_root: Path, relocations: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    """§2.1(f)(iii)：由冻结基础几何按 default 六条调整派生的**实际**目录车辆。

    专用配置逐字继承 default 的 6 条 relocation/removal（§2.1(b)），所以这里
    传的就是 default 的那 6 条；派生走 S2 生产路径的同一对函数，不另写一套。
    """
    geometry = bind_layout.load_base_geometry(repo_root)
    unadjusted, phantom_candidates = bind_layout.unadjusted_base(
        geometry["instances"], relocations
    )
    derived = bind_layout.apply_layout(unadjusted, relocations, phantom_candidates)
    return [
        instance
        for instance in derived["instances"]
        if contract.class_for_scene_object(instance["scene_object_name"]) is not None
    ]


def obstacle_boxes(repo_root: Path) -> list[dict[str, float]]:
    """`B'` 闭集扩展框；障碍 = 冻结基础几何的全部**非车辆**实例（§2.1(c)）。"""
    geometry = bind_layout.load_base_geometry(repo_root)
    return contract.expanded_obstacle_boxes(geometry["instances"])


def recompute_anchor_candidates(repo_root: Path) -> dict[str, Any]:
    """§8 表 2 的候选生成**诊断**复算（BC-SURVEY-9：不是门）。

    冻结的只是锚点的坐标、序号与使用顺序；`2,684`、逐锚点覆盖数与
    `99/101` 都是规划估计。本函数把复算结果与表 2 声明的数字并列报告，供
    证据文件如实披露，任何不等都不得使 `plan`/pipeline 失败，也不得改写
    锚点表。
    """
    geometry = bind_layout.load_base_geometry(repo_root)
    boxes = [
        instance
        for instance in geometry["instances"]
        if str(instance.get("group")) != "vehicle"
    ]
    xs = [value for box in boxes for value in (box["min_x_m"], box["max_x_m"])]
    zs = [value for box in boxes for value in (box["min_z_m"], box["max_z_m"])]
    step = ANCHOR_CANDIDATE_GRID_M
    # 栅格相位取自冻结锚点表本身（表内 x ≡ 2、z ≡ 1 (mod 3)，实测），
    # 这样复算网格至少覆盖被冻结的那 10 个点。
    phase_x = ANCHOR_TABLE[0][1] % step
    phase_z = ANCHOR_TABLE[0][2] % step
    expanded = [
        (
            box["min_x_m"] - contract.SURVEY_OBSTACLE_EXPANSION_XZ_M,
            box["max_x_m"] + contract.SURVEY_OBSTACLE_EXPANSION_XZ_M,
            box["min_z_m"] - contract.SURVEY_OBSTACLE_EXPANSION_XZ_M,
            box["max_z_m"] + contract.SURVEY_OBSTACLE_EXPANSION_XZ_M,
        )
        for box in boxes
    ]
    candidates = 0
    x = math.floor((min(xs) - phase_x) / step) * step + phase_x
    while x <= max(xs):
        z = math.floor((min(zs) - phase_z) / step) * step + phase_z
        while z <= max(zs):
            if not any(x0 <= x <= x1 and z0 <= z <= z1 for x0, x1, z0, z1 in expanded):
                candidates += 1
            z += step
        x += step
    return {
        "grid_step_m": step,
        "grid_phase_xz_m": [phase_x, phase_z],
        "recomputed_candidates": candidates,
        "proposal_section8_declared_candidates": 2684,
        "matches_declared": candidates == 2684,
        "coverage_radius_m": ANCHOR_COVERAGE_RADIUS_M,
        "note": (
            "BC-SURVEY-9：§8 表 2 只冻结十个锚点的坐标、序号与使用顺序；"
            "2,684 与覆盖数是规划估计，不是门也不是可引用证据。本项是诊断"
            "复算，不参与任何判定，也不改写锚点表。"
        ),
    }


# --- 相机合成（供 plan 侧的证人可见性预测；与归档 sidecar 约定逐位一致） ---
def _normalize(vector: Sequence[float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(value * value for value in vector))
    if length <= 0.0:
        raise SurveyError("零长向量不能归一化")
    return (vector[0] / length, vector[1] / length, vector[2] / length)


def _cross(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def synthetic_camera(
    position_world_m: Sequence[float],
    look_at_world_m: Sequence[float],
    sensor: dict[str, Any],
) -> project_boxes.Camera:
    """按 Unity 归档 sidecar 的**同一**约定合成相机。

    实测自归档字节（`…arm-b-trial-1-post-run/frames/frame_0000000730.json`）：
    `right = normalize(cross(worldUp, forward))`、
    `up = normalize(cross(forward, right))`、
    `fx = fy = (height/2) / tan(vfov/2)`、`cx = width/2`、`cy = height/2`。
    本函数只用于 plan 侧的**预测**；正式判定一律读归档 sidecar 自己的基底。
    """
    forward = _normalize(
        [look_at_world_m[i] - position_world_m[i] for i in range(3)]
    )
    right = _normalize(_cross((0.0, 1.0, 0.0), forward))
    up = _normalize(_cross(forward, right))
    width = int(sensor["width"])
    height = int(sensor["height"])
    focal = (height / 2.0) / math.tan(math.radians(float(sensor["vertical_fov_deg"])) / 2.0)
    return project_boxes.Camera(
        position=tuple(float(value) for value in position_world_m),
        right=right,
        up=up,
        forward=forward,
        fx=focal,
        fy=focal,
        cx=width / 2.0,
        cy=height / 2.0,
        width=width,
        height=height,
    )


def off_nadir_deg(forward: Sequence[float]) -> float:
    """视线相对天底（世界 −y）的夹角，单位度。"""
    down = max(-1.0, min(1.0, -float(forward[1])))
    return math.degrees(math.acos(down))


def angle_between_deg(a: Sequence[float], b: Sequence[float]) -> float:
    left, right = _normalize(a), _normalize(b)
    dot = max(-1.0, min(1.0, sum(left[i] * right[i] for i in range(3))))
    return math.degrees(math.acos(dot))


# --- §2.1(f) 停放候选 ------------------------------------------------------
def _inset_surface(surface: dict[str, Any], inset: float) -> dict[str, Any]:
    """内缩 `inset` 米的 patch 副本；判据仍是 `strictly_inside_surface` 本体。"""
    return {
        **surface,
        "half_extent_x_m": float(surface["half_extent_x_m"]) - inset,
        "half_extent_z_m": float(surface["half_extent_z_m"]) - inset,
    }


def _local_margin(point: tuple[float, float], surface: dict[str, Any]) -> float:
    """点到 patch 四条边界的**最小局部余量**（未内缩的真实边界）。"""
    radians = -math.radians(float(surface["yaw_deg"]))
    cosine, sine = math.cos(radians), math.sin(radians)
    delta_x = point[0] - float(surface["center_x_m"])
    delta_z = point[1] - float(surface["center_z_m"])
    local_x = cosine * delta_x - sine * delta_z
    local_z = sine * delta_x + cosine * delta_z
    return min(
        float(surface["half_extent_x_m"]) - abs(local_x),
        float(surface["half_extent_z_m"]) - abs(local_z),
    )


def _inset_patches(
    point: tuple[float, float], surfaces: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    inset = contract.SURVEY_PARKED_SURFACE_INSET_M
    return [
        surface
        for surface in surfaces
        if strictly_inside_surface(point, _inset_surface(surface, inset))
    ]


def _clear_of_catalog_vehicles(
    point: tuple[float, float], vehicles: Sequence[dict[str, Any]]
) -> bool:
    limit = contract.SURVEY_PARKED_MIN_CATALOG_VEHICLE_M
    for vehicle in vehicles:
        centre = (
            (vehicle["min_x_m"] + vehicle["max_x_m"]) / 2.0,
            (vehicle["min_z_m"] + vehicle["max_z_m"]) / 2.0,
        )
        if math.dist(centre, point) < limit:
            return False
    return True


def _clear_of_obstacles(
    point: tuple[float, float], surface_y: float, raw_obstacles: Sequence[dict[str, Any]]
) -> bool:
    """(iv) 在任一障碍 AABB **扩 4 m** 之外。

    BC-SURVEY-8：「扩 4 m」是 x/y/z 三轴各向外 4 m 的**闭集**扩张；停放点
    `(x, surface_y, z)` 同时落入三个扩张轴区间才被拒绝。这是本合同的唯一
    三维语义，不是与纯水平判据的比较结果。
    """
    margin = contract.SURVEY_PARKED_OBSTACLE_MARGIN_M
    for obstacle in raw_obstacles:
        if (
            obstacle["min_x_m"] - margin <= point[0] <= obstacle["max_x_m"] + margin
            and obstacle["min_z_m"] - margin <= point[1] <= obstacle["max_z_m"] + margin
            and obstacle["min_y_m"] - margin <= surface_y <= obstacle["max_y_m"] + margin
        ):
            return False
    return True


def parked_candidates(
    repo_root: Path,
    anchor_world_m: tuple[float, float, float],
    scenario: dict[str, Any],
) -> list[dict[str, Any]]:
    """§2.1(f) 停放候选的完整机械枚举，按 `(|d − 8|, x, z)` 升序编号。"""
    road = load_road_data(repo_root, scenario["road_data_sha256"])
    surfaces = road["surfaces"]
    relocations = scenario.get("scene_adjustments", {}).get("vehicle_relocations", [])
    vehicles = derived_catalog_vehicles(repo_root, relocations)
    geometry = bind_layout.load_base_geometry(repo_root)
    raw_obstacles = [
        instance
        for instance in geometry["instances"]
        if str(instance.get("group")) != "vehicle"
    ]
    low, high = contract.SURVEY_PARKED_ANCHOR_DISTANCE_M
    anchor_xz = (anchor_world_m[0], anchor_world_m[2])
    span = int(math.ceil(high)) + 1
    found: list[dict[str, Any]] = []
    for x in range(int(math.floor(anchor_xz[0] - span)), int(math.ceil(anchor_xz[0] + span)) + 1):
        for z in range(
            int(math.floor(anchor_xz[1] - span)), int(math.ceil(anchor_xz[1] + span)) + 1
        ):
            point = (float(x), float(z))
            distance = math.dist(point, anchor_xz)
            if not (low <= distance <= high):
                continue
            head = _inset_patches(point, surfaces)
            if not head:
                continue
            far = (point[0], point[1] + contract.SURVEY_PARKED_SEGMENT_M)
            tail = _inset_patches(far, surfaces)
            if not tail:
                continue
            shared = [
                surface
                for surface in head
                if any(other["id"] == surface["id"] for other in tail)
            ]
            if not shared:
                continue  # (v) 两端必须落在**同一** patch
            # 平手规则：两端到四条边界的最小局部余量最大者；仍平手按 id 升序。
            canonical = max(
                shared,
                key=lambda surface: (
                    min(_local_margin(point, surface), _local_margin(far, surface)),
                    [-code for code in str(surface["id"]).encode("utf-8")],
                ),
            )
            surface_y = float(canonical["surface_y_m"])
            if not (
                _clear_of_catalog_vehicles(point, vehicles)
                and _clear_of_catalog_vehicles(far, vehicles)
                and _clear_of_obstacles(point, surface_y, raw_obstacles)
                and _clear_of_obstacles(far, surface_y, raw_obstacles)
            ):
                continue
            found.append(
                {
                    "position_world_m": [point[0], surface_y, point[1]],
                    "far_world_m": [far[0], surface_y, far[1]],
                    "surface_id": str(canonical["id"]),
                    "surface_y_m": surface_y,
                    "anchor_distance_m": distance,
                }
            )
    found.sort(
        key=lambda item: (
            abs(item["anchor_distance_m"] - contract.SURVEY_PARKED_MIN_CATALOG_VEHICLE_M),
            item["position_world_m"][0],
            item["position_world_m"][2],
        )
    )
    for index, item in enumerate(found, start=1):
        item["candidate_index"] = index
    return found


# --- §2.1(c) 位置、视角与顺序 ----------------------------------------------
def ring_radius(height_m: float) -> float:
    """`r(H) = 0.75·√(33² − H²)`（33 m = 35 m 系留减 2 m 控制余量）。"""
    radius_squared = contract.SURVEY_MAX_TETHER_RADIUS_M ** 2 - height_m ** 2
    if radius_squared <= 0.0:
        return 0.0
    return contract.SURVEY_RING_COEFFICIENT * math.sqrt(radius_squared)


def _position_world(
    anchor: tuple[float, float, float], radius: float, height: float, azimuth_deg: float
) -> tuple[float, float, float]:
    angle = math.radians(azimuth_deg)
    return (
        anchor[0] + radius * math.cos(angle),
        anchor[1] + height,
        anchor[2] + radius * math.sin(angle),
    )


def resolve_position(
    anchor: tuple[float, float, float],
    height_m: float,
    azimuth_deg: float,
    radius_m: float,
    boxes: Sequence[dict[str, float]],
) -> dict[str, Any]:
    """位置净空求解（§2.1(c)）：违规则 H 以 2 m 步长上调，**每步重算** r'。

    `r' = min(r, √(33² − H'²))`，θ 不变；到 30 m 仍违规即
    `PLAN_POSITION_DROPPED`。保留的位置断言 `√(r² + H²) ≤ 33` 与 H ∈ [8,30]。
    """
    height = height_m
    radius = radius_m
    attempts: list[dict[str, Any]] = []
    while height <= contract.SURVEY_MAX_HEIGHT_M:
        limit_squared = contract.SURVEY_MAX_TETHER_RADIUS_M ** 2 - height ** 2
        limit = math.sqrt(limit_squared) if limit_squared > 0.0 else 0.0
        radius = min(radius, limit)
        point = _position_world(anchor, radius, height, azimuth_deg)
        inside = contract.boxes_containing(point, boxes)
        attempts.append(
            {"height_m": height, "radius_m": radius, "blocking_boxes": inside[:3]}
        )
        if not inside:
            tether = math.hypot(radius, height)
            if tether > contract.SURVEY_MAX_TETHER_RADIUS_M + 1e-9:
                raise SurveyError(
                    f"位置系留距离 {tether} 超 {contract.SURVEY_MAX_TETHER_RADIUS_M} m"
                )
            if not (
                contract.SURVEY_MIN_HEIGHT_M - 1e-9
                <= height
                <= contract.SURVEY_MAX_HEIGHT_M + 1e-9
            ):
                raise SurveyError(f"位置高度 {height} 越出 [8, 30]")
            return {
                "kept": True,
                "height_m": height,
                "radius_m": radius,
                "azimuth_deg": azimuth_deg,
                "world_m": list(point),
                "tether_m": tether,
                "raise_attempts": attempts,
            }
        height += contract.SURVEY_HEIGHT_STEP_M
    return {
        "kept": False,
        "reason": "PLAN_POSITION_DROPPED",
        "azimuth_deg": azimuth_deg,
        "raise_attempts": attempts,
    }


def witness_azimuth_deg(
    anchor: tuple[float, float, float], parked_world_m: Sequence[float]
) -> float:
    """θ_W = 锚点→P_k 的方位角取整到最近 15° 倍数；正中点取较小者。"""
    raw = math.degrees(
        math.atan2(parked_world_m[2] - anchor[2], parked_world_m[0] - anchor[0])
    ) % 360.0
    quantum = contract.SURVEY_WITNESS_AZIMUTH_QUANTUM_DEG
    lower = math.floor(raw / quantum) * quantum
    remainder = raw - lower
    if remainder * 2.0 > quantum + 1e-12:
        lower += quantum
    return lower % 360.0


def survey_views(position: dict[str, Any]) -> list[dict[str, Any]]:
    """一个巡览位置的 16 个视角（离天底 20° 全方位角，再 44° 同序）。"""
    world = position["world_m"]
    height = position["height_m"]
    views: list[dict[str, Any]] = []
    for off_nadir in contract.SURVEY_OFF_NADIR_DEG:
        offset = height * math.tan(math.radians(off_nadir))
        for azimuth in contract.SURVEY_VIEW_AZIMUTHS_DEG:
            angle = math.radians(azimuth)
            views.append(
                {
                    "kind": "survey",
                    "off_nadir_deg": off_nadir,
                    "azimuth_deg": azimuth,
                    "look_at_world_m": [
                        world[0] + offset * math.cos(angle),
                        contract.SURVEY_GROUND_LOOK_AT_Y_M,
                        world[2] + offset * math.sin(angle),
                    ],
                    "dwell_s": contract.SURVEY_DWELL_S,
                    "min_valid_frames": contract.SURVEY_MIN_VALID_FRAMES_PER_VIEW,
                }
            )
    return views


def witness_view(parked_world_m: Sequence[float]) -> dict[str, Any]:
    return {
        "kind": "witness",
        "look_at_world_m": [float(value) for value in parked_world_m],
        "dwell_s": contract.SURVEY_WITNESS_DWELL_S,
        "min_valid_frames": contract.SURVEY_MIN_VALID_FRAMES_PER_WITNESS_VIEW,
    }


def transition_waypoints(
    start: Sequence[float],
    end: Sequence[float],
    anchor: tuple[float, float, float],
    boxes: Sequence[dict[str, float]],
) -> dict[str, Any]:
    """§2.1(d) + BC-SURVEY-1：直线转场，必要时三段绕行；不做侧向绕行。"""
    start = tuple(float(value) for value in start)
    end = tuple(float(value) for value in end)
    hits = contract.segment_intersecting_boxes(start, end, boxes)
    if not hits:
        return {"reachable": True, "mode": "direct", "waypoints": [list(end)]}
    safe_world_y = max(
        start[1],
        end[1],
        max(box["max_y_m"] for box in hits) + contract.SURVEY_DETOUR_EXTRA_M,
    )
    height_safe = safe_world_y - anchor[1]
    if not (
        contract.SURVEY_MIN_HEIGHT_M - 1e-9
        <= height_safe
        <= contract.SURVEY_MAX_HEIGHT_M + 1e-9
    ):
        return {
            "reachable": False,
            "reason": "PLAN_POSITION_UNREACHABLE",
            "detail": f"H_safe {height_safe} 越出 [8, 30]",
        }
    rise = (start[0], safe_world_y, start[2])
    cross = (end[0], safe_world_y, end[2])
    for point in (rise, cross):
        tether = math.dist(point, anchor)
        if tether > contract.SURVEY_MAX_TETHER_RADIUS_M + 1e-9:
            return {
                "reachable": False,
                "reason": "PLAN_POSITION_UNREACHABLE",
                "detail": f"绕行端点系留 {tether} > {contract.SURVEY_MAX_TETHER_RADIUS_M}",
            }
    legs = ((start, rise), (rise, cross), (cross, end))
    for leg_start, leg_end in legs:
        if contract.segment_intersecting_boxes(leg_start, leg_end, boxes):
            return {
                "reachable": False,
                "reason": "PLAN_POSITION_UNREACHABLE",
                "detail": "绕行三段仍与扩展框相交",
            }
    return {
        "reachable": True,
        "mode": "detour",
        "safe_world_y_m": safe_world_y,
        "height_safe_m": height_safe,
        "waypoints": [list(rise), list(cross), list(end)],
    }


# --- §2.1(f) 证人预测 ------------------------------------------------------
def predict_witness_views(
    views: Sequence[dict[str, Any]],
    parked_world_m: Sequence[float],
    sensor: dict[str, Any],
) -> list[dict[str, Any]]:
    """逐证人视角预测离天底 ≤ 40° 且 visible 框短边 ≥ 16 px；不满足者丢弃。"""
    predicted: list[dict[str, Any]] = []
    for view in views:
        camera = synthetic_camera(
            view["position_world_m"], view["look_at_world_m"], sensor
        )
        angle = off_nadir_deg(camera.forward)
        box = bind_layout.parked_target_visible_box(camera, parked_world_m)
        short_side = (
            None if box is None else min(box[2] - box[0], box[3] - box[1])
        )
        keep = (
            angle <= contract.SURVEY_WITNESS_PREDICT_MAX_OFF_NADIR_DEG
            and short_side is not None
            and short_side >= contract.SURVEY_WITNESS_PREDICT_MIN_SIDE_PX
        )
        predicted.append(
            {
                **view,
                "predicted_off_nadir_deg": angle,
                "predicted_short_side_px": short_side,
                "kept": keep,
            }
        )
    return predicted


# --- plan ------------------------------------------------------------------
def build_plan(
    repo_root: Path,
    anchor: int,
    plan_version: int,
    candidate: int,
    *,
    candidates: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """生成一个计划身份的完整 plan 载荷（纯函数；不写盘）。

    `candidates` 只是**同一** `parked_candidates` 输出的复用入口，供
    BC-SURVEY-16 的穷举求解免去逐候选重算（枚举本身占 build 的 ~92%）；
    传与不传的结果逐字相同，`test_precomputed_candidates_change_nothing`
    钉住这一点。
    """
    identity = plan_identity(anchor, plan_version, candidate)
    scenario_default = load_default_scenario(repo_root)
    anchor_x, anchor_z = ANCHOR_INDEX[anchor]
    anchor_world = (anchor_x, ANCHOR_Y_M, anchor_z)
    boxes = obstacle_boxes(repo_root)
    sensor = dict(scenario_default["sensor"])

    if candidates is None:
        candidates = parked_candidates(repo_root, anchor_world, scenario_default)
    if candidate > len(candidates):
        raise SurveyError(
            f"锚点 {anchor} 只有 {len(candidates)} 个合法停放候选，请求的第 "
            f"{candidate} 个不存在"
        )
    parked = candidates[candidate - 1]
    parked_world = tuple(parked["position_world_m"])

    # 位置：C14 → R14(θ 升序) → C26 → R26(θ 升序) → W26（访问顺序即本表序）。
    specifications: list[dict[str, Any]] = []
    for height in contract.SURVEY_HEIGHTS_M:
        radius = ring_radius(height)
        specifications.append(
            {"position_id": f"C{int(height)}", "height_m": height, "radius_m": 0.0,
             "azimuth_deg": 0.0, "role": "survey"}
        )
        for azimuth in contract.SURVEY_RING_AZIMUTHS_DEG:
            specifications.append(
                {
                    "position_id": f"R{int(height)}-{int(azimuth):03d}",
                    "height_m": height,
                    "radius_m": radius,
                    "azimuth_deg": azimuth,
                    "role": "survey",
                }
            )
    theta_witness = witness_azimuth_deg(anchor_world, parked_world)
    witness_height = contract.SURVEY_HEIGHTS_M[-1]
    specifications.append(
        {
            "position_id": "W26",
            "height_m": witness_height,
            "radius_m": ring_radius(witness_height),
            "azimuth_deg": theta_witness,
            "role": "witness",
        }
    )
    # C14/C26 在 16 个巡览视角之后各追加 1 个证人视角。冻结三元组住在合同里
    # （BC-SURVEY-13），本模块不再复制字面量。
    witness_positions = set(contract.SURVEY_WITNESS_POSITION_IDS)

    positions: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for specification in specifications:
        resolved = resolve_position(
            anchor_world,
            specification["height_m"],
            specification["azimuth_deg"],
            specification["radius_m"],
            boxes,
        )
        if not resolved["kept"]:
            dropped.append({**specification, **resolved})
            continue
        record = {**specification, **resolved}
        record["views"] = (
            [] if specification["role"] == "witness" else survey_views(record)
        )
        if specification["position_id"] in witness_positions:
            record["views"].append(witness_view(parked_world))
        for index, view in enumerate(record["views"]):
            view["position_world_m"] = list(record["world_m"])
            view["position_id"] = specification["position_id"]
            view["view_id"] = (
                contract.survey_witness_view_id(specification["position_id"])
                if view["kind"] == "witness"
                else contract.survey_view_id(specification["position_id"], index)
            )
        positions.append(record)

    # 证人视角预测：不达标者丢弃；预测证人帧 < 60 → 换下一候选。
    witness_views = [
        view for position in positions for view in position["views"]
        if view["kind"] == "witness"
    ]
    predicted = predict_witness_views(witness_views, parked_world, sensor)
    kept_witness_ids = {view["view_id"] for view in predicted if view["kept"]}
    for position in positions:
        position["views"] = [
            view
            for view in position["views"]
            if view["kind"] != "witness" or view["view_id"] in kept_witness_ids
        ]

    # 转场：出生点 → 各位置（按上表序）→ 结束悬停；不可达即丢弃终点位置，
    # 从上一位置直连下一位置重测。
    birth = (anchor_world[0], anchor_world[1] + BIRTH_HEIGHT_M, anchor_world[2])
    transitions: list[dict[str, Any]] = []
    reachable: list[dict[str, Any]] = []
    cursor: tuple[float, float, float] = birth
    for position in positions:
        result = transition_waypoints(cursor, position["world_m"], anchor_world, boxes)
        transitions.append(
            {
                "from_world_m": list(cursor),
                "to_position_id": position["position_id"],
                **result,
            }
        )
        if not result["reachable"]:
            dropped.append({**position, "kept": False, "reason": result["reason"],
                            "detail": result["detail"]})
            continue
        reachable.append(position)
        cursor = tuple(position["world_m"])

    survey_positions = [
        position for position in reachable if position["role"] == "survey"
    ]
    final_witness_views = [
        view for position in reachable for view in position["views"]
        if view["kind"] == "witness"
    ]
    # 预测证人帧的分母只能数**实际保留**的证人视角：转场不可达而被丢弃的
    # 位置不会产生任何帧，把它算进 60 帧下限就是 fail-open。
    predicted_frames = (
        len(final_witness_views) * contract.SURVEY_WITNESS_PREDICT_FRAMES_PER_VIEW
    )
    survey_view_count = sum(
        1 for position in reachable for view in position["views"]
        if view["kind"] == "survey"
    )
    valid = (
        len(survey_positions) >= contract.SURVEY_MIN_KEPT_SURVEY_POSITIONS
        and len(final_witness_views) >= contract.SURVEY_MIN_WITNESS_VIEWS
        and predicted_frames >= contract.SURVEY_WITNESS_PREDICT_MIN_FRAMES
    )
    return {
        "schema_version": PLAN_SCHEMA,
        "work_id": WORK_ID,
        # BC-SURVEY-14：plan 与 manifest 都携带采集协议 canonical bytes 的 SHA-256。
        "survey_acquisition_sha256": contract.survey_acquisition_sha256(),
        "plan_identity": identity,
        "anchor_index": anchor,
        "plan_version": plan_version,
        "candidate_index": candidate,
        "anchor_world_m": list(anchor_world),
        "birth_world_m": list(birth),
        "parked": parked,
        "witness_azimuth_deg": theta_witness,
        "parked_forward_world": list(contract.PARKED_TARGET_FORWARD_WORLD),
        "positions": reachable,
        "dropped_positions": dropped,
        "transitions": transitions,
        "witness_prediction": predicted,
        "predicted_witness_frames": predicted_frames,
        "survey_position_count": len(survey_positions),
        "survey_view_count": survey_view_count,
        "witness_view_count": len(final_witness_views),
        "valid": valid,
    }


# --- 场景配置生成（§2.1(b)：只允许改五个字段） -----------------------------
SURVEY_MUTABLE_FIELDS: tuple[str, ...] = contract.SURVEY_MUTABLE_SCENARIO_FIELDS


def build_scenario_config(
    repo_root: Path, plan: dict[str, Any]
) -> dict[str, Any]:
    """从 `config/scenario.default.json` 派生专用配置；**只改五个字段**。

    其余字节逐字继承——包括 default 已冻结的 6 条 relocation/removal
    （bootstrap 照常搬移 3 辆、移除 3 辆）、`road_data_sha256`、`sensor` 的
    分辨率/视场/帧率、`drone`、`gimbal`、`evaluation`（§2.1(b)、AR2-6）。
    """
    document = load_default_scenario(repo_root)
    anchor = plan["anchor_world_m"]
    parked = plan["parked"]
    document["scenario_id"] = plan["plan_identity"]
    document["anchor_world_m"] = {
        "x": anchor[0], "y": anchor[1], "z": anchor[2]
    }
    document["target"]["route_world_m"] = [
        {
            "x": parked["position_world_m"][0],
            "y": parked["position_world_m"][1],
            "z": parked["position_world_m"][2],
        },
        {
            "x": parked["far_world_m"][0],
            "y": parked["far_world_m"][1],
            "z": parked["far_world_m"][2],
        },
    ]
    document["target"]["speed_mps"] = 0
    document["sensor"]["retained_frame_count"] = contract.SURVEY_RETAINED_FRAME_COUNT
    return document


def scenario_diff_fields(default: dict[str, Any], derived: dict[str, Any]) -> list[str]:
    """列出两份场景文档所有**顶层与二层**不同的字段路径（用于机检五字段）。"""
    differences: list[str] = []

    def walk(left: Any, right: Any, prefix: str) -> None:
        if isinstance(left, dict) and isinstance(right, dict):
            for key in sorted(set(left) | set(right)):
                walk(left.get(key), right.get(key), f"{prefix}.{key}" if prefix else key)
            return
        if left != right:
            differences.append(prefix)

    walk(default, derived, "")
    return differences


# --- 会话状态、活动标记与信封 ----------------------------------------------
def runtime_dir(repo_root: Path) -> Path:
    return repo_root / "runtime"


def marker_path(repo_root: Path) -> Path:
    return runtime_dir(repo_root) / ACTIVE_MARKER


def override_path(repo_root: Path) -> Path:
    return runtime_dir(repo_root) / RUNTIME_OVERRIDE


def frames_dir(repo_root: Path) -> Path:
    return runtime_dir(repo_root) / "frames"


def spent_play_count(repo_root: Path) -> int:
    """已用正式 Play 数 = 已写出 completion 的会话数（含零帧会话）。"""
    base = repo_root / roots.SURVEY_STATE_ROOT
    if not base.is_dir():
        return 0
    return sum(
        1
        for child in sorted(base.iterdir())
        if child.is_dir() and (child / "completion.json").is_file()
    )


def existing_plan_identities(repo_root: Path) -> list[str]:
    base = repo_root / PLAN_DIRECTORY
    if not base.is_dir():
        return []
    return sorted(
        child.name for child in base.iterdir()
        if child.is_dir() and (child / "plan.json").is_file()
    )


def assert_runtime_quiescent(repo_root: Path) -> None:
    """`prepare`/`diagnostic` 的共同前置：现场必须干净（§2.1(g)）。"""
    frames = frames_dir(repo_root)
    if frames.is_dir():
        entries = sorted(child.name for child in frames.iterdir())
        if entries:
            raise SurveyError(
                f"runtime/frames/ 非空（{len(entries)} 项，前 5：{entries[:5]}）；"
                "先归档或移入 hold 再开始"
            )
    if override_path(repo_root).exists():
        raise SurveyError(
            f"已存在运行时场景覆盖 {override_path(repo_root)}；先卸载再开始"
        )
    if marker_path(repo_root).exists():
        marker = json.loads(marker_path(repo_root).read_text(encoding="utf-8"))
        raise SurveyError(
            f"已有活动巡览会话 {marker.get('session_id')!r}；同一时刻只允许一个"
        )
    for conflicting in ("rate-study", "p1-detect-scouting", "p1-scene-004-scouting"):
        path = runtime_dir(repo_root) / conflicting / "state.json"
        if path.exists():
            raise SurveyError(f"存在率研究/scouting 活动状态：{path}")


# BC-SURVEY-16：备用锚点的依序启用门。BC 逐字点名「备 9/10」，即冻结锚点表的
# 最后两行——这里由已投影的 `SURVEY_ANCHOR_TABLE` 派生，而不是新立一个会改动
# `survey_acquisition` 钉子的常量。
BACKUP_ANCHORS: tuple[int, ...] = tuple(
    row[0] for row in contract.SURVEY_ANCHOR_TABLE[-2:]
)
ANCHOR_DISPOSITION_CLOSED = "CLOSED"
ANCHOR_DISPOSITION_UNREACHABLE = "UNREACHABLE"
ANCHOR_DISPOSITION_PENDING = "PENDING"


def anchor_disposition(repo_root: Path, anchor: int, plan_version: int = 1) -> str:
    """一个锚点当前的处置：已 `close` / 不可达 / 仍待办。

    「已 close」= 该锚点任一计划身份下存在写出 `completion.json` 的会话；
    「不可达」= 该锚点没有正式计划身份且穷举后无合法候选。两者都算「已了结」，
    其余为 `PENDING`。
    """
    repo_root = Path(repo_root)
    state = repo_root / roots.SURVEY_STATE_ROOT
    if state.is_dir():
        for child in sorted(state.iterdir()):
            if not child.is_dir() or not (child / "completion.json").is_file():
                continue
            identity = contract.survey_plan_identity(child.name)
            if identity.startswith(f"p1-vlm-survey-a{anchor}-"):
                return ANCHOR_DISPOSITION_CLOSED
    if not (repo_root / plan_path_for(plan_identity(anchor, plan_version, 1))).is_file():
        # 没有正式身份：只有在穷举确认不可达时才算了结，否则仍是待办。
        if not resolve_anchor_plan(repo_root, anchor, plan_version)["reachable"]:
            return ANCHOR_DISPOSITION_UNREACHABLE
    return ANCHOR_DISPOSITION_PENDING


def assert_anchor_enabled(repo_root: Path, anchor: int, plan_version: int = 1) -> None:
    """BC-SURVEY-16：备 9/10 只在前八项分别已 `close` 或不可达后依序启用。

    前八个主锚点不受本门约束；备用锚点则要求它之前的每一个锚点都已了结。
    """
    if anchor not in BACKUP_ANCHORS:
        return
    pending = [
        index
        for index in range(1, anchor)
        if anchor_disposition(repo_root, index, plan_version)
        == ANCHOR_DISPOSITION_PENDING
    ]
    if pending:
        raise SurveyError(
            f"备用锚点 {anchor} 尚未启用：锚点 {pending} 既未 close 也未判不可达。"
            "BC-SURVEY-16 要求备 9/10 在其之前的锚点分别了结后才依序启用"
        )


def prepare_session(
    repo_root: Path, session: str, *, envelope_limit: int = MAX_FORMAL_PLAY
) -> dict[str, Any]:
    """安装场景、写 manifest 与活动标记（§2.1(g) `prepare`）。

    拒绝路径**不计次**：信封序号只在真正安装后才加一。
    """
    identity = contract.survey_plan_identity(session)
    plan_file = repo_root / plan_path_for(identity)
    scenario_file = repo_root / scenario_path_for(identity)
    if not plan_file.is_file() or not scenario_file.is_file():
        raise SurveyError(
            f"计划身份 {identity} 的 plan/config 尚未生成（{plan_file} / {scenario_file}）"
        )
    assert_runtime_quiescent(repo_root)
    # BC-SURVEY-16：备用锚点的依序启用门，早于任何现场安装。
    assert_anchor_enabled(repo_root, int(identity.split("-a")[1].split("-")[0]))
    # BC-SURVEY-14：发布 manifest 前先核对「已复核 plan 的钉子 == 当前投影」。
    plan_document = json.loads(plan_file.read_text(encoding="utf-8"))
    acquisition_pin = contract.assert_survey_acquisition_pin(
        plan_document.get("survey_acquisition_sha256"), where=f"prepare {session} 的 plan"
    )
    spent = spent_play_count(repo_root)
    if spent >= envelope_limit:
        raise SurveyError(
            f"信封用尽：已用正式 Play {spent} / 上限 {envelope_limit}（BC-SURVEY-6：越界回用户）"
        )
    state = repo_root / state_root_for(session)
    if (state / "completion.json").exists():
        raise SurveyError(f"会话 {session} 已 close，身份不可重用（每会话恰一次 Play）")

    scenario_bytes = scenario_file.read_bytes()
    manifest = {
        "schema_version": contract.SURVEY_MANIFEST_SCHEMA,
        "work_id": WORK_ID,
        "session_id": session,
        "plan_identity": identity,
        "scenario_path": scenario_path_for(identity),
        "scenario_config_sha256": sha256_file(scenario_file),
        "plan_path": plan_path_for(identity),
        "plan_sha256": sha256_file(plan_file),
        "survey_acquisition_sha256": acquisition_pin,
        "base_geometry_sha256": contract.BASE_GEOMETRY_SHA256,
        "road_data_sha256": json.loads(scenario_bytes)["road_data_sha256"],
        "git_head": _git_head(repo_root),
        "target_construction_oracle": contract.DYNAMIC_TARGET_SOURCE_AUTHORITY,
        "envelope_ordinal": spent + 1,
        "envelope_limit": envelope_limit,
        "archive_root": archive_root_for(session),
    }
    _create_once_json(state / "manifest.json", manifest, f"{session} manifest")
    override_path(repo_root).parent.mkdir(parents=True, exist_ok=True)
    override_path(repo_root).write_bytes(scenario_bytes)
    _atomic_write_json(
        marker_path(repo_root),
        {
            "schema_version": contract.SURVEY_ACTIVE_MARKER_SCHEMA,
            "session_id": session,
            "plan_identity": identity,
            "scenario_config_sha256": manifest["scenario_config_sha256"],
            "envelope_ordinal": manifest["envelope_ordinal"],
        },
    )
    return manifest


# --- 运行时桥（只用既有协议；可注入时钟以便无 Unity 测试） -----------------
class RuntimeBridge:
    """`runtime/` 文件桥的薄封装。控制指令一律经 `controller.*_entry` 发出。"""

    def __init__(
        self,
        repo_root: Path,
        *,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.runtime = runtime_dir(self.repo_root)
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        # BC-SURVEY-2：「发任何控制指令前」是个**事实**，不是可以从事件名反推的
        # 推论。桥自己数，`drive` 把计数写进日志头，零帧 `close` 直接读它。
        self.commands_issued = 0

    def latest_frame(self) -> tuple[int, dict[str, Any]] | None:
        """→ `(frame_id, sidecar)`；未发布或半发布返回 `None`。"""
        manifest_path = self.runtime / "frames" / "latest.json"
        if not manifest_path.is_file():
            return None
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if manifest.get("schema_version") != FRAME_MANIFEST_SCHEMA:
            raise SurveyError(
                f"帧清单 schema 不符：{manifest.get('schema_version')!r}"
            )
        metadata = manifest_path.parent / Path(manifest["metadata_file"]).name
        image = manifest_path.parent / Path(manifest["image_file"]).name
        if not metadata.is_file() or not image.is_file():
            return None  # 两个成员文件落盘后才算发布
        try:
            sidecar = json.loads(metadata.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if sidecar.get("schema_version") != SENSOR_FRAME_SCHEMA:
            raise SurveyError(
                f"帧 sidecar schema 不符：{sidecar.get('schema_version')!r}，"
                f"要求 {SENSOR_FRAME_SCHEMA!r}"
            )
        return int(manifest["frame_id"]), sidecar

    def road_audit(self) -> dict[str, Any] | None:
        path = self.runtime / "road_scene_audit.json"
        if not path.is_file():
            return None
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if document.get("schema_version") != ROAD_AUDIT_SCHEMA:
            raise SurveyError(f"审计报告 schema 不符：{document.get('schema_version')!r}")
        return document

    def send_velocity(self, velocity: Sequence[float]) -> None:
        from controller import body_entry  # noqa: PLC0415 - 只在真正发指令时导入

        self.commands_issued += 1
        body_entry.velocity(
            _finite(velocity[0], "vx"),
            _finite(velocity[2], "vz"),
            _finite(velocity[1], "vy"),
            contract.SURVEY_COMMAND_LEASE_S,
            runtime=self.runtime,
        )

    def send_hold(self) -> None:
        from controller import body_entry  # noqa: PLC0415

        self.commands_issued += 1
        body_entry.hold(contract.SURVEY_COMMAND_LEASE_S, runtime=self.runtime)

    def send_look_at(self, point: Sequence[float]) -> None:
        from controller import gimbal_entry  # noqa: PLC0415

        self.commands_issued += 1
        gimbal_entry.look_at(
            _finite(point[0], "x"),
            _finite(point[2], "z"),
            _finite(point[1], "y"),
            contract.SURVEY_COMMAND_LEASE_S,
            runtime=self.runtime,
        )


def _velocity_towards(
    current: Sequence[float], target: Sequence[float]
) -> tuple[tuple[float, float, float], float]:
    """`v = clamp(1.0·Δ, 3 m/s)`；返回 `(速度, 指令速率)`。"""
    delta = [target[i] - current[i] for i in range(3)]
    scaled = [contract.SURVEY_DRIVE_GAIN * value for value in delta]
    speed = math.sqrt(sum(value * value for value in scaled))
    if speed > contract.SURVEY_DRIVE_MAX_SPEED_MPS:
        factor = contract.SURVEY_DRIVE_MAX_SPEED_MPS / speed
        scaled = [value * factor for value in scaled]
        speed = contract.SURVEY_DRIVE_MAX_SPEED_MPS
    return (scaled[0], scaled[1], scaled[2]), speed


class DriveSession:
    """§2.1(g) `drive` 的状态机；一次运行对应一次 Play。"""

    def __init__(
        self,
        repo_root: Path,
        session: str,
        plan: dict[str, Any],
        bridge: RuntimeBridge,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.session = session
        self.plan = plan
        self.bridge = bridge
        self.log: list[dict[str, Any]] = []
        self.started = bridge.clock()
        self.last_frame_id: int | None = None
        self.last_frame_at = self.started

    # --- 记录 ---------------------------------------------------------------
    def _record(self, event: str, **fields: Any) -> None:
        self.log.append({"event": event, "t_s": self.bridge.clock() - self.started, **fields})

    # --- 帧观察 -------------------------------------------------------------
    def _observe(self) -> tuple[int, dict[str, Any]] | None:
        observation = self.bridge.latest_frame()
        if observation is None:
            return None
        frame_id, _sidecar = observation
        if frame_id != self.last_frame_id:
            self.last_frame_id = frame_id
            self.last_frame_at = self.bridge.clock()
        return observation

    def _check_deadlines(self) -> str | None:
        now = self.bridge.clock()
        if now - self.started > contract.SURVEY_SESSION_TIMEOUT_S:
            return "ABORTED_TIMEOUT"
        if now - self.last_frame_at > contract.SURVEY_NO_FRAME_TIMEOUT_S:
            return "ABORTED_NO_FRAMES"
        return None

    # --- 前置：首帧 + 零违规审计（发任何控制指令**之前**） -------------------
    def await_first_frame(self) -> tuple[int, dict[str, Any]] | None:
        deadline = self.bridge.clock() + contract.SURVEY_NO_FRAME_TIMEOUT_S
        while self.bridge.clock() <= deadline:
            observation = self._observe()
            if observation is not None:
                return observation
            self.bridge.sleep(contract.SURVEY_DRIVE_TICK_S)
        return None

    def verify_preconditions(self, sidecar: dict[str, Any]) -> str | None:
        """BC-SURVEY-2：观察到首帧后、发任何控制前核对场景与零违规审计。"""
        identity = contract.survey_plan_identity(self.session)
        if sidecar.get("scenario_id") != identity:
            return f"帧 sidecar 的 scenario_id 是 {sidecar.get('scenario_id')!r}，期望 {identity!r}"
        audit = self.bridge.road_audit()
        if audit is None:
            return "缺 runtime/road_scene_audit.json"
        if audit.get("scenario_id") != identity:
            return f"审计报告属于 {audit.get('scenario_id')!r}，不是本会话场景"
        if audit.get("status") != contract.SURVEY_ROAD_AUDIT_CLEAR_STATUS:
            return f"审计报告 status = {audit.get('status')!r}"
        if int(audit.get("road_violation_count", -1)) or int(
            audit.get("obstacle_violation_count", -1)
        ):
            return "审计报告违规计数非零"
        return None

    # --- 航点 ---------------------------------------------------------------
    def goto(self, waypoint: Sequence[float]) -> str:
        """飞到一个航点；→ `ARRIVED` / `UNREACHABLE_RUNTIME` / 中止终态。"""
        deadline = self.bridge.clock() + contract.SURVEY_WAYPOINT_TIMEOUT_S
        while True:
            terminal = self._check_deadlines()
            if terminal is not None:
                return terminal
            if self.bridge.clock() > deadline:
                self.bridge.send_hold()
                return "UNREACHABLE_RUNTIME"
            observation = self._observe()
            if observation is None:
                self.bridge.sleep(contract.SURVEY_DRIVE_TICK_S)
                continue
            position = observation[1]["camera_position_world_m"]
            velocity, speed = _velocity_towards(position, waypoint)
            distance = math.dist(
                tuple(float(value) for value in position),
                tuple(float(value) for value in waypoint),
            )
            if (
                distance <= contract.SURVEY_ARRIVAL_DISTANCE_M
                and speed <= contract.SURVEY_ARRIVAL_SPEED_MPS
            ):
                self.bridge.send_hold()
                self._settle(contract.SURVEY_SETTLE_S)
                return "ARRIVED"
            self.bridge.send_velocity(velocity)
            self.bridge.sleep(contract.SURVEY_DRIVE_TICK_S)

    def _settle(self, seconds: float) -> None:
        deadline = self.bridge.clock() + seconds
        while self.bridge.clock() < deadline:
            self._observe()
            self.bridge.sleep(contract.SURVEY_DRIVE_TICK_S)

    # --- 视角 ---------------------------------------------------------------
    def execute_view(self, view: dict[str, Any]) -> dict[str, Any]:
        """发 `look_at_world` → 稳定 → 停留；记录停留窗的 frame_id 闭区间。"""
        self.bridge.send_look_at(view["look_at_world_m"])
        stabilize_deadline = (
            self.bridge.clock() + contract.SURVEY_VIEW_SETTLE_TIMEOUT_S
        )
        settle_until = self.bridge.clock() + contract.SURVEY_SETTLE_S
        stabilized = False
        while self.bridge.clock() <= stabilize_deadline:
            terminal = self._check_deadlines()
            if terminal is not None:
                return {"view_id": view["view_id"], "outcome": terminal}
            observation = self._observe()
            if observation is not None and self.bridge.clock() >= settle_until:
                sidecar = observation[1]
                desired = [
                    view["look_at_world_m"][i] - sidecar["camera_position_world_m"][i]
                    for i in range(3)
                ]
                if (
                    angle_between_deg(sidecar["camera_forward_world"], desired)
                    <= contract.SURVEY_BEARING_TOLERANCE_DEG
                ):
                    stabilized = True
                    break
            self.bridge.sleep(contract.SURVEY_DRIVE_TICK_S)
        if not stabilized:
            self._record("view_skipped", view_id=view["view_id"], reason="NOT_STABILIZED")
            return {"view_id": view["view_id"], "outcome": "SKIPPED_NOT_STABILIZED"}

        first = self.last_frame_id
        dwell_deadline = self.bridge.clock() + float(view["dwell_s"])
        while self.bridge.clock() < dwell_deadline:
            terminal = self._check_deadlines()
            if terminal is not None:
                return {"view_id": view["view_id"], "outcome": terminal}
            self._observe()
            self.bridge.sleep(contract.SURVEY_DRIVE_TICK_S)
        window = {
            "view_id": view["view_id"],
            "position_id": view["position_id"],
            "kind": view["kind"],
            "outcome": "DWELL_COMPLETE",
            "position_world_m": list(view["position_world_m"]),
            "look_at_world_m": list(view["look_at_world_m"]),
            "frame_window": [first, self.last_frame_id],
            "min_valid_frames": view["min_valid_frames"],
        }
        self._record("view_window", **window)
        return window

    # --- 主循环 -------------------------------------------------------------
    def run(self) -> dict[str, Any]:
        first = self.await_first_frame()
        if first is None:
            self._record("aborted", reason="ABORTED_NO_FRAMES", stage="await_first_frame")
            return {
                "terminal": "ABORTED_NO_FRAMES",
                "views": [],
                "log": self.log,
                "commands_issued": self.bridge.commands_issued,
            }
        problem = self.verify_preconditions(first[1])
        if problem is not None:
            # 一条控制指令也没发过：零帧 `close` 路径接受本 log（BC-SURVEY-2）。
            self._record("drive_refused", reason="DRIVE_REFUSED_AUDIT", detail=problem)
            return {
                "terminal": "DRIVE_REFUSED_AUDIT",
                "detail": problem,
                "views": [],
                "log": self.log,
                "pre_command": True,
                "commands_issued": self.bridge.commands_issued,
            }
        self._record("preconditions_ok", first_frame_id=first[0])

        windows: list[dict[str, Any]] = []
        skipped_positions: list[str] = []
        # 转场记录必须**在场且显式可达**：缺记录或缺 `reachable` 键时直飞终点
        # 会把 BC-SURVEY-1 计算出的绕行几何整条丢掉，等于穿越扩展框。
        transitions: dict[str, dict[str, Any]] = {}
        for item in self.plan["transitions"]:
            if "reachable" not in item:
                raise SurveyError(
                    f"plan 转场记录缺 reachable 键：{item.get('to_position_id')!r}"
                )
            if item["reachable"] is True:
                transitions[item["to_position_id"]] = item
        for position in self.plan["positions"]:
            transition = transitions.get(position["position_id"])
            if transition is None:
                raise SurveyError(
                    f"plan 保留了位置 {position['position_id']!r} 却没有可达的转场"
                    "记录；计划自相矛盾，拒绝驱动"
                )
            waypoints = transition["waypoints"]
            outcome = "ARRIVED"
            for waypoint in waypoints:
                outcome = self.goto(waypoint)
                if outcome != "ARRIVED":
                    break
            if outcome in ("ABORTED_NO_FRAMES", "ABORTED_TIMEOUT"):
                self._record("aborted", reason=outcome, position_id=position["position_id"])
                return {
                    "terminal": outcome,
                    "views": windows,
                    "log": self.log,
                    "commands_issued": self.bridge.commands_issued,
                }
            if outcome != "ARRIVED":
                skipped_positions.append(position["position_id"])
                self._record(
                    "position_skipped",
                    position_id=position["position_id"],
                    reason=outcome,
                )
                continue
            for view in position["views"]:
                window = self.execute_view(view)
                if window["outcome"] in ("ABORTED_NO_FRAMES", "ABORTED_TIMEOUT"):
                    self._record("aborted", reason=window["outcome"])
                    return {
                        "terminal": window["outcome"],
                        "views": windows,
                        "log": self.log,
                        "commands_issued": self.bridge.commands_issued,
                    }
                if window["outcome"] == "DWELL_COMPLETE":
                    windows.append(window)
        self.bridge.send_hold()
        terminal = (
            "DRIVE_COMPLETE_WITH_SKIPS" if skipped_positions else "DRIVE_COMPLETE"
        )
        self._record("finished", terminal=terminal, skipped_positions=skipped_positions)
        return {
            "terminal": terminal,
            "views": windows,
            "skipped_positions": skipped_positions,
            "log": self.log,
            "commands_issued": self.bridge.commands_issued,
        }


def write_drive_log(repo_root: Path, session: str, result: dict[str, Any]) -> Path:
    path = repo_root / state_root_for(session) / "drive_log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {"schema_version": DRIVE_LOG_SCHEMA, "session_id": session,
             "terminal": result["terminal"],
             # BC-SURVEY-2：本次运行实际发出的控制指令条数。
             "commands_issued": int(result["commands_issued"])},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        )
    ]
    lines.extend(
        json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for entry in result["log"]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def drive_session(repo_root: Path, session: str, bridge: RuntimeBridge) -> dict[str, Any]:
    marker = marker_path(repo_root)
    if not marker.is_file():
        raise SurveyError("没有活动巡览会话标记；先跑 `prepare`")
    active = json.loads(marker.read_text(encoding="utf-8"))
    if active.get("session_id") != session:
        raise SurveyError(
            f"活动会话是 {active.get('session_id')!r}，不是 {session!r}"
        )
    # BC-SURVEY-13：驱动读的必须是 `prepare` 钉住的那份 plan。不经 manifest
    # 直读 plan 文件，会让 prepare 与 drive 之间被改过的 plan 一路跑到 close
    # 才失败——那时一次正式 Play 已经从 ≤10 的信封里花掉了。
    plan = contract.load_pinned_survey_plan(
        repo_root,
        repo_root / state_root_for(session) / "manifest.json",
        session_id=session,
    )
    result = DriveSession(repo_root, session, plan, bridge).run()
    write_drive_log(repo_root, session, result)
    return result


# --- §2.1(e) 逐帧有效性 ----------------------------------------------------
def planned_view_counts(plan: dict[str, Any]) -> tuple[int, int]:
    """计划侧的 `(巡览视角数, 证人视角数)`——达成率的**分母**。

    §2.1(e) 写的是「达成巡览视角数 / **计划**巡览视角数」。用驱动器实际完成的
    停留窗当分母，会把被跳过的位置和未稳定的视角一并从分母里抹掉，从而把达成率
    抬高——恰好是 90% 门要拦的那种情况。
    """
    survey_views = witness_views = 0
    for position in plan.get("positions", []):
        for view in position.get("views", []):
            if view.get("kind") == "witness":
                witness_views += 1
            else:
                survey_views += 1
    return survey_views, witness_views


def classify_frames(
    windows: Sequence[dict[str, Any]],
    sidecars: dict[int, dict[str, Any]],
    legal_view_ids: frozenset[str],
    planned_counts: tuple[int, int],
) -> dict[str, Any]:
    """逐帧独立判定 + 逐视角达成 + 会话达成率（§2.1(e)）。

    `legal_view_ids` 是**必传**的：BC-SURVEY-13 要求任何进入 `selection.json`
    的标签都出自该会话 manifest 所钉的已复核 plan，把它做成可选参数就等于
    留了一条宽松回退。

    帧 f 为 `VALID_SURVEY` ⇔ f 属于某视角的停留窗 ∧ 位置距计划位置 ≤ 1.0 m
    ∧ `camera_forward_world` 与**计划视线**夹角 ≤ 3°。其余帧一律
    `PROTOCOL_INVALID`（起飞、转场、稳定等待、窗内不达标）。
    """
    for window in windows:
        if "view_id" not in window:
            raise SurveyError(f"停留窗缺 view_id 键：{window!r}")
        if window["view_id"] not in legal_view_ids:
            raise SurveyError(
                f"停留窗的 view_id {window['view_id']!r} 不在该会话已复核 plan "
                "的视角集合内"
            )
    view_of_frame: dict[int, dict[str, Any]] = {}
    for window in windows:
        first, last = window["frame_window"]
        if first is None or last is None:
            continue
        for frame_id in range(int(first), int(last) + 1):
            # 窗重叠不可能发生（视角串行执行），但若发生，先到者优先且记为
            # 确定性结果，不静默改判。
            view_of_frame.setdefault(frame_id, window)

    entries: list[dict[str, Any]] = []
    valid_by_view: dict[str, int] = {}
    for frame_id in sorted(sidecars):
        sidecar = sidecars[frame_id]
        window = view_of_frame.get(frame_id)
        if window is None:
            entries.append(
                {"frame_id": frame_id, "view_id": None,
                 "class": "PROTOCOL_INVALID", "reason": "OUTSIDE_ANY_DWELL_WINDOW"}
            )
            continue
        planned_position = window["position_world_m"]
        actual_position = [float(v) for v in sidecar["camera_position_world_m"]]
        offset = math.dist(tuple(actual_position), tuple(float(v) for v in planned_position))
        desired = [
            window["look_at_world_m"][i] - planned_position[i] for i in range(3)
        ]
        bearing = angle_between_deg(sidecar["camera_forward_world"], desired)
        if offset > contract.SURVEY_POSITION_TOLERANCE_M:
            reason = "POSITION_OFF_PLAN"
        elif bearing > contract.SURVEY_BEARING_TOLERANCE_DEG:
            reason = "BEARING_OFF_PLAN"
        else:
            reason = None
        if reason is None:
            valid_by_view[window["view_id"]] = valid_by_view.get(window["view_id"], 0) + 1
        entries.append(
            {
                "frame_id": frame_id,
                "view_id": window["view_id"],
                "class": "VALID_SURVEY" if reason is None else "PROTOCOL_INVALID",
                "reason": reason or "IN_WINDOW",
                "position_offset_m": offset,
                "bearing_error_deg": bearing,
            }
        )

    achieved_survey = 0
    achieved_witness = 0
    # 分母来自**计划**，不是实际完成的窗（关注项 1）。
    planned_survey, planned_witness = planned_counts
    executed_survey = executed_witness = 0
    per_view: list[dict[str, Any]] = []
    for window in windows:
        count = valid_by_view.get(window["view_id"], 0)
        achieved = count >= int(window["min_valid_frames"])
        per_view.append(
            {
                "view_id": window["view_id"],
                "kind": window["kind"],
                "valid_frames": count,
                "min_valid_frames": window["min_valid_frames"],
                "achieved": achieved,
            }
        )
        if window["kind"] == "witness":
            executed_witness += 1
            achieved_witness += int(achieved)
        elif window["kind"] == "survey":
            executed_survey += 1
            achieved_survey += int(achieved)
        else:
            # 未知 kind 落进巡览分母会直接改变 90% 达成率门。
            raise SurveyError(
                f"视角 kind 不在闭集 {{survey, witness}}：{window['kind']!r}"
                f"（view {window.get('view_id')!r}）"
            )
    rate = (achieved_survey / planned_survey) if planned_survey else 0.0
    return {
        "entries": entries,
        "per_view": per_view,
        "achieved_survey_views": achieved_survey,
        "planned_survey_views": planned_survey,
        "achieved_witness_views": achieved_witness,
        "planned_witness_views": planned_witness,
        # 执行数与计划数分开报告：两者不等即说明有位置/视角被跳过。
        "executed_survey_views": executed_survey,
        "executed_witness_views": executed_witness,
        "achievement_rate": rate,
    }


def apply_low_achievement_downgrade(
    classification: dict[str, Any]
) -> tuple[list[dict[str, Any]], bool]:
    """达成率 < 90% → 整会话全部帧 `PROTOCOL_INVALID`（§2.1(e)）。"""
    if classification["achievement_rate"] >= contract.SURVEY_MIN_ACHIEVEMENT_RATE:
        return classification["entries"], False
    return (
        [
            {**entry, "class": "PROTOCOL_INVALID", "reason": "SESSION_ACHIEVEMENT_BELOW_90"}
            for entry in classification["entries"]
        ],
        True,
    )


# --- §2.1(h) 归档成员与两阶段发布 -------------------------------------------
def _frame_members(repo_root: Path) -> list[tuple[Path, str]]:
    """`runtime/frames/` 下要归档的成员：`(源路径, 归档相对名)`。

    `latest.json` 也是成员：它是 `frames/*.json`，且 S1 断言
    `runtime/frames/` 必须为空——留下它既违反成员域，也让下一次 `prepare`
    与 S1 同时失败。
    """
    frames = frames_dir(repo_root)
    if not frames.is_dir():
        return []
    members: list[tuple[Path, str]] = []
    for path in sorted(frames.iterdir()):
        if path.is_file():
            members.append((path, f"frames/{path.name}"))
    return members


def _session_members(repo_root: Path, session: str) -> list[tuple[Path, str]]:
    members: list[tuple[Path, str]] = []
    state = repo_root / state_root_for(session)
    manifest = state / "manifest.json"
    if manifest.is_file():
        members.append((manifest, "session/manifest.json"))
    override = override_path(repo_root)
    if override.is_file():
        members.append((override, "session/scenario_config.json"))
    audit = runtime_dir(repo_root) / "road_scene_audit.json"
    if audit.is_file():
        members.append((audit, "session/road_scene_audit.json"))
    metrics = runtime_dir(repo_root) / "metrics.json"
    if metrics.is_file():
        members.append((metrics, "metrics.json"))
    drive_log = state / "drive_log.jsonl"
    if drive_log.is_file():
        members.append((drive_log, "drive_log.jsonl"))
    return members


def _copy_verified(source: Path, destination: Path) -> str:
    """复制后**重读比对 SHA**；不符即硬错误（§2.1(h) 第 2 步）。"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    expected = sha256_file(source)
    actual = sha256_file(destination)
    if expected != actual:
        raise SurveyError(
            f"归档复制后字节不符：{source} → {destination}（{expected} vs {actual}）"
        )
    return actual


def publish_archive(
    repo_root: Path, session: str, staged_members: Sequence[tuple[Path, str]]
) -> Path:
    """staging → 逐文件复核 → 整体原子 rename（§2.1(h) 第 2/3 步）。"""
    archive_root = repo_root / archive_root_for(session)
    staging = archive_root.parent / f".staging-{session}"
    if archive_root.exists():
        return archive_root
    staging.parent.mkdir(parents=True, exist_ok=True)
    if not staging.exists():
        staging.mkdir(parents=True)
    for source, relative in staged_members:
        target = staging / relative
        if target.is_file() and sha256_file(target) == sha256_file(source):
            continue  # 重入：已核验的成员不重复复制
        _copy_verified(source, target)
    members = contract.survey_tree_members(staging)
    _create_once_json(
        staging / "tree.json",
        {
            "schema_version": contract.SURVEY_TREE_SCHEMA,
            "work_id": WORK_ID,
            "session_id": session,
            "members": members,
            "tree_sha256": contract.survey_tree_sha256(members),
        },
        f"{session} tree.json",
    )
    os.replace(staging, archive_root)
    return archive_root


def _read_sidecars(repo_root: Path) -> dict[int, dict[str, Any]]:
    """`runtime/frames/` 内每张 jpg 的 sidecar，按 frame_id 索引。"""
    frames = frames_dir(repo_root)
    sidecars: dict[int, dict[str, Any]] = {}
    if not frames.is_dir():
        return sidecars
    for path in sorted(frames.glob("frame_*.jpg")):
        sidecar_path = path.with_suffix(".json")
        if not sidecar_path.is_file():
            raise SurveyError(f"帧缺 sidecar：{path}")
        frame_id = int(path.stem.rsplit("_", 1)[-1])
        sidecars[frame_id] = json.loads(sidecar_path.read_text(encoding="utf-8"))
    return sidecars


def _drive_log(repo_root: Path, session: str) -> dict[str, Any]:
    """读回整份 drive log：终态、视角窗与**全部**事件。

    BC-SURVEY-2 要求零帧 `close` 能证明日志「仅含」pre-command 事件，所以这里
    不能像早前那样只留 `view_window` 而把其余事件丢掉——被丢掉的恰恰是判断
    「有没有发过控制指令」的唯一依据。
    """
    path = repo_root / state_root_for(session) / "drive_log.jsonl"
    if not path.is_file():
        return {"present": False, "terminal": None, "windows": [], "events": []}
    windows: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    terminal: str | None = None
    commands_issued: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("schema_version") == DRIVE_LOG_SCHEMA:
            terminal = entry.get("terminal")
            commands_issued = entry.get("commands_issued")
            continue
        events.append(entry)
        if entry.get("event") == "view_window":
            windows.append(entry)
    return {
        "present": True,
        "terminal": terminal,
        "windows": windows,
        "events": events,
        "commands_issued": commands_issued,
    }


def drive_log_is_pre_command_only(log: dict[str, Any]) -> bool:
    """日志是否证明**一条控制指令都没发过**（BC-SURVEY-2）。

    缺席的日志算合格：bootstrap 抛错时驱动器根本没跑起来。存在时读日志头
    自己记录的 `commands_issued`——这是运行时数出来的**事实**，比按事件名
    反推「哪些事件算 pre-command」强：后者要维护一份事件白名单，而白名单
    本身又是会影响正式结果的常量。缺该键即拒绝（老形状的日志不得蒙混）。
    """
    if not log["present"]:
        return True
    count = log.get("commands_issued")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return False
    return count == 0


def _release_runtime(repo_root: Path, archive_root: Path, tree: dict[str, Any]) -> list[str]:
    """§2.1(h) 第 5 步：只删**已核验**成员，卸载 override，清活动标记。"""
    by_relative = {member["path"]: member["sha256"] for member in tree["members"]}
    removed: list[str] = []
    residue: list[str] = []
    frames = frames_dir(repo_root)
    if frames.is_dir():
        for path in sorted(frames.iterdir()):
            if not path.is_file():
                continue
            relative = f"frames/{path.name}"
            digest = by_relative.get(relative)
            if digest is not None and digest == sha256_file(path):
                path.unlink()
                removed.append(relative)
            else:
                residue.append(relative)
    for extra in ("metrics.json", "road_scene_audit.json"):
        path = runtime_dir(repo_root) / extra
        relative = "metrics.json" if extra == "metrics.json" else "session/road_scene_audit.json"
        digest = by_relative.get(relative)
        if path.is_file() and digest is not None and digest == sha256_file(path):
            path.unlink()
            removed.append(relative)
    override = override_path(repo_root)
    if override.is_file():
        override.unlink()
    marker = marker_path(repo_root)
    if marker.is_file():
        marker.unlink()
    if residue:
        hold = runtime_dir(repo_root) / f"frames.{archive_root.name}-foreign-residue-hold"
        hold.mkdir(parents=True, exist_ok=True)
        for relative in residue:
            source = frames / Path(relative).name
            target = hold / Path(relative).name
            if target.exists():
                raise SurveyError(f"foreign 残留 hold 已有同名成员：{target}")
            shutil.move(str(source), str(target))
    return removed


def assert_archived_pinned_plan(
    repo_root: Path, archive_root: Path, session: str
) -> dict[str, Any]:
    """BC-SURVEY-14：释放现场 / 补写 completion 前的**完整** pinned-plan 核对。

    只核对采集协议钉子是不够的：`load_pinned_survey_plan` 同时核对 plan 路径、
    plan 字节 SHA、manifest 与 plan **两侧**的采集协议钉子，并把它们一起对到
    当前投影上。plan 缺失或任一侧漂移都在这里失败——而不是等到释放完现场、
    写完 create-once completion 之后。
    """
    manifest_path = Path(archive_root) / "session" / "manifest.json"
    if not manifest_path.is_file():
        raise SurveyError(
            f"归档缺 manifest，无法核对所钉 plan：{manifest_path}"
        )
    try:
        return contract.load_pinned_survey_plan(
            repo_root, manifest_path, session_id=session
        )
    except contract.SurveyContractError as exc:
        raise SurveyError(f"{session} 的归档所钉 plan 核对失败：{exc}") from exc


def close_session(repo_root: Path, session: str, pixels: Any | None = None) -> dict[str, Any]:
    """§2.1(h) 两阶段发布 + 三种重入 + 零帧路径。"""
    repo_root = Path(repo_root)
    identity = contract.survey_plan_identity(session)
    state = repo_root / state_root_for(session)
    archive_root = repo_root / archive_root_for(session)
    completion_path = state / "completion.json"
    staging = archive_root.parent / f".staging-{session}"

    # 重入 3：completion 已写，但源未删净。
    if completion_path.is_file() and archive_root.is_dir():
        assert_archived_pinned_plan(repo_root, archive_root, session)
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        tree = json.loads((archive_root / "tree.json").read_text(encoding="utf-8"))
        recomputed = contract.survey_tree_sha256(contract.survey_tree_members(archive_root))
        if recomputed != completion.get("tree_sha256"):
            return _tree_mismatch(session, completion.get("tree_sha256"), recomputed)
        removed = _release_runtime(repo_root, archive_root, tree)
        return {
            "terminal": "CLOSE_RESIDUE_RECOVERED" if removed else completion["terminal"],
            "session_id": session,
            "tree_sha256": recomputed,
            "released": removed,
            "reentry": "completion_present",
        }

    # 重入 2：最终目录存在而 completion 缺失。
    if archive_root.is_dir() and not completion_path.is_file():
        assert_archived_pinned_plan(repo_root, archive_root, session)
        members = contract.survey_tree_members(archive_root)
        recomputed = contract.survey_tree_sha256(members)
        declared = json.loads((archive_root / "tree.json").read_text(encoding="utf-8"))
        if declared.get("tree_sha256") != recomputed:
            return _tree_mismatch(session, declared.get("tree_sha256"), recomputed)
        selection_path = archive_root / "selection.json"
        if selection_path.is_file():
            selection = json.loads(selection_path.read_text(encoding="utf-8"))
            # 缺 `session_terminal` 不是「成功」：它会被写进 create-once 的
            # completion，之后再也改不了。缺键/越闭集一律拒绝。
            if "session_terminal" not in selection:
                raise SurveyError(
                    f"归档 selection.json 缺 session_terminal：{selection_path}；"
                    "不得以 CLOSED_OK 补默认值"
                )
            terminal = selection["session_terminal"]
        elif not any(member["path"].endswith(".jpg") for member in members):
            terminal = "CLOSED_ZERO_FRAMES"
        else:
            raise SurveyError(
                f"归档有帧却无 selection.json：{archive_root}；无法重建终态"
            )
        if terminal not in contract.SURVEY_CLOSE_TERMINALS:
            raise SurveyError(
                f"终态不在闭集 {contract.SURVEY_CLOSE_TERMINALS}：{terminal!r}"
            )
        _create_once_json(
            completion_path,
            _completion_document(session, terminal, recomputed, members, None),
            f"{session} completion.json",
        )
        removed = _release_runtime(repo_root, archive_root, declared)
        return {
            "terminal": terminal,
            "session_id": session,
            "tree_sha256": recomputed,
            "released": removed,
            "reentry": "completion_missing",
        }

    log = _drive_log(repo_root, session)
    windows, drive_terminal = log["windows"], log["terminal"]
    sidecars = _read_sidecars(repo_root)
    # BC-SURVEY-13：新鲜归档路径上，先把该会话 manifest 所钉的已复核 plan 取到
    # 手，selection 的每一个标签都必须出自它。重入分支不走这里——那两条是在
    # 重新发布一份已经关闭的归档，加钉子只会把 CLOSE_RESIDUE_RECOVERED 变成
    # 硬失败并把归档搁浅。
    plan = contract.load_pinned_survey_plan(
        repo_root, state / "manifest.json", session_id=session
    )
    survey_ids, witness_ids = contract.survey_plan_view_ids(plan)
    legal_view_ids = survey_ids | witness_ids

    # 零帧路径（§2.1(h)）：`runtime/frames/` 为空，且 drive log 缺席或只含
    # **发任何控制指令前**的拒绝/无帧终态。
    if not sidecars:
        # BC-SURVEY-2：终态在接受集内**还不够**，必须证明日志「仅含」
        # pre-command 事件——终态只是首行，其后的事件才说明控制指令是否发过。
        allowed = drive_terminal in (None, "DRIVE_REFUSED_AUDIT", "ABORTED_NO_FRAMES")
        if not allowed:
            raise SurveyError(
                f"零帧却带终态 {drive_terminal!r}：不属零帧 `close` 的接受集，"
                "现场需人工对账"
            )
        if not drive_log_is_pre_command_only(log):
            raise SurveyError(
                f"零帧却已发出控制指令（日志头 commands_issued = "
                f"{log.get('commands_issued')!r}）：BC-SURVEY-2 的零帧路径只接受无"
                "日志或证明一条控制指令都没发过的日志，现场需人工对账"
            )
        staged = _session_members(repo_root, session)
        publish_archive(repo_root, session, staged)
        members = contract.survey_tree_members(archive_root)
        recomputed = contract.survey_tree_sha256(members)
        _create_once_json(
            completion_path,
            _completion_document(session, "CLOSED_ZERO_FRAMES", recomputed, members, None),
            f"{session} completion.json",
        )
        tree = json.loads((archive_root / "tree.json").read_text(encoding="utf-8"))
        _release_runtime(repo_root, archive_root, tree)
        return {
            "terminal": "CLOSED_ZERO_FRAMES",
            "session_id": session,
            "tree_sha256": recomputed,
            "frame_count": 0,
        }

    classification = classify_frames(
        windows, sidecars, legal_view_ids, planned_view_counts(plan)
    )
    entries, downgraded = apply_low_achievement_downgrade(classification)
    terminal = "CLOSED_PROTOCOL_INVALID" if downgraded else "CLOSED_OK"

    scenario = json.loads(
        (repo_root / scenario_path_for(identity)).read_text(encoding="utf-8")
    )
    route = scenario["target"]["route_world_m"]
    parked = (float(route[0]["x"]), float(route[0]["y"]), float(route[0]["z"]))
    valid_ids = {
        entry["frame_id"] for entry in entries if entry["class"] == "VALID_SURVEY"
    }
    witness_frames = [
        {
            "frame_id": (
                frames_dir(repo_root).relative_to(repo_root) / f"frame_{entry['frame_id']:010d}.jpg"
            ).as_posix(),
            "sidecar": sidecars[entry["frame_id"]],
        }
        for entry in entries
        if entry["frame_id"] in valid_ids and entry["view_id"] in witness_ids
    ]
    if pixels is None:
        from tools.dist_data import pixel_source  # noqa: PLC0415

        pixels = pixel_source.ArchivePixelSource(repo_root)
    # §2.1(f)：`close` 的结论是**临时**的，S2 用同一函数重算为权威。
    witness = bind_layout.evaluate_parked_witness(witness_frames, parked, pixels)

    selection_document = {
        "schema_version": contract.SURVEY_SELECTION_SCHEMA,
        "work_id": WORK_ID,
        "session_id": session,
        "session_terminal": terminal,
        "achievement_rate": classification["achievement_rate"],
        "achieved_survey_views": classification["achieved_survey_views"],
        "planned_survey_views": classification["planned_survey_views"],
        "achieved_witness_views": classification["achieved_witness_views"],
        "planned_witness_views": classification["planned_witness_views"],
        "per_view": classification["per_view"],
        "entries": [
            {
                "frame_id": entry["frame_id"],
                "view_id": entry["view_id"],
                "class": entry["class"],
                "reason": entry["reason"],
            }
            for entry in entries
        ],
    }
    # 发布前最后一道：写进 create-once selection 的每一行标签都必须合法。
    for entry in selection_document["entries"]:
        try:
            contract.validate_selection_view_id(
                entry["view_id"], entry["class"], legal_view_ids
            )
        except contract.SurveyContractError as exc:
            raise SurveyError(f"selection 行 view_id 非法，拒绝发布：{exc}") from exc
    selection_path = state / "selection.json"
    _create_once_json(selection_path, selection_document, f"{session} selection.json")

    staged = _frame_members(repo_root) + _session_members(repo_root, session)
    staged.append((selection_path, "selection.json"))
    publish_archive(repo_root, session, staged)
    members = contract.survey_tree_members(archive_root)
    recomputed = contract.survey_tree_sha256(members)
    declared = json.loads((archive_root / "tree.json").read_text(encoding="utf-8"))
    if declared.get("tree_sha256") != recomputed:
        return _tree_mismatch(session, declared.get("tree_sha256"), recomputed)
    _create_once_json(
        completion_path,
        _completion_document(session, terminal, recomputed, members, witness),
        f"{session} completion.json",
    )
    _release_runtime(repo_root, archive_root, declared)
    return {
        "terminal": terminal,
        "session_id": session,
        "tree_sha256": recomputed,
        "frame_count": sum(1 for member in members if member["path"].endswith(".jpg")),
        "achievement_rate": classification["achievement_rate"],
        "witness": witness,
        "staging_left": staging.exists(),
    }


def _completion_document(
    session: str,
    terminal: str,
    tree_sha256: str,
    members: Sequence[dict[str, Any]],
    witness: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema_version": contract.SURVEY_COMPLETION_SCHEMA,
        "work_id": WORK_ID,
        "session_id": session,
        "terminal": terminal,
        "tree_sha256": tree_sha256,
        "member_count": len(members),
        "frame_count": sum(1 for member in members if member["path"].endswith(".jpg")),
        # §2.1(f)：临时结论，S2 重算为权威，两者不等即硬错误。
        "tentative_witness": witness,
    }


def _tree_mismatch(session: str, declared: str | None, recomputed: str) -> dict[str, Any]:
    """`CLOSE_TREE_MISMATCH`：归档保留、不删任何文件、标记保留待人工对账。"""
    return {
        "terminal": "CLOSE_TREE_MISMATCH",
        "session_id": session,
        "declared_tree_sha256": declared,
        "recomputed_tree_sha256": recomputed,
        "released": [],
        "note": (
            "唯一不自动解锁的终态：归档原样保留，`runtime/` 一个文件也不删，"
            "活动标记保留，需用户知情后人工对账"
        ),
    }


# --- verify ----------------------------------------------------------------
def verify_session(repo_root: Path, session: str) -> dict[str, Any]:
    """只读重算归档树 SHA、selection 一致性与清单闭集；任何不一致即失败。"""
    repo_root = Path(repo_root)
    archive_root = repo_root / archive_root_for(session)
    if not archive_root.is_dir():
        raise SurveyError(f"归档不存在：{archive_root}")
    # BC-SURVEY-14：**不论**有无帧/selection，先完成同一 pinned-plan 核对。
    # 挂在 `selection.json` 存在与否上，零帧归档就整条跳过了。
    plan = assert_archived_pinned_plan(repo_root, archive_root, session)
    survey_ids, witness_ids = contract.survey_plan_view_ids(plan)
    legal_ids = survey_ids | witness_ids

    members = contract.survey_tree_members(archive_root)
    recomputed = contract.survey_tree_sha256(members)
    declared = json.loads((archive_root / "tree.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    if declared.get("tree_sha256") != recomputed:
        problems.append(
            f"tree.json 声明 {declared.get('tree_sha256')}，重算 {recomputed}"
        )
    declared_members = {
        member["path"]: member["sha256"] for member in declared.get("members", [])
    }
    actual_members = {member["path"]: member["sha256"] for member in members}
    if declared_members != actual_members:
        missing = sorted(set(declared_members) - set(actual_members))
        extra = sorted(set(actual_members) - set(declared_members))
        changed = sorted(
            path
            for path in set(declared_members) & set(actual_members)
            if declared_members[path] != actual_members[path]
        )
        problems.append(
            f"成员集合不符：缺 {missing[:5]}、多 {extra[:5]}、字节变 {changed[:5]}"
        )

    completion_path = repo_root / state_root_for(session) / "completion.json"
    if not completion_path.is_file():
        problems.append(f"缺 completion：{completion_path}")
    else:
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        if completion.get("tree_sha256") != recomputed:
            problems.append("completion 记录的树摘要与归档不符")
        if completion.get("terminal") not in contract.SURVEY_CLOSE_TERMINALS:
            problems.append(f"终态不在闭集：{completion.get('terminal')!r}")

    archived_ids = {
        int(Path(member["path"]).stem.rsplit("_", 1)[-1])
        for member in members
        if member["path"].startswith("frames/") and member["path"].endswith(".jpg")
    }
    selection_path = archive_root / "selection.json"
    if archived_ids and not selection_path.is_file():
        problems.append("有归档帧却无 selection.json")
    elif selection_path.is_file():
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        if selection.get("schema_version") != contract.SURVEY_SELECTION_SCHEMA:
            problems.append("selection.json schema 不符")
        declared_ids = [int(entry["frame_id"]) for entry in selection.get("entries", [])]
        if len(declared_ids) != len(set(declared_ids)):
            problems.append("selection 内 frame_id 重复")
        if set(declared_ids) != archived_ids:
            problems.append(
                f"selection 与归档 jpg 不一一对应："
                f"清单多 {sorted(set(declared_ids) - archived_ids)[:5]}、"
                f"归档多 {sorted(archived_ids - set(declared_ids))[:5]}"
            )
        outside = sorted(
            {
                str(entry.get("class"))
                for entry in selection.get("entries", [])
                if entry.get("class") not in contract.SURVEY_FRAME_CLASSES
            }
        )
        if outside:
            problems.append(f"selection 的类不在闭集：{outside}")
        # BC-SURVEY-13：`verify` 是工具自己的读回，必须把 view_id 也验了。
        # 所钉 plan 已在函数开头无条件核对过，这里只用它的合法集合。
        try:
            for entry in selection.get("entries", []):
                if "view_id" not in entry:
                    problems.append(f"selection 行缺 view_id 键：{entry!r}")
                    continue
                contract.validate_selection_view_id(
                    entry["view_id"], entry.get("class"), legal_ids
                )
        except contract.SurveyContractError as exc:
            problems.append(f"view_id 校验失败：{exc}")
    if problems:
        raise SurveyError(
            f"`verify --session {session}` 不一致（{len(problems)} 项）：\n  "
            + "\n  ".join(problems)
        )
    return {
        "session_id": session,
        "tree_sha256": recomputed,
        "member_count": len(members),
        "frame_count": len(archived_ids),
        "verified": True,
    }


# --- diagnostic（COORD-005；BC-SURVEY-3：零新 ID） --------------------------
def diagnostic_hold_path(repo_root: Path, index: int) -> Path:
    return runtime_dir(repo_root) / f"frames.p1-vlm-survey-diagnostic-{index}-hold"


def next_diagnostic_index(repo_root: Path) -> int:
    index = 1
    while diagnostic_hold_path(repo_root, index).exists():
        index += 1
    return index


def install_diagnostic(repo_root: Path, anchor: int) -> dict[str, Any]:
    """§2.3 步 2：只在 `runtime/` 生存的临时配置；**沿用 default 的
    `scenario_id`**，不建正式 plan/config、不建 session/run ID、不写标记。

    诊断序号只命名 hold，不是任何 ID（BC-SURVEY-3）。
    """
    repo_root = Path(repo_root)
    assert_runtime_quiescent(repo_root)
    used = next_diagnostic_index(repo_root) - 1
    if used >= MAX_DIAGNOSTIC_PLAY:
        raise SurveyError(
            f"诊断 Play 信封用尽：已用 {used} / 上限 {MAX_DIAGNOSTIC_PLAY}"
        )
    # BC-SURVEY-9/16：锚点在冻结表内**不**豁免 §2.1(c)–(f) 的硬门；诊断配置同样
    # 由首个合法候选派生，穷举后仍无合法 plan 就没有可诊断的几何。
    resolved = resolve_anchor_plan(repo_root, anchor, 1)
    if not resolved["reachable"]:
        raise SurveyError(
            f"锚点 {anchor} 记 {resolved['terminal']}：穷举了全部 "
            f"{resolved['candidates_enumerated']} 个停放候选，无一产出合法 plan；"
            "诊断不得绕过计划有效性门"
        )
    plan = resolved["plan"]
    document = build_scenario_config(repo_root, plan)
    default = load_default_scenario(repo_root)
    # BC-SURVEY-3：逐字沿用 default 的既有 scenario id，不创建新 scenario ID。
    document["scenario_id"] = default["scenario_id"]
    override_path(repo_root).parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(override_path(repo_root), document)
    return {
        "mode": "diagnostic",
        "anchor_index": anchor,
        "candidate_index": resolved["candidate_index"],
        "scenario_id": document["scenario_id"],
        "next_hold_index": used + 1,
        "override_path": str(override_path(repo_root)),
        "creates_ids": False,
    }


def collect_diagnostic(repo_root: Path) -> dict[str, Any]:
    """退出 Play 后：`runtime/frames/` **整体**移入 create-once 诊断 hold，
    卸载 override 恢复现场。产物是 `DIAGNOSTIC_HOLD`，不进证据链。"""
    repo_root = Path(repo_root)
    index = next_diagnostic_index(repo_root)
    hold = diagnostic_hold_path(repo_root, index)
    if hold.exists():
        raise SurveyError(f"诊断 hold 已存在（create-once）：{hold}")
    frames = frames_dir(repo_root)
    entries = sorted(frames.iterdir()) if frames.is_dir() else []
    if not any(path.is_file() for path in entries):
        raise SurveyError(
            f"`runtime/frames/` 无可收集的诊断帧；拒绝创建空 hold {hold.name}"
            "（空收集会白占一个诊断序号）"
        )
    hold.mkdir(parents=True)
    moved: list[str] = []
    for path in entries:
        if not path.is_file():
            continue
        shutil.move(str(path), str(hold / path.name))
        moved.append(path.name)
    override = override_path(repo_root)
    if override.is_file():
        override.unlink()
    return {
        "mode": "diagnostic-collect",
        "hold": str(hold.relative_to(repo_root)),
        "hold_index": index,
        "moved": len(moved),
        "jpg_count": sum(1 for name in moved if name.endswith(".jpg")),
        "override_unloaded": True,
    }


# --- BC-SURVEY-16：按冻结次序穷举候选，取首个过硬门者 ----------------------
ANCHOR_UNREACHABLE = "PLAN_POSITION_UNREACHABLE"


def resolve_anchor_plan(
    repo_root: Path, anchor: int, plan_version: int = 1
) -> dict[str, Any]:
    """对一个锚点的**全部**停放候选依冻结次序只读求 plan，取首个合法者。

    BC-SURVEY-16：无合法候选或全部 plan 无效即记该锚点
    `PLAN_POSITION_UNREACHABLE`——**不创建** plan/scenario/session ID，也不
    消耗 Play。本函数一个字节也不写。
    """
    scenario_default = load_default_scenario(repo_root)
    anchor_x, anchor_z = ANCHOR_INDEX[anchor]
    candidates = parked_candidates(
        repo_root, (anchor_x, ANCHOR_Y_M, anchor_z), scenario_default
    )
    rejected: list[dict[str, Any]] = []
    for item in candidates:
        index = item["candidate_index"]
        plan = build_plan(
            repo_root, anchor, plan_version, index, candidates=candidates
        )
        if plan["valid"]:
            return {
                "anchor_index": anchor,
                "reachable": True,
                "candidate_index": index,
                "candidates_enumerated": len(candidates),
                "candidates_rejected": rejected,
                "plan": plan,
                "terminal": None,
            }
        rejected.append(
            {
                "candidate_index": index,
                "survey_position_count": plan["survey_position_count"],
                "witness_view_count": plan["witness_view_count"],
                "predicted_witness_frames": plan["predicted_witness_frames"],
            }
        )
    return {
        "anchor_index": anchor,
        "reachable": False,
        "candidate_index": None,
        "candidates_enumerated": len(candidates),
        "candidates_rejected": rejected,
        "plan": None,
        "terminal": ANCHOR_UNREACHABLE,
    }


def resolve_anchor_sequence(
    repo_root: Path, plan_version: int = 1
) -> dict[str, Any]:
    """按冻结锚点顺序求整条可达序列（只读诊断；不创建任何身份）。

    BC-SURVEY-16：备 9/10 只在前八项分别 `close` 或到达不可达终态后才依序
    启用；本函数只报告序列，启用与否由 `prepare` 的信封与会话状态决定。
    """
    reachable: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for index, _x, _z in ANCHOR_TABLE:
        result = resolve_anchor_plan(repo_root, index, plan_version)
        row = {
            "anchor_index": index,
            "candidates_enumerated": result["candidates_enumerated"],
            "candidate_index": result["candidate_index"],
            "terminal": result["terminal"],
        }
        (reachable if result["reachable"] else dropped).append(row)
    return {
        "reachable": reachable,
        "dropped": dropped,
        "reachable_sequence": [row["anchor_index"] for row in reachable],
    }


# --- plan 的落盘（create-once + 字节幂等） ----------------------------------
def write_plan(
    repo_root: Path,
    anchor: int,
    plan_version: int = 1,
    candidate: int | None = None,
) -> dict[str, Any]:
    """生成并落盘计划身份的 `plan.json` 与专用场景配置。

    §2.3 步 3 与 BC-SURVEY-5：正式 plan/config **只有在 COORD-005 保真通过后**
    才允许创建，且必须随首个稳定候选进入独立复核。信封上限 10 个计划身份。

    BC-SURVEY-16：`candidate` 省略时按冻结次序穷举该锚点的**全部**候选，只给
    首个过 §2.1(c)–(f) 硬门者建身份；全部无效即 `PLAN_POSITION_UNREACHABLE`，
    不创建任何 ID。显式传 `candidate` 供 §2.4 的 pilot p2 / 候选切换使用，
    该候选自身仍须过门。
    """
    if candidate is None:
        resolved = resolve_anchor_plan(repo_root, anchor, plan_version)
        if not resolved["reachable"]:
            raise SurveyError(
                f"锚点 {anchor} 记 {resolved['terminal']}：穷举了全部 "
                f"{resolved['candidates_enumerated']} 个停放候选，无一产出合法 "
                "plan；不创建 plan/scenario/session ID，也不消耗 Play"
            )
        plan = resolved["plan"]
        candidate = resolved["candidate_index"]
    else:
        plan = build_plan(repo_root, anchor, plan_version, candidate)
        if not plan["valid"]:
            raise SurveyError(
                f"计划无效：保留巡览位置 {plan['survey_position_count']}（需 ≥ "
                f"{contract.SURVEY_MIN_KEPT_SURVEY_POSITIONS}）、证人视角 "
                f"{plan['witness_view_count']}（需 ≥ {contract.SURVEY_MIN_WITNESS_VIEWS}）、"
                f"预测证人帧 {plan['predicted_witness_frames']}（需 ≥ "
                f"{contract.SURVEY_WITNESS_PREDICT_MIN_FRAMES}）；换下一候选"
            )
    identity = plan["plan_identity"]
    existing = existing_plan_identities(repo_root)
    if identity not in existing and len(existing) >= MAX_PLAN_IDENTITIES:
        raise SurveyError(
            f"计划身份信封用尽：已有 {len(existing)} / 上限 {MAX_PLAN_IDENTITIES}"
        )
    document = build_scenario_config(repo_root, plan)
    default = load_default_scenario(repo_root)
    differences = scenario_diff_fields(default, document)
    allowed = {
        "scenario_id",
        "anchor_world_m.x",
        "anchor_world_m.y",
        "anchor_world_m.z",
        "target.speed_mps",
        "sensor.retained_frame_count",
    }
    unexpected = [
        path
        for path in differences
        if path not in allowed and not path.startswith("target.route_world_m")
    ]
    if unexpected:
        raise SurveyError(
            f"专用配置改动越出 §2.1(b) 的五个字段：{unexpected}"
        )
    _create_once_json(
        repo_root / scenario_path_for(identity), document, f"{identity} scenario config"
    )
    _create_once_json(repo_root / plan_path_for(identity), plan, f"{identity} plan.json")
    return {
        "plan_identity": identity,
        "scenario_path": scenario_path_for(identity),
        "plan_path": plan_path_for(identity),
        "survey_positions": plan["survey_position_count"],
        "survey_views": plan["survey_view_count"],
        "witness_views": plan["witness_view_count"],
        "candidate_index": candidate,
        "dropped_positions": len(plan["dropped_positions"]),
        "changed_scenario_fields": sorted(differences),
    }


# --- CLI -------------------------------------------------------------------
def _emit(document: Any) -> None:
    print(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="P1-VLM-DATA-002 巡览采集驱动器（阶段 A）"
    )
    parser.add_argument("--repo-root", default=".", help="仓库根（默认当前目录）")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_parser = sub.add_parser("plan", help="生成计划身份的场景配置与 plan.json")
    plan_parser.add_argument("--anchor", type=int, required=True)
    plan_parser.add_argument("--plan-version", type=int, default=1)
    plan_parser.add_argument(
        "--candidate",
        type=int,
        default=None,
        help="省略即按 BC-SURVEY-16 穷举取首个合法候选",
    )
    plan_parser.add_argument(
        "--dry-run", action="store_true", help="只算不写（不创建任何身份）"
    )

    prepare_parser = sub.add_parser("prepare", help="安装场景、写 manifest 与活动标记")
    prepare_parser.add_argument("--session", required=True)

    drive_parser = sub.add_parser("drive", help="执行巡览（对应一次 Play）")
    drive_parser.add_argument("--session", required=True)

    close_parser = sub.add_parser("close", help="逐帧判定、无损归档与解锁")
    close_parser.add_argument("--session", required=True)

    verify_parser = sub.add_parser("verify", help="只读重算归档树与 selection 一致性")
    verify_parser.add_argument("--session", required=True)

    anchors_parser = sub.add_parser(
        "anchors", help="只读报告冻结锚点表的可达序列（不创建任何身份）"
    )
    anchors_parser.add_argument("--plan-version", type=int, default=1)

    diagnostic_parser = sub.add_parser(
        "diagnostic", help="COORD-005 诊断（零新 ID；沿用 default 的 scenario_id）"
    )
    diagnostic_parser.add_argument("--anchor", type=int)
    diagnostic_parser.add_argument(
        "--collect", action="store_true", help="退出 Play 后把帧移入诊断 hold"
    )

    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        if args.command == "anchors":
            _emit(resolve_anchor_sequence(repo_root, args.plan_version))
        elif args.command == "plan":
            if args.dry_run:
                if args.candidate is None:
                    resolved = resolve_anchor_plan(
                        repo_root, args.anchor, args.plan_version
                    )
                    if not resolved["reachable"]:
                        _emit(
                            {
                                key: value
                                for key, value in resolved.items()
                                if key != "plan"
                            }
                        )
                        return 0
                    document = resolved["plan"]
                else:
                    document = build_plan(
                        repo_root, args.anchor, args.plan_version, args.candidate
                    )
                _emit(
                    {
                        key: value
                        for key, value in document.items()
                        if key not in ("positions", "transitions", "dropped_positions")
                    }
                )
            else:
                _emit(write_plan(repo_root, args.anchor, args.plan_version, args.candidate))
        elif args.command == "prepare":
            _emit(prepare_session(repo_root, args.session))
        elif args.command == "drive":
            result = drive_session(repo_root, args.session, RuntimeBridge(repo_root))
            _emit({key: value for key, value in result.items() if key != "log"})
        elif args.command == "close":
            _emit(close_session(repo_root, args.session))
        elif args.command == "verify":
            _emit(verify_session(repo_root, args.session))
        elif args.command == "diagnostic":
            if args.collect:
                _emit(collect_diagnostic(repo_root))
            elif args.anchor is not None:
                _emit(install_diagnostic(repo_root, args.anchor))
            else:
                diagnostic_parser.error("需要 --anchor 或 --collect")
    except (SurveyError, contract.SurveyContractError) as exc:
        # `SurveyContractError` 是合同模块的域错误，与 `SurveyError` 无继承关系；
        # `drive`/`close` 经 `load_pinned_survey_plan` 会抛它，必须同样落在这里，
        # 不能从 CLI 裸抛出去。
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
