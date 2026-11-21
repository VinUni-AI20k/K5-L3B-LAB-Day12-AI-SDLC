"""Kiểm tra logic Gather v1.2 độc lập với adapter kho đang tích hợp."""
import json
import unittest
from pathlib import Path

from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


class GatherFreshness(unittest.TestCase):
    def make_sim(self, scenario):
        tuning = json.loads(Path("game.contract.json").read_text(encoding="utf-8"))["tuning"]
        tuning["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5,
                               "quan_decay_per_s": 0.25, "spoiled_below": 30}
        return GatherSim(tuning, {"random_fish": False, "monsters": [], **scenario}, Streams(1), IdAllocator())

    def step(self, sim, *buttons):
        return sim.step(InputState((0, 0), {}, set(buttons)))

    def test_spoil_order_and_exact_threshold(self):
        sim = self.make_sim({"hold": [{"id": "I10", "kind": "ca_loc", "fresh": 30},
                                      {"id": "I2", "kind": "ca_linh", "fresh": 30.5}]})
        first = self.step(sim)
        self.assertEqual(first[0], ("spoiled", {"item_id": "I10", "kind": "ca_loc", "location": "hold"}))
        for _ in range(59):
            self.assertFalse(any(name == "spoiled" for name, _ in self.step(sim)))
        self.assertEqual(sim.hold[1]["fresh"], 30)
        self.assertEqual(self.step(sim)[0][1]["item_id"], "I2")

    def test_pickup_is_fresh_and_ids_continue_after_fixture(self):
        sim = self.make_sim({"player": {"pos": [12, 0]},
                             "hold": [{"id": "I7", "kind": "ca_loc", "fresh": 100}]})
        self.step(sim, "interact")
        self.assertEqual(sim.hold[-1], {"id": "I8", "kind": "bong_dien_dien", "fresh": 100})
        self.assertLess(sim.hold[0]["fresh"], 100)
        self.step(sim)
        self.assertLess(sim.hold[-1]["fresh"], 100)

    def test_faint_exports_empty_items_and_lifo_objects(self):
        sim = self.make_sim({"player": {"pos": [10, 5], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                             "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100},
                                      {"id": "I2", "kind": "ca_linh", "fresh": 100}]})
        result = self.step(sim)
        faint = next(data for name, data in result if name == "faint")
        self.assertEqual([item["id"] for item in faint["lost"]], ["I2", "I1"])
        self.assertEqual(result[-1][1]["inventory"], {"items": []})


if __name__ == "__main__":
    unittest.main()
