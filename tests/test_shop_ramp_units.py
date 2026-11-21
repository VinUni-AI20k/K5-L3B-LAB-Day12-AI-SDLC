"""Unit test cho hai module luật chỉ được phủ gián tiếp qua smoke/day: `chonoi/sim/shop.py` (Shop cuối Ngày,
Test Contract v1.1 mục 2 và 4.5) và `chonoi/sim/ramp.py` (ramp_max_ticks, PRD-0). Giá/cấp đọc từ game.contract.json."""

import types
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.sim.ramp import ramp_velocity
from chonoi.sim.shop import ShopSim


def frame(buy=None, done=False):
    return InputState((0, 0), {}, {"shop_done"} if done else set(), buy)


class ShopUnits(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.levels = self.tuning["shop"]["upgrades"]

    def shop(self, money, upgrades=None):
        return ShopSim(self.tuning, money, upgrades if upgrades is not None else {})

    def test_buy_next_level_deducts_only_money(self):
        lv1 = self.levels["oxygen"][0]
        s = self.shop(lv1["price"])  # đủ đúng giá vẫn mua được
        ev = s.step(frame(buy="oxygen"))
        self.assertEqual(ev, [("bought", {"upgrade": "oxygen", "level": 1, "price": lv1["price"], "money": 0})])
        self.assertEqual(s.money, 0)
        self.assertEqual(s.upgrades, {"oxygen": 1})

    def test_buy_failed_reasons(self):
        top = max(lv["level"] for lv in self.levels["hp"])
        cases = [
            (self.shop(10**6), "lan_ca", "unknown"),
            (self.shop(10**6, {"hp": top}), "hp", "max_level"),
            (self.shop(self.levels["hp"][0]["price"] - 1), "hp", "funds"),
        ]
        for s, action, reason in cases:
            with self.subTest(reason=reason):
                money = s.money
                self.assertEqual(s.step(frame(buy=action)), [("buy_failed", {"action": action, "reason": reason})])
                self.assertEqual(s.money, money)

    def test_buy_is_handled_before_shop_done_on_same_frame(self):
        s = self.shop(10**6)
        ev = s.step(frame(buy="hp", done=True))
        self.assertEqual([e[0] for e in ev], ["bought", "shop_end"])
        self.assertEqual(ev[1][1], {"reason": "done"})
        self.assertTrue(s.done)

    def test_time_out_closes_shop(self):
        s = self.shop(0)
        ev = []
        for _ in range(int(self.tuning["shop"]["max_ticks"])):
            ev = s.step(frame())
        self.assertEqual(ev, [("shop_end", {"reason": "time"})])
        self.assertEqual((s.time_left_ticks, s.reason), (0, "time"))

    def test_snapshot_sorts_leftover_stock_by_id(self):
        s = ShopSim(self.tuning, 0, {}, stock=[{"id": "I10", "kind": "ca_linh", "units": 1},
                                                {"id": "I2", "kind": "ca_linh", "units": 1}])
        self.assertEqual([it["id"] for it in s.snapshot()["stock"]], ["I2", "I10"])


class RampUnits(unittest.TestCase):
    def sim(self):
        return types.SimpleNamespace(vel=[0.0, 0.0], _tgt=None, _ramp_left=0)

    def run_ticks(self, s, target, ramp, n):
        out = []
        for _ in range(n):
            s.vel = ramp_velocity(s, target, ramp)
            out.append(list(s.vel))
        return out

    def test_ramp_zero_applies_immediately(self):
        self.assertEqual(self.run_ticks(self.sim(), (2, -1), 0, 1), [[2.0, -1.0]])

    def test_reaches_target_after_exactly_ramp_ticks(self):
        vs = self.run_ticks(self.sim(), (4, 0), 4, 5)
        self.assertEqual([v[0] for v in vs], [1.0, 2.0, 3.0, 4.0, 4.0])

    def test_changing_target_restarts_ramp_from_current_velocity(self):
        s = self.sim()
        self.run_ticks(s, (4, 0), 4, 2)  # vel = 2
        vs = self.run_ticks(s, (0, 0), 2, 2)
        self.assertEqual([v[0] for v in vs], [1.0, 0.0])


if __name__ == "__main__":
    unittest.main()
