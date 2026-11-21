import json
import unittest
from pathlib import Path

from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


class GatherCollectionTest(unittest.TestCase):
    def make_sim(self, pos, **scenario):
        path = Path(__file__).resolve().parents[1] / "game.contract.json"
        tuning = json.loads(path.read_text(encoding="utf-8"))["tuning"]
        return GatherSim(tuning, {"player": {"pos": pos}, **scenario}, Streams(1), IdAllocator())

    def step(self, sim, *buttons):
        return sim.step(InputState((0, 0), {}, set(buttons)))

    def test_harvest_at_radius_and_regrow(self):
        sim = self.make_sim([10, 0])
        self.assertEqual(self.step(sim, "interact")[0][0], "gather")
        self.assertEqual(sim.hold, ["bong_dien_dien"])
        self.assertEqual(sim.nodes[0]["regrow_ticks"], 1200)
        for _ in range(1199):
            self.assertEqual(self.step(sim, "interact"), [])
        self.assertEqual([name for name, _ in self.step(sim, "interact")],
                         ["node_regrown", "gather"])

    def test_harvest_requires_surface_and_space(self):
        sim = self.make_sim([12, 1])
        self.assertEqual(self.step(sim, "interact"), [])
        sim.pos[1] = 0
        sim.hold = ["ca_loc"] * 12
        self.assertEqual(self.step(sim, "interact")[0][0], "hold_full")
        self.assertEqual(sim.nodes[0]["regrow_ticks"], 0)

    def test_dock_has_priority(self):
        sim = self.make_sim([2, 0], nodes=[
            {"id": "N1", "kind": "bong_dien_dien", "pos": [2, 0]},
        ])
        self.assertEqual([name for name, _ in self.step(sim, "interact")], ["gather_end"])
        self.assertEqual(sim.hold, [])

    def test_catch_tie_space_and_cooldown(self):
        sim = self.make_sim([12, 2], hold=["bong_sung"] * 10, fish=[
            {"id": "F10", "kind": "ca_loc", "pos": [14, 2]},
            {"id": "F2", "kind": "ca_linh", "pos": [10, 2]},
        ])
        self.assertEqual(self.step(sim, "catch")[0][0], "hold_full")
        self.assertEqual(len(sim.hold), 10)
        self.assertEqual(len(sim.fish), 2)
        self.assertEqual(sim.catch_cd_ticks, 0)
        sim.hold.pop()
        self.assertEqual(self.step(sim, "catch")[0][1]["fish_id"], "F2")
        self.assertEqual(sim.hold[-3:], ["ca_linh"] * 3)
        self.assertEqual(sim.catch_cd_ticks, 30)
        sim.hold.pop()
        for _ in range(29):
            self.assertEqual(self.step(sim, "catch"), [])
        self.assertEqual(self.step(sim, "catch")[0][1]["fish_id"], "F10")

    def test_catch_requires_submersion(self):
        sim = self.make_sim([12, 0], fish=[
            {"id": "F1", "kind": "ca_loc", "pos": [12, 1]},
        ])
        self.assertEqual(self.step(sim, "catch"), [])
        self.assertEqual(len(sim.fish), 1)
