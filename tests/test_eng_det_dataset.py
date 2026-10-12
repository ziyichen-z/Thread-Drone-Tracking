"""P1-ENG-FAST-002 AC-1：标签规则、三域断言与 §3.1.2 分层抽查（AR2-1 释义）的具名反例。

全部是纯函数合成输入（S3 记录形状取自帧目录首条实读），不读数据根、不跑模型。
"""

from __future__ import annotations

import unittest

from tools.eng_det import common, dataset, spotcheck


def vehicle(object_id, status, xyxy, depth=40.0):
    return {
        "object_id": object_id,
        "status": status,
        "visible_px": list(xyxy) if xyxy is not None else None,
        "camera_depth_m": depth,
        "is_phantom": status == "PHANTOM",
    }


def entry(objects, *, target_px=None, target_in_view=False, bound=True, frame_id="runtime/x/frame_0000000001.jpg"):
    blocking = [o["object_id"] for o in objects]
    if target_in_view:
        blocking.append(dataset.DYNAMIC_TARGET_ID)
    return {
        "frame_id": frame_id,
        "family": "p1-vlm-survey-a2-p1-c1-s1",
        "blocking": blocking,
        "objects": objects,
        "target_blocker_px": target_px,
        "target_source_bound": bound,
        "layout_binding_valid": True,
        "sidecar_complete": True,
    }


class LabelRuleTests(unittest.TestCase):
    def test_non_ok_status_at_least_12px_is_positive(self):
        labels = dataset.label_entry(
            entry(
                [
                    vehicle("Vehicle_Car_color01", "EXCLUDED_OCCLUDED", (100, 100, 140, 130)),
                    vehicle("Vehicle_Car_color02", "TRUNCATED", (0, 200, 20, 240)),
                    vehicle("Vehicle_Car_color03", "TOO_SMALL", (300, 300, 330, 330)),
                    vehicle("Vehicle_Car_color04", "OK", (400, 100, 460, 160)),
                ]
            ),
            "a2",
        )
        statuses = sorted(p["status"] for p in labels["positives"])
        self.assertEqual(statuses, ["EXCLUDED_OCCLUDED", "OK", "TOO_SMALL", "TRUNCATED"])
        self.assertTrue(all(p["cls"] == common.CLASS_VEHICLE for p in labels["positives"]))

    def test_short_side_11px_is_ignore_not_positive(self):
        labels = dataset.label_entry(entry([vehicle("Vehicle_Bus", "OK", (10, 10, 60, 21))]), "a2")
        self.assertEqual(labels["positives"], [])
        self.assertEqual([i["why"] for i in labels["ignores"]], ["i_small"])

    def test_phantom_with_box_is_ignore_ii_and_non_vehicle_skipped(self):
        labels = dataset.label_entry(
            entry(
                [
                    vehicle("phantom:Vehicle_Car_color03@1,2", "PHANTOM", (50, 50, 90, 90)),
                    vehicle("Building_Stadium", "OK", (0, 0, 640, 480)),
                ]
            ),
            "a2",
        )
        self.assertEqual(labels["positives"], [])
        self.assertEqual([i["why"] for i in labels["ignores"]], ["ii_phantom"])

    def test_not_in_view_has_no_box_anywhere(self):
        labels = dataset.label_entry(entry([vehicle("Vehicle_Taxi", "NOT_IN_VIEW", None)]), "a2")
        self.assertEqual((labels["positives"], labels["ignores"]), ([], []))

    def test_frame_wildcard_frame_is_excluded_whole(self):
        labels = dataset.label_entry(
            entry([vehicle("Vehicle_Taxi", "OK", (100, 100, 200, 200))], target_in_view=True, target_px=None),
            "a2",
        )
        self.assertTrue(labels["excluded"])
        self.assertEqual(labels["exclusion_reason"], "MISSING_BOX")
        self.assertEqual((labels["positives"], labels["ignores"]), ([], []))
        unbound = dataset.label_entry(entry([], target_in_view=True, target_px=[1, 1, 50, 50], bound=False), "a2")
        self.assertEqual(unbound["exclusion_reason"], "UNBOUND")

    def test_target_unbounded_frame_is_excluded_whole_q1(self):
        unbounded = entry([vehicle("Vehicle_Taxi", "OK", (100, 100, 200, 200))])
        unbounded["target_unbounded"] = True
        labels = dataset.label_entry(unbounded, "rate")
        self.assertTrue(labels["excluded"])
        self.assertEqual(labels["exclusion_reason"], dataset.EXCLUSION_TARGET_UNBOUNDED)
        self.assertEqual((labels["positives"], labels["ignores"]), ([], []))
        # 既有通配原因优先（计数不重复归因）；`target_unbounded=False` 不排除。
        both = entry([], target_in_view=True, target_px=None)
        both["target_unbounded"] = True
        self.assertEqual(dataset.label_entry(both, "a2")["exclusion_reason"], "MISSING_BOX")
        bounded = entry([vehicle("Vehicle_Taxi", "OK", (100, 100, 200, 200))])
        bounded["target_unbounded"] = False
        self.assertFalse(dataset.label_entry(bounded, "a2")["excluded"])

    def test_truth_flag_false_turns_target_into_ignore_q2(self):
        e = entry([], target_in_view=True, target_px=[100, 100, 140, 130])
        labels = dataset.label_entry(e, "demo-route", (), False)
        self.assertEqual(labels["positives"], [])
        self.assertEqual([(i["why"], i["object_id"]) for i in labels["ignores"]], [("iv_truth_invisible", dataset.DYNAMIC_TARGET_ID)])
        self.assertEqual(labels["status_counts"], {"TARGET|ignore_iv": 1})

    def test_truth_flag_true_or_absent_keeps_original_rule_q2(self):
        e = entry([], target_in_view=True, target_px=[100, 100, 140, 130])
        for flag in (True, None):
            labels = dataset.label_entry(e, "demo-route", (), flag)
            self.assertEqual([p["cls"] for p in labels["positives"]], [common.CLASS_TARGET], flag)
            self.assertEqual(labels["ignores"], [])

    def test_truth_flag_only_for_demo_route_families_q2(self):
        flag, source = dataset.truth_visibility_flag("runtime/x/frame_0000000001.jpg", "p1-vlm-survey-a2-p1-c1-s1")
        self.assertEqual((flag, source), (None, "not_demo_route"))
        self.assertEqual(set(dataset.DEMO_ROUTE_FLAG_FAMILIES), {"detect-scout1", "m3-armA", "m3-armB"})

    def test_target_box_is_cropped_blocker_px(self):
        labels = dataset.label_entry(entry([], target_in_view=True, target_px=[600, 400, 700, 500]), "a2")
        (target,) = labels["positives"]
        self.assertEqual(target["cls"], common.CLASS_TARGET)
        self.assertAlmostEqual(target["box"][0] + target["box"][2], 1.0)
        self.assertAlmostEqual(target["box"][1] + target["box"][3], 1.0)

    def test_stratum_ignored_layer_absent_from_positives_across_groups(self):
        objects = [vehicle("Vehicle_Car_color01", "EXCLUDED_OCCLUDED", (100, 100, 140, 130))]
        layer = dataset.layer_of("vehicle", "EXCLUDED_OCCLUDED", "12-31")
        for group in ("a2", "survey-H", "rate"):
            labels = dataset.label_entry(entry(objects), group, [layer])
            self.assertEqual(labels["positives"], [])
            self.assertEqual([i["why"] for i in labels["ignores"]], ["iii_stratum"])
        target_layer = dataset.layer_of("target", "-", "12-31")
        labels = dataset.label_entry(entry([], target_in_view=True, target_px=[10, 10, 30, 30]), "a2", [target_layer])
        self.assertEqual(labels["positives"], [])
        self.assertEqual([i["why"] for i in labels["ignores"]], ["iii_stratum"])


def frame(domain, sha, atom, family, frame_id):
    return {"domain": domain, "sha256": sha, "atom": atom, "family": family, "frame_id": frame_id}


class DomainAssertionTests(unittest.TestCase):
    def base(self):
        return [
            frame("T", "t1", "atomT", "famT", "t/1.jpg"),
            frame("V", "v1", "atomD", "famV", "v/1.jpg"),
            frame("H", "h1", "atomH", "famH", "h/1.jpg"),
        ]

    def test_clean_domains_pass(self):
        result = dataset.assert_domains(self.base(), {"h1"}, {"h/1.jpg"})
        self.assertTrue(result["passed"])

    def test_h_frame_mixed_into_t_fails(self):
        frames = self.base() + [frame("T", "h1", "atomT", "famT", "t/2.jpg")]
        with self.assertRaises(dataset.DatasetFailure):
            dataset.assert_domains(frames, {"h1"}, {"h/1.jpg"})

    def test_h_atom_in_v_fails(self):
        frames = self.base() + [frame("V", "v2", "atomH", "famV", "v/2.jpg")]
        with self.assertRaises(dataset.DatasetFailure):
            dataset.assert_domains(frames, {"h1"}, {"h/1.jpg"})

    def test_v_frame_mixed_into_t_fails(self):
        frames = self.base() + [frame("T", "v1", "atomT", "famT", "t/3.jpg")]
        with self.assertRaises(dataset.DatasetFailure):
            dataset.assert_domains(frames, {"h1"}, {"h/1.jpg"})

    def test_v_family_in_t_fails(self):
        frames = self.base() + [frame("T", "t9", "atomD", "famV", "t/9.jpg")]
        with self.assertRaises(dataset.DatasetFailure):
            dataset.assert_domains(frames, {"h1"}, {"h/1.jpg"})

    def test_eval_frame_only_in_excluded_h_frame_fails_q1(self):
        frames = self.base()
        frames[2]["excluded"] = True
        with self.assertRaises(dataset.DatasetFailure):
            dataset.assert_domains(frames, {"h1"}, {"h/1.jpg"})

    def test_eval_frame_outside_h_fails(self):
        with self.assertRaises(dataset.DatasetFailure):
            dataset.assert_domains(self.base(), {"t1"}, {"t/1.jpg"})

    def test_expected_domain_table(self):
        self.assertEqual(dataset.expected_domain("train", "p1-vlm-survey-a2-p1-c1-s1"), "T")
        self.assertEqual(dataset.expected_domain("dev", "p1-vlm-survey-a7-p1-c1-s1"), "V")
        self.assertEqual(dataset.expected_domain("dev", "detect-scout1"), "T")
        self.assertEqual(dataset.expected_domain("test", "m3-armB"), "H")
        for family, domain in dataset.DOMAIN_OF_FAMILY.items():
            self.assertIn(domain, dataset.DOMAINS, family)


def candidates(layer_sizes):
    return {
        key: [{"frame_sha": f"{key}-sha-{i}", "object_id": f"obj-{i}", "frame_id": f"{key}/{i}.jpg"} for i in range(size)]
        for key, size in layer_sizes.items()
    }


class SpotcheckSamplingTests(unittest.TestCase):
    def test_round_robin_caps_at_300_with_every_layer_at_least_one(self):
        layers = {f"vehicle|OK|12-31|g{i:03d}": 20 for i in range(100)}
        chosen = spotcheck.sample_boxes(candidates(layers))
        self.assertEqual(len(chosen), spotcheck.TOTAL_MAX)
        per_layer = {key: sum(1 for c in chosen if c["layer_key"] == key) for key in layers}
        self.assertEqual(set(per_layer.values()), {3})

    def test_per_layer_max_eight_and_small_layers_take_all(self):
        chosen = spotcheck.sample_boxes(candidates({"a|x|12-31|g": 20, "b|y|12-31|g": 2}))
        counts = {key: sum(1 for c in chosen if c["layer_key"] == key) for key in ("a|x|12-31|g", "b|y|12-31|g")}
        self.assertEqual(counts, {"a|x|12-31|g": 8, "b|y|12-31|g": 2})

    def test_more_than_300_layers_is_not_evaluable(self):
        with self.assertRaises(spotcheck.SpotcheckNotEvaluable):
            spotcheck.sample_boxes(candidates({f"l|s|12-31|g{i}": 1 for i in range(301)}))

    def test_order_is_sha_keyed_and_reproducible(self):
        pool = candidates({"a|x|12-31|g": 12})
        first = [c["object_id"] for c in spotcheck.sample_boxes(pool)]
        reversed_pool = {k: list(reversed(v)) for k, v in pool.items()}
        self.assertEqual(first, [c["object_id"] for c in spotcheck.sample_boxes(reversed_pool)])
        expected = sorted(pool["a|x|12-31|g"], key=lambda c: spotcheck.order_key("a|x|12-31|g", c["frame_sha"], c["object_id"]))
        self.assertEqual(first, [c["object_id"] for c in expected[:8]])

    def test_identical_frame_sha_boxes_are_not_sampled_twice(self):
        pool = {"a|x|12-31|g": [{"frame_sha": "same", "object_id": "o", "frame_id": f"f{i}.jpg"} for i in range(3)]}
        chosen = spotcheck.sample_boxes(pool)
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0]["frame_id"], "f0.jpg")


def sample(sample_id, layer_key):
    return {"sample_id": sample_id, "layer_key": layer_key}


class SpotcheckDecisionTests(unittest.TestCase):
    frames = [{"sample_id": f"F{i}", "group": "g1" if i < 10 else "g2"} for i in range(20)]

    def frame_judgments(self, unlabeled_g1=0, unlabeled_g2=0):
        values = {}
        for i in range(20):
            count = unlabeled_g1 if i < 10 else unlabeled_g2
            values[f"F{i}"] = 1 if (i % 10) < count else 0
        return values

    def test_over_20_percent_ignores_layer_across_groups(self):
        samples = [sample(f"B{i}", "vehicle|TRUNCATED|32-63|a2") for i in range(4)]
        judgments = {"B0": "INVISIBLE", "B1": "OK", "B2": "OK", "B3": "OK"}
        result = spotcheck.decide(samples, judgments, self.frames, self.frame_judgments())
        self.assertEqual(result["stratum_ignored_layers"], ["vehicle|TRUNCATED|32-63"])
        self.assertEqual(result["layers"]["vehicle|TRUNCATED|32-63|a2"]["disposition"], "STRATUM_IGNORED")

    def test_ten_to_twenty_percent_is_flagged_and_loose_not_counted_bad(self):
        samples = [sample(f"B{i}", "vehicle|OK|>=64|a7") for i in range(8)] + [sample("B8", "vehicle|OK|>=64|a7"), sample("B9", "vehicle|OK|>=64|a7")]
        judgments = {f"B{i}": "OK" for i in range(10)}
        judgments.update({"B0": "WRONG", "B1": "LOOSE", "B2": "LOOSE"})
        result = spotcheck.decide(samples, judgments, self.frames, self.frame_judgments())
        layer = result["layers"]["vehicle|OK|>=64|a7"]
        self.assertEqual((layer["bad_rate"], layer["disposition"]), (0.1, "STRATUM_FLAGGED"))
        self.assertEqual(result["stratum_ignored_layers"], [])
        self.assertEqual(result["loose_total"], 2)

    def test_missing_judgment_is_not_evaluable(self):
        samples = [sample("B0", "vehicle|OK|>=64|a7"), sample("B1", "vehicle|OK|>=64|a7")]
        with self.assertRaises(spotcheck.SpotcheckNotEvaluable):
            spotcheck.decide(samples, {"B0": "OK"}, self.frames, self.frame_judgments())
        with self.assertRaises(spotcheck.SpotcheckNotEvaluable):
            spotcheck.decide(samples, {"B0": "OK", "B1": "MAYBE"}, self.frames, self.frame_judgments())

    def test_unlabeled_risk_above_ten_percent(self):
        samples = [sample("B0", "vehicle|OK|>=64|a7")]
        result = spotcheck.decide(samples, {"B0": "OK"}, self.frames, self.frame_judgments(unlabeled_g1=1, unlabeled_g2=2))
        self.assertEqual(result["unlabeled_risk_groups"], ["g2"])
        self.assertIsNone(result["groups"]["g1"]["flag"])


class TargetResampleTests(unittest.TestCase):
    """Q-2 CLARIFY：目标层按 AR2-1 原算法重抽一次；车辆层沿用原抽查。"""

    def test_candidates_only_retained_target_positives(self):
        rows = [
            {
                "frame_id": "f1", "sha256": "s1", "domain": "T", "excluded": False,
                "positives": [
                    {"cls": 1, "object_id": "dynamic-target", "stratum": "target|-|12-31|demo-route", "box": [0, 0, 0.1, 0.1], "status": "-", "side_px": 20.0},
                    {"cls": 0, "object_id": "Vehicle_A", "stratum": "vehicle|OK|12-31|demo-route", "box": [0, 0, 0.1, 0.1], "status": "OK", "side_px": 20.0},
                ],
                "ignores": [],
            },
            {
                "frame_id": "f2", "sha256": "s2", "domain": "T", "excluded": True,
                "positives": [{"cls": 1, "object_id": "dynamic-target", "stratum": "target|-|12-31|rate", "box": [0, 0, 0.1, 0.1], "status": "-", "side_px": 20.0}],
                "ignores": [],
            },
            {
                "frame_id": "f3", "sha256": "s3", "domain": "T", "excluded": False, "positives": [],
                "ignores": [{"box": [0, 0, 0.1, 0.1], "why": "iv_truth_invisible", "object_id": "dynamic-target"}],
            },
        ]
        pool = spotcheck.target_candidates(rows)
        self.assertEqual(list(pool), ["target|-|12-31|demo-route"])
        self.assertEqual([c["frame_id"] for c in pool["target|-|12-31|demo-route"]], ["f1"])

    def test_disposition_ignores_target_layer_and_keeps_vehicle_layers(self):
        samples = [sample(f"T{i}", "target|-|12-31|demo-route") for i in range(4)] + [sample("T9", "target|-|>=64|a7")]
        judgments = {"T0": "INVISIBLE", "T1": "OK", "T2": "OK", "T3": "OK", "T9": "OK"}
        result = spotcheck.target_resample_disposition(samples, judgments, ["vehicle|TRUNCATED|12-31"])
        self.assertEqual(result["target_ignored_layers"], ["target|-|12-31"])
        self.assertEqual(result["effective_stratum_ignored_layers"], ["target|-|12-31", "vehicle|TRUNCATED|12-31"])

    def test_clean_resample_ignores_no_target_layer(self):
        samples = [sample(f"T{i}", "target|-|12-31|demo-route") for i in range(8)]
        judgments = {f"T{i}": "OK" for i in range(8)}
        judgments["T0"] = "INVISIBLE"  # 1/8 = 12.5% → FLAGGED，不 ignore
        result = spotcheck.target_resample_disposition(samples, judgments, [])
        self.assertEqual(result["target_ignored_layers"], [])
        self.assertEqual(result["stratum_flagged"], ["target|-|12-31|demo-route"])

    def test_non_target_sample_or_non_vehicle_carryover_is_not_evaluable(self):
        with self.assertRaises(spotcheck.SpotcheckNotEvaluable):
            spotcheck.target_resample_disposition([sample("B0", "vehicle|OK|>=64|a7")], {"B0": "OK"}, [])
        with self.assertRaises(spotcheck.SpotcheckNotEvaluable):
            spotcheck.target_resample_disposition([sample("T0", "target|-|>=64|a7")], {"T0": "OK"}, ["target|-|12-31"])
        with self.assertRaises(spotcheck.SpotcheckNotEvaluable):
            spotcheck.target_resample_disposition([sample("T0", "target|-|>=64|a7")], {}, [])


class SubsampleTests(unittest.TestCase):
    def test_every_second_frame_per_session_in_time_order_and_exclusion_after(self):
        rows = [
            {"session": "s1", "sim_t": t, "frame_id": f"s1/{t}", "excluded": t == 0.4}
            for t in (0.8, 0.0, 0.2, 0.4, 0.6)
        ] + [{"session": "s2", "sim_t": 0.0, "frame_id": "s2/0", "excluded": False}]
        chosen = [r["frame_id"] for r in dataset.subsample(rows, 2)]
        self.assertEqual(chosen, ["s1/0.0", "s1/0.8", "s2/0"])


if __name__ == "__main__":
    unittest.main()
