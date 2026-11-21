"""Kiểm tra quản lý khách, giữ chỗ và kho cá thể Phase 3 (Contract v1.2 - Độ tươi):
1. Ngưỡng 30: stock fresh=30 -> sau 1 bước phát spoiled {item_id, kind, location:"stock"}; các bước sau không phát lại.
2. Nhiều cá thể cùng vượt ngưỡng phát theo thứ tự id (I2 trước I10).
3. Giữ lại khi ươn: khách nhả phần giữ và giữ cá thể tươi còn lại.
4. Giữ lại thất bại khi hết hàng tươi -> unfulfillable, khách vẫn chờ tới hết kiên nhẫn.
5. Khách mới chọn cá thể tươi nhất (hòa fresh thì id nhỏ thắng).
6. Hàng ươn không tính là khả dụng -> phát no_dish.
7. Khách rời bàn nhả id: cá thể vẫn trong stock và khách sau có thể giữ lại.
8. Scenario sai -> BadInput (id không có, id đã ươn, sai kind, trùng id, reserved không rỗng ở assigned/unfulfillable).
9. Tính tất định: cùng seed thì chuỗi event và snapshot 2 lần chạy giống hệt nhau.
10. Hai đơn cùng bị ươn: đơn có order_tick cũ hơn được ưu tiên giữ lại trước.
11. Chốt giá dùng fresh chính xác (Fraction): fresh 50 sau 1 tick hao còn 49.9958, base_price = floor(60 * 49.9958 / 100) = 29.
"""

import copy
import math
import unittest
from fractions import Fraction

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


def _inp(move=(0.0, 0.0), interact=False):
    edges = {"interact"} if interact else set()
    return InputState(move, set(edges), edges)


def _make_tuning():
    t = copy.deepcopy(load_contract()["tuning"])
    t["freshness"] = {
        "initial": 100,
        "gather_decay_per_s": 0.5,
        "quan_decay_per_s": 0.25,
        "spoiled_below": 30,
    }
    return t


class TestPhase3CustomersFresh(unittest.TestCase):
    def setUp(self):
        self.tuning = _make_tuning()

    def test_01_spoiled_boundary_emitted_once(self):
        """1. Ngưỡng 30: cá thể fresh=30 sau 1 bước phát spoiled và các bước sau không phát lại."""
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 30}]
        scen = {"random_customers": False, "stock": stock}
        sim = QuanSim(self.tuning, scen, Streams(42), IdAllocator())

        # Bước 1: fresh giảm từ 30 xuống 29.9958... -> phát spoiled
        evs1 = sim.step(_inp())
        spoiled1 = [e for e in evs1 if e[0] == "spoiled"]
        self.assertEqual(len(spoiled1), 1)
        self.assertEqual(spoiled1[0][1], {"item_id": "I1", "kind": "ca_loc", "location": "stock"})

        # Bước 2: fresh tiếp tục giảm nhưng đã < 30 từ trước -> không phát lại
        evs2 = sim.step(_inp())
        spoiled2 = [e for e in evs2 if e[0] == "spoiled"]
        self.assertEqual(len(spoiled2), 0)

    def test_02_multiple_spoiled_sorted_by_id(self):
        """2. Nhiều cá thể cùng vượt ngưỡng phát theo thứ tự id (I2 trước I10)."""
        stock = [
            {"id": "I10", "kind": "ca_loc", "fresh": 30},
            {"id": "I2", "kind": "ca_loc", "fresh": 30},
            {"id": "I1", "kind": "ca_linh", "fresh": 30},
        ]
        scen = {"random_customers": False, "stock": stock}
        sim = QuanSim(self.tuning, scen, Streams(42), IdAllocator())

        evs = sim.step(_inp())
        spoiled = [e for e in evs if e[0] == "spoiled"]
        self.assertEqual(len(spoiled), 3)
        spoiled_ids = [e[1]["item_id"] for e in spoiled]
        self.assertEqual(spoiled_ids, ["I1", "I2", "I10"])

    def test_03_re_reserve_when_item_spoiled(self):
        """3. Giữ lại khi ươn: stock I1 fresh 30, I2 fresh 50; sau bước 1 C1 nhả I1 và giữ I2."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 30},
            {"id": "I2", "kind": "ca_loc", "fresh": 50},
        ]
        customers = [{
            "id": "C1",
            "table_id": "T1",
            "dish_id": "ca_loc_nuong_trui",
            "order_tick": 0,
            "order_status": "reserved",
            "reserved": ["I1"],
        }]
        scen = {"random_customers": False, "stock": stock, "customers": customers}
        sim = QuanSim(self.tuning, scen, Streams(42), IdAllocator())

        evs = sim.step(_inp())
        spoiled = [e for e in evs if e[0] == "spoiled"]
        self.assertEqual(len(spoiled), 1)
        self.assertEqual(spoiled[0][1]["item_id"], "I1")

        c1 = sim.customers[0]
        self.assertEqual(c1["order_status"], "reserved")
        self.assertEqual(c1["reserved"], ["I2"])

    def test_04_re_reserve_fails_becomes_unfulfillable_and_waits(self):
        """4. Giữ lại thất bại khi hết hàng tươi -> unfulfillable, reserved=[], khách vẫn ngồi chờ."""
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 30}]
        customers = [{
            "id": "C1",
            "table_id": "T1",
            "dish_id": "ca_loc_nuong_trui",
            "order_tick": 0,
            "order_status": "reserved",
            "reserved": ["I1"],
        }]
        scen = {"random_customers": False, "stock": stock, "customers": customers}
        sim = QuanSim(self.tuning, scen, Streams(42), IdAllocator())

        evs = sim.step(_inp())
        left = [e for e in evs if e[0] == "customer_left"]
        self.assertEqual(len(left), 0, "Khách không được bỏ đi ngay khi đơn chuyển unfulfillable")

        c1 = sim.customers[0]
        self.assertEqual(c1["order_status"], "unfulfillable")
        self.assertEqual(c1["reserved"], [])
        self.assertEqual(c1["state"], "waiting")

    def test_05_new_customer_picks_freshest_items(self):
        """5. Khách mới chọn cá thể tươi nhất; hòa fresh thì id nhỏ hơn thắng."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 60},
            {"id": "I3", "kind": "ca_loc", "fresh": 90},
            {"id": "I2", "kind": "ca_loc", "fresh": 90},
        ]
        scen = {"random_customers": True, "stock": stock}
        sim = QuanSim(self.tuning, scen, Streams(42), IdAllocator(), dish_pool=["ca_loc_nuong_trui"])

        for _ in range(119):
            sim.step(_inp())
        evs120 = sim.step(_inp())

        arrived = [e for e in evs120 if e[0] == "customer_arrived"]
        self.assertEqual(len(arrived), 1)
        self.assertEqual(len(sim.customers), 1)
        # I2 và I3 cùng tươi 90 (sau 120 tick cùng còn ~89.5), nhưng I2 có id nhỏ hơn I3
        self.assertEqual(sim.customers[0]["reserved"], ["I2"])

    def test_06_spoiled_items_not_available_emits_no_dish(self):
        """6. Hàng ươn không tính là khả dụng -> phát no_dish ở tick 120."""
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 20}]
        scen = {"random_customers": True, "stock": stock}
        sim = QuanSim(self.tuning, scen, Streams(42), IdAllocator(), dish_pool=["ca_loc_nuong_trui"])

        for _ in range(119):
            sim.step(_inp())
        evs120 = sim.step(_inp())

        no_dish = [e for e in evs120 if e[0] == "no_dish"]
        arrived = [e for e in evs120 if e[0] == "customer_arrived"]
        self.assertEqual(len(no_dish), 1)
        self.assertEqual(len(arrived), 0)

    def test_07_customer_left_releases_reserved_ids_back_to_available(self):
        """7. Khách rời bàn (patience) nhả id cá thể: cá thể vẫn trong stock và khách sau giữ lại được."""
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 80}]
        # patience 5 tick để khách C1 hết kiên nhẫn sớm
        customers = [{
            "id": "C1",
            "table_id": "T1",
            "dish_id": "ca_loc_nuong_trui",
            "order_tick": 0,
            "order_status": "reserved",
            "reserved": ["I1"],
            "patience_ticks_left": 2,
        }]
        scen = {"random_customers": False, "stock": stock, "customers": customers}
        sim = QuanSim(self.tuning, scen, Streams(42), IdAllocator())

        # Tick 1: patience còn 1
        sim.step(_inp())
        # Tick 2: patience = 0 -> customer_left
        evs2 = sim.step(_inp())
        left = [e for e in evs2 if e[0] == "customer_left"]
        self.assertEqual(len(left), 1)
        self.assertEqual(len(sim.customers), 0)

        # Cá thể I1 vẫn còn trong kho
        stock_ids = [it["id"] for it in sim.stock]
        self.assertIn("I1", stock_ids)

        # Thêm khách mới C2, I1 đã được nhả nên C2 giữ được I1
        c2 = {
            "id": "C2",
            "table_id": "T1",
            "dish_id": "ca_loc_nuong_trui",
            "order_tick": 10,
            "order_status": "reserved",
            "reserved": None,
        }
        sim.customers.append(c2)
        from chonoi.sim.kitchen import _re_reserve_v12
        _re_reserve_v12(sim, c2, self.tuning["menu"]["ca_loc_nuong_trui"]["recipe"], sim.spoiled_below)
        self.assertEqual(c2["order_status"], "reserved")
        self.assertEqual(c2["reserved"], ["I1"])

    def test_08_invalid_scenario_raises_bad_input(self):
        """8. Scenario sai cú pháp / mâu thuẫn -> BadInput."""
        valid_stock = [{"id": "I1", "kind": "ca_loc", "fresh": 80}]

        # reserved trỏ id không có trong kho
        scen1 = {
            "stock": valid_stock,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I999"]}],
        }
        with self.assertRaises(BadInput):
            QuanSim(self.tuning, scen1, Streams(1), IdAllocator())

        # reserved trỏ id đã ươn (< 30)
        scen2 = {
            "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 25}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}],
        }
        with self.assertRaises(BadInput):
            QuanSim(self.tuning, scen2, Streams(1), IdAllocator())

        # reserved sai kind
        scen3 = {
            "stock": [{"id": "I1", "kind": "bong_sung", "fresh": 80}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}],
        }
        with self.assertRaises(BadInput):
            QuanSim(self.tuning, scen3, Streams(1), IdAllocator())

        # hai đơn dùng chung một id cá thể
        scen4 = {
            "stock": valid_stock,
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
            ],
        }
        with self.assertRaises(BadInput):
            QuanSim(self.tuning, scen4, Streams(1), IdAllocator())

        # đơn unfulfillable nhưng reserved không rỗng
        scen5 = {
            "stock": valid_stock,
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "order_status": "unfulfillable", "reserved": ["I1"]
            }],
        }
        with self.assertRaises(BadInput):
            QuanSim(self.tuning, scen5, Streams(1), IdAllocator())

    def test_09_determinism_identical_runs(self):
        """9. Tính tất định: cùng seed và cấu hình thì 2 lượt chạy ra chuỗi snapshot và event giống hệt."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 80},
            {"id": "I2", "kind": "ca_loc", "fresh": 75},
            {"id": "I3", "kind": "bong_sung", "fresh": 90},
            {"id": "I4", "kind": "bong_sung", "fresh": 85},
        ]
        scen = {"random_customers": True, "stock": stock}

        def _run_sim():
            sim = QuanSim(self.tuning, scen, Streams(99), IdAllocator())
            all_events = []
            snapshots = []
            for _ in range(130):
                all_events.extend(sim.step(_inp()))
            snapshots.append(sim.snapshot())
            return all_events, snapshots

        evs1, snaps1 = _run_sim()
        evs2, snaps2 = _run_sim()
        self.assertEqual(evs1, evs2)
        self.assertEqual(snaps1, snaps2)

    def test_10_multiple_orders_spoiled_handled_by_order_tick(self):
        """10. Hai đơn cùng bị ươn: đơn có order_tick cũ hơn được ưu tiên giữ cá thể tươi còn lại trước."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 30},
            {"id": "I2", "kind": "ca_loc", "fresh": 30},
            {"id": "I3", "kind": "ca_loc", "fresh": 80},
        ]
        customers = [
            {
                "id": "C1",
                "table_id": "T2",
                "dish_id": "ca_loc_nuong_trui",
                "order_tick": 0,
                "order_status": "reserved",
                "reserved": ["I1"],
            },
            {
                "id": "C2",
                "table_id": "T1",
                "dish_id": "ca_loc_nuong_trui",
                "order_tick": 10,
                "order_status": "reserved",
                "reserved": ["I2"],
            },
        ]
        scen = {"random_customers": False, "stock": stock, "customers": customers}
        sim = QuanSim(self.tuning, scen, Streams(42), IdAllocator())

        # Bước 1: cả I1 và I2 đều ươn (< 30)
        sim.step(_inp())

        c1 = next(c for c in sim.customers if c["id"] == "C1")
        c2 = next(c for c in sim.customers if c["id"] == "C2")

        # C1 (order_tick 0 < 10) được xử lý trước -> lấy I3 thành công
        self.assertEqual(c1["order_status"], "reserved")
        self.assertEqual(c1["reserved"], ["I3"])

        # C2 (order_tick 10) xử lý sau, không còn ca_loc tươi -> unfulfillable
        self.assertEqual(c2["order_status"], "unfulfillable")
        self.assertEqual(c2["reserved"], [])

    def test_11_fraction_exact_price_calculation_no_premature_rounding(self):
        """11. Chốt giá dùng fresh chính xác (Fraction): fresh 50 sau 1 tick hao còn 49.9958, base_price = floor(60 * 49.9958 / 100) = 29."""
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 50}]
        customers = [{
            "id": "C1",
            "table_id": "T1",
            "dish_id": "ca_loc_nuong_trui",
            "order_tick": 0,
            "order_status": "reserved",
            "reserved": ["I1"],
        }]
        scen = {
            "random_customers": False,
            "player": {"pos": [2, 8]},
            "stoves": [{"id": "B1", "pos": [2, 8], "state": "idle"}],
            "stock": stock,
            "customers": customers,
        }
        sim = QuanSim(self.tuning, scen, Streams(42), IdAllocator())

        # Bước 1: Người chơi bấm interact tại bếp B1 [2, 8]
        # Đầu tick 1: I1 hao từ 50 xuống 50 - 1/240 = 49.995833...
        # Giữa tick 1: Bếp nhận đơn, chốt base_price = floor(60 * (50 - 1/240) / 100) = 29
        evs = sim.step(_inp(interact=True))
        cook = [e for e in evs if e[0] == "cook_started"]
        self.assertEqual(len(cook), 1)
        self.assertEqual(cook[0][1]["stove_id"], "B1")
        self.assertEqual(cook[0][1]["order_id"], "C1")
        self.assertEqual(cook[0][1]["base_price"], 29)


if __name__ == "__main__":
    unittest.main()
