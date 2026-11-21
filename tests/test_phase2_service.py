"""Kiểm thử độc lập Phục vụ 4 Bàn & 6 Món ăn (Người B — Phase 2 / TICKET-02).

Phụ trách:
1. Phục vụ độc lập tại cả 4 bàn: T1 [9, 2], T2 [13, 2], T3 [9, 6], T4 [13, 6].
2. Tính tiền boa chuẩn floor(giá * 0.2) cho cả 6 món ăn Phase 2:
   - ca_loc_nuong_trui: 60k -> boa 12k (tổng 72k).
   - goi_bong_sung: 40k -> boa 8k (tổng 48k).
   - lau_ca_linh_dien_dien: 120k -> boa 24k (tổng 144k).
   - canh_chua_ca_loc: 90k -> boa 18k (tổng 108k).
   - ca_keo_nuong: 70k -> boa 14k (tổng 84k).
   - lau_mam: 200k -> boa 40k (tổng 240k).
3. Điều kiện biên: đúng 50% kiên nhẫn thì được nhận boa, dưới 50% thì không boa.
4. Tương thích tay cầm (hand) dạng dictionary từ Bếp (Người A).
5. Tính điểm kết thúc ca: score = earned + 100 * floor(reputation).
"""

import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from chonoi.sim.service import handle_table_interact, update_dining


class FakeQuanSim:
    """Mock QuanSim cho kiểm thử độc lập service Phase 2."""

    def __init__(self, customers=None, hand=None, money=0, reputation=3.0):
        self.t = {
            "patience_s": 60,
            "eat_s": 10,
            "tip_rate": 0.2,
            "tip_min_patience_ratio": 0.5,
            "tip_reputation": 0.2,
            "left_reputation_delta": -0.5,
            "reputation_initial": 3.0,
            "reputation_min": 0.0,
            "reputation_max": 5.0,
        }
        self.menu = {
            "ca_loc_nuong_trui": {"recipe": {"ca_loc": 1}, "cook_s": 6, "price": 60},
            "goi_bong_sung": {"recipe": {"bong_sung": 2}, "cook_s": 4, "price": 40},
            "lau_ca_linh_dien_dien": {"recipe": {"ca_linh": 3, "bong_dien_dien": 1}, "cook_s": 10, "price": 120},
            "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
            "ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
            "lau_mam": {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, "cook_s": 12, "price": 200},
        }
        self.customers = customers if customers is not None else []
        self.tables = [
            {"id": "T1", "pos": [9, 2]},
            {"id": "T2", "pos": [13, 2]},
            {"id": "T3", "pos": [9, 6]},
            {"id": "T4", "pos": [13, 6]},
        ]
        self.hand = hand
        self.money = money
        self.earned = money
        self.shift_earned = money
        self.reputation = reputation


class TestPhase2ServiceStandalone(unittest.TestCase):
    """Kiểm thử độc lập Phase 2 Service theo đúng đặc tả Person B."""

    def test_serve_four_tables_independently(self):
        """Phục vụ độc lập tại 4 bàn T1..T4 khi khách ngồi cùng lúc."""
        tables = [
            {"id": "T1", "pos": [9, 2]},
            {"id": "T2", "pos": [13, 2]},
            {"id": "T3", "pos": [9, 6]},
            {"id": "T4", "pos": [13, 6]},
        ]
        customers = [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting_dish", "patience_ticks": 3600, "patience_ticks_left": 3600},
            {"id": "C2", "table_id": "T2", "dish_id": "canh_chua_ca_loc", "state": "waiting_dish", "patience_ticks": 3600, "patience_ticks_left": 3600},
            {"id": "C3", "table_id": "T3", "dish_id": "ca_keo_nuong", "state": "waiting_dish", "patience_ticks": 3600, "patience_ticks_left": 3600},
            {"id": "C4", "table_id": "T4", "dish_id": "lau_mam", "state": "waiting_dish", "patience_ticks": 3600, "patience_ticks_left": 3600},
        ]
        sim = FakeQuanSim(customers=customers)

        # 1. Phục vụ bàn T4 (lẩu mắm 200k)
        sim.hand = "lau_mam"
        evs4 = handle_table_interact(sim, tables[3])
        self.assertEqual(len(evs4), 1)
        self.assertEqual(evs4[0][0], "served")
        self.assertEqual(evs4[0][1]["table_id"], "T4")
        self.assertEqual(evs4[0][1]["dish"], "lau_mam")
        self.assertEqual(evs4[0][1]["tip"], 40)
        self.assertEqual(customers[3]["state"], "eating")

        # 2. Phục vụ bàn T3 (cá kèo nướng 70k)
        sim.hand = "ca_keo_nuong"
        evs3 = handle_table_interact(sim, tables[2])
        self.assertEqual(len(evs3), 1)
        self.assertEqual(evs3[0][1]["table_id"], "T3")
        self.assertEqual(evs3[0][1]["dish"], "ca_keo_nuong")
        self.assertEqual(evs3[0][1]["tip"], 14)
        self.assertEqual(customers[2]["state"], "eating")

        # 3. Phục vụ bàn T2 (canh chua cá lóc 90k)
        sim.hand = "canh_chua_ca_loc"
        evs2 = handle_table_interact(sim, tables[1])
        self.assertEqual(len(evs2), 1)
        self.assertEqual(evs2[0][1]["table_id"], "T2")
        self.assertEqual(evs2[0][1]["dish"], "canh_chua_ca_loc")
        self.assertEqual(evs2[0][1]["tip"], 18)
        self.assertEqual(customers[1]["state"], "eating")

        # 4. Phục vụ bàn T1 (cá lóc nướng trui 60k)
        sim.hand = "ca_loc_nuong_trui"
        evs1 = handle_table_interact(sim, tables[0])
        self.assertEqual(len(evs1), 1)
        self.assertEqual(evs1[0][1]["table_id"], "T1")
        self.assertEqual(evs1[0][1]["dish"], "ca_loc_nuong_trui")
        self.assertEqual(evs1[0][1]["tip"], 12)
        self.assertEqual(customers[0]["state"], "eating")

        # Tất cả 4 bàn đã được phục vụ và chuyển sang eating
        for c in customers:
            self.assertEqual(c["state"], "eating")

    def test_all_six_dishes_pricing_and_tips(self):
        """Tính đúng giá và tiền boa cho tất cả 6 món ăn Phase 2."""
        specs = [
            ("ca_loc_nuong_trui", 60, 12),      # 60k -> boa 12k
            ("goi_bong_sung", 40, 8),          # 40k -> boa 8k
            ("lau_ca_linh_dien_dien", 120, 24), # 120k -> boa 24k
            ("canh_chua_ca_loc", 90, 18),      # 90k -> boa 18k
            ("ca_keo_nuong", 70, 14),          # 70k -> boa 14k
            ("lau_mam", 200, 40),              # 200k -> boa 40k
        ]
        table = {"id": "T1", "pos": [9, 2]}

        for dish, price, tip in specs:
            cust = {
                "id": f"C_{dish}",
                "table_id": "T1",
                "dish_id": dish,
                "state": "waiting_dish",
                "patience_ticks": 3600,
                "patience_ticks_left": 3600,
            }
            sim = FakeQuanSim(customers=[cust], hand=dish)
            evs = handle_table_interact(sim, table)
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0][1]["tip"], tip)
            self.assertEqual(cust["base_price"], price)
            self.assertEqual(cust["tip"], tip)

            # Thanh toán khi ăn xong
            cust["eat_ticks_left"] = 0
            paid_evs = update_dining(sim)
            self.assertEqual(len(paid_evs), 1)
            self.assertEqual(paid_evs[0][1]["amount"], price + tip)
            self.assertEqual(paid_evs[0][1]["tip"], tip)
            self.assertEqual(sim.money, price + tip)

    def test_tip_boundary_50_percent(self):
        """Đúng 50% kiên nhẫn được boa, 49.9% không được boa."""
        table = {"id": "T1", "pos": [9, 2]}

        # Đúng 50% kiên nhẫn (1800/3600 = 0.5)
        c50 = {
            "id": "C50",
            "table_id": "T1",
            "dish_id": "lau_mam",
            "state": "waiting_dish",
            "patience_ticks": 3600,
            "patience_ticks_left": 1800,
        }
        sim50 = FakeQuanSim(customers=[c50], hand="lau_mam")
        handle_table_interact(sim50, table)
        self.assertEqual(c50["tip"], 40)

        # Dưới 50% kiên nhẫn (1799/3600 = 0.4997)
        c49 = {
            "id": "C49",
            "table_id": "T1",
            "dish_id": "lau_mam",
            "state": "waiting_dish",
            "patience_ticks": 3600,
            "patience_ticks_left": 1799,
        }
        sim49 = FakeQuanSim(customers=[c49], hand="lau_mam")
        handle_table_interact(sim49, table)
        self.assertEqual(c49["tip"], 0)

    def test_hand_dict_from_kitchen_compatibility(self):
        """Tương thích khi Bếp (Người A) chuyển món dạng dict lên tay."""
        table = {"id": "T1", "pos": [9, 2]}
        cust = {
            "id": "C1",
            "table_id": "T1",
            "dish_id": "canh_chua_ca_loc",
            "state": "waiting_dish",
            "patience_ticks": 3600,
            "patience_ticks_left": 2500,
        }
        hand_dict = {
            "order_id": "C1",
            "dish_id": "canh_chua_ca_loc",
            "base_price": 90,
        }
        sim = FakeQuanSim(customers=[cust], hand=hand_dict)
        evs = handle_table_interact(sim, table)
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0][1]["dish"], "canh_chua_ca_loc")
        self.assertEqual(evs[0][1]["tip"], 18)
        self.assertIsNone(sim.hand)
        self.assertEqual(cust["state"], "eating")
        self.assertEqual(cust["base_price"], 90)

    def test_score_calculation(self):
        """Công thức điểm số ca: score = earned + 100 * floor(reputation)."""
        sim = FakeQuanSim(money=1200, reputation=4.7)
        score = sim.earned + 100 * math.floor(sim.reputation)
        self.assertEqual(score, 1200 + 400)


if __name__ == "__main__":
    unittest.main()

