#!/usr/bin/env python3
"""表 B 解析器的具名回归（AC-4）。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_sft import parse  # noqa: E402


class ParserTests(unittest.TestCase):
    def test_error_closed_set_clears_status_pred(self) -> None:
        cases = [
            ("not json at all", parse.JSON_ERROR, None),
            ('["status"]', parse.SCHEMA_ERROR, None),
            # 非闭集状态词照样存进 raw_status（诊断用），但 status_pred 仍为 null。
            ('{"status": "maybe"}', parse.SCHEMA_ERROR, "maybe"),
            ('{"status": "none", "bbox_2d": [1, 2, 3, 4]}', parse.SCHEMA_ERROR, "none"),
            ('{"status": "unique"}', parse.SCHEMA_ERROR, "unique"),
            ('{"status": "unique", "bbox_2d": [1, 2, 3]}', parse.SCHEMA_ERROR, "unique"),
            ('{"status": "unique", "bbox_2d": [1, 2, 3.5, 4]}', parse.SCHEMA_ERROR, "unique"),
            ('{"status": "unique", "bbox_2d": [1, 2, 3, 1001]}', parse.RANGE_ERROR, "unique"),
            ('{"status": "unique", "bbox_2d": [-1, 2, 3, 4]}', parse.RANGE_ERROR, "unique"),
            ('{"status": "unique", "bbox_2d": [5, 2, 3, 4]}', parse.ORDER_ERROR, "unique"),
            ('{"status": "unique", "bbox_2d": [1, 4, 3, 4]}', parse.ORDER_ERROR, "unique"),
            ('{"status": "ambiguous", "candidates": [{"bbox_2d": [1,2,3,4]}]}', parse.SCHEMA_ERROR, "ambiguous"),
            (
                '{"status": "ambiguous", "candidates": ['
                + ",".join('{"bbox_2d": [1,2,3,4]}' for _ in range(9))
                + "]}",
                parse.SCHEMA_ERROR,
                "ambiguous",
            ),
            ('{"status": "ambiguous", "candidates": [{"bbox_2d": [1,2,3,4]}, {"box": 1}]}', parse.SCHEMA_ERROR, "ambiguous"),
        ]
        for raw, expected_error, raw_status in cases:
            result = parse.parse_prediction(raw)
            self.assertEqual(result["parse_error"], expected_error, raw)
            # 任一 parse_error ≠ null 即 status_pred = null；原始状态只存 raw_status。
            self.assertIsNone(result["status_pred"], raw)
            self.assertEqual(result["raw_status"], raw_status, raw)
            self.assertIn(result["parse_error"], parse.PARSE_ERRORS)

        # 截断（生成到 token 上限）优先判 TRUNCATED，且同样清空 status_pred。
        truncated = parse.parse_prediction('{"status": "none"}', finish_reason="length")
        self.assertEqual(truncated["parse_error"], parse.TRUNCATED)
        self.assertIsNone(truncated["status_pred"])

        # 合法三种骨架：去 fence 后解析成功并计 fence 数。
        ok_none = parse.parse_prediction('{"status": "none"}')
        self.assertEqual((ok_none["status_pred"], ok_none["parse_error"]), ("none", None))
        fenced = parse.parse_prediction('```json\n{"status": "unique", "bbox_2d": [1,2,3,4]}\n```')
        self.assertEqual(fenced["status_pred"], "unique")
        self.assertEqual(fenced["boxes_1000"], [[1, 2, 3, 4]])
        self.assertGreaterEqual(fenced["fence_stripped"], 1)
        ambiguous = parse.parse_prediction(
            '{"status": "ambiguous", "candidates": [{"bbox_2d": [1,2,3,4]}, {"bbox_2d": [5,6,7,8]}]}'
        )
        self.assertEqual(ambiguous["status_pred"], "ambiguous")
        self.assertEqual(len(ambiguous["boxes_1000"]), 2)


if __name__ == "__main__":
    unittest.main()
