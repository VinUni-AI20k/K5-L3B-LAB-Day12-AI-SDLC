"""TICKET-04 mở rộng leaderboard: `<run_cmd> --export-leaderboard <out.json> [--leaderboard <store.json>]` (qua run_cmd thật)."""

import json
import os
import shlex
import subprocess
import unittest

from chonoi.leaderboard import record
from helpers import ROOT, Workdir


def run_cmd():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return shlex.split(json.load(f)["run_cmd"])


class RunCmdExport(unittest.TestCase):
    def test_run_cmd_exports_sorted_board_without_starting_server(self):
        with Workdir() as w:
            store, out = w.path("store.json"), w.path("out.json")
            record(store, "Út Sen", 300, 5, 42)
            record(store, "Má Tư", 500, 5, 7)
            p = subprocess.run([*run_cmd(), "--export-leaderboard", out, "--leaderboard", store],
                               cwd=ROOT, capture_output=True, text=True, timeout=20)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                got = json.load(f)
            self.assertEqual([(e["name"], e["score"]) for e in got["entries"]], [("Má Tư", 500), ("Út Sen", 300)])
            self.assertEqual(set(got["entries"][0]), {"name", "score", "days_completed", "seed"})


if __name__ == "__main__":
    unittest.main()
