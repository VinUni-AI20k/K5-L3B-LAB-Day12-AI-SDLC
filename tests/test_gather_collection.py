"""Phase 1, Lát 2: thu thập ở gather và bàn giao file kho cho quan."""

import copy
import json
import os
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherCollection(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.g = self.tuning["gather"]

    def session(self, block, tuning=None):
        fixture = {"nodes": [], "fish": [], **block}
        return Session("gather", tuning or self.tuning, fixture, 1)

    @staticmethod
    def step(session, player):
        return session.step(player.advance(session.tick))

    def test_harvest_edge_radius_and_numeric_id_tie(self):
        s = self.session({"player": {"pos": [20, 0]}, "nodes": [
            {"id": "N10", "kind": "bong_sung", "pos": [18, 0]},
            {"id": "N2", "kind": "bong_dien_dien", "pos": [22, 0]}]})
        p = InputPlayer([{"tick": 0, "interact": True}])
        first = self.step(s, p)
        self.assertEqual([(e["name"], e["data"]) for e in first], [
            ("gather", {"node_id": "N2", "kind": "bong_dien_dien", "amount": self.g["node_yield"]})])
        self.assertEqual(s.sim.hold, ["bong_dien_dien"] * self.g["node_yield"])
        self.assertEqual(next(n for n in s.sim.nodes if n["id"] == "N2")["regrow_ticks"],
                         int(round(self.g["regrow_s"] * 60)))
        self.assertEqual(self.step(s, p), [], "giữ interact không hái thêm")

    def test_harvest_nearest_and_surface_only(self):
        nodes = [{"id": "N2", "kind": "bong_sung", "pos": [22, 0]},
                 {"id": "N10", "kind": "bong_dien_dien", "pos": [20.5, 0]}]
        s = self.session({"player": {"pos": [20, 0]}, "nodes": nodes})
        picked = self.step(s, InputPlayer([{"tick": 0, "interact": True}]))
        self.assertEqual(picked[0]["data"]["node_id"], "N10", "gần nhất ưu tiên trước id")
        s = self.session({"player": {"pos": [20, 1]}, "nodes": nodes})
        self.assertEqual(self.step(s, InputPlayer([{"tick": 0, "interact": True}])), [])

    def test_dock_precedes_harvest_at_boundary(self):
        dock_edge = [self.g["dock_pos"][0] + self.g["dock_radius"], 0]
        s = self.session({"player": {"pos": dock_edge}, "nodes": [
            {"id": "N1", "kind": "bong_sung", "pos": dock_edge}]})
        rows = self.step(s, InputPlayer([{"tick": 0, "interact": True}]))
        self.assertEqual([r["name"] for r in rows], ["gather_end"])
        self.assertEqual(rows[0]["data"]["reason"], "docked")
        self.assertEqual(s.sim.hold, [])

    def test_regrown_node_can_be_harvested_same_tick(self):
        s = self.session({"player": {"pos": [20, 0]}, "nodes": [
            {"id": "N1", "kind": "bong_sung", "pos": [20, 0], "regrow_ticks": 1}]})
        rows = self.step(s, InputPlayer([{"tick": 0, "interact": True}]))
        self.assertEqual([r["name"] for r in rows], ["node_regrown", "gather"])
        self.assertEqual(rows[0]["data"], {"node_id": "N1"})
        self.assertEqual(s.sim.nodes[0]["regrow_ticks"], int(round(self.g["regrow_s"] * 60)))

    def test_node_not_ready_cannot_be_harvested(self):
        s = self.session({"player": {"pos": [20, 0]}, "nodes": [
            {"id": "N1", "kind": "bong_sung", "pos": [20, 0], "regrow_ticks": 2}]})
        p = InputPlayer([{"tick": 0, "interact": True}])
        self.assertEqual(self.step(s, p), [])
        self.assertEqual(s.sim.nodes[0]["regrow_ticks"], 1)
        self.assertEqual(s.sim.hold, [])
        self.assertEqual([r["name"] for r in self.step(s, p)], ["node_regrown"])
        self.assertEqual(s.sim.hold, [], "nút được hái chỉ khi có cạnh lên mới")

    def test_harvest_full_does_not_change_node_or_try_another(self):
        hold = ["ca_loc"] * self.g["hold_capacity"]
        s = self.session({"player": {"pos": [20, 0]}, "hold": hold, "nodes": [
            {"id": "N2", "kind": "bong_sung", "pos": [20, 0]},
            {"id": "N10", "kind": "bong_dien_dien", "pos": [21, 0]}]})
        rows = self.step(s, InputPlayer([{"tick": 0, "interact": True}]))
        self.assertEqual([(r["name"], r["data"]) for r in rows], [
            ("hold_full", {"action": "gather", "node_id": "N2",
                           "required": self.g["node_yield"], "free": 0})])
        self.assertEqual(s.sim.hold, hold)
        self.assertTrue(all(n["regrow_ticks"] == 0 for n in s.sim.nodes))

    def test_node_yield_comes_from_tuning(self):
        tuning = copy.deepcopy(self.tuning)
        tuning["gather"]["node_yield"] = 2
        s = self.session({"player": {"pos": [20, 0]}, "nodes": [
            {"id": "N1", "kind": "bong_sung", "pos": [20, 0]}]}, tuning=tuning)
        rows = self.step(s, InputPlayer([{"tick": 0, "interact": True}]))
        self.assertEqual(rows[0]["data"]["amount"], 2)
        self.assertEqual(s.sim.hold, ["bong_sung", "bong_sung"])

    def test_catch_underwater_radius_tie_yield_and_edge(self):
        s = self.session({"player": {"pos": [20, 5]}, "fish": [
            {"id": "F10", "kind": "ca_loc", "pos": [18, 5]},
            {"id": "F2", "kind": "ca_linh", "pos": [22, 5]}]})
        p = InputPlayer([{"tick": 0, "catch": True}])
        rows = self.step(s, p)
        self.assertEqual([(r["name"], r["data"]) for r in rows], [
            ("fish_caught", {"fish_id": "F2", "kind": "ca_linh", "yield": self.g["fish_yield"]["ca_linh"]})])
        self.assertEqual(s.sim.hold, ["ca_linh"] * self.g["fish_yield"]["ca_linh"])
        self.assertEqual([f["id"] for f in s.sim.fish], ["F10"])
        self.assertEqual(s.sim.catch_cd_ticks, int(round(self.g["catch_cooldown_s"] * 60)))
        self.assertEqual(self.step(s, p), [], "giữ catch không bắt thêm")

    def test_catch_nearest_and_invalid_phase_or_range(self):
        fish = [{"id": "F2", "kind": "ca_loc", "pos": [22, 5]},
                {"id": "F10", "kind": "ca_linh", "pos": [20.5, 5]}]
        s = self.session({"player": {"pos": [20, 5]}, "fish": fish})
        self.assertEqual(self.step(s, InputPlayer([{"tick": 0, "catch": True}]))[0]["data"]["fish_id"], "F10")
        for pos, lone_fish in (([20, 0], [{"id": "F1", "kind": "ca_loc", "pos": [20, 1]}]),
                               ([20, 5], [{"id": "F1", "kind": "ca_loc", "pos": [23, 5]}])):
            s = self.session({"player": {"pos": pos}, "fish": lone_fish})
            self.assertEqual(self.step(s, InputPlayer([{"tick": 0, "catch": True}])), [])
            self.assertEqual(s.sim.catch_cd_ticks, 0)

    def test_catch_cooldown_available_at_t_plus_l(self):
        cooldown = int(round(self.g["catch_cooldown_s"] * 60))
        s = self.session({"player": {"pos": [20, 5]}, "fish": [
            {"id": "F1", "kind": "ca_loc", "pos": [20, 5]},
            {"id": "F2", "kind": "ca_loc", "pos": [21, 5]}]})
        p = InputPlayer([{"tick": 0, "catch": True}, {"tick": 1, "catch": False},
                         {"tick": 2, "catch": True}, {"tick": 3, "catch": False},
                         {"tick": cooldown, "catch": True}])
        catches = []
        for _ in range(cooldown + 1):
            catches.extend(r for r in self.step(s, p) if r["name"] == "fish_caught")
        self.assertEqual([(r["tick"], r["data"]["fish_id"]) for r in catches],
                         [(1, "F1"), (cooldown + 1, "F2")])

    def test_fish_hold_full_never_takes_partial_or_fallback(self):
        for count in (10, 11):
            with self.subTest(held=count):
                hold = ["bong_sung"] * count
                s = self.session({"player": {"pos": [20, 5]}, "hold": hold, "fish": [
                    {"id": "F2", "kind": "ca_linh", "pos": [20, 5]},
                    {"id": "F10", "kind": "ca_loc", "pos": [21, 5]}]})
                rows = self.step(s, InputPlayer([{"tick": 0, "catch": True}]))
                self.assertEqual([(r["name"], r["data"]) for r in rows], [
                    ("hold_full", {"action": "catch", "fish_id": "F2",
                                   "required": self.g["fish_yield"]["ca_linh"],
                                   "free": self.g["hold_capacity"] - count})])
                self.assertEqual(s.sim.hold, hold)
                self.assertEqual([f["id"] for f in s.sim.fish], ["F2", "F10"])
                self.assertEqual(s.sim.catch_cd_ticks, 0)

    def test_last_tick_harvest_catch_and_dock(self):
        cases = [
            ({"player": {"pos": [20, 0]}, "nodes": [
                {"id": "N1", "kind": "bong_sung", "pos": [20, 0]}]}, "interact", ["gather", "gather_end"], "time"),
            ({"player": {"pos": [20, 5]}, "fish": [
                {"id": "F1", "kind": "ca_loc", "pos": [20, 5]}]}, "catch", ["fish_caught", "gather_end"], "time"),
            ({"player": {"pos": self.g["dock_pos"]}}, "interact", ["gather_end"], "docked"),
        ]
        for block, button, names, reason in cases:
            with self.subTest(button=button, reason=reason):
                s = self.session({**block, "time_left_ticks": 1})
                rows = self.step(s, InputPlayer([{"tick": 0, button: True}]))
                self.assertEqual([r["name"] for r in rows], names)
                self.assertEqual(rows[-1]["data"]["reason"], reason)
                self.assertEqual(rows[-1]["data"]["inventory"], {"items": s.sim.inventory_items()})

    def test_headless_inventory_round_trip_into_quan(self):
        with Workdir() as w:
            scenario = write_json(w.path("g.json"), {"gather": {"player": {"pos": [20, 0]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
                "time_left_ticks": 1}})
            inputs = write_json(w.path("i.json"), frames({"tick": 0, "interact": True}))
            inventory = w.path("catch.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", scenario, "--inputs", inputs,
                                     "--inventory-out", inventory, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            with open(inventory, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved, events(rows, "gather_end")[0]["data"]["inventory"])
            self.assertEqual(saved, {"items": {"bong_sung": self.g["node_yield"]}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--inventory", inventory, "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], saved["items"])

    def test_tick_limit_neither_creates_nor_overwrites_inventory(self):
        with Workdir() as w:
            inventory = w.path("catch.json")
            for original in (None, b"existing inventory\n"):
                if original is not None:
                    with open(inventory, "wb") as f:
                        f.write(original)
                code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                         "--inventory-out", inventory, "--out", w.path("g.jsonl"))
                self.assertEqual(code, 0, err)
                self.assertEqual(read_jsonl(w.path("g.jsonl"))[-1]["reason"], "tick_limit")
                if original is None:
                    self.assertFalse(os.path.exists(inventory))
                else:
                    with open(inventory, "rb") as f:
                        self.assertEqual(f.read(), original)

    def test_fainted_clears_hold_before_inventory_written(self):
        """Phụ thuộc Lát 1: để thất bại thật đến khi Người 1 hoàn thiện ngất."""
        with Workdir() as w:
            scenario = write_json(w.path("g.json"), {"gather": {
                "player": {"pos": [20, 5], "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 59},
                "hold": ["ca_loc", "bong_sung"], "time_left_ticks": 2}})
            inventory = w.path("catch.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", scenario, "--inventory-out", inventory,
                                     "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            self.assertEqual([r["name"] for r in events(rows)], ["choke", "faint", "gather_end"])
            self.assertEqual(events(rows, "faint")[0]["data"]["lost"], ["bong_sung", "ca_loc"])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": {}})
            with open(inventory, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


if __name__ == "__main__":
    unittest.main()
