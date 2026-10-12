import unittest

import numpy as np

from controller.sensor_protocol import validate_system_monotonic_frame
from tools.benchmark_reanchor import _frame


class BenchmarkReanchorTests(unittest.TestCase):
    def test_synthetic_frame_uses_the_reviewed_v3_clock_contract(self):
        frame = _frame(
            7,
            np.zeros((480, 640, 3), dtype=np.uint8),
            501.25,
        )

        self.assertEqual(frame.frame_id, 7)
        self.assertEqual(
            validate_system_monotonic_frame(
                frame.metadata,
                context="benchmark frame",
            ),
            501.25,
        )


if __name__ == "__main__":
    unittest.main()
