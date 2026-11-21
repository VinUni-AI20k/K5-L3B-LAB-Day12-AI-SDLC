"""Kiểm tra cá bơi, đổi hướng và phản xạ trong Phase 2."""

import math
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


class FishMovementTests(unittest.TestCase):
    def make_sim(self, fish, **scenario):
        scenario.update(fish=fish, nodes=[])
        return GatherSim(load_contract()["tuning"], scenario, Streams(42), IdAllocator())

    def step(self, sim, frames=None):
        return sim.step(InputPlayer(frames or []).advance(0))

    def test_speed_and_fixture_disabled(self):
        fish = [{"id": "F1", "kind": "ca_linh", "pos": [20, 5], "heading_deg": 0}]
        sim = self.make_sim(fish)
        self.step(sim)
        self.assertAlmostEqual(sim.fish[0]["pos"][0], 20 + 1.5 / 60)
        self.assertEqual(sim.fish[0]["age_ticks"], 1)
        frozen = self.make_sim(fish, random_fish=False)
        self.step(frozen)
        self.assertEqual(frozen.fish[0]["pos"], [20, 5])
        self.assertEqual(frozen.fish[0]["age_ticks"], 0)

    def test_turn_before_movement_and_seed(self):
        fish = [{"id": "F1", "kind": "ca_linh", "pos": [20, 5],
                 "heading_deg": 0, "age_ticks": 119}]
        expected = Streams(42).get("fish_turn").uniform(0, 360)
        sim = self.make_sim(fish)
        self.step(sim)
        self.assertAlmostEqual(sim.fish[0]["heading_deg"], expected)
        self.assertAlmostEqual(sim.fish[0]["pos"][0], 20 + math.cos(math.radians(expected)) * 1.5 / 60)
        self.assertEqual(sim.fish[0]["age_ticks"], 120)
        other = self.make_sim(fish)
        self.step(other)
        self.assertEqual(sim.fish, other.fish)

    def test_reflect_edge_and_corner_with_remaining_distance(self):
        fish = [{"id": "F1", "kind": "ca_linh", "pos": [95.99, 5], "heading_deg": 0},
                {"id": "F2", "kind": "ca_linh", "pos": [95.99, 11.99], "heading_deg": 45}]
        sim = self.make_sim(fish)
        self.step(sim)
        by_id = {f["id"]: f for f in sim.fish}
        self.assertAlmostEqual(by_id["F1"]["pos"][0], 95.985)
        self.assertAlmostEqual(by_id["F1"]["heading_deg"], 180)
        distance = 1.5 / 60 / math.sqrt(2)
        self.assertAlmostEqual(by_id["F2"]["pos"][0], 96 - (distance - 0.01))
        self.assertAlmostEqual(by_id["F2"]["pos"][1], 12 - (distance - 0.01))
        self.assertAlmostEqual(by_id["F2"]["heading_deg"], 225)

    def test_catch_before_fish_move_and_no_move_after_time(self):
        fish = [{"id": "F1", "kind": "ca_loc", "pos": [22, 10], "heading_deg": 0}]
        sim = self.make_sim(fish, player={"pos": [20, 10]})
        events = self.step(sim, [{"tick": 0, "catch": True}])
        self.assertEqual(events[0][0], "fish_caught")
        self.assertEqual(sim.fish, [])
        ending = self.make_sim(fish, time_left_ticks=1)
        self.step(ending)
        self.assertEqual(ending.fish[0]["pos"], [22, 10])
        self.assertEqual(ending.fish[0]["age_ticks"], 0)


if __name__ == "__main__":
    unittest.main()
