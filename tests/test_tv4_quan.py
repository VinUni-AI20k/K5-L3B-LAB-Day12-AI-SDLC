"""Test bộ phận Bếp, Phục vụ, Tiền boa và Thanh toán (TV4 - AnhQuanHANU)."""

import os
import unittest

try:
    from helpers import Workdir, events, frames, read_jsonl, run_headless, write_json
except ImportError:
    from tests.helpers import Workdir, events, frames, read_jsonl, run_headless, write_json


class TestQuanTV4(unittest.TestCase):
    def test_cook_and_pick_dish_at_stove(self):
        """Kiểm tra Bếp: đứng gần B1, bấm interact bắt đầu nấu -> chín món -> nhặt lên tay."""
        with Workdir() as w:
            # Khách C1 ở bàn T1 đặt cá lóc nướng trui (nấu 6s = 360 ticks)
            # Người chơi đứng tại B1 [2.0, 8.0]
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [2.0, 8.0]},
                    "stock": {"ca_loc": 2},
                    "customers": [
                        {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 3600}
                    ]
                }
            })
            # Tick 0: interact bắt đầu nấu
            # Tick 361: interact nhặt món (sau khi chín ở tick 360)
            inp = write_json(w.path("inp.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False},
                {"tick": 361, "interact": True},
                {"tick": 362, "interact": False}
            ))
            out = w.path("out.jsonl")

            code, err = run_headless(
                "--mode", "quan", "--seed", "42", "--ticks", "365",
                "--scenario", sc, "--inputs", inp, "--out", out
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)

            # 1. Kiểm tra sự kiện cook_started ở tick 1
            cook_ev = events(rows, "cook_started")
            self.assertEqual(len(cook_ev), 1)
            self.assertEqual(cook_ev[0]["data"]["stove_id"], "B1")
            self.assertEqual(cook_ev[0]["data"]["order_id"], "C1")
            self.assertEqual(cook_ev[0]["data"]["dish_id"], "ca_loc_nuong_trui")
            self.assertEqual(cook_ev[0]["data"]["base_price"], 60)
            self.assertEqual(cook_ev[0]["data"]["items"], ["ca_loc"])

            # 2. Kiểm tra sự kiện dish_ready sau 360 tick nấu (bước k ghi tại k+1 => tick 361)
            ready_ev = events(rows, "dish_ready")
            self.assertEqual(len(ready_ev), 1)
            self.assertEqual(ready_ev[0]["tick"], 361)
            self.assertEqual(ready_ev[0]["data"]["stove_id"], "B1")

            # 3. Kiểm tra sự kiện dish_picked ở tick 362
            picked_ev = events(rows, "dish_picked")
            self.assertEqual(len(picked_ev), 1)
            self.assertEqual(picked_ev[0]["tick"], 362)
            self.assertEqual(picked_ev[0]["data"]["order_id"], "C1")

    def test_serve_eat_and_payment_with_tip(self):
        """Kiểm tra Phục vụ & Thanh toán: tay có món, đứng tại bàn T1 bấm interact -> phục vụ -> ăn xong trả tiền + tip."""
        with Workdir() as w:
            # Người chơi đứng tại bàn T1 [9.0, 2.0], tay đang cầm cá lóc nướng trui của C1
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [9.0, 2.0]},
                    "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                    "customers": [
                        {
                            "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "patience_ticks_left": 3000, "base_price": 60
                        }
                    ]
                }
            })
            # Tick 0: interact để giao món
            inp = write_json(w.path("inp.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False}
            ))
            out = w.path("out.jsonl")

            # Chạy 610 ticks (ăn 600 ticks = 10s)
            code, err = run_headless(
                "--mode", "quan", "--seed", "42", "--ticks", "610",
                "--scenario", sc, "--inputs", inp, "--out", out
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)

            # 1. Kiểm tra served tại tick 1
            served_ev = events(rows, "served")
            self.assertEqual(len(served_ev), 1)
            self.assertEqual(served_ev[0]["data"]["order_id"], "C1")
            self.assertEqual(served_ev[0]["data"]["table_id"], "T1")
            # Kiên nhẫn còn 3000/3600 > 50% => tip = 60 * 0.2 = 12
            self.assertEqual(served_ev[0]["data"]["tip"], 12)

            # 2. Kiểm tra paid sau 600 ticks ăn
            paid_ev = events(rows, "paid")
            self.assertEqual(len(paid_ev), 1)
            self.assertEqual(paid_ev[0]["data"]["base_price"], 60)
            self.assertEqual(paid_ev[0]["data"]["tip"], 12)
            self.assertEqual(paid_ev[0]["data"]["amount"], 72)
            self.assertEqual(paid_ev[0]["data"]["reason"], "finished_eating")

            # 3. Kiểm tra điểm uy tín tăng từ 3.0 lên 3.2
            end_row = rows[-1]
            self.assertEqual(end_row["type"], "end")
            self.assertEqual(end_row["money"], 72)
            self.assertAlmostEqual(end_row["reputation"], 3.2, places=2)

    def test_closing_immediate_payment_for_eating_customers(self):
        """Kiểm tra khi hết ca: khách đang ăn trả tiền ngay với reason 'closing'."""
        with Workdir() as w:
            # Khách C1 đang ăn ở bàn T1, ca chỉ còn 5 ticks
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "time_left_ticks": 5,
                    "customers": [
                        {
                            "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "state": "eating", "eat_ticks_left": 500, "base_price": 60, "tip": 12
                        }
                    ]
                }
            })
            out = w.path("out.jsonl")
            code, err = run_headless(
                "--mode", "quan", "--seed", "42", "--ticks", "10",
                "--scenario", sc, "--out", out
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)

            paid_ev = events(rows, "paid")
            self.assertEqual(len(paid_ev), 1)
            self.assertEqual(paid_ev[0]["data"]["reason"], "closing")
            self.assertEqual(paid_ev[0]["data"]["amount"], 72)

            quan_end_ev = events(rows, "quan_end")
            self.assertEqual(len(quan_end_ev), 1)
            self.assertEqual(quan_end_ev[0]["data"]["reason"], "time")
            self.assertEqual(quan_end_ev[0]["data"]["money"], 72)


    def test_serve_at_exact_zero_patience_tick_is_valid(self):
        """Ca biên: Giao đúng món ở tick kiên nhẫn về 0 vẫn hợp lệ, không bị customer_left."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [9.0, 2.0]},
                    "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "patience_ticks_left": 1, "base_price": 60
                    }]
                }
            })
            inp = write_json(w.path("inp.json"), frames({"tick": 0, "interact": True}))
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            served_ev = events(rows, "served")
            left_ev = events(rows, "customer_left")
            self.assertEqual(len(served_ev), 1)
            self.assertEqual(len(left_ev), 0)

    def test_serve_at_closing_tick_pays_immediately_once(self):
        """Ca biên: Nếu giao đúng tick đóng ca, khách trả ngay đúng một lần với reason closing."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [9.0, 2.0]},
                    "time_left_ticks": 1,
                    "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "patience_ticks_left": 100, "base_price": 60
                    }]
                }
            })
            inp = write_json(w.path("inp.json"), frames({"tick": 0, "interact": True}))
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(len(events(rows, "served")), 1)
            paid_ev = events(rows, "paid")
            self.assertEqual(len(paid_ev), 1)
            self.assertEqual(paid_ev[0]["data"]["reason"], "closing")
            self.assertEqual(len(events(rows, "quan_end")), 1)


if __name__ == "__main__":
    unittest.main()
