"""Unit and integration tests for Quán (sim/quan) — Lát 3 và 4 của PRD-0."""

import json
import os
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.quan import QuanSim

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def make_sim(scenario=None, inventory=None, seed=1):
    contract = load_contract()
    tuning = contract["tuning"]
    streams = Streams(seed)
    ids = IdAllocator()
    sc = dict(scenario or {})
    return QuanSim(tuning, sc, streams, ids, inventory=inventory)


def make_input(move=(0.0, 0.0), interact=False, catch=False):
    held = {"interact": interact, "catch": catch}
    edges = set()
    if interact:
        edges.add("interact")
    if catch:
        edges.add("catch")
    return InputState(move, held, edges)


class TestQuanBasics(unittest.TestCase):
    def test_quan_snapshot_structure(self):
        contract = load_contract()
        sim = make_sim(inventory={"ca_loc": 2, "bong_sung": 2})
        snap = sim.snapshot()
        self.assertIn("player", snap)
        self.assertIn("pos", snap["player"])
        self.assertIn("vel", snap["player"])
        self.assertEqual(snap["stock"], {"bong_sung": 2, "ca_loc": 2})
        self.assertIsNone(snap["hand"])
        self.assertEqual(len(snap["stoves"]), 1)
        self.assertEqual(snap["stoves"][0]["id"], "B1")
        self.assertEqual(snap["stoves"][0]["state"], "idle")
        self.assertEqual(len(snap["tables"]), 1)
        self.assertEqual(snap["tables"][0]["id"], "T1")
        self.assertIsNone(snap["tables"][0]["customer_id"])
        self.assertEqual(snap["customers"], [])

    def test_customer_arrival_and_reserved(self):
        """Khách đến lúc first_customer_tick (120), giữ chỗ nguyên liệu theo công thức."""
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
        self.assertEqual(c["state"], "waiting")
        self.assertEqual(c["order_status"], "reserved")
        self.assertEqual(c["reserved"], sim.menu[c["dish_id"]]["recipe"])

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

    def test_table_busy_skips_new_customer(self):
        """Bàn bận thì bỏ lượt khách mới."""
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
            inventory={"ca_loc": 5},
            seed=1,
        )
        inp = make_input()
        for _ in range(119):
            sim.step(inp)
        evs = sim.step(inp)
        # Bàn T1 đã bận: không có customer_arrived và cũng không có no_dish
        self.assertEqual([e[0] for e in evs if e[0] in ("customer_arrived", "no_dish")], [])
        self.assertEqual(len(sim.customers), 1)

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
        # Tick 1: patience_ticks_left giảm từ 2 xuống 1
        evs1 = sim.step(inp)
        self.assertEqual(evs1, [])
        self.assertEqual(len(sim.customers), 1)

        # Tick 2: patience_ticks_left giảm từ 1 xuống 0 -> khách rời
        evs2 = sim.step(inp)
        left_evs = [e for e in evs2 if e[0] == "customer_left"]
        self.assertEqual(len(left_evs), 1)
        name, data = left_evs[0]
        self.assertEqual(data["order_id"], "C1")
        self.assertEqual(data["table_id"], "T1")
        self.assertEqual(data["reason"], "patience")
        self.assertAlmostEqual(data["reputation"], 2.5)  # 3.0 - 0.5
        self.assertAlmostEqual(sim.reputation, 2.5)
        self.assertEqual(len(sim.customers), 0)


class TestQuanCookingAndService(unittest.TestCase):
    def test_full_service_cycle(self):
        """Chu trình đầy đủ: đặt đơn -> nhận bếp (cook_started) -> chín (dish_ready) -> bưng (dish_picked) -> phục vụ (served) -> trả tiền (paid)."""
        contract = load_contract()
        menu = contract["tuning"]["menu"]
        # Đặt người chơi tại vị trí bếp B1 [2, 8]
        sim = make_sim(
            scenario={
                "player": {"pos": [2.0, 8.0]},
                "customers": [
                    {
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                        "state": "waiting",
                        "patience_ticks_left": 3600,
                    }
                ],
                "random_customers": False,
            },
            inventory={"ca_loc": 2},
        )

        # 1. Nhấn E tại bếp B1 để bắt đầu nấu
        inp_e = make_input(interact=True)
        evs = sim.step(inp_e)
        cook_evs = [e for e in evs if e[0] == "cook_started"]
        self.assertEqual(len(cook_evs), 1)
        data = cook_evs[0][1]
        self.assertEqual(data["stove_id"], "B1")
        self.assertEqual(data["order_id"], "C1")
        self.assertEqual(data["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(data["items"], ["ca_loc"])
        self.assertEqual(data["base_price"], 60)

        # Kho vật lý giảm từ 2 xuống 1
        self.assertEqual(sim.stock["ca_loc"], 1)
        # Bếp đang nấu
        b1 = sim.stoves[0]
        self.assertEqual(b1["state"], "cooking")
        cook_ticks = int(round(menu["ca_loc_nuong_trui"]["cook_s"] * 60))
        self.assertEqual(b1["cook_ticks_left"], cook_ticks)

        # 2. Đợi món chín (cook_ticks ticks)
        inp_idle = make_input()
        ready_found = False
        for _ in range(cook_ticks):
            step_evs = sim.step(inp_idle)
            for name, d in step_evs:
                if name == "dish_ready":
                    ready_found = True
                    self.assertEqual(d["stove_id"], "B1")
                    self.assertEqual(d["order_id"], "C1")
                    self.assertEqual(d["dish_id"], "ca_loc_nuong_trui")
        self.assertTrue(ready_found)
        self.assertEqual(b1["state"], "ready")

        # 3. Nhấn E tại bếp B1 để bưng món lên tay
        evs_pick = sim.step(inp_e)
        pick_evs = [e for e in evs_pick if e[0] == "dish_picked"]
        self.assertEqual(len(pick_evs), 1)
        self.assertEqual(pick_evs[0][1]["stove_id"], "B1")
        self.assertEqual(pick_evs[0][1]["order_id"], "C1")
        self.assertIsNotNone(sim.hand)
        self.assertEqual(sim.hand["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(b1["state"], "idle")

        # 4. Người chơi di chuyển tới bàn T1 [9, 2]
        sim.pos = [9.0, 2.0]

        # 5. Nhấn E tại bàn T1 để phục vụ
        evs_serve = sim.step(inp_e)
        serve_evs = [e for e in evs_serve if e[0] == "served"]
        self.assertEqual(len(serve_evs), 1)
        s_data = serve_evs[0][1]
        self.assertEqual(s_data["order_id"], "C1")
        self.assertEqual(s_data["table_id"], "T1")
        self.assertEqual(s_data["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(s_data["base_price"], 60)
        self.assertEqual(s_data["tip"], 12)  # 60 * 0.2 = 12 vì kiên nhẫn còn > 50%
        self.assertIsNone(sim.hand)

        cust = sim.customers[0]
        self.assertEqual(cust["state"], "eating")
        self.assertEqual(cust["order_status"], "served")
        eat_ticks = int(round(sim.t["eat_s"] * 60))
        self.assertEqual(cust["eat_ticks_left"], eat_ticks)

        # 6. Đợi khách ăn xong và thanh toán
        paid_found = False
        for _ in range(eat_ticks):
            step_evs = sim.step(inp_idle)
            for name, d in step_evs:
                if name == "paid":
                    paid_found = True
                    self.assertEqual(d["order_id"], "C1")
                    self.assertEqual(d["table_id"], "T1")
                    self.assertEqual(d["base_price"], 60)
                    self.assertEqual(d["tip"], 12)
                    self.assertEqual(d["amount"], 72)
                    self.assertEqual(d["reason"], "finished_eating")
        self.assertTrue(paid_found)
        self.assertEqual(sim.money, 72)
        self.assertEqual(sim.earned, 72)
        self.assertEqual(sim.shift_earned, 72)
        self.assertAlmostEqual(sim.reputation, 3.2)  # 3.0 + 0.2
        self.assertEqual(len(sim.customers), 0)

    def test_serve_on_boundary_tick_succeeds(self):
        """Xét phục vụ trước bỏ đi: phục vụ đúng tick kiên nhẫn chạm 0 vẫn được chấp nhận."""
        sim = make_sim(
            scenario={
                "player": {"pos": [9.0, 2.0]},
                "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                "customers": [
                    {
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                        "state": "waiting",
                        "patience_ticks_left": 1,
                    }
                ],
                "random_customers": False,
            }
        )
        inp_e = make_input(interact=True)
        evs = sim.step(inp_e)
        serve_evs = [e for e in evs if e[0] == "served"]
        self.assertEqual(len(serve_evs), 1)
        self.assertEqual(serve_evs[0][1]["patience_ticks_left"], 0)
        # Không có customer_left vì đã được phục vụ
        self.assertFalse(any(e[0] == "customer_left" for e in evs))
        self.assertEqual(sim.customers[0]["state"], "eating")

    def test_closing_clears_customers_and_pays_eating(self):
        """Hết giờ: khách đang ăn trả tiền với reason closing, khách chờ rời quán với reason closing, phát quan_end."""
        sim = make_sim(
            scenario={
                "time_left_ticks": 1,
                "customers": [
                    {
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                        "state": "eating",
                        "base_price": 60,
                        "tip": 12,
                        "eat_ticks_left": 100,
                    }
                ],
                "random_customers": False,
            }
        )
        inp = make_input()
        evs = sim.step(inp)
        names = [e[0] for e in evs]
        self.assertIn("paid", names)
        self.assertIn("quan_end", names)
        paid_data = next(e[1] for e in evs if e[0] == "paid")
        self.assertEqual(paid_data["reason"], "closing")
        self.assertEqual(paid_data["amount"], 72)
        end_data = next(e[1] for e in evs if e[0] == "quan_end")
        self.assertEqual(end_data["reason"], "time")
        self.assertEqual(end_data["money"], 72)
        self.assertTrue(sim.done)


class TestQuanHeadlessIntegration(unittest.TestCase):
    def test_headless_quan_run_deterministic(self):
        """Chạy headless với quan xuất snapshot và event đầy đủ, tất định theo byte."""
        with Workdir() as w:
            for i in (1, 2):
                code, err = run_headless(
                    "--mode",
                    "quan",
                    "--seed",
                    "42",
                    "--ticks",
                    "150",
                    "--inventory",
                    "docs/contracts/inventory.sample.json",
                    "--out",
                    w.path(f"q{i}.jsonl"),
                )
                self.assertEqual(code, 0, err)
            with open(w.path("q1.jsonl"), "rb") as f1, open(w.path("q2.jsonl"), "rb") as f2:
                self.assertEqual(f1.read(), f2.read())

            rows = read_jsonl(w.path("q1.jsonl"))
            # Snapshot tick 0 có stock
            s0 = snapshots(rows)[0]
            self.assertEqual(s0["stock"], {"bong_sung": 2, "ca_loc": 1})
            # Có event customer_arrived tại tick 120
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1)
            self.assertEqual(arr[0]["tick"], 120)
            self.assertEqual(arr[0]["data"]["order_id"], "C1")


if __name__ == "__main__":
    unittest.main()
