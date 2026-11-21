"""Lát 3 Phase 2 (quán, phần khách): lọc món theo kế hoạch Ngày trong `--mode day`, quán độc lập dùng cả menu.

AC-P2-06 (khách chỉ gọi món trong kế hoạch). Ticket-02 mục 2: "Trong day, khách chọn đều theo seed từ các id món
trong kế hoạch có đủ nguyên liệu sau khi trừ phần đang giữ ... Quán chạy riêng dùng cả 6 món. Có bàn mà thiếu
món thì no_dish." và mục 4.5: "Trong day, lọc menu theo id món trong kế hoạch trước khi lọc nguyên liệu khả dụng."

Cập bến ở tick 0 -> gather_end tick 1 -> quán mở cùng tick (phase_tick 0) -> lượt khách đầu ở
phase_tick = first_customer_tick, tức tick ngoài = 1 + first_customer_tick.
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, write_json
from legacy_v11 import setUpModule, tearDownModule  # noqa: F401  v1.2: fixture kho đếm chạy trên manifest v1.1 tạm, xem tests/legacy_v11.py

with open("game.contract.json", encoding="utf-8") as _f:
    TUNING = json.load(_f)["tuning"]
FIRST = TUNING["quan"]["first_customer_tick"]
ARRIVE = 1 + FIRST  # tick ngoài của lượt khách đầu trong Ngày khi cập bến ở tick 0
PLAN = {p["day"]: set(p["dishes"]) for p in TUNING["day_plan"]}
# giỏ đủ cho món TRONG kế hoạch D1 (ca_loc_nuong_trui) lẫn món NGOÀI kế hoạch (lẩu cá linh, canh chua)
MIXED_HOLD = ["ca_linh", "ca_linh", "ca_linh", "bong_dien_dien", "ca_loc"]


def run_day(scenario, ticks=ARRIVE, seed=1):
    """Chạy mode day, cập bến ngay tick 0. Trả (mã thoát, stderr, rows)."""
    with Workdir() as w:
        out = w.path("o.jsonl")
        code, err = run_headless("--mode", "day", "--seed", str(seed), "--ticks", str(ticks),
                                 "--scenario", write_json(w.path("sc.json"), scenario),
                                 "--inputs", write_json(w.path("in.json"), frames({"tick": 0, "interact": True})),
                                 "--out", out)
        return code, err, (read_jsonl(out) if code == 0 else None)


def day_scenario(hold, **day_block):
    sc = {"gather": {"hold": list(hold), "random_fish": False}}
    if day_block:
        sc["day"] = day_block
    return sc


class DayPlanFilter(unittest.TestCase):
    def test_ac_p2_06_khach_chi_goi_mon_trong_ke_hoach(self):
        """Kho đủ cả món ngoài kế hoạch, nhưng khách Ngày 1 chỉ được gọi món trong kế hoạch D1."""
        in_plan = {d for d in PLAN[1]
                   if all(MIXED_HOLD.count(k) >= n for k, n in TUNING["menu"][d]["recipe"].items())}
        self.assertTrue(in_plan, "fixture phải có ít nhất một món trong kế hoạch D1 nấu được")
        for seed in range(1, 9):
            code, err, rows = run_day(day_scenario(MIXED_HOLD), seed=seed)
            self.assertEqual(code, 0, err)
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1, seed)
            e = arr[0]
            self.assertEqual((e["tick"], e["phase"], e["day"]), (ARRIVE, "quan", 1))
            self.assertIn(e["data"]["dish_id"], in_plan, seed)

    def test_ac_p2_06_chi_du_mon_ngoai_ke_hoach_thi_no_dish(self):
        hold = ["ca_linh", "ca_linh", "ca_linh", "bong_dien_dien"]  # chỉ đủ lẩu cá linh — không có trong D1
        self.assertNotIn("lau_ca_linh_dien_dien", PLAN[1])
        code, err, rows = run_day(day_scenario(hold))
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows, "customer_arrived"), [])
        nd = events(rows, "no_dish")
        self.assertEqual([(e["tick"], e["phase"], e["data"]) for e in nd], [(ARRIVE, "quan", {})])

    def test_ac_p2_06_ke_hoach_ghi_de_trong_scenario_doi_mon_khach_goi(self):
        hold = ["ca_linh", "ca_linh", "ca_linh", "bong_dien_dien"]
        sc = day_scenario(hold, day_plan=[{"day": 1, "dishes": {"lau_ca_linh_dien_dien": 1}}])
        code, err, rows = run_day(sc)
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows, "day_plan")[0]["data"]["dishes"], {"lau_ca_linh_dien_dien": 1})
        arr = events(rows, "customer_arrived")
        self.assertEqual([e["data"]["dish_id"] for e in arr], ["lau_ca_linh_dien_dien"])

    def test_ac_p2_06_khach_fixture_goi_mon_ngoai_ke_hoach_ma_2(self):
        sc = day_scenario(["ca_linh", "ca_linh", "ca_linh", "bong_dien_dien"])
        sc["quan"] = {"customers": [{"id": "C1", "table_id": TUNING["quan"]["tables"][0]["id"],
                                     "dish_id": "lau_ca_linh_dien_dien"}]}
        code, _, _ = run_day(sc, ticks=2)
        self.assertEqual(code, 2)


class StandaloneMenu(unittest.TestCase):
    def test_quan_doc_lap_dung_ca_menu(self):
        """Quán chạy riêng không lọc theo kế hoạch: món ngoài D1 (canh chua) vẫn được gọi."""
        self.assertNotIn("canh_chua_ca_loc", PLAN[1])
        seen = set()
        for seed in range(1, 21):
            with Workdir() as w:
                sc = write_json(w.path("sc.json"), {"quan": {"stock": {"ca_loc": 1, "bong_dien_dien": 1}}})
                out = w.path("q.jsonl")
                code, err = run_headless("--mode", "quan", "--seed", str(seed), "--ticks", str(FIRST),
                                         "--scenario", sc, "--out", out)
                self.assertEqual(code, 0, err)
                seen |= {e["data"]["dish_id"] for e in events(read_jsonl(out), "customer_arrived")}
        self.assertIn("canh_chua_ca_loc", seen)
        self.assertLessEqual(seen, {"ca_loc_nuong_trui", "canh_chua_ca_loc"})


if __name__ == "__main__":
    unittest.main()
