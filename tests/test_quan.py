"""Unit test luật quán (PRD-0 mục F, Quán): lát 3 (khách) + lát 4 (bếp, bưng, phục vụ, tiền)."""

import json
import unittest

from chonoi.inputs import InputState
from chonoi.runner import Session


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


def make(scn=None, seed=1, inventory=None):
    block = (scn or {}).get("quan", {})  # Session nhận đúng khối `quan` (như scenario.load_scenario trả về)
    return Session("quan", tuning(), block, seed, inventory)  # contract v1.1: preset đã có T1..T4


def idle():
    return InputState((0.0, 0.0), {}, set())


def press():
    return InputState((0.0, 0.0), {}, {"interact"})


def run(sess, n, first=None):
    """Chạy n bước (bước đầu có thể nhấn E); trả list (tick, name, data)."""
    out = []
    for i in range(n):
        for e in sess.step(first if (i == 0 and first) else idle()):
            out.append((e["tick"], e["name"], e["data"]))
    return out


def names(ev):
    return [e[1] for e in ev]


class Customers(unittest.TestCase):
    def test_first_customer_at_tick_120_with_reservation(self):
        s = make({"quan": {"stock": {"ca_loc": 1}}})
        ev = run(s, 120)
        self.assertEqual(names(ev), ["customer_arrived"])
        self.assertEqual(ev[0][0], 120)
        self.assertEqual(ev[0][2], {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"})
        c = s.sim.customers[0]
        self.assertEqual(c["order_tick"], 120)
        self.assertEqual(c["patience_ticks_left"], 3600)
        self.assertEqual(c["reserved"], {"ca_loc": 1})

    def test_no_dish_when_empty_stock(self):
        s = make()
        ev = run(s, 120)
        self.assertEqual(ev, [(120, "no_dish", {})])
        self.assertEqual(s.sim.customers, [])

    def test_no_free_table_skips_without_no_dish(self):
        # v1.1: preset có 4 bàn -> phải chiếm đủ T1..T4 thì lượt đến mới bị bỏ qua (không phát no_dish)
        cs = [{"id": f"C{i}", "table_id": f"T{i}", "dish_id": "ca_loc_nuong_trui"} for i in range(1, 5)]
        s = make({"quan": {"stock": {"ca_loc": 5}, "customers": cs}})
        self.assertEqual(run(s, 120 + 900), [])

    def test_random_customers_false(self):
        s = make({"quan": {"stock": {"ca_loc": 1}, "random_customers": False}})
        self.assertEqual(run(s, 300), [])

    def test_reservation_excludes_available_stock(self):
        # kho chỉ đủ 1 phần; khách 1 giữ chỗ, khách 2 (bàn khác) phải no_dish
        sc = {"quan": {"stock": {"ca_loc": 1}}}
        s = make(sc)
        ev = run(s, 120 + 900)
        self.assertEqual(names(ev), ["customer_arrived", "no_dish"])

    def test_patience_leave_cuts_reputation(self):
        sc = {"quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}],
                       "stock": {"ca_loc": 1}, "random_customers": False}}
        s = make(sc)
        ev = run(s, 3600)
        self.assertEqual(ev, [(3600, "customer_left",
                               {"order_id": "C1", "table_id": "T1", "reason": "patience", "reputation": 2.5})])
        self.assertEqual(s.sim.customers, [])


class Kitchen(unittest.TestCase):
    def scn(self, **extra):
        q = {"player": {"pos": [2, 8]}, "stock": {"ca_loc": 1}, "random_customers": False,
             "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}
        q.update(extra)
        return {"quan": q}

    def test_cook_pick_serve_pay_with_tip(self):
        s = make(self.scn())
        ev = run(s, 1, press())
        self.assertEqual(ev, [(1, "cook_started", {"stove_id": "B1", "order_id": "C1",
                                                    "dish_id": "ca_loc_nuong_trui", "items": ["ca_loc"],
                                                    "base_price": 60})])
        self.assertEqual(s.sim.stock, {"ca_loc": 0})
        self.assertEqual(s.sim.customers[0]["order_status"], "assigned")
        ev = run(s, 360)  # cook_s = 6 -> 360 tick
        self.assertEqual(ev, [(361, "dish_ready", {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui"})])
        ev = run(s, 1, press())
        self.assertEqual(names(ev), ["dish_picked"])
        self.assertEqual(s.sim.hand["order_id"], "C1")
        s.sim.pos = [9.0, 2.0]  # dịch tới bàn
        ev = run(s, 1, press())
        # kiên nhẫn đã giảm 363 tick -> còn 3237/3600 >= 0.5 -> boa floor(60*0.2) = 12
        self.assertEqual(ev[0][1:], ("served", {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                                "patience_ticks_left": 3237, "base_price": 60, "tip": 12}))
        ev = run(s, 600)  # eat_s = 10
        self.assertEqual(ev[0][1], "paid")
        self.assertEqual(ev[0][2]["amount"], 72)
        self.assertEqual((s.sim.money, s.sim.earned, s.sim.shift_earned), (72, 72, 72))
        self.assertAlmostEqual(s.sim.reputation, 3.2)

    def test_no_tip_below_ratio(self):
        s = make(self.scn(hand={"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                          customers=[{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                      "order_status": "assigned", "patience_ticks_left": 1799, "reserved": {}}],
                          stock={}, player={"pos": [9, 2]}))
        ev = run(s, 1, press())
        self.assertEqual(ev[0][2]["tip"], 0)  # 1798/3600 < 0.5

    def test_tip_at_exact_ratio(self):
        s = make(self.scn(hand={"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                          customers=[{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                      "order_status": "assigned", "patience_ticks_left": 1801, "reserved": {}}],
                          stock={}, player={"pos": [9, 2]}))
        ev = run(s, 1, press())
        self.assertEqual(ev[0][2]["patience_ticks_left"], 1800)
        self.assertEqual(ev[0][2]["tip"], 12)  # đúng 0.5 vẫn có boa (>=)

    def test_wrong_order_at_table_ignored(self):
        s = make(self.scn(hand={"order_id": "C9", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                          player={"pos": [9, 2]}))
        self.assertEqual(run(s, 1, press()), [])

    def test_serve_on_tick_patience_zero_is_valid(self):
        s = make(self.scn(hand={"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                          customers=[{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                      "order_status": "assigned", "patience_ticks_left": 1, "reserved": {}}],
                          stock={}, player={"pos": [9, 2]}))
        ev = run(s, 1, press())
        self.assertEqual(names(ev), ["served"])
        self.assertEqual(ev[0][2]["tip"], 0)

    def test_leaving_customer_discards_dish_in_hand(self):
        s = make(self.scn(hand={"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                          customers=[{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                      "order_status": "assigned", "patience_ticks_left": 1, "reserved": {}}],
                          stock={}, player={"pos": [2, 8]}))
        ev = run(s, 1)
        self.assertEqual(names(ev), ["customer_left"])
        self.assertIsNone(s.sim.hand)

    def test_stove_before_table_on_tie(self):
        # bếp và bàn cùng khoảng cách: bếp trước. Đặt bàn T1 chồng lên bếp B1.
        s = make(self.scn(tables=[{"id": "T1", "pos": [2, 8]}], player={"pos": [2, 8]}))
        self.assertEqual(names(run(s, 1, press())), ["cook_started"])

    def test_closing_paying_and_leaving(self):
        sc = self.scn(time_left_ticks=2,
                      customers=[{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                  "state": "eating", "order_status": "served", "eat_ticks_left": 500,
                                  "base_price": 60, "tip": 12, "reserved": {}},
                                 {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung"}],
                      stock={"bong_sung": 2})
        s = make(sc)
        ev = run(s, 2)
        self.assertEqual(names(ev), ["paid", "customer_left", "quan_end"])
        self.assertEqual(ev[0][2]["reason"], "closing")
        self.assertEqual(ev[1][2]["reason"], "closing")
        self.assertEqual(ev[1][2]["reputation"], 3.2)  # chỉ cộng boa của C1, không trừ khi closing
        self.assertTrue(s.done)

    def test_deterministic_same_seed(self):
        a = run(make({"quan": {"stock": {"ca_loc": 3, "bong_sung": 4}}}, seed=5), 3000)
        b = run(make({"quan": {"stock": {"ca_loc": 3, "bong_sung": 4}}}, seed=5), 3000)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
