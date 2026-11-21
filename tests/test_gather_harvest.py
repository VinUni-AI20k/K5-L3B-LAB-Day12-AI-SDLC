"""Kiểm tra hành vi hái cây của buổi sáng."""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.sim.gather import GatherSim


class HarvestTests(unittest.TestCase):
    def make_sim(self, **scenario):
        tuning = load_contract()["tuning"]
        scenario.setdefault("player", {"pos": [20, 0]})
        scenario.setdefault("fish", [])
        return GatherSim(tuning, scenario, None, IdAllocator())

    def test_edge_tie_and_regrowth(self):
        sim = self.make_sim(nodes=[
            {"id": "N10", "kind": "bong_sung", "pos": [18, 0]},
            {"id": "N2", "kind": "bong_dien_dien", "pos": [22, 0], "regrow_ticks": 1},
        ])
        inputs = InputPlayer([{"tick": 0, "interact": True}])
        events = sim.step(inputs.advance(0))
        self.assertEqual(events, [
            ("node_regrown", {"node_id": "N2"}),
            ("gather", {"node_id": "N2", "kind": "bong_dien_dien", "amount": 1}),
        ])
        self.assertEqual(sim.hold, ["bong_dien_dien"])
        self.assertEqual(sim.nodes[1]["regrow_ticks"], int(round(sim.t["regrow_s"] * 60)))
        self.assertEqual(sim.step(inputs.advance(1)), [])  # Giữ E không hái lại.

    def test_full_hold_preserves_node(self):
        sim = self.make_sim(nodes=[{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}])
        sim.hold = ["ca_loc"] * sim.t["hold_capacity"]
        events = sim.step(InputPlayer([{"tick": 0, "interact": True}]).advance(0))
        self.assertEqual(events, [("hold_full", {"action": "gather", "node_id": "N1",
                                                  "required": sim.t["node_yield"], "free": 0})])
        self.assertEqual(sim.nodes[0]["regrow_ticks"], 0)

    def test_underwater_does_not_harvest(self):
        sim = self.make_sim(player={"pos": [20, 1]},
                            nodes=[{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}])
        self.assertEqual(sim.step(InputPlayer([{"tick": 0, "interact": True}]).advance(0)), [])
        self.assertEqual(sim.hold, [])

    def test_dock_takes_priority(self):
        sim = self.make_sim(player={"pos": [2, 0]},
                            nodes=[{"id": "N1", "kind": "bong_sung", "pos": [2, 0]}])
        events = sim.step(InputPlayer([{"tick": 0, "interact": True}]).advance(0))
        self.assertEqual([name for name, _ in events], ["gather_end"])
        self.assertEqual(sim.hold, [])


if __name__ == "__main__":
    unittest.main()
