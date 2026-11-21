import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chonoi.runner import Session


TUNING = json.loads(
    Path("game.contract.json").read_text(encoding="utf-8")
)["tuning"]


class Input:
    move = (0.0, 0.0)

    def __init__(self, pressed=()):
        self.buttons = set(pressed)

    def pressed(self, name):
        return name in self.buttons


def make_session(scenario):
    data = {
        "fish": [],
        "monsters": [],
        **scenario,
    }
    return Session("gather", TUNING, data, 42)


class GatherPhase3FinalTests(unittest.TestCase):

    def test_pause_stops_freshness_and_simulation(self):
        s = make_session({
            "player": {"pos": [50, 12]},
            "hold": [
                {"id": "I1", "kind": "ca_linh", "fresh": 50.0}
            ]
        })

        s.step(Input(["pause"]))

        self.assertTrue(s.sim.paused)
        self.assertEqual(s.snapshot()["state"], "paused")

        tick = s.sim.tick
        fresh = s.sim.hold[0]["fresh"]
        pos = list(s.sim.pos)
        time_left = s.sim.time_left_ticks

        for _ in range(120):
            s.step(Input())

        self.assertEqual(s.sim.tick, tick)
        self.assertEqual(s.sim.hold[0]["fresh"], fresh)
        self.assertEqual(s.sim.pos, pos)
        self.assertEqual(s.sim.time_left_ticks, time_left)

    def test_resume_continues_simulation(self):
        s = make_session({
            "hold": [
                {"id": "I1", "kind": "ca_loc", "fresh": 50.0}
            ]
        })

        s.step(Input(["pause"]))
        tick = s.sim.tick

        events = s.step(Input(["pause"]))
        self.assertTrue(any(e["name"] == "resumed" for e in events))
        self.assertFalse(s.sim.paused)

        s.step(Input())

        self.assertEqual(s.sim.tick, tick + 1)
        self.assertLess(s.sim.hold[0]["fresh"], 50.0)

    def test_faint_lifo_and_atomic_empty_inventory(self):
        s = make_session({
            "player": {
                "pos": [50, 5],
                "oxygen_ticks": 0,
                "zero_oxy_ticks": 59,
                "hp": 1,
            },
            "hold": [
                {"id": "I1", "kind": "ca_linh", "fresh": 90.0},
                {"id": "I2", "kind": "ca_loc", "fresh": 80.0},
                {"id": "I3", "kind": "keo_neo", "fresh": 70.0},
            ],
        })

        events = s.step(Input())
        faint = [e["data"] for e in events if e["name"] == "faint"]

        self.assertEqual(len(faint), 1)
        self.assertEqual(
            [item["id"] for item in faint[0]["lost"]],
            ["I3", "I2", "I1"],
        )
        self.assertEqual(s.sim.hold, [])
        self.assertEqual(s.sim.inventory_items(), [])
        self.assertTrue(s.done)

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "inventory.json"
            target.write_text('{"items":[{"old":"data"}]}', encoding="utf-8")

            with patch("chonoi.inventory.os.replace", wraps=os.replace) as replace:
                s.write_inventory_if_done(str(target))

                self.assertEqual(replace.call_count, 1)
                source, destination = replace.call_args.args
                self.assertEqual(Path(destination), target)
                self.assertEqual(Path(source).parent, target.parent)

            saved = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(saved, {"items": []})
            self.assertEqual(list(Path(tmp).glob(".inv-*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
