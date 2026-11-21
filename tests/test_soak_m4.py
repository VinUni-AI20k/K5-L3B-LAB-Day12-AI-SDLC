"""Unit test cho P4-M4.1 (`chonoi.soak`): chạy 10 Ngày liên tục, lặp D1–D5 cho D6–D10, tất định."""

import json
import unittest

from chonoi.soak import main as soak_main
from helpers import Workdir


class SoakM4Tests(unittest.TestCase):
    def test_soak_10_days_deterministic_and_zero_crashes(self):
        with Workdir() as w:
            out1 = w.path("soak1.json")
            out2 = w.path("soak2.json")
            self.assertEqual(soak_main(["--seed", "7", "--days", "10", "--out", out1]), 0)
            self.assertEqual(soak_main(["--seed", "7", "--days", "10", "--out", out2]), 0)
            with open(out1, encoding="utf-8") as f1, open(out2, encoding="utf-8") as f2:
                d1, d2 = json.load(f1), json.load(f2)
            for d in (d1, d2):
                self.assertEqual(d["days"], 10)
                self.assertEqual(d["days_completed"], 10)
                self.assertEqual(d["crashes"], 0)
                self.assertEqual(len(d["results"]), 10)
                self.assertEqual([r["day"] for r in d["results"]], list(range(1, 11)))
                self.assertGreaterEqual(d["duration_s"], 0.0)
            # Tính lặp ở các trường gameplay (bỏ duration_s)
            self.assertEqual(d1["results"], d2["results"])


if __name__ == "__main__":
    unittest.main()
