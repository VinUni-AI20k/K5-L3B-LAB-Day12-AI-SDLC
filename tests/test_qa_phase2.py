"""Phase 2 QA regression fixtures migrated to Contract v1.2."""

import json
import unittest

from helpers import Workdir, close, counts, events, frames, items, kinds_of, read_jsonl, run_headless, snapshots, write_json


class Phase2P1Regression(unittest.TestCase):
    def test_default_gather_has_expected_fish_and_node_counts(self):
        with Workdir() as w:
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "0",
                "--out", w.path("gather.jsonl"),
            )
            self.assertEqual(code, 0, err)
            snapshot = snapshots(read_jsonl(w.path("gather.jsonl")))[0]
            self.assertEqual(len(snapshot["fish"]), 8)
            self.assertEqual(
                [node["id"] for node in snapshot["nodes"]],
                ["N1", "N2", "N3", "N4", "N5", "N6"],
            )
            self.assertEqual(
                {node["id"]: node["kind"] for node in snapshot["nodes"] if node["id"] in ("N5", "N6")},
                {"N5": "keo_neo", "N6": "keo_neo"},
            )

    def test_ca_keo_fixture_uses_contract_yield(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "gather": {
                    "player": {"pos": [50, 24]},
                    "fish": [{"id": "F1", "kind": "ca_keo", "pos": [50, 24]}],
                    "random_fish": False,
                    "time_left_ticks": 2,
                }
            })
            inputs = write_json(w.path("inputs.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", scenario, "--inputs", inputs, "--out", w.path("gather.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("gather.jsonl"))
            self.assertEqual(
                events(rows, "fish_caught")[0]["data"],
                {"fish_id": "F1", "kind": "ca_keo", "yield": 2},
            )
            hold = snapshots(rows)[-1]["hold"]
            self.assertEqual(kinds_of(hold), ["ca_keo", "ca_keo"])
            self.assertEqual([item["id"] for item in hold], ["I1", "I2"])
            self.assertTrue(all(item["fresh"] == 100 for item in hold))

    def test_quan_defaults_have_expected_entity_and_menu_counts(self):
        with Workdir() as w:
            code, err = run_headless(
                "--mode", "quan", "--seed", "1", "--ticks", "0",
                "--out", w.path("quan.jsonl"),
            )
            self.assertEqual(code, 0, err)
            snapshot = snapshots(read_jsonl(w.path("quan.jsonl")))[0]
            self.assertEqual([stove["id"] for stove in snapshot["stoves"]], ["B1", "B2"])
            self.assertEqual([table["id"] for table in snapshot["tables"]], ["T1", "T2", "T3", "T4"])
            with open("game.contract.json", encoding="utf-8") as f:
                contract = json.load(f)
            self.assertEqual(len(contract["tuning"]["menu"]), 6)

    def test_inventory_handoff_supports_contract_kinds(self):
        hand = items("ca_loc", "bong_sung", "bong_sung", "ca_keo", "keo_neo")
        with Workdir() as w:
            scenario = write_json(w.path("gather.json"), {
                "gather": {
                    "hold": hand,
                    "random_fish": False,
                }
            })
            inputs = write_json(w.path("inputs.json"), frames({"tick": 0, "interact": True}))
            inventory_path = w.path("inventory.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "42", "--scenario", scenario,
                "--inputs", inputs, "--ticks", "1",
                "--inventory-out", inventory_path, "--out", w.path("gather.jsonl"),
            )
            self.assertEqual(code, 0, err)
            gather_rows = read_jsonl(w.path("gather.jsonl"))
            handoff = events(gather_rows, "gather_end")[0]["data"]["inventory"]
            with open(inventory_path, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(counts(saved), {"bong_sung": 2, "ca_keo": 1, "ca_loc": 1, "keo_neo": 1})
            self.assertEqual([item["id"] for item in saved["items"]], [f"I{i}" for i in range(1, 6)])
            self.assertEqual(kinds_of(saved["items"]), kinds_of(hand))
            self.assertEqual([item["id"] for item in handoff["items"]], [f"I{i}" for i in range(1, 6)])
            self.assertEqual(kinds_of(handoff["items"]), kinds_of(hand))
            for item in saved["items"] + handoff["items"]:
                self.assertTrue(close(item["fresh"], 100 - 1 / 120, 0.01), item)

            code, err = run_headless(
                "--mode", "quan", "--seed", "42", "--inventory", inventory_path,
                "--ticks", "0", "--out", w.path("quan.jsonl"),
            )
            self.assertEqual(code, 0, err)
            stock = snapshots(read_jsonl(w.path("quan.jsonl")))[0]["stock"]
            self.assertEqual([item["id"] for item in stock], [f"I{i}" for i in range(1, 6)])
            self.assertEqual(kinds_of(stock), kinds_of(hand))
            for item in stock:
                self.assertTrue(close(item["fresh"], 100 - 1 / 120, 0.01), item)


if __name__ == "__main__":
    unittest.main()
