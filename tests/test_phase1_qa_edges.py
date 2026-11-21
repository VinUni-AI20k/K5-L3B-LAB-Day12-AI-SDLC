"""Regression checks for Phase 1 edge cases owned by QA.

These tests use the shared tuning contract and step the simulation directly so
each boundary can be checked without wall-clock timing or browser behavior.
"""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from chonoi.sim.quan import QuanSim


def idle():
    return InputState((0.0, 0.0), {"interact": False, "catch": False}, set())


def pressed(button):
    return InputState((0.0, 0.0), {"interact": button == "interact", "catch": button == "catch"}, {button})


class Phase1GatherEdges(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def make_sim(self, scenario):
        return GatherSim(self.tuning, scenario, Streams(1), IdAllocator())

    def test_interact_with_full_hold_emits_hold_full_without_changing_hold(self):
        g = self.tuning["gather"]
        node = {"id": "N1", "kind": "bong_sung", "pos": [20, 0]}
        hold = ["ca_loc"] * g["hold_capacity"]
        sim = self.make_sim({"player": {"pos": [20, 0]}, "nodes": [node], "hold": hold, "fish": []})

        events = sim.step(pressed("interact"))

        self.assertIn("hold_full", [name for name, _ in events])
        self.assertEqual(sim.hold, hold)
        self.assertEqual(sim.nodes[0]["regrow_ticks"], 0)

    def test_choke_damages_only_after_full_60_tick_interval(self):
        interval = self.tuning["gather"]["choke_interval_ticks"]
        sim = self.make_sim({"player": {"pos": [50, 5], "oxygen_ticks": 0}, "nodes": [], "fish": []})

        for _ in range(interval - 1):
            sim.step(idle())
        self.assertEqual(sim.hp, self.tuning["gather"]["hp_max"])
        self.assertEqual(sim.zero_oxy_ticks, interval - 1)

        events = sim.step(idle())
        self.assertEqual(sim.hp, self.tuning["gather"]["hp_max"] - 1)
        self.assertIn("choke", [name for name, _ in events])

    def test_unready_node_regrows_and_emits_event_on_exact_tick(self):
        g = self.tuning["gather"]
        sim = self.make_sim({"nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0],
                                         "regrow_ticks": 2}], "fish": []})

        self.assertEqual(sim.snapshot()["nodes"][0]["ready"], False)
        first_events = sim.step(idle())
        self.assertNotIn("node_regrown", [name for name, _ in first_events])
        self.assertEqual(sim.nodes[0]["regrow_ticks"], 1)
        final_events = sim.step(idle())
        self.assertIn("node_regrown", [name for name, _ in final_events])
        self.assertEqual(sim.nodes[0]["regrow_ticks"], 0)
        self.assertEqual(sim.snapshot()["nodes"][0]["ready"], True)


class Phase1QuanEdges(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def make_sim(self, customer):
        return QuanSim(self.tuning, {"customers": [customer]}, Streams(1), IdAllocator())

    def test_customer_leaves_on_tick_patience_reaches_zero(self):
        sim = self.make_sim({"id": "C1", "table_id": "T1", "patience_ticks_left": 2})

        first_events = sim.step(idle())
        self.assertNotIn("customer_left", [name for name, _ in first_events])
        self.assertEqual(sim.customers[0]["patience_ticks_left"], 1)
        second_events = sim.step(idle())
        self.assertIn("customer_left", [name for name, _ in second_events])
        self.assertNotIn("C1", [customer["id"] for customer in sim.customers])

    def test_fast_service_tip_uses_contract_rate_and_menu_price(self):
        q = self.tuning["quan"]
        dish_id = "ca_loc_nuong_trui"
        dish = self.tuning["menu"][dish_id]
        patience = round(q["patience_s"] * 60)
        customer = {"id": "C1", "table_id": "T1", "state": "eating", "dish": dish_id,
                    "eat_ticks_left": 1,
                    "patience_ticks_left": round(patience * q["tip_min_patience_ratio"])}
        sim = self.make_sim(customer)

        events = sim.step(idle())
        paid = [data for name, data in events if name == "paid"]
        self.assertEqual(len(paid), 1)
        self.assertEqual(paid[0]["tip"], round(dish["price"] * q["tip_rate"]))


if __name__ == "__main__":
    unittest.main()
