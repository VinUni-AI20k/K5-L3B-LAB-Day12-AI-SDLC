import contextlib
import io
import json
import os
import tempfile
import unittest

from chonoi.contract import load_contract
from chonoi.day import merged_day_plan
from chonoi.errors import BadInput
from chonoi.soak import main, run_soak


class DayPlanCycle(unittest.TestCase):
    def test_preset_and_scenario_plans_repeat_after_day_five(self):
        tuning = load_contract()["tuning"]
        plan = merged_day_plan(tuning, [{"day": 1, "dishes": {"lau_mam": 2}}], days=10)

        self.assertEqual(list(plan), list(range(1, 11)))
        for day in range(1, 6):
            self.assertEqual(plan[day], plan[day + 5])
        self.assertEqual(plan[1]["dishes"], {"lau_mam": 2})
        self.assertEqual(plan[6]["dishes"], {"lau_mam": 2})
        self.assertEqual(plan[6]["ingredients"],
                         {"bong_dien_dien": 2, "ca_keo": 2, "ca_linh": 4, "keo_neo": 2})


class SoakRunner(unittest.TestCase):
    def test_soak_completes_a_repeated_day_deterministically(self):
        first = run_soak(seed=7, days=6)
        second = run_soak(seed=7, days=6)

        self.assertEqual(first["days"], 6)
        self.assertEqual(first["days_completed"], 6)
        self.assertEqual(first["crashes"], 0)
        self.assertEqual([result["day"] for result in first["results"]], list(range(1, 7)))
        self.assertTrue(all(set(result) == {"day", "earned", "reputation", "score"}
                            for result in first["results"]))
        self.assertEqual({key: value for key, value in first.items() if key != "duration_s"},
                         {key: value for key, value in second.items() if key != "duration_s"})
        self.assertGreaterEqual(first["duration_s"], 0)

    def test_cli_writes_report_and_rejects_non_positive_days(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, "soak.json")
            self.assertEqual(main(["--seed", "7", "--days", "1", "--out", output]), 0)
            with open(output, encoding="utf-8") as f:
                report = json.load(f)
            self.assertEqual((report["days"], report["days_completed"], report["crashes"]), (1, 1, 0))
            self.assertEqual([result["day"] for result in report["results"]], [1])
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--seed", "7", "--days", "0", "--out", output]), 2)

        with self.assertRaises(BadInput):
            run_soak(seed=7, days=0)


if __name__ == "__main__":
    unittest.main()
