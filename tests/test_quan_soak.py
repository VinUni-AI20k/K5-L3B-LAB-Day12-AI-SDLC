"""Phase 4 TV3 (TICKET-04): soak 10 Ngày cho QuanSim (qua DaySim) + dữ liệu HUD "khách sắp giận".

Soak dựng DaySim TRỰC TIẾP với days=10 (CLI chặn --days 1–5, kiểm ở test_day_mode) và kế hoạch
D1–D5 lặp ở Ngày 6–10 qua khối day.day_plan. Mỗi Ngày: cập bến ở bước đầu (giữ edge interact),
quán chạy 3800 ticks, Shop 600 ticks. Kho nhỏ (4 nguyên liệu) + giữ chỗ theo kế hoạch nên chỉ
2–3 lượt khách mỗi Ngày rồi no_dish — khách đầu (đến tick 120) rời vì hết kiên nhẫn ở 3720,
còn lại rời closing lúc hết ca (không trừ uy tín).

Kiểm: days_completed = 10; khách mỗi Ngày bắt đầu sạch; uy tín kế thừa đúng và luôn trong [0, 5];
id khách cấp liên tục không trùng xuyên Ngày; snapshot quán đủ customers[].patience_ticks_left
+ state cho HUD. Số liệu đọc từ fixture contract (không hard-code).
Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import os
import unittest
from collections import Counter

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator, id_key
from chonoi.inputs import InputPlayer, load_frames
from chonoi.rng import Streams
from chonoi.sim.day import DaySim

from helpers import ROOT, Workdir, frames, write_json

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "contract-v1.1-day.json")
T11 = load_contract(FIXTURE)["tuning"]

QUAN_TICKS = 3800          # thời lượng ca quán mỗi Ngày trong soak
DAY_TICKS = 1 + QUAN_TICKS + 600  # cập bến 1 tick + quán + Shop mặc định (shop.max_ticks)
STOCK_DAY = {"bong_sung": 2, "ca_loc": 1, "ca_linh": 1}
REP0 = T11["quan"]["reputation_initial"]
DELTA = T11["quan"]["left_reputation_delta"]
REP_LO, REP_HI = T11["quan"]["reputation_min"], T11["quan"]["reputation_max"]


def soak_scenario():
    """Kế hoạch D1–D5 lặp cho Ngày 6–10 + mẫu gather/quan của mỗi Ngày."""
    src = {p["day"]: p["dishes"] for p in T11["day_plan"]}
    return {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung", "ca_linh"], "random_fish": False},
            "quan": {"time_left_ticks": QUAN_TICKS},
            "day": {"day_plan": [{"day": d, "dishes": dict(src[(d - 1) % 5 + 1])} for d in range(1, 11)]}}


def player_with_daily_dock(days=10):
    """Edge interact ở bước đầu mỗi Ngày (giữ True sẽ không có cạnh mới ở Ngày kế);
    Shop không nhận lệnh -> tự đóng sau shop.max_ticks."""
    fr = []
    for k in range(days):
        fr.append({"tick": k * DAY_TICKS, "interact": True})
        fr.append({"tick": k * DAY_TICKS + 1, "interact": False})
    return fr


class SoakTenDays(unittest.TestCase):
    def test_soak_10_ngay_lien_tiep_on_dinh(self):
        with Workdir() as w:
            inp_path = write_json(w.path("i.json"), frames(*player_with_daily_dock(10)))
            player = InputPlayer(load_frames(inp_path))
            sim = DaySim(T11, soak_scenario(), Streams(1), IdAllocator(), days=10)

            arrivals, left_by_reason = [], Counter()
            used_ids = []
            quan_start_reps, quan_start_snaps = [], []
            quan_end_reps = []
            midday_checked = False
            steps = 0
            while not sim.done and steps < 60000:
                out = sim.step(player.advance(steps))
                steps += 1
                for name, data, phase, day in out:
                    if name == "customer_arrived":
                        arrivals.append((day, data["order_id"]))
                    elif name == "customer_left":
                        left_by_reason[data["reason"]] += 1
                        used_ids.append(data["order_id"])
                    elif name == "quan_end":
                        quan_end_reps.append(data["reputation"])
                        self.assertTrue(0 <= data["reputation"] <= 5)
                if sim.phase_changed and sim.phase == "quan":
                    quan_start_snaps.append(sim.snapshot())
                    quan_start_reps.append(sim.reputation)  # property: child/state theo pha
                # giữa Ngày 1: khách đang chờ trong snapshot -> HUD đọc được patience + state
                if not midday_checked and sim.phase == "quan" and sim.day == 1 \
                        and sim.child.phase_tick == 150:
                    mid_snap = sim.snapshot()
                    self.assertEqual(len(mid_snap["customers"]), 1)
                    for c in mid_snap["customers"]:
                        self.assertIn("patience_ticks_left", c)
                        self.assertIn("state", c)
                        self.assertEqual(c["state"], "waiting")
                    midday_checked = True

        self.assertTrue(midday_checked, "đã chụp được snapshot giữa Ngày 1")
        self.assertTrue(sim.done)
        self.assertEqual((sim.reason, sim.days_completed), ("days_complete", 10))
        self.assertLessEqual(steps, 60000, "10 Ngày phải kết thúc trong giới hạn bước")

        # Mỗi Ngày: khách bắt đầu sạch, kho bàn giao đúng giỏ cập bến, uy tín kế thừa đúng
        self.assertEqual([s["day"] for s in quan_start_snaps], list(range(1, 11)))
        for snap in quan_start_snaps:
            self.assertEqual(snap["customers"], [], "Ngày mới khách phải bắt đầu sạch")
            self.assertEqual(snap["stock"], STOCK_DAY)
        expected_reps = [max(REP_LO, min(REP_HI, REP0 + DELTA * k)) for k in range(10)]
        self.assertEqual(quan_start_reps, expected_reps,
                         "uy tín kế thừa từ Ngày trước (mỗi Ngày -0.5 vì 1 khách hết kiên nhẫn), kẹp [0, 5]")
        expected_end = [max(REP_LO, min(REP_HI, REP0 + DELTA * (k + 1))) for k in range(10)]
        self.assertEqual(quan_end_reps, expected_end, "quan_end chốt đúng uy tín cuối Ngày")

        # Khách: mỗi Ngày có khách (kế hoạch + kho nhỏ nên chỉ 2–3 lượt trước khi no_dish — tối đa
        # bằng số bàn); đúng 1 khách/Ngày hết kiên nhẫn (khách đến tick 120 rời ở 3720), còn lại
        # rời closing; mọi khách đều rời trong Ngày của mình.
        per_day_arr = Counter(day for day, _ in arrivals)
        self.assertEqual(sorted(per_day_arr), list(range(1, 11)), "mỗi Ngày đều có khách đến")
        self.assertTrue(all(1 <= n <= 4 for n in per_day_arr.values()),
                        f"lượt khách mỗi Ngày trong [1, số bàn]: {dict(per_day_arr)}")
        self.assertEqual(left_by_reason["patience"], 10)
        self.assertEqual(left_by_reason["closing"] + left_by_reason["patience"], len(arrivals),
                         "không khách nào mất tích: patience hoặc closing")

        # IdAllocator: không trùng, không nhảy id — mọi id khách đã dùng là C1..Cn (so theo id_key,
        # vì thứ tự RỜI bàn là theo id_key(table_id) chứ không theo id khách)
        self.assertEqual(sorted(used_ids, key=id_key), [f"C{i}" for i in range(1, len(used_ids) + 1)],
                         "id khách duy nhất, cấp liên tục không nhảy, xuyên Ngày")
        self.assertGreaterEqual(len(used_ids), 10)
        self.assertNotIn(sim.ids.new("C"), used_ids, "cấp tiếp sau soak vẫn không đụng id đã dùng")


class SnapshotFields(unittest.TestCase):
    """QuanSim.snapshot() phải mang đủ trường HUD cần cho cảnh báo khách sắp giận."""

    def test_snapshot_co_day_du_patience_va_state(self):
        from chonoi.inputs import InputState
        from chonoi.sim.quan import QuanSim
        idle = InputState((0, 0), frozenset(), frozenset())
        sc = {"stock": {"ca_loc": 3},
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                             "order_tick": 0, "state": "waiting", "order_status": "reserved",
                             "patience_ticks_left": 900, "eat_ticks_left": 0,
                             "reserved": {"ca_loc": 1}}]}
        sim = QuanSim(T11, sc, Streams(1), IdAllocator())
        sim.step(idle)
        snap = sim.snapshot()
        self.assertEqual(len(snap["customers"]), 1)
        c = snap["customers"][0]
        self.assertIn("patience_ticks_left", c)
        self.assertIn("state", c)
        self.assertEqual(c["state"], "waiting")
        self.assertEqual(c["patience_ticks_left"], 899)


if __name__ == "__main__":
    unittest.main()
