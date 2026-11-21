"""Unit tests cho Phase 3 · M4 (`P3-M4.2`): chốt giá theo độ tươi, boa trên giá đã chốt,
`cook_started.items` mảng cá thể sắp (kind, id), và bàn giao kho cá thể trong `day`/Shop.

Tương thích song song v1.1/v1.2 nên chạy xanh ngay cả trước khi M6.4 bật `contract_version: "1.2"`.
"""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.day import DaySim
from chonoi.sim.quan import QuanSim
from chonoi.sim.shop import ShopSim


def _inp(edges=(), buy=None):
    return InputState((0.0, 0.0), {b: True for b in edges}, set(edges), buy=buy)


class FreshnessPricingM4V12(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def _make_quan(self, stock, customers, player_pos=(2.0, 8.0), hand=None):
        sc = {
            "player": {"pos": list(player_pos)},
            "stock": stock,
            "customers": customers,
            "random_customers": False,
        }
        if hand is not None:
            sc["hand"] = hand
        return QuanSim(self.tuning, sc, Streams(1), IdAllocator())

    def test_ac_p3_m4_01_fresh_100_keeps_full_price(self):
        """AC-P3-M4-01: Nấu ca_loc_nuong_trui với 1 cá thể fresh=100 -> base_price = 60."""
        sim = self._make_quan(
            stock=[{"id": "I1", "kind": "ca_loc", "fresh": 100}],
            customers=[{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}],
        )
        evs = sim.step(_inp(edges=("interact",)))
        cook = [d for n, d in evs if n == "cook_started"][0]
        self.assertEqual(cook["base_price"], 60)
        self.assertEqual(cook["items"], [{"id": "I1", "kind": "ca_loc", "fresh": 100.0}])
        self.assertEqual(sim.snapshot()["stock"], [])

    def test_ac_p3_m4_02_04_05_06_avg_fresh_price_tip_sorted_items_and_removal(self):
        """AC-P3-M4-02/04/05/06: avg=85 -> base_price=102, tip=20, items sắp (kind, id_key), loại đúng id khỏi kho."""
        stock = [
            {"id": "I10", "kind": "ca_linh", "fresh": 80},
            {"id": "I2", "kind": "ca_linh", "fresh": 100},
            {"id": "I5", "kind": "ca_linh", "fresh": 90},
            {"id": "I3", "kind": "bong_dien_dien", "fresh": 70},
            {"id": "I9", "kind": "ca_loc", "fresh": 95},  # không thuộc đơn, phải còn lại
        ]
        sim = self._make_quan(
            stock=stock,
            customers=[{
                "id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien",
                "reserved": ["I10", "I2", "I5", "I3"],
            }],
        )
        evs = sim.step(_inp(edges=("interact",)))
        cook = [d for n, d in evs if n == "cook_started"][0]
        # avg = (100 + 90 + 80 + 70) / 4 = 85 -> floor(120 * 85 / 100) = 102
        self.assertEqual(cook["base_price"], 102)
        # Sắp theo (kind, id_key): bong_dien_dien(I3) rồi ca_linh(I2, I5, I10)
        self.assertEqual(
            [(it["kind"], it["id"]) for it in cook["items"]],
            [("bong_dien_dien", "I3"), ("ca_linh", "I2"), ("ca_linh", "I5"), ("ca_linh", "I10")],
        )
        # Kho chỉ còn lại I9
        self.assertEqual([it["id"] for it in sim.snapshot()["stock"]], ["I9"])
        self.assertEqual(sim.customers[0]["reserved"], [])
        self.assertEqual(sim.customers[0]["order_status"], "assigned")

        # Chờ nấu xong (cook_s = 10 -> 600 tick), bưng món và phục vụ -> tip tính trên 102 (floor(102*0.2) = 20)
        for _ in range(600):
            sim.step(_inp())
        pick_evs = sim.step(_inp(edges=("interact",)))
        self.assertEqual([n for n, _ in pick_evs], ["dish_picked"])
        sim.pos = [9.0, 2.0]  # T1
        serve_evs = sim.step(_inp(edges=("interact",)))
        served = [d for n, d in serve_evs if n == "served"][0]
        self.assertEqual(served["base_price"], 102)
        self.assertEqual(served["tip"], 20)

    def test_ac_p3_m4_03_exact_integer_floor_no_rounding_up(self):
        """AC-P3-M4-03: avg_fresh=97.5 với giá 60 -> floor(58.5) = 58 (không làm tròn lên 59)."""
        sim = self._make_quan(
            stock=[{"id": "I1", "kind": "ca_loc", "fresh": 97.5}],
            customers=[{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}],
        )
        evs = sim.step(_inp(edges=("interact",)))
        cook = [d for n, d in evs if n == "cook_started"][0]
        self.assertEqual(cook["base_price"], 58)

    def test_ac_p3_m4_07_shop_no_decay_and_day_item_instance_handover(self):
        """AC-P3-M4-07: Shop giữ nguyên fresh của mảng cá thể qua 600 tick; DaySim chuyển kho cá thể sang Shop không hao."""
        items = [
            {"id": "I10", "kind": "ca_loc", "fresh": 88.5},
            {"id": "I2", "kind": "bong_sung", "fresh": 42.0},
        ]
        shop = ShopSim(self.tuning, money=0, earned=0, reputation=3.0, upgrades={}, stock=items)
        for _ in range(100):
            shop.step(_inp())
        self.assertEqual(
            shop.snapshot()["stock"],
            [
                {"id": "I2", "kind": "bong_sung", "fresh": 42.0},
                {"id": "I10", "kind": "ca_loc", "fresh": 88.5},
            ],
        )

        # Kiểm tra DaySim chuyển kho cá thể từ quan -> shop cùng tick không làm đổi fresh
        day = DaySim(
            self.tuning,
            {"quan": {"time_left_ticks": 1, "random_customers": False}, "gather": {"random_fish": False}},
            Streams(1),
            IdAllocator(),
            days=1,
        )
        day._start_quan(items)
        self.assertEqual(day.phase, "quan")
        self.assertEqual([x["id"] for x in day.snapshot()["stock"]], ["I2", "I10"])
        day.step(_inp())  # quan hết giờ -> chuyển sang shop
        self.assertEqual(day.phase, "shop")
        self.assertEqual(
            day.snapshot()["stock"],
            [
                {"id": "I2", "kind": "bong_sung", "fresh": 42.0},
                {"id": "I10", "kind": "ca_loc", "fresh": 88.5},
            ],
        )


if __name__ == "__main__":
    unittest.main()
