import json
import unittest
from pathlib import Path

from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


TUNING = json.loads(
    Path("game.contract.json").read_text(encoding="utf-8")
)["tuning"]


class NoInput:
    move = (0.0, 0.0)

    def pressed(self, name):
        return False


def make_sim(tick=0, depth=12.0, seed=42):
    return GatherSim(
        TUNING,
        {
            "tick": tick,
            "player": {"pos": [50.0, depth]},
            "fish": [],
            "monsters": [],
        },
        Streams(seed),
        IdAllocator(),
    )


def events_named(events, name):
    return [data for event, data in events if event == name]


class GatherPhase3CurrentTests(unittest.TestCase):

    def test_warning_exact_tick_1680(self):
        sim = make_sim(tick=1678)
        self.assertFalse(events_named(sim.step(NoInput()), "current_warning"))
        events = sim.step(NoInput())
        self.assertEqual(len(events_named(events, "current_warning")), 1)

    def test_start_exact_tick_1800(self):
        sim = make_sim(tick=1798)
        self.assertFalse(events_named(sim.step(NoInput()), "current_start"))
        events = sim.step(NoInput())
        self.assertEqual(len(events_named(events, "current_start")), 1)
        self.assertIn(sim.current_direction, (-1, 1))

    def test_end_exact_tick_2280(self):
        sim = make_sim(tick=2278)
        self.assertFalse(events_named(sim.step(NoInput()), "current_end"))
        events = sim.step(NoInput())
        self.assertEqual(len(events_named(events, "current_end")), 1)
        self.assertEqual(sim.current_direction, 0)

    def test_current_pushes_at_depth_10(self):
        sim = make_sim(tick=1799, depth=10.0)
        before = sim.pos[0]
        sim.step(NoInput())
        expected = sim.current_direction * 1.5 / 60.0
        self.assertAlmostEqual(sim.pos[0] - before, expected, places=6)

    def test_no_push_above_depth_10(self):
        sim = make_sim(tick=1799, depth=9.0)
        before = sim.pos[0]
        sim.step(NoInput())
        self.assertAlmostEqual(sim.pos[0], before, places=6)

    def test_same_seed_same_direction_and_position(self):
        a = make_sim(tick=1799, seed=123)
        b = make_sim(tick=1799, seed=123)
        for _ in range(100):
            a.step(NoInput())
            b.step(NoInput())
        self.assertEqual(a.current_direction, b.current_direction)
        self.assertEqual(a.pos, b.pos)


if __name__ == "__main__":
    unittest.main()
