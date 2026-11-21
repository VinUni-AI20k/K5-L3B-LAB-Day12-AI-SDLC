"""Test hộp đen cho luật Quán (PRD-0 mục D, E, F) — chạy qua headless_cmd, đọc JSONL.

Chạy: PYTHONPATH=tests:. python3 -m unittest test_quan_p1 -v
"""

import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

DISH_LOC = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}


def run_quan(w, scenario=None, inputs=None, ticks=1, seed=1, name="q"):
    args = ["--mode", "quan", "--seed", str(seed), "--ticks", str(ticks), "--out", w.path(f"{name}.jsonl")]
    if scenario is not None:
        args += ["--scenario", write_json(w.path(f"{name}-sc.json"), {"quan": scenario})]
    if inputs is not None:
        args += ["--inputs", write_json(w.path(f"{name}-in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path(f"{name}.jsonl")) if code == 0 else None)


class Customers(unittest.TestCase):
    def test_khach_den_theo_lich_va_giu_cho(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": {"ca_linh": 3, "bong_dien_dien": 1}}, ticks=120)
            self.assertEqual(code, 0, err)
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1)
            self.assertEqual(arr[0]["tick"], 120)
            self.assertEqual(arr[0]["data"], {"order_id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien"})
            c = snapshots(rows)[-1]["customers"][0]
            self.assertEqual(c["reserved"], {"bong_dien_dien": 1, "ca_linh": 3})
            self.assertEqual(c["order_status"], "reserved")
            self.assertEqual(c["patience_ticks_left"], 3600)
            self.assertEqual(c["order_tick"], 120)
            self.assertEqual(snapshots(rows)[-1]["tables"][0]["customer_id"], "C1")

    def test_kien_nhan_bat_dau_giam_tu_buoc_sau(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": {"ca_loc": 1}}, ticks=121, name="a")
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(rows)[-1]["customers"][0]["patience_ticks_left"], 3599)

    def test_khong_mon_nao_nau_duoc_thi_no_dish(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {}, ticks=120)
            self.assertEqual(code, 0, err)
            nd = events(rows, "no_dish")
            self.assertEqual([(e["tick"], e["data"]) for e in nd], [(120, {})])
            self.assertEqual(events(rows, "customer_arrived"), [])

    def test_het_ban_thi_bo_luot(self):
        with Workdir() as w:
            sc = {"stock": {"ca_loc": 2}, "random_customers": True,
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}
            code, err, rows = run_quan(w, sc, ticks=120)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "customer_arrived") + events(rows, "no_dish"), [])

    def test_het_kien_nhan_bo_di_tru_uy_tin(self):
        with Workdir() as w:
            sc = {"stock": {"ca_loc": 1}, "random_customers": False,
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                 "patience_ticks_left": 1}]}
            code, err, rows = run_quan(w, sc, ticks=2)
            self.assertEqual(code, 0, err)
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1)
            self.assertEqual(left[0]["tick"], 1)
            self.assertEqual(left[0]["data"], {"order_id": "C1", "table_id": "T1", "reason": "patience",
                                               "reputation": 2.5})
            last = snapshots(rows)[-1]
            self.assertEqual(last["customers"], [])
            self.assertEqual(last["stock"], {"ca_loc": 1})  # phần giữ được nhả, kho còn nguyên

    def test_khach_bo_di_thi_bo_mon_tren_tay(self):
        with Workdir() as w:
            sc = {"random_customers": False, "hand": DISH_LOC,
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                 "order_status": "assigned", "patience_ticks_left": 1}]}
            code, err, rows = run_quan(w, sc, ticks=1)
            self.assertEqual(code, 0, err)
            self.assertIsNone(snapshots(rows)[-1]["hand"])


class KitchenAndService(unittest.TestCase):
    def test_nau_chin_bung(self):
        with Workdir() as w:
            sc = {"stock": {"ca_loc": 1}, "random_customers": False, "player": {"pos": [2, 7]},
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}
            inp = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                   {"tick": 361, "interact": True}]
            code, err, rows = run_quan(w, sc, inp, ticks=362)
            self.assertEqual(code, 0, err)
            cs = events(rows, "cook_started")
            self.assertEqual(cs[0]["tick"], 1)
            self.assertEqual(cs[0]["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui",
                                             "items": ["ca_loc"], "base_price": 60})
            rd = events(rows, "dish_ready")
            self.assertEqual((rd[0]["tick"], rd[0]["data"]),
                             (361, {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui"}))
            pk = events(rows, "dish_picked")
            self.assertEqual(pk[0]["tick"], 362)
            last = snapshots(rows)[-1]
            self.assertEqual(last["hand"], DISH_LOC)
            self.assertEqual(last["stock"], {})
            self.assertEqual(last["stoves"][0]["state"], "idle")
            self.assertEqual(last["customers"][0]["order_status"], "assigned")

    def test_phuc_vu_co_boa_roi_tra_tien(self):
        with Workdir() as w:
            sc = {"random_customers": False, "player": {"pos": [9, 3]}, "hand": DISH_LOC,
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                 "order_status": "assigned"}]}
            code, err, rows = run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=602)
            self.assertEqual(code, 0, err)
            sv = events(rows, "served")[0]
            self.assertEqual(sv["data"], {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                          "patience_ticks_left": 3599, "base_price": 60, "tip": 12})
            pd = events(rows, "paid")[0]
            self.assertEqual(pd["tick"], 601)
            self.assertEqual(pd["data"], {"order_id": "C1", "table_id": "T1", "base_price": 60, "tip": 12,
                                          "amount": 72, "reason": "finished_eating"})
            last = snapshots(rows)[-1]
            self.assertEqual((last["money"], last["earned"], last["reputation"]), (72, 72, 3.2))
            self.assertEqual(last["score"], 72 + 300)

    def test_kien_nhan_thap_thi_khong_boa(self):
        with Workdir() as w:
            sc = {"random_customers": False, "player": {"pos": [9, 3]}, "hand": DISH_LOC,
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                 "order_status": "assigned", "patience_ticks_left": 1000}]}
            code, err, rows = run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "served")[0]["data"]["tip"], 0)

    def test_bep_truoc_ban_khi_bang_khoang_cach_va_mat_luot(self):
        """Bếp B1 [2,8] và bàn T1 dời tới [2,6]; đứng [2,7]: chọn bếp (idle, không có đơn) -> bỏ lượt."""
        with Workdir() as w:
            sc = {"random_customers": False, "player": {"pos": [2, 7]}, "hand": DISH_LOC,
                  "tables": [{"id": "T1", "pos": [2, 6]}],
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                 "order_status": "assigned"}]}
            code, err, rows = run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "served"), [])

    def test_het_ca_khach_an_tra_tien_khach_cho_roi_khong_tru_uy_tin(self):
        with Workdir() as w:
            sc = {"random_customers": False, "time_left_ticks": 1, "stock": {"ca_loc": 1},
                  "tables": [{"id": "T1", "pos": [9, 2]}],
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                 "state": "eating", "base_price": 60, "tip": 0, "eat_ticks_left": 100}]}
            code, err, rows = run_quan(w, sc, ticks=5)
            self.assertEqual(code, 0, err)
            names = [e["name"] for e in events(rows)]
            self.assertEqual(names, ["paid", "quan_end"])
            self.assertEqual(events(rows, "paid")[0]["data"]["reason"], "closing")
            self.assertEqual(rows[-1]["reason"], "time")
        with Workdir() as w:
            sc = {"random_customers": False, "time_left_ticks": 1, "stock": {"ca_loc": 1},
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}
            code, err, rows = run_quan(w, sc, ticks=5)
            self.assertEqual(code, 0, err)
            left = events(rows, "customer_left")[0]["data"]
            self.assertEqual((left["reason"], left["reputation"]), ("closing", 3.0))
            self.assertEqual(events(rows, "quan_end")[0]["data"]["reputation"], 3.0)


class Fixtures(unittest.TestCase):
    def test_fixture_mau_thuan_exit_2(self):
        bad = [
            {"stock": {}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]},
            {"stock": {"ca_loc": 1}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                                    "reserved": {"bong_sung": 2}}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "mon_la"}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating"}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "order_status": "assigned"}]},
            {"hand": DISH_LOC},
            {"hand": DISH_LOC, "stoves": [{"id": "B1", "state": "ready", "dish": DISH_LOC}],
             "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "order_status": "assigned"}]},
            {"stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 0}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "mood": 1}]},
            {"reputation": 9},
        ]
        with Workdir() as w:
            for sc in bad:
                code, _, _ = run_quan(w, sc, ticks=0)
                self.assertEqual(code, 2, sc)

    def test_cung_seed_ra_giong_tung_byte(self):
        with Workdir() as w:
            sc = {"stock": {"ca_loc": 3, "bong_sung": 4, "ca_linh": 6, "bong_dien_dien": 2}}
            inp = [{"tick": 0, "move": [-1, 1]}, {"tick": 200, "move": [0, 0]}]
            outs = []
            for name in ("a", "b"):
                code, err, _ = run_quan(w, sc, inp, ticks=2000, seed=7, name=name)
                self.assertEqual(code, 0, err)
                with open(w.path(f"{name}.jsonl"), "rb") as f:
                    outs.append(f.read())
            self.assertEqual(outs[0], outs[1])


if __name__ == "__main__":
    unittest.main()
