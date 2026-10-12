"""P1-VLM-DATA-002 巡览工具回归（提案 §5 第 1 条点名的全部拒绝路径）。

**夹具策略**：没有 Unity 的情况下，唯一诚实的做法是让「Unity 侧」只做
两件事，其余全部走生产路径：

1. 帧字节与 sidecar 模板取自**真实归档帧**（`runtime/frames.1b-diagnostic-hold`
   的第一帧及其 sidecar），仿真只替换位姿相关字段，用的是与工具
   `synthetic_camera` 同一套、已用归档字节核实过的基底约定；
2. 机身/云台按既有 `tethered-drone-control/v1` 包运动，指令由工具本身经
   `controller.body_entry` / `controller.gimbal_entry` 真实写盘。

计划、场景配置、manifest、selection、tree、completion 与归档一律由
`tools/run_grounding_survey.py` 自己产出——不手写任何一份 JSON。

时间用虚拟时钟：工具的每次 `sleep` 推进仿真一个采样周期，所以整批用例
不依赖真实等待，也不改变工具里的任何时限常量。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools import run_grounding_survey as survey  # noqa: E402
from tools.dist_data import contract  # noqa: E402

# 模板帧取**已纳入版本控制**的归档副本，不是 `runtime/` 下的 hold：
# `runtime/` 是 gitignored 的，用它会让整份用例在复核角色的新鲜 worktree 里
# 全部 skip，而 runner 仍报 OK——一份什么都没执行的绿色套件。
# `docs/evidence/P1-M3-BODY-001-1b/frame_0000000012.jpg` 与
# `runtime/frames.1b-diagnostic-hold` 内的同名帧逐字节相同（附录 A.3 的
# `DOC_COPY` 行正是按内容哈希把它折叠进源 lineage 的）。
TEMPLATE_FRAME_DIR = "docs/evidence/P1-M3-BODY-001-1b"


def _template_frame() -> tuple[Path, Path]:
    """模板帧必须存在；缺失是硬失败，不是 skip。"""
    base = PROJECT_ROOT / TEMPLATE_FRAME_DIR
    for image in sorted(base.glob("frame_*.jpg")):
        sidecar = image.with_suffix(".json")
        if sidecar.is_file():
            return image, sidecar
    raise AssertionError(
        f"版本控制内的模板帧缺失：{base}/frame_*.jpg + 同名 sidecar；"
        "本套件不得在缺夹具时静默 skip"
    )


class VirtualClock:
    """推进虚拟时间并驱动仿真；工具的时限常量一字不改。"""

    def __init__(self, simulator: "FakeSimulator | None" = None) -> None:
        self.t = 0.0
        self.simulator = simulator

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += float(seconds)
        if self.simulator is not None:
            self.simulator.step(float(seconds))


class FakeSimulator:
    """最小 Unity 替身：消费控制包、按采样率发布帧、写路线合法性审计报告。"""

    def __init__(
        self,
        root: Path,
        scenario: dict,
        template: tuple[Path, Path],
        *,
        publish_audit: bool = True,
        audit_status: str = "CLEAR",
        audit_violations: int = 0,
        publish_frames: bool = True,
    ) -> None:
        self.root = Path(root)
        self.runtime = self.root / "runtime"
        self.frames = self.runtime / "frames"
        self.scenario = scenario
        self.image_bytes = template[0].read_bytes()
        self.sidecar_template = json.loads(template[1].read_text(encoding="utf-8"))
        anchor = scenario["anchor_world_m"]
        self.position = [
            float(anchor["x"]),
            float(anchor["y"]) + survey.BIRTH_HEIGHT_M,
            float(anchor["z"]),
        ]
        # 出生姿态不取正天底：真实相机在正天底时 `cross(worldUp, forward)`
        # 退化，Unity 侧靠 LookRotation 的 fallback 处理，仿真侧则直接给一个
        # 微小水平偏置。计划里没有任何正天底视角（巡览 20°/44°，证人看 P_k）。
        self.look_at = [
            float(anchor["x"]) + 1.0, float(anchor["y"]), float(anchor["z"])
        ]
        self.frame_id = 0
        self.time = 0.0
        self.accumulator = 0.0
        self.period = 1.0 / float(scenario["sensor"]["capture_hz"])
        self.publish_frames = publish_frames
        self.bearing_lag = 0
        self._pending_look_at: list[float] | None = None
        self.frames.mkdir(parents=True, exist_ok=True)
        if publish_audit:
            self._write_audit(scenario["scenario_id"], audit_status, audit_violations)

    def _write_audit(self, scenario_id: str, status: str, violations: int) -> None:
        survey._atomic_write_json(
            self.runtime / "road_scene_audit.json",
            {
                "schema_version": survey.ROAD_AUDIT_SCHEMA,
                "scenario_id": scenario_id,
                "status": status,
                "route_sample_count": 4,
                "road_violation_count": violations,
                "road_violations": [],
                "audited_obstacle_count": 0,
                "overhead_exemption_count": 0,
                "obstacle_violation_count": 0,
                "obstacle_violations": [],
            },
        )

    # --- 控制消费 -----------------------------------------------------------
    def _read_packet(self, name: str) -> dict | None:
        path = self.runtime / name
        if not path.is_file():
            return None
        try:
            packet = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if packet.get("protocol") != survey.CONTROL_PROTOCOL:
            raise AssertionError(f"非法控制协议：{packet.get('protocol')!r}")
        return packet

    def step(self, seconds: float) -> None:
        body = self._read_packet("body_command.json")
        if body is not None and body["command"]["mode"] == "velocity_world":
            velocity = body["command"]["velocity_world_mps"]
            for index, axis in enumerate(("x", "y", "z")):
                self.position[index] += float(velocity[axis]) * seconds
        gimbal = self._read_packet("gimbal_command.json")
        if gimbal is not None and gimbal["command"]["mode"] == "look_at_world":
            point = gimbal["command"]["target_world_m"]
            target = [float(point["x"]), float(point["y"]), float(point["z"])]
            if target != self.look_at:
                if self.bearing_lag:
                    self._pending_look_at = target
                    self._lag_left = self.bearing_lag
                else:
                    self.look_at = target
        self.time += seconds
        self.accumulator += seconds
        while self.accumulator >= self.period - 1e-9:
            self.accumulator -= self.period
            if self._pending_look_at is not None:
                self._lag_left -= 1
                if self._lag_left <= 0:
                    self.look_at = self._pending_look_at
                    self._pending_look_at = None
            if self.publish_frames:
                self.publish()

    # --- 帧发布 -------------------------------------------------------------
    def publish(self) -> int:
        forward = survey._normalize(
            [self.look_at[i] - self.position[i] for i in range(3)]
        )
        right = survey._normalize(survey._cross((0.0, 1.0, 0.0), forward))
        up = survey._normalize(survey._cross(forward, right))
        sidecar = dict(self.sidecar_template)
        sidecar["schema_version"] = survey.SENSOR_FRAME_SCHEMA
        sidecar["capture_monotonic_clock_id"] = "system-stopwatch/v1"
        sidecar["capture_monotonic_s"] = self.time
        sidecar["scenario_id"] = self.scenario["scenario_id"]
        sidecar["frame_id"] = self.frame_id
        sidecar["simulation_time_s"] = self.time
        sidecar["capture_unix_s"] = 1_800_000_000.0 + self.time
        sidecar["camera_position_world_m"] = list(self.position)
        sidecar["camera_forward_world"] = list(forward)
        sidecar["camera_right_world"] = list(right)
        sidecar["camera_up_world"] = list(up)
        stem = f"frame_{self.frame_id:010d}"
        (self.frames / f"{stem}.jpg").write_bytes(self.image_bytes)
        survey._atomic_write_json(self.frames / f"{stem}.json", sidecar)
        survey._atomic_write_json(
            self.frames / "latest.json",
            {
                "schema_version": survey.FRAME_MANIFEST_SCHEMA,
                "frame_id": self.frame_id,
                "image_file": f"{stem}.jpg",
                "metadata_file": f"{stem}.json",
            },
        )
        published = self.frame_id
        self.frame_id += 1
        return published


class SurveyCase(unittest.TestCase):
    """临时仓库根：只放巡览工具真正需要的仓库输入，其余由工具产出。"""

    REPO_INPUTS = (
        "config/scenario.default.json",
        "config/road_data.json",
        "docs/evidence/P1-M3-BODY-001-scene-geometry.json",
    )

    def setUp(self) -> None:
        self.template = _template_frame()
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        for relative in self.REPO_INPUTS:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT_ROOT / relative, destination)
        (self.root / "runtime" / "frames").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # --- 便捷装配 -----------------------------------------------------------
    def write_plan(self, anchor: int = 1, candidate: int = 1) -> dict:
        return survey.write_plan(self.root, anchor, 1, candidate)

    def load_plan(self, identity: str) -> dict:
        return json.loads(
            (self.root / survey.plan_path_for(identity)).read_text(encoding="utf-8")
        )

    def trim_plan(self, identity: str, positions: int = 2, views: int = 2) -> dict:
        """把**生产产出的** plan 裁到少数位置/视角，让虚拟时间内可跑完。

        只做子集选择，不改任何几何或阈值：被保留的位置、视角、转场航点全部
        是 `build_plan` 的原始输出字节。
        """
        plan = self.load_plan(identity)
        kept = plan["positions"][:positions]
        for position in kept:
            witness = [v for v in position["views"] if v["kind"] == "witness"]
            survey_views = [v for v in position["views"] if v["kind"] == "survey"]
            position["views"] = survey_views[:views] + witness
        plan["positions"] = kept
        keep_ids = {position["position_id"] for position in kept}
        plan["transitions"] = [
            item for item in plan["transitions"] if item["to_position_id"] in keep_ids
        ]
        (self.root / survey.plan_path_for(identity)).write_text(
            json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        return plan


class PlanGeometryTest(SurveyCase):
    """§2.1(c)(d)：净空、绕行、系留与端点极值的逐条拒绝路径。"""

    def setUp(self) -> None:
        super().setUp()
        self.boxes = survey.obstacle_boxes(self.root)
        self.anchor = (206.0, survey.ANCHOR_Y_M, 55.0)

    def test_ring_radius_matches_the_frozen_formula(self) -> None:
        self.assertAlmostEqual(survey.ring_radius(14.0), 22.412, places=3)
        self.assertAlmostEqual(survey.ring_radius(26.0), 15.242, places=3)

    def test_position_inside_an_expanded_box_is_raised_or_dropped(self) -> None:
        """位置落入 B' 必须被处置：不是抬高就是丢弃，绝不原样保留。"""
        box = self.boxes[0]
        centre = (
            (box["min_x_m"] + box["max_x_m"]) / 2.0,
            (box["min_z_m"] + box["max_z_m"]) / 2.0,
        )
        anchor = (centre[0], survey.ANCHOR_Y_M, centre[1])
        result = survey.resolve_position(anchor, 14.0, 0.0, 0.0, self.boxes)
        if result["kept"]:
            point = result["world_m"]
            self.assertEqual(contract.boxes_containing(tuple(point), self.boxes), [])
            self.assertGreater(result["height_m"], 14.0)  # 只能靠抬高脱离
        else:
            self.assertEqual(result["reason"], "PLAN_POSITION_DROPPED")

    def test_dropped_position_reports_every_attempted_height(self) -> None:
        tall = {
            "scene_object_name": "synthetic-tower",
            "min_x_m": self.anchor[0] - 50.0, "max_x_m": self.anchor[0] + 50.0,
            "min_y_m": 0.0, "max_y_m": 100.0,
            "min_z_m": self.anchor[2] - 50.0, "max_z_m": self.anchor[2] + 50.0,
        }
        result = survey.resolve_position(self.anchor, 14.0, 0.0, 0.0, [tall])
        self.assertFalse(result["kept"])
        self.assertEqual(result["reason"], "PLAN_POSITION_DROPPED")
        heights = [attempt["height_m"] for attempt in result["raise_attempts"]]
        self.assertEqual(heights[0], 14.0)
        self.assertEqual(heights[-1], 30.0)
        self.assertTrue(all(step == 2.0 for step in
                            (b - a for a, b in zip(heights, heights[1:]))))

    def test_raising_recomputes_the_ring_radius_each_step(self) -> None:
        """`r' = min(r, √(33² − H'²))` 每步重算；否则系留会被抬高破坏。"""
        blocker = {
            "scene_object_name": "synthetic-slab",
            "min_x_m": -1e6, "max_x_m": 1e6,
            "min_y_m": 0.0, "max_y_m": self.anchor[1] + 25.0,
            "min_z_m": -1e6, "max_z_m": 1e6,
        }
        result = survey.resolve_position(
            self.anchor, 14.0, 0.0, survey.ring_radius(14.0), [blocker]
        )
        self.assertTrue(result["kept"])
        self.assertLessEqual(
            math.hypot(result["radius_m"], result["height_m"]),
            contract.SURVEY_MAX_TETHER_RADIUS_M + 1e-9,
        )
        self.assertLess(result["radius_m"], survey.ring_radius(14.0))

    def test_kept_positions_satisfy_the_endpoint_extremum_assertions(self) -> None:
        plan = survey.build_plan(self.root, 1, 1, 1)
        for position in plan["positions"]:
            self.assertLessEqual(
                math.hypot(position["radius_m"], position["height_m"]),
                contract.SURVEY_MAX_TETHER_RADIUS_M + 1e-9,
            )
            self.assertGreaterEqual(position["height_m"], contract.SURVEY_MIN_HEIGHT_M)
            self.assertLessEqual(position["height_m"], contract.SURVEY_MAX_HEIGHT_M)
            self.assertEqual(
                contract.boxes_containing(tuple(position["world_m"]), self.boxes), []
            )

    def test_intersecting_segment_is_detoured_not_passed_through(self) -> None:
        wall = {
            "scene_object_name": "synthetic-wall",
            "min_x_m": self.anchor[0] + 4.0, "max_x_m": self.anchor[0] + 6.0,
            "min_y_m": 0.0, "max_y_m": self.anchor[1] + 12.0,
            "min_z_m": self.anchor[2] - 20.0, "max_z_m": self.anchor[2] + 20.0,
        }
        start = (self.anchor[0], self.anchor[1] + 10.0, self.anchor[2])
        end = (self.anchor[0] + 12.0, self.anchor[1] + 10.0, self.anchor[2])
        self.assertTrue(contract.segment_intersects_box(start, end, wall))
        result = survey.transition_waypoints(start, end, self.anchor, [wall])
        self.assertTrue(result["reachable"])
        self.assertEqual(result["mode"], "detour")
        # BC-SURVEY-1：安全世界高度 = 相交 B'.max_y **再加 1 m**，不是 +4。
        self.assertAlmostEqual(result["safe_world_y_m"], wall["max_y_m"] + 1.0)
        self.assertEqual(len(result["waypoints"]), 3)
        legs = [start] + [tuple(point) for point in result["waypoints"]]
        for leg_start, leg_end in zip(legs, legs[1:]):
            self.assertEqual(
                contract.segment_intersecting_boxes(leg_start, leg_end, [wall]), []
            )

    def test_h_safe_above_thirty_is_unreachable(self) -> None:
        tower = {
            "scene_object_name": "synthetic-tower",
            "min_x_m": self.anchor[0] + 4.0, "max_x_m": self.anchor[0] + 6.0,
            "min_y_m": 0.0, "max_y_m": self.anchor[1] + 30.0,
            "min_z_m": self.anchor[2] - 20.0, "max_z_m": self.anchor[2] + 20.0,
        }
        start = (self.anchor[0], self.anchor[1] + 10.0, self.anchor[2])
        end = (self.anchor[0] + 12.0, self.anchor[1] + 10.0, self.anchor[2])
        result = survey.transition_waypoints(start, end, self.anchor, [tower])
        self.assertFalse(result["reachable"])
        self.assertEqual(result["reason"], "PLAN_POSITION_UNREACHABLE")
        self.assertIn("H_safe", result["detail"])

    def test_detour_endpoint_beyond_the_tether_is_unreachable(self) -> None:
        wall = {
            "scene_object_name": "synthetic-wall",
            "min_x_m": self.anchor[0] + 20.0, "max_x_m": self.anchor[0] + 22.0,
            "min_y_m": 0.0, "max_y_m": self.anchor[1] + 24.0,
            "min_z_m": self.anchor[2] - 40.0, "max_z_m": self.anchor[2] + 40.0,
        }
        start = (self.anchor[0], self.anchor[1] + 10.0, self.anchor[2])
        end = (self.anchor[0] + 30.0, self.anchor[1] + 10.0, self.anchor[2])
        result = survey.transition_waypoints(start, end, self.anchor, [wall])
        self.assertFalse(result["reachable"])
        self.assertEqual(result["reason"], "PLAN_POSITION_UNREACHABLE")
        self.assertIn("系留", result["detail"])

    def test_parked_segment_direction_is_exactly_plus_z(self) -> None:
        """§2.1(f) 零转动证明的机检：方向向量逐位等于 (0, 0, 1)。"""
        plan = survey.build_plan(self.root, 1, 1, 1)
        near = plan["parked"]["position_world_m"]
        far = plan["parked"]["far_world_m"]
        direction = [far[i] - near[i] for i in range(3)]
        self.assertEqual(direction, [0.0, 0.0, contract.SURVEY_PARKED_SEGMENT_M])
        self.assertEqual(
            plan["parked_forward_world"], list(contract.PARKED_TARGET_FORWARD_WORLD)
        )
        # 段长 1.0 m ≥ 0.5 m ⇒ `LoopTargetVehicle` 的航点索引永不翻转。
        self.assertGreaterEqual(math.dist(tuple(near), tuple(far)), 0.5)

    def test_witness_azimuth_rounds_to_fifteen_degrees_with_lower_tie(self) -> None:
        anchor = (0.0, 0.2, 0.0)
        self.assertEqual(survey.witness_azimuth_deg(anchor, (1.0, 0.2, 0.0)), 0.0)
        # 正落在两倍数中点（7.5°）取较小者。
        midpoint = (math.cos(math.radians(7.5)), 0.2, math.sin(math.radians(7.5)))
        self.assertEqual(survey.witness_azimuth_deg(anchor, midpoint), 0.0)
        above = (math.cos(math.radians(7.6)), 0.2, math.sin(math.radians(7.6)))
        self.assertEqual(survey.witness_azimuth_deg(anchor, above), 15.0)

    def test_full_plan_has_the_frozen_view_shape(self) -> None:
        plan = survey.build_plan(self.root, 1, 1, 1)
        self.assertTrue(plan["valid"])
        self.assertEqual(plan["survey_position_count"], 14)
        self.assertEqual(plan["survey_view_count"], 14 * 16)
        self.assertEqual(plan["witness_view_count"], 3)
        self.assertEqual(len(plan["positions"]), 15)
        order = [position["position_id"] for position in plan["positions"]]
        self.assertEqual(order[0], "C14")
        self.assertEqual(order[7], "C26")
        self.assertEqual(order[-1], "W26")
        self.assertEqual(order[1:7], [f"R14-{int(a):03d}" for a in
                                     contract.SURVEY_RING_AZIMUTHS_DEG])


class PlanWriteTest(SurveyCase):
    """§5 第 1 条：`plan` 重跑字节幂等；create-once；五字段边界。"""

    def test_plan_rerun_is_byte_idempotent(self) -> None:
        first = self.write_plan()
        plan_file = self.root / first["plan_path"]
        scenario_file = self.root / first["scenario_path"]
        before = (plan_file.read_bytes(), scenario_file.read_bytes())
        self.write_plan()
        self.assertEqual((plan_file.read_bytes(), scenario_file.read_bytes()), before)

    def test_create_once_rejects_different_bytes(self) -> None:
        first = self.write_plan()
        plan_file = self.root / first["plan_path"]
        plan_file.write_bytes(plan_file.read_bytes() + b" ")
        with self.assertRaises(survey.SurveyError) as caught:
            self.write_plan()
        self.assertIn("create-once", str(caught.exception))

    def test_scenario_changes_only_the_five_permitted_fields(self) -> None:
        result = self.write_plan()
        default = survey.load_default_scenario(self.root)
        derived = json.loads(
            (self.root / result["scenario_path"]).read_text(encoding="utf-8")
        )
        changed = set(survey.scenario_diff_fields(default, derived))
        roots_changed = {
            path.split(".")[0] + ("." + path.split(".")[1] if "." in path else "")
            for path in changed
        }
        self.assertTrue(
            roots_changed
            <= {
                "scenario_id",
                "anchor_world_m.x", "anchor_world_m.y", "anchor_world_m.z",
                "target.route_world_m", "target.speed_mps",
                "sensor.retained_frame_count",
            },
            roots_changed,
        )

    def test_inherited_scene_adjustments_are_byte_identical(self) -> None:
        """AR2-6：default 已冻结的 6 条 relocation/removal 原样继承。"""
        result = self.write_plan()
        default = survey.load_default_scenario(self.root)
        derived = json.loads(
            (self.root / result["scenario_path"]).read_text(encoding="utf-8")
        )
        self.assertEqual(
            derived["scene_adjustments"], default["scene_adjustments"]
        )
        self.assertEqual(len(derived["scene_adjustments"]["vehicle_relocations"]), 6)
        self.assertEqual(derived["road_data_sha256"], default["road_data_sha256"])
        self.assertEqual(derived["drone"], default["drone"])
        self.assertEqual(derived["gimbal"], default["gimbal"])
        self.assertEqual(derived["evaluation"], default["evaluation"])
        self.assertEqual(derived["target"]["speed_mps"], 0)
        self.assertEqual(
            derived["sensor"]["retained_frame_count"],
            contract.SURVEY_RETAINED_FRAME_COUNT,
        )

    def test_unknown_anchor_is_rejected(self) -> None:
        with self.assertRaises(survey.SurveyError):
            survey.plan_identity(99, 1, 1)

    def test_plan_identity_envelope_caps_at_ten(self) -> None:
        original = survey.MAX_PLAN_IDENTITIES
        try:
            survey.MAX_PLAN_IDENTITIES = 1
            self.write_plan(anchor=1)
            with self.assertRaises(survey.SurveyError) as caught:
                self.write_plan(anchor=2)
            self.assertIn("信封用尽", str(caught.exception))
        finally:
            survey.MAX_PLAN_IDENTITIES = original


class PrepareTest(SurveyCase):
    """§5 第 1 条：帧目录非空、活动会话冲突、信封用尽、manifest create-once。"""

    def setUp(self) -> None:
        super().setUp()
        self.identity = self.write_plan()["plan_identity"]
        self.session = survey.session_identity(self.identity, 1)

    def test_prepare_installs_override_and_marker(self) -> None:
        manifest = survey.prepare_session(self.root, self.session)
        self.assertEqual(manifest["envelope_ordinal"], 1)
        self.assertTrue(survey.override_path(self.root).is_file())
        self.assertTrue(survey.marker_path(self.root).is_file())
        installed = json.loads(
            survey.override_path(self.root).read_text(encoding="utf-8")
        )
        self.assertEqual(installed["scenario_id"], self.identity)

    def test_manifest_is_create_once(self) -> None:
        survey.prepare_session(self.root, self.session)
        state = self.root / survey.state_root_for(self.session)
        (state / "manifest.json").write_bytes(b"{}\n")
        survey.override_path(self.root).unlink()
        survey.marker_path(self.root).unlink()
        with self.assertRaises(survey.SurveyError) as caught:
            survey.prepare_session(self.root, self.session)
        self.assertIn("create-once", str(caught.exception))

    def test_non_empty_frames_directory_is_rejected(self) -> None:
        (self.root / "runtime" / "frames" / "frame_0000000000.jpg").write_bytes(b"x")
        with self.assertRaises(survey.SurveyError) as caught:
            survey.prepare_session(self.root, self.session)
        self.assertIn("runtime/frames/ 非空", str(caught.exception))

    def test_existing_override_is_rejected(self) -> None:
        survey.override_path(self.root).write_text("{}", encoding="utf-8")
        with self.assertRaises(survey.SurveyError) as caught:
            survey.prepare_session(self.root, self.session)
        self.assertIn("运行时场景覆盖", str(caught.exception))

    def test_active_session_conflict_is_rejected(self) -> None:
        survey.prepare_session(self.root, self.session)
        survey.override_path(self.root).unlink()
        second = survey.session_identity(self.identity, 2)
        with self.assertRaises(survey.SurveyError) as caught:
            survey.prepare_session(self.root, second)
        self.assertIn("已有活动巡览会话", str(caught.exception))

    def test_exhausted_envelope_is_rejected_and_does_not_count(self) -> None:
        with self.assertRaises(survey.SurveyError) as caught:
            survey.prepare_session(self.root, self.session, envelope_limit=0)
        self.assertIn("信封用尽", str(caught.exception))
        self.assertFalse(survey.marker_path(self.root).exists())
        self.assertFalse(survey.override_path(self.root).exists())

    def test_prepare_requires_an_existing_plan_identity(self) -> None:
        absent = survey.session_identity("p1-vlm-survey-a7-p1-c1", 1)
        with self.assertRaises(survey.SurveyError) as caught:
            survey.prepare_session(self.root, absent)
        self.assertIn("尚未生成", str(caught.exception))


class DriveCase(SurveyCase):
    """装好计划 + 仿真的驱动用例基类。"""

    POSITIONS = 2
    VIEWS = 2

    def setUp(self) -> None:
        super().setUp()
        self.identity = self.write_plan()["plan_identity"]
        self.session = survey.session_identity(self.identity, 1)
        self.plan = self.trim_plan(self.identity, self.POSITIONS, self.VIEWS)
        survey.prepare_session(self.root, self.session)
        self.scenario = json.loads(
            survey.override_path(self.root).read_text(encoding="utf-8")
        )

    def _legal_view_ids(self) -> frozenset:
        survey_ids, witness_ids = contract.survey_plan_view_ids(self.plan)
        return survey_ids | witness_ids

    def start_simulator(self, **kwargs) -> tuple[FakeSimulator, survey.RuntimeBridge]:
        clock = VirtualClock()
        simulator = FakeSimulator(self.root, self.scenario, self.template, **kwargs)
        clock.simulator = simulator
        simulator.publish()  # 首帧（Play 进入后 FrameWriter 立即发布）
        bridge = survey.RuntimeBridge(self.root, clock=clock.now, sleep=clock.sleep)
        self.clock = clock
        return simulator, bridge

    def run_drive(self, **kwargs) -> dict:
        _simulator, bridge = self.start_simulator(**kwargs)
        return survey.drive_session(self.root, self.session, bridge)


class DrivePreconditionTest(DriveCase):
    """BC-SURVEY-2：观察到首帧后、发任何控制前核对零违规审计。"""

    def _body_command_written(self) -> bool:
        return (self.root / "runtime" / "body_command.json").exists()

    def test_missing_audit_refuses_before_any_control_command(self) -> None:
        result = self.run_drive(publish_audit=False)
        self.assertEqual(result["terminal"], "DRIVE_REFUSED_AUDIT")
        self.assertTrue(result["pre_command"])
        self.assertIn("road_scene_audit", result["detail"])
        self.assertFalse(self._body_command_written())

    def test_non_zero_violation_audit_refuses(self) -> None:
        result = self.run_drive(audit_status="INVALID_SCENE_LEGALITY", audit_violations=2)
        self.assertEqual(result["terminal"], "DRIVE_REFUSED_AUDIT")
        self.assertFalse(self._body_command_written())

    def test_audit_for_another_scenario_refuses(self) -> None:
        simulator, bridge = self.start_simulator()
        simulator._write_audit("some-other-scenario", "CLEAR", 0)
        result = survey.drive_session(self.root, self.session, bridge)
        self.assertEqual(result["terminal"], "DRIVE_REFUSED_AUDIT")
        self.assertFalse(self._body_command_written())

    def test_no_frames_aborts(self) -> None:
        clock = VirtualClock()
        simulator = FakeSimulator(
            self.root, self.scenario, self.template, publish_frames=False
        )
        clock.simulator = simulator
        bridge = survey.RuntimeBridge(self.root, clock=clock.now, sleep=clock.sleep)
        result = survey.drive_session(self.root, self.session, bridge)
        self.assertEqual(result["terminal"], "ABORTED_NO_FRAMES")
        self.assertFalse(self._body_command_written())

    def test_drive_requires_the_matching_active_marker(self) -> None:
        survey.marker_path(self.root).unlink()
        _simulator, bridge = self.start_simulator()
        with self.assertRaises(survey.SurveyError):
            survey.drive_session(self.root, self.session, bridge)


class DriveRunTest(DriveCase):
    def test_drive_completes_and_records_windows(self) -> None:
        result = self.run_drive()
        self.assertEqual(result["terminal"], "DRIVE_COMPLETE")
        self.assertTrue(result["views"])
        for window in result["views"]:
            first, last = window["frame_window"]
            self.assertIsNotNone(first)
            self.assertGreaterEqual(last, first)
        log = (self.root / survey.state_root_for(self.session) / "drive_log.jsonl")
        self.assertTrue(log.is_file())
        header = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(header["schema_version"], survey.DRIVE_LOG_SCHEMA)

    def test_commands_use_the_frozen_lease_and_speed_cap(self) -> None:
        self.run_drive()
        body = json.loads(
            (self.root / "runtime" / "body_command.json").read_text(encoding="utf-8")
        )
        self.assertEqual(body["protocol"], survey.CONTROL_PROTOCOL)
        self.assertEqual(body["expires_after_s"], contract.SURVEY_COMMAND_LEASE_S)
        gimbal = json.loads(
            (self.root / "runtime" / "gimbal_command.json").read_text(encoding="utf-8")
        )
        self.assertEqual(gimbal["command"]["mode"], "look_at_world")

    def test_velocity_is_clamped_to_three_metres_per_second(self) -> None:
        velocity, speed = survey._velocity_towards((0.0, 0.0, 0.0), (100.0, 0.0, 0.0))
        self.assertAlmostEqual(speed, contract.SURVEY_DRIVE_MAX_SPEED_MPS)
        self.assertAlmostEqual(velocity[0], contract.SURVEY_DRIVE_MAX_SPEED_MPS)
        slow, slow_speed = survey._velocity_towards((0.0, 0.0, 0.0), (0.2, 0.0, 0.0))
        self.assertAlmostEqual(slow_speed, 0.2)


class CloseTest(DriveCase):
    """§2.1(e)(h)：逐帧判定、两阶段发布、三种重入、零帧与树不符。"""

    def _run_and_close(self) -> tuple[dict, dict]:
        drive = self.run_drive()
        self.assertEqual(drive["terminal"], "DRIVE_COMPLETE")
        return drive, survey.close_session(self.root, self.session)

    def test_close_publishes_an_archive_and_clears_the_runtime(self) -> None:
        _drive, result = self._run_and_close()
        self.assertEqual(result["terminal"], "CLOSED_OK")
        archive = self.root / survey.archive_root_for(self.session)
        self.assertTrue((archive / "tree.json").is_file())
        self.assertTrue((archive / "selection.json").is_file())
        self.assertTrue((archive / "session" / "manifest.json").is_file())
        self.assertTrue((archive / "session" / "scenario_config.json").is_file())
        self.assertTrue((archive / "session" / "road_scene_audit.json").is_file())
        self.assertEqual(sorted((self.root / "runtime" / "frames").iterdir()), [])
        self.assertFalse(survey.override_path(self.root).exists())
        self.assertFalse(survey.marker_path(self.root).exists())
        self.assertFalse(
            (self.root / survey.archive_root_for(self.session)).parent.joinpath(
                f".staging-{self.session}"
            ).exists()
        )

    def test_completion_is_create_once_and_matches_the_tree(self) -> None:
        _drive, result = self._run_and_close()
        completion = json.loads(
            (self.root / survey.state_root_for(self.session) / "completion.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(completion["tree_sha256"], result["tree_sha256"])
        self.assertIn(completion["terminal"], contract.SURVEY_CLOSE_TERMINALS)
        self.assertIn("tentative_witness", completion)

    def test_verify_accepts_the_published_archive(self) -> None:
        self._run_and_close()
        verified = survey.verify_session(self.root, self.session)
        self.assertTrue(verified["verified"])
        self.assertGreater(verified["frame_count"], 0)

    def test_verify_rejects_a_selection_that_lost_a_frame(self) -> None:
        self._run_and_close()
        archive = self.root / survey.archive_root_for(self.session)
        selection = json.loads((archive / "selection.json").read_text(encoding="utf-8"))
        selection["entries"] = selection["entries"][:-1]
        (archive / "selection.json").write_text(
            json.dumps(selection, ensure_ascii=False), encoding="utf-8"
        )
        with self.assertRaises(survey.SurveyError) as caught:
            survey.verify_session(self.root, self.session)
        self.assertIn("一一对应", str(caught.exception))

    def test_verify_rejects_a_class_outside_the_closed_set(self) -> None:
        self._run_and_close()
        archive = self.root / survey.archive_root_for(self.session)
        selection = json.loads((archive / "selection.json").read_text(encoding="utf-8"))
        selection["entries"][0]["class"] = "SOMETHING_ELSE"
        (archive / "selection.json").write_text(
            json.dumps(selection, ensure_ascii=False), encoding="utf-8"
        )
        with self.assertRaises(survey.SurveyError) as caught:
            survey.verify_session(self.root, self.session)
        self.assertIn("闭集", str(caught.exception))

    def test_selection_covers_every_archived_frame_exactly_once(self) -> None:
        self._run_and_close()
        archive = self.root / survey.archive_root_for(self.session)
        selection = json.loads((archive / "selection.json").read_text(encoding="utf-8"))
        archived = sorted(
            int(path.stem.rsplit("_", 1)[-1])
            for path in (archive / "frames").glob("frame_*.jpg")
        )
        declared = sorted(entry["frame_id"] for entry in selection["entries"])
        self.assertEqual(declared, archived)
        for entry in selection["entries"]:
            self.assertIn(entry["class"], contract.SURVEY_FRAME_CLASSES)

    def test_transit_frames_are_protocol_invalid(self) -> None:
        self._run_and_close()
        archive = self.root / survey.archive_root_for(self.session)
        selection = json.loads((archive / "selection.json").read_text(encoding="utf-8"))
        outside = [
            entry for entry in selection["entries"] if entry["view_id"] is None
        ]
        self.assertTrue(outside, "转场/起飞帧必须存在且被判 PROTOCOL_INVALID")
        for entry in outside:
            self.assertEqual(entry["class"], "PROTOCOL_INVALID")
            self.assertEqual(entry["reason"], "OUTSIDE_ANY_DWELL_WINDOW")


class ReentryTest(DriveCase):
    """§2.1(h)：三种重入 + `CLOSE_TREE_MISMATCH` 不删任何文件。"""

    def setUp(self) -> None:
        super().setUp()
        self.run_drive()

    def test_reentry_after_completion_with_leftover_source(self) -> None:
        first = survey.close_session(self.root, self.session)
        archive = self.root / survey.archive_root_for(self.session)
        tree = json.loads((archive / "tree.json").read_text(encoding="utf-8"))
        # 模拟第 5 步中断：把一个已核验成员放回源目录。
        member = next(m for m in tree["members"] if m["path"].startswith("frames/"))
        source = self.root / "runtime" / "frames" / Path(member["path"]).name
        shutil.copy2(archive / member["path"], source)
        result = survey.close_session(self.root, self.session)
        self.assertEqual(result["terminal"], "CLOSE_RESIDUE_RECOVERED")
        self.assertEqual(result["tree_sha256"], first["tree_sha256"])
        self.assertFalse(source.exists())

    def test_reentry_moves_foreign_residue_into_a_hold(self) -> None:
        survey.close_session(self.root, self.session)
        frames = self.root / "runtime" / "frames"
        frames.mkdir(parents=True, exist_ok=True)
        foreign = frames / "frame_0009999999.jpg"
        foreign.write_bytes(b"foreign bytes not in the tree")
        result = survey.close_session(self.root, self.session)
        hold = (
            self.root / "runtime" / f"frames.{self.session}-foreign-residue-hold"
        )
        self.assertTrue((hold / foreign.name).is_file())
        self.assertFalse(foreign.exists())
        self.assertIn(result["terminal"], contract.SURVEY_CLOSE_TERMINALS)
        # 附录 A.3：该 hold 只盘点，永不进母集。
        from tools.dist_data import roots as _roots

        relative = (hold / foreign.name).relative_to(self.root).as_posix()
        entries = _roots.matching_entries(relative)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].usage_class, "DIAGNOSTIC_HOLD")

    def test_reentry_when_completion_is_missing(self) -> None:
        first = survey.close_session(self.root, self.session)
        completion = self.root / survey.state_root_for(self.session) / "completion.json"
        completion.unlink()
        result = survey.close_session(self.root, self.session)
        self.assertTrue(completion.is_file())
        self.assertEqual(result["tree_sha256"], first["tree_sha256"])
        self.assertEqual(result["reentry"], "completion_missing")

    def test_reentry_from_staging_residue(self) -> None:
        archive_parent = (self.root / survey.archive_root_for(self.session)).parent
        staging = archive_parent / f".staging-{self.session}"
        staging.mkdir(parents=True)
        (staging / "frames").mkdir()
        source = next((self.root / "runtime" / "frames").glob("frame_*.jpg"))
        shutil.copy2(source, staging / "frames" / source.name)
        result = survey.close_session(self.root, self.session)
        self.assertEqual(result["terminal"], "CLOSED_OK")
        self.assertFalse(staging.exists())
        survey.verify_session(self.root, self.session)

    def test_tree_mismatch_keeps_every_file(self) -> None:
        survey.close_session(self.root, self.session)
        archive = self.root / survey.archive_root_for(self.session)
        completion_path = (
            self.root / survey.state_root_for(self.session) / "completion.json"
        )
        # 归档被外部改动 → 重算树摘要与 completion 不符。改的是一张归档帧，
        # 而不是 manifest：manifest 还要供 BC-SURVEY-14 的钉子核对，把它清空会
        # 先在钉子上失败，测不到树摘要那一支。
        target = next((archive / "frames").glob("frame_*.jpg"))
        target.write_bytes(target.read_bytes() + b"\x00")
        before = sorted(path.name for path in archive.rglob("*") if path.is_file())
        result = survey.close_session(self.root, self.session)
        self.assertEqual(result["terminal"], "CLOSE_TREE_MISMATCH")
        self.assertEqual(result["released"], [])
        after = sorted(path.name for path in archive.rglob("*") if path.is_file())
        self.assertEqual(before, after)
        self.assertTrue(completion_path.is_file())


class FrameValidityTest(DriveCase):
    """§2.1(e)：逐帧独立判定——窗内朝向/位置不达标的帧被降级。"""

    def _sidecars(self, aims: list[list[float]], position: list[float]) -> dict:
        simulator = FakeSimulator(self.root, self.scenario, self.template)
        simulator.position = list(position)
        collected: dict[int, dict] = {}
        for aim in aims:
            simulator.look_at = list(aim)
            frame_id = simulator.publish()
            collected[frame_id] = json.loads(
                (self.root / "runtime" / "frames" / f"frame_{frame_id:010d}.json")
                .read_text(encoding="utf-8")
            )
        return collected

    def _window(self, position: list[float], look_at: list[float], first: int, last: int) -> dict:
        return {
            "view_id": contract.survey_view_id("C14", 0),
            "position_id": "C14",
            "kind": "survey",
            "position_world_m": list(position),
            "look_at_world_m": list(look_at),
            "frame_window": [first, last],
            "min_valid_frames": contract.SURVEY_MIN_VALID_FRAMES_PER_VIEW,
        }

    def test_early_in_window_frame_off_bearing_is_downgraded(self) -> None:
        position = [206.0, 20.2, 55.0]
        planned = [216.0, 0.2, 55.0]
        off = [206.0 + 10.0 * math.cos(math.radians(40.0)), 0.2,
               55.0 + 10.0 * math.sin(math.radians(40.0))]
        sidecars = self._sidecars([off, planned, planned, planned], position)
        window = self._window(position, planned, min(sidecars), max(sidecars))
        classification = survey.classify_frames(
            [window], sidecars, self._legal_view_ids(),
            survey.planned_view_counts(self.plan),
        )
        by_id = {entry["frame_id"]: entry for entry in classification["entries"]}
        first = min(sidecars)
        self.assertEqual(by_id[first]["class"], "PROTOCOL_INVALID")
        self.assertEqual(by_id[first]["reason"], "BEARING_OFF_PLAN")
        self.assertGreater(by_id[first]["bearing_error_deg"],
                           contract.SURVEY_BEARING_TOLERANCE_DEG)
        for frame_id in sorted(sidecars)[1:]:
            self.assertEqual(by_id[frame_id]["class"], "VALID_SURVEY")
        # 窗内有效帧 3 ≥ 3 → 该视角仍达成。
        self.assertTrue(classification["per_view"][0]["achieved"])
        self.assertEqual(classification["per_view"][0]["valid_frames"], 3)

    def test_view_below_the_valid_frame_floor_is_not_achieved(self) -> None:
        position = [206.0, 20.2, 55.0]
        planned = [216.0, 0.2, 55.0]
        sidecars = self._sidecars([planned, planned], position)
        window = self._window(position, planned, min(sidecars), max(sidecars))
        classification = survey.classify_frames(
            [window], sidecars, self._legal_view_ids(),
            survey.planned_view_counts(self.plan),
        )
        self.assertEqual(classification["per_view"][0]["valid_frames"], 2)
        self.assertFalse(classification["per_view"][0]["achieved"])
        self.assertEqual(classification["achievement_rate"], 0.0)

    def test_position_off_plan_is_downgraded(self) -> None:
        planned_position = [206.0, 20.2, 55.0]
        actual_position = [206.0 + 5.0, 20.2, 55.0]
        planned = [216.0, 0.2, 55.0]
        sidecars = self._sidecars([planned], actual_position)
        window = self._window(planned_position, planned, min(sidecars), max(sidecars))
        classification = survey.classify_frames(
            [window], sidecars, self._legal_view_ids(),
            survey.planned_view_counts(self.plan),
        )
        entry = classification["entries"][0]
        self.assertEqual(entry["class"], "PROTOCOL_INVALID")
        self.assertEqual(entry["reason"], "POSITION_OFF_PLAN")

    def test_low_achievement_downgrades_the_whole_session(self) -> None:
        classification = {
            "entries": [
                {"frame_id": 1, "view_id": "s/C14/00", "class": "VALID_SURVEY",
                 "reason": "IN_WINDOW"},
            ],
            "achievement_rate": 0.5,
        }
        entries, downgraded = survey.apply_low_achievement_downgrade(classification)
        self.assertTrue(downgraded)
        self.assertEqual(entries[0]["class"], "PROTOCOL_INVALID")
        self.assertEqual(entries[0]["reason"], "SESSION_ACHIEVEMENT_BELOW_90")

    def test_at_threshold_achievement_is_not_downgraded(self) -> None:
        classification = {
            "entries": [{"frame_id": 1, "view_id": "s/C14/00",
                         "class": "VALID_SURVEY", "reason": "IN_WINDOW"}],
            "achievement_rate": contract.SURVEY_MIN_ACHIEVEMENT_RATE,
        }
        entries, downgraded = survey.apply_low_achievement_downgrade(classification)
        self.assertFalse(downgraded)
        self.assertEqual(entries[0]["class"], "VALID_SURVEY")


class ZeroFrameCloseTest(DriveCase):
    """§2.1(h)：零帧会话归档、计 Play、清标记。"""

    def test_zero_frame_close_archives_only_the_session_directory(self) -> None:
        clock = VirtualClock()
        simulator = FakeSimulator(
            self.root, self.scenario, self.template, publish_frames=False
        )
        clock.simulator = simulator
        bridge = survey.RuntimeBridge(self.root, clock=clock.now, sleep=clock.sleep)
        drive = survey.drive_session(self.root, self.session, bridge)
        self.assertEqual(drive["terminal"], "ABORTED_NO_FRAMES")

        result = survey.close_session(self.root, self.session)
        self.assertEqual(result["terminal"], "CLOSED_ZERO_FRAMES")
        self.assertEqual(result["frame_count"], 0)
        archive = self.root / survey.archive_root_for(self.session)
        self.assertTrue((archive / "session" / "manifest.json").is_file())
        self.assertFalse((archive / "frames").exists())
        self.assertFalse(survey.marker_path(self.root).exists())
        self.assertFalse(survey.override_path(self.root).exists())
        # 计 Play：零帧会话同样消耗信封。
        self.assertEqual(survey.spent_play_count(self.root), 1)

    def test_zero_frame_close_accepts_a_pre_command_refusal_log(self) -> None:
        _simulator, bridge = self.start_simulator(publish_audit=False)
        drive = survey.drive_session(self.root, self.session, bridge)
        self.assertEqual(drive["terminal"], "DRIVE_REFUSED_AUDIT")
        # 模拟操作员在任何帧被保留前退出 Play：仿真发布的帧不落地。
        for path in sorted((self.root / "runtime" / "frames").iterdir()):
            path.unlink()
        result = survey.close_session(self.root, self.session)
        self.assertEqual(result["terminal"], "CLOSED_ZERO_FRAMES")
        archive = self.root / survey.archive_root_for(self.session)
        self.assertTrue((archive / "drive_log.jsonl").is_file())

    def test_zero_frames_with_a_post_command_terminal_is_fail_closed(self) -> None:
        self.run_drive()
        for path in sorted((self.root / "runtime" / "frames").iterdir()):
            path.unlink()
        with self.assertRaises(survey.SurveyError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("不属零帧", str(caught.exception))


class DiagnosticTest(SurveyCase):
    """BC-SURVEY-3：COORD-005 诊断零新 ID，配置只在 `runtime/` 生存。"""

    def test_diagnostic_reuses_the_default_scenario_id_and_creates_no_identity(self) -> None:
        result = survey.install_diagnostic(self.root, 1)
        default = survey.load_default_scenario(self.root)
        self.assertEqual(result["scenario_id"], default["scenario_id"])
        self.assertFalse(result["creates_ids"])
        installed = json.loads(
            survey.override_path(self.root).read_text(encoding="utf-8")
        )
        self.assertEqual(installed["scenario_id"], default["scenario_id"])
        # 不建正式 plan/config、不建 session 状态、不写活动标记。
        self.assertFalse((self.root / survey.PLAN_DIRECTORY).exists())
        self.assertEqual(
            sorted((self.root / "config").glob("scenario.p1-vlm-survey-*.json")), []
        )
        self.assertFalse((self.root / roots_state()).exists())
        self.assertFalse(survey.marker_path(self.root).exists())

    def test_diagnostic_still_installs_the_survey_anchor_and_parked_target(self) -> None:
        survey.install_diagnostic(self.root, 1)
        installed = json.loads(
            survey.override_path(self.root).read_text(encoding="utf-8")
        )
        self.assertEqual(installed["anchor_world_m"]["x"], 206.0)
        self.assertEqual(installed["target"]["speed_mps"], 0)
        self.assertEqual(len(installed["target"]["route_world_m"]), 2)

    def test_diagnostic_requires_a_quiescent_runtime(self) -> None:
        (self.root / "runtime" / "frames" / "frame_0000000000.jpg").write_bytes(b"x")
        with self.assertRaises(survey.SurveyError):
            survey.install_diagnostic(self.root, 1)

    def test_collect_moves_frames_into_a_create_once_hold_and_unloads_override(self) -> None:
        survey.install_diagnostic(self.root, 1)
        scenario = json.loads(
            survey.override_path(self.root).read_text(encoding="utf-8")
        )
        simulator = FakeSimulator(self.root, scenario, self.template)
        for _ in range(3):
            simulator.publish()
        result = survey.collect_diagnostic(self.root)
        self.assertEqual(result["hold_index"], 1)
        self.assertEqual(result["jpg_count"], 3)
        hold = self.root / result["hold"]
        self.assertTrue(hold.is_dir())
        self.assertEqual(sorted((self.root / "runtime" / "frames").iterdir()), [])
        self.assertFalse(survey.override_path(self.root).exists())
        # 现场已恢复干净：再次 collect 无帧可收，拒绝白占一个诊断序号。
        with self.assertRaises(survey.SurveyError) as caught:
            survey.collect_diagnostic(self.root)
        self.assertIn("无可收集的诊断帧", str(caught.exception))
        self.assertFalse(survey.diagnostic_hold_path(self.root, 2).exists())

    def test_diagnostic_envelope_caps_at_three(self) -> None:
        for index in range(1, survey.MAX_DIAGNOSTIC_PLAY + 1):
            survey.diagnostic_hold_path(self.root, index).mkdir(parents=True)
        with self.assertRaises(survey.SurveyError) as caught:
            survey.install_diagnostic(self.root, 1)
        self.assertIn("诊断 Play 信封用尽", str(caught.exception))


def roots_state() -> str:
    from tools.dist_data import roots as _roots

    return _roots.SURVEY_STATE_ROOT


class InventoryIntegrationTest(DriveCase):
    """§2.2 第 1/4 条：S1 在真实归档上的逐帧降级与会话表一致性。"""

    def setUp(self) -> None:
        super().setUp()
        self.run_drive()
        self.close_result = survey.close_session(self.root, self.session)
        shutil.copytree(
            PROJECT_ROOT / "docs" / "evidence" / "P1-M3-BODY-001-1b",
            self.root / "docs" / "evidence" / "P1-M3-BODY-001-1b",
            dirs_exist_ok=True,
        )

    def test_inventory_classifies_survey_frames_and_resolves_the_family(self) -> None:
        from tools.dist_data import build_inventory as inventory_module

        payload = inventory_module.build_inventory(self.root)
        survey_records = [
            record
            for record in payload["records"]
            if record["kind"] == "image"
            and record["path"].startswith(roots_archive())
        ]
        self.assertTrue(survey_records)
        for record in survey_records:
            self.assertEqual(record["family"], self.session)
            self.assertIn(record["usage_class"], contract.SURVEY_FRAME_CLASSES)
            self.assertIn("survey_selection", record)
        self.assertTrue(
            any(record["usage_class"] == "VALID_SURVEY" for record in survey_records)
        )
        self.assertTrue(
            any(record["usage_class"] == "PROTOCOL_INVALID" for record in survey_records)
        )

    def test_selection_downgrade_is_only_downward(self) -> None:
        from tools.dist_data import build_inventory as inventory_module

        payload = inventory_module.build_inventory(self.root)
        for record in payload["records"]:
            if "survey_selection" not in record:
                continue
            declared = record["survey_selection"]["class"]
            self.assertEqual(record["usage_class"], declared)
            # pattern 给的永远是 VALID_SURVEY；结果只能是它本身或降级。
            self.assertIn(declared, contract.SURVEY_FRAME_CLASSES)

    def test_missing_selection_row_is_fail_closed(self) -> None:
        from tools.dist_data import build_inventory as inventory_module

        archive = self.root / survey.archive_root_for(self.session)
        selection = json.loads((archive / "selection.json").read_text(encoding="utf-8"))
        selection["entries"] = selection["entries"][:-1]
        (archive / "selection.json").write_text(
            json.dumps(selection, ensure_ascii=False), encoding="utf-8"
        )
        with self.assertRaises(inventory_module.InventoryError) as caught:
            inventory_module.build_inventory(self.root)
        self.assertIn("selection.json", str(caught.exception))

    def test_survey_sessions_table_matches_the_enumerated_archives(self) -> None:
        from tools.dist_data import build_inventory as inventory_module

        sessions = contract.build_survey_sessions(self.root)
        self.assertEqual(len(sessions), 1)
        row = sessions[0]
        self.assertEqual(row["session_id"], self.session)
        self.assertEqual(row["plan_identity"], self.identity)
        self.assertEqual(row["tree_sha256"], self.close_result["tree_sha256"])
        self.assertEqual(sorted(row), sorted(contract.SURVEY_SESSION_ROW_KEYS))
        inventory_module.build_inventory(self.root, survey_sessions=sessions)

    def test_a_stale_session_table_is_rejected(self) -> None:
        from tools.dist_data import build_inventory as inventory_module

        with self.assertRaises(inventory_module.InventoryError) as caught:
            inventory_module.build_inventory(self.root, survey_sessions=[])
        self.assertIn("行数 0 与实际枚举 1 不等", str(caught.exception))

    def test_a_duplicated_session_row_is_rejected(self) -> None:
        """dict 化会让重复行被静默覆盖，逐项相等就成了空话（C1 关注项 3）。"""
        from tools.dist_data import build_inventory as inventory_module

        sessions = contract.build_survey_sessions(self.root)
        with self.assertRaises(inventory_module.InventoryError) as caught:
            inventory_module.build_inventory(
                self.root, survey_sessions=sessions + list(sessions)
            )
        self.assertIn("重复会话行", str(caught.exception))

    def test_a_row_with_extra_keys_is_rejected(self) -> None:
        from tools.dist_data import build_inventory as inventory_module

        sessions = contract.build_survey_sessions(self.root)
        sessions[0]["smuggled"] = "x"
        with self.assertRaises(inventory_module.InventoryError) as caught:
            inventory_module.build_inventory(self.root, survey_sessions=sessions)
        self.assertIn("闭集外字段", str(caught.exception))

    def test_a_tampered_row_is_rejected(self) -> None:
        from tools.dist_data import build_inventory as inventory_module

        sessions = contract.build_survey_sessions(self.root)
        sessions[0]["tree_sha256"] = "0" * 64
        with self.assertRaises(inventory_module.InventoryError) as caught:
            inventory_module.build_inventory(self.root, survey_sessions=sessions)
        self.assertIn("tree_sha256", str(caught.exception))


def roots_archive() -> str:
    from tools.dist_data import roots as _roots

    return _roots.SURVEY_ARCHIVE_ROOT


class SurveyLayoutAuthorityTest(DriveCase):
    """§2.2 第 2 条：S2 的三项巡览族失效条件（审计 / 证人 / 事后净空）。"""

    def setUp(self) -> None:
        super().setUp()
        self.run_drive()
        survey.close_session(self.root, self.session)
        from tools.dist_data import bind_layout

        self.bind_layout = bind_layout
        self.archive = self.root / survey.archive_root_for(self.session)
        self.frames = sorted(
            (self.archive / "frames").glob("frame_*.jpg")
        )
        self.record = {
            "partition_id": f"{self.session}|sha",
            "scenario_path": survey.scenario_path_for(self.identity),
        }
        self.frame_paths = [
            path.relative_to(self.root).as_posix() for path in self.frames
        ]
        self.base_instances = self.bind_layout.load_base_geometry(self.root)["instances"]

    def _validate(self) -> dict:
        return self.bind_layout.validate_survey_partition(
            self.root,
            self.record,
            self.frame_paths,
            [self.archive.relative_to(self.root).as_posix()],
            self.base_instances,
            _NoPixels(),
        )

    def test_clear_audit_report_is_recognised(self) -> None:
        status = self.bind_layout.survey_audit_report_status(self.archive)
        self.assertTrue(status["clear"])
        self.assertEqual(status["scenario_id"], self.identity)

    def test_missing_audit_report_invalidates_the_family(self) -> None:
        (self.archive / "session" / "road_scene_audit.json").unlink()
        result = self._validate()
        self.assertEqual(result["status"], self.bind_layout.BINDING_INVALID)
        self.assertIn("审计", result["reason"])

    def test_non_zero_violation_audit_invalidates_the_family(self) -> None:
        path = self.archive / "session" / "road_scene_audit.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["status"] = "INVALID_SCENE_LEGALITY"
        document["road_violation_count"] = 1
        path.write_text(json.dumps(document), encoding="utf-8")
        status = self.bind_layout.survey_audit_report_status(self.archive)
        self.assertFalse(status["clear"])
        self.assertEqual(self._validate()["status"], self.bind_layout.BINDING_INVALID)

    def test_post_hoc_clearance_rejects_a_frame_beyond_the_tether(self) -> None:
        anchor = (206.0, 0.2, 55.0)
        samples = [
            {"frame_id": "a", "camera_position_world_m": [206.0, 20.2, 55.0]},
            {"frame_id": "b", "camera_position_world_m": [206.0 + 40.0, 20.2, 55.0]},
        ]
        result = self.bind_layout.survey_post_hoc_clearance(samples, anchor, [])
        self.assertFalse(result["passed"])
        self.assertEqual(result["tether_violation_count"], 1)
        self.assertEqual(result["tether_violation_frames"], ["b"])

    def test_post_hoc_clearance_rejects_a_frame_inside_an_expanded_box(self) -> None:
        anchor = (206.0, 0.2, 55.0)
        box = {
            "scene_object_name": "synthetic",
            "min_x_m": 205.0, "max_x_m": 207.0,
            "min_y_m": 0.0, "max_y_m": 25.0,
            "min_z_m": 54.0, "max_z_m": 56.0,
        }
        samples = [{"frame_id": "a", "camera_position_world_m": [206.0, 20.2, 55.0]}]
        result = self.bind_layout.survey_post_hoc_clearance(samples, anchor, [box])
        self.assertFalse(result["passed"])
        self.assertEqual(result["box_violation_count"], 1)

    def test_real_archive_frames_pass_post_hoc_clearance(self) -> None:
        result = self._validate()
        clearance = result.get("post_hoc_clearance")
        self.assertIsNotNone(clearance)
        self.assertTrue(clearance["passed"], clearance)
        self.assertLessEqual(
            clearance["max_tether_distance_m"], contract.SURVEY_TETHER_LENGTH_M
        )

    def test_insufficient_witness_frames_invalidates_without_touching_pixels(self) -> None:
        result = self._validate()
        self.assertEqual(result["witness"]["verdict"], "INSUFFICIENT_WITNESS_FRAMES")
        self.assertLess(
            result["witness"]["denominator"], contract.SURVEY_WITNESS_MIN_DENOMINATOR
        )
        self.assertEqual(result["status"], self.bind_layout.BINDING_INVALID)

    def test_close_tentative_witness_uses_the_same_function_as_s2(self) -> None:
        completion = json.loads(
            (self.root / survey.state_root_for(self.session) / "completion.json")
            .read_text(encoding="utf-8")
        )
        tentative = completion["tentative_witness"]
        authoritative = self._validate()["witness"]
        self.assertEqual(tentative["verdict"], authoritative["verdict"])
        self.assertEqual(tentative["denominator"], authoritative["denominator"])
        self.assertEqual(tentative["connectivity"], authoritative["connectivity"])


class _NoPixels:
    """分母不足时证人判定必须在触碰像素**之前**返回；触碰即用例失败。"""

    def crop_rgb(self, frame_id, box_px):  # noqa: ANN001
        raise AssertionError("分母不足时不应读取像素")


class WitnessPixelTest(SurveyCase):
    """§2.1(f) 证人判定的像素侧（需要 Pillow，与既有像素用例同一约定）。"""

    def setUp(self) -> None:
        super().setUp()
        try:
            import PIL  # noqa: F401,PLC0415
        except ImportError:
            self.skipTest("本解释器没有 Pillow；改用钉死环境 .venv-yoloe/bin/python")

    def _pixels(self, frame_id: str, painter) -> object:
        from PIL import Image  # noqa: PLC0415
        from tools.dist_data import pixel_source  # noqa: PLC0415

        image = Image.new("RGB", (64, 48), (30, 30, 30))
        painter(image)
        path = self.root / frame_id
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, format="JPEG", quality=95)
        return pixel_source.ArchivePixelSource(self.root)

    def test_red_components_finds_the_painted_blob(self) -> None:
        from tools.dist_data import bind_layout  # noqa: PLC0415

        def paint(image):
            for x in range(10, 20):
                for y in range(12, 22):
                    image.putpixel((x, y), (230, 20, 20))

        frame_id = "runtime/frames.witness-fixture/frame_0000000000.jpg"
        pixels = self._pixels(frame_id, paint)
        components = bind_layout.red_components(pixels, frame_id, 64, 48)
        self.assertTrue(components)
        best = max(components, key=lambda item: item["area"])
        self.assertGreater(best["area"], 50)
        x0, y0, x1, y1 = best["box"]
        self.assertLessEqual(abs(x0 - 10.0), 2.0)
        self.assertLessEqual(abs(y1 - 22.0), 2.0)

    def test_a_grey_frame_yields_no_red_component(self) -> None:
        from tools.dist_data import bind_layout  # noqa: PLC0415

        frame_id = "runtime/frames.witness-fixture/frame_0000000001.jpg"
        pixels = self._pixels(frame_id, lambda image: None)
        self.assertEqual(bind_layout.red_components(pixels, frame_id, 64, 48), [])


class PlanPinTest(DriveCase):
    """BC-SURVEY-13：manifest 是 plan 的钉子，钉不住即 fail-closed。"""

    def _manifest_path(self) -> Path:
        return self.root / survey.state_root_for(self.session) / "manifest.json"

    def test_pinned_plan_loads_on_the_happy_path(self) -> None:
        plan = contract.load_pinned_survey_plan(
            self.root, self._manifest_path(), session_id=self.session
        )
        self.assertEqual(plan["plan_identity"], self.identity)

    def test_edited_plan_bytes_break_the_pin(self) -> None:
        plan_file = self.root / survey.plan_path_for(self.identity)
        plan_file.write_bytes(plan_file.read_bytes() + b" ")
        with self.assertRaises(contract.SurveyContractError) as caught:
            contract.load_pinned_survey_plan(
                self.root, self._manifest_path(), session_id=self.session
            )
        self.assertIn("哈希不符", str(caught.exception))

    def test_missing_plan_file_breaks_the_pin(self) -> None:
        (self.root / survey.plan_path_for(self.identity)).unlink()
        with self.assertRaises(contract.SurveyContractError):
            contract.load_pinned_survey_plan(
                self.root, self._manifest_path(), session_id=self.session
            )

    def test_manifest_supplied_plan_path_is_checked_not_trusted(self) -> None:
        path = self._manifest_path()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["plan_path"] = "config/elsewhere/plan.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(contract.SurveyContractError) as caught:
            contract.load_pinned_survey_plan(
                self.root, path, session_id=self.session
            )
        self.assertIn("plan_path", str(caught.exception))

    def test_short_or_non_hex_pin_is_rejected(self) -> None:
        path = self._manifest_path()
        for bogus in ("", "abc", "Z" * 64, "A" * 64, None):
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["plan_sha256"] = bogus
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(contract.SurveyContractError, msg=repr(bogus)):
                contract.load_pinned_survey_plan(
                    self.root, path, session_id=self.session
                )

    def test_session_id_mismatch_is_rejected(self) -> None:
        other = survey.session_identity(self.identity, 2)
        with self.assertRaises(contract.SurveyContractError):
            contract.load_pinned_survey_plan(
                self.root, self._manifest_path(), session_id=other
            )

    def test_drive_refuses_a_plan_edited_after_prepare(self) -> None:
        plan_file = self.root / survey.plan_path_for(self.identity)
        plan_file.write_bytes(plan_file.read_bytes() + b"\n")
        _simulator, bridge = self.start_simulator()
        with self.assertRaises(contract.SurveyContractError):
            survey.drive_session(self.root, self.session, bridge)


class ViewIdEnforcementTest(DriveCase):
    """BC-SURVEY-13：生产侧与读回侧都拒绝未绑定 plan 的标签。"""

    def test_classify_frames_rejects_an_unplanned_window(self) -> None:
        legal = frozenset({"s/C14/00"})
        window = {
            "view_id": "w/C14",
            "position_id": "C14",
            "kind": "witness",
            "position_world_m": [0.0, 10.0, 0.0],
            "look_at_world_m": [1.0, 0.0, 0.0],
            "frame_window": [0, 1],
            "min_valid_frames": 3,
        }
        with self.assertRaises(survey.SurveyError) as caught:
            survey.classify_frames([window], {}, legal, (1, 0))
        self.assertIn("已复核 plan", str(caught.exception))

    def test_classify_frames_rejects_a_window_without_a_view_id(self) -> None:
        window = {"kind": "survey", "frame_window": [0, 1], "min_valid_frames": 3}
        with self.assertRaises(survey.SurveyError):
            survey.classify_frames([window], {}, frozenset({"s/C14/00"}), (1, 0))

    def test_classify_frames_rejects_an_unknown_kind(self) -> None:
        legal = frozenset({"s/C14/00"})
        window = {
            "view_id": "s/C14/00",
            "position_id": "C14",
            "kind": "calibration",
            "position_world_m": [0.0, 10.0, 0.0],
            "look_at_world_m": [1.0, 0.0, 0.0],
            "frame_window": [None, None],
            "min_valid_frames": 3,
        }
        with self.assertRaises(survey.SurveyError) as caught:
            survey.classify_frames([window], {}, legal, (1, 0))
        self.assertIn("kind", str(caught.exception))

    def test_close_produces_only_plan_bound_view_ids(self) -> None:
        self.run_drive()
        survey.close_session(self.root, self.session)
        archive = self.root / survey.archive_root_for(self.session)
        selection = json.loads((archive / "selection.json").read_text(encoding="utf-8"))
        plan = contract.load_pinned_survey_plan(
            self.root,
            archive / "session" / "manifest.json",
            session_id=self.session,
        )
        survey_ids, witness_ids = contract.survey_plan_view_ids(plan)
        legal = survey_ids | witness_ids
        for entry in selection["entries"]:
            contract.validate_selection_view_id(
                entry["view_id"], entry["class"], legal
            )

    def test_verify_rejects_a_prefix_only_witness_label(self) -> None:
        self.run_drive()
        survey.close_session(self.root, self.session)
        archive = self.root / survey.archive_root_for(self.session)
        selection = json.loads((archive / "selection.json").read_text(encoding="utf-8"))
        # 一个「像证人」但未绑定 plan 的标签：旧的 `startswith("w/")` 会放行。
        target = next(
            entry for entry in selection["entries"] if entry["class"] == "VALID_SURVEY"
        )
        target["view_id"] = "w/R14-000"
        (archive / "selection.json").write_text(
            json.dumps(selection, ensure_ascii=False), encoding="utf-8"
        )
        with self.assertRaises(survey.SurveyError) as caught:
            survey.verify_session(self.root, self.session)
        self.assertIn("view_id", str(caught.exception))

    def test_s2_rejects_a_prefix_only_witness_label(self) -> None:
        from tools.dist_data import bind_layout  # noqa: PLC0415

        self.run_drive()
        survey.close_session(self.root, self.session)
        archive = self.root / survey.archive_root_for(self.session)
        selection = json.loads((archive / "selection.json").read_text(encoding="utf-8"))
        target = next(
            entry for entry in selection["entries"] if entry["class"] == "VALID_SURVEY"
        )
        target["view_id"] = "w/R14-000"
        (archive / "selection.json").write_text(
            json.dumps(selection, ensure_ascii=False), encoding="utf-8"
        )
        with self.assertRaises(bind_layout.LayoutError) as caught:
            bind_layout._survey_selection_rows(self.root, archive)
        self.assertIn("view_id", str(caught.exception))

    def test_s1_rejects_a_prefix_only_witness_label(self) -> None:
        from tools.dist_data import build_inventory as inventory_module  # noqa: PLC0415

        self.run_drive()
        survey.close_session(self.root, self.session)
        archive = self.root / survey.archive_root_for(self.session)
        selection = json.loads((archive / "selection.json").read_text(encoding="utf-8"))
        target = next(
            entry for entry in selection["entries"] if entry["class"] == "VALID_SURVEY"
        )
        target["view_id"] = "w/R14-000"
        (archive / "selection.json").write_text(
            json.dumps(selection, ensure_ascii=False), encoding="utf-8"
        )
        with self.assertRaises(inventory_module.InventoryError) as caught:
            inventory_module.build_inventory(self.root)
        self.assertIn("view_id", str(caught.exception))

    def test_s1_rejects_a_missing_view_id_key(self) -> None:
        from tools.dist_data import build_inventory as inventory_module  # noqa: PLC0415

        self.run_drive()
        survey.close_session(self.root, self.session)
        archive = self.root / survey.archive_root_for(self.session)
        selection = json.loads((archive / "selection.json").read_text(encoding="utf-8"))
        selection["entries"][0].pop("view_id")
        (archive / "selection.json").write_text(
            json.dumps(selection, ensure_ascii=False), encoding="utf-8"
        )
        with self.assertRaises(inventory_module.InventoryError) as caught:
            inventory_module.build_inventory(self.root)
        self.assertIn("缺 view_id", str(caught.exception))


class ParkedObstacleMarginTest(SurveyCase):
    """BC-SURVEY-8：三轴各向外 4 m 的闭集扩张；三轴同时命中才拒绝。"""

    OBSTACLE = {
        "scene_object_name": "synthetic",
        "min_x_m": 0.0, "max_x_m": 10.0,
        "min_y_m": 0.0, "max_y_m": 1.0,
        "min_z_m": 0.0, "max_z_m": 10.0,
    }

    def test_inside_all_three_expanded_intervals_is_rejected(self) -> None:
        self.assertFalse(
            survey._clear_of_obstacles((5.0, 5.0), 0.2, [self.OBSTACLE])
        )

    def test_outside_the_vertical_interval_is_accepted(self) -> None:
        """y 也扩 4 m：`surface_y` 落在 [min_y−4, max_y+4] 之外即通过。"""
        self.assertTrue(
            survey._clear_of_obstacles((5.0, 5.0), 20.0, [self.OBSTACLE])
        )
        self.assertTrue(
            survey._clear_of_obstacles((5.0, 5.0), -10.0, [self.OBSTACLE])
        )

    def test_the_margin_is_closed_on_every_axis(self) -> None:
        margin = contract.SURVEY_PARKED_OBSTACLE_MARGIN_M
        self.assertEqual(margin, 4.0)
        # 恰在扩张边界上 → 闭集 → 拒绝。
        self.assertFalse(
            survey._clear_of_obstacles((-margin, 5.0), 0.2, [self.OBSTACLE])
        )
        self.assertFalse(
            survey._clear_of_obstacles((5.0, 10.0 + margin), 0.2, [self.OBSTACLE])
        )
        self.assertFalse(
            survey._clear_of_obstacles((5.0, 5.0), 1.0 + margin, [self.OBSTACLE])
        )
        # 越过边界一点点 → 通过。
        self.assertTrue(
            survey._clear_of_obstacles((-margin - 0.001, 5.0), 0.2, [self.OBSTACLE])
        )


class WitnessAlgorithmTest(unittest.TestCase):
    """BC-SURVEY-12：分量选择规则被冻结（相交过滤 + `(area, box)` 最大）。"""

    def setUp(self) -> None:
        from tools.dist_data import bind_layout  # noqa: PLC0415

        self.bind_layout = bind_layout
        self.visible = (10.0, 10.0, 20.0, 20.0)

    def test_only_intersecting_components_are_candidates(self) -> None:
        components = [
            {"area": 999, "box": (100.0, 100.0, 200.0, 200.0)},
            {"area": 1, "box": (11.0, 11.0, 12.0, 12.0)},
        ]
        best = self.bind_layout.select_witness_component(components, self.visible)
        self.assertEqual(best["area"], 1)

    def test_equal_area_takes_the_lexicographically_larger_box(self) -> None:
        smaller = {"area": 4, "box": (10.0, 10.0, 12.0, 12.0)}
        larger = {"area": 4, "box": (12.0, 10.0, 14.0, 12.0)}
        for order in ([smaller, larger], [larger, smaller]):
            best = self.bind_layout.select_witness_component(order, self.visible)
            self.assertEqual(best["box"], larger["box"])

    def test_no_intersecting_component_returns_none(self) -> None:
        components = [{"area": 5, "box": (100.0, 100.0, 110.0, 110.0)}]
        self.assertIsNone(
            self.bind_layout.select_witness_component(components, self.visible)
        )

    def test_connectivity_is_four(self) -> None:
        self.assertEqual(self.bind_layout.WITNESS_CONNECTIVITY, 4)


class PlanIntegrityTest(DriveCase):
    """横扫查出的 fail-open：转场记录与重入终态不得走宽松回退。"""

    def test_drive_refuses_a_transition_record_without_reachable(self) -> None:
        plan_file = self.root / survey.plan_path_for(self.identity)
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
        plan["transitions"][0].pop("reachable")
        plan_file.write_text(json.dumps(plan), encoding="utf-8")
        survey.marker_path(self.root).unlink()
        survey.override_path(self.root).unlink()
        shutil.rmtree(self.root / survey.state_root_for(self.session))
        survey.prepare_session(self.root, self.session)
        _simulator, bridge = self.start_simulator()
        with self.assertRaises(survey.SurveyError) as caught:
            survey.drive_session(self.root, self.session, bridge)
        self.assertIn("reachable", str(caught.exception))

    def test_drive_refuses_a_kept_position_with_no_reachable_transition(self) -> None:
        plan_file = self.root / survey.plan_path_for(self.identity)
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
        plan["transitions"][0]["reachable"] = False
        plan_file.write_text(json.dumps(plan), encoding="utf-8")
        survey.marker_path(self.root).unlink()
        survey.override_path(self.root).unlink()
        shutil.rmtree(self.root / survey.state_root_for(self.session))
        survey.prepare_session(self.root, self.session)
        _simulator, bridge = self.start_simulator()
        with self.assertRaises(survey.SurveyError) as caught:
            survey.drive_session(self.root, self.session, bridge)
        self.assertIn("没有可达的转场", str(caught.exception))

    def _rewrite_selection_and_retree(self, mutate) -> Path:
        """改归档 selection 后用**生产函数**重算 tree.json，使归档自洽。

        不重算的话 `close` 会先在树摘要不符上 fail（那本身也是正确行为，见
        `ReentryTest.test_tree_mismatch_keeps_every_file`），测不到终态那一支。
        """
        archive = self.root / survey.archive_root_for(self.session)
        selection_path = archive / "selection.json"
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        mutate(selection)
        selection_path.write_text(
            json.dumps(selection, ensure_ascii=False), encoding="utf-8"
        )
        members = contract.survey_tree_members(archive)
        (archive / "tree.json").write_text(
            json.dumps(
                {
                    "schema_version": contract.SURVEY_TREE_SCHEMA,
                    "work_id": contract.SURVEY_WORK_ID,
                    "session_id": self.session,
                    "members": members,
                    "tree_sha256": contract.survey_tree_sha256(members),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return archive

    def test_reentry_refuses_a_selection_without_a_session_terminal(self) -> None:
        self.run_drive()
        survey.close_session(self.root, self.session)
        completion = self.root / survey.state_root_for(self.session) / "completion.json"
        completion.unlink()
        self._rewrite_selection_and_retree(
            lambda document: document.pop("session_terminal")
        )
        with self.assertRaises(survey.SurveyError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("session_terminal", str(caught.exception))
        self.assertFalse(completion.exists())

    def test_reentry_refuses_a_terminal_outside_the_closed_set(self) -> None:
        self.run_drive()
        survey.close_session(self.root, self.session)
        completion = self.root / survey.state_root_for(self.session) / "completion.json"
        completion.unlink()
        self._rewrite_selection_and_retree(
            lambda document: document.__setitem__(
                "session_terminal", "CLOSED_TOTALLY_FINE"
            )
        )
        with self.assertRaises(survey.SurveyError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("闭集", str(caught.exception))
        self.assertFalse(completion.exists())


class WitnessCentreContainmentTest(unittest.TestCase):
    """BC-SURVEY-15：中心命中必须半开 `x0 ≤ cx < x1 ∧ y0 ≤ cy < y1`。"""

    def setUp(self) -> None:
        from tools.dist_data import bind_layout, project_boxes  # noqa: PLC0415

        self.bind_layout = bind_layout
        self.project_boxes = project_boxes

    def _hit(self, centre, observed) -> bool:
        """复刻 `evaluate_parked_witness` 的中心命中判据（同一表达式）。"""
        return (
            observed[0] <= centre[0] < observed[2]
            and observed[1] <= centre[1] < observed[3]
        )

    def test_centre_exactly_on_the_right_edge_is_a_miss(self) -> None:
        self.assertFalse(self._hit((20.0, 15.0), (10.0, 10.0, 20.0, 20.0)))

    def test_centre_exactly_on_the_bottom_edge_is_a_miss(self) -> None:
        self.assertFalse(self._hit((15.0, 20.0), (10.0, 10.0, 20.0, 20.0)))

    def test_centre_exactly_on_the_left_or_top_edge_is_a_hit(self) -> None:
        self.assertTrue(self._hit((10.0, 15.0), (10.0, 10.0, 20.0, 20.0)))
        self.assertTrue(self._hit((15.0, 10.0), (10.0, 10.0, 20.0, 20.0)))
        self.assertTrue(self._hit((10.0, 10.0), (10.0, 10.0, 20.0, 20.0)))

    def test_the_production_expression_is_half_open(self) -> None:
        """直接读生产源码，确认 `x1/y1` 用的是 `<` 而不是 `<=`。"""
        import inspect  # noqa: PLC0415

        source = inspect.getsource(self.bind_layout.evaluate_parked_witness)
        self.assertIn("observed[0] <= centre[0] < observed[2]", source)
        self.assertIn("observed[1] <= centre[1] < observed[3]", source)
        self.assertNotIn("centre[0] <= observed[2]", source)
        self.assertNotIn("centre[1] <= observed[3]", source)

    def test_red_components_boxes_are_right_and_bottom_open(self) -> None:
        """右/下开的机检：单像素分量的框宽高恰为 1。"""
        components = [{"area": 1, "box": (5.0, 7.0, 6.0, 8.0)}]
        best = self.bind_layout.select_witness_component(
            components, (0.0, 0.0, 100.0, 100.0)
        )
        x0, y0, x1, y1 = best["box"]
        self.assertEqual((x1 - x0, y1 - y0), (1.0, 1.0))


class AcquisitionPinTest(DriveCase):
    """BC-SURVEY-14：钉子必须在每个生产入口把漂移挡下来。"""

    def _manifest_path(self) -> Path:
        return self.root / survey.state_root_for(self.session) / "manifest.json"

    def test_plan_and_manifest_both_carry_the_pin(self) -> None:
        pin = contract.survey_acquisition_sha256()
        plan = json.loads(
            (self.root / survey.plan_path_for(self.identity)).read_text(encoding="utf-8")
        )
        manifest = json.loads(self._manifest_path().read_text(encoding="utf-8"))
        self.assertEqual(plan["survey_acquisition_sha256"], pin)
        self.assertEqual(manifest["survey_acquisition_sha256"], pin)

    def test_drive_fails_closed_on_a_drifted_manifest_pin(self) -> None:
        path = self._manifest_path()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["survey_acquisition_sha256"] = "0" * 64
        path.write_text(json.dumps(manifest), encoding="utf-8")
        _simulator, bridge = self.start_simulator()
        with self.assertRaises(contract.SurveyContractError) as caught:
            survey.drive_session(self.root, self.session, bridge)
        self.assertIn("采集协议已漂移", str(caught.exception))

    def test_close_fails_closed_on_a_drifted_plan_pin(self) -> None:
        self.run_drive()
        plan_file = self.root / survey.plan_path_for(self.identity)
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
        plan["survey_acquisition_sha256"] = "0" * 64
        plan_file.write_text(json.dumps(plan), encoding="utf-8")
        # 同时更新 manifest 的 plan 哈希，隔离出「采集协议钉子」这一项。
        path = self._manifest_path()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["plan_sha256"] = survey.sha256_file(plan_file)
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(contract.SurveyContractError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("采集协议", str(caught.exception))

    def test_reentry_fails_closed_on_a_drifted_archived_pin(self) -> None:
        self.run_drive()
        survey.close_session(self.root, self.session)
        archive = self.root / survey.archive_root_for(self.session)
        path = archive / "session" / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["survey_acquisition_sha256"] = "0" * 64
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(survey.SurveyError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("采集协议已漂移", str(caught.exception))

    def test_prepare_refuses_a_plan_whose_pin_drifted(self) -> None:
        survey.marker_path(self.root).unlink()
        survey.override_path(self.root).unlink()
        shutil.rmtree(self.root / survey.state_root_for(self.session))
        plan_file = self.root / survey.plan_path_for(self.identity)
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
        plan["survey_acquisition_sha256"] = "0" * 64
        plan_file.write_text(json.dumps(plan), encoding="utf-8")
        with self.assertRaises(contract.SurveyContractError) as caught:
            survey.prepare_session(self.root, self.session)
        self.assertIn("采集协议已漂移", str(caught.exception))

    def test_s2_fails_closed_on_a_drifted_pin(self) -> None:
        from tools.dist_data import bind_layout  # noqa: PLC0415

        self.run_drive()
        survey.close_session(self.root, self.session)
        archive = self.root / survey.archive_root_for(self.session)
        path = archive / "session" / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["survey_acquisition_sha256"] = "0" * 64
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(bind_layout.LayoutError) as caught:
            bind_layout._survey_selection_rows(self.root, archive)
        self.assertIn("采集协议", str(caught.exception))

    def test_cli_converts_contract_domain_errors(self) -> None:
        """`drive`/`close` 经 `load_pinned_survey_plan` 会抛合同域错误；
        CLI 必须转成退出码，不能裸抛出去。"""
        path = self._manifest_path()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["survey_acquisition_sha256"] = "0" * 64
        path.write_text(json.dumps(manifest), encoding="utf-8")
        code = survey.main(
            ["--repo-root", str(self.root), "close", "--session", self.session]
        )
        self.assertEqual(code, 2)


class DiagnosticGateTest(SurveyCase):
    """BC-SURVEY-9：锚点在冻结表内不豁免计划有效性门。"""

    def test_diagnostic_refuses_an_anchor_whose_candidate_1_plan_is_invalid(self) -> None:
        # 锚点 5 穷举 135 个候选全部无效；`write_plan` 与诊断都必须拒绝。
        with self.assertRaises(survey.SurveyError) as caught:
            survey.write_plan(self.root, 5)
        self.assertIn(survey.ANCHOR_UNREACHABLE, str(caught.exception))
        # 诊断此前只试候选 1，且更早的版本连有效性都不查。
        with self.assertRaises(survey.SurveyError) as caught:
            survey.install_diagnostic(self.root, 5)
        self.assertIn(survey.ANCHOR_UNREACHABLE, str(caught.exception))
        self.assertIn("135", str(caught.exception))
        self.assertFalse(survey.override_path(self.root).exists())

    def test_diagnostic_still_installs_for_a_valid_anchor(self) -> None:
        result = survey.install_diagnostic(self.root, 1)
        self.assertEqual(result["anchor_index"], 1)
        self.assertTrue(survey.override_path(self.root).is_file())


class AnchorTableReachabilityTest(SurveyCase):
    """BC-SURVEY-16/18：按冻结顺序穷举每个锚点的**全部**候选。

    BC-SURVEY-18 把「全部停放候选」的闭集定为
    `tools/run_grounding_survey.py::parked_candidates` 的有序输出，并逐锚点
    钉住枚举计数。本用例按该闭集逐一求 plan：5/8 的 135/128 个成员必须全部
    无效，10 必须保持空集，1/2/3/4/6/7/9 必须保持候选 1 为首个合法 plan。
    """

    ENUMERATION_COUNTS = {
        1: 53, 2: 209, 3: 60, 4: 74, 5: 135,
        6: 248, 7: 62, 8: 128, 9: 217, 10: 0,
    }
    REACHABLE_SEQUENCE = (1, 2, 3, 4, 6, 7, 9)
    EXHAUSTIVELY_INVALID = (5, 8)
    EMPTY_CANDIDATE_SET = (10,)

    def _candidates(self, anchor: int) -> list:
        scenario = survey.load_default_scenario(self.root)
        x, z = survey.ANCHOR_INDEX[anchor]
        return survey.parked_candidates(
            self.root, (x, survey.ANCHOR_Y_M, z), scenario
        )

    def test_enumeration_counts_match_the_frozen_closed_set(self) -> None:
        for anchor, expected in sorted(self.ENUMERATION_COUNTS.items()):
            candidates = self._candidates(anchor)
            self.assertEqual(len(candidates), expected, anchor)
            # 连续 `candidate_index`，1..N，无洞。
            self.assertEqual(
                [item["candidate_index"] for item in candidates],
                list(range(1, expected + 1)),
                anchor,
            )

    def test_five_and_eight_are_invalid_across_every_enumerated_candidate(self) -> None:
        for anchor in self.EXHAUSTIVELY_INVALID:
            resolved = survey.resolve_anchor_plan(self.root, anchor, 1)
            self.assertFalse(resolved["reachable"], anchor)
            self.assertEqual(resolved["terminal"], survey.ANCHOR_UNREACHABLE, anchor)
            self.assertEqual(
                resolved["candidates_enumerated"], self.ENUMERATION_COUNTS[anchor]
            )
            # 穷举证明：被拒的候选数 == 枚举总数（没有提前退出）。
            self.assertEqual(
                len(resolved["candidates_rejected"]),
                self.ENUMERATION_COUNTS[anchor],
                anchor,
            )
            self.assertEqual(
                [row["candidate_index"] for row in resolved["candidates_rejected"]],
                list(range(1, self.ENUMERATION_COUNTS[anchor] + 1)),
                anchor,
            )
            with self.assertRaises(survey.SurveyError) as caught:
                survey.write_plan(self.root, anchor)
            self.assertIn(survey.ANCHOR_UNREACHABLE, str(caught.exception))

    def test_ten_has_an_empty_candidate_set(self) -> None:
        for anchor in self.EMPTY_CANDIDATE_SET:
            self.assertEqual(self._candidates(anchor), [])
            resolved = survey.resolve_anchor_plan(self.root, anchor, 1)
            self.assertFalse(resolved["reachable"])
            self.assertEqual(resolved["candidates_enumerated"], 0)
            self.assertEqual(resolved["terminal"], survey.ANCHOR_UNREACHABLE)

    def test_seven_reachable_anchors_take_candidate_one(self) -> None:
        for anchor in self.REACHABLE_SEQUENCE:
            resolved = survey.resolve_anchor_plan(self.root, anchor, 1)
            self.assertTrue(resolved["reachable"], anchor)
            self.assertEqual(resolved["candidate_index"], 1, anchor)
            self.assertEqual(resolved["candidates_rejected"], [], anchor)
            plan = resolved["plan"]
            self.assertGreaterEqual(
                plan["survey_position_count"],
                contract.SURVEY_MIN_KEPT_SURVEY_POSITIONS,
                anchor,
            )
            self.assertGreaterEqual(
                plan["witness_view_count"], contract.SURVEY_MIN_WITNESS_VIEWS, anchor
            )

    def test_the_reachable_sequence_follows_the_frozen_anchor_order(self) -> None:
        sequence = survey.resolve_anchor_sequence(self.root, 1)
        self.assertEqual(sequence["reachable_sequence"], list(self.REACHABLE_SEQUENCE))
        self.assertEqual(
            [row["anchor_index"] for row in sequence["dropped"]], [5, 8, 10]
        )
        for row in sequence["dropped"]:
            self.assertEqual(row["terminal"], survey.ANCHOR_UNREACHABLE)

    def test_precomputed_candidates_change_nothing(self) -> None:
        """穷举求解复用同一份候选枚举；传与不传必须逐字相同。"""
        candidates = self._candidates(1)
        without = survey.build_plan(self.root, 1, 1, 1)
        with_cache = survey.build_plan(self.root, 1, 1, 1, candidates=candidates)
        self.assertEqual(
            json.dumps(without, sort_keys=True), json.dumps(with_cache, sort_keys=True)
        )

    def test_unreachable_anchor_creates_no_identity(self) -> None:
        with self.assertRaises(survey.SurveyError):
            survey.write_plan(self.root, 5)
        self.assertEqual(
            sorted((self.root / "config").glob("scenario.p1-vlm-survey-*.json")), []
        )
        self.assertFalse((self.root / survey.PLAN_DIRECTORY).exists())


class WitnessScanExtentTest(SurveyCase):
    """BC-SURVEY-12：整帧扫描不得建立在 sidecar 自述尺寸上。"""

    def setUp(self) -> None:
        super().setUp()
        try:
            import PIL  # noqa: F401,PLC0415
        except ImportError:
            self.skipTest("本解释器没有 Pillow；改用钉死环境 .venv-yoloe/bin/python")

    def _source(self, frame_id: str, size: tuple[int, int]):
        from PIL import Image  # noqa: PLC0415
        from tools.dist_data import pixel_source  # noqa: PLC0415

        image = Image.new("RGB", size, (30, 30, 30))
        for x in range(40, 60):
            for y in range(30, 44):
                if x < size[0] and y < size[1]:
                    image.putpixel((x, y), (230, 20, 20))
        path = self.root / frame_id
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, format="JPEG", quality=95)
        return pixel_source.ArchivePixelSource(self.root)

    def test_understated_dimensions_fail_closed_instead_of_cropping(self) -> None:
        from tools.dist_data import bind_layout  # noqa: PLC0415

        frame_id = "runtime/frames.scan-extent/frame_0000000000.jpg"
        pixels = self._source(frame_id, (64, 48))
        found = bind_layout.red_components(pixels, frame_id, 64, 48)
        self.assertTrue(found, "真实画幅下应当找到红色分量")
        # 谎报偏小：此前会静默变成左上角裁窗，整辆红车漏掉且不抛异常。
        with self.assertRaises(bind_layout.LayoutError) as caught:
            bind_layout.red_components(pixels, frame_id, 32, 24)
        self.assertIn("sidecar 画幅与帧字节不符", str(caught.exception))

    def test_overstated_dimensions_also_fail_closed(self) -> None:
        from tools.dist_data import bind_layout  # noqa: PLC0415

        frame_id = "runtime/frames.scan-extent/frame_0000000001.jpg"
        pixels = self._source(frame_id, (64, 48))
        with self.assertRaises(bind_layout.LayoutError):
            bind_layout.red_components(pixels, frame_id, 128, 96)

    def test_connectivity_is_actually_consumed(self) -> None:
        """此前 `WITNESS_CONNECTIVITY` 是装饰性的：改成 8 也没人会发现。"""
        from tools.dist_data import bind_layout  # noqa: PLC0415

        frame_id = "runtime/frames.scan-extent/frame_0000000002.jpg"
        pixels = self._source(frame_id, (64, 48))
        original = bind_layout.WITNESS_CONNECTIVITY
        try:
            bind_layout.WITNESS_CONNECTIVITY = 8
            with self.assertRaises(bind_layout.LayoutError) as caught:
                bind_layout.red_components(pixels, frame_id, 64, 48)
            self.assertIn("4-邻接", str(caught.exception))
        finally:
            bind_layout.WITNESS_CONNECTIVITY = original
        self.assertTrue(bind_layout.red_components(pixels, frame_id, 64, 48))


class ArchivedPinnedPlanTest(DriveCase):
    """BC-SURVEY-14 两条 fail-open：重入与 `verify` 的完整所钉 plan 核对。

    只核对采集协议钉子不够——plan 路径、plan 字节 SHA 与 plan 侧的钉子同样
    要在**释放现场 / 补写 completion 之前**过一遍。
    """

    def _archive(self) -> Path:
        return self.root / survey.archive_root_for(self.session)

    def _closed(self) -> Path:
        self.run_drive()
        survey.close_session(self.root, self.session)
        return self._archive()

    def _drop_completion(self) -> Path:
        path = self.root / survey.state_root_for(self.session) / "completion.json"
        path.unlink()
        return path

    # --- 重入分支 1（completion 已在，源有残留） -----------------------------
    def test_reentry_with_completion_refuses_a_missing_plan(self) -> None:
        archive = self._closed()
        (self.root / survey.plan_path_for(self.identity)).unlink()
        with self.assertRaises(survey.SurveyError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("所钉 plan 核对失败", str(caught.exception))
        self.assertTrue((archive / "tree.json").is_file())

    def test_reentry_with_completion_refuses_drifted_plan_bytes(self) -> None:
        self._closed()
        plan_file = self.root / survey.plan_path_for(self.identity)
        plan_file.write_bytes(plan_file.read_bytes() + b" ")
        with self.assertRaises(survey.SurveyError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("哈希不符", str(caught.exception))

    def test_reentry_with_completion_refuses_a_drifted_plan_side_pin(self) -> None:
        self._closed()
        plan_file = self.root / survey.plan_path_for(self.identity)
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
        plan["survey_acquisition_sha256"] = "0" * 64
        plan_file.write_text(json.dumps(plan), encoding="utf-8")
        path = self._archive() / "session" / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["plan_sha256"] = survey.sha256_file(plan_file)
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(survey.SurveyError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("采集协议已漂移", str(caught.exception))

    def test_reentry_with_completion_refuses_a_tampered_plan_path(self) -> None:
        self._closed()
        path = self._archive() / "session" / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["plan_path"] = "config/elsewhere/plan.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(survey.SurveyError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("plan_path", str(caught.exception))

    # --- 重入分支 2（completion 缺失） ---------------------------------------
    def test_reentry_without_completion_refuses_a_missing_plan(self) -> None:
        self._closed()
        completion = self._drop_completion()
        (self.root / survey.plan_path_for(self.identity)).unlink()
        with self.assertRaises(survey.SurveyError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("所钉 plan 核对失败", str(caught.exception))
        # create-once completion 绝不能在核对失败后被补写。
        self.assertFalse(completion.exists())

    def test_reentry_without_completion_refuses_drifted_plan_bytes(self) -> None:
        self._closed()
        completion = self._drop_completion()
        plan_file = self.root / survey.plan_path_for(self.identity)
        plan_file.write_bytes(plan_file.read_bytes() + b"\n")
        with self.assertRaises(survey.SurveyError):
            survey.close_session(self.root, self.session)
        self.assertFalse(completion.exists())

    def test_reentry_without_completion_refuses_a_drifted_manifest_pin(self) -> None:
        self._closed()
        completion = self._drop_completion()
        path = self._archive() / "session" / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["survey_acquisition_sha256"] = "0" * 64
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(survey.SurveyError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("采集协议已漂移", str(caught.exception))
        self.assertFalse(completion.exists())

    # --- verify：零帧归档也必须走同一核对 ------------------------------------
    def _zero_frame_archive(self) -> Path:
        clock = VirtualClock()
        simulator = FakeSimulator(
            self.root, self.scenario, self.template, publish_frames=False
        )
        clock.simulator = simulator
        bridge = survey.RuntimeBridge(self.root, clock=clock.now, sleep=clock.sleep)
        result = survey.drive_session(self.root, self.session, bridge)
        self.assertEqual(result["terminal"], "ABORTED_NO_FRAMES")
        closed = survey.close_session(self.root, self.session)
        self.assertEqual(closed["terminal"], "CLOSED_ZERO_FRAMES")
        return self._archive()

    def test_verify_checks_the_pin_on_a_zero_frame_archive(self) -> None:
        archive = self._zero_frame_archive()
        self.assertFalse((archive / "selection.json").exists())
        survey.verify_session(self.root, self.session)  # happy path
        path = archive / "session" / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["survey_acquisition_sha256"] = "0" * 64
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(survey.SurveyError) as caught:
            survey.verify_session(self.root, self.session)
        self.assertIn("采集协议已漂移", str(caught.exception))

    def test_verify_refuses_a_missing_plan_on_a_zero_frame_archive(self) -> None:
        self._zero_frame_archive()
        (self.root / survey.plan_path_for(self.identity)).unlink()
        with self.assertRaises(survey.SurveyError) as caught:
            survey.verify_session(self.root, self.session)
        self.assertIn("所钉 plan 核对失败", str(caught.exception))

    def test_verify_refuses_drifted_plan_bytes_on_a_zero_frame_archive(self) -> None:
        self._zero_frame_archive()
        plan_file = self.root / survey.plan_path_for(self.identity)
        plan_file.write_bytes(plan_file.read_bytes() + b" ")
        with self.assertRaises(survey.SurveyError) as caught:
            survey.verify_session(self.root, self.session)
        self.assertIn("哈希不符", str(caught.exception))

    def test_verify_still_checks_the_pin_on_a_framed_archive(self) -> None:
        archive = self._closed()
        survey.verify_session(self.root, self.session)
        path = archive / "session" / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["survey_acquisition_sha256"] = "0" * 64
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(survey.SurveyError) as caught:
            survey.verify_session(self.root, self.session)
        self.assertIn("采集协议已漂移", str(caught.exception))


class C1UnmetTest(DriveCase):
    """`C1@stageA` 判不满足的 BC-2 / BC-16 与关注项 1 / 2 的具名回归。"""

    # --- BC-SURVEY-2：零帧 close 必须证明一条控制指令都没发过 ---------------
    def test_drive_log_records_the_command_count(self) -> None:
        result = self.run_drive()
        log = survey._drive_log(self.root, self.session)
        self.assertGreater(log["commands_issued"], 0)
        self.assertEqual(log["commands_issued"], result["commands_issued"])

    def test_refused_drive_records_zero_commands(self) -> None:
        result = self.run_drive(publish_audit=False)
        self.assertEqual(result["terminal"], "DRIVE_REFUSED_AUDIT")
        self.assertEqual(result["commands_issued"], 0)
        self.assertTrue(
            survey.drive_log_is_pre_command_only(
                survey._drive_log(self.root, self.session)
            )
        )

    def test_zero_frame_close_refuses_a_log_that_issued_commands(self) -> None:
        """终态在接受集内还不够：日志必须自证零控制指令。

        构造一份终态 `ABORTED_NO_FRAMES`、但 `commands_issued > 0` 的日志——
        修复前 `close` 只看首行终态，会直接放行。
        """
        self.run_drive()
        path = self.root / survey.state_root_for(self.session) / "drive_log.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        header = json.loads(lines[0])
        header["terminal"] = "ABORTED_NO_FRAMES"
        self.assertGreater(header["commands_issued"], 0)
        path.write_text(
            "\n".join([json.dumps(header, ensure_ascii=False)] + lines[1:]) + "\n",
            encoding="utf-8",
        )
        for frame in sorted((self.root / "runtime" / "frames").iterdir()):
            frame.unlink()
        with self.assertRaises(survey.SurveyError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("已发出控制指令", str(caught.exception))

    def test_zero_frame_close_refuses_a_log_without_the_command_count(self) -> None:
        """老形状（无 `commands_issued`）的日志不得蒙混过关。"""
        self.run_drive()
        path = self.root / survey.state_root_for(self.session) / "drive_log.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        header = json.loads(lines[0])
        header["terminal"] = "ABORTED_NO_FRAMES"
        header.pop("commands_issued")
        path.write_text(
            "\n".join([json.dumps(header, ensure_ascii=False)] + lines[1:]) + "\n",
            encoding="utf-8",
        )
        for frame in sorted((self.root / "runtime" / "frames").iterdir()):
            frame.unlink()
        with self.assertRaises(survey.SurveyError) as caught:
            survey.close_session(self.root, self.session)
        self.assertIn("已发出控制指令", str(caught.exception))

    # --- BC-SURVEY-16：备用锚点依序启用 -------------------------------------
    def test_backup_anchors_are_derived_from_the_projected_table(self) -> None:
        self.assertEqual(survey.BACKUP_ANCHORS, (9, 10))
        self.assertEqual(
            survey.BACKUP_ANCHORS,
            tuple(row[0] for row in contract.SURVEY_ANCHOR_TABLE[-2:]),
        )

    def test_primary_anchors_are_not_gated(self) -> None:
        for anchor in (1, 2, 8):
            survey.assert_anchor_enabled(self.root, anchor)

    def test_backup_anchor_is_refused_while_primaries_are_pending(self) -> None:
        survey.write_plan(self.root, 9)
        with self.assertRaises(survey.SurveyError) as caught:
            survey.assert_anchor_enabled(self.root, 9)
        message = str(caught.exception)
        self.assertIn("备用锚点 9 尚未启用", message)
        self.assertIn("1", message)

    def test_prepare_refuses_an_ungated_backup_anchor(self) -> None:
        survey.write_plan(self.root, 9)
        survey.marker_path(self.root).unlink()
        survey.override_path(self.root).unlink()
        session9 = survey.session_identity("p1-vlm-survey-a9-p1-c1", 1)
        with self.assertRaises(survey.SurveyError) as caught:
            survey.prepare_session(self.root, session9)
        self.assertIn("备用锚点 9 尚未启用", str(caught.exception))
        self.assertFalse(survey.override_path(self.root).exists())

    def test_unreachable_anchors_count_as_settled(self) -> None:
        for anchor in (5, 8, 10):
            self.assertEqual(
                survey.anchor_disposition(self.root, anchor),
                survey.ANCHOR_DISPOSITION_UNREACHABLE,
                anchor,
            )

    def test_a_closed_session_settles_its_anchor(self) -> None:
        self.assertEqual(
            survey.anchor_disposition(self.root, 1), survey.ANCHOR_DISPOSITION_PENDING
        )
        self.run_drive()
        survey.close_session(self.root, self.session)
        self.assertEqual(
            survey.anchor_disposition(self.root, 1), survey.ANCHOR_DISPOSITION_CLOSED
        )

    # --- 关注项 1：达成率分母来自计划，不是实际完成的窗 ----------------------
    def test_achievement_denominator_comes_from_the_plan(self) -> None:
        planned = survey.planned_view_counts(self.plan)
        self.assertEqual(
            planned,
            (
                sum(1 for p in self.plan["positions"]
                    for v in p["views"] if v["kind"] == "survey"),
                sum(1 for p in self.plan["positions"]
                    for v in p["views"] if v["kind"] == "witness"),
            ),
        )
        # 只交出一个已达成的窗：修复前分母 = 1 → 达成率 1.0；修复后分母是计划数。
        position = self.plan["positions"][0]
        view = next(v for v in position["views"] if v["kind"] == "survey")
        window = {
            "view_id": view["view_id"],
            "position_id": position["position_id"],
            "kind": "survey",
            "position_world_m": list(position["world_m"]),
            "look_at_world_m": list(view["look_at_world_m"]),
            "frame_window": [None, None],
            "min_valid_frames": 0,
        }
        result = survey.classify_frames(
            [window], {}, self._legal_view_ids(), planned
        )
        self.assertEqual(result["planned_survey_views"], planned[0])
        self.assertEqual(result["executed_survey_views"], 1)
        self.assertLess(result["achievement_rate"], 1.0)
        self.assertAlmostEqual(result["achievement_rate"], 1 / planned[0])

    def test_skipped_views_cannot_inflate_the_rate(self) -> None:
        planned = survey.planned_view_counts(self.plan)
        self.assertGreater(planned[0], 1)
        result = survey.classify_frames([], {}, self._legal_view_ids(), planned)
        self.assertEqual(result["planned_survey_views"], planned[0])
        self.assertEqual(result["executed_survey_views"], 0)
        self.assertEqual(result["achievement_rate"], 0.0)


class TentativeWitnessComparisonTest(DriveCase):
    """关注项 2：S2 重算的权威结论必须与 completion 的临时结论比对，不等即硬错误。"""

    def setUp(self) -> None:
        super().setUp()
        from tools.dist_data import bind_layout

        self.bind_layout = bind_layout
        self.run_drive()
        survey.close_session(self.root, self.session)
        self.archive = self.root / survey.archive_root_for(self.session)
        self.record = {
            "partition_id": f"{self.session}|sha",
            "scenario_path": survey.scenario_path_for(self.identity),
        }
        self.frame_paths = [
            p.relative_to(self.root).as_posix()
            for p in sorted((self.archive / "frames").glob("frame_*.jpg"))
        ]
        self.base = self.bind_layout.load_base_geometry(self.root)["instances"]

    def _validate(self):
        return self.bind_layout.validate_survey_partition(
            self.root, self.record, self.frame_paths,
            [self.archive.relative_to(self.root).as_posix()],
            self.base, _NoPixels(),
        )

    def test_matching_tentative_and_authoritative_pass(self) -> None:
        result = self._validate()
        self.assertIn("witness", result)

    def test_a_mismatched_tentative_verdict_is_a_hard_error(self) -> None:
        path = self.root / survey.state_root_for(self.session) / "completion.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["tentative_witness"]["verdict"] = "WITNESS_PASS"
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(self.bind_layout.LayoutError) as caught:
            self._validate()
        self.assertIn("不等", str(caught.exception))

    def test_a_missing_tentative_verdict_is_a_hard_error(self) -> None:
        path = self.root / survey.state_root_for(self.session) / "completion.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["tentative_witness"] = None
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(self.bind_layout.LayoutError) as caught:
            self._validate()
        self.assertIn("未记录临时证人结论", str(caught.exception))
