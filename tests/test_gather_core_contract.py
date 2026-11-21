"""Hồi quy payload Gather Core theo PRD-0 mục E/F/G, qua CLI headless."""

import json
import unittest

from chonoi.contract import load_contract
from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


class GatherCoreContract(unittest.TestCase):
    def test_oxygen_empty_payload_and_no_repeat(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {"gather": {
                "player": {"pos": [20, 5], "oxygen_ticks": 1}, "nodes": [], "fish": []}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "3",
                                     "--scenario", scenario, "--out", w.path("out.jsonl"))
            self.assertEqual(code, 0, err)
            empty = events(read_jsonl(w.path("out.jsonl")), "oxygen_empty")
            self.assertEqual([(e["tick"], e["data"]) for e in empty], [(1, {"oxygen_ticks": 0})])

    def test_faint_lost_lifo_and_empty_inventory(self):
        interval = load_contract()["tuning"]["gather"]["choke_interval_ticks"]
        for kinds in ([], ["ca_loc", "bong_sung"], ["ca_loc", "bong_sung", "ca_loc", "ca_linh"]):
            hold = [{"id": f"I{i}", "kind": k, "fresh": 100} for i, k in enumerate(kinds, 1)]
            with self.subTest(hold=kinds), Workdir() as w:
                scenario = write_json(w.path("scenario.json"), {"gather": {
                    "player": {"pos": [20, 5], "oxygen_ticks": 0, "hp": 1,
                               "zero_oxy_ticks": interval - 1}, "hold": hold, "nodes": [], "fish": []}})
                inventory = write_json(w.path("inventory.json"), {"items": [{"id": "I99", "kind": "ca_loc", "fresh": 100}]})
                code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "3",
                                         "--scenario", scenario, "--inventory-out", inventory,
                                         "--out", w.path("out.jsonl"))
                self.assertEqual(code, 0, err)
                rows = read_jsonl(w.path("out.jsonl"))
                exp_lost = [{"id": f"I{i}", "kind": k, "fresh": 99.991667} for i, k in reversed(list(enumerate(kinds, 1)))]
                self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)], [
                    (1, "choke", {"hp": 0}),
                    (1, "faint", {"cause": "choke", "lost": exp_lost, "hp": 0}),
                    (1, "gather_end", {"reason": "fainted", "inventory": {"items": []}})])
                self.assertEqual(snapshots(rows)[-1]["hold"], [])
                self.assertEqual(snapshots(rows)[-1]["hold_count"], 0)
                self.assertEqual(rows[-1]["reason"], "fainted")
                with open(inventory, encoding="utf-8") as f:
                    self.assertEqual(json.load(f), {"items": []})
