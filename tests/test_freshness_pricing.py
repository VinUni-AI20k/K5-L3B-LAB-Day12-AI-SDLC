"""P3-04: real kitchen/lifecycle with explicitly mocked P3-03 boundary."""
from copy import deepcopy
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.sim.freshness_pricing import consume_fresh_order
from p3_04_boundary_fixture import FRESHNESS, item, order, session, step


class FreshnessPricing(unittest.TestCase):
    def test_tick_one_decays_before_price_floor_59(self):
        s = session()
        started, = step(s, True)
        self.assertEqual((started["tick"], started["name"], started["data"]["base_price"]), (1, "cook_started", 59))
        self.assertAlmostEqual(started["data"]["items"][0]["fresh"], 100 - 1 / 240, places=12)
        self.assertEqual(s.sim.stock, [])
        self.assertEqual(s.sim.customers[0]["reserved"], [])
        self.assertEqual(s.sim.customers[0]["order_status"], "assigned")

    def test_two_bong_sung_at_cook_80_70_price_30(self):
        s = session([item("I10", "bong_sung", 80), item("I2", "bong_sung", 70)],
                    [order(dish="goi_bong_sung", reserved=["I10", "I2"])])
        events = []
        s.sim._interact_stove(s.sim.stoves[0], events)  # State AFTER P3-03's decay.
        data = events[0][1]
        self.assertEqual(data["base_price"], 30)
        self.assertEqual([i["id"] for i in data["items"]], ["I2", "I10"])

    def test_80_70_at_tick_zero_must_decay_and_floor_to_29(self):
        s = session([item("I1", "bong_sung", 80), item("I2", "bong_sung", 70)],
                    [order(dish="goi_bong_sung", reserved=["I1", "I2"])])
        self.assertEqual(step(s, True)[0]["data"]["base_price"], 29)

    def test_average_is_weighted_by_individual_not_kind(self):
        stock = [item("I1", "ca_linh", 30), item("I2", "ca_linh", 30),
                 item("I3", "ca_linh", 90), item("I4", "bong_dien_dien", 90)]
        c = order(dish="lau_ca_linh_dien_dien", reserved=[i["id"] for i in stock])
        price, _ = consume_fresh_order(stock, [c], c, load_contract()["tuning"]["menu"][c["dish_id"]], FRESHNESS)
        self.assertEqual(price, 72)  # (30+30+90+90)/4=60, not per-kind average=70.

    def test_spoiled_reserved_cannot_cook_and_retry_is_scripted_once(self):
        s = session([item(fresh=30)])
        events = step(s, True)
        self.assertEqual([e["name"] for e in events], ["spoiled"])
        self.assertEqual(s.sim.customers[0]["order_status"], "unfulfillable")
        self.assertEqual(s.sim.customers[0]["reserved"], [])
        self.assertEqual(s.sim.stoves[0]["state"], "idle")
        step(s, True)
        self.assertEqual(s.sim.retry_calls, ["C1"])
        self.assertEqual(len(s.sim.stock), 1)

    def test_scripted_re_reserve_before_cook_uses_new_id_only(self):
        s = session([item(fresh=30), item("I2", fresh=80)], replacements={"C1": ["I2"]})
        events = step(s, True)
        self.assertEqual([e["name"] for e in events], ["spoiled", "cook_started"])
        self.assertEqual([i["id"] for i in events[1]["data"]["items"]], ["I2"])
        self.assertEqual(events[1]["data"]["base_price"], 47)
        self.assertEqual([i["id"] for i in s.sim.stock], ["I1"])
        self.assertEqual(s.sim.retry_calls, ["C1"])

    def test_two_stoves_never_double_consume_or_replace_claims(self):
        s = session([item("I1"), item("I2", fresh=80), item("I3", fresh=100)],
                    [order(), order("C2", "T2", reserved=["I2"])])
        first, = step(s, True)
        s.sim.pos = [5, 8]
        second, = step(s, True)
        self.assertEqual([e["data"]["items"][0]["id"] for e in (first, second)], ["I1", "I2"])
        self.assertEqual([e["data"]["base_price"] for e in (first, second)], [59, 47])
        self.assertEqual(step(s, True), [])
        self.assertEqual([i["id"] for i in s.sim.stock], ["I3"])
        self.assertEqual([b["dish"]["order_id"] for b in s.sim.stoves], ["C1", "C2"])

    def test_price_locks_through_ready_hand_served_paid_and_score(self):
        s = session()
        step(s, True)
        s.sim.menu["ca_loc_nuong_trui"]["price"] = 999  # Never used after cook.
        for _ in range(359):
            step(s)
        ready_pick = step(s, True)
        self.assertEqual([e["name"] for e in ready_pick], ["dish_ready", "dish_picked"])
        self.assertEqual(s.sim.hand["base_price"], 59)
        s.sim.pos = [9, 2]
        served, = step(s, True)
        self.assertEqual((served["data"]["base_price"], served["data"]["tip"]), (59, 11))
        self.assertEqual(s.sim.money, 0)
        rows = [e for _ in range(600) for e in step(s)]
        paid = [e for e in rows if e["name"] == "paid"]
        self.assertEqual(len(paid), 1)
        self.assertEqual(paid[0]["data"]["amount"], 70)
        self.assertEqual((s.sim.money, s.sim.earned, s.sim.shift_earned, s.sim.reputation), (70, 70, 70, 3.2))
        self.assertEqual(s.end_row()["score"], 370)
        self.assertEqual(step(s), [])

    def test_tip_boundary_on_locked_price(self):
        for remaining, tip in ((1801, 11), (1800, 0)):
            with self.subTest(remaining=remaining):
                s = session()
                step(s, True)
                for _ in range(360):
                    step(s)
                step(s, True)
                s.sim.customers[0]["patience_ticks_left"] = remaining
                s.sim.pos = [9, 2]
                self.assertEqual(step(s, True)[0]["data"]["tip"], tip)

    def test_closing_and_zero_patience_pay_once_without_refund(self):
        s = session()
        step(s, True)
        for _ in range(360):
            step(s)
        step(s, True)
        s.sim.customers[0]["patience_ticks_left"] = 1
        s.sim.pos = [9, 2]
        s.sim.time_left_ticks = 1
        rows = step(s, True)
        self.assertEqual([e["name"] for e in rows], ["served", "paid", "quan_end"])
        self.assertEqual(rows[1]["data"]["amount"], 59)
        self.assertEqual(rows[1]["data"]["reason"], "closing")
        self.assertEqual(s.sim.stock, [])
        self.assertEqual(step(s, True), [])

    def test_timeout_cleans_dish_and_keeps_other_physical_items(self):
        for location in ("cooking", "ready", "hand"):
            with self.subTest(location=location):
                s = session([item(), item("I2")])
                step(s, True)
                if location != "cooking":
                    for _ in range(360):
                        step(s)
                if location == "hand":
                    step(s, True)
                c = s.sim.customers[0]
                c["patience_ticks_left"] = 1
                self.assertEqual(step(s)[0]["name"], "customer_left")
                self.assertEqual(c["reserved"], [])
                self.assertIsNone(s.sim.hand)
                self.assertEqual(s.sim.stoves[0]["state"], "idle")
                self.assertEqual([i["id"] for i in s.sim.stock], ["I2"])

    def test_atomic_rejection_of_invalid_claims_freshness_and_ownership(self):
        cases = [([item()], ["missing"], []), ([item()], ["I1", "I1"], []),
                 ([item()], ["I1"], [order("C2", "T2")]),
                 ([item(fresh=29.999999999)], ["I1"], []), ([item(kind="ca_keo")], ["I1"], []),
                 ([item(), item()], ["I1"], [])]
        cases += [([item(fresh=f)], ["I1"], []) for f in (float("nan"), float("inf"), True, -1, 101)]
        for stock, ids, others in cases:
            with self.subTest(ids=ids, stock=stock):
                c = order(reserved=ids)
                snapshot = deepcopy(stock)
                result = consume_fresh_order(stock, [c, *others], c,
                                             load_contract()["tuning"]["menu"][c["dish_id"]], FRESHNESS)
                self.assertIsNone(result)
                self.assertEqual([i["id"] for i in stock], [i["id"] for i in snapshot])
                self.assertEqual(c["order_status"], "reserved")
                self.assertEqual(c["reserved"], ids)

    def test_exact_threshold_and_no_double_consumption(self):
        stock = [item(fresh=30)]
        c = order()
        menu = load_contract()["tuning"]["menu"][c["dish_id"]]
        self.assertEqual(consume_fresh_order(stock, [c], c, menu, FRESHNESS)[0], 18)
        self.assertIsNone(consume_fresh_order(stock, [c], c, menu, FRESHNESS))

    def test_event_items_sorted_kind_then_natural_id_and_are_copies(self):
        stock = [item("I10", "ca_linh", 70), item("I2", "ca_linh", 70), item("I7", "bong_dien_dien", 70),
                 item("I3", "ca_keo", 70), item("I1", "keo_neo", 70)]
        original = stock[0]
        c = order(dish="lau_mam", reserved=[i["id"] for i in stock])
        menu = load_contract()["tuning"]["menu"][c["dish_id"]]
        price, items = consume_fresh_order(stock, [c], c, menu, FRESHNESS)
        self.assertEqual(price, 140)
        self.assertEqual([i["id"] for i in items], ["I7", "I3", "I2", "I10", "I1"])
        original["fresh"] = 0
        self.assertEqual(items[3]["fresh"], 70)

    def test_all_six_recipes_consume_individuals_at_exact_price(self):
        expected = {"ca_loc_nuong_trui": 42, "goi_bong_sung": 28, "lau_ca_linh_dien_dien": 84,
                    "canh_chua_ca_loc": 63, "ca_keo_nuong": 49, "lau_mam": 140}
        for dish, price in expected.items():
            with self.subTest(dish=dish):
                menu = load_contract()["tuning"]["menu"][dish]
                stock = [item(f"I{n}", kind, 70) for n, kind in enumerate(
                    (k for k, count in menu["recipe"].items() for _ in range(count)), 1)]
                c = order(dish=dish, reserved=[i["id"] for i in stock])
                self.assertEqual(consume_fresh_order(stock, [c], c, menu, FRESHNESS)[0], price)
                self.assertEqual(stock, [])

    def test_missing_configuration_is_an_explicit_dependency_error(self):
        with self.assertRaises(BadInput):
            consume_fresh_order([item()], [], order(), {"recipe": {"ca_loc": 1}, "price": 60}, None)

    def test_pause_does_not_call_mock_decay_and_resume_runs_it_once(self):
        s = session()
        self.assertEqual(step(s, pause=True)[0]["name"], "paused")
        step(s)
        self.assertEqual(s.sim.stock[0]["fresh"], 100)
        rows = step(s, interact=True, pause=True)
        self.assertEqual([e["name"] for e in rows], ["resumed", "cook_started"])
        self.assertEqual(rows[-1]["data"]["base_price"], 59)
        self.assertEqual((s.tick, s.sim_tick, s.sim.tick), (3, 1, 1))
