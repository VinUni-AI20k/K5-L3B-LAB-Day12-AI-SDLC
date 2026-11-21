"""Unit tests cho sim/quan (Lát 3 & Lát 4).

Kiểm tra:
- Lát 3: Đón khách theo lịch, chọn món, giữ chỗ nguyên liệu (reserved), no_dish, đếm ngược kiên nhẫn, bỏ về (customer_left).
- Lát 4: Tương tác bếp (cook_started, dish_ready, dish_picked), giao món (served), boa và uy tín, ăn xong trả tiền (paid), kết thúc ca (quan_end).
"""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


class QuanSimTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.streams = Streams(42)
        self.ids = IdAllocator()

    def test_customer_arrival_and_reserved(self):
        """Khách đến ở tick 120, chọn món nấu được và giữ chỗ nguyên liệu."""
        stock = {"ca_loc": 2}
        sim = QuanSim(self.tuning, {"stock": stock}, self.streams, self.ids)
        inp = LiveInputs()

        events = []
        for _ in range(120):
            events.extend(sim.step(inp.advance()))

        # Khách C1 đến ở tick 120
        arrived = [e for e in events if e[0] == "customer_arrived"]
        self.assertEqual(len(arrived), 1)
        self.assertEqual(arrived[0][1]["order_id"], "C1")
        self.assertEqual(arrived[0][1]["table_id"], "T1")
        self.assertEqual(arrived[0][1]["dish_id"], "ca_loc_nuong_trui")

        # Khách đang đợi, giữ chỗ 1 ca_loc
        self.assertEqual(len(sim.customers), 1)
        c = sim.customers[0]
        self.assertEqual(c["state"], "waiting")
        self.assertEqual(c["reserved"], {"ca_loc": 1})
        self.assertEqual(c["order_status"], "reserved")

    def test_no_dish_when_stock_empty(self):
        """Kho rỗng: đến tick 120 không đủ nguyên liệu -> phát sự kiện no_dish, không có khách."""
        sim = QuanSim(self.tuning, {"stock": {}}, self.streams, self.ids)
        inp = LiveInputs()

        events = []
        for _ in range(120):
            events.extend(sim.step(inp.advance()))

        no_dish = [e for e in events if e[0] == "no_dish"]
        self.assertEqual(len(no_dish), 1)
        self.assertEqual(len(sim.customers), 0)

    def test_customer_patience_and_left(self):
        """Khách đợi hết 60s kiên nhẫn mà không được phục vụ -> bỏ về, trừ 0.5 uy tín, nhả reserved."""
        stock = {"ca_loc": 1}
        sim = QuanSim(self.tuning, {"stock": stock}, self.streams, self.ids)
        inp = LiveInputs()

        # Chạy đến lúc khách vào (tick 120)
        for _ in range(120):
            sim.step(inp.advance())
        self.assertEqual(len(sim.customers), 1)

        # Chạy thêm 3600 tick (60s kiên nhẫn)
        events = []
        for _ in range(3600):
            events.extend(sim.step(inp.advance()))

        left = [e for e in events if e[0] == "customer_left"]
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0][1]["order_id"], "C1")
        self.assertEqual(left[0][1]["reason"], "patience")
        self.assertEqual(left[0][1]["reputation"], 2.5)  # 3.0 - 0.5
        self.assertEqual(sim.reputation, 2.5)

        # Do 3600 tick = 4 chu kỳ 15s (900 tick), đúng lúc C1 rời bàn T1 thì khách mới C2 đến lượt vào bàn
        arrived = [e for e in events if e[0] == "customer_arrived"]
        self.assertEqual(len(arrived), 1)
        self.assertEqual(arrived[0][1]["order_id"], "C2")
        self.assertEqual(sim.customers[0]["id"], "C2")

    def test_full_cooking_serving_and_payment_flow(self):
        """Luồng hoàn chỉnh: Nấu tại bếp B1 -> Bưng món -> Phục vụ tại bàn T1 -> Nhận tiền + Tip + Uy tín."""
        stock = {"ca_loc": 1}
        scenario = {
            "stock": stock,
            "player": {"pos": [2, 8]},  # Đứng ngay cạnh bếp B1 [2, 8]
        }
        sim = QuanSim(self.tuning, scenario, self.streams, self.ids)
        inp = LiveInputs()

        # 1. Chờ đến tick 120 cho khách C1 tới
        for _ in range(120):
            sim.step(inp.advance())
        self.assertEqual(len(sim.customers), 1)

        # 2. Bấm interact tại bếp B1 -> cook_started
        inp.set(interact=True)
        ev1 = sim.step(inp.advance())
        inp.set(interact=False)
        cook_ev = [e for e in ev1 if e[0] == "cook_started"]
        self.assertEqual(len(cook_ev), 1)
        self.assertEqual(cook_ev[0][1]["stove_id"], "B1")
        self.assertEqual(cook_ev[0][1]["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(sim.stock.get("ca_loc", 0), 0)  # Đã trừ kho thật

        # 3. Chờ 6s (360 tick) để món chín -> dish_ready
        events = []
        for _ in range(360):
            events.extend(sim.step(inp.advance()))
        ready_ev = [e for e in events if e[0] == "dish_ready"]
        self.assertEqual(len(ready_ev), 1)
        self.assertEqual(ready_ev[0][1]["stove_id"], "B1")

        # 4. Bấm interact tại bếp B1 để nhấc món lên tay -> dish_picked
        inp.set(interact=True)
        ev2 = sim.step(inp.advance())
        inp.set(interact=False)
        pick_ev = [e for e in ev2 if e[0] == "dish_picked"]
        self.assertEqual(len(pick_ev), 1)
        self.assertIsNotNone(sim.hand)
        self.assertEqual(sim.hand["dish_id"], "ca_loc_nuong_trui")

        # 5. Di chuyển đến bàn T1 [9, 2]
        sim.pos = [9, 2]

        # 6. Bấm interact tại bàn T1 -> served
        inp.set(interact=True)
        ev3 = sim.step(inp.advance())
        inp.set(interact=False)
        served_ev = [e for e in ev3 if e[0] == "served"]
        self.assertEqual(len(served_ev), 1)
        # Kiên nhẫn mới trôi qua ~365 / 3600 tick (>50%) -> có tip
        self.assertEqual(served_ev[0][1]["tip"], 12)  # 60 * 0.2 = 12
        self.assertIsNone(sim.hand)

        # 7. Khách ăn trong 10s (600 tick) -> paid
        events = []
        for _ in range(600):
            events.extend(sim.step(inp.advance()))
        paid_ev = [e for e in events if e[0] == "paid"]
        self.assertEqual(len(paid_ev), 1)
        self.assertEqual(paid_ev[0][1]["amount"], 72)  # 60 + 12
        self.assertEqual(sim.money, 72)
        self.assertEqual(sim.reputation, 3.2)  # 3.0 + 0.2
        self.assertEqual(len(sim.customers), 0)

    def test_closing_ca_end(self):
        """Hết giờ ca tối (180s = 10800 tick): khách đang ăn trả ngay, khách chờ rời, phát quan_end."""
        scenario = {
            "stock": {"ca_loc": 2},
            "time_left_ticks": 10,
            "customers": [{
                "id": "C1",
                "table_id": "T1",
                "dish_id": "ca_loc_nuong_trui",
                "state": "eating",
                "eat_ticks_left": 50,
                "base_price": 60,
                "tip": 12,
            }]
        }
        sim = QuanSim(self.tuning, scenario, self.streams, self.ids)
        inp = LiveInputs()

        events = []
        for _ in range(10):
            events.extend(sim.step(inp.advance()))

        self.assertTrue(sim.done)
        self.assertEqual(sim.reason, "time")

        # Khách đang ăn được thanh toán ngay với reason closing
        paid_ev = [e for e in events if e[0] == "paid"]
        self.assertEqual(len(paid_ev), 1)
        self.assertEqual(paid_ev[0][1]["reason"], "closing")
        self.assertEqual(paid_ev[0][1]["amount"], 72)

        # Kết thúc ca
        end_ev = [e for e in events if e[0] == "quan_end"]
        self.assertEqual(len(end_ev), 1)
        self.assertEqual(end_ev[0][1]["reason"], "time")
        self.assertEqual(end_ev[0][1]["money"], 72)


if __name__ == "__main__":
    unittest.main()
