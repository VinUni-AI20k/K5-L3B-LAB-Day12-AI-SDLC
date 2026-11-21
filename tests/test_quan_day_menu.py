import unittest

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.runner import Session


class QuanDayMenu(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.day_dishes = self.tuning["day_plan"][0]["dishes"]

    def first_arrival(self, **kwargs):
        session = Session("quan", self.tuning, {}, 42, **kwargs)
        idle = LiveInputs().advance()
        for _ in range(self.tuning["quan"]["first_customer_tick"]):
            events = session.step(idle)
        event, = events
        return session, event

    def test_day_menu_filters_before_reserving_ingredients(self):
        session, event = self.first_arrival(
            inventory={"ca_keo": 2, "ca_loc": 1}, day_dishes=self.day_dishes
        )
        self.assertEqual(event["name"], "customer_arrived")
        self.assertEqual(event["data"]["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(session.sim.available_stock(), {"ca_keo": 2, "ca_loc": 0})
        self.assertEqual(len(session.snapshot()["stoves"]), 2)
        self.assertEqual(len(session.snapshot()["tables"]), 4)
        self.assertEqual(len(session.sim.menu), 6)

    def test_standalone_can_order_dish_excluded_by_day(self):
        inventory = {"ca_keo": 2}
        _, day_event = self.first_arrival(inventory=inventory, day_dishes=self.day_dishes)
        _, standalone_event = self.first_arrival(inventory=inventory)
        self.assertEqual(day_event["name"], "no_dish")
        self.assertEqual(standalone_event["data"]["dish_id"], "ca_keo_nuong")
