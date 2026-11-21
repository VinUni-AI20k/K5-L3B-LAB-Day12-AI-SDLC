"""Kiểm tra lịch sinh cá và điều kiện điểm sinh Phase 2."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


class FishSpawnTests(unittest.TestCase):
    def make_sim(self, seed=42, **scenario):
        scenario.setdefault("fish", [])
        scenario.setdefault("nodes", [])
        return GatherSim(copy.deepcopy(load_contract()["tuning"]), scenario, Streams(seed), IdAllocator())

    def step(self, sim):
        return sim.step(InputPlayer([]).advance(0))

    def test_schedule_age_id_and_determinism(self):
        sim, other = self.make_sim(), self.make_sim()
        for _ in range(359):
            self.assertEqual(self.step(sim), [])
            self.step(other)
        self.assertEqual(sim.fish, [])
        events = self.step(sim)
        self.assertEqual(events, self.step(other))
        self.assertEqual(events[0][0], "fish_spawned")
        self.assertEqual(events[0][1]["id"], "F1")
        self.assertEqual(sim.fish[0]["age_ticks"], 0)
        self.assertEqual(sim.fish, other.fish)
        self.step(sim)
        self.assertEqual(sim.fish[0]["age_ticks"], 1)

    def test_limit_disabled_and_closing_tick(self):
        sim = self.make_sim()
        sim.t["fish_max"] = 0
        sim.phase_tick = 359
        self.assertEqual(self.step(sim), [])
        disabled = self.make_sim(random_fish=False)
        disabled.phase_tick = 359
        self.assertEqual(self.step(disabled), [])
        ending = self.make_sim(time_left_ticks=1)
        ending.phase_tick = 359
        self.assertEqual([name for name, _ in self.step(ending)], ["gather_end"])
        self.assertEqual(ending.fish, [])

    def test_clearance_inclusive_and_eligible_species_only(self):
        sim = self.make_sim(fish=[{"id": "F10", "kind": "ca_linh", "pos": [14, 5]}])
        sim.t["fish_spawn_x"] = [15]
        sim.t["fish_spawn_depths"] = {"ca_linh": [5], "ca_keo": [24]}
        events = []
        sim._spawn_fish(events)
        self.assertEqual(events[0][1], {"id": "F11", "kind": "ca_keo", "pos": [15, 24]})
        sim.t["fish_spawn_depths"] = {"ca_linh": [5]}
        events = []
        sim._spawn_fish(events)
        self.assertEqual(events, [])

    def test_spawn_uses_position_after_movement(self):
        sim = self.make_sim(fish=[{"id": "F1", "kind": "ca_linh", "pos": [13.99, 5],
                                   "heading_deg": 0}])
        sim.t["fish_spawn_x"] = [15]
        sim.t["fish_spawn_depths"] = {"ca_linh": [5]}
        sim.phase_tick = 359
        self.assertEqual(self.step(sim), [])  # Bơi tới cách điểm sinh <= 1 m.
        self.assertEqual(len(sim.fish), 1)


if __name__ == "__main__":
    unittest.main()
