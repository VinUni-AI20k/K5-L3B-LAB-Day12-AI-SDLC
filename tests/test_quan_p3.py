import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
from helpers import ROOT


DISH = "ca_loc_nuong_trui"


class Phase3FreshStock(unittest.TestCase):
    def setUp(self):
        self.tuning = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))["tuning"]

    def sim(self, stock, customers):
        return QuanSim(self.tuning, {"player": {"pos": [2, 8]}, "customers": customers,
                                    "random_customers": False}, Streams(42), IdAllocator(),
                       inventory=stock)

    def test_spoiled_events_precede_reassignment_and_cooking(self):
        sim = self.sim([
            {"id": "I10", "kind": "ca_loc", "fresh": 30},
            {"id": "I2", "kind": "ca_loc", "fresh": 30},
            {"id": "I3", "kind": "ca_loc", "fresh": 75},
        ], [{"id": "C1", "table_id": "T1", "dish_id": DISH, "reserved": ["I10"]}])
        rows = sim.step(SimpleNamespace(move=(0, 0), pressed=lambda name: name == "interact"))
        self.assertEqual([name for name, _ in rows], ["spoiled", "spoiled", "cook_started"])
        self.assertEqual([data["item_id"] for _, data in rows[:2]], ["I2", "I10"])
        cooked = rows[-1][1]
        self.assertEqual([item["id"] for item in cooked["items"]], ["I3"])
        self.assertEqual(cooked["base_price"], 44)
        self.assertEqual(sim.customers[0]["base_price"], 44)
        self.assertEqual(sim.customers[0]["reserved"], [])
        self.assertEqual(sim.step(SimpleNamespace(move=(0, 0), pressed=lambda _: False)), [])

    def test_reassignment_uses_order_tick_then_table(self):
        sim = self.sim([
            {"id": "I1", "kind": "ca_loc", "fresh": 30},
            {"id": "I2", "kind": "ca_loc", "fresh": 30},
            {"id": "I3", "kind": "ca_loc", "fresh": 70},
        ], [
            {"id": "C1", "table_id": "T1", "dish_id": DISH, "order_tick": 4, "reserved": ["I1"]},
            {"id": "C2", "table_id": "T2", "dish_id": DISH, "order_tick": 3, "reserved": ["I2"]},
        ])
        sim.step(SimpleNamespace(move=(0, 0), pressed=lambda _: False))
        first, second = sim.customers
        self.assertEqual((first["order_status"], first["reserved"]), ("unfulfillable", []))
        self.assertEqual((second["order_status"], second["reserved"]), ("reserved", ["I3"]))

    def test_implicit_reservation_uses_freshness_then_numeric_id(self):
        sim = self.sim([
            {"id": "I1", "kind": "ca_loc", "fresh": 80},
            {"id": "I10", "kind": "ca_loc", "fresh": 90},
            {"id": "I2", "kind": "ca_loc", "fresh": 90},
        ], [{"id": "C1", "table_id": "T1", "dish_id": DISH}])
        self.assertEqual(sim.customers[0]["reserved"], ["I2"])

    def test_fixture_rejects_shared_reservation(self):
        with self.assertRaises(BadInput):
            self.sim([{"id": "I1", "kind": "ca_loc", "fresh": 100}], [
                {"id": "C1", "table_id": "T1", "dish_id": DISH, "reserved": ["I1"]},
                {"id": "C2", "table_id": "T2", "dish_id": DISH, "reserved": ["I1"]},
            ])
