"""Unit và black-box tests cho Lát 3 (Nguyễn Minh Phương - minhphuong150505):
Hệ thống khách hàng, đặt món, giữ nguyên liệu và kiên nhẫn.
"""

import json
import os
import unittest

from helpers import (Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json)


class ScenarioValidation(unittest.TestCase):
    def test_quan_valid_customer_fixture(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 2},
                    "customers": [{
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                        "order_tick": 0,
                        "reserved": {"ca_loc": 1}
                    }]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)

    def test_quan_valid_customer_fixture_missing_reserved(self):
        """Khách fixture thiếu reserved nhưng hợp lệ và suy ra được."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 2},
                    "customers": [{
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                    }]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)

    def test_quan_customer_duplicate_table(self):
        """1. Hai khách cùng sử dụng một bàn -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 2},
                    "customers": [
                        {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"},
                        {"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
                    ]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_nonexistent_table(self):
        """2. Khách sử dụng bàn không tồn tại -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [
                        {"id": "C1", "table_id": "T99", "dish_id": "ca_loc_nuong_trui"}
                    ]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_nonexistent_dish(self):
        """3. Khách sử dụng món không tồn tại trong menu -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [
                        {"id": "C1", "table_id": "T1", "dish_id": "mon_khong_ton_tai"}
                    ]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_invalid_id(self):
        """4. Customer ID không hợp lệ hoặc trùng -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            # ID rỗng
            sc1 = write_json(w.path("sc1.json"), {
                "quan": {
                    "customers": [{"id": "", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc1, "--out", out)[0], 2)
            # Trùng ID
            sc2 = write_json(w.path("sc2.json"), {
                "quan": {
                    "tables": [{"id": "T1"}, {"id": "T2"}],  # T2 not in defaults
                    "customers": [
                        {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"},
                        {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
                    ]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc2, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_reserved_invalid_format(self):
        """5. reserved có số lượng âm, kiểu sai hoặc nguyên liệu không hợp lệ -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            # Số lượng âm
            sc1 = write_json(w.path("sc1.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "reserved": {"ca_loc": -1}}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc1, "--out", out)[0], 2)

            # Nguyên liệu lạ
            sc2 = write_json(w.path("sc2.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "reserved": {"nguyen_lieu_la": 1}}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc2, "--out", out)[0], 2)

            # Kiểu sai (boolean)
            sc3 = write_json(w.path("sc3.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "reserved": {"ca_loc": True}}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc3, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_reserved_recipe_mismatch(self):
        """6. Nguyên liệu giữ không phù hợp công thức -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            # ca_loc_nuong_trui cần {"ca_loc": 1}, nhưng giữ bong_sung
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"bong_sung": 2, "ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "reserved": {"bong_sung": 1}}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_reserved_exceeds_stock(self):
        """7. Tổng nguyên liệu giữ vượt quá kho thực tế trong scenario -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            # Cần 1 ca_loc nhưng kho chỉ có 0
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 0},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "reserved": {"ca_loc": 1}}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_order_status_contradiction(self):
        """8. Trạng thái đơn hàng mâu thuẫn với nguyên liệu giữ -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            # order_status là cooking mà vẫn có reserved
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "cooking", "reserved": {"ca_loc": 1}}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_stove_and_hand_share_order(self):
        """9. Bếp và tay cùng giữ một đơn -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {},
                    "stoves": [{"id": "B1", "state": "cooking", "dish": "ca_loc_nuong_trui", "order_id": "C1"}],
                    "hand": {"dish": "ca_loc_nuong_trui", "order_id": "C1"},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "cooking"}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_reference_nonexistent_customer(self):
        """10. Tham chiếu order/customer không tồn tại -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stoves": [{"id": "B1", "state": "cooking", "dish": "ca_loc_nuong_trui", "order_id": "C999"}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "cooking"}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))


class CustomerInitializationAndReservations(unittest.TestCase):
    def test_customer_data_model_and_snapshot(self):
        """Kiểm tra cấu trúc dữ liệu khách hàng theo hợp đồng trong snapshot."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 2},
                    "customers": [{
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                        "order_tick": 0,
                        "state": "waiting",
                        "patience_ticks_left": 3600,
                        "eat_ticks_left": 0,
                        "order_status": "reserved",
                        "reserved": {"ca_loc": 1},
                        "base_price": None,
                        "tip": 0
                    }]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            snap = snapshots(rows)[0]
            self.assertEqual(len(snap["customers"]), 1)
            c = snap["customers"][0]
            self.assertEqual(c["id"], "C1")
            self.assertEqual(c["table_id"], "T1")
            self.assertEqual(c["dish_id"], "ca_loc_nuong_trui")
            self.assertEqual(c["state"], "waiting")
            self.assertEqual(c["order_status"], "reserved")
            self.assertEqual(c["reserved"], {"ca_loc": 1})
            self.assertEqual(c["patience_ticks_left"], 3600)
            self.assertEqual(c["eat_ticks_left"], 0)
            self.assertIsNone(c["base_price"])
            self.assertEqual(c["tip"], 0)

    def test_infer_customer_reserved_when_missing(self):
        """Khách fixture thiếu reserved được suy ra đúng theo công thức món."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 2},
                    "customers": [{
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                    }]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            snap = snapshots(rows)[0]
            c = snap["customers"][0]
            self.assertEqual(c["reserved"], {"ca_loc": 1})

    def test_customer_fixture_with_inventory_flag(self):
        """Khởi tạo khách với kho nạp qua --inventory."""
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 2}})
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "customers": [{
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                    }]
                }
            })
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--inventory", inv, "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            snap = snapshots(rows)[0]
            self.assertEqual(snap["customers"][0]["reserved"], {"ca_loc": 1})

    def test_customer_fixture_with_insufficient_inventory_flag_exit_2(self):
        """Kho nạp qua --inventory không đủ nguyên liệu cho khách fixture -> mã 2."""
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 0}})
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "customers": [{
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                    }]
                }
            })
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--inventory", inv, "--scenario", sc, "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))


class CustomerArrivalSchedule(unittest.TestCase):
    def setUp(self):
        from chonoi.contract import load_contract
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.quan import QuanSim
        self.tuning = load_contract()["tuning"]
        self.sim = QuanSim(self.tuning, {}, Streams(1), IdAllocator())

    def test_t01_no_spawn_at_tick_119(self):
        """T01: Khách chưa đến ở tick 119."""
        self.sim.phase_tick = 119
        self.assertFalse(self.sim._should_spawn_customer())

    def test_t02_spawn_at_tick_120(self):
        """T02: Khách đầu tiên đến ở tick 120."""
        self.sim.phase_tick = 120
        self.assertTrue(self.sim._should_spawn_customer())

    def test_t03_next_spawn_interval(self):
        """T03: Lượt khách tiếp theo đúng khoảng thời gian (1020, 1920)."""
        self.sim.phase_tick = 121
        self.assertFalse(self.sim._should_spawn_customer())
        self.sim.phase_tick = 1019
        self.assertFalse(self.sim._should_spawn_customer())
        self.sim.phase_tick = 1020
        self.assertTrue(self.sim._should_spawn_customer())
        self.sim.phase_tick = 1919
        self.assertFalse(self.sim._should_spawn_customer())
        self.sim.phase_tick = 1920
        self.assertTrue(self.sim._should_spawn_customer())

    def test_t04_find_available_table_lowest_id(self):
        """T04: Bàn trống có ID nhỏ nhất được chọn."""
        # Mặc định chỉ có T1
        tb = self.sim._find_available_table()
        self.assertIsNotNone(tb)
        self.assertEqual(tb["id"], "T1")

        # Giả sử có thêm T2, T0
        self.sim.tables = [{"id": "T2"}, {"id": "T0"}, {"id": "T1"}]
        tb = self.sim._find_available_table()
        self.assertEqual(tb["id"], "T0")

    def test_t05_no_table_skips_turn(self):
        """T05: Không còn bàn thì bỏ lượt."""
        self.sim.customers.append({
            "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
            "order_status": "reserved", "reserved": {"ca_loc": 1}
        })
        self.assertIsNone(self.sim._find_available_table())

    def test_random_customers_false_disables_spawn(self):
        """random_customers: False tắt lịch khách đến."""
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.quan import QuanSim
        sim = QuanSim(self.tuning, {"random_customers": False}, Streams(1), IdAllocator())
        sim.phase_tick = 120
        self.assertFalse(sim._should_spawn_customer())


class DishSelectionAndReservation(unittest.TestCase):
    def test_t06_select_valid_dish_headless(self):
        """T06: Khách đến chọn món hợp lệ theo kho và phát customer_arrived."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {"stock": {"ca_loc": 1}}
            })
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "125",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            arrived_ev = events(rows, "customer_arrived")
            self.assertEqual(len(arrived_ev), 1)
            ev = arrived_ev[0]
            self.assertEqual(ev["tick"], 120)
            self.assertEqual(ev["data"]["customer_id"], "C1")
            self.assertEqual(ev["data"]["table_id"], "T1")
            self.assertEqual(ev["data"]["dish_id"], "ca_loc_nuong_trui")
            self.assertEqual(ev["data"]["reserved"], {"ca_loc": 1})

    def test_t07_no_dish_when_empty_stock(self):
        """T07: Không có món nào đủ nguyên liệu -> no_dish."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {"stock": {}}
            })
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "125",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            no_dish_ev = events(rows, "no_dish")
            self.assertEqual(len(no_dish_ev), 1)
            self.assertEqual(no_dish_ev[0]["tick"], 120)
            self.assertEqual(no_dish_ev[0]["data"], {})  # PRD-0 mục E
            # Không có khách nào được tạo
            self.assertEqual(len(events(rows, "customer_arrived")), 0)
            last_snap = snapshots(rows)[-1]
            self.assertEqual(len(last_snap["customers"]), 0)

    def test_t08_available_stock_and_no_over_reserve(self):
        """T08: Tính nguyên liệu khả dụng chính xác, không giữ vượt tồn."""
        from chonoi.contract import load_contract
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.quan import QuanSim
        tuning = load_contract()["tuning"]
        sim = QuanSim(tuning, {"stock": {"ca_loc": 1, "bong_sung": 2}}, Streams(1), IdAllocator())
        self.assertEqual(sim._available_stock(), {"ca_loc": 1, "bong_sung": 2})

        # C1 đến và giữ ca_loc: 1
        table = sim._find_available_table()
        evs = sim._spawn_customer(table)
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0][0], "customer_arrived")
        # ca_loc_nuong_trui hoặc goi_bong_sung có thể được chọn
        chosen_dish = sim.customers[0]["dish_id"]
        avail = sim._available_stock()
        if chosen_dish == "ca_loc_nuong_trui":
            self.assertEqual(avail["ca_loc"], 0)
            self.assertEqual(avail["bong_sung"], 2)
        else:
            self.assertEqual(avail["ca_loc"], 1)
            self.assertEqual(avail["bong_sung"], 0)

    def test_customer_dish_selection_deterministic(self):
        """Cùng seed tạo ra cùng món được chọn."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {"stock": {"ca_loc": 5, "ca_linh": 5, "bong_sung": 5, "bong_dien_dien": 5}}
            })
            for i in (1, 2):
                code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "125",
                                         "--scenario", sc, "--out", w.path(f"o{i}.jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("o1.jsonl"), "rb") as f1, open(w.path("o2.jsonl"), "rb") as f2:
                self.assertEqual(f1.read(), f2.read())


class CustomerPatienceAndLeft(unittest.TestCase):
    def test_t14_patience_not_reduced_on_arrival_tick(self):
        """T14: Kiên nhẫn không giảm ngay tại tick đến (120: 3600, 121: 3599)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {"stock": {"ca_loc": 1}}
            })
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "122",
                                     "--snapshot-every", "1", "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            snaps = {r["tick"]: r for r in snapshots(read_jsonl(out))}
            c_120 = snaps[120]["customers"][0]
            self.assertEqual(c_120["patience_ticks_left"], 3600)
            c_121 = snaps[121]["customers"][0]
            self.assertEqual(c_121["patience_ticks_left"], 3599)
            c_122 = snaps[122]["customers"][0]
            self.assertEqual(c_122["patience_ticks_left"], 3598)

    def test_t15_customer_left_when_patience_zero(self):
        """T15: Khách hết kiên nhẫn rời quán (customer_left, reason=patience)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "patience_ticks_left": 3, "reserved": {"ca_loc": 1}
                    }]
                }
            })
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5",
                                     "--snapshot-every", "1", "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            left_evs = events(rows, "customer_left")
            self.assertEqual(len(left_evs), 1)
            ev = left_evs[0]
            self.assertEqual(ev["tick"], 3)
            self.assertEqual(ev["data"]["customer_id"], "C1")
            self.assertEqual(ev["data"]["table_id"], "T1")
            self.assertEqual(ev["data"]["reason"], "patience")
            # Snapshot sau tick 3 không còn khách
            snaps = {r["tick"]: r for r in snapshots(rows)}
            self.assertEqual(len(snaps[3]["customers"]), 0)
            self.assertEqual(len(snaps[4]["customers"]), 0)

    def test_t16_customer_left_releases_reserved(self):
        """T16: Rời quán giải phóng reserved, kho khả dụng được phục hồi."""
        from chonoi.contract import load_contract
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.quan import QuanSim
        tuning = load_contract()["tuning"]
        sim = QuanSim(tuning, {
            "stock": {"ca_loc": 1},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "patience_ticks_left": 1, "reserved": {"ca_loc": 1}
            }]
        }, Streams(1), IdAllocator())

        self.assertEqual(sim._available_stock()["ca_loc"], 0)
        from chonoi.inputs import InputState
        dummy_input = InputState((0.0, 0.0), {}, set())
        evs = sim.step(dummy_input)
        self.assertEqual(len(sim.customers), 0)
        self.assertEqual(sim._available_stock()["ca_loc"], 1)

    def test_t17_customer_left_decreases_reputation(self):
        """T17: Khách rời quán do hết kiên nhẫn làm giảm đúng 0.5 uy tín."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "reputation": 3.0,
                    "stock": {"ca_loc": 1},
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "patience_ticks_left": 2, "reserved": {"ca_loc": 1}
                    }]
                }
            })
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "4",
                                     "--snapshot-every", "1", "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            snaps = {r["tick"]: r for r in snapshots(read_jsonl(out))}
            self.assertEqual(snaps[0]["reputation"], 3.0)
            self.assertEqual(snaps[2]["reputation"], 2.5)

    def test_t18_reputation_clamped_to_minimum(self):
        """T18: Uy tín được kẹp không thấp hơn reputation_min (0)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "reputation": 0.2,
                    "stock": {"ca_loc": 1},
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "patience_ticks_left": 1, "reserved": {"ca_loc": 1}
                    }]
                }
            })
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "2",
                                     "--snapshot-every", "1", "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            snaps = {r["tick"]: r for r in snapshots(read_jsonl(out))}
            self.assertEqual(snaps[1]["reputation"], 0.0)

    def test_eating_customer_not_expired_by_patience(self):
        """Khách đang ăn (eating) không bị trừ kiên nhẫn và không rời quán do patience."""
        from chonoi.contract import load_contract
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.quan import QuanSim
        from chonoi.inputs import InputState
        tuning = load_contract()["tuning"]
        sim = QuanSim(tuning, {
            "stock": {},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "state": "eating", "order_status": "served", "eat_ticks_left": 600,
                "patience_ticks_left": 100
            }]
        }, Streams(1), IdAllocator())

        dummy_input = InputState((0.0, 0.0), {}, set())
        for _ in range(5):
            sim.step(dummy_input)
        self.assertEqual(len(sim.customers), 1)
        self.assertEqual(sim.customers[0]["patience_ticks_left"], 100)
        self.assertEqual(sim.reputation, 3.0)


class EdgeCasesAndDeterminism(unittest.TestCase):
    def test_sample_inventory_determinism_identical_bytes(self):
        """T19 & BƯỚC 9: Hai lần chạy cùng seed và inventory.sample.json cho JSONL giống từng byte."""
        inv_sample = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "docs", "contracts", "inventory.sample.json")
        with Workdir() as w:
            out1 = w.path("quan_a.jsonl")
            out2 = w.path("quan_b.jsonl")
            code1, err1 = run_headless("--mode", "quan", "--seed", "42", "--ticks", "1500",
                                       "--inventory", inv_sample, "--out", out1)
            self.assertEqual(code1, 0, err1)
            code2, err2 = run_headless("--mode", "quan", "--seed", "42", "--ticks", "1500",
                                       "--inventory", inv_sample, "--out", out2)
            self.assertEqual(code2, 0, err2)
            with open(out1, "rb") as f1, open(out2, "rb") as f2:
                self.assertEqual(f1.read(), f2.read(), "Hai lần chạy phải giống nhau từng byte")

    def test_inventory_missing_one_ingredient_emits_no_dish(self):
        """Inventory thiếu đúng 1 nguyên liệu -> không đủ nấu món nào -> no_dish."""
        with Workdir() as w:
            # goi_bong_sung cần 2 bông súng, kho chỉ có 1
            sc = write_json(w.path("sc.json"), {
                "quan": {"stock": {"bong_sung": 1}}
            })
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "125",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            no_dish_evs = events(rows, "no_dish")
            self.assertEqual(len(no_dish_evs), 1)
            self.assertEqual(no_dish_evs[0]["tick"], 120)

    def test_customer_fixture_cooking_state_no_double_reservation(self):
        """Khách fixture ở trạng thái cooking không chiếm giữ reserved từ stock."""
        from chonoi.contract import load_contract
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.quan import QuanSim
        tuning = load_contract()["tuning"]
        sim = QuanSim(tuning, {
            "stock": {"ca_loc": 1},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "order_status": "cooking", "reserved": {}
            }]
        }, Streams(1), IdAllocator())

        # Kho khả dụng vẫn còn 1 ca_loc vì C1 không ở trạng thái reserved
        self.assertEqual(sim._available_stock()["ca_loc"], 1)

    def test_ticks_zero_lat3(self):
        """Chạy --ticks 0 trong chế độ quan tạo snapshot tick 0 hợp lệ và end line."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(rows[0]["type"], "snapshot")
            self.assertEqual(rows[0]["tick"], 0)
            self.assertEqual(rows[-1]["type"], "end")


if __name__ == "__main__":
    unittest.main()
