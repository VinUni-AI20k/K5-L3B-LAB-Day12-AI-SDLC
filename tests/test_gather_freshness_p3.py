"""Phase 3 gather: item freshness, spoilage, and v1.2 handoff."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def run_gather(w, block, ticks, inputs=None, inventory_out=None):
    scenario = write_json(w.path("scenario.json"), {"gather": block})
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", scenario,
            "--snapshot-every", "1", "--out", w.path("run.jsonl")]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("inputs.json"), frames(*inputs))]
    if inventory_out is not None:
        args += ["--inventory-out", w.path(inventory_out)]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("run.jsonl"))


def snapshot_at(rows, tick):
    return next(row for row in snapshots(rows) if row["tick"] == tick)


class GatherFreshness(unittest.TestCase):
    def test_threshold_item_spoils_on_tick_one_only(self):
        with Workdir() as w:
            rows = run_gather(w, {
                "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
                "random_fish": False,
                "monsters": [],
            }, 2)

            spoiled = events(rows, "spoiled")
            self.assertEqual([(event["tick"], event["data"]) for event in spoiled], [
                (1, {"item_id": "I1", "kind": "ca_linh", "location": "hold"}),
            ])
            self.assertEqual(snapshot_at(rows, 1)["hold"][0]["id"], "I1")
            self.assertAlmostEqual(snapshot_at(rows, 1)["hold"][0]["fresh"], 30 - 1 / 120, places=3)
            self.assertAlmostEqual(snapshot_at(rows, 2)["hold"][0]["fresh"], 30 - 2 / 120, places=3)

    def test_harvest_and_catch_start_fresh_and_decay_from_next_tick(self):
        with Workdir() as w:
            harvested = run_gather(w, {
                "player": {"pos": [20, 0]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
                "random_fish": False,
                "monsters": [],
            }, 2, [{"tick": 0, "interact": True}])
            self.assertEqual(events(harvested, "gather")[0]["data"],
                             {"node_id": "N1", "kind": "bong_sung", "amount": 1})
            harvest_item = snapshot_at(harvested, 1)["hold"][0]
            self.assertEqual((harvest_item["id"], harvest_item["kind"], harvest_item["fresh"]),
                             ("I1", "bong_sung", 100))
            self.assertAlmostEqual(snapshot_at(harvested, 2)["hold"][0]["fresh"],
                                   100 - 1 / 120, places=3)

        with Workdir() as w:
            caught = run_gather(w, {
                "player": {"pos": [20, 5]},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20, 5]}],
                "random_fish": False,
                "monsters": [],
            }, 2, [{"tick": 0, "catch": True}])
            self.assertEqual(events(caught, "fish_caught")[0]["data"],
                             {"fish_id": "F1", "kind": "ca_loc", "yield": 1})
            catch_item = snapshot_at(caught, 1)["hold"][0]
            self.assertEqual((catch_item["id"], catch_item["kind"], catch_item["fresh"]),
                             ("I1", "ca_loc", 100))
            self.assertAlmostEqual(snapshot_at(caught, 2)["hold"][0]["fresh"],
                                   100 - 1 / 120, places=3)

    def test_dock_handoff_writes_sorted_items_at_full_precision(self):
        with Workdir() as w:
            rows = run_gather(w, {
                "hold": [
                    {"id": "I10", "kind": "ca_loc", "fresh": 100},
                    {"id": "I2", "kind": "ca_linh", "fresh": 80},
                ],
                "random_fish": False,
                "monsters": [],
            }, 1, [{"tick": 0, "interact": True}], inventory_out="inventory.json")

            event_items = events(rows, "gather_end")[0]["data"]["inventory"]["items"]
            with open(w.path("inventory.json"), encoding="utf-8") as f:
                file_items = json.load(f)["items"]
            self.assertEqual([item["id"] for item in event_items], ["I2", "I10"])
            self.assertEqual([(item["id"], item["kind"]) for item in file_items],
                             [("I2", "ca_linh"), ("I10", "ca_loc")])
            self.assertAlmostEqual(file_items[0]["fresh"], 80 - 1 / 120, places=12)
            self.assertAlmostEqual(file_items[1]["fresh"], 100 - 1 / 120, places=12)
            self.assertAlmostEqual(event_items[0]["fresh"], file_items[0]["fresh"], places=3)
            self.assertAlmostEqual(event_items[1]["fresh"], file_items[1]["fresh"], places=3)

    def test_faint_loses_individual_items_lifo_and_exports_empty_inventory(self):
        with Workdir() as w:
            rows = run_gather(w, {
                "player": {"pos": [20, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                "hold": [
                    {"id": "I2", "kind": "ca_loc", "fresh": 70},
                    {"id": "I8", "kind": "ca_linh", "fresh": 40},
                ],
                "random_fish": False,
                "monsters": [],
            }, 1, inventory_out="inventory.json")

            faint = events(rows, "faint")[0]["data"]
            self.assertEqual([item["id"] for item in faint["lost"]], ["I8", "I2"])
            self.assertEqual(faint["cause"], "choke")
            self.assertEqual(events(rows, "gather_end")[0]["data"],
                             {"reason": "fainted", "inventory": {"items": []}})
            self.assertEqual(snapshot_at(rows, 1)["hold"], [])
            with open(w.path("inventory.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})


if __name__ == "__main__":
    unittest.main()
