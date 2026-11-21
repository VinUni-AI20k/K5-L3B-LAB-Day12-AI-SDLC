"""P3-02: ID cá thể, file kho v1.2 và bàn giao xuyên ngày."""

import json
import os
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdRegistry
from chonoi.inputs import InputState
from chonoi.inventory import (clone_items, read_inventory, save_inventory_atomic,
                              validate_inventory_items)
from chonoi.runner import Session
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


def item(ident="I1", kind="ca_linh", fresh=100.0):
    return {"id": ident, "kind": kind, "fresh": fresh}


class InventoryV12(unittest.TestCase):
    def test_schema_accepts_six_kinds_and_clones(self):
        kinds = ("ca_linh", "ca_loc", "ca_keo", "bong_sung", "bong_dien_dien", "keo_neo")
        source = [item(f"I{k}", kind, k * 10) for k, kind in enumerate(kinds, 1)]
        result = validate_inventory_items(source, kinds)
        self.assertEqual([row["fresh"] for row in result], [10.0, 20.0, 30.0, 40.0, 50.0, 60.0])
        copied = clone_items(result)
        copied[0]["fresh"] = 0.0
        self.assertEqual(result[0]["fresh"], 10.0)
        self.assertEqual(validate_inventory_items([item(fresh=0), item("I2", fresh=100)]),
                         [item(fresh=0.0), item("I2", fresh=100.0)])

    def test_schema_rejects_old_counts_and_invalid_fields(self):
        bad = ({"ca_loc": 2}, [item(), item()], [item(kind="unknown")],
               [item(fresh=-0.1)], [item(fresh=100.1)], [item(fresh=True)],
               [item("I0")], [item("I01")], [item("X1")],
               [{"id": "I1", "kind": "ca_linh"}], [{**item(), "extra": 1}])
        for value in bad:
            with self.subTest(value=value), self.assertRaises(BadInput):
                validate_inventory_items(value)

    def test_id_registry_observes_and_never_reuses(self):
        ids = IdRegistry()
        self.assertEqual([ids.next_item_id(), ids.next_item_id()], ["I1", "I2"])
        ids.observe_item_ids([item("I12"), item("I3")])
        self.assertEqual(ids.next_item_id(), "I13")
        ids.observe_item_ids(["I1"])
        self.assertEqual(ids.next_item_id(), "I14")

    def test_dropped_item_ids_are_not_reused_by_next_catch(self):
        ids = IdRegistry()
        scenario = {"player": {"pos": [60, 24]},
                    "hold": [item(f"I{k}", "ca_loc") for k in range(1, 5)],
                    "fish": [{"id": "F1", "kind": "ca_keo", "pos": [60, 24]}]}
        sim = GatherSim(load_contract()["tuning"], scenario, Streams(1), ids)
        sim.step(InputState((0, 0), {}, set()))
        self.assertEqual([entry["id"] for entry in sim.hold_items], ["I1", "I2"])
        sim.step(InputState((0, 0), {}, {"catch"}))
        self.assertEqual([entry["id"] for entry in sim.hold_items], ["I1", "I2", "I5", "I6"])

    def test_atomic_write_replaces_file_and_cleans_temporary(self):
        with Workdir() as work:
            path = work.path("inventory.json")
            with open(path, "w", encoding="utf-8") as stream:
                stream.write("old")
            rows = [item("I8", "ca_loc", 64.25)]
            save_inventory_atomic(path, rows)
            self.assertEqual(read_inventory(path), rows)
            self.assertEqual(os.listdir(os.path.dirname(path)), ["inventory.json"])

    def test_headless_rejects_bad_file_before_output_with_exit_two(self):
        invalid = ({"ca_loc": 2}, [item(), item()], [item(kind="unknown")],
                   [item(fresh=-1)], [item(fresh=101)], [item(fresh=True)])
        for value in invalid:
            with self.subTest(value=value), Workdir() as work:
                source = write_json(work.path("inventory.json"), {"items": value})
                out = work.path("out.jsonl")
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                       "--inventory", source, "--out", out)
                self.assertEqual(code, 2)
                self.assertFalse(os.path.exists(out))

    def test_scenario_validates_individual_hold_and_stock(self):
        for mode, block in (("gather", {"hold": [item(), item()]}),
                            ("quan", {"stock": [item(fresh=True)]})):
            with self.subTest(mode=mode), Workdir() as work:
                scenario = write_json(work.path("scenario.json"), {mode: block})
                out = work.path("out.jsonl")
                code, _ = run_headless("--mode", mode, "--seed", "1", "--ticks", "0",
                                       "--scenario", scenario, "--out", out)
                self.assertEqual(code, 2)
                self.assertFalse(os.path.exists(out))

    def test_two_process_handoff_preserves_id_and_fresh(self):
        with Workdir() as work:
            original = [item("I7", "ca_loc", 65.5)]
            scenario = write_json(work.path("gather.json"), {"gather": {"hold": original}})
            inputs = write_json(work.path("inputs.json"), {"frames": [{"tick": 0, "interact": True}]})
            inventory = work.path("inventory.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", scenario, "--inputs", inputs,
                                     "--inventory-out", inventory, "--out", work.path("gather.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual([(i["id"], i["kind"]) for i in read_inventory(inventory)], [("I7", "ca_loc")])
            self.assertAlmostEqual(read_inventory(inventory)[0]["fresh"], 65.5 - 0.5 / 60, places=9)
            end_items = events(read_jsonl(work.path("gather.jsonl")), "gather_end")[0]["data"]["inventory"]["items"]
            self.assertEqual([(i["id"], i["kind"]) for i in end_items], [("I7", "ca_loc")])
            self.assertAlmostEqual(end_items[0]["fresh"], 65.5 - 0.5 / 60, delta=0.01)  # JSONL làm tròn 3 chữ số
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--inventory", inventory, "--out", work.path("quan.jsonl"))
            self.assertEqual(code, 0, err)
            stock = snapshots(read_jsonl(work.path("quan.jsonl")))[0]["stock_items"]
            self.assertEqual([(i["id"], i["kind"]) for i in stock], [("I7", "ca_loc")])
            self.assertAlmostEqual(stock[0]["fresh"], 65.5 - 0.5 / 60, delta=0.01)  # JSONL làm tròn 3 chữ số

    def test_day_registry_continues_after_handoff_and_resets_hold(self):
        tuning = load_contract()["tuning"]
        scenario = {"gather": {"player": {"pos": [12, 0]}, "hold": [item("I8", "ca_loc", 72.5)],
                               "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
                               "time_left_ticks": 1, "random_fish": False, "monsters": []},
                    "quan": {"time_left_ticks": 1, "random_customers": False}}
        session = Session("day", tuning, scenario, 1, days=2)
        press = InputState((0, 0), {}, {"interact"})
        neutral = InputState((0, 0), {}, set())
        rows = session.step(press)
        first = next(row["data"]["inventory"]["items"] for row in rows if row["name"] == "gather_end")
        self.assertEqual([(i["id"], i["kind"]) for i in first], [("I8", "ca_loc"), ("I9", "bong_sung")])
        self.assertAlmostEqual(first[0]["fresh"], 72.5 - 0.5 / 60, places=9)  # hao 1 tick trước bến
        self.assertEqual(first[1]["fresh"], 100.0)
        self.assertEqual(session.snapshot()["stock"], first)
        session.step(neutral)  # Quán -> Shop
        session.step(InputState((0, 0), {}, {"shop_done"}))
        self.assertEqual(session.snapshot()["hold"], [])
        self.assertEqual(session.sim.day, 2)
        rows = session.step(press)
        second = next(row["data"]["inventory"]["items"] for row in rows if row["name"] == "gather_end")
        self.assertEqual(second, [item("I10", "bong_sung", 100.0)])


if __name__ == "__main__":
    unittest.main()
