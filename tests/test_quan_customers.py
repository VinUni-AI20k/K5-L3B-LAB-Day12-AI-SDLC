import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session


class QuanCustomers(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.quan = self.tuning["quan"]
        self.inputs = InputPlayer([])

    def session(self, scenario, seed=1):
        return Session("quan", self.tuning, scenario, seed)

    def advance(self, session, to_tick):
        events = []
        while session.tick < to_tick:
            events.extend(session.step(self.inputs.advance(session.tick)))
        return events

    def test_arrival_tick_interval_and_full_tables(self):
        self.quan["tables"] = [{"id": "T10", "pos": [8, 2]}, {"id": "T2", "pos": [9, 2]}]
        first = self.quan["first_customer_tick"]
        interval = round(self.quan["customer_interval_s"] * self.tuning["tick_hz"])
        session = self.session({"stock": {"ca_loc": 3}, "time_left_ticks": 2 * interval + first + 1})

        self.assertEqual(self.advance(session, first - 1), [])
        events = self.advance(session, first + 2 * interval)
        self.assertEqual([(row["tick"], row["name"], row["data"]) for row in events], [
            (first, "customer_arrived", {"customer_id": "C1", "table_id": "T2", "dish": "ca_loc_nuong_trui"}),
            (first + interval, "customer_arrived",
             {"customer_id": "C2", "table_id": "T10", "dish": "ca_loc_nuong_trui"}),
        ])
        self.assertEqual([table["customer_id"] for table in session.snapshot()["tables"]], ["C1", "C2"])

    def test_fixture_can_disable_arrivals(self):
        session = self.session({"stock": {"ca_loc": 1}, "random_customers": False})
        self.assertEqual(self.advance(session, self.quan["first_customer_tick"]), [])
        self.assertEqual(session.snapshot()["customers"], [])

    def test_new_id_continues_after_highest_fixture_id(self):
        self.quan["tables"].append({"id": "T2", "pos": [9, 4]})
        session = self.session({"stock": {"ca_loc": 1}, "customers": [{"id": "C9", "table_id": "T1"}]})
        arrival, = self.advance(session, self.quan["first_customer_tick"])
        self.assertEqual(arrival["data"]["customer_id"], "C10")
        self.assertEqual([c["id"] for c in session.snapshot()["customers"]], ["C9", "C10"])

    def test_reservation_blocks_other_tables_without_spending_stock(self):
        self.quan["tables"].append({"id": "T2", "pos": [9, 4]})
        first = self.quan["first_customer_tick"]
        interval = round(self.quan["customer_interval_s"] * self.tuning["tick_hz"])
        stock = {"ca_linh": 3, "bong_dien_dien": 1, "bong_sung": 1}
        session = self.session({"stock": stock})

        arrival, rejected, next_rejected = self.advance(session, first + 2 * interval)
        self.assertEqual(arrival["data"]["dish"], "lau_ca_linh_dien_dien")
        self.assertEqual((rejected["tick"], rejected["name"], rejected["data"]),
                         (first + interval, "no_dish", {"customer_id": "C2"}))
        self.assertEqual(next_rejected["data"], {"customer_id": "C3"})
        snapshot = session.snapshot()
        customer, = snapshot["customers"]
        self.assertEqual(customer["reserved"], {"ca_linh": 3, "bong_dien_dien": 1})
        self.assertEqual(snapshot["stock"], stock)
        self.assertIsNone(snapshot["tables"][1]["customer_id"])
        self.assertEqual(snapshot["reputation"], self.quan["reputation_initial"])

    def test_preloaded_order_reserves_its_recipe(self):
        self.quan["tables"].append({"id": "T2", "pos": [9, 4]})
        session = self.session({"stock": {"ca_loc": 1, "bong_sung": 2}, "customers": [
            {"id": "C1", "table_id": "T1", "dish": "ca_loc_nuong_trui", "state": "waiting"},
        ]})

        arrival, = self.advance(session, self.quan["first_customer_tick"])
        self.assertEqual(arrival["data"]["dish"], "goi_bong_sung")
        self.assertEqual([c["reserved"] for c in session.snapshot()["customers"]],
                         [{"ca_loc": 1}, {"bong_sung": 2}])
