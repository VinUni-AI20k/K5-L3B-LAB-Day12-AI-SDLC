import copy
import json
import unittest

from chonoi.sim.gather import GatherSim
from chonoi.rng import Streams
from chonoi.ids import IdAllocator


with open("game.contract.json", encoding="utf-8") as f:
    TUNING = json.load(f)["tuning"]


class NoInput:
    move = (0.0, 0.0)

    def pressed(self, button):
        return False


def make_sim(seed=1, scenario=None):
    return GatherSim(
        copy.deepcopy(TUNING),
        scenario or {},
        Streams(seed),
        IdAllocator(),
    )


class GatherPhase2FishTests(unittest.TestCase):

    def test_initial_eight_fish(self):
        s = make_sim()
        self.assertEqual(len(s.fish), 8)

    def test_fish_moves_at_1_5_mps(self):
        s = make_sim(scenario={
            "fish": [{
                "id": "F1", "kind": "ca_linh",
                "pos": [20, 5], "heading_deg": 0
            }]
        })
        s.step(NoInput())
        self.assertAlmostEqual(s.fish[0]["pos"][0], 20.025, places=6)

    def test_fish_turns_at_tick_120(self):
        s = make_sim(scenario={
            "fish": [{
                "id": "F1", "kind": "ca_linh",
                "pos": [20, 5], "heading_deg": 0
            }]
        })
        for _ in range(119):
            s.step(NoInput())
        self.assertEqual(s.fish[0]["heading_deg"], 0)
        s.step(NoInput())
        self.assertNotEqual(s.fish[0]["heading_deg"], 0)

    def test_reflection_at_right_edge(self):
        s = make_sim(scenario={
            "fish": [{
                "id": "F1", "kind": "ca_linh",
                "pos": [95.99, 5], "heading_deg": 0
            }]
        })
        s.step(NoInput())
        self.assertLess(s.fish[0]["pos"][0], 96)
        self.assertEqual(s.fish[0]["heading_deg"], 180)

    def test_spawn_on_tick_360(self):
        s = make_sim(scenario={
            "fish": [{
                "id": "F1", "kind": "ca_linh",
                "pos": [20, 5], "heading_deg": 0
            }]
        })
        for _ in range(359):
            s.step(NoInput())
        self.assertEqual(len(s.fish), 1)
        s.step(NoInput())
        self.assertEqual(len(s.fish), 2)

    def test_population_cap(self):
        s = make_sim()
        for _ in range(1800):
            s.step(NoInput())
        self.assertEqual(len(s.fish), 12)

    def test_deterministic_with_seed(self):
        a = make_sim(seed=42)
        b = make_sim(seed=42)
        for _ in range(400):
            a.step(NoInput())
            b.step(NoInput())
        self.assertEqual(a.snapshot()["fish"], b.snapshot()["fish"])

    def test_fish_depth_stays_valid(self):
        s = make_sim()
        for _ in range(500):
            s.step(NoInput())
            for fish in s.fish:
                lo, hi = s.t["fish_depths"][fish["kind"]]
                self.assertGreaterEqual(fish["pos"][1], lo)
                self.assertLessEqual(fish["pos"][1], hi)


if __name__ == "__main__":
    unittest.main()
