"""Unit test cho Vòng lặp Ngày (Người B — Phase 3 / Chế độ --mode day).

Kiểm tra:
1. Trình tự chuyển đổi các pha:
   DayIntro -> gather -> EveningIntro -> quan -> DayResult -> Shop -> Next Day.
2. Công bố thực đơn Má Tư theo từng ngày D1..D5.
3. Chuyển giao kho thu hoạch từ Sáng sang Tối.
4. Chuyển giao tiền, uy tín từ Tối sang Shop.
5. Hiệu ứng nâng cấp mua ở Shop (đêm D1) phát huy tác dụng ở sáng D2 (oxy/máu).
6. Bảo lưu doanh thu (earned), uy tín và tính điểm số cuối ngày.
7. Tích hợp chạy headless `--mode day`.
"""

import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session
from chonoi.sim.day import DEFAULT_DAILY_MENU, DaySim
from helpers import Workdir, read_jsonl, run_headless, write_json


def _inp(move=(0.0, 0.0), interact=False, buy=None):
    edges = {"interact"} if interact else set()
    inp = InputState(move, set(edges), edges)
    if buy:
        inp.buy = buy
    return inp


class TestDayLoop(unittest.TestCase):
    """Kiểm tra logic State Machine của DaySim và vòng ngày D1..D5."""

    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_day_intro_announces_ma_tu_menu(self):
        """Pha DayIntro công bố đúng thực đơn kế hoạch Má Tư cho D1..D5."""
        day_sim = DaySim(self.tuning, {"intro_ticks": 2})

        # Tick 1: Bắn day_start và day_intro
        evs = day_sim.step(_inp())
        ev_names = [e[0] for e in evs]
        self.assertIn("day_start", ev_names)
        self.assertIn("day_intro", ev_names)

        intro_ev = next(e for e in evs if e[0] == "day_intro")
        self.assertEqual(intro_ev[1]["day"], 1)
        self.assertEqual(intro_ev[1]["menu"], DEFAULT_DAILY_MENU[1])

        # Thực đơn D1: cá lóc nướng trui, gỏi bông súng
        self.assertIn("ca_loc_nuong_trui", intro_ev[1]["menu"])
        self.assertIn("goi_bong_sung", intro_ev[1]["menu"])

        # Kiểm tra thực đơn các ngày tiếp theo
        self.assertEqual(day_sim.get_daily_menu(2), DEFAULT_DAILY_MENU[2])
        self.assertEqual(day_sim.get_daily_menu(5), DEFAULT_DAILY_MENU[5])
        self.assertEqual(len(day_sim.get_daily_menu(5)), 6)  # D5 đủ 6 món

    def test_transition_from_day_intro_to_gather(self):
        """Hết giờ intro hoặc khi bấm interact sẽ chuyển sang gather."""
        day_sim = DaySim(self.tuning, {"intro_ticks": 5})
        day_sim.step(_inp())  # Tick 1

        # Người chơi ấn interact để skip intro
        evs = day_sim.step(_inp(interact=True))
        self.assertEqual(day_sim.phase, "gather")
        self.assertIsNotNone(day_sim.active_sim)
        self.assertEqual(day_sim.active_sim.mode, "gather")
        self.assertTrue(any(e[0] == "phase_started" and e[1]["phase"] == "gather" for e in evs))

    def test_gather_inventory_handover_to_evening_and_quan(self):
        """Nguyên liệu thu hoạch buổi sáng được chuyển giao vào kho quán tối."""
        day_sim = DaySim(self.tuning, {
            "intro_ticks": 1,
            "gather": {
                "time_left_ticks": 10,
                "hold": ["ca_loc", "ca_linh", "ca_linh", "bong_sung"],
            },
        })

        # Tick 1: DayIntro
        day_sim.step(_inp())
        # Tick 2: Sang gather
        day_sim.step(_inp())
        self.assertEqual(day_sim.phase, "gather")

        # Cập bến hoặc kết thúc gather -> thu hoạch vào kho
        day_sim.active_sim.done = True
        evs = day_sim.step(_inp())

        # Kiểm tra kho nhận được nguyên liệu từ giỏ
        self.assertEqual(day_sim.stock.get("ca_loc"), 1)
        self.assertEqual(day_sim.stock.get("ca_linh"), 2)
        self.assertEqual(day_sim.stock.get("bong_sung"), 1)
        self.assertEqual(day_sim.phase, "evening_intro")

        # Skip evening_intro -> sang quan
        day_sim.step(_inp(interact=True))
        self.assertEqual(day_sim.phase, "quan")
        self.assertEqual(day_sim.active_sim.stock.get("ca_loc"), 1)

    def test_quan_closing_transfers_money_and_reputation_to_shop(self):
        """Kết thúc ca tối, doanh thu và uy tín chuyển vào Shop ban đêm."""
        day_sim = DaySim(self.tuning, {"intro_ticks": 1})
        day_sim.phase = "quan"
        day_sim.stock = {"ca_loc": 2}
        day_sim._start_quan()

        # Giả lập quán kết thúc ca với tiền kiếm được và uy tín tăng
        day_sim.active_sim.money = 250
        day_sim.active_sim.earned = 250
        day_sim.active_sim.reputation = 3.6
        day_sim.active_sim.done = True

        day_sim.step(_inp())
        self.assertEqual(day_sim.phase, "day_result")
        self.assertEqual(day_sim.money, 250)
        self.assertEqual(day_sim.earned, 250)
        self.assertAlmostEqual(day_sim.reputation, 3.6, places=2)

        # Chuyển từ DayResult sang Shop
        day_sim.step(_inp(interact=True))
        self.assertEqual(day_sim.phase, "shop")
        self.assertEqual(day_sim.active_sim.money, 250)

    def test_shop_upgrade_takes_effect_on_next_day_morning(self):
        """Mua nâng cấp bình oxy ở đêm D1 thì sáng D2 nhận oxy tối đa 45s."""
        day_sim = DaySim(self.tuning, {"intro_ticks": 1})
        day_sim.phase = "shop"
        day_sim.day = 1
        day_sim.money = 300
        day_sim.earned = 300
        day_sim._start_shop()

        # Mua oxy Lv 1 (giá 200)
        buy_evs = day_sim.active_sim.buy("oxygen")
        self.assertEqual(buy_evs[0][0], "upgrade_bought")
        self.assertEqual(day_sim.active_sim.money, 100)

        # Đóng shop -> chuyển sang Ngày 2
        day_sim.active_sim.finish()
        evs = day_sim.step(_inp())

        self.assertEqual(day_sim.day, 2)
        self.assertEqual(day_sim.money, 100)
        self.assertEqual(day_sim.upgrades["oxygen"], 1)

        # Sáng ngày 2 bắt đầu gather
        day_sim._start_gather()
        self.assertEqual(day_sim.tuning["gather"]["oxygen_max_s"], 45)
        self.assertEqual(day_sim.active_sim.oxygen_max, 45 * 60)  # 2700 ticks

    def test_five_days_cycle_completes_game(self):
        """Chạy đủ 5 ngày (D1..D5) kết thúc game và tính điểm chung cuộc."""
        day_sim = DaySim(self.tuning, {"intro_ticks": 1, "max_days": 5})
        day_sim.day = 5
        day_sim.phase = "shop"
        day_sim.money = 1500
        day_sim.earned = 1500
        day_sim.reputation = 4.5
        day_sim._start_shop()

        # Đóng shop đêm Ngày 5
        day_sim.active_sim.finish()
        evs = day_sim.step(_inp())

        self.assertTrue(day_sim.done)
        self.assertEqual(day_sim.reason, "completed")
        day_end_ev = next(e for e in evs if e[0] == "day_end")
        self.assertEqual(day_end_ev[1]["total_days"], 5)
        # score = earned + 100 * floor(reputation) = 1500 + 100 * 4 = 1900
        self.assertEqual(day_end_ev[1]["score"], 1900)

    def test_headless_mode_day_execution(self):
        """Chạy thử lệnh headless `--mode day` không bị lỗi."""
        with Workdir() as w:
            out = w.path("day_out.jsonl")
            sc = write_json(w.path("day_sc.json"), {
                "day": {
                    "intro_ticks": 5,
                    "money": 100,
                    "earned": 100,  # v1.1 yêu cầu khai earned khi có tiền đầu kỳ.
                    "reputation": 3.5,
                }
            })
            code, err = run_headless(
                "--mode", "day",
                "--seed", "1",
                "--ticks", "10",
                "--scenario", sc,
                "--out", out,
            )
            self.assertEqual(code, 0, f"Headless mode day failed: {err}")
            rows = read_jsonl(out)
            self.assertTrue(len(rows) > 0)
            self.assertEqual(rows[0]["type"], "snapshot")
            self.assertEqual(rows[0]["mode"], "day")


if __name__ == "__main__":
    unittest.main()
