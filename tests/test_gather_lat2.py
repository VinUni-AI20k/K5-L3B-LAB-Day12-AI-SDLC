"""Lát 2: hái/bắt, giỏ nguyên khối và thứ tự xử lý qua API mô phỏng."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


def node(ident="N1", pos=(20, 0), kind="bong_sung", regrow_ticks=0):
    return {"id": ident, "pos": list(pos), "kind": kind, "regrow_ticks": regrow_ticks}


def fish(ident="F1", pos=(20, 5), kind="ca_loc"):
    return {"id": ident, "pos": list(pos), "kind": kind}


def press(sim, **buttons):
    return sim.step(InputPlayer([{"tick": 0, **buttons}]).advance(0))


def names(events):
    return [name for name, _ in events]


def data_for(events, name):
    return [data for event_name, data in events if event_name == name]


class GatherLat2(unittest.TestCase):
    def sim(self, *, pos=(20, 0), nodes=(), fish=(), hold=(), player=None, tuning=None,
            time_left_ticks=1000):
        preset = load_contract()["tuning"]
        preset["gather"].update(tuning or {})
        scenario = {
            "player": {"pos": list(pos), **(player or {})},
            "nodes": list(nodes), "fish": list(fish), "hold": list(hold),
            "random_fish": False, "time_left_ticks": time_left_ticks,
        }
        return GatherSim(preset, scenario, Streams(1), IdAllocator())

    def test_gather_chooses_nearest_ready_node(self):
        sim = self.sim(nodes=[node("N1", (20, 0), regrow_ticks=10),
                              node("N2", (21.5, 0)), node("N10", (20.5, 0))])
        ev = press(sim, interact=True)
        self.assertEqual(data_for(ev, "gather"), [{
            "node_id": "N10", "kind": "bong_sung", "amount": sim.t["node_yield"],
        }])
        self.assertEqual(sim.nodes[0]["regrow_ticks"], 9)
        self.assertEqual(sim.nodes[1]["regrow_ticks"], 0)

    def test_gather_distance_tie_uses_natural_id(self):
        sim = self.sim(nodes=[node("N10", (19, 0)), node("N2", (21, 0))])
        ev = press(sim, interact=True)
        self.assertEqual(data_for(ev, "gather")[0]["node_id"], "N2")
        self.assertEqual(len(data_for(ev, "gather")), 1)

    def test_gather_radius_includes_boundary(self):
        radius = load_contract()["tuning"]["gather"]["interact_radius"]
        for offset, expected in ((radius, True), (radius + 0.001, False)):
            with self.subTest(offset=offset):
                sim = self.sim(nodes=[node(pos=(20 + offset, 0))])
                ev = press(sim, interact=True)
                self.assertEqual("gather" in names(ev), expected)
                self.assertEqual(bool(sim.hold), expected)

    def test_gather_only_at_surface_including_depth_boundary(self):
        surface = load_contract()["tuning"]["gather"]["surface_depth"]
        for depth, expected in ((surface, True), (surface + 0.001, False)):
            with self.subTest(depth=depth):
                sim = self.sim(pos=(20, depth), nodes=[node()])
                ev = press(sim, interact=True)
                self.assertEqual("gather" in names(ev), expected)

    def test_surface_and_dive_gate_actions_after_movement(self):
        surface = load_contract()["tuning"]["gather"]["surface_depth"]
        for depth, direction, transition, action in (
            (surface + 0.01, -1, "surface", "gather"),
            (surface - 0.01, 1, "dive", "fish_caught"),
        ):
            with self.subTest(transition=transition):
                sim = self.sim(pos=(20, depth), nodes=[node()],
                               fish=[fish(pos=(20, surface + 0.1))],
                               tuning={"ramp_max_ticks": 0})
                ev = press(sim, move=[0, direction], interact=True, catch=True)
                self.assertEqual(names(ev), [transition, action])

    def test_action_radius_uses_position_after_movement(self):
        preset = load_contract()["tuning"]
        step_distance = preset["gather"]["swim_speed"] / preset["tick_hz"]
        for button, action, depth, radius_key in (
            ("interact", "gather", 0, "interact_radius"),
            ("catch", "fish_caught", 5, "catch_radius"),
        ):
            with self.subTest(action=action):
                target_pos = (20 + preset["gather"][radius_key] + step_distance / 2, depth)
                sim = self.sim(pos=(20, depth),
                               nodes=[node(pos=target_pos)] if depth == 0 else [],
                               fish=[fish(pos=target_pos)] if depth else [],
                               tuning={"ramp_max_ticks": 0})
                ev = press(sim, move=[1, 0], **{button: True})
                self.assertIn(action, names(ev))

    def test_node_yield_is_tuned_and_added_atomically_in_pickup_order(self):
        for initial_hold, succeeds in ((["ca_loc"] * 2, True), (["ca_loc"] * 3, False)):
            with self.subTest(succeeds=succeeds):
                sim = self.sim(nodes=[node()], hold=initial_hold,
                               tuning={"hold_capacity": 4, "node_yield": 2})
                before_nodes = copy.deepcopy(sim.nodes)
                ev = press(sim, interact=True)
                if succeeds:
                    self.assertEqual(sim.hold, initial_hold + ["bong_sung"] * 2)
                    self.assertEqual(data_for(ev, "gather")[0]["amount"], 2)
                else:
                    self.assertEqual(names(ev), ["hold_full"])
                    self.assertEqual(data_for(ev, "hold_full"), [{"required": 2, "free": 1}])
                    self.assertEqual(sim.hold, initial_hold)
                    self.assertEqual(sim.nodes, before_nodes)
                    self.assertEqual(sim.catch_cd_ticks, 0)

    def test_regrow_counter_starts_after_pick_and_can_be_picked_when_expiring(self):
        sim = self.sim(nodes=[node()], tuning={"regrow_s": 0.1})
        ticks = round(sim.t["regrow_s"] * load_contract()["tuning"]["tick_hz"])
        press(sim, interact=True)
        self.assertEqual(sim.nodes[0]["regrow_ticks"], ticks)
        for _ in range(ticks - 1):
            self.assertNotIn("node_regrown", names(press(sim)))
        self.assertEqual(sim.nodes[0]["regrow_ticks"], 1)
        ev = press(sim, interact=True)
        self.assertEqual(names(ev), ["node_regrown", "gather"])
        self.assertEqual(data_for(ev, "node_regrown"), [{"node_id": "N1"}])
        self.assertEqual(sim.nodes[0]["regrow_ticks"], ticks)
        self.assertEqual(sim.hold, ["bong_sung"] * (2 * sim.t["node_yield"]))

    def test_simultaneous_regrowth_emits_once_in_natural_id_order(self):
        sim = self.sim(nodes=[node("N10", regrow_ticks=1), node("N2", regrow_ticks=1),
                              node("N1")])
        ev = press(sim)
        self.assertEqual(ev, [("node_regrown", {"node_id": "N2"}),
                              ("node_regrown", {"node_id": "N10"})])
        self.assertEqual(press(sim), [])

    def test_catch_chooses_nearest_fish_before_id(self):
        sim = self.sim(pos=(20, 5), fish=[fish("F2", (21.5, 5)), fish("F10", (20.5, 5))])
        ev = press(sim, catch=True)
        self.assertEqual(data_for(ev, "fish_caught"), [{
            "fish_id": "F10", "kind": "ca_loc", "yield": sim.t["fish_yield"]["ca_loc"],
        }])
        self.assertEqual([f["id"] for f in sim.fish], ["F2"])

    def test_catch_distance_tie_uses_natural_id(self):
        sim = self.sim(pos=(20, 5), fish=[fish("F10", (19, 5)), fish("F2", (21, 5))])
        ev = press(sim, catch=True)
        self.assertEqual(data_for(ev, "fish_caught")[0]["fish_id"], "F2")
        self.assertEqual([f["id"] for f in sim.fish], ["F10"])

    def test_catch_radius_and_surface_boundary(self):
        g = load_contract()["tuning"]["gather"]
        for depth, offset, expected in (
            (5, g["catch_radius"], True),
            (5, g["catch_radius"] + 0.001, False),
            (g["surface_depth"], 0, False),
        ):
            with self.subTest(depth=depth, offset=offset):
                target_depth = depth if depth > g["surface_depth"] else depth + 0.01
                sim = self.sim(pos=(20, depth), fish=[fish(pos=(20 + offset, target_depth))])
                ev = press(sim, catch=True)
                self.assertEqual("fish_caught" in names(ev), expected)
                self.assertEqual(bool(sim.hold), expected)

    def test_fish_yield_uses_kind_tuning_and_appends_all_items(self):
        for kind, count in (("ca_linh", 2), ("ca_loc", 4)):
            with self.subTest(kind=kind):
                sim = self.sim(pos=(20, 5), fish=[fish(kind=kind)], hold=["bong_sung"],
                               tuning={"fish_yield": {"ca_linh": 2, "ca_loc": 4}})
                ev = press(sim, catch=True)
                self.assertEqual(sim.hold, ["bong_sung"] + [kind] * count)
                self.assertEqual(data_for(ev, "fish_caught")[0]["yield"], count)
                self.assertEqual(sim.fish, [])

    def test_full_hold_keeps_nearest_fish_and_does_not_try_smaller_school(self):
        sim = self.sim(pos=(20, 5), hold=["bong_sung"] * 3,
                       fish=[fish("F10", (20, 5), "ca_linh"), fish("F2", (21, 5), "ca_loc")],
                       tuning={"hold_capacity": 4, "fish_yield": {"ca_linh": 3, "ca_loc": 1}})
        before_fish, before_hold = copy.deepcopy(sim.fish), list(sim.hold)
        ev = press(sim, catch=True)
        self.assertEqual(names(ev), ["hold_full"])
        self.assertEqual(data_for(ev, "hold_full"), [{"required": 3, "free": 1}])
        self.assertEqual(sim.fish, before_fish)
        self.assertEqual(sim.hold, before_hold)
        self.assertEqual(sim.catch_cd_ticks, 0)

    def test_catch_cooldown_expires_before_action_and_starts_at_full_duration(self):
        sim = self.sim(pos=(20, 5), fish=[fish()], player={"catch_cd_ticks": 2},
                       tuning={"catch_cooldown_s": 0.1})
        self.assertEqual(press(sim, catch=True), [])
        self.assertEqual(sim.catch_cd_ticks, 1)
        self.assertEqual(len(sim.fish), 1)
        ev = press(sim, catch=True)
        self.assertEqual(names(ev), ["fish_caught"])
        ticks = round(sim.t["catch_cooldown_s"] * load_contract()["tuning"]["tick_hz"])
        self.assertEqual(sim.catch_cd_ticks, ticks)

    def test_catch_miss_does_not_start_cooldown(self):
        sim = self.sim(pos=(20, 5), fish=[fish(pos=(30, 5))])
        before_fish = copy.deepcopy(sim.fish)
        self.assertEqual(press(sim, catch=True), [])
        self.assertEqual(sim.catch_cd_ticks, 0)
        self.assertEqual(sim.fish, before_fish)
        self.assertEqual(sim.hold, [])

    def test_held_buttons_do_not_repeat_after_regrow_or_cooldown(self):
        for button, action, depth in (("interact", "gather", 0), ("catch", "fish_caught", 5)):
            with self.subTest(action=action):
                sim = self.sim(pos=(20, depth), nodes=[node()] if depth == 0 else [],
                               fish=[fish("F1"), fish("F2")] if depth else [],
                               tuning={"regrow_s": 0.1, "catch_cooldown_s": 0.1})
                inputs = InputPlayer([{"tick": 0, button: True},
                                      {"tick": 7, button: False}, {"tick": 8, button: True}])
                action_ticks = []
                for tick in range(9):
                    ev = sim.step(inputs.advance(tick))
                    if action in names(ev):
                        action_ticks.append(tick + 1)
                self.assertEqual(action_ticks, [1, 9])

    def test_dock_finishes_before_gather_or_catch(self):
        for depth in (0, 5):
            with self.subTest(depth=depth):
                sim = self.sim(pos=(20, depth), nodes=[node()], fish=[fish()], hold=["ca_loc"],
                               tuning={"dock_pos": [20, depth]})
                before_nodes, before_fish = copy.deepcopy(sim.nodes), copy.deepcopy(sim.fish)
                ev = press(sim, interact=True, catch=True)
                self.assertEqual(ev, [("gather_end", {
                    "reason": "docked", "inventory": {"items": {"ca_loc": 1}},
                })])
                self.assertTrue(sim.done)
                self.assertEqual(sim.nodes, before_nodes)
                self.assertEqual(sim.fish, before_fish)
                self.assertEqual(sim.hold, ["ca_loc"])

    def test_faint_finishes_before_catch_and_time(self):
        g = load_contract()["tuning"]["gather"]
        sim = self.sim(pos=(20, 5), fish=[fish()], hold=["ca_loc"], time_left_ticks=1,
                       player={"hp": 1, "oxygen_ticks": 0,
                               "zero_oxy_ticks": g["choke_interval_ticks"] - 1})
        ev = press(sim, catch=True)
        self.assertEqual(names(ev), ["choke", "faint", "gather_end"])
        self.assertEqual(data_for(ev, "gather_end"), [{
            "reason": "fainted", "inventory": {"items": {}},
        }])
        self.assertEqual(len(sim.fish), 1)
        self.assertEqual(sim.catch_cd_ticks, 0)

    def test_last_tick_keeps_new_gathered_or_caught_items_in_end_inventory(self):
        for button, action, depth, kind in (
            ("interact", "gather", 0, "bong_sung"),
            ("catch", "fish_caught", 5, "ca_loc"),
        ):
            with self.subTest(action=action):
                sim = self.sim(pos=(20, depth), nodes=[node()] if depth == 0 else [],
                               fish=[fish()] if depth else [], time_left_ticks=1)
                ev = press(sim, **{button: True})
                self.assertEqual(names(ev), [action, "gather_end"])
                count = sim.t["node_yield"] if depth == 0 else sim.t["fish_yield"][kind]
                self.assertEqual(data_for(ev, "gather_end"), [{
                    "reason": "time", "inventory": {"items": {kind: count}},
                }])


if __name__ == "__main__":
    unittest.main()
