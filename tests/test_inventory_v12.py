"""Smoke hộp đen cho kho cá thể và việc bàn giao khi chạy một Ngày."""

import json
import unittest
from pathlib import Path

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def item(id, fresh=100):
    return {"id": id, "kind": "ca_loc", "fresh": fresh}


class InventoryV12Tests(unittest.TestCase):
    def run_mode(self, mode, ticks, output, *args):
        code, error = run_headless("--mode", mode, "--ticks", str(ticks), "--seed", "42", "--out", output,
                                   "--snapshot-every", "1", *args)
        self.assertEqual(code, 0, error)
        return read_jsonl(output)

    def test_file_handoff_keeps_exact_json_view(self):
        with Workdir() as work:
            scenario = write_json(work.path("gather.json"), {"gather": {
                "hold": [item("I10", 30), item("I2")], "random_fish": False, "monsters": [],
            }})
            inputs = write_json(work.path("inputs.json"), frames({"tick": 0, "interact": True}))
            inventory = work.path("inventory.json")
            gather = self.run_mode("gather", 1, work.path("g.jsonl"), "--scenario", scenario,
                                   "--inputs", inputs, "--inventory-out", inventory)
            quan = self.run_mode("quan", 0, work.path("q.jsonl"), "--inventory", inventory)
            stored = json.loads(Path(inventory).read_text(encoding="utf-8"))
        self.assertEqual(stored, events(gather, "gather_end")[0]["data"]["inventory"])
        self.assertEqual(stored["items"], snapshots(quan)[0]["stock"])
        self.assertEqual([row["id"] for row in stored["items"]], ["I2", "I10"])
        self.assertLess(stored["items"][1]["fresh"], 30)
        self.assertEqual(events(gather, "spoiled")[0]["data"]["item_id"], "I10")

    def test_v12_rejects_count_file_before_output(self):
        with Workdir() as work:
            inventory = write_json(work.path("count.json"), {"items": {"ca_loc": 1}})
            existing = Path(work.path("out.jsonl"))
            existing.write_text("old", encoding="utf-8")
            code, _ = run_headless("--mode", "quan", "--seed", "42", "--ticks", "0",
                                   "--inventory", inventory, "--out", str(existing))
            self.assertEqual(code, 2)
            self.assertEqual(existing.read_text(encoding="utf-8"), "old")

    def test_day_renews_fixture_ids_and_keeps_stock_through_shop(self):
        with Workdir() as work:
            scenario = write_json(work.path("day.json"), {
                "gather": {"hold": [item("I12")], "time_left_ticks": 1, "monsters": []},
                "quan": {"time_left_ticks": 1, "random_customers": False, "customers": [
                    {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I12"]},
                ]},
            })
            inputs = write_json(work.path("inputs.json"), frames(
                {"tick": 2, "pause": True}, {"tick": 3, "pause": False},
                {"tick": 4, "pause": True, "shop_done": True},
            ))
            rows = self.run_mode("day", 6, work.path("day.jsonl"), "--days", "2",
                                 "--scenario", scenario, "--inputs", inputs)
        at = {row["tick"]: row for row in snapshots(rows)}
        self.assertEqual(at[1]["stock"], events(rows, "gather_end")[0]["data"]["inventory"]["items"])
        self.assertEqual(at[1]["customers"][0]["reserved"], ["I12"])
        self.assertEqual(at[2]["stock"], at[4]["stock"])
        self.assertEqual(at[4]["state"], "paused")
        self.assertEqual(at[5]["hold"], [item("I13")])
        self.assertEqual(at[6]["customers"][0]["reserved"], ["I13"])

    def test_freshness_stays_below_threshold_after_jsonl_conversion(self):
        with Workdir() as work:
            scenario = Path(work.path("below.json"))
            scenario.write_text('{"gather":{"hold":[{"id":"I1","kind":"ca_loc","fresh":29.999999999999999999}]}}',
                                encoding="utf-8")
            rows = self.run_mode("gather", 0, work.path("g.jsonl"), "--scenario", str(scenario))
            self.assertLess(snapshots(rows)[0]["hold"][0]["fresh"], 30)
