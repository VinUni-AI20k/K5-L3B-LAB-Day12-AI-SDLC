"""Phase 3 slices 3–4: Quán freshness, reservation orders and day integration."""

import unittest

from helpers import Workdir, events, frames
from rules_common import at, run_day, run_mode


class QuanFreshness(unittest.TestCase):
    def test_stock_decays_and_spoils_before_order_handling(self):
        with Workdir() as w:
            rows = run_mode(w, "quan", {
                "random_customers": False, "random_reservations": False,
                "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 30}],
            }, ticks=1)
        self.assertEqual(events(rows, "spoiled")[0]["data"],
                         {"item_id": "I1", "kind": "ca_loc", "location": "stock"})
        self.assertEqual(at(rows, 1)["stock"], [])

    def test_cook_locks_exact_item_and_fresh_adjusted_price(self):
        with Workdir() as w:
            rows = run_mode(w, "quan", {
                "random_customers": False, "random_reservations": False,
                "player": {"pos": [2, 8]},
                "stock": [{"id": "I7", "kind": "ca_loc", "fresh": 80}],
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                               "order_tick": 0, "state": "waiting", "order_status": "reserved",
                               "reserved": ["I7"]}],
            }, inp=frames({"tick": 0, "interact": True}), ticks=1)
        cooked = events(rows, "cook_started")[0]["data"]
        self.assertEqual(cooked["items"][0]["id"], "I7")
        self.assertEqual(cooked["base_price"], 47)


class ReservationOrders(unittest.TestCase):
    def test_fixture_reservation_arrives_and_holds_distinct_stock_ids(self):
        with Workdir() as w:
            rows = run_mode(w, "quan", {
                "random_customers": False, "random_reservations": False,
                "time_left_ticks": 3,
                "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                "reservations": [{"id": "R1", "table_id": "T2",
                                  "dish_id": "ca_loc_nuong_trui", "arrival_tick": 1}],
            }, ticks=1)
        self.assertEqual([e["name"] for e in events(rows)], ["reservation_arrived", "customer_arrived"])
        snap = at(rows, 1)
        customer = snap["customers"][0]
        self.assertEqual(customer["reservation_id"], "R1")
        self.assertEqual(customer["reserved"], ["I1"])
        self.assertEqual(next(t for t in snap["tables"] if t["id"] == "T2")["reservation_id"], "R1")

    def test_occupied_reservation_fails_once_with_penalty(self):
        with Workdir() as w:
            rows = run_mode(w, "quan", {
                "random_customers": False, "random_reservations": False,
                "time_left_ticks": 3,
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                               "order_tick": 0, "state": "waiting", "order_status": "assigned",
                               "reserved": []}],
                "reservations": [{"id": "R1", "table_id": "T1",
                                  "dish_id": "ca_loc_nuong_trui", "arrival_tick": 1}],
            }, ticks=1)
        failed = events(rows, "reservation_failed")
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["data"]["reason"], "occupied")
        self.assertEqual(at(rows, 1)["reputation"], 2)

    def test_day_publishes_reservations_after_gather_phase_start(self):
        with Workdir() as w:
            rows = run_day(w, {"gather": {"time_left_ticks": 2},
                               "quan": {"random_reservations": True}}, ticks=0)
        names = [e["name"] for e in events(rows)]
        self.assertEqual(names[:3], ["day_start", "day_plan", "phase_start"])
        published = [e for e in events(rows, "reservation_published")]
        self.assertEqual(len(published), 2)
        self.assertEqual([e["data"]["id"] for e in published], ["R1", "R2"])

    def test_day_two_fixture_items_get_new_ids_and_initial_freshness(self):
        with Workdir() as w:
            rows = run_day(w, {"gather": {"time_left_ticks": 1,
                                          "hold": [{"id": "I7", "kind": "ca_loc", "fresh": 92}]},
                               "quan": {"time_left_ticks": 1, "random_reservations": False}},
                           inp=frames({"tick": 2, "shop_done": True}), days=2, ticks=3)
        day_two = at(rows, 3)
        self.assertEqual(day_two["day"], 2)
        self.assertEqual([(x["id"], x["fresh"]) for x in day_two["hold"]], [("I8", 100)])

