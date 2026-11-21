"""Kiểm tra bắt cá và kết thúc buổi sáng."""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.sim.gather import GatherSim


class CatchTests(unittest.TestCase):
    def make_sim(self, **scenario):
        scenario.setdefault("player", {"pos": [20, 5]})
        scenario.setdefault("nodes", [])
        # Phase 2: tắt bơi để các fixture kiểm tra bắt cá giữ vị trí cố định.
        scenario.setdefault("random_fish", False)
        return GatherSim(load_contract()["tuning"], scenario, None, IdAllocator())

    def test_nearest_tie_at_radius_and_held_button(self):
        sim = self.make_sim(fish=[
            {"id": "F10", "kind": "ca_loc", "pos": [18, 5]},
            {"id": "F2", "kind": "ca_linh", "pos": [22, 5]},
        ])
        inputs = InputPlayer([{"tick": 0, "catch": True}])
        self.assertEqual(sim.step(inputs.advance(0)), [
            ("fish_caught", {"fish_id": "F2", "kind": "ca_linh", "yield": 3})])
        self.assertEqual(sim.hold, ["ca_linh"] * 3)
        self.assertEqual([f["id"] for f in sim.fish], ["F10"])
        self.assertEqual(sim.catch_cd_ticks, int(round(sim.t["catch_cooldown_s"] * 60)))
        self.assertEqual(sim.step(inputs.advance(1)), [])

    def test_insufficient_capacity_does_not_try_another_fish(self):
        sim = self.make_sim(fish=[
            {"id": "F1", "kind": "ca_linh", "pos": [20, 5]},
            {"id": "F2", "kind": "ca_loc", "pos": [21, 5]},
        ])
        sim.hold = ["ca_loc"] * (sim.t["hold_capacity"] - 1)
        events = sim.step(InputPlayer([{"tick": 0, "catch": True}]).advance(0))
        self.assertEqual(events, [("hold_full", {"action": "catch", "fish_id": "F1",
                                                  "required": 3, "free": 1})])
        self.assertEqual(len(sim.fish), 2)
        self.assertEqual(sim.catch_cd_ticks, 0)

    def test_surface_cooldown_and_empty_radius(self):
        fish = [{"id": "F1", "kind": "ca_loc", "pos": [20, 1]}]
        for player, cooldown in [({"pos": [20, 0]}, 0), ({"pos": [20, 1]}, 2),
                                 ({"pos": [30, 5]}, 0)]:
            with self.subTest(player=player, cooldown=cooldown):
                sim = self.make_sim(player=player, fish=fish)
                sim.catch_cd_ticks = cooldown
                self.assertEqual(sim.step(InputPlayer([{"tick": 0, "catch": True}]).advance(0)), [])
                self.assertEqual(len(sim.fish), 1)

    def test_last_tick_catch_is_in_final_inventory(self):
        sim = self.make_sim(time_left_ticks=1, hold=["bong_sung"],
                            fish=[{"id": "F1", "kind": "ca_loc", "pos": [20, 5]}])
        events = sim.step(InputPlayer([{"tick": 0, "catch": True}]).advance(0))
        self.assertEqual(events, [
            ("fish_caught", {"fish_id": "F1", "kind": "ca_loc", "yield": 1}),
            ("gather_end", {"reason": "time", "inventory": {"items": {"bong_sung": 1, "ca_loc": 1}}}),
        ])
        self.assertTrue(sim.done)
        self.assertEqual(sim.reason, "time")

    def test_last_tick_dock_has_priority(self):
        sim = self.make_sim(player={"pos": [2, 0]}, time_left_ticks=1, fish=[])
        events = sim.step(InputPlayer([{"tick": 0, "interact": True}]).advance(0))
        self.assertEqual(events, [("gather_end", {"reason": "docked", "inventory": {"items": {}}})])


if __name__ == "__main__":
    unittest.main()
