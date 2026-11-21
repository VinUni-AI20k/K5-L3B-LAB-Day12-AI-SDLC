"""P4-04 (AC-P4-03): soak headless nhiều Ngày liền trong một tiến trình, xuất soak.json đúng năm trường."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from chonoi import soak
from chonoi.contract import load_contract
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.day import DaySim

CONTRACT = load_contract()
T = CONTRACT["tuning"]
FIELDS = {"days", "days_completed", "crashes", "results", "duration_s"}
RESULT_FIELDS = {"day", "money", "earned", "reputation", "score", "upgrades"}


def stable(report):
    return {k: v for k, v in report.items() if k != "duration_s"}  # duration_s là thời gian thật


class Report(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = soak.run_soak(7, 10)  # đúng lệnh của đề: --seed 7 --days 10

    def test_ten_days_complete_without_crash(self):
        r = self.report
        self.assertEqual(set(r), FIELDS)
        self.assertEqual((r["days"], r["days_completed"], r["crashes"]), (10, 10, 0))
        self.assertEqual([x["day"] for x in r["results"]], list(range(1, 11)))
        self.assertTrue(all(set(x) == RESULT_FIELDS for x in r["results"]))
        self.assertGreater(r["duration_s"], 0)

    def test_state_carries_across_days(self):
        rep = [x["reputation"] for x in self.report["results"]]
        lo, hi = T["quan"]["reputation_min"], T["quan"]["reputation_max"]
        self.assertTrue(all(lo <= v <= hi for v in rep))
        for x in self.report["results"]:
            self.assertGreaterEqual(x["earned"], x["money"] - 0)  # chưa mua gì: tiền không vượt tổng thu
            self.assertEqual(x["score"], x["earned"] + T["score"]["reputation_multiplier"] * int(x["reputation"]))

    def test_same_seed_gives_identical_results(self):
        self.assertEqual(stable(soak.run_soak(7, 2)), stable(soak.run_soak(7, 2)))

    def test_days_six_to_ten_repeat_plan_of_days_one_to_five(self):
        sim = DaySim(T, {}, Streams(7), 10)
        for day in range(6, 11):
            self.assertEqual(sim._plan_for(day), sim._plan_for(day - 5))


class Bot(unittest.TestCase):
    def test_bot_harvests_and_docks_in_day_one(self):
        s = Session("day", T, {}, 7, days=1, contract_version=CONTRACT["contract_version"])
        names = []
        while not s.done and "gather_end" not in names:
            names += [r["name"] for r in s.step(soak.bot_input(s.sim, T))]
        self.assertGreaterEqual(names.count("gather"), 1)
        self.assertIn("gather_end", names)

    def test_bot_has_no_input_outside_gather(self):
        class Fake:
            phase = "quan"
        inp = soak.bot_input(Fake(), T)
        self.assertEqual((tuple(inp.move), inp.pressed("interact")), ((0.0, 0.0), False))


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "chonoi.soak", *args], capture_output=True, text=True,
                              encoding="utf-8", timeout=120)

    def test_writes_json_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "soak.json"
            p = self.run_cli("--seed", "7", "--days", "2", "--out", str(out))
            self.assertEqual(p.returncode, 0, p.stderr)
            data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual((set(data), data["days_completed"], data["crashes"]), (FIELDS, 2, 0))

    def test_bad_days_exit_two_and_leave_file_alone(self):
        for days in ("0", "101", "-1", "x"):
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / "soak.json"
                out.write_text("{}", encoding="utf-8")
                p = self.run_cli("--days", days, "--out", str(out))
                self.assertEqual(p.returncode, 2, (days, p.stderr))
                self.assertEqual(out.read_text(encoding="utf-8"), "{}")

    def test_crash_is_counted_reported_and_exit_one(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "soak.json"
            with mock.patch("chonoi.soak.bot_input", side_effect=RuntimeError("boom")):
                code = soak.main(["--days", "2", "--out", str(out)])
            data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(code, 1)
        self.assertEqual((data["crashes"], data["days_completed"], data["results"]), (1, 0, []))


if __name__ == "__main__":
    unittest.main()
