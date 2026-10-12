#!/usr/bin/env python3
"""表 A 三态派生的具名回归（AC-2）。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_sft.three_state import (  # noqa: E402
    DYNAMIC_TARGET_ID,
    STATES,
    ObjectRecord,
    three_state,
)


def obj(object_id, class_word="car", color_word=None, referable=True, definite=False):
    return ObjectRecord(
        object_id=object_id,
        class_word=class_word,
        color_word=color_word,
        referable=referable,
        status="OK",
        visible_norm_xywh=[0.1, 0.1, 0.2, 0.2],
        definite=definite,
    )


class ThreeStateTests(unittest.TestCase):
    def test_rule_one_and_six_states(self) -> None:
        car = {"class": "car"}
        red_car = {"class": "car", "color": "red"}
        target = obj(DYNAMIC_TARGET_ID, "car", "red", referable=False, definite=True)

        # 1 none：冲突集为空。
        self.assertEqual(three_state([obj("t", "taxi")], car).state, "none")
        # 2 unique：C = M 且 |M| = 1。
        result = three_state([obj("a"), obj("t", "taxi")], car)
        self.assertEqual((result.state, result.target_object_ids), ("unique", ("a",)))
        # 3 ambiguous：2 ≤ |M| ≤ 4，目标按 object_id 升序。
        result = three_state([obj("b"), obj("a")], car)
        self.assertEqual((result.state, result.target_object_ids), ("ambiguous", ("a", "b")))
        # 4 gray_overflow：|M| ≥ 5 排除。
        self.assertEqual(three_state([obj(f"c{i}") for i in range(5)], car).state, "gray_overflow")
        # 5 gray_definite_plus_uncertain：有确证但 C ≠ M（非 OK 同类车在 C 内）。
        result = three_state([obj("a"), obj("x", referable=False)], car)
        self.assertEqual(result.state, "gray_definite_plus_uncertain")
        self.assertEqual(result.target_object_ids, ())
        self.assertEqual(result.definite_ids, ("a",))
        # 6 gray_uncertain_none：M 为空但 C 非空（不确证不存在，不标 none）。
        result = three_state([obj("x", referable=False)], car)
        self.assertEqual((result.state, result.definite_ids), ("gray_uncertain_none", ()))

        # 规则 ①：已绑定且框有效的目标车并入 M（它自身 referable=False）。
        self.assertEqual(three_state([target], car).state, "unique")
        self.assertEqual(three_state([target], red_car).state, "unique")
        result = three_state([obj("a"), target], car)
        self.assertEqual((result.state, result.target_object_ids), ("ambiguous", ("a", DYNAMIC_TARGET_ID)))
        # 未标 definite（未绑定/缺框/退化）时不并入：只剩不确证 → 灰区。
        undecided = obj(DYNAMIC_TARGET_ID, "car", "red", referable=False, definite=False)
        self.assertEqual(three_state([undecided], car).state, "gray_uncertain_none")
        self.assertEqual(three_state([obj("a"), undecided], car).state, "gray_definite_plus_uncertain")
        # 规则 ① 不改变目录车对其他类 noun 的判定。
        self.assertEqual(three_state([obj("t", "taxi"), target], {"class": "taxi"}).state, "unique")
        # 目标车即便可指称也不重复计数（集合并）。
        referable_target = obj(DYNAMIC_TARGET_ID, "car", "red", referable=True, definite=True)
        self.assertEqual(three_state([referable_target], car).state, "unique")
        # 颜色未验证（color_word=None）对 class noun 无影响、对 color noun 是灰区。
        unverified = obj("u", "car", None)
        self.assertEqual(three_state([unverified], car).state, "unique")
        self.assertEqual(three_state([unverified], red_car).state, "gray_uncertain_none")
        # 未知类别阻断体：class_word=None 通配冲突 → 任何 class noun 灰区。
        unknown = obj("k", None, None, referable=False)
        self.assertEqual(three_state([obj("a"), unknown], car).state, "gray_definite_plus_uncertain")
        self.assertEqual(three_state([unknown], car).state, "gray_uncertain_none")
        # 六个状态都在闭集内。
        self.assertEqual(len(STATES), 6)


if __name__ == "__main__":
    unittest.main()
