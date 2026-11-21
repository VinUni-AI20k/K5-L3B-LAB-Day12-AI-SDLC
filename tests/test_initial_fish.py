"""Kiểm tra tạo đàn cá đầu ca Phase 2."""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


class InitialFishTests(unittest.TestCase):
    def make_sim(self, seed=1, scenario=None):
        return GatherSim(load_contract()["tuning"], scenario or {}, Streams(seed), IdAllocator())

    def test_initial_schools_are_distinct_valid_and_repeatable(self):
        sim = self.make_sim()
        fish = sim.fish
        self.assertEqual(len(fish), sim.t["fish_initial"])
        self.assertEqual(len({tuple(f["pos"]) for f in fish}), len(fish))
        self.assertEqual(len({f["id"] for f in fish}), len(fish))
        self.assertEqual(fish, self.make_sim().fish)
        self.assertNotEqual(fish, self.make_sim(seed=2).fish)
        for f in fish:
            self.assertIn(f["pos"][0], sim.t["fish_spawn_x"])
            self.assertIn(f["pos"][1], sim.t["fish_spawn_depths"][f["kind"]])
            self.assertGreaterEqual(f["heading_deg"], 0)
            self.assertLess(f["heading_deg"], 360)
            self.assertEqual(f["age_ticks"], 0)
        self.assertEqual(sim.ids.new("F"), "F9")

    def test_fixture_and_disabled_default(self):
        fixture = [{"id": "F10", "kind": "ca_loc", "pos": [30, 10], "age_ticks": 42}]
        sim = self.make_sim(scenario={"fish": fixture, "random_fish": False})
        self.assertEqual(len(sim.fish), 1)
        self.assertEqual(sim.fish[0]["age_ticks"], 42)
        self.assertEqual(sim.ids.new("F"), "F11")
        self.assertEqual(self.make_sim(scenario={"random_fish": False}).fish, [])


if __name__ == "__main__":
    unittest.main()
