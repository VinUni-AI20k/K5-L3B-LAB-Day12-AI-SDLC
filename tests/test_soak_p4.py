"""Tests for Phase 4 soak_cmd (AC-P4-03): 10-day deterministic run, D1-D5 cycling, 0 crashes."""

import json
import subprocess
import sys
import unittest

from helpers import Workdir


class TestSoakP4(unittest.TestCase):
    def _run_soak(self, out_path, seed=7, days=10):
        proc = subprocess.run(
            [sys.executable, "-m", "chonoi.soak", "--seed", str(seed), "--days", str(days), "--out", out_path],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(out_path, encoding="utf-8") as f:
            return json.load(f)

    def test_ac_p4_03_soak_10_days_deterministic_and_zero_crashes(self):
        with Workdir() as w:
            r1 = self._run_soak(w.path("soak1.json"), seed=7, days=10)
            r2 = self._run_soak(w.path("soak2.json"), seed=7, days=10)

            self.assertEqual(set(r1.keys()), {"days", "days_completed", "crashes", "results", "duration_s"})
            self.assertEqual(r1["days"], 10)
            self.assertEqual(r1["days_completed"], 10)
            self.assertEqual(r1["crashes"], 0)
            self.assertIsInstance(r1["duration_s"], (int, float))
            self.assertGreaterEqual(r1["duration_s"], 0.0)

            self.assertEqual(len(r1["results"]), 10)
            for idx, entry in enumerate(r1["results"], start=1):
                self.assertEqual(set(entry.keys()), {"day", "earned", "reputation", "score"})
                self.assertEqual(entry["day"], idx)

            c1 = {k: v for k, v in r1.items() if k != "duration_s"}
            c2 = {k: v for k, v in r2.items() if k != "duration_s"}
            self.assertEqual(c1, c2)


if __name__ == "__main__":
    unittest.main()