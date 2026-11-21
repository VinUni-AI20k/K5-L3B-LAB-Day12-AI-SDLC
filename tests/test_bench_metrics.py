import unittest

from chonoi.bench import frame_metrics


class BenchmarkMetrics(unittest.TestCase):
    def test_one_percent_low_uses_mean_of_slowest_frames(self):
        intervals = [0.01] * 198 + [0.1, 0.2]
        result = frame_metrics(intervals, 250)
        self.assertEqual(result["frames"], 200)
        self.assertAlmostEqual(result["p1_low_fps"], 6.67)
        self.assertAlmostEqual(result["avg_fps"], 200 / 2.28, places=2)
        self.assertEqual(result["load_ms"], 250)

    def test_short_sample_uses_one_slowest_frame(self):
        self.assertEqual(frame_metrics([0.01, 0.05], 0)["p1_low_fps"], 20)
