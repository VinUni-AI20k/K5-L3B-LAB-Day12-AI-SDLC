"""Unit tests cho sim/quan Phase 3 — Bếp & Độ tươi (Lát 2).

Kiểm tra:
1. Quản lý kho quán cá thể:
   - Tiếp nhận s.stock dạng mảng cá thể {id, kind, fresh}.
   - Hao tươi kho quán: giảm 0.25 điểm/s (mỗi tick giảm 0.25/60, kẹp đáy 0, dừng khi pause).
   - Phát event spoiled {item_id, kind, location: "stock"} theo id khi fresh < 30.
2. Giữ chỗ & Nấu theo cá thể:
   - Chọn các cá thể khả dụng tươi nhất (fresh cao nhất, nếu bằng nhau thì theo id nhỏ).
   - Xử lý ươn khi đang giữ chỗ: Nếu cá thể đang giữ bị rơi xuống < 30, nhả toàn bộ phần giữ của đơn và thử giữ lại đúng 1 lần. Nếu thiếu thì chuyển unfulfillable.
   - Chốt giá món: base_price = floor(giá niêm yết * trung bình fresh của các cá thể nấu / 100). Tiền boa = floor(tiền món * 0.2) trên giá đã chốt.
   - Sự kiện cook_started: data.items là mảng cá thể sắp xếp theo kind rồi theo id.
"""

import math
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.sim.quan import FRESH_DECAY_PER_TICK, QuanSim


class QuanFreshnessTest(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()
        self.tuning = self.contract["tuning"]
        self.streams = Streams(42)
        self.ids = IdAllocator()

    def test_stock_individual_intake_and_snapshot(self):
        """Kho cá thể: tiếp nhận s.stock mảng cá thể {id, kind, fresh} và snapshot đúng chuẩn."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 85.5},
            {"id": "I2", "kind": "ca_linh", "fresh": 92.0},
        ]
        sim = QuanSim(self.tuning, {"stock": stock}, self.streams, self.ids)
        snap = sim.snapshot()
        self.assertIsInstance(snap["stock"], list)
        self.assertEqual(len(snap["stock"]), 2)
        self.assertEqual(snap["stock"][0]["id"], "I1")
        self.assertEqual(snap["stock"][0]["kind"], "ca_loc")
        self.assertAlmostEqual(snap["stock"][0]["fresh"], 85.5)

    def test_stock_freshness_decay_and_pause(self):
        """Hao tươi kho quán: giảm 0.25 điểm/s (0.25/60 mỗi tick), dừng khi pause."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 50.0},
        ]
        sim = QuanSim(self.tuning, {"stock": stock}, self.streams, self.ids)
        inp = LiveInputs()

        # Chạy 60 tick (1s) bình thường: 50.0 - 0.25 = 49.75
        for _ in range(60):
            sim.step(inp.advance())

        item1 = next(it for it in sim.stock if it["id"] == "I1")
        self.assertAlmostEqual(item1["fresh"], 49.75, places=5)

        # Pause hệ thống
        inp.set(pause=True)
        for _ in range(60):
            sim.step(inp.advance())
        # Độ tươi không thay đổi khi pause
        self.assertAlmostEqual(item1["fresh"], 49.75, places=5)

        # Unpause: độ tươi tiếp tục giảm
        inp.set(pause=False)
        for _ in range(60):
            sim.step(inp.advance())
        # 49.75 - 0.25 = 49.50
        self.assertAlmostEqual(item1["fresh"], 49.50, places=5)

    def test_spoiled_event_and_removal(self):
        """Phát event spoiled {item_id, kind, location: 'stock'} theo id khi fresh < 30 và xóa khỏi kho."""
        # 2 item: I1 fresh 30.002 (sau 1 tick sẽ < 30), I2 fresh 30.001
        stock = [
            {"id": "I2", "kind": "bong_dien_dien", "fresh": 30.001},
            {"id": "I1", "kind": "ca_loc", "fresh": 30.002},
            {"id": "I3", "kind": "ca_linh", "fresh": 90.0},
        ]
        sim = QuanSim(self.tuning, {"stock": stock}, self.streams, self.ids)
        inp = LiveInputs()

        # Step 1 tick -> I1 và I2 rơi xuống < 30
        events = sim.step(inp.advance())

        spoiled_evs = [e for e in events if e[0] == "spoiled"]
        self.assertEqual(len(spoiled_evs), 2)
        # Event phát theo thứ tự id: I1 trước I2
        self.assertEqual(spoiled_evs[0][1], {"item_id": "I1", "kind": "ca_loc", "location": "stock"})
        self.assertEqual(spoiled_evs[1][1], {"item_id": "I2", "kind": "bong_dien_dien", "location": "stock"})

        # Kho chỉ còn lại I3
        remaining_ids = [it["id"] for it in sim.stock]
        self.assertEqual(remaining_ids, ["I3"])

    def test_freshest_items_reservation(self):
        """Giữ chỗ: Chọn các cá thể khả dụng tươi nhất (fresh cao nhất, nếu bằng nhau thì theo id nhỏ)."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 80.0},
            {"id": "I2", "kind": "ca_loc", "fresh": 95.0},
            {"id": "I3", "kind": "ca_loc", "fresh": 95.0},
            {"id": "I4", "kind": "ca_loc", "fresh": 25.0},  # Đã < 30 ngay từ đầu, không chọn
        ]
        sim = QuanSim(self.tuning, {"stock": stock}, self.streams, self.ids)

        # Món ca_loc_nuong_trui cần 1 ca_loc
        reserved = sim._reserve_items_for_dish("ca_loc_nuong_trui")
        # I2 và I3 cùng có fresh cao nhất (95.0), I2 có id nhỏ hơn I3 -> chọn I2
        self.assertEqual(reserved, ["I2"])

        # Nếu I2 đã bị giữ bởi đơn khác
        reserved2 = sim._reserve_items_for_dish("ca_loc_nuong_trui", excluded_ids={"I2"})
        self.assertEqual(reserved2, ["I3"])

        # Nếu cả I2 và I3 bị giữ
        reserved3 = sim._reserve_items_for_dish("ca_loc_nuong_trui", excluded_ids={"I2", "I3"})
        self.assertEqual(reserved3, ["I1"])

        # Nếu cả I1, I2, I3 bị giữ -> chỉ còn I4 (fresh < 30) -> None
        reserved4 = sim._reserve_items_for_dish("ca_loc_nuong_trui", excluded_ids={"I1", "I2", "I3"})
        self.assertIsNone(reserved4)

    def test_spoiled_while_reserved_re_reserve_success(self):
        """Ươn khi đang giữ chỗ: nhả toàn bộ reservation và giữ lại thành công nếu kho còn cá thể tươi."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 30.001},  # Sắp ươn
            {"id": "I2", "kind": "ca_loc", "fresh": 85.0},    # Tươi tốt
        ]
        # Khách C1 đang giữ I1
        scenario = {
            "stock": stock,
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "state": "waiting",
                    "order_status": "reserved",
                    "reserved_ids": ["I1"],
                }
            ],
        }
        sim = QuanSim(self.tuning, scenario, self.streams, self.ids)
        inp = LiveInputs()

        # Step 1 tick -> I1 rơi xuống < 30 -> spoiled -> re-reserve sang I2
        events = sim.step(inp.advance())

        spoiled_evs = [e for e in events if e[0] == "spoiled"]
        self.assertEqual(len(spoiled_evs), 1)
        self.assertEqual(spoiled_evs[0][1]["item_id"], "I1")

        cust = sim.customers[0]
        self.assertEqual(cust["order_status"], "reserved")
        self.assertEqual(cust["reserved_ids"], ["I2"])

    def test_spoiled_while_reserved_unfulfillable(self):
        """Ươn khi đang giữ chỗ: kho hết cá thể thay thế -> chuyển sang unfulfillable."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 30.001},  # Duy nhất 1 con cá lóc và sắp ươn
        ]
        scenario = {
            "stock": stock,
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "state": "waiting",
                    "order_status": "reserved",
                    "reserved_ids": ["I1"],
                }
            ],
        }
        sim = QuanSim(self.tuning, scenario, self.streams, self.ids)
        inp = LiveInputs()

        events = sim.step(inp.advance())
        spoiled_evs = [e for e in events if e[0] == "spoiled"]
        self.assertEqual(len(spoiled_evs), 1)

        cust = sim.customers[0]
        self.assertEqual(cust["order_status"], "unfulfillable")
        self.assertEqual(cust["reserved_ids"], [])

        # Kiểm tra bếp idle không nhận đơn unfulfillable
        sim.pos = [2, 8]  # Đứng cạnh bếp B1
        inp.set(interact=True)
        ev_interact = sim.step(inp.advance())
        cook_ev = [e for e in ev_interact if e[0] == "cook_started"]
        self.assertEqual(len(cook_ev), 0)
        self.assertEqual(sim.stoves[0]["state"], "idle")

    def test_dynamic_pricing_and_cook_started_items(self):
        """Chốt giá món theo trung bình fresh; cook_started có data.items sắp xếp theo kind rồi id."""
        # Món lau_ca_linh_dien_dien cần: ca_linh: 3, bong_dien_dien: 1 (niêm yết 120k)
        stock = [
            {"id": "I4", "kind": "bong_dien_dien", "fresh": 70.0},
            {"id": "I1", "kind": "ca_linh", "fresh": 90.0},
            {"id": "I2", "kind": "ca_linh", "fresh": 85.0},
            {"id": "I3", "kind": "ca_linh", "fresh": 75.0},
        ]
        scenario = {
            "stock": stock,
            "player": {"pos": [2, 8]},
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "lau_ca_linh_dien_dien",
                    "state": "waiting",
                    "order_status": "reserved",
                    "reserved_ids": ["I1", "I2", "I3", "I4"],
                }
            ],
        }
        sim = QuanSim(self.tuning, scenario, self.streams, self.ids)
        inp = LiveInputs()

        # Bấm interact để bắt đầu nấu
        inp.set(interact=True)
        events = sim.step(inp.advance())
        inp.set(interact=False)

        cook_evs = [e for e in events if e[0] == "cook_started"]
        self.assertEqual(len(cook_evs), 1)
        data = cook_evs[0][1]

        # Trung bình fresh: (70.0 + 90.0 + 85.0 + 75.0) / 4 = 320 / 4 = 80.0 (trước tick hao nhẹ)
        # Tại tick interact, hao tươi 0.25/60 trước khi interact:
        # fresh_decay = 0.25 / 60 = 0.0041666667
        # avg_fresh = (320 - 4*0.0041666667) / 4 = 79.9958333
        # base_price = floor(120 * 79.9958333 / 100) = floor(95.995) = 95
        expected_base_price = math.floor(120 * ((320.0 - 4 * FRESH_DECAY_PER_TICK) / 4.0) / 100.0)
        self.assertEqual(data["base_price"], expected_base_price)

        # Kiểm tra mảng data.items sắp xếp theo kind rồi id:
        # kind 'bong_dien_dien' < 'ca_linh'
        # Trong ca_linh: I1, I2, I3
        items = data["items"]
        self.assertEqual(len(items), 4)
        self.assertEqual(items[0]["kind"], "bong_dien_dien")
        self.assertEqual(items[0]["id"], "I4")
        self.assertEqual(items[1]["kind"], "ca_linh")
        self.assertEqual(items[1]["id"], "I1")
        self.assertEqual(items[2]["kind"], "ca_linh")
        self.assertEqual(items[2]["id"], "I2")
        self.assertEqual(items[3]["kind"], "ca_linh")
        self.assertEqual(items[3]["id"], "I3")

    def test_tip_calculated_on_locked_base_price(self):
        """Tiền boa tính floor(base_price * 0.2) trên giá món đã chốt."""
        # 1 con cá lóc fresh 80.0, món ca_loc_nuong_trui niêm yết 60k
        # Sau 1 tick hao tươi: fresh ~ 79.9958
        # base_price = floor(60 * 79.9958 / 100) = floor(47.997) = 47k
        # tip = floor(47 * 0.2) = floor(9.4) = 9k
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 80.0},
        ]
        scenario = {
            "stock": stock,
            "player": {"pos": [2, 8]},
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "state": "waiting",
                    "patience_ticks_left": 3600,
                    "order_status": "reserved",
                    "reserved_ids": ["I1"],
                }
            ],
        }
        sim = QuanSim(self.tuning, scenario, self.streams, self.ids)
        inp = LiveInputs()

        # 1. Bắt đầu nấu
        inp.set(interact=True)
        sim.step(inp.advance())
        inp.set(interact=False)

        expected_base_price = math.floor(60 * (80.0 - FRESH_DECAY_PER_TICK) / 100.0)
        self.assertEqual(sim.stoves[0]["base_price"], expected_base_price)

        # 2. Đợi nấu xong 6s (360 tick)
        for _ in range(360):
            sim.step(inp.advance())
        self.assertEqual(sim.stoves[0]["state"], "ready")

        # 3. Nhấc món lên tay
        inp.set(interact=True)
        sim.step(inp.advance())
        inp.set(interact=False)
        self.assertEqual(sim.hand["base_price"], expected_base_price)

        # 4. Đến bàn T1 [9, 2] và giao món
        sim.pos = [9, 2]
        inp.set(interact=True)
        events = sim.step(inp.advance())
        inp.set(interact=False)

        served_evs = [e for e in events if e[0] == "served"]
        self.assertEqual(len(served_evs), 1)
        expected_tip = math.floor(expected_base_price * 0.2)
        self.assertEqual(served_evs[0][1]["base_price"], expected_base_price)
        self.assertEqual(served_evs[0][1]["tip"], expected_tip)

        # 5. Khách ăn xong và thanh toán
        for _ in range(600):  # 10s ăn
            events = sim.step(inp.advance())
            paid_evs = [e for e in events if e[0] == "paid"]
            if paid_evs:
                self.assertEqual(paid_evs[0][1]["base_price"], expected_base_price)
                self.assertEqual(paid_evs[0][1]["tip"], expected_tip)
                self.assertEqual(paid_evs[0][1]["amount"], expected_base_price + expected_tip)
                break
        else:
            self.fail("Khách không thanh toán sau 10s ăn")


if __name__ == "__main__":
    unittest.main()
