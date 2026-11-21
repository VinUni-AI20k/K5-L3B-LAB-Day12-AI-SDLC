"""Unit test cho sim/quan Lát 3b Phase 2 (Trần Trung Kiên - ttkien0710).

Kiểm thử toàn diện Lát 3b Phase 2:
- Hỗ trợ 2 bếp (B1, B2) nấu độc lập song song.
- Ưu tiên nhận đơn theo order_tick cũ nhất, nếu bằng nhau thì theo table_id nhỏ hơn.
- Ưu tiên khoảng cách gần nhất khi tương tác (Bếp trước Bàn, id nhỏ hơn).
- Tương thích menu 6 món và nguyên liệu của Phase 2.
- Cơ chế mở rộng burn: cháy món khi ready quá burn_s (1200 ticks) và dọn sạch bếp.
- Đóng ca dọn món: dọn sạch bếp và tay khi hết ca (quan_end).
"""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.runner import Session


class QuanLat3bPhase2Tests(unittest.TestCase):
    def setUp(self):
        base_tuning = load_contract()["tuning"]
        self.tuning = copy.deepcopy(base_tuning)
        # Bổ sung cấu hình 2 bếp và 4 bàn chuẩn Phase 2
        self.tuning["quan"]["stoves"] = [
            {"id": "B1", "pos": [2, 8]},
            {"id": "B2", "pos": [5, 8]},
        ]
        self.tuning["quan"]["tables"] = [
            {"id": "T1", "pos": [9, 2]},
            {"id": "T2", "pos": [13, 2]},
            {"id": "T3", "pos": [9, 6]},
            {"id": "T4", "pos": [13, 6]},
        ]
        # Bổ sung trọn bộ 6 món ăn Phase 2
        self.tuning["menu"] = {
            "ca_loc_nuong_trui": {"recipe": {"ca_loc": 1}, "cook_s": 6, "price": 60},
            "goi_bong_sung": {"recipe": {"bong_sung": 2}, "cook_s": 4, "price": 40},
            "lau_ca_linh_dien_dien": {"recipe": {"ca_linh": 3, "bong_dien_dien": 1}, "cook_s": 10, "price": 120},
            "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
            "ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
            "lau_mam": {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, "cook_s": 12, "price": 200},
        }

    def test_two_stoves_cooking_simultaneously(self):
        """2 bếp B1 và B2 có thể nấu song song độc lập và phát sự kiện dish_ready đúng thời điểm."""
        sc = {
            "stoves": [
                {"id": "B1", "pos": [2, 8], "state": "cooking", "dish": "ca_loc_nuong_trui", "cook_ticks_left": 2},
                {"id": "B2", "pos": [5, 8], "state": "cooking", "dish": "goi_bong_sung", "cook_ticks_left": 4},
            ]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        # Tick 1: B1: 2->1, B2: 4->3
        evs = s.step(li.advance())
        self.assertEqual(evs, [])
        self.assertEqual(s.sim.stoves[0]["state"], "cooking")
        self.assertEqual(s.sim.stoves[1]["state"], "cooking")

        # Tick 2: B1: 1->0 => B1 ready
        evs = s.step(li.advance())
        ready_b1 = [e for e in evs if e["name"] == "dish_ready" and e["data"]["stove_id"] == "B1"]
        self.assertEqual(len(ready_b1), 1)
        self.assertEqual(s.sim.stoves[0]["state"], "ready")
        self.assertEqual(s.sim.stoves[1]["state"], "cooking")
        self.assertEqual(s.sim.stoves[1]["cook_ticks_left"], 2)

        # Tick 3: B2: 2->1
        evs = s.step(li.advance())
        self.assertEqual(evs, [])

        # Tick 4: B2: 1->0 => B2 ready
        evs = s.step(li.advance())
        ready_b2 = [e for e in evs if e["name"] == "dish_ready" and e["data"]["stove_id"] == "B2"]
        self.assertEqual(len(ready_b2), 1)
        self.assertEqual(s.sim.stoves[1]["state"], "ready")

    def test_oldest_order_served_first(self):
        """Bếp trống tự động chọn đơn của khách có order_tick cũ nhất."""
        sc = {
            "player": {"pos": [2, 8]},  # đứng tại B1
            "stock": {"ca_loc": 2, "bong_sung": 4},
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order": "ca_loc_nuong_trui",
                 "order_tick": 120, "reserved": {"ca_loc": 1}},
                {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "order": "goi_bong_sung",
                 "order_tick": 60, "reserved": {"bong_sung": 2}},
            ]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        # Nhấn interact tại B1 -> Phải ưu tiên nấu cho C2 (order_tick 60 < 120)
        li.set(interact=True)
        evs = s.step(li.advance())
        cook_ev = [e for e in evs if e["name"] == "cook_started"]
        self.assertEqual(len(cook_ev), 1)
        self.assertEqual(cook_ev[0]["data"]["stove_id"], "B1")
        self.assertEqual(cook_ev[0]["data"]["customer_id"], "C2")
        self.assertEqual(cook_ev[0]["data"]["dish_id"], "goi_bong_sung")

        # Thả nút, di chuyển sang B2 [5, 8]
        li.set(interact=False)
        s.sim.pos = [5, 8]
        s.step(li.advance())

        # Nhấn interact tại B2 -> Nấu tiếp cho C1 (đơn tiếp theo)
        li.set(interact=True)
        evs = s.step(li.advance())
        cook_ev2 = [e for e in evs if e["name"] == "cook_started"]
        self.assertEqual(len(cook_ev2), 1)
        self.assertEqual(cook_ev2[0]["data"]["stove_id"], "B2")
        self.assertEqual(cook_ev2[0]["data"]["customer_id"], "C1")
        self.assertEqual(cook_ev2[0]["data"]["dish_id"], "ca_loc_nuong_trui")

    def test_same_order_tick_prioritizes_lower_table_id(self):
        """Nếu order_tick bằng nhau, ưu tiên khách ở bàn có id nhỏ hơn (T1 < T2)."""
        sc = {
            "player": {"pos": [2, 8]},
            "stock": {"ca_loc": 2},
            "customers": [
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order": "ca_loc_nuong_trui",
                 "order_tick": 100, "reserved": {"ca_loc": 1}},
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order": "ca_loc_nuong_trui",
                 "order_tick": 100, "reserved": {"ca_loc": 1}},
            ]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        li.set(interact=True)
        evs = s.step(li.advance())
        cook_ev = [e for e in evs if e["name"] == "cook_started"]
        self.assertEqual(len(cook_ev), 1)
        self.assertEqual(cook_ev[0]["data"]["customer_id"], "C1")
        self.assertEqual(s.sim.customers[0]["state"], "ordered")

    def test_nearest_interaction_priority(self):
        """Tương tác ưu tiên đối tượng gần nhất; nếu khoảng cách bằng nhau ưu tiên Bếp trước Bàn."""
        sc = {
            "player": {"pos": [2, 8]},
            "stoves": [{"id": "B1", "pos": [2, 8], "state": "ready", "dish": "ca_loc_nuong_trui"}],
            "tables": [{"id": "T1", "pos": [2, 8]}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order": "ca_loc_nuong_trui"}]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        # Khi tay trống đứng cùng khoảng cách giữa B1 và T1, bấm E phải nhấc món từ bếp B1 trước
        li.set(interact=True)
        evs = s.step(li.advance())
        picked_ev = [e for e in evs if e["name"] == "dish_picked"]
        self.assertEqual(len(picked_ev), 1)
        self.assertEqual(s.sim.hand, "ca_loc_nuong_trui")

        # Sau khi cầm đĩa, bấm E tiếp tại bàn T1 -> phục vụ món
        li.set(interact=False)
        s.step(li.advance())
        li.set(interact=True)
        evs2 = s.step(li.advance())
        served_ev = [e for e in evs2 if e["name"] == "served"]
        self.assertEqual(len(served_ev), 1)
        self.assertIsNone(s.sim.hand)

    def test_six_dishes_cooking_and_serving(self):
        """Thực đơn 6 món (đặc biệt các món phức tạp như lau_mam) nấu và phục vụ thành công."""
        dish = "lau_mam"
        recipe = self.tuning["menu"][dish]["recipe"]
        sc = {
            "player": {"pos": [2, 8]},
            "stock": dict(recipe),
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish, "order": dish, "reserved": dict(recipe)}]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        # 1. Bắt đầu nấu
        li.set(interact=True)
        evs = s.step(li.advance())
        self.assertTrue(any(e["name"] == "cook_started" and e["data"]["dish_id"] == dish for e in evs))
        cook_ticks = int(round(self.tuning["menu"][dish]["cook_s"] * 60))
        self.assertEqual(s.sim.stoves[0]["cook_ticks_left"], cook_ticks)

        # 2. Tua qua thời gian nấu -> dish_ready
        s.sim.stoves[0]["cook_ticks_left"] = 1
        li.set(interact=False)
        evs = s.step(li.advance())
        self.assertTrue(any(e["name"] == "dish_ready" and e["data"]["dish_id"] == dish for e in evs))

        # 3. Nhấc món lên tay
        li.set(interact=True)
        evs = s.step(li.advance())
        self.assertEqual(s.sim.hand, dish)

        # 4. Di chuyển tới bàn T1 [9, 2] và phục vụ
        li.set(interact=False)
        s.sim.pos = [9, 2]
        s.step(li.advance())
        li.set(interact=True)
        evs = s.step(li.advance())
        self.assertTrue(any(e["name"] == "served" and e["data"]["dish_id"] == dish for e in evs))

    def test_burn_mechanic_and_discard(self):
        """Cơ chế mở rộng burn: khi bật burn_s = 20s, ready quá 1200 ticks chuyển sang burned."""
        self.tuning["quan"]["burn_s"] = 20
        sc = {
            "player": {"pos": [2, 8]},
            "stoves": [{"id": "B1", "pos": [2, 8], "state": "ready", "dish": "ca_loc_nuong_trui", "ready_ticks": 1200}]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        # Tick tiếp theo: ready_ticks = 1201 > 1200 -> dish_burned
        evs = s.step(li.advance())
        burned_ev = [e for e in evs if e["name"] == "dish_burned"]
        self.assertEqual(len(burned_ev), 1)
        self.assertEqual(burned_ev[0]["data"]["stove_id"], "B1")
        self.assertEqual(s.sim.stoves[0]["state"], "burned")

        # Bấm E dọn sạch bếp cháy
        li.set(interact=True)
        evs2 = s.step(li.advance())
        discard_ev = [e for e in evs2 if e["name"] == "dish_discarded"]
        self.assertEqual(len(discard_ev), 1)
        self.assertEqual(s.sim.stoves[0]["state"], "idle")
        self.assertIsNone(s.sim.stoves[0]["dish"])

    def test_shift_ends_cleans_stoves_and_hand(self):
        """Đóng ca dọn món: khi hết giờ ca, tự động dọn sạch các món trên bếp và trên tay."""
        sc = {
            "time_left_ticks": 1,
            "hand": "goi_bong_sung",
            "stoves": [
                {"id": "B1", "pos": [2, 8], "state": "cooking", "dish": "ca_loc_nuong_trui", "cook_ticks_left": 100},
                {"id": "B2", "pos": [5, 8], "state": "ready", "dish": "ca_keo_nuong", "ready_ticks": 50},
            ]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        evs = s.step(li.advance())
        self.assertTrue(any(e["name"] == "quan_end" for e in evs))
        self.assertTrue(s.sim.done)
        self.assertIsNone(s.sim.hand)
        for stove in s.sim.stoves:
            self.assertEqual(stove["state"], "idle")
            self.assertIsNone(stove["dish"])


if __name__ == "__main__":
    unittest.main()
