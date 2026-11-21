"""Lát quán v1.2: hao tươi, sự kiện ươn và giữ theo id cá thể."""

import copy
import json
import unittest

from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


with open("game.contract.json", encoding="utf-8") as f:
    BASE_TUNING = json.load(f)["tuning"]

IDLE = InputState((0.0, 0.0), {}, set())


def sim(stock, customers=()):
    tuning = copy.deepcopy(BASE_TUNING)
    tuning["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5,
                           "quan_decay_per_s": 0.25, "spoiled_below": 30}
    scenario = {"stock": stock, "customers": list(customers), "random_customers": False}
    return QuanSim(tuning, scenario, Streams(1), IdAllocator())


def customer(reserved):
    return {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
            "order_status": "reserved", "reserved": reserved}


class FreshReservation(unittest.TestCase):
    def test_exact_threshold_is_usable_then_spoils_on_next_tick(self):
        q = sim([{"id": "I1", "kind": "ca_loc", "fresh": 30}])
        self.assertEqual(q.reserve_items({"ca_loc": 1}), ["I1"])
        events = q.step(IDLE)
        self.assertEqual(events, [("spoiled", {"item_id": "I1", "kind": "ca_loc", "location": "stock"})])
        self.assertEqual(q.reserve_items({"ca_loc": 1}), [])
        self.assertLess(q.snapshot()["stock"][0]["fresh"], 30)

    def test_reserved_item_spoils_and_order_reselects_freshest(self):
        q = sim([{"id": "I1", "kind": "ca_loc", "fresh": 30},
                 {"id": "I2", "kind": "ca_loc", "fresh": 60},
                 {"id": "I3", "kind": "ca_loc", "fresh": 60}], [customer(["I1"])])
        events = q.step(IDLE)
        self.assertEqual([name for name, _ in events], ["spoiled"])
        self.assertEqual(q.customers[0]["reserved"], ["I2"])
        self.assertEqual(q.customers[0]["order_status"], "reserved")
        self.assertEqual(q.available_stock()["ca_loc"], 1)

    def test_no_replacement_marks_unfulfillable_without_consuming_stock(self):
        q = sim([{"id": "I1", "kind": "ca_loc", "fresh": 30}], [customer(["I1"])])
        q.step(IDLE)
        self.assertEqual(q.customers[0]["reserved"], [])
        self.assertEqual(q.customers[0]["order_status"], "unfulfillable")
        self.assertEqual(len(q.stock), 1)

    def test_spoiled_events_are_ordered_by_id_and_freshness_is_exact_at_boundary(self):
        q = sim([{"id": "I10", "kind": "ca_loc", "fresh": 30},
                 {"id": "I2", "kind": "ca_loc", "fresh": 30 + 1 / 240}])
        events = q.step(IDLE)
        self.assertEqual([data["item_id"] for _, data in events], ["I10"])
        self.assertAlmostEqual(q.snapshot()["stock"][0]["fresh"], 30)

    def test_stock_spoils_before_dish_becomes_ready(self):
        q = sim([{"id": "I1", "kind": "ca_loc", "fresh": 30}])
        stove = q.stoves[0]
        stove.update(state="cooking", cook_ticks_left=1,
                     dish={"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60})
        events = q.step(IDLE)
        self.assertEqual([name for name, _ in events], ["spoiled", "dish_ready"])

    def test_just_below_threshold_does_not_emit_spoiled_again(self):
        q = sim([{"id": "I1", "kind": "ca_loc", "fresh": 29.9999}])
        self.assertEqual(q.step(IDLE), [])
        self.assertEqual(q.reserve_items({"ca_loc": 1}), [])


if __name__ == "__main__":
    unittest.main()
