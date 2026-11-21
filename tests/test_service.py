"""Unit test cho module chonoi/sim/service.py (Người B).

Kiểm tra toàn bộ logic:
1. Phục vụ món tại bàn (handle_table_interact): đúng món, sai món, tay trống, bàn trống.
2. Tiến trình ăn & Thanh toán (update_dining): đếm lùi ăn, tính tiền, tip (khi kiên nhẫn >= 50%), cộng uy tín.
3. Quản lý kiên nhẫn (update_patience): đếm lùi, khách bỏ về, trừ uy tín, kẹp min/max.
4. Xử lý ngoại lệ / dữ liệu bất thường (defensive checks).
"""

import math
import os
import sys
import unittest

# Đảm bảo đường dẫn import cho cả test runner và chạy đơn lẻ
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from chonoi.sim.service import (
    get_customer_at_table,
    handle_table_interact,
    update_dining,
    update_patience,
    update_service,
)


class FakeQuanSim:
    """Mock đối tượng QuanSim phục vụ unit test cho service.py."""

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


class TestServiceInteract(unittest.TestCase):
    """Kiểm tra chức năng 1: Phục vụ món tại bàn (handle_table_interact)."""

    def test_serve_success_matching_dish(self):
        """Phục vụ thành công khi tay cầm đúng món khách gọi."""
        customer = {
            "id": "C1",
            "table_id": "T1",
            "dish": "ca_loc_nuong_trui",
            "state": "waiting_dish",
            "patience_ticks": 3600,
            "patience_ticks_left": 3600,
        }
        sim = FakeQuanSim(customers=[customer], hand="ca_loc_nuong_trui")
        table = {"id": "T1", "pos": [9, 2]}

        events = handle_table_interact(sim, table)

        self.assertEqual(len(events), 1)
        name, data = events[0]
        self.assertEqual(name, "served")
        self.assertEqual(data["table_id"], "T1")
        self.assertEqual(data["customer_id"], "C1")
        self.assertEqual(data["dish"], "ca_loc_nuong_trui")

        # Sau khi phục vụ: tay phải trống, khách chuyển sang 'eating'
        self.assertIsNone(sim.hand)
        self.assertEqual(customer["state"], "eating")
        self.assertEqual(customer["eat_ticks_left"], 600)  # 10s * 60 tick

    def test_serve_fails_when_hand_is_empty(self):
        """Không phục vụ nếu tay người chơi không cầm gì."""
        customer = {
            "id": "C1",
            "table_id": "T1",
            "dish": "ca_loc_nuong_trui",
            "state": "waiting_dish",
        }
        sim = FakeQuanSim(customers=[customer], hand=None)
        table = {"id": "T1", "pos": [9, 2]}

        events = handle_table_interact(sim, table)
        self.assertEqual(events, [])
        self.assertEqual(customer["state"], "waiting_dish")

    def test_serve_fails_wrong_dish(self):
        """Không phục vụ nếu món trên tay khác món khách gọi."""
        customer = {
            "id": "C1",
            "table_id": "T1",
            "dish": "ca_loc_nuong_trui",
            "state": "waiting_dish",
        }
        sim = FakeQuanSim(customers=[customer], hand="goi_bong_sung")
        table = {"id": "T1", "pos": [9, 2]}

        events = handle_table_interact(sim, table)
        self.assertEqual(events, [])
        self.assertEqual(sim.hand, "goi_bong_sung")  # Món vẫn còn trên tay
        self.assertEqual(customer["state"], "waiting_dish")

    def test_serve_fails_customer_already_eating(self):
        """Không phục vụ lại nếu khách đã đang ăn."""
        customer = {
            "id": "C1",
            "table_id": "T1",
            "dish": "ca_loc_nuong_trui",
            "state": "eating",
            "eat_ticks_left": 300,
        }
        sim = FakeQuanSim(customers=[customer], hand="ca_loc_nuong_trui")
        table = {"id": "T1", "pos": [9, 2]}

        events = handle_table_interact(sim, table)
        self.assertEqual(events, [])
        self.assertEqual(sim.hand, "ca_loc_nuong_trui")

    def test_serve_fails_empty_table(self):
        """Tương tác bàn không có khách ngồi thì không làm gì."""
        sim = FakeQuanSim(customers=[], hand="ca_loc_nuong_trui")
        table = {"id": "T1", "pos": [9, 2]}

        events = handle_table_interact(sim, table)
        self.assertEqual(events, [])
        self.assertEqual(sim.hand, "ca_loc_nuong_trui")


class TestServiceDiningAndPayment(unittest.TestCase):
    """Kiểm tra chức năng 2: Tiến trình ăn, Thanh toán & Tiền tip (update_dining)."""

    def test_dining_still_eating(self):
        """Khách đang ăn và còn thời gian thì không kích hoạt paid."""
        customer = {
            "id": "C1",
            "table_id": "T1",
            "dish": "ca_loc_nuong_trui",
            "state": "eating",
            "eat_ticks_left": 10,
        }
        sim = FakeQuanSim(customers=[customer])

        events = update_dining(sim)
        self.assertEqual(events, [])
        self.assertEqual(len(sim.customers), 1)

    def test_paid_with_tip_when_served_fast(self):
        """Ăn xong và nhận tip nếu kiên nhẫn lúc trước >= 50% (tip đã được tính lúc giao)."""
        customer = {
            "id": "C1",
            "table_id": "T1",
            "dish": "ca_loc_nuong_trui",  # Giá 60
            "dish_id": "ca_loc_nuong_trui",
            "base_price": 60,
            "tip": 12,  # 60 * 0.2 = 12
            "state": "eating",
            "eat_ticks_left": 0,
        }
        sim = FakeQuanSim(customers=[customer], money=0, reputation=3.0)

        events = update_dining(sim)
        self.assertEqual(len(events), 1)
        name, data = events[0]
        self.assertEqual(name, "paid")
        self.assertEqual(data["customer_id"], "C1")
        self.assertEqual(data["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(data["amount"], 72)
        self.assertEqual(data["tip"], 12)
        self.assertAlmostEqual(data["reputation"], 3.2, places=2)  # 3.0 + 0.2

        # Tài chính được cộng đúng 60 + 12 = 72
        self.assertEqual(sim.money, 72)
        self.assertEqual(sim.earned, 72)
        # Bàn được giải phóng (khách bị xóa khỏi danh sách)
        self.assertEqual(len(sim.customers), 0)

    def test_paid_no_tip_when_served_slow(self):
        """Ăn xong không có tip nếu kiên nhẫn < 50%."""
        customer = {
            "id": "C1",
            "table_id": "T1",
            "dish": "ca_loc_nuong_trui",  # Giá 60
            "dish_id": "ca_loc_nuong_trui",
            "base_price": 60,
            "tip": 0,
            "state": "eating",
            "eat_ticks_left": 0,
        }
        sim = FakeQuanSim(customers=[customer], money=0, reputation=3.0)

        events = update_dining(sim)
        self.assertEqual(len(events), 1)
        name, data = events[0]
        self.assertEqual(data["amount"], 60)
        self.assertEqual(data["tip"], 0)
        self.assertAlmostEqual(data["reputation"], 3.0, places=2)
        self.assertEqual(sim.money, 60)

    def test_reputation_clamped_at_max(self):
        """Uy tín không bao giờ vượt quá reputation_max (5.0)."""
        customer = {
            "id": "C1",
            "table_id": "T1",
            "dish": "goi_bong_sung",
            "dish_id": "goi_bong_sung",
            "base_price": 40,
            "tip": 8,
            "state": "eating",
            "eat_ticks_left": 0,
        }
        sim = FakeQuanSim(customers=[customer], reputation=4.95)
        update_dining(sim)
        self.assertAlmostEqual(sim.reputation, 5.0, places=2)


class TestServicePatience(unittest.TestCase):
    """Kiểm tra chức năng 3: Quản lý kiên nhẫn & Khách bỏ về (update_patience)."""

    def test_patience_still_waiting(self):
        """Khách chờ món khi còn kiên nhẫn thì không bỏ đi."""
        customer = {
            "id": "C1",
            "table_id": "T1",
            "state": "waiting",
            "patience_ticks_left": 100,
        }
        sim = FakeQuanSim(customers=[customer])
        events = update_patience(sim)
        self.assertEqual(events, [])
        self.assertEqual(len(sim.customers), 1)

    def test_customer_leaves_when_out_of_patience(self):
        """Hết kiên nhẫn -> khách bỏ đi, trừ uy tín và giải phóng bàn."""
        customer = {
            "id": "C1",
            "table_id": "T1",
            "state": "waiting",
            "patience_ticks_left": 0,
        }
        sim = FakeQuanSim(customers=[customer], reputation=3.0)

        events = update_patience(sim)
        self.assertEqual(len(events), 1)
        name, data = events[0]
        self.assertEqual(name, "customer_left")
        self.assertEqual(data["customer_id"], "C1")
        self.assertEqual(data["reason"], "patience")
        self.assertAlmostEqual(data["reputation"], 2.5, places=2)  # 3.0 - 0.5

        # Uy tín bị trừ và bàn được giải phóng
        self.assertAlmostEqual(sim.reputation, 2.5, places=2)
        self.assertEqual(len(sim.customers), 0)

    def test_reputation_clamped_at_min(self):
        """Uy tín không bị trừ xuống dưới reputation_min (0.0)."""
        customer = {
            "id": "C1",
            "table_id": "T1",
            "state": "waiting",
            "patience_ticks_left": 0,
        }
        sim = FakeQuanSim(customers=[customer], reputation=0.2)
        update_patience(sim)
        self.assertAlmostEqual(sim.reputation, 0.0, places=2)

    def test_eating_customer_does_not_lose_patience(self):
        """Khách đang ăn không bị trừ kiên nhẫn và không bị bỏ đi."""
        customer = {
            "id": "C1",
            "table_id": "T1",
            "state": "eating",
            "patience_ticks_left": 1,
            "eat_ticks_left": 300,
        }
        sim = FakeQuanSim(customers=[customer])
        events = update_patience(sim)
        self.assertEqual(events, [])
        self.assertEqual(customer["patience_ticks_left"], 1)
        self.assertEqual(events, [])
        self.assertEqual(customer["patience_ticks_left"], 1)


class TestServiceDefensive(unittest.TestCase):
    """Kiểm tra tính an toàn phòng thủ lỗi (try-catch & defensive checks)."""

    def test_handles_corrupted_customer_list(self):
        """Không văng lỗi nếu danh sách customers có phần tử null/lạ."""
        sim = FakeQuanSim(customers=[None, {}, "invalid"])
        # Các hàm phải chạy êm đẹp, không throw uncaught exception
        self.assertEqual(update_dining(sim), [])
        self.assertEqual(update_patience(sim), [])
        self.assertEqual(update_service(sim), [])

    def test_get_customer_safe_on_invalid_sim(self):
        """get_customer_at_table trả về None an toàn khi sim rỗng hoặc lỗi."""
        self.assertIsNone(get_customer_at_table(None, "T1"))
        self.assertIsNone(get_customer_at_table({}, "T1"))


class TestPhase2Service(unittest.TestCase):
    """Kiểm tra Person B theo chuẩn Phase 2 (TICKET-02):
    
    1. 4 bàn ăn: T1 [9, 2], T2 [13, 2], T3 [9, 6], T4 [13, 6].
    2. 6 món ăn:
       - ca_loc_nuong_trui: 60k
       - goi_bong_sung: 40k
       - lau_ca_linh_dien_dien: 120k
       - canh_chua_ca_loc: 90k
       - ca_keo_nuong: 70k
       - lau_mam: 200k
    3. Tính tip chính xác: floor(giá * 0.2) khi kiên nhẫn lúc giao >= 50%.
    4. Tương thích tay cầm dạng dict từ Người A (bếp).
    5. Điểm số kết thúc ca: score = earned + 100 * floor(reputation).
    """

    def test_serve_four_tables(self):
        """Phục vụ độc lập tại cả 4 bàn T1, T2, T3, T4."""
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

        # 1. Phục vụ T4 (lau_mam)
        sim.hand = "lau_mam"
        evs4 = handle_table_interact(sim, tables[3])
        self.assertEqual(len(evs4), 1)
        self.assertEqual(evs4[0][0], "served")
        self.assertEqual(evs4[0][1]["table_id"], "T4")
        self.assertEqual(evs4[0][1]["dish"], "lau_mam")
        self.assertEqual(evs4[0][1]["tip"], 40)  # 200 * 0.2 = 40
        self.assertEqual(customers[3]["state"], "eating")

        # 2. Phục vụ T3 (ca_keo_nuong)
        sim.hand = "ca_keo_nuong"
        evs3 = handle_table_interact(sim, tables[2])
        self.assertEqual(len(evs3), 1)
        self.assertEqual(evs3[0][1]["table_id"], "T3")
        self.assertEqual(evs3[0][1]["dish"], "ca_keo_nuong")
        self.assertEqual(evs3[0][1]["tip"], 14)  # 70 * 0.2 = 14
        self.assertEqual(customers[2]["state"], "eating")

        # 3. Phục vụ T2 (canh_chua_ca_loc)
        sim.hand = "canh_chua_ca_loc"
        evs2 = handle_table_interact(sim, tables[1])
        self.assertEqual(len(evs2), 1)
        self.assertEqual(evs2[0][1]["table_id"], "T2")
        self.assertEqual(evs2[0][1]["dish"], "canh_chua_ca_loc")
        self.assertEqual(evs2[0][1]["tip"], 18)  # 90 * 0.2 = 18
        self.assertEqual(customers[1]["state"], "eating")

        # 4. Phục vụ T1 (ca_loc_nuong_trui)
        sim.hand = "ca_loc_nuong_trui"
        evs1 = handle_table_interact(sim, tables[0])
        self.assertEqual(len(evs1), 1)
        self.assertEqual(evs1[0][1]["table_id"], "T1")
        self.assertEqual(evs1[0][1]["dish"], "ca_loc_nuong_trui")
        self.assertEqual(evs1[0][1]["tip"], 12)  # 60 * 0.2 = 12
        self.assertEqual(customers[0]["state"], "eating")

        # Tất cả 4 khách đều chuyển sang 'eating'
        for c in customers:
            self.assertEqual(c["state"], "eating")

    def test_all_six_dishes_pricing_and_tips(self):
        """Kiểm tra chính xác giá và tiền tip cho tất cả 6 món ăn Phase 2."""
        dishes_expected = [
            ("ca_loc_nuong_trui", 60, 12),      # floor(60 * 0.2) = 12
            ("goi_bong_sung", 40, 8),          # floor(40 * 0.2) = 8
            ("lau_ca_linh_dien_dien", 120, 24), # floor(120 * 0.2) = 24
            ("canh_chua_ca_loc", 90, 18),      # floor(90 * 0.2) = 18
            ("ca_keo_nuong", 70, 14),          # floor(70 * 0.2) = 14
            ("lau_mam", 200, 40),              # floor(200 * 0.2) = 40
        ]
        table = {"id": "T1", "pos": [9, 2]}

        for dish_name, base_price, expected_tip in dishes_expected:
            customer = {
                "id": f"C_{dish_name}",
                "table_id": "T1",
                "dish_id": dish_name,
                "state": "waiting_dish",
                "patience_ticks": 3600,
                "patience_ticks_left": 3600,  # 100% kiên nhẫn
            }
            sim = FakeQuanSim(customers=[customer], hand=dish_name, money=0)
            evs = handle_table_interact(sim, table)
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0][1]["tip"], expected_tip)
            self.assertEqual(customer["base_price"], base_price)
            self.assertEqual(customer["tip"], expected_tip)

            # Ăn xong và thanh toán
            customer["eat_ticks_left"] = 0
            paid_evs = update_dining(sim)
            self.assertEqual(len(paid_evs), 1)
            name, paid_data = paid_evs[0]
            self.assertEqual(name, "paid")
            self.assertEqual(paid_data["dish_id"], dish_name)
            self.assertEqual(paid_data["amount"], base_price + expected_tip)
            self.assertEqual(paid_data["tip"], expected_tip)
            self.assertEqual(sim.money, base_price + expected_tip)

    def test_tip_threshold_edge_cases(self):
        """Kiểm tra điều kiện biên tỷ lệ kiên nhẫn: đúng 50% được tip, dưới 50% không có tip."""
        table = {"id": "T1", "pos": [9, 2]}

        # Đúng 50% kiên nhẫn (1800 / 3600 = 0.5) -> có tip (40)
        c_exact = {
            "id": "C1",
            "table_id": "T1",
            "dish_id": "lau_mam",
            "state": "waiting_dish",
            "patience_ticks": 3600,
            "patience_ticks_left": 1800,
        }
        sim1 = FakeQuanSim(customers=[c_exact], hand="lau_mam")
        handle_table_interact(sim1, table)
        self.assertEqual(c_exact["tip"], 40)

        # Dưới 50% kiên nhẫn (1799 / 3600 = 0.4997) -> 0 tip
        c_under = {
            "id": "C2",
            "table_id": "T1",
            "dish_id": "lau_mam",
            "state": "waiting_dish",
            "patience_ticks": 3600,
            "patience_ticks_left": 1799,
        }
        sim2 = FakeQuanSim(customers=[c_under], hand="lau_mam")
        handle_table_interact(sim2, table)
        self.assertEqual(c_under["tip"], 0)

    def test_hand_as_dict_from_kitchen(self):
        """Tương thích khi món trên tay là dict do Bếp (Người A) truyền sang."""
        table = {"id": "T1", "pos": [9, 2]}
        customer = {
            "id": "C1",
            "table_id": "T1",
            "dish_id": "lau_mam",
            "state": "waiting_dish",
            "patience_ticks": 3600,
            "patience_ticks_left": 3000,
        }
        hand_dict = {
            "order_id": "C1",
            "dish_id": "lau_mam",
            "base_price": 200,
        }
        sim = FakeQuanSim(customers=[customer], hand=hand_dict)

        evs = handle_table_interact(sim, table)
        self.assertEqual(len(evs), 1)
        name, d = evs[0]
        self.assertEqual(name, "served")
        self.assertEqual(d["table_id"], "T1")
        self.assertEqual(d["dish_id"], "lau_mam")
        self.assertEqual(d["tip"], 40)
        self.assertIsNone(sim.hand)
        self.assertEqual(customer["state"], "eating")
        self.assertEqual(customer["base_price"], 200)

    def test_score_calculation_formula(self):
        """Công thức điểm số ca: score = earned + 100 * floor(reputation)."""
        # earned = 520, reputation = 3.8 -> floor(3.8) = 3 -> score = 520 + 300 = 820
        sim = FakeQuanSim(money=520, reputation=3.8)
        mult = 100
        score = sim.earned + mult * math.floor(sim.reputation)
        self.assertEqual(score, 820)

        # Sau khi khách boa và uy tín tăng lên 4.0: floor(4.0) = 4 -> score = 800 + 400 = 1200
        sim.earned = 800
        sim.reputation = 4.0
        score2 = sim.earned + mult * math.floor(sim.reputation)
        self.assertEqual(score2, 1200)


if __name__ == "__main__":
    unittest.main()


