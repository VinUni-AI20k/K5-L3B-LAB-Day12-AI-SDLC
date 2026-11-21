"""Unit tests cho sim/quan Phase 2 (Lát 3 & Lát 4 nâng cấp).

Kiểm tra:
1. Không gian quán mới: 2 bếp B1 [2,8], B2 [5,8] và 4 bàn T1 [9,2], T2 [13,2], T3 [9,6], T4 [13,6].
2. Thực đơn 6 món chuẩn: cá lóc nướng trui (60k), gỏi bông súng (40k), lẩu cá linh bông điên điển (120k),
   canh chua cá lóc (90k), cá kèo nướng (70k), lẩu mắm (200k).
3. Trong mode day, lọc món khách gọi bám sát theo Kế hoạch ngày (D1–D5) và tồn khả dụng.
4. Đón khách ở tick 120 + 900*k vào bàn trống có ID nhỏ nhất (T1 -> T2 -> T3 -> T4).
5. Bếp ưu tiên lấy đơn reserved cũ nhất theo order_tick rồi đến ID bàn.
"""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


class QuanPhase2Test(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()
        self.tuning = self.contract["tuning"]
        self.streams = Streams(42)
        self.ids = IdAllocator()

    def test_new_space_stoves_and_tables(self):
        """Kiểm tra không gian quán mới: 2 bếp B1, B2 và 4 bàn T1, T2, T3, T4."""
        sim = QuanSim(self.tuning, {}, self.streams, self.ids)
        stove_ids = [s["id"] for s in sim.stoves]
        self.assertEqual(stove_ids, ["B1", "B2"])
        self.assertEqual(sim.stoves[0]["pos"], [2, 8])
        self.assertEqual(sim.stoves[1]["pos"], [5, 8])

        table_ids = [t["id"] for t in sim.tables]
        self.assertEqual(table_ids, ["T1", "T2", "T3", "T4"])
        self.assertEqual(sim.tables[0]["pos"], [9, 2])
        self.assertEqual(sim.tables[1]["pos"], [13, 2])
        self.assertEqual(sim.tables[2]["pos"], [9, 6])
        self.assertEqual(sim.tables[3]["pos"], [13, 6])

    def test_menu_6_dishes_defined(self):
        """Kiểm tra thực đơn 6 món chuẩn trong game.contract.json."""
        menu = self.tuning["menu"]
        expected_dishes = {
            "ca_loc_nuong_trui": ({"ca_loc": 1}, 6, 60),
            "goi_bong_sung": ({"bong_sung": 2}, 4, 40),
            "lau_ca_linh_dien_dien": ({"ca_linh": 3, "bong_dien_dien": 1}, 10, 120),
            "canh_chua_ca_loc": ({"ca_loc": 1, "bong_dien_dien": 1}, 8, 90),
            "ca_keo_nuong": ({"ca_keo": 2}, 6, 70),
            "lau_mam": ({"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, 12, 200),
        }
        for dish_id, (recipe, cook_s, price) in expected_dishes.items():
            self.assertIn(dish_id, menu, f"Thiếu món {dish_id}")
            self.assertEqual(menu[dish_id]["recipe"], recipe)
            self.assertEqual(menu[dish_id]["cook_s"], cook_s)
            self.assertEqual(menu[dish_id]["price"], price)

    def test_mode_day_plan_filtering_d1_to_d5(self):
        """Trong mode day, món khách gọi bám sát theo Kế hoạch ngày (D1–D5) và tồn khả dụng."""
        # Kho có dồi dào tất cả nguyên liệu
        full_stock = {
            "ca_loc": 50,
            "ca_linh": 50,
            "ca_keo": 50,
            "bong_dien_dien": 50,
            "bong_sung": 50,
            "keo_neo": 50,
        }

        # Day 1: Kế hoạch chỉ có ca_loc_nuong_trui và goi_bong_sung
        sim_d1 = QuanSim(self.tuning, {"mode": "day", "day": 1, "stock": full_stock}, Streams(100), IdAllocator())
        inp = LiveInputs()
        for _ in range(120):
            sim_d1.step(inp.advance())
        self.assertEqual(len(sim_d1.customers), 1)
        self.assertIn(sim_d1.customers[0]["dish_id"], ["ca_loc_nuong_trui", "goi_bong_sung"])

        # Day 3: Kế hoạch có goi_bong_sung, canh_chua_ca_loc, ca_keo_nuong
        sim_d3 = QuanSim(self.tuning, {"mode": "day", "day": 3, "stock": full_stock}, Streams(103), IdAllocator())
        for _ in range(120):
            sim_d3.step(inp.advance())
        self.assertEqual(len(sim_d3.customers), 1)
        self.assertIn(sim_d3.customers[0]["dish_id"], ["goi_bong_sung", "canh_chua_ca_loc", "ca_keo_nuong"])

        # Day 4: Kế hoạch có lau_mam, ca_loc_nuong_trui, goi_bong_sung
        sim_d4 = QuanSim(self.tuning, {"mode": "day", "day": 4, "stock": full_stock}, Streams(104), IdAllocator())
        for _ in range(120):
            sim_d4.step(inp.advance())
        self.assertEqual(len(sim_d4.customers), 1)
        self.assertIn(sim_d4.customers[0]["dish_id"], ["lau_mam", "ca_loc_nuong_trui", "goi_bong_sung"])

    def test_customer_spawning_tables_order_t1_to_t4(self):
        """Khách đến ở tick 120 + 900*k lần lượt ngồi vào bàn trống có ID nhỏ nhất (T1 -> T2 -> T3 -> T4)."""
        stock = {"ca_loc": 10}
        sim = QuanSim(self.tuning, {"stock": stock}, self.streams, self.ids)
        inp = LiveInputs()

        # Khách 1: tick 120 -> T1
        for _ in range(120):
            sim.step(inp.advance())
        self.assertEqual(len(sim.customers), 1)
        self.assertEqual(sim.customers[0]["table_id"], "T1")

        # Khách 2: tick 120 + 900 = 1020 -> T2
        for _ in range(900):
            sim.step(inp.advance())
        self.assertEqual(len(sim.customers), 2)
        self.assertEqual(sim.customers[1]["table_id"], "T2")

        # Khách 3: tick 1020 + 900 = 1920 -> T3
        for _ in range(900):
            sim.step(inp.advance())
        self.assertEqual(len(sim.customers), 3)
        self.assertEqual(sim.customers[2]["table_id"], "T3")

        # Khách 4: tick 1920 + 900 = 2820 -> T4
        for _ in range(900):
            sim.step(inp.advance())
        self.assertEqual(len(sim.customers), 4)
        self.assertEqual(sim.customers[3]["table_id"], "T4")

    def test_stoves_order_priority_oldest_order_tick_then_table_id(self):
        """Bếp ưu tiên lấy đơn reserved cũ nhất theo order_tick, nếu bằng nhau thì theo ID bàn nhỏ hơn."""
        stock = {"ca_loc": 5}
        # Tình huống: B1 [2, 8] và B2 [5, 8] đều idle.
        # Khách C1 ở T2 (order_tick: 50), Khách C2 ở T1 (order_tick: 100).
        scenario = {
            "stock": stock,
            "player": {"pos": [2, 8]},  # Đang đứng tại bếp B1
            "customers": [
                {"id": "C1", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 50, "order_status": "reserved"},
                {"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 100, "order_status": "reserved"},
            ]
        }
        sim = QuanSim(self.tuning, scenario, self.streams, self.ids)
        inp = LiveInputs()

        # Tương tác tại bếp B1 -> B1 phải nhận đơn C1 trước (vì order_tick 50 < 100)
        inp.set(interact=True)
        events = sim.step(inp.advance())
        inp.set(interact=False)

        cook_ev = [e for e in events if e[0] == "cook_started"]
        self.assertEqual(len(cook_ev), 1)
        self.assertEqual(cook_ev[0][1]["stove_id"], "B1")
        self.assertEqual(cook_ev[0][1]["order_id"], "C1")

        # Di chuyển sang bếp B2 [5, 8]
        sim.pos = [5, 8]
        # Tương tác tại B2 -> B2 nhận đơn tiếp theo C2
        inp.set(interact=True)
        events2 = sim.step(inp.advance())
        inp.set(interact=False)

        cook_ev2 = [e for e in events2 if e[0] == "cook_started"]
        self.assertEqual(len(cook_ev2), 1)
        self.assertEqual(cook_ev2[0][1]["stove_id"], "B2")
        self.assertEqual(cook_ev2[0][1]["order_id"], "C2")

        # Hai bếp đang nấu đồng thời
        self.assertEqual(sim.stoves[0]["state"], "cooking")
        self.assertEqual(sim.stoves[1]["state"], "cooking")


if __name__ == "__main__":
    unittest.main()
