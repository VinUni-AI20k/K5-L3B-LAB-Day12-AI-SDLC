"""Lát 2 (gather): hái, bắt cá, cooldown và bàn giao kho — PRD-0 mục F."""

import json
import unittest

from helpers import Workdir, events, frames, items, kinds_of, read_jsonl, run_headless, snapshots, write_json


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


class Harvest(unittest.TestCase):
    def test_nearest_ready_node_tie_breaks_by_id(self):
        with Workdir() as w:
            rows = run_gather(w, {
                "player": {"pos": [20, 0]},
                "nodes": [
                    {"id": "N10", "kind": "bong_sung", "pos": [21, 0]},
                    {"id": "N2", "kind": "bong_dien_dien", "pos": [19, 0]},
                ],
            }, 1, [{"tick": 0, "interact": True}])
            self.assertEqual([(e["name"], e["data"]) for e in events(rows)],
                             [("gather", {"node_id": "N2", "kind": "bong_dien_dien", "amount": 1})])
            snap = snapshot_at(rows, 1)
            self.assertEqual(kinds_of(snap["hold"]), ["bong_dien_dien"])
            self.assertEqual(snap["hold"][0]["id"], "I1")
            self.assertEqual(snap["hold"][0]["fresh"], 100)
            self.assertEqual({n["id"]: n["regrow_ticks"] for n in snap["nodes"]}, {"N2": 1200, "N10": 0})

    def test_gather_requires_surface_ready_node_and_range(self):
        cases = [
            {"player": {"pos": [20, 1]}, "nodes": [
                {"id": "N1", "kind": "bong_sung", "pos": [20, 0]}]},
            {"player": {"pos": [20, 0]}, "nodes": [
                {"id": "N1", "kind": "bong_sung", "pos": [20, 0], "regrow_ticks": 2}]},
            {"player": {"pos": [20, 0]}, "nodes": [
                {"id": "N1", "kind": "bong_sung", "pos": [30, 0]}]},
        ]
        for block in cases:
            with self.subTest(block=block), Workdir() as w:
                rows = run_gather(w, block, 1, [{"tick": 0, "interact": True}])
                self.assertEqual(events(rows, "gather"), [])

    def test_hold_full_does_not_harvest_or_start_regrow(self):
        with Workdir() as w:
            rows = run_gather(w, {
                "player": {"pos": [20, 0]},
                "hold": ["ca_loc"] * 12,
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
            }, 1, [{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "hold_full")[0]["data"],
                             {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
            node = snapshot_at(rows, 1)["nodes"][0]
            self.assertEqual(node["regrow_ticks"], 0)
            self.assertTrue(node["ready"])

    def test_dock_interaction_ends_before_harvesting(self):
        with Workdir() as w:
            rows = run_gather(w, {
                "player": {"pos": [2, 0]},
                "hold": ["ca_loc"],
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [2, 0]}],
            }, 1, [{"tick": 0, "interact": True}], inventory_out="inventory.json")
            named_events = events(rows)
            self.assertEqual([e["name"] for e in named_events], ["gather_end"])
            event_items = named_events[0]["data"]["inventory"]["items"]
            self.assertEqual(named_events[0]["data"]["reason"], "docked")
            self.assertEqual([(it["id"], it["kind"]) for it in event_items], [("I1", "ca_loc")])
            self.assertAlmostEqual(event_items[0]["fresh"], 100 - 1 / 120, places=3)
            with open(w.path("inventory.json"), encoding="utf-8") as f:
                file_items = json.load(f)["items"]
            self.assertEqual([(it["id"], it["kind"]) for it in file_items], [("I1", "ca_loc")])
            self.assertAlmostEqual(file_items[0]["fresh"], 100 - 1 / 120, places=12)

    def test_regrown_node_can_be_harvested_in_same_step(self):
        with Workdir() as w:
            rows = run_gather(w, {
                "player": {"pos": [20, 0]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0], "regrow_ticks": 1}],
            }, 1, [{"tick": 0, "interact": True}])
            self.assertEqual([(e["name"], e["data"]) for e in events(rows)],
                             [("node_regrown", {"node_id": "N1"}),
                              ("gather", {"node_id": "N1", "kind": "bong_sung", "amount": 1})])

    def test_final_tick_harvest_is_written_to_inventory_once(self):
        with Workdir() as w:
            rows = run_gather(w, {
                "player": {"pos": [50, 0]},
                "time_left_ticks": 1,
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [50, 0]}],
            }, 5, [{"tick": 0, "interact": True}], inventory_out="inventory.json")
            named_events = events(rows)
            self.assertEqual([e["name"] for e in named_events], ["gather", "gather_end"])
            self.assertEqual(named_events[-1]["data"]["reason"], "time")
            with open(w.path("inventory.json"), encoding="utf-8") as f:
                file_items = json.load(f)["items"]
            event_items = named_events[-1]["data"]["inventory"]["items"]
            self.assertEqual([(it["id"], it["kind"]) for it in file_items], [("I1", "bong_sung")])
            self.assertEqual([(it["id"], it["kind"]) for it in event_items], [("I1", "bong_sung")])
            self.assertEqual(file_items[0]["fresh"], 100)
            self.assertEqual(event_items[0]["fresh"], 100)


class Catch(unittest.TestCase):
    def test_catches_nearest_fish_with_id_tie_break_and_cooldown(self):
        with Workdir() as w:
            rows = run_gather(w, {
                "player": {"pos": [20, 5]},
                "fish": [
                    {"id": "F10", "kind": "ca_loc", "pos": [21, 5]},
                    {"id": "F2", "kind": "ca_linh", "pos": [19, 5]},
                ],
            }, 1, [{"tick": 0, "catch": True}])
            self.assertEqual(events(rows, "fish_caught")[0]["data"],
                             {"fish_id": "F2", "kind": "ca_linh", "yield": 3})
            snap = snapshot_at(rows, 1)
            self.assertEqual(snap["hold"], items("ca_linh", "ca_linh", "ca_linh"))
            self.assertEqual([f["id"] for f in snap["fish"]], ["F10"])
            self.assertEqual(snap["player"]["catch_cd_ticks"], 30)

    def test_catch_requires_underwater_in_range_and_expired_cooldown(self):
        cases = [
            ({"player": {"pos": [20, 0]}, "fish": [
                {"id": "F1", "kind": "ca_loc", "pos": [20, 5]}]}, 0),
            ({"player": {"pos": [20, 5]}, "fish": [
                {"id": "F1", "kind": "ca_loc", "pos": [30, 5]}]}, 0),
            ({"player": {"pos": [20, 5], "catch_cd_ticks": 2}, "fish": [
                {"id": "F1", "kind": "ca_loc", "pos": [20, 5]}]}, 1),
        ]
        for block, cooldown in cases:
            with self.subTest(block=block), Workdir() as w:
                rows = run_gather(w, block, 1, [{"tick": 0, "catch": True}])
                self.assertEqual(events(rows, "fish_caught"), [])
                snap = snapshot_at(rows, 1)
                self.assertEqual([fish["id"] for fish in snap["fish"]], ["F1"])
                self.assertEqual(snap["player"]["catch_cd_ticks"], cooldown)

    def test_hold_full_keeps_selected_fish_and_cooldown(self):
        with Workdir() as w:
            rows = run_gather(w, {
                "player": {"pos": [20, 5]},
                "hold": ["ca_loc"] * 10,
                "fish": [
                    {"id": "F1", "kind": "ca_linh", "pos": [20, 5]},
                    {"id": "F2", "kind": "ca_loc", "pos": [21, 5]},
                ],
            }, 1, [{"tick": 0, "catch": True}])
            self.assertEqual(events(rows, "hold_full")[0]["data"],
                             {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
            snap = snapshot_at(rows, 1)
            self.assertEqual([f["id"] for f in snap["fish"]], ["F1", "F2"])
            self.assertEqual(snap["player"]["catch_cd_ticks"], 0)


if __name__ == "__main__":
    unittest.main()
