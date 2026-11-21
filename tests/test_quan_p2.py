"""Test Ticket 04 — Phase 2: Quán 2 bếp / 4 bàn / 6 món / Kế hoạch ngày."""

import unittest
from types import SimpleNamespace

from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
from chonoi.sim.quan_customers import affordable_dishes, free_table, spawn_due
from chonoi.sim.quan_service import (
    advance_stoves_and_eating,
    find_interact_target,
    handle_finished_eating,
    handle_interact,
)


class MockInput:
    def __init__(self, pressed_keys=None):
        self._pressed = set(pressed_keys or [])
        self.move = [0.0, 0.0]

    def pressed(self, key):
        return key in self._pressed


def create_p2_tuning():
    return {
        "tick_hz": 60,
        "score": {"reputation_multiplier": 100},
        "quan": {
            "duration_s": 180,
            "bounds": {"x": [0, 16], "z": [0, 10]},
            "start_pos": [8, 5],
            "walk_speed": 4.0,
            "ramp_max_ticks": 6,
            "interact_radius": 1.5,
            "stoves": [{"id": "B1", "pos": [2, 8]}, {"id": "B2", "pos": [5, 8]}],
            "tables": [
                {"id": "T1", "pos": [9, 2]},
                {"id": "T2", "pos": [13, 2]},
                {"id": "T3", "pos": [9, 6]},
                {"id": "T4", "pos": [13, 6]},
            ],
            "first_customer_tick": 120,
            "customer_interval_s": 15,
            "patience_s": 60,
            "eat_s": 10,
            "burn_s": None,
            "carry_limit": 1,
            "tip_rate": 0.2,
            "tip_min_patience_ratio": 0.5,
            "tip_reputation": 0.2,
            "left_reputation_delta": -0.5,
            "reputation_initial": 3.0,
            "reputation_min": 0,
            "reputation_max": 5,
        },
        "menu": {
            "ca_loc_nuong_trui": {"recipe": {"ca_loc": 1}, "cook_s": 6, "price": 60},
            "goi_bong_sung": {"recipe": {"bong_sung": 2}, "cook_s": 4, "price": 40},
            "lau_ca_linh_dien_dien": {"recipe": {"ca_linh": 3, "bong_dien_dien": 1}, "cook_s": 10, "price": 120},
            "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
            "ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
            "lau_mam": {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, "cook_s": 12, "price": 200},
        },
    }


class TestQuanP2(unittest.TestCase):
    def test_two_stoves_cook_parallel_without_collision(self):
        """Hai bếp B1, B2 nấu song song 2 đơn khác nhau mà không giẫm đơn nhau."""
        tuning = create_p2_tuning()
        scenario = {
            "stock": {"ca_loc": 1, "bong_sung": 2},
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting", "order_status": "reserved", "order_tick": 10},
                {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "state": "waiting", "order_status": "reserved", "order_tick": 20},
            ],
        }
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())

        # Người chơi tương tác với Bếp B1 (tại pos [2, 8])
        sim.pos = [2.0, 8.0]
        ev1 = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(len(ev1), 1)
        self.assertEqual(ev1[0][0], "cook_started")
        self.assertEqual(ev1[0][1]["stove_id"], "B1")
        self.assertEqual(ev1[0][1]["order_id"], "C1")
        self.assertEqual(sim.stoves[0]["state"], "cooking")
        self.assertEqual(sim.customers[0]["order_status"], "assigned")

        # Người chơi di chuyển sang Bếp B2 (tại pos [5, 8]) và tương tác
        sim.pos = [5.0, 8.0]
        ev2 = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(len(ev2), 1)
        self.assertEqual(ev2[0][0], "cook_started")
        self.assertEqual(ev2[0][1]["stove_id"], "B2")
        self.assertEqual(ev2[0][1]["order_id"], "C2")
        self.assertEqual(sim.stoves[1]["state"], "cooking")
        self.assertEqual(sim.customers[1]["order_status"], "assigned")

        # Cả hai bếp đang nấu đồng thời độc lập
        self.assertEqual(sim.stoves[0]["dish"], "ca_loc_nuong_trui")
        self.assertEqual(sim.stoves[1]["dish"], "goi_bong_sung")

    def test_four_tables_capacity(self):
        """4 bàn ăn T1-T4: khi kín 4 bàn thì free_table trả về None."""
        tuning = create_p2_tuning()
        scenario = {
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting"},
                {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "state": "waiting"},
                {"id": "C3", "table_id": "T3", "dish_id": "ca_loc_nuong_trui", "state": "waiting"},
            ],
        }
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())
        # Bàn T4 còn trống
        self.assertEqual(free_table(sim)["id"], "T4")

        # Thêm khách vào T4 -> Kín 4 bàn
        sim.customers.append({"id": "C4", "table_id": "T4", "dish_id": "goi_bong_sung", "state": "waiting", "reserved": {}})
        self.assertIsNone(free_table(sim))

    def test_six_dishes_and_new_ingredients(self):
        """Hỗ trợ cả 6 món với 2 nguyên liệu mới (ca_keo, keo_neo)."""
        tuning = create_p2_tuning()
        scenario = {
            "stock": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1},
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "lau_mam", "state": "waiting", "order_status": "reserved", "order_tick": 5},
            ],
        }
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())
        sim.pos = [2.0, 8.0]
        events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], "cook_started")
        data = events[0][1]
        self.assertEqual(data["dish_id"], "lau_mam")
        self.assertEqual(data["base_price"], 200)
        # Nguyên liệu sorted alphabet: bong_dien_dien, ca_keo, ca_linh (2), keo_neo
        self.assertEqual(data["items"], ["bong_dien_dien", "ca_keo", "ca_linh", "ca_linh", "keo_neo"])
        # Kho trừ sạch
        self.assertEqual(sim.stock, {})

    def test_day_plan_filtering(self):
        """Trong day mode: chỉ lọc trong các món của day_plan.dishes trước."""
        tuning = create_p2_tuning()
        # Kho đủ cả 6 món
        stock = {"ca_loc": 5, "bong_sung": 5, "ca_linh": 5, "bong_dien_dien": 5, "ca_keo": 5, "keo_neo": 5}
        scenario = {"stock": stock}
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())

        # 1. Chế độ quán độc lập (day_plan = None) -> Đủ cả 6 món
        dishes_standalone = affordable_dishes(sim)
        self.assertEqual(len(dishes_standalone), 6)

        # 2. Chế độ Day với Day 1: chỉ nấu ca_loc_nuong_trui và goi_bong_sung
        sim.day_plan = {
            "day": 1,
            "dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
            "ingredients": {"ca_loc": 3, "bong_sung": 6},
        }
        dishes_day = affordable_dishes(sim)
        self.assertEqual(dishes_day, ["ca_loc_nuong_trui", "goi_bong_sung"])

        # 3. Kế hoạch không phải là trần bán: dù kế hoạch là 3 suất, khách vẫn gọi được tiếp
        self.assertIn("ca_loc_nuong_trui", dishes_day)

    def test_no_dish_when_ingredients_insufficient(self):
        """Có bàn trống nhưng không món nào đủ nguyên liệu -> phát no_dish và không sinh khách."""
        tuning = create_p2_tuning()
        scenario = {"stock": {"bong_sung": 1}}  # gỏi bông súng cần 2, không món nào đủ
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())
        sim.phase_tick = 120  # đúng first_customer_tick

        events = []
        spawn_due(sim, events)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], ("no_dish", {}))
        self.assertEqual(len(sim.customers), 0)

    def test_random_customers_false(self):
        """random_customers: false không sinh khách."""
        tuning = create_p2_tuning()
        scenario = {"random_customers": False, "stock": {"ca_loc": 10}}
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())

        inp = MockInput()
        for _ in range(150):
            sim.step(inp)
        self.assertEqual(len(sim.customers), 0)


if __name__ == "__main__":
    unittest.main()
