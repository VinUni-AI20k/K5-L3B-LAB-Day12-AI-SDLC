import json
import os
import unittest
from unittest.mock import patch

from chonoi import headless
from chonoi.leaderboard import export, record
from helpers import Workdir


class LeaderboardTests(unittest.TestCase):
    def test_top_ten_sort_is_stable_across_reopen_and_exports_unicode(self):
        with Workdir() as w:
            store, out = w.path("scores.json"), w.path("export.json")
            for i in range(12):
                record(store, f"Người chơi {i}", i // 2, 5, i)
            record(store, "Út Sen 🌱", 99, 5, 42)
            record(store, "Sen kế", 99, 5, 43)
            record(store, "Sen sau", 2, 5, 43)
            export(store, out)
            with open(out, encoding="utf-8") as f:
                got = json.load(f)["entries"]
            self.assertEqual(len(got), 10)
            self.assertEqual(got[0]["name"], "Út Sen 🌱")
            self.assertEqual(got[1]["name"], "Sen kế")
            self.assertNotIn("Sen sau", [row["name"] for row in got])
            self.assertFalse(os.path.exists(store + ".tmp"))

    def test_export_cli_and_invalid_flag_pairs(self):
        with Workdir() as w:
            store, out = w.path("scores.json"), w.path("export.json")
            record(store, "Út Sen", 300, 5, 42)
            self.assertEqual(headless.main(["--leaderboard", store, "--export-leaderboard", out]), 0)
            with open(out, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["entries"][0]["name"], "Út Sen")
            base = ["--mode", "day", "--seed", "1", "--ticks", "0", "--out", w.path("run.jsonl")]
            self.assertEqual(headless.main(base + ["--leaderboard", store]), 2)
            self.assertEqual(headless.main(base + ["--player-name", "Sen"]), 2)
            self.assertEqual(headless.main(base + ["--leaderboard", store, "--player-name", " "]), 2)

    def test_only_completed_five_day_run_records(self):
        with Workdir() as w:
            store, out = w.path("scores.json"), w.path("run.jsonl")
            completed = type("Run", (), {"done": True, "reason": "days_complete", "days_completed": 5,
                                           "end_row": lambda self: {"score": 123}})()
            args = ["--mode", "day", "--seed", "5", "--ticks", "1", "--days", "5", "--out", out,
                    "--leaderboard", store, "--player-name", "Út Sen"]
            with patch("chonoi.headless.run", return_value=completed):
                self.assertEqual(headless.main(args), 0)
            with open(store, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["entries"],
                                 [{"name": "Út Sen", "score": 123, "days_completed": 5, "seed": 5}])

            incomplete = type("Run", (), {"done": False, "reason": None, "days_completed": 0})()
            with patch("chonoi.headless.run", return_value=incomplete):
                self.assertEqual(headless.main(args), 0)
            with open(store, encoding="utf-8") as f:
                self.assertEqual(len(json.load(f)["entries"]), 1)


if __name__ == "__main__":
    unittest.main()
