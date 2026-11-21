"""Luật khách Phase 1: lịch, giữ chỗ và hạn kiên nhẫn."""

import json
import unittest

from chonoi.inputs import InputState
from chonoi.runner import Session


with open("game.contract.json", encoding="utf-8") as f:
    TUNING = json.load(f)["tuning"]

IDLE = InputState((0.0, 0.0), {}, set())


class QuanCustomers(unittest.TestCase):
    def test_arrival_reserves_stock_and_new_customer_waits_from_next_step(self):
        sim = Session("quan", TUNING, {"stock": {"ca_loc": 1}}, 1)
        for _ in range(TUNING["quan"]["first_customer_tick"]):
            events = sim.step(IDLE)
        self.assertEqual([e["name"] for e in events], ["customer_arrived"])
        customer = sim.sim.customers[0]
        self.assertEqual(customer["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(customer["reserved"], {"ca_loc": 1})
        self.assertEqual(sim.sim.available_stock()["ca_loc"], 0)
        self.assertEqual(customer["patience_ticks_left"], 60 * TUNING["quan"]["patience_s"])
        sim.step(IDLE)
        self.assertEqual(customer["patience_ticks_left"], 60 * TUNING["quan"]["patience_s"] - 1)

    def test_waiting_customer_leaves_and_releases_order(self):
        customer = {"id": "C9", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "patience_ticks_left": 1}
        sim = Session("quan", TUNING, {"stock": {"ca_loc": 1},
                                           "customers": [customer], "random_customers": False}, 1)
        events = sim.step(IDLE)
        self.assertEqual(events[0]["name"], "customer_left")
        self.assertEqual(events[0]["data"]["reason"], "patience")
        self.assertEqual(sim.sim.reputation, 2.5)
        self.assertEqual(sim.sim.customers, [])

    def test_closing_does_not_penalize_waiting_customer(self):
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "patience_ticks_left": 1}
        sim = Session("quan", TUNING, {"stock": {"ca_loc": 1},
                                           "customers": [customer], "time_left_ticks": 1}, 1)
        events = sim.step(IDLE)
        self.assertEqual([e["name"] for e in events], ["customer_left", "quan_end"])
        self.assertEqual(events[0]["data"]["reason"], "closing")
        self.assertEqual(sim.sim.reputation, 3.0)


if __name__ == "__main__":
    unittest.main()
