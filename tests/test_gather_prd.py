"""Kiểm chứng mục D, E, F và G của Test Contract v1.0 cho gather."""

import json
from pathlib import Path
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherPRD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tuning = json.loads(Path(ROOT, "game.contract.json").read_text(encoding="utf-8"))["tuning"]["gather"]

    def run_gather(self, scenario, *, ticks=1, **buttons):
        with Workdir() as w:
            sc = write_json(w.path("scenario.json"), {"gather": scenario})
            inp = write_json(w.path("inputs.json"), frames({"tick": 0, **buttons}))
            out = w.path("gather.jsonl")
            inv = Path(w.path("inventory.json"))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(ticks),
                                     "--scenario", sc, "--inputs", inp, "--out", out,
                                     "--inventory-out", str(inv))
            self.assertEqual(code, 0, err)
            return read_jsonl(out), json.loads(inv.read_bytes())

    def test_faint_reports_lifo_loss_and_writes_empty_inventory(self):
        hold = ["ca_loc", "bong_sung", "bong_dien_dien"]
        interval = self.tuning["choke_interval_ticks"]
        rows, inv = self.run_gather({"player": {"pos": [20, 5], "hp": 1, "oxygen_ticks": 1},
                                     "hold": hold}, ticks=interval)
        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)], [
            (1, "oxygen_empty", {"oxygen_ticks": 0}),
            (interval, "choke", {"hp": 0}),
            (interval, "faint", {"cause": "choke", "lost": hold[::-1], "hp": 0}),
            (interval, "gather_end", {"reason": "fainted", "inventory": {"items": {}}}),
        ])
        self.assertEqual(inv, {"items": {}})
        self.assertEqual(snapshots(rows)[-1]["hold"], [])
        self.assertNotIn("invuln_ticks", snapshots(rows)[0]["player"])

    def test_harvest_reports_amount_and_free_capacity(self):
        radius = self.tuning["interact_radius"]
        amount = self.tuning["node_yield"]
        plants = [{"id": ident, "kind": "bong_dien_dien", "pos": [20 + radius, 0]}
                  for ident in ("N\u0661", "N10", "N2")]
        scenario = {"player": {"pos": [20, 0]}, "nodes": plants, "time_left_ticks": 1}
        rows, inv = self.run_gather(scenario, interact=True)
        self.assertEqual([(e["name"], e["data"]) for e in events(rows)], [
            ("gather", {"node_id": "N2", "kind": "bong_dien_dien", "amount": amount}),
            ("gather_end", {"reason": "time", "inventory": inv}),
        ])
        self.assertEqual(inv, {"items": {"bong_dien_dien": amount}})

        hold = ["ca_loc"] * self.tuning["hold_capacity"]
        rows, _ = self.run_gather({**scenario, "hold": hold}, interact=True)
        self.assertEqual([e["data"] for e in events(rows, "hold_full")], [
            {"action": "gather", "node_id": "N2", "required": amount, "free": 0},
        ])
        self.assertTrue(all(n["ready"] for n in snapshots(rows)[-1]["nodes"]))

    def test_catch_reports_yield_and_does_not_switch_targets_when_full(self):
        radius = self.tuning["catch_radius"]
        count = self.tuning["fish_yield"]["ca_linh"]
        free = count - 1
        fish = [{"id": "F10", "kind": "ca_loc", "pos": [20 - radius, 5]},
                {"id": "F2", "kind": "ca_linh", "pos": [20 + radius, 5]}]
        scenario = {"player": {"pos": [20, 5]}, "fish": fish, "time_left_ticks": 1}
        rows, inv = self.run_gather(scenario, catch=True)
        self.assertEqual([(e["name"], e["data"]) for e in events(rows)], [
            ("fish_caught", {"fish_id": "F2", "kind": "ca_linh", "yield": count}),
            ("gather_end", {"reason": "time", "inventory": inv}),
        ])
        self.assertEqual(inv, {"items": {"ca_linh": count}})

        hold = ["bong_sung"] * (self.tuning["hold_capacity"] - free)
        rows, _ = self.run_gather({**scenario, "hold": hold}, catch=True)
        self.assertEqual([e["data"] for e in events(rows, "hold_full")], [
            {"action": "catch", "fish_id": "F2", "required": count, "free": free},
        ])
        end = snapshots(rows)[-1]
        self.assertEqual([f["id"] for f in end["fish"]], ["F2", "F10"])
        self.assertEqual(end["hold"], hold)
        self.assertEqual(end["player"]["catch_cd_ticks"], 0)

    def test_v10_rejects_invuln_fixture_before_writing_output(self):
        with Workdir() as w:
            sc = write_json(w.path("scenario.json"), {"gather": {"player": {"invuln_ticks": 5}}})
            out, inv = Path(w.path("gather.jsonl")), Path(w.path("inventory.json"))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--scenario", sc,
                                     "--out", str(out), "--inventory-out", str(inv))
            self.assertEqual(code, 2, err)
            self.assertFalse(out.exists())
            self.assertFalse(inv.exists())
