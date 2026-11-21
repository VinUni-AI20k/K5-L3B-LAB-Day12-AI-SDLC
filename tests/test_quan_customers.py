import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import LiveInputs
from chonoi.runner import Session


class QuanCustomers(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.tuning["quan"]["first_customer_tick"] = 1

    def test_arrival_reserves_recipe_without_consuming_stock(self):
        session = Session("quan", self.tuning, {"stock": {"bong_sung": 2}}, 42)
        inp = LiveInputs().advance()
        event, = session.step(inp)
        customer, = session.sim.customers
        self.assertEqual(event["name"], "customer_arrived")
        self.assertEqual(event["tick"], 1)
        self.assertEqual(event["data"]["order_id"], customer["order_id"])
        self.assertEqual(customer["dish_id"], "goi_bong_sung")
        self.assertEqual(customer["patience_ticks_left"], session.sim.patience_ticks)
        self.assertEqual(customer["reserved"], {"bong_sung": 2})
        self.assertEqual(session.snapshot()["stock"], {"bong_sung": 2})
        self.assertEqual(session.sim.available_stock(), {"bong_sung": 0})
        self.assertEqual(session.step(inp), [])
        self.assertEqual(customer["patience_ticks_left"], session.sim.patience_ticks - 1)

    def test_insufficient_stock_produces_no_dish(self):
        session = Session("quan", self.tuning, {"stock": {"bong_sung": 1}}, 42)
        event, = session.step(LiveInputs().advance())
        self.assertEqual(event["name"], "no_dish")
        self.assertEqual(session.sim.customers, [])

    def test_fixture_leaves_at_deadline_and_releases_stock(self):
        scenario = {
            "stock": {"bong_sung": 2},
            "random_customers": False,
            "customers": [{"id": "C7", "table_id": "T1", "order_id": "O7",
                           "dish_id": "goi_bong_sung", "patience_ticks_left": 2}],
        }
        session = Session("quan", self.tuning, scenario, 42)
        inp = LiveInputs().advance()
        self.assertEqual(session.sim.available_stock(), {"bong_sung": 0})
        self.assertEqual(session.step(inp), [])
        self.assertEqual(session.sim.customers[0]["patience_ticks_left"], 1)
        event, = session.step(inp)
        self.assertEqual(event["name"], "customer_left")
        self.assertEqual(session.sim.available_stock(), {"bong_sung": 2})
        self.assertEqual(session.snapshot()["stock"], {"bong_sung": 2})
        self.assertIsNone(session.snapshot()["tables"][0]["customer_id"])

    def test_fixture_reservation_cannot_exceed_stock(self):
        scenario = {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]}
        with self.assertRaises(BadInput):
            Session("quan", self.tuning, scenario, 42)
