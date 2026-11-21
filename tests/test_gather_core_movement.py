"""Movement checks for the Gather Core slice."""

import copy
import math
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session


class GatherCoreMovement(unittest.TestCase):
    def make_session(self, ramp=None, pos=(50, 15)):
        tuning = copy.deepcopy(load_contract()["tuning"])
        if ramp is not None:
            tuning["gather"]["ramp_max_ticks"] = ramp
        return Session("gather", tuning, {"player": {"pos": list(pos)}}, 7)

    def test_acceleration_and_integration_from_rest(self):
        session = self.make_session()
        g = session.tuning["gather"]
        inputs = InputPlayer([{"tick": 0, "move": [1, 0]}])
        x = 50.0
        for tick in range(g["ramp_max_ticks"]):
            session.step(inputs.advance(tick))
            expected_v = g["swim_speed"] * (tick + 1) / g["ramp_max_ticks"]
            x += expected_v / session.tuning["tick_hz"]
            player = session.snapshot()["player"]
            self.assertAlmostEqual(player["vel"][0], expected_v)
            self.assertAlmostEqual(player["pos"][0], x)

    def test_heading_is_retained_after_stopping(self):
        session = self.make_session()
        inputs = InputPlayer([{"tick": 0, "move": [-1, 1]}, {"tick": 1, "move": [0, 0]}])
        for tick in range(10):
            session.step(inputs.advance(tick))
        player = session.snapshot()["player"]
        self.assertAlmostEqual(player["heading_deg"], 135)
        self.assertAlmostEqual(math.hypot(*player["vel"]), 0)

    def test_zero_ramp_and_diagonal_normalization(self):
        session = self.make_session(ramp=0)
        inputs = InputPlayer([{"tick": 0, "move": [1, 1]}])
        session.step(inputs.advance(0))
        player = session.snapshot()["player"]
        speed = session.tuning["gather"]["swim_speed"]
        self.assertAlmostEqual(math.hypot(*player["vel"]), speed)
        self.assertAlmostEqual(player["vel"][0], speed / math.sqrt(2))
        self.assertAlmostEqual(player["pos"][1], 15 + player["vel"][1] / session.tuning["tick_hz"])

    def test_outward_velocity_is_zero_at_each_boundary(self):
        b = load_contract()["tuning"]["gather"]["bounds"]
        for pos, move, axis in [([b["x"][0], 15], [-1, 0], 0),
                                ([b["x"][1], 15], [1, 0], 0),
                                ([50, b["d"][0]], [0, -1], 1),
                                ([50, b["d"][1]], [0, 1], 1)]:
            with self.subTest(pos=pos):
                session = self.make_session(ramp=0, pos=pos)
                session.step(InputPlayer([{"tick": 0, "move": move}]).advance(0))
                player = session.snapshot()["player"]
                self.assertEqual(player["pos"][axis], pos[axis])
                self.assertEqual(player["vel"][axis], 0)


if __name__ == "__main__":
    unittest.main()
