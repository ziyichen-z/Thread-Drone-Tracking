import unittest

from tools.benchmark_tracker import percentile


class BenchmarkTrackerTests(unittest.TestCase):
    def test_percentile_uses_linear_interpolation(self):
        self.assertEqual(percentile([1.0], 95.0), 1.0)
        self.assertAlmostEqual(percentile([1.0, 2.0, 3.0], 50.0), 2.0)
        self.assertAlmostEqual(percentile([0.0, 10.0], 95.0), 9.5)

    def test_percentile_rejects_empty_and_out_of_range_inputs(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            percentile([], 95.0)
        with self.assertRaisesRegex(ValueError, "in \\[0, 100\\]"):
            percentile([1.0], 101.0)


if __name__ == "__main__":
    unittest.main()
