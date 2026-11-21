"""Unit test cho Shop & Nâng cấp (Người B — Phase 2 / TICKET-02).

Kiểm tra:
1. Mua nâng cấp tuần tự (oxygen Lv 1 -> Lv 2, hp Lv 1 -> Lv 2).
2. Trừ tiền (money) nhưng BẢO TOÀN doanh thu (earned) và điểm số (score).
3. Xử lý thất bại: không đủ tiền (insufficient_money), đã max cấp (max_level), sai mã nâng cấp.
4. Thời gian đóng cửa hàng (auto-close sau 600 ticks hoặc khi người chơi bấm tương tác).
5. Áp dụng hiệu ứng nâng cấp vào tuning cho ngày hôm sau (apply_to_tuning).
"""

import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from chonoi.inputs import InputState
from chonoi.sim.shop import ShopSim, UPGRADE_CATALOG


def _inp(move=(0.0, 0.0), interact=False, buy=None):
    edges = {"interact"} if interact else set()
    inp = InputState(move, set(edges), edges)
    if buy:
        inp.buy = buy
    return inp


class TestShopSim(unittest.TestCase):
    """Bộ test kiểm tra toàn bộ luồng hoạt động của ShopSim."""

    def test_initial_state_and_score(self):
        """Khởi tạo cửa hàng đúng thông số ban đầu và tính điểm chuẩn."""
        shop = ShopSim(money=600, earned=600, reputation=3.8)
        self.assertEqual(shop.money, 600)
        self.assertEqual(shop.earned, 600)
        self.assertEqual(shop.upgrades, {"oxygen": 0, "hp": 0})
        self.assertEqual(shop.time_left_ticks, 600)
        self.assertFalse(shop.done)
        # score = earned + 100 * floor(reputation) = 600 + 100 * 3 = 900
        self.assertEqual(shop.score, 900)

    def test_buy_oxygen_sequential(self):
        """Mua bình oxy tuần tự: Lv 1 (200k -> 45s) rồi Lv 2 (400k -> 60s)."""
        shop = ShopSim(money=700, earned=700, reputation=4.0)

        # Mua Lv 1
        evs1 = shop.buy("oxygen")
        self.assertEqual(len(evs1), 1)
        name1, d1 = evs1[0]
        self.assertEqual(name1, "upgrade_bought")
        self.assertEqual(d1["upgrade_id"], "oxygen")
        self.assertEqual(d1["level"], 1)
        self.assertEqual(d1["price"], 200)
        self.assertEqual(d1["money"], 500)
        self.assertEqual(shop.money, 500)
        self.assertEqual(shop.earned, 700)  # earned bảo toàn
        self.assertEqual(shop.score, 1100)  # score bảo toàn: 700 + 100 * 4
        self.assertEqual(shop.upgrades["oxygen"], 1)
        self.assertEqual(shop.pending_effects["oxygen_max_s"], 45)

        # Mua tiếp Lv 2
        evs2 = shop.buy("oxygen")
        self.assertEqual(len(evs2), 1)
        name2, d2 = evs2[0]
        self.assertEqual(name2, "upgrade_bought")
        self.assertEqual(d2["upgrade_id"], "oxygen")
        self.assertEqual(d2["level"], 2)
        self.assertEqual(d2["price"], 400)
        self.assertEqual(d2["money"], 100)
        self.assertEqual(shop.money, 100)
        self.assertEqual(shop.earned, 700)
        self.assertEqual(shop.upgrades["oxygen"], 2)
        self.assertEqual(shop.pending_effects["oxygen_max_s"], 60)

    def test_buy_hp_sequential(self):
        """Mua nâng cấp HP tuần tự: Lv 1 (250k -> 4 HP) rồi Lv 2 (500k -> 5 HP)."""
        shop = ShopSim(money=800, earned=800, reputation=3.2)

        # Mua HP Lv 1
        evs1 = shop.buy("hp")
        self.assertEqual(len(evs1), 1)
        name1, d1 = evs1[0]
        self.assertEqual(name1, "upgrade_bought")
        self.assertEqual(d1["upgrade_id"], "hp")
        self.assertEqual(d1["level"], 1)
        self.assertEqual(d1["price"], 250)
        self.assertEqual(d1["money"], 550)
        self.assertEqual(shop.upgrades["hp"], 1)
        self.assertEqual(shop.pending_effects["hp_max"], 4)

        # Mua tiếp HP Lv 2
        evs2 = shop.buy("hp")
        self.assertEqual(len(evs2), 1)
        name2, d2 = evs2[0]
        self.assertEqual(name2, "upgrade_bought")
        self.assertEqual(d2["upgrade_id"], "hp")
        self.assertEqual(d2["level"], 2)
        self.assertEqual(d2["price"], 500)
        self.assertEqual(d2["money"], 50)
        self.assertEqual(shop.upgrades["hp"], 2)
        self.assertEqual(shop.pending_effects["hp_max"], 5)

    def test_buy_fails_insufficient_money(self):
        """Thất bại khi không đủ tiền, giữ nguyên tiền và cấp độ."""
        shop = ShopSim(money=150, earned=150, upgrades={"oxygen": 0})
        evs = shop.buy("oxygen")  # Cần 200
        self.assertEqual(len(evs), 1)
        name, d = evs[0]
        self.assertEqual(name, "buy_failed")
        self.assertEqual(d["upgrade_id"], "oxygen")
        self.assertEqual(d["reason"], "insufficient_money")
        self.assertEqual(d["money"], 150)
        self.assertEqual(shop.money, 150)
        self.assertEqual(shop.upgrades["oxygen"], 0)

    def test_buy_fails_max_level_reached(self):
        """Thất bại khi nâng cấp đã đạt mức tối đa (Lv 2)."""
        shop = ShopSim(money=1000, upgrades={"oxygen": 2})
        evs = shop.buy("oxygen")
        self.assertEqual(len(evs), 1)
        name, d = evs[0]
        self.assertEqual(name, "buy_failed")
        self.assertEqual(d["upgrade_id"], "oxygen")
        self.assertEqual(d["reason"], "max_level")
        self.assertEqual(shop.money, 1000)
        self.assertEqual(shop.upgrades["oxygen"], 2)

    def test_buy_fails_invalid_upgrade(self):
        """Thất bại khi upgrade_id không hợp lệ."""
        shop = ShopSim(money=1000)
        evs = shop.buy("super_speed")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0][0], "buy_failed")
        self.assertEqual(evs[0][1]["reason"], "invalid_upgrade")

    def test_shop_auto_close_after_600_ticks(self):
        """Cửa hàng tự động đóng sau 600 ticks (10s) và bắn shop_done."""
        shop = ShopSim(money=500)
        for tick in range(599):
            evs = shop.step(_inp())
            self.assertEqual(evs, [])
            self.assertFalse(shop.done)

        # Tick thứ 600 hết giờ
        evs = shop.step(_inp())
        self.assertTrue(shop.done)
        self.assertEqual(shop.reason, "time")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0][0], "shop_done")
        self.assertEqual(evs[0][1]["reason"], "time")
        self.assertEqual(evs[0][1]["money"], 500)

        # Các tick tiếp theo không phát sinh thêm event
        self.assertEqual(shop.step(_inp()), [])

    def test_shop_user_interact_closes_early(self):
        """Người chơi bấm E (interact) kết thúc sớm và bắn shop_done."""
        shop = ShopSim(money=300)
        # Sau 50 tick người chơi ấn tương tác
        for _ in range(50):
            shop.step(_inp())
        self.assertFalse(shop.done)

        evs = shop.step(_inp(interact=True))
        self.assertTrue(shop.done)
        self.assertEqual(shop.reason, "user")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0][0], "shop_done")
        self.assertEqual(evs[0][1]["reason"], "user")

    def test_apply_upgrades_to_tuning_for_next_day(self):
        """Hiệu ứng nâng cấp được truyền vào tuning ngày tiếp theo."""
        shop = ShopSim(money=1000)
        shop.buy("oxygen")  # Lv 1 -> 45s
        shop.buy("hp")      # Lv 1 -> 4 HP

        base_tuning = {
            "gather": {
                "oxygen_max_s": 30,
                "hp_max": 3,
            }
        }
        updated_tuning = shop.apply_to_tuning(base_tuning)
        self.assertEqual(updated_tuning["gather"]["oxygen_max_s"], 45)
        self.assertEqual(updated_tuning["gather"]["hp_max"], 4)

    def test_snapshot_contains_all_fields(self):
        """Snapshot cửa hàng đầy đủ thông tin trạng thái."""
        shop = ShopSim(money=400, earned=600, reputation=3.5)
        snap = shop.snapshot()
        self.assertEqual(snap["money"], 400)
        self.assertEqual(snap["earned"], 600)
        self.assertEqual(snap["score"], 900)
        self.assertEqual(snap["upgrades"], {"oxygen": 0, "hp": 0})
        self.assertEqual(snap["time_left_ticks"], 600)
        self.assertFalse(snap["done"])


if __name__ == "__main__":
    unittest.main()
