#!/usr/bin/env python3
"""P1-ENG-FAST-001 AC-4：P2a 帧对资格（同会话、±0.2 s、同类 ≥2）、确定性抽样与 margin 口径。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_fast import margin  # noqa: E402


def veh(object_id: str, class_word: str, x: float) -> dict:
    return {"object_id": object_id, "class_word": class_word, "box": [x, 0.1, 0.1, 0.1]}


def row(family: str, vehicles: list) -> dict:
    return {"family": family, "usable": True, "vehicles": vehicles}


class Pairs(unittest.TestCase):
    def setUp(self) -> None:
        self.index = {
            "s1/f0.jpg": row("fam", [veh("a", "bus", 0.1), veh("b", "bus", 0.5), veh("c", "taxi", 0.8)]),
            "s1/f1.jpg": row("fam", [veh("a", "bus", 0.12), veh("b", "bus", 0.52)]),
            "s1/f2.jpg": row("fam", [veh("a", "bus", 0.14)]),  # 同类只剩 a：无「其他」→ 不成对
            "s2/f0.jpg": row("fam", [veh("a", "bus", 0.1), veh("b", "bus", 0.5)]),
        }
        self.times = {"s1/f0.jpg": 0.0, "s1/f1.jpg": 1.15, "s1/f2.jpg": 5.3, "s2/f0.jpg": 1.0}

    def test_eligibility(self) -> None:
        pairs = margin.eligible_pairs(self.index, self.times, 1.0)
        # f0→f1（dt 1.15，在 ±0.2 内）：a、b 各一对；s2 的帧与 s1 不同会话，不配对。
        self.assertEqual(sorted((p["anchor_frame"], p["later_frame"], p["object_id"]) for p in pairs),
                         [("s1/f0.jpg", "s1/f1.jpg", "a"), ("s1/f0.jpg", "s1/f1.jpg", "b")])
        self.assertEqual(margin.eligible_pairs(self.index, self.times, 5.0), [])  # f2 只有 1 辆 bus
        self.assertEqual(margin.eligible_pairs(self.index, {**self.times, "s1/f1.jpg": 1.25}, 1.0), [])  # 超出容差

    def test_selection_is_deterministic_and_capped(self) -> None:
        pairs = margin.eligible_pairs(self.index, self.times, 1.0)
        self.assertEqual(margin.select_pairs(pairs, cap=1), margin.select_pairs(list(reversed(pairs)), cap=1))
        self.assertEqual(len(margin.select_pairs(pairs, cap=1)), 1)

    def test_margin_and_crop_invalid(self) -> None:
        pairs = margin.eligible_pairs(self.index, self.times, 1.0)
        vectors = {
            ("s1/f0.jpg", 0.1): (1.0, 0.0),
            ("s1/f1.jpg", 0.12): (0.8, 0.6),
            ("s1/f1.jpg", 0.52): (0.6, 0.8),
            ("s1/f0.jpg", 0.5): None,  # b 的锚裁图无效
        }

        def embed(path, box):
            return vectors.get((path, round(box[0], 2)))

        def cosine(left, right):
            return sum(a * b for a, b in zip(left, right))

        scored = {r["object_id"]: r for r in margin.score_pairs(pairs, embed, cosine)}
        self.assertEqual(scored["a"]["status"], "OK")
        self.assertAlmostEqual(scored["a"]["margin"], 0.8 - 0.6, places=6)
        self.assertEqual(scored["b"]["status"], "CROP_INVALID")
        summary = margin.summarize(list(scored.values()), {1.0: 2})
        entry = summary["1s"]
        self.assertEqual((entry["pairs"], entry["scored"], entry["crop_invalid"]), (2, 1, 1))
        self.assertEqual(entry["margin_ge_0_1"], 1)
        self.assertEqual(entry["self_ge_0_5"], 1)
        self.assertFalse(entry["meets_target_200"])


if __name__ == "__main__":
    unittest.main()
