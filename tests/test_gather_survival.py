"""PRD-0 F/G: lặn, thở, ngạt và bàn giao kho khi ngất."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from helpers import ROOT, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherSurvival(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)

    def gather(self, player, ticks, commands=(), **scenario):
        fixture = write_json(self.work / "scenario.json", {"gather": {"player": player, **scenario}})
        inputs = write_json(self.work / "inputs.json", frames(*commands))
        output = self.work / "gather.jsonl"
        self.inventory = self.work / "inventory.json"
        code, err = run_headless("--mode", "gather", "--seed", "1", "--scenario", fixture,
                                 "--inputs", inputs, "--ticks", str(ticks), "--snapshot-every", "1",
                                 "--out", output, "--inventory-out", str(self.inventory))
        self.assertEqual(code, 0, err)
        return read_jsonl(output)

    def test_dive_at_surface_boundary(self):
        rows = self.gather({"pos": [20, 0.5], "oxygen_ticks": 1}, 2,
                           commands=[{"tick": 0, "move": [0, 1]}])
        first = snapshots(rows)[1]["player"]
        self.assertFalse(first["at_surface"])
        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)], [
            (1, "dive", {"pos": first["pos"]}), (1, "oxygen_empty", {"oxygen_ticks": 0})])
        self.assertEqual(first["zero_oxy_ticks"], 1)

    def test_first_zero_tick_counts_and_choke_repeats(self):
        rows = self.gather({"pos": [20, 5], "oxygen_ticks": 2}, 121, hold=["ca_linh"])
        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)], [
            (2, "oxygen_empty", {"oxygen_ticks": 0}), (61, "choke", {"hp": 2}),
            (121, "choke", {"hp": 1})])
        self.assertEqual(snapshots(rows)[-1]["hold"], ["ca_linh"])
        self.assertEqual(snapshots(rows)[-1]["player"]["zero_oxy_ticks"], 0)

    def test_surface_on_choke_step_resets_timer_and_refills(self):
        rows = self.gather({"pos": [20, 0.501], "oxygen_ticks": 0, "zero_oxy_ticks": 59,
                            "hp": 1}, 2, commands=[{"tick": 0, "move": [0, -1]}])
        first = snapshots(rows)[1]["player"]
        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)],
                         [(1, "surface", {"pos": first["pos"]})])
        self.assertTrue(first["at_surface"])
        self.assertEqual((first["hp"], first["zero_oxy_ticks"], first["oxygen_ticks"]), (1, 0, 6))
        self.assertEqual(snapshots(rows)[-1]["player"]["oxygen_ticks"], 12)

    def test_oxygen_caps_at_max_on_surface(self):
        tuning = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))["tuning"]
        maximum = round(tuning["gather"]["oxygen_max_s"] * tuning["tick_hz"])
        rows = self.gather({"pos": [20, 0.5], "oxygen_ticks": maximum - 1}, 2)
        for snap in snapshots(rows)[1:]:
            self.assertEqual(snap["player"]["oxygen_ticks"], snap["player"]["oxygen_max_ticks"])
        self.assertEqual(events(rows), [])

    def test_faint_precedes_docking_catching_and_timeout(self):
        hold = ["bong_sung", "ca_loc", "ca_linh"]
        rows = self.gather({"pos": [2, 1], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                           8, commands=[{"tick": 0, "interact": True, "catch": True}],
                           time_left_ticks=1, hold=hold, random_fish=False,
                           fish=[{"id": "F1", "kind": "ca_loc", "pos": [2, 1]}])
        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)], [
            (1, "choke", {"hp": 0}),
            (1, "faint", {"cause": "choke", "lost": list(reversed(hold)), "hp": 0}),
            (1, "gather_end", {"reason": "fainted", "inventory": {"items": {}}})])
        self.assertEqual(snapshots(rows)[-1]["hold"], [])
        self.assertEqual((rows[-1]["reason"], rows[-1]["ticks"]), ("fainted", 1))
        self.assertEqual(json.loads(self.inventory.read_text(encoding="utf-8")), {"items": {}})
