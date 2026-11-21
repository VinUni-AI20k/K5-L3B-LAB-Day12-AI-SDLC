import json
import unittest
from pathlib import Path

from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


TUNING = json.loads(
    Path("game.contract.json").read_text(encoding="utf-8")
)["tuning"]


class Input:
    move = (0.0, 0.0)
    def pressed(self, name):
        return False


def make_sim(scenario=None):
    data = dict(scenario or {})
    data.setdefault("fish", [])
    data.setdefault("monsters", [])
    return GatherSim(TUNING, data, Streams(42), IdAllocator())


class GatherPhase3HoldTests(unittest.TestCase):

    def test_new_item_objects(self):
        s = make_sim()
        items = s._new_items("ca_linh", 3)
        self.assertEqual([i["id"] for i in items], ["I1", "I2", "I3"])
        self.assertEqual([i["fresh"] for i in items], [100.0] * 3)

    def test_existing_ids_reserved(self):
        s = make_sim({
            "hold": [{"id": "I9", "kind": "ca_loc", "fresh": 95.0}]
        })
        self.assertEqual(s._new_items("ca_linh", 1)[0]["id"], "I10")

    def test_freshness_decreases(self):
        s = make_sim({
            "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100.0}]
        })
        s.step(Input())
        self.assertAlmostEqual(s.hold[0]["fresh"], 100 - 0.5/60)

    def test_freshness_never_negative(self):
        s = make_sim({
            "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 0.001}]
        })
        s.step(Input())
        self.assertEqual(s.hold[0]["fresh"], 0.0)

    def test_spoiled_exactly_once(self):
        s = make_sim({
            "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 30.0}]
        })
        events = s.step(Input())
        spoiled = [data for name, data in events if name == "spoiled"]
        self.assertEqual(len(spoiled), 1)
        self.assertEqual(spoiled[0], {
            "item_id": "I1",
            "kind": "ca_loc",
            "location": "hold",
        })
        events = s.step(Input())
        self.assertFalse(any(name == "spoiled" for name, _ in events))

    def test_inventory_preserves_freshness(self):
        s = make_sim({
            "hold": [
                {"id": "I2", "kind": "ca_loc", "fresh": 85.0},
                {"id": "I1", "kind": "keo_neo", "fresh": 97.5},
            ]
        })
        result = s.inventory_items()
        self.assertEqual([i["id"] for i in result], ["I1", "I2"])
        self.assertEqual(result[1]["fresh"], 85.0)


if __name__ == "__main__":
    unittest.main()
