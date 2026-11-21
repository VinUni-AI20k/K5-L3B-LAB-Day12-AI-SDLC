"""P2-06: giá, cấp, thứ tự đóng Shop và hiệu lực từ ngày kế."""

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.runner import Session
from chonoi.sim.shop import ShopSim, apply_gather_upgrades


T = load_contract()["tuning"]
OXYGEN = T["shop"]["upgrades"]["oxygen"]
HP = T["shop"]["upgrades"]["hp"]
LIMIT = T["shop"]["max_ticks"]


def shop(money, *, upgrades=None, stock=None):
    return ShopSim(T, money=money, earned=money + 20, reputation=3.2, upgrades=upgrades, stock=stock)


class ShopTests(unittest.TestCase):
    def test_two_levels_cost_only_money_and_are_visible_immediately(self):
        balance = sum(level["price"] for level in OXYGEN)
        sess = shop(balance)
        initial = sess.snapshot()
        for upgrade in OXYGEN:
            balance -= upgrade["price"]
            self.assertEqual(sess.step("oxygen"), [("bought", {
                "upgrade": "oxygen", "level": upgrade["level"], "price": upgrade["price"], "money": balance,
            })])
            self.assertEqual(sess.snapshot()["upgrades"], {"oxygen": upgrade["level"]})
        self.assertEqual(sess.money, 0)  # Đủ đúng giá ở lần mua cuối.
        self.assertEqual((sess.earned, sess.reputation), (initial["earned"], initial["reputation"]))
        self.assertEqual(initial["upgrades"], {})
        self.assertEqual(sess.step("oxygen"), [("buy_failed", {"action": "oxygen", "reason": "max_level"})])

    def test_insufficient_and_unknown_leave_money_levels_and_stock(self):
        stock = {"ca_keo": 2}
        sess = shop(HP[0]["price"] - 1, stock=stock)
        before = sess.snapshot()
        for action, reason in (("hp", "funds"), ("buy:ca_keo", "unknown"), ("weapon", "unknown")):
            self.assertEqual(sess.step(action), [("buy_failed", {"action": action, "reason": reason})])
        after = sess.snapshot()
        for key in ("money", "earned", "reputation", "upgrades", "stock"):
            self.assertEqual(after[key], before[key])
        self.assertEqual(stock, {"ca_keo": 2})

    def test_buy_precedes_manual_close_even_on_last_tick(self):
        price = HP[0]["price"]
        sess = shop(price)
        for _ in range(LIMIT - 1):
            self.assertEqual(sess.step(), [])
        self.assertEqual(sess.time_left_ticks, 1)
        self.assertEqual(sess.step("hp", done=True), [
            ("bought", {"upgrade": "hp", "level": 1, "price": price, "money": 0}),
            ("shop_end", {"reason": "done"}),
        ])
        self.assertTrue(sess.done)
        self.assertEqual(sess.step("hp", done=True), [])
        self.assertEqual(sess.time_left_ticks, 0)

    def test_timeout_applies_buy_before_closing(self):
        sess = shop(OXYGEN[0]["price"])
        for _ in range(LIMIT - 1):
            sess.step()
        self.assertEqual(sess.step("oxygen"), [
            ("bought", {"upgrade": "oxygen", "level": 1, "price": OXYGEN[0]["price"], "money": 0}),
            ("shop_end", {"reason": "time"}),
        ])
        self.assertTrue(sess.done)
        self.assertEqual(sess.time_left_ticks, 0)

    def test_new_day_applies_purchases_without_mutating_current_tuning(self):
        active = {"oxygen": 1}
        sess = shop(OXYGEN[1]["price"] + HP[0]["price"], upgrades=active)
        current_tuning = apply_gather_upgrades(T, active)
        sess.step("oxygen")
        sess.step("hp", done=True)
        next_tuning = apply_gather_upgrades(T, sess.upgrades)
        self.assertEqual(active, {"oxygen": 1})
        self.assertLess(T["gather"]["oxygen_max_s"], current_tuning["gather"]["oxygen_max_s"])
        self.assertEqual(current_tuning["gather"]["hp_max"], T["gather"]["hp_max"])
        player = Session("gather", next_tuning, {"random_fish": False}, 1).snapshot()["player"]
        self.assertEqual(player["hp"], HP[0]["hp_max"])
        self.assertEqual(player["oxygen_ticks"], OXYGEN[1]["oxygen_max_s"] * T["tick_hz"])
        self.assertEqual(player["oxygen_ticks"], player["oxygen_max_ticks"])
        with self.assertRaises(BadInput):
            apply_gather_upgrades(T, {"hp": -1})
