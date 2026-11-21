"""Test Quán Phase 2 (TICKET-02, Test Contract v1.1): 2 bếp / 4 bàn, 6 món, kế hoạch Ngày.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p "test_quan_p2.py" -v
(Windows: PYTHONPATH="tests;.")
"""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

TUNING = load_contract()["tuning"]
NO_INPUT = InputState((0.0, 0.0), {}, set())


def run_quan(w, scenario=None, inputs=None, ticks=1, inventory=None, name="q"):
    args = ["--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--out", w.path(f"{name}.jsonl")]
    if scenario is not None:
        args += ["--scenario", write_json(w.path(f"{name}-sc.json"), {"quan": scenario})]
    if inputs is not None:
        args += ["--inputs", write_json(w.path(f"{name}-in.json"), frames(*inputs))]
    if inventory is not None:
        args += ["--inventory", write_json(w.path(f"{name}-inv.json"), {"items": inventory})]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path(f"{name}.jsonl")) if code == 0 else None)


def sim(stock, plan_dishes=None, carry=None, scenario=None):
    sc = dict(scenario or {}, stock=stock)
    return QuanSim(TUNING, sc, Streams(1), IdAllocator(), plan_dishes=plan_dishes, carry=carry)


def step_until(s, phase_tick):
    out = []
    while s.phase_tick < phase_tick:
        out += s.step(NO_INPUT)
    return out


class StandardData(unittest.TestCase):
    """Mục 1.3 TICKET-02: số chuẩn quán, thực đơn 6 món, kế hoạch 5 Ngày."""

    def test_bep_ban_chuan(self):
        q = TUNING["quan"]
        self.assertEqual([(s["id"], s["pos"]) for s in q["stoves"]], [("B1", [2, 8]), ("B2", [5, 8])])
        self.assertEqual([(t["id"], t["pos"]) for t in q["tables"]],
                         [("T1", [9, 2]), ("T2", [13, 2]), ("T3", [9, 6]), ("T4", [13, 6])])

    def test_thuc_don_6_mon(self):
        menu = {k: (v["recipe"], v["cook_s"], v["price"]) for k, v in TUNING["menu"].items()}
        self.assertEqual(menu, {
            "ca_loc_nuong_trui": ({"ca_loc": 1}, 6, 60),
            "goi_bong_sung": ({"bong_sung": 2}, 4, 40),
            "lau_ca_linh_dien_dien": ({"ca_linh": 3, "bong_dien_dien": 1}, 10, 120),
            "canh_chua_ca_loc": ({"ca_loc": 1, "bong_dien_dien": 1}, 8, 90),
            "ca_keo_nuong": ({"ca_keo": 2}, 6, 70),
            "lau_mam": ({"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, 12, 200),
        })

    def test_ke_hoach_5_ngay(self):
        plan = TUNING["day_plan"]
        self.assertEqual([p["day"] for p in plan], [1, 2, 3, 4, 5])
        self.assertEqual(plan[0]["dishes"], {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3})
        self.assertEqual(plan[0]["ingredients"], {"ca_loc": 3, "bong_sung": 6})
        self.assertEqual(sum(plan[3]["ingredients"].values()), 9)   # D4: 9 ô (11 nếu bắt đàn)
        self.assertEqual(sum(plan[4]["ingredients"].values()), 10)  # D5: 10 ô


class StandaloneQuan(unittest.TestCase):
    def test_snapshot_co_2_bep_4_ban(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, ticks=0)
            self.assertEqual(code, 0, err)
            s = snapshots(rows)[0]
            self.assertEqual([x["id"] for x in s["stoves"]], ["B1", "B2"])
            self.assertEqual([x["id"] for x in s["tables"]], ["T1", "T2", "T3", "T4"])
            self.assertTrue(all(x["customer_id"] is None for x in s["tables"]))

    def test_kho_nhan_ca_keo_keo_neo_va_quan_rieng_dung_ca_6_mon(self):
        """Chỉ đủ nguyên liệu cho lẩu mắm (món mới) -> khách gọi đúng món đó."""
        with Workdir() as w:
            inv = {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}
            code, err, rows = run_quan(w, ticks=120, inventory=inv)
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(rows)[0]["stock"], {"bong_dien_dien": 1, "ca_keo": 1, "ca_linh": 2, "keo_neo": 1})
            arr = events(rows, "customer_arrived")
            self.assertEqual(arr[0]["data"], {"order_id": "C1", "table_id": "T1", "dish_id": "lau_mam"})

    def test_khach_thu_hai_ngoi_ban_trong_tiep_theo(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, ticks=1020, inventory={"ca_keo": 4})
            self.assertEqual(code, 0, err)
            arr = [(e["tick"], e["data"]["table_id"], e["data"]["dish_id"]) for e in events(rows, "customer_arrived")]
            self.assertEqual(arr, [(120, "T1", "ca_keo_nuong"), (1020, "T2", "ca_keo_nuong")])

    def test_bep_B2_nau_khi_B1_dang_ban(self):
        cook = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        sc = {"random_customers": False, "stock": {"ca_keo": 2}, "player": {"pos": [5, 7]},
              "stoves": [{"id": "B1", "state": "cooking", "dish": cook, "cook_ticks_left": 100}],
              "customers": [
                  {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"},
                  {"id": "C2", "table_id": "T2", "dish_id": "ca_keo_nuong", "order_tick": 5}]}
        with Workdir() as w:
            code, err, rows = run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "cook_started")[0]["data"],
                             {"stove_id": "B2", "order_id": "C2", "dish_id": "ca_keo_nuong",
                              "items": ["ca_keo", "ca_keo"], "base_price": 70})


class DayHooks(unittest.TestCase):
    """Giao diện cho mode `day` (lát day/Shop gọi): lọc món theo kế hoạch, mang tiền/uy tín qua Ngày."""

    def test_loc_mon_theo_ke_hoach_truoc_khi_xet_nguyen_lieu(self):
        # Đủ cả cá lóc nướng lẫn gỏi, nhưng kế hoạch chỉ có gỏi -> khách gọi gỏi.
        s = sim({"ca_loc": 5, "bong_sung": 2}, plan_dishes=["goi_bong_sung"])
        ev = step_until(s, 120)
        self.assertEqual(ev, [("customer_arrived", {"order_id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"})])

    def test_mon_ngoai_ke_hoach_khong_tinh_nen_no_dish(self):
        s = sim({"ca_loc": 5}, plan_dishes=["goi_bong_sung"])
        self.assertEqual(step_until(s, 120), [("no_dish", {})])

    def test_khach_goi_tiep_khi_da_ban_du_so_suat(self):
        """Số suất chỉ để tính mục tiêu thu gom: còn nguyên liệu thì vẫn gọi tiếp."""
        plan = TUNING["day_plan"][0]["dishes"]  # D1: ca_loc_nuong_trui x3, goi x3
        s = sim({"ca_loc": 10}, plan_dishes=list(plan))
        for c in range(4):
            s.customers.append({"id": f"X{c}", "table_id": f"T{c + 1}", "dish_id": "ca_loc_nuong_trui",
                                "order_tick": 0, "state": "eating", "patience_ticks_left": 0,
                                "eat_ticks_left": 1, "order_status": "served", "reserved": {},
                                "base_price": 60, "tip": 0})
        step_until(s, 1)  # 4 khách ăn xong, trả tiền, bàn trống
        ev = step_until(s, 120)
        self.assertEqual([e[1]["dish_id"] for e in ev if e[0] == "customer_arrived"], ["ca_loc_nuong_trui"])

    def test_mang_tien_uy_tin_tu_ngay_truoc(self):
        s = sim({}, carry={"money": 150, "earned": 380, "reputation": 4.2})
        self.assertEqual((s.money, s.earned, s.shift_earned, s.reputation), (150, 380, 0, 4.2))
        s.customers.append({"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_tick": 0,
                            "state": "eating", "patience_ticks_left": 3000, "eat_ticks_left": 1,
                            "order_status": "served", "reserved": {}, "base_price": 40, "tip": 8})
        ev = step_until(s, 1)
        self.assertEqual(ev[0][0], "paid")
        self.assertEqual((s.money, s.earned, s.shift_earned, s.reputation), (198, 428, 48, 4.4))

    def test_mac_dinh_quan_rieng_khong_doi(self):
        s = sim({})
        self.assertEqual((s.money, s.earned, s.reputation), (0, 0, TUNING["quan"]["reputation_initial"]))
        self.assertEqual(s.dish_pool, sorted(TUNING["menu"]))


if __name__ == "__main__":
    unittest.main()
