"""Unit and integration tests for Quán (sim/quan) — Phase 2 (TICKET-02)."""

import json
import math
import os
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.quan import QuanSim

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def make_sim(scenario=None, inventory=None, seed=1, day_plan=None):
    contract = load_contract()
    tuning = contract["tuning"]
    streams = Streams(seed)
    ids = IdAllocator()
    sc = dict(scenario or {})
    return QuanSim(tuning, sc, streams, ids, inventory=inventory, day_plan=day_plan)


def make_input(move=(0.0, 0.0), interact=False, catch=False):
    held = {"interact": interact, "catch": catch}
    edges = set()
    if interact:
        edges.add("interact")
    if catch:
        edges.add("catch")
    return InputState(move, held, edges)


class TestQuanBasicsPhase2(unittest.TestCase):
    def test_quan_snapshot_structure_p2(self):
        """Phase 2: 2 bếp (B1, B2), 4 bàn (T1, T2, T3, T4)."""
        sim = make_sim(inventory={"ca_loc": 2, "bong_sung": 2})
        snap = sim.snapshot()
        self.assertIn("player", snap)
        self.assertIn("pos", snap["player"])
        self.assertIn("vel", snap["player"])
        self.assertEqual(snap["stock"], {"bong_sung": 2, "ca_loc": 2})
        self.assertIsNone(snap["hand"])
        self.assertEqual(len(snap["stoves"]), 2)
        self.assertEqual([s["id"] for s in snap["stoves"]], ["B1", "B2"])
        self.assertEqual(len(snap["tables"]), 4)
        self.assertEqual([t["id"] for t in snap["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertEqual(snap["customers"], [])

    def test_customer_arrival_and_reserved(self):
        """Khách đến lúc first_customer_tick (120), ghế trống ID nhỏ nhất (T1), giữ chỗ theo công thức."""
        sim = make_sim(inventory={"ca_loc": 5, "bong_sung": 5, "ca_linh": 5, "bong_dien_dien": 5}, seed=42)
        inp = make_input()

        # Chạy 119 tick: chưa có khách
        for _ in range(119):
            evs = sim.step(inp)
            self.assertEqual(evs, [])
            self.assertEqual(len(sim.customers), 0)

        # Tick 120: khách đầu tiên đến
        evs = sim.step(inp)
        arr_evs = [e for e in evs if e[0] == "customer_arrived"]
        self.assertEqual(len(arr_evs), 1)
        name, data = arr_evs[0]
        self.assertEqual(data["order_id"], "C1")
        self.assertEqual(data["table_id"], "T1")
        self.assertIn(data["dish_id"], sim.menu)

        # Kiểm tra customer và reserved
        self.assertEqual(len(sim.customers), 1)
        c = sim.customers[0]
        self.assertEqual(c["id"], "C1")
        self.assertEqual(c["table_id"], "T1")
        self.assertEqual(c["state"], "waiting")
        self.assertEqual(c["order_status"], "reserved")
        self.assertEqual(c["reserved"], sim.menu[c["dish_id"]]["recipe"])

    def test_seating_smallest_table_id(self):
        """Đến ghế trống ID nhỏ nhất: T1 đã có khách thì khách sau ngồi T2."""
        sim = make_sim(
            scenario={
                "customers": [
                    {
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                        "state": "waiting",
                        "patience_ticks_left": 1000,
                    }
                ]
            },
            inventory={"ca_loc": 5, "bong_sung": 5},
            seed=1,
        )
        inp = make_input()
        for _ in range(119):
            sim.step(inp)
        evs = sim.step(inp)
        arr_evs = [e for e in evs if e[0] == "customer_arrived"]
        self.assertEqual(len(arr_evs), 1)
        # Ghế trống tiếp theo có ID nhỏ nhất là T2
        self.assertEqual(arr_evs[0][1]["table_id"], "T2")

    def test_day_plan_filters_dishes(self):
        """Trong day mode, khách chỉ chọn món thuộc day_plan có đủ nguyên liệu."""
        d1_plan = {
            "day": 1,
            "dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
            "ingredients": {"ca_loc": 3, "bong_sung": 6},
        }
        # Kho có đủ cá kèo nhưng kế hoạch D1 không có món cá kèo
        sim = make_sim(
            inventory={"ca_loc": 5, "bong_sung": 5, "ca_keo": 10},
            seed=42,
            day_plan=d1_plan,
        )
        inp = make_input()
        for _ in range(120):
            evs = sim.step(inp)
        c = sim.customers[0]
        self.assertIn(c["dish_id"], ["ca_loc_nuong_trui", "goi_bong_sung"])

    def test_no_dish_when_out_of_stock(self):
        """Bàn trống nhưng kho không đủ nấu món nào -> phát no_dish {}."""
        sim = make_sim(inventory={}, seed=1)
        inp = make_input()
        for _ in range(119):
            sim.step(inp)
        evs = sim.step(inp)
        no_dish_evs = [e for e in evs if e[0] == "no_dish"]
        self.assertEqual(len(no_dish_evs), 1)
        self.assertEqual(no_dish_evs[0][1], {})
        self.assertEqual(len(sim.customers), 0)

    def test_table_busy_skips_when_all_4_occupied(self):
        """Cả 4 bàn đều bận: bỏ lượt khách mới."""
        sim = make_sim(
            scenario={
                "customers": [
                    {"id": f"C{i}", "table_id": f"T{i}", "dish_id": "ca_loc_nuong_trui", "state": "waiting"}
                    for i in range(1, 5)
                ]
            },
            inventory={"ca_loc": 10},
            seed=1,
        )
        inp = make_input()
        for _ in range(119):
            sim.step(inp)
        evs = sim.step(inp)
        self.assertEqual([e[0] for e in evs if e[0] in ("customer_arrived", "no_dish")], [])
        self.assertEqual(len(sim.customers), 4)

    def test_customer_impatient_leaves(self):
        """Khách hết kiên nhẫn: giảm uy tín 0.5, nhả reserved, phát customer_left reason patience."""
        sim = make_sim(
            scenario={
                "customers": [
                    {
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                        "state": "waiting",
                        "patience_ticks_left": 2,
                    }
                ],
                "random_customers": False,
            },
            inventory={"ca_loc": 1},
        )
        inp = make_input()
        evs1 = sim.step(inp)
        self.assertEqual(evs1, [])
        self.assertEqual(len(sim.customers), 1)

        evs2 = sim.step(inp)
        left_evs = [e for e in evs2 if e[0] == "customer_left"]
        self.assertEqual(len(left_evs), 1)
        data = left_evs[0][1]
        self.assertEqual(data["order_id"], "C1")
        self.assertEqual(data["table_id"], "T1")
        self.assertEqual(data["reason"], "patience")
        self.assertAlmostEqual(data["reputation"], 2.5)
        self.assertAlmostEqual(sim.reputation, 2.5)
        self.assertEqual(len(sim.customers), 0)


class TestQuanCookingAndServicePhase2(unittest.TestCase):
    def test_full_service_cycle_new_dishes(self):
        """Thử món mới Phase 2: cá kèo nướng (ca_keo_nuong) và lẩu mắm (lau_mam)."""
        contract = load_contract()
        menu = contract["tuning"]["menu"]
        self.assertIn("ca_keo_nuong", menu)
        self.assertIn("lau_mam", menu)

        # Nấu tại B2 [5, 8]
        sim = make_sim(
            scenario={
                "player": {"pos": [5.0, 8.0]},
                "customers": [
                    {
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_keo_nuong",
                        "state": "waiting",
                        "patience_ticks_left": 3600,
                    }
                ],
                "random_customers": False,
            },
            inventory={"ca_keo": 4},
        )

        inp_e = make_input(interact=True)
        evs = sim.step(inp_e)
        cook_evs = [e for e in evs if e[0] == "cook_started"]
        self.assertEqual(len(cook_evs), 1)
        self.assertEqual(cook_evs[0][1]["stove_id"], "B2")
        self.assertEqual(cook_evs[0][1]["dish_id"], "ca_keo_nuong")
        self.assertEqual(cook_evs[0][1]["base_price"], 70)
        self.assertEqual(sim.stock["ca_keo"], 2)  # Trừ 2 con cá kèo

        # Đợi chín (6s = 360 ticks)
        inp_idle = make_input()
        for _ in range(360):
            sim.step(inp_idle)
        b2 = next(s for s in sim.stoves if s["id"] == "B2")
        self.assertEqual(b2["state"], "ready")

        # Bưng món
        sim.step(inp_e)
        self.assertIsNotNone(sim.hand)
        self.assertEqual(sim.hand["dish_id"], "ca_keo_nuong")

        # Phục vụ tại bàn T1 [9, 2]
        sim.pos = [9.0, 2.0]
        evs_serve = sim.step(inp_e)
        s_data = next(e[1] for e in evs_serve if e[0] == "served")
        self.assertEqual(s_data["base_price"], 70)
        self.assertEqual(s_data["tip"], 14)  # floor(70 * 0.2) = 14

        # Khách ăn xong (10s = 600 ticks)
        for _ in range(600):
            step_evs = sim.step(inp_idle)
            if any(e[0] == "paid" for e in step_evs):
                paid_data = next(e[1] for e in step_evs if e[0] == "paid")
                self.assertEqual(paid_data["amount"], 84)  # 70 + 14
        self.assertEqual(sim.money, 84)
        self.assertAlmostEqual(sim.reputation, 3.2)

    def test_two_stoves_order_tick_and_table_priority(self):
        """Bếp lấy đơn reserved cũ nhất theo order_tick rồi id bàn."""
        sim = make_sim(
            scenario={
                "player": {"pos": [2.0, 8.0]},  # Gần B1 [2, 8]
                "customers": [
                    {
                        "id": "C2",
                        "table_id": "T2",
                        "dish_id": "goi_bong_sung",
                        "order_tick": 200,
                        "state": "waiting",
                    },
                    {
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                        "order_tick": 100,
                        "state": "waiting",
                    },
                ],
                "random_customers": False,
            },
            inventory={"ca_loc": 2, "bong_sung": 4},
        )
        inp_e = make_input(interact=True)
        evs = sim.step(inp_e)
        # B1 phải nhận C1 (order_tick 100 cũ hơn 200)
        cook_ev = next(e[1] for e in evs if e[0] == "cook_started")
        self.assertEqual(cook_ev["order_id"], "C1")
        self.assertEqual(cook_ev["dish_id"], "ca_loc_nuong_trui")

    def test_burn_extension_ready_ticks(self):
        """Mở rộng burn_s: món chín quá 1200 tick bị cháy, phát dish_burnt."""
        contract = load_contract()
        tuning = dict(contract["tuning"])
        tuning["quan"] = dict(tuning["quan"], burn_s=20)  # 20s = 1200 ticks
        streams = Streams(1)
        ids = IdAllocator()
        sim = QuanSim(
            tuning,
            {
                "stoves": [
                    {
                        "id": "B1",
                        "state": "ready",
                        "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                        "ready_ticks": 1200,
                    }
                ],
                "customers": [
                    {
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                        "state": "waiting",
                        "order_status": "assigned",
                    }
                ],
                "stock": {},  # Hết kho nên không thể reserved lại -> unfulfillable
                "random_customers": False,
            },
            streams,
            ids,
        )
        inp = make_input()
        # Ở tick tiếp theo, ready_ticks tăng thành 1201 > 1200 -> cháy
        evs = sim.step(inp)
        burnt_evs = [e for e in evs if e[0] == "dish_burnt"]
        self.assertEqual(len(burnt_evs), 1)
        data = burnt_evs[0][1]
        self.assertEqual(data["stove_id"], "B1")
        self.assertEqual(data["order_id"], "C1")
        self.assertEqual(data["order_status"], "unfulfillable")
        b1 = next(s for s in sim.stoves if s["id"] == "B1")
        self.assertEqual(b1["state"], "idle")
        self.assertIsNone(b1["dish"])

    def test_closing_clears_customers_and_stoves(self):
        """Hết giờ ca: đóng ca dọn dẹp món và phần giữ của đơn, thu tiền khách đang ăn, phát quan_end."""
        sim = make_sim(
            scenario={
                "time_left_ticks": 1,
                "stoves": [
                    {
                        "id": "B1",
                        "state": "cooking",
                        "dish": {"order_id": "C2", "dish_id": "goi_bong_sung", "base_price": 40},
                        "cook_ticks_left": 50,
                    }
                ],
                "customers": [
                    {
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                        "state": "eating",
                        "base_price": 60,
                        "tip": 12,
                        "eat_ticks_left": 100,
                    },
                    {
                        "id": "C2",
                        "table_id": "T2",
                        "dish_id": "goi_bong_sung",
                        "state": "waiting",
                        "patience_ticks_left": 500,
                    },
                ],
                "random_customers": False,
            }
        )
        inp = make_input()
        evs = sim.step(inp)
        names = [e[0] for e in evs]
        self.assertIn("paid", names)
        self.assertIn("customer_left", names)
        self.assertIn("quan_end", names)
        # Bếp được dọn rảnh
        self.assertTrue(all(s["state"] == "idle" for s in sim.stoves))
        self.assertTrue(sim.done)


class TestQuanHeadlessPhase2(unittest.TestCase):
    def test_headless_quan_run_phase2_preset(self):
        """Headless Quán với 2 bếp, 4 bàn và 6 món chạy thành công và xuất đủ trường snapshot."""
        with Workdir() as w:
            code, err = run_headless(
                "--mode",
                "quan",
                "--seed",
                "1",
                "--ticks",
                "150",
                "--inventory",
                "docs/contracts/inventory.sample.json",
                "--out",
                w.path("q.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("q.jsonl"))
            s0 = snapshots(rows)[0]
            self.assertEqual(len(s0["stoves"]), 2)
            self.assertEqual(len(s0["tables"]), 4)


if __name__ == "__main__":
    unittest.main()
