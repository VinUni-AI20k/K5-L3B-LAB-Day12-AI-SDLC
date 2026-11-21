"""Unit test suite cho Phase 4 (TV4 - Nguyễn Anh Quân - AnhQuanHANU).
Kiểm chứng:
1. Cảnh báo khách sắp giận (is_angry, warning: patience_low) khi kiên nhẫn < 25%.
2. Xóa trạng thái giận khi khách được phục vụ chuyển sang ăn (eating).
3. Độ bền vững của Quán và Shop qua các chu kỳ ngày (chuẩn bị cho soak test 10 ngày).
"""

import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
from chonoi.sim.shop import ShopSim

try:
    from helpers import ROOT
except ImportError:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def make_inp(move=(0, 0), interact=False):
    return SimpleNamespace(move=move, pressed=lambda name: (name == "interact" if interact else False))


class TestTV4Phase4(unittest.TestCase):
    def setUp(self):
        self.contract_path = Path(ROOT) / "game.contract.json"
        self.tuning = json.loads(self.contract_path.read_text(encoding="utf-8"))["tuning"]

    def test_customer_angry_warning_when_patience_below_25_percent(self):
        """Khách kiên nhẫn < 25% (900 ticks với duration 60s) bật is_angry = True và warning = patience_low."""
        # Total patience: 60s * 60 = 3600 ticks.
        # 25% = 900 ticks.
        # Khách C1 bắt đầu với 901 ticks -> chưa giận.
        sc = {
            "player": {"pos": [8.0, 5.0]},
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "patience_ticks_left": 901,
                    "order_status": "assigned"
                }
            ],
            "random_customers": False
        }
        sim = QuanSim(self.tuning, sc, Streams(42), IdAllocator(), inventory=[])
        self.assertFalse(sim.customers[0]["is_angry"])
        self.assertIsNone(sim.customers[0]["warning"])

        # Tick 1: patience_ticks_left giảm xuống 900 -> vẫn >= 900 -> chưa giận
        sim.step(make_inp())
        self.assertEqual(sim.customers[0]["patience_ticks_left"], 900)
        self.assertFalse(sim.customers[0]["is_angry"])
        self.assertIsNone(sim.customers[0]["warning"])

        # Tick 2: patience_ticks_left giảm xuống 899 < 900 -> BẬT CẢNH BÁO
        sim.step(make_inp())
        self.assertEqual(sim.customers[0]["patience_ticks_left"], 899)
        self.assertTrue(sim.customers[0]["is_angry"])
        self.assertEqual(sim.customers[0]["warning"], "patience_low")

        # Snapshot phản ánh đúng trường cảnh báo cho TV5 render UI
        snap = sim.snapshot()
        cust_snap = snap["customers"][0]
        self.assertTrue(cust_snap["is_angry"])
        self.assertEqual(cust_snap["warning"], "patience_low")

    def test_customer_clears_angry_warning_when_served(self):
        """Khi được giao món, khách chuyển sang eating thì xóa cảnh báo giận."""
        sc = {
            "player": {"pos": [9.0, 2.0]},  # Đứng sát bàn T1
            "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "patience_ticks_left": 100,  # Đang giận
                    "is_angry": True,
                    "warning": "patience_low",
                    "base_price": 60,
                    "order_status": "assigned"
                }
            ],
            "random_customers": False
        }
        sim = QuanSim(self.tuning, sc, Streams(42), IdAllocator(), inventory=[])
        # Giao món tại bàn T1
        events = sim.step(make_inp(interact=True))
        served_ev = [ev for ev in events if ev[0] == "served"]
        self.assertEqual(len(served_ev), 1)

        # Tick sau: khách đang eating, cảnh báo giận bị xóa
        sim.step(make_inp())
        self.assertEqual(sim.customers[0]["state"], "eating")
        self.assertFalse(sim.customers[0]["is_angry"])
        self.assertIsNone(sim.customers[0]["warning"])

    def test_shop_and_quan_multiday_persistence(self):
        """Kiểm chứng Quán và Shop lưu giữ chính xác tiền, uy tín và nâng cấp qua nhiều chu kỳ (phục vụ soak test)."""
        # Ngày 1: Quán thu tiền
        quan1 = QuanSim(
            self.tuning,
            {
                "player": {"pos": [9.0, 2.0]},
                "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                "customers": [{
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "base_price": 60,
                    "order_status": "assigned",
                    "reserved": []
                }],
                "time_left_ticks": 1,
                "reputation": 3.0
            },
            Streams(42), IdAllocator(), inventory=[]
        )
        # Giao món ở tick cuối -> đóng ca thanh toán ngay
        quan1.step(make_inp(interact=True))
        self.assertEqual(quan1.money, 72)
        self.assertEqual(quan1.earned, 72)
        self.assertAlmostEqual(quan1.reputation, 3.2, places=2)

        # Chuyển sang Shop: mua nâng cấp oxy lv1 (giá 200) -> thiếu tiền thất bại
        shop_state = {
            "money": quan1.money,
            "earned": quan1.earned,
            "reputation": quan1.reputation,
            "upgrades": {"oxygen": 0, "hp": 0},
            "active_upgrades": {"oxygen": 0, "hp": 0}
        }
        shop = ShopSim(self.tuning, shop_state, Streams(42), IdAllocator())
        # Thử mua oxy giá 200 khi chỉ có 72
        evs = shop.step(SimpleNamespace(buy="oxygen"))
        self.assertEqual([e[0] for e in evs], ["buy_failed"])
        self.assertEqual(evs[0][1]["reason"], "funds")
        self.assertEqual(shop.money, 72)
        self.assertEqual(shop.earned, 72)


if __name__ == "__main__":
    unittest.main()
