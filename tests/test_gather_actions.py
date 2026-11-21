"""Ticket 03: kiểm hành vi qua CLI, JSONL và file kho, không import sim."""

import json
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherActions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(f"{ROOT}/game.contract.json", encoding="utf-8") as f:
            cls.tuning = json.load(f)["tuning"]
        cls.g = cls.tuning["gather"]
        cls.hz = cls.tuning["tick_hz"]

    def run_gather(self, block, inputs=(), ticks=1, existing_inventory=None):
        with Workdir() as w:
            # Các test tương tác P1 cần cá đứng yên khi dùng lại ở contract v1.1.
            scenario = {"player": {"pos": [50, 0]}, "nodes": [], "fish": [], "random_fish": False, **block}
            sc = write_json(w.path("scenario.json"), {"gather": scenario})
            inp = write_json(w.path("inputs.json"), frames(*inputs))
            inv = w.path("inventory.json")
            if existing_inventory is not None:
                with open(inv, "wb") as f:
                    f.write(existing_inventory)
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(ticks),
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                                     "--inventory-out", inv, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            try:
                with open(inv, "rb") as f:
                    inventory = f.read()
            except FileNotFoundError:
                inventory = None
            with open(out, "rb") as f:
                log = f.read()
            return rows, inventory, log

    @staticmethod
    def node(ident="N1", pos=None, regrow=0):
        return {"id": ident, "kind": "bong_sung", "pos": pos or [50, 0], "regrow_ticks": regrow}

    @staticmethod
    def fish(ident="F1", kind="ca_linh", pos=None):
        return {"id": ident, "kind": kind, "pos": pos or [50, 5]}

    def test_gather_nearest_ready_then_numeric_id(self):
        rows, _, _ = self.run_gather({"nodes": [self.node("N10", [49, 0]), self.node("N2", [51, 0]),
                                                              self.node("N1", [51.5, 0]), self.node("N0", regrow=2)]},
                                     [{"tick": 0, "interact": True}])
        amount = self.g["node_yield"]
        self.assertEqual([e["data"] for e in events(rows, "gather")],
                         [{"node_id": "N2", "kind": "bong_sung", "amount": amount}])
        self.assertEqual(snapshots(rows)[-1]["hold"], ["bong_sung"] * amount)

    def test_gather_uses_unrounded_distance(self):
        rows, _, _ = self.run_gather({"nodes": [self.node("N2", [51.0000004, 0]),
                                                              self.node("N10", [51.0000001, 0])]},
                                     [{"tick": 0, "interact": True}])
        self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N10")

    def test_gather_surface_threshold(self):
        for depth, count in ((self.g["surface_depth"], 1), (self.g["surface_depth"] + 0.000001, 0)):
            with self.subTest(depth=depth):
                rows, _, _ = self.run_gather({"player": {"pos": [50, depth]}, "nodes": [self.node()]},
                                             [{"tick": 0, "interact": True}])
                self.assertEqual(len(events(rows, "gather")), count)

    def test_gather_radius_includes_edge_and_excludes_outside(self):
        for offset, count in ((0, 1), (0.000001, 0)):
            with self.subTest(offset=offset):
                rows, _, _ = self.run_gather({"nodes": [self.node(pos=[50 + self.g["interact_radius"] + offset, 0])]},
                                             [{"tick": 0, "interact": True}])
                self.assertEqual(len(events(rows, "gather")), count)

    def test_gather_radius_uses_depth_as_well_as_horizontal_distance(self):
        rows, _, _ = self.run_gather({"player": {"pos": [50, self.g["surface_depth"]]},
                                      "nodes": [self.node(pos=[50 + self.g["interact_radius"], 0])]},
                                     [{"tick": 0, "interact": True}])
        self.assertEqual(events(rows, "gather"), [])

    def test_gather_full_preserves_node_and_hold(self):
        hold = ["ca_loc"] * self.g["hold_capacity"]
        rows, _, _ = self.run_gather({"hold": hold, "nodes": [self.node()]},
                                     [{"tick": 0, "interact": True}])
        self.assertEqual([e["data"] for e in events(rows, "hold_full")],
                         [{"action": "gather", "node_id": "N1", "required": self.g["node_yield"], "free": 0}])
        last = snapshots(rows)[-1]
        self.assertEqual(last["hold"], hold)
        self.assertEqual(last["nodes"][0]["regrow_ticks"], 0)
        self.assertTrue(last["nodes"][0]["ready"])
        self.assertEqual(events(rows, "gather"), [])

    def test_gather_exact_capacity_succeeds(self):
        amount = self.g["node_yield"]
        hold = ["ca_loc"] * (self.g["hold_capacity"] - amount)
        rows, _, _ = self.run_gather({"hold": hold, "nodes": [self.node()]},
                                     [{"tick": 0, "interact": True}])
        self.assertEqual(snapshots(rows)[-1]["hold"], hold + ["bong_sung"] * amount)
        self.assertEqual(events(rows, "hold_full"), [])

    def test_regrow_exact_tick_and_gather_in_same_step(self):
        delay = int(round(self.g["regrow_s"] * self.hz))
        rows, _, _ = self.run_gather({"nodes": [self.node()]},
                                     [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                                      {"tick": delay, "interact": True}], ticks=delay + 1)
        by_tick = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual(by_tick[1]["nodes"][0]["regrow_ticks"], delay)
        self.assertEqual(by_tick[delay]["nodes"][0]["regrow_ticks"], 1)
        self.assertEqual([e["tick"] for e in events(rows, "gather")], [1, delay + 1])
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "node_regrown")],
                         [(delay + 1, {"node_id": "N1"})])
        self.assertEqual([e["name"] for e in events(rows) if e["tick"] == delay + 1],
                         ["node_regrown", "gather"])

    def test_held_interact_does_not_gather_again_after_regrow(self):
        delay = int(round(self.g["regrow_s"] * self.hz))
        rows, _, _ = self.run_gather({"nodes": [self.node()]},
                                     [{"tick": 0, "interact": True}], ticks=delay + 2)
        self.assertEqual(len(events(rows, "gather")), 1)
        self.assertEqual(len(events(rows, "node_regrown")), 1)
        self.assertTrue(snapshots(rows)[-1]["nodes"][0]["ready"])

    def test_no_ready_node_is_noop(self):
        rows, _, _ = self.run_gather({"nodes": [self.node(regrow=2)]},
                                     [{"tick": 0, "interact": True}])
        self.assertEqual(events(rows), [])
        self.assertEqual(snapshots(rows)[-1]["hold"], [])

    def test_catch_yield_removes_whole_school(self):
        for kind, amount in self.g["fish_yield"].items():
            with self.subTest(kind=kind):
                rows, _, _ = self.run_gather({"player": {"pos": [50, 5]}, "fish": [self.fish(kind=kind)]},
                                             [{"tick": 0, "catch": True}])
                self.assertEqual([e["data"] for e in events(rows, "fish_caught")],
                                 [{"fish_id": "F1", "kind": kind, "yield": amount}])
                last = snapshots(rows)[-1]
                self.assertEqual(last["hold"], [kind] * amount)
                self.assertEqual(last["fish"], [])
                self.assertEqual(last["player"]["catch_cd_ticks"],
                                 int(round(self.g["catch_cooldown_s"] * self.hz)))

    def test_catch_nearest_then_numeric_id(self):
        rows, _, _ = self.run_gather({"player": {"pos": [50, 5]},
                                      "fish": [self.fish("F10", pos=[49, 5]), self.fish("F2", pos=[51, 5]),
                                               self.fish("F1", pos=[51.5, 5])]}, [{"tick": 0, "catch": True}])
        self.assertEqual(events(rows, "fish_caught")[0]["data"]["fish_id"], "F2")
        self.assertEqual([f["id"] for f in snapshots(rows)[-1]["fish"]], ["F1", "F10"])

    def test_catch_uses_unrounded_distance(self):
        rows, _, _ = self.run_gather({"player": {"pos": [50, 5]},
                                      "fish": [self.fish("F2", pos=[51.0000004, 5]),
                                               self.fish("F10", pos=[51.0000001, 5])]},
                                     [{"tick": 0, "catch": True}])
        self.assertEqual(events(rows, "fish_caught")[0]["data"]["fish_id"], "F10")

    def test_catch_full_keeps_school_no_fallback_or_cooldown(self):
        hold = ["bong_sung"] * (self.g["hold_capacity"] - 1)
        rows, _, _ = self.run_gather({"player": {"pos": [50, 5]}, "hold": hold,
                                      "fish": [self.fish(), self.fish("F2", "ca_loc", [51, 5])]},
                                     [{"tick": 0, "catch": True}])
        self.assertEqual([e["data"] for e in events(rows, "hold_full")],
                         [{"action": "catch", "fish_id": "F1", "required": self.g["fish_yield"]["ca_linh"], "free": 1}])
        last = snapshots(rows)[-1]
        self.assertEqual(last["hold"], hold)
        self.assertEqual(len(last["fish"]), 2)
        self.assertEqual(last["player"]["catch_cd_ticks"], 0)
        self.assertEqual(events(rows, "fish_caught"), [])

    def test_catch_exact_capacity_succeeds(self):
        amount = self.g["fish_yield"]["ca_linh"]
        hold = ["bong_sung"] * (self.g["hold_capacity"] - amount)
        rows, _, _ = self.run_gather({"player": {"pos": [50, 5]}, "hold": hold, "fish": [self.fish()]},
                                     [{"tick": 0, "catch": True}])
        self.assertEqual(snapshots(rows)[-1]["hold"], hold + ["ca_linh"] * amount)
        self.assertEqual(events(rows, "hold_full"), [])

    def test_catch_surface_is_noop(self):
        rows, _, _ = self.run_gather({"player": {"pos": [50, self.g["surface_depth"]]},
                                      "fish": [self.fish(pos=[50, self.g["surface_depth"] + 0.1])]},
                                     [{"tick": 0, "catch": True}])
        self.assertEqual(events(rows), [])
        self.assertEqual(len(snapshots(rows)[-1]["fish"]), 1)
        self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"], 0)

    def test_catch_radius_includes_edge_and_excludes_outside(self):
        for offset, count in ((0, 1), (0.000001, 0)):
            with self.subTest(offset=offset):
                rows, _, _ = self.run_gather({"player": {"pos": [50, 5]},
                                              "fish": [self.fish(pos=[50 + self.g["catch_radius"] + offset, 5])]},
                                             [{"tick": 0, "catch": True}])
                self.assertEqual(len(events(rows, "fish_caught")), count)
                if count == 0:
                    self.assertEqual(events(rows), [])
                    self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"], 0)

    def test_catch_without_fish_is_noop(self):
        rows, _, _ = self.run_gather({"player": {"pos": [50, 5]}}, [{"tick": 0, "catch": True}])
        self.assertEqual(events(rows), [])
        self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"], 0)

    def test_catch_cooldown_boundary(self):
        delay = int(round(self.g["catch_cooldown_s"] * self.hz))
        rows, _, _ = self.run_gather({"player": {"pos": [50, 5]}, "fish": [self.fish("F2"), self.fish("F10")]},
                                     [{"tick": 0, "catch": True}, {"tick": 1, "catch": False},
                                      {"tick": delay - 2, "catch": True}, {"tick": delay - 1, "catch": False},
                                      {"tick": delay, "catch": True}], ticks=delay + 1)
        self.assertEqual([(e["tick"], e["data"]["fish_id"]) for e in events(rows, "fish_caught")],
                         [(1, "F2"), (delay + 1, "F10")])
        by_tick = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual(by_tick[delay]["player"]["catch_cd_ticks"], 1)

    def test_catch_fixture_cooldown_decrements_before_action(self):
        for cd, count in ((1, 1), (2, 0)):
            with self.subTest(cooldown=cd):
                rows, _, _ = self.run_gather({"player": {"pos": [50, 5], "catch_cd_ticks": cd},
                                              "fish": [self.fish()]}, [{"tick": 0, "catch": True}])
                self.assertEqual(len(events(rows, "fish_caught")), count)

    def test_dock_precedes_gather_and_time_and_writes_once(self):
        rows, inventory, _ = self.run_gather({"player": {"pos": self.g["dock_pos"]},
                                              "nodes": [self.node(pos=self.g["dock_pos"])],
                                              "hold": ["ca_loc"], "time_left_ticks": 1},
                                             [{"tick": 0, "interact": True, "catch": True}], ticks=10)
        saved = {"items": {"ca_loc": 1}}
        self.assertEqual([(e["name"], e["data"]) for e in events(rows)],
                         [("gather_end", {"reason": "docked", "inventory": saved})])
        self.assertEqual(json.loads(inventory), saved)
        self.assertEqual(rows[-1]["ticks"], 1)
        self.assertEqual(rows[-1]["reason"], "docked")

    def test_submerged_dock_precedes_catch(self):
        pos = [self.g["dock_pos"][0], self.g["dock_pos"][1] + self.g["dock_radius"]]
        rows, inventory, _ = self.run_gather({"player": {"pos": pos}, "fish": [self.fish(pos=pos)]},
                                             [{"tick": 0, "interact": True, "catch": True}])
        self.assertEqual([e["name"] for e in events(rows)], ["gather_end"])
        self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
        self.assertEqual(json.loads(inventory), {"items": {}})
        self.assertEqual(len(snapshots(rows)[-1]["fish"]), 1)

    def test_last_tick_action_included_in_saved_inventory(self):
        cases = [({"nodes": [self.node()]}, {"interact": True}, "gather", "bong_sung", self.g["node_yield"]),
                 ({"player": {"pos": [50, 5]}, "fish": [self.fish()]}, {"catch": True},
                  "fish_caught", "ca_linh", self.g["fish_yield"]["ca_linh"])]
        for block, buttons, name, kind, amount in cases:
            with self.subTest(action=name):
                rows, inventory, _ = self.run_gather({**block, "time_left_ticks": 1},
                                                     [{"tick": 0, **buttons}], ticks=10)
                self.assertEqual([e["name"] for e in events(rows)], [name, "gather_end"])
                self.assertEqual(json.loads(inventory), {"items": {kind: amount}})
                self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], json.loads(inventory))
                self.assertEqual(rows[-1]["reason"], "time")

    def test_tick_limit_does_not_create_or_overwrite_inventory(self):
        for original in (None, b"existing inventory must remain byte-for-byte\n"):
            with self.subTest(existing=original is not None):
                rows, inventory, _ = self.run_gather({"nodes": [self.node()]},
                                                     [{"tick": 0, "interact": True}], existing_inventory=original)
                self.assertEqual(len(events(rows, "gather")), 1)
                self.assertEqual(events(rows, "gather_end"), [])
                self.assertEqual(inventory, original)
                self.assertEqual(rows[-1]["reason"], "tick_limit")

    def test_actions_are_deterministic_bytes(self):
        block = {"player": {"pos": [50, 5]}, "fish": [self.fish("F10"), self.fish("F2")], "time_left_ticks": 1}
        first = self.run_gather(block, [{"tick": 0, "catch": True}])
        second = self.run_gather(block, [{"tick": 0, "catch": True}])
        self.assertEqual(first[2], second[2])
        self.assertEqual(first[1], second[1])


if __name__ == "__main__":
    unittest.main()
