"""Kiểm thử khách hàng Quán theo PRD-0: lịch đến, giữ chỗ, kiên nhẫn, đóng ca và schema."""

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer
from chonoi.runner import Session


class QuanCustomers(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.quan = self.tuning["quan"]
        # These Phase 1 fixtures start with one table and add others explicitly.
        self.quan["tables"] = self.quan["tables"][:1]
        self.inputs = InputPlayer([])

    def session(self, scenario, seed=1):
        return Session("quan", self.tuning, scenario, seed)

    def advance(self, session, to_tick):
        events = []
        while session.tick < to_tick and not session.done:
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
            (first, "customer_arrived", {"order_id": "C1", "table_id": "T2", "dish_id": "ca_loc_nuong_trui"}),
            (first + interval, "customer_arrived",
             {"order_id": "C2", "table_id": "T10", "dish_id": "ca_loc_nuong_trui"}),
        ])
        self.assertEqual([table["customer_id"] for table in session.snapshot()["tables"]], ["C1", "C2"])

    def test_fixture_can_disable_arrivals(self):
        session = self.session({"stock": {"ca_loc": 1}, "random_customers": False})
        self.assertEqual(self.advance(session, self.quan["first_customer_tick"]), [])
        self.assertEqual(session.snapshot()["customers"], [])

    def test_new_id_continues_after_highest_fixture_id(self):
        self.quan["tables"].append({"id": "T2", "pos": [9, 4]})
        session = self.session({"stock": {"ca_loc": 1}, "customers": [
            {"id": "C9", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
        ]})
        arrival, = self.advance(session, self.quan["first_customer_tick"])
        self.assertEqual(arrival["name"], "no_dish")
        self.assertEqual(arrival["data"], {})

        session2 = self.session({"stock": {"ca_loc": 2}, "customers": [
            {"id": "C9", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
        ]})
        arrival2, = self.advance(session2, self.quan["first_customer_tick"])
        self.assertEqual(arrival2["data"]["order_id"], "C10")
        self.assertEqual([c["id"] for c in session2.snapshot()["customers"]], ["C9", "C10"])

    def test_reservation_blocks_other_tables_without_spending_stock(self):
        self.quan["tables"].append({"id": "T2", "pos": [9, 4]})
        first = self.quan["first_customer_tick"]
        interval = round(self.quan["customer_interval_s"] * self.tuning["tick_hz"])
        stock = {"ca_linh": 3, "bong_dien_dien": 1, "bong_sung": 1}
        session = self.session({"stock": stock})

        arrival, rejected, next_rejected = self.advance(session, first + 2 * interval)
        self.assertEqual(arrival["data"]["dish_id"], "lau_ca_linh_dien_dien")
        self.assertEqual((rejected["tick"], rejected["name"], rejected["data"]), (first + interval, "no_dish", {}))
        self.assertEqual((next_rejected["name"], next_rejected["data"]), ("no_dish", {}))
        snapshot = session.snapshot()
        customer, = snapshot["customers"]
        self.assertEqual(customer["reserved"], {"ca_linh": 3, "bong_dien_dien": 1})
        self.assertEqual(customer["order_status"], "reserved")
        self.assertEqual(snapshot["stock"], stock)
        self.assertIsNone(snapshot["tables"][1]["customer_id"])
        self.assertEqual(snapshot["reputation"], self.quan["reputation_initial"])

    def test_preloaded_order_auto_reserves_missing_reserved(self):
        self.quan["tables"].append({"id": "T2", "pos": [9, 4]})
        session = self.session({"stock": {"ca_loc": 1, "bong_sung": 2}, "customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 0},
        ]})

        arrival, = self.advance(session, self.quan["first_customer_tick"])
        self.assertEqual(arrival["data"]["dish_id"], "goi_bong_sung")
        self.assertEqual([c["reserved"] for c in session.snapshot()["customers"]],
                         [{"ca_loc": 1}, {"bong_sung": 2}])

    def test_new_customer_waits_full_patience_then_leaves(self):
        self.quan["customer_interval_s"] += 1
        first = self.quan["first_customer_tick"]
        patience = round(self.quan["patience_s"] * self.tuning["tick_hz"])
        session = self.session({"stock": {"ca_loc": 1}})
        self.advance(session, first)
        at_arrival = session.snapshot()
        self.assertEqual(at_arrival["customers"][0]["patience_ticks_left"], patience)
        self.assertEqual(self.advance(session, first + patience - 1), [])
        self.assertEqual(session.snapshot()["customers"][0]["patience_ticks_left"], 1)

        departure, = self.advance(session, first + patience)
        expected_rep = round(self.quan["reputation_initial"] + self.quan["left_reputation_delta"], 6)
        self.assertEqual(departure["name"], "customer_left")
        self.assertEqual(departure["data"], {
            "order_id": "C1",
            "table_id": "T1",
            "reason": "patience",
            "reputation": expected_rep,
        })
        state = session.snapshot()
        self.assertEqual(state["customers"], [])
        self.assertIsNone(state["tables"][0]["customer_id"])
        self.assertEqual(state["stock"], {"ca_loc": 1})
        self.assertEqual(state["reputation"], expected_rep)

    def test_expiry_releases_reservation_before_same_tick_arrival(self):
        first = self.quan["first_customer_tick"]
        session = self.session({"stock": {"ca_loc": 1}, "customers": [
            {"id": "C9", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": first},
        ]})
        events = self.advance(session, first)
        self.assertEqual([(row["tick"], row["name"], row["data"]) for row in events], [
            (first, "customer_left", {"order_id": "C9", "table_id": "T1", "reason": "patience", "reputation": 2.5}),
            (first, "customer_arrived", {"order_id": "C10", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}),
        ])
        customer, = session.snapshot()["customers"]
        self.assertEqual(customer["reserved"], {"ca_loc": 1})
        self.assertEqual(session.snapshot()["tables"][0]["customer_id"], "C10")

    def test_simultaneous_timeouts_ordered_by_table_and_eating_stays(self):
        self.quan["tables"].extend([{"id": "T2", "pos": [9, 4]}, {"id": "T3", "pos": [9, 6]}])
        minimum = self.quan["reputation_min"]
        penalty = self.quan["left_reputation_delta"]
        session = self.session({
            "random_customers": False,
            "reputation": minimum - penalty / 2,
            "stoves": [{"id": "B1", "state": "cooking",
                        "dish": {"order_id": "C2", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                        "cook_ticks_left": 50}],
            "customers": [
                {"id": "C10", "table_id": "T3", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 1, "reserved": {"ca_loc": 1}},
                {"id": "C3", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "state": "eating", "order_status": "served",
                 "patience_ticks_left": 1, "eat_ticks_left": 20, "reserved": {}, "base_price": 60, "tip": 0},
                {"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned",
                 "patience_ticks_left": 1, "reserved": {}},
            ],
            "stock": {"ca_loc": 1},
        })
        events = self.advance(session, 1)
        self.assertEqual([(row["data"]["order_id"], row["data"]["table_id"]) for row in events], [("C2", "T1"), ("C10", "T3")])
        state = session.snapshot()
        self.assertEqual(state["reputation"], minimum)
        self.assertEqual([(c["id"], c["state"], c["order_status"]) for c in state["customers"]], [("C3", "eating", "served")])
        self.assertEqual(state["stoves"][0]["state"], "idle")

    def test_multi_dish_choice_is_seeded_and_independent_of_menu_order(self):
        stock = {"ca_loc": 1, "bong_sung": 2, "ca_linh": 3, "bong_dien_dien": 1}
        first = self.quan["first_customer_tick"]
        initial = self.advance(self.session({"stock": stock}, seed=42), first)
        self.tuning["menu"] = dict(reversed(list(self.tuning["menu"].items())))
        repeated = self.advance(self.session({"stock": stock}, seed=42), first)
        self.assertEqual(initial, repeated)

    def test_legacy_customer_fixture_is_loaded_without_mutating_input(self):
        customer = {"id": "C9", "table_id": "T1", "dish": "ca_loc_nuong_trui", "patience_ticks": 2}
        session = self.session({"stock": {"ca_loc": 1}, "customers": [customer]})
        snapshot = session.snapshot()["customers"][0]
        self.assertEqual(snapshot["dish_id"], customer["dish"])
        self.assertEqual(snapshot["patience_ticks_left"], customer["patience_ticks"])
        self.assertEqual(snapshot["reserved"], {"ca_loc": 1})
        self.assertNotIn("dish_id", customer)
        self.assertNotIn("patience_ticks_left", customer)

    def test_invalid_fixture_types_and_links_are_rejected_before_first_tick(self):
        bad_scenarios = [
            {"random_customers": "false"},
            {"tables": [{"id": "T99", "pos": [5, 5]}]},
            {"stoves": [{"id": "B99", "pos": [2, 8]}]},
            {"hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": -1}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "mon_la"}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "patience_ticks": 2, "patience_ticks_left": 1}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": {"bong_sung": 1}}]},
            {"stock": {}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]},
        ]
        for sc in bad_scenarios:
            with self.subTest(sc=sc), self.assertRaises(BadInput):
                self.session(sc)


if __name__ == "__main__":
    unittest.main()
