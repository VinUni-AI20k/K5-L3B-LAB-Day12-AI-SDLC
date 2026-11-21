"""Tests for deterministic, actual-DaySim soak execution."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.soak import main, run_soak


class SoakTests(unittest.TestCase):
    def quick_tuning(self):
        tuning = copy.deepcopy(load_contract()["tuning"])
        tuning["gather"]["duration_s"] = 1
        tuning["quan"]["duration_s"] = 2
        tuning["quan"]["first_customer_tick"] = 10000
        tuning["shop"]["max_ticks"] = 2
        return tuning

    def run_in(self, directory, name, days=1):
        return run_soak(7, days, str(Path(directory) / name), tuning=self.quick_tuning())

    def test_cli_rejects_non_integer_seed_and_invalid_days(self):
        with self.assertRaises(SystemExit) as seed_error:
            main(["--seed", "nope", "--days", "1", "--out", "unused.json"])
        self.assertEqual(seed_error.exception.code, 2)
        with self.assertRaises(SystemExit) as days_error:
            main(["--seed", "1", "--days", "0", "--out", "unused.json"])
        self.assertEqual(days_error.exception.code, 2)

    def test_one_day_uses_real_daysim_and_writes_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            code, result = self.run_in(directory, "one.json")
            written = json.loads((Path(directory) / "one.json").read_text(encoding="utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(result["days_completed"], 1)
        self.assertEqual(result["crashes"], 0)
        self.assertEqual(result["results"], [{"day": 1, "earned": 0, "reputation": 3.0, "score": 300}])
        self.assertEqual(set(written), {"days", "days_completed", "crashes", "results", "duration_s"})
        self.assertGreaterEqual(written["duration_s"], 0)

    def test_ten_day_replay_matches_gameplay_results(self):
        with tempfile.TemporaryDirectory() as directory:
            code_a, result_a = self.run_in(directory, "a.json", days=10)
            code_b, result_b = self.run_in(directory, "b.json", days=10)
        self.assertEqual(code_a, 0)
        self.assertEqual(code_b, 0)
        self.assertEqual(result_a["days_completed"], 10)
        self.assertEqual(result_a["crashes"], 0)
        for field in ("days", "days_completed", "crashes", "results"):
            self.assertEqual(result_a[field], result_b[field])
        self.assertEqual([row["day"] for row in result_a["results"]], list(range(1, 11)))

    def test_runtime_crash_is_counted_and_not_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("chonoi.soak.Session.step", side_effect=RuntimeError("injected runtime failure")):
                code, result = self.run_in(directory, "crash.json")
            saved = json.loads((Path(directory) / "crash.json").read_text(encoding="utf-8"))
        self.assertEqual(code, 1)
        self.assertEqual(result["crashes"], 1)
        self.assertEqual(result["days_completed"], 0)
        self.assertIn("injected runtime failure", saved["diagnostics"][0]["error"])

    def test_output_path_error_returns_nonzero(self):
        code, result = run_soak(7, 1, "missing-parent/soak.json", tuning=self.quick_tuning())
        self.assertEqual(code, 1)
        self.assertEqual(result["days_completed"], 1)
        self.assertEqual(result["crashes"], 0)


if __name__ == "__main__":
    unittest.main()
