"""Quán Phase 2 đọc bếp, bàn, món và kế hoạch ngày từ contract."""

import json
import unittest

from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


with open("game.contract.json", encoding="utf-8") as f:
    TUNING = json.load(f)["tuning"]

IDLE = InputState((0.0, 0.0), {}, set())


def arrive(sim):
    sim.phase_tick = sim.t["first_customer_tick"] - 1
    return sim.step(IDLE)


class QuanPhase2(unittest.TestCase):
    def test_standalone_uses_all_contract_stoves_tables_and_menu(self):
        sim = QuanSim(TUNING, {}, Streams(1), IdAllocator())
        self.assertEqual([s["id"] for s in sim.stoves], [s["id"] for s in TUNING["quan"]["stoves"]])
        self.assertEqual([t["id"] for t in sim.tables], [t["id"] for t in TUNING["quan"]["tables"]])
        self.assertEqual(sim.day_dishes, set(TUNING["menu"]))

    def test_day_filters_menu_before_checking_available_ingredients(self):
        # Ngày 1 có ca_loc_nuong_trui, không có ca_keo_nuong.
        stock = {"ca_keo": 2}
        day = QuanSim(TUNING, {"stock": stock}, Streams(1), IdAllocator(), day=1)
        events = arrive(day)
        self.assertEqual(events, [("no_dish", {})])
        self.assertEqual(day.customers, [])

        standalone = QuanSim(TUNING, {"stock": stock}, Streams(1), IdAllocator())
        events = arrive(standalone)
        self.assertEqual(events[0][0], "customer_arrived")
        self.assertEqual(events[0][1]["dish_id"], "ca_keo_nuong")

    def test_day_can_choose_only_planned_dishes_and_uses_multiple_tables(self):
        stock = {"ca_loc": 5, "bong_sung": 10, "ca_keo": 10}
        sim = QuanSim(TUNING, {"stock": stock}, Streams(2), IdAllocator(), day=1)
        for i in range(4):
            sim.phase_tick = sim.t["first_customer_tick"] - 1 + i * round(sim.t["customer_interval_s"] * 60)
            events = sim.step(IDLE)
            self.assertEqual(events[0][0], "customer_arrived")
            self.assertIn(events[0][1]["dish_id"], TUNING["day_plan"][0]["dishes"])
        self.assertEqual([c["table_id"] for c in sim.customers], ["T1", "T2", "T3", "T4"])


if __name__ == "__main__":
    unittest.main()
