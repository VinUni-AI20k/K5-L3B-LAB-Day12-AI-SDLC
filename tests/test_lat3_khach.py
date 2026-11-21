"""Lát 3 (C): khách đến, chọn món, giữ chỗ, kiên nhẫn, bỏ đi, kiểm scenario quán. Chạy headless thật."""

import json
import unittest

from helpers import Workdir, run_headless, write_json


def inst(*kinds, fresh=100):
    """Kho cá thể v1.2: I1, I2, ... theo thứ tự kind, mặc định tươi 100 (Ticket-03 mục 1)."""
    return [{"id": f"I{i + 1}", "kind": k, "fresh": fresh} for i, k in enumerate(kinds)]


def rows(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def events(rs, name=None):
    return [r for r in rs if r["type"] == "event" and (name is None or r["name"] == name)]


def snap_at(rs, tick):
    return [r for r in rs if r["type"] == "snapshot" and r["tick"] == tick][-1]


class Lat3(unittest.TestCase):
    def quan(self, w, block, ticks, seed=1, every=1):
        sc = write_json(w.path("sc.json"), {"quan": block})
        out = w.path("out.jsonl")
        code, err = run_headless("--mode", "quan", "--seed", str(seed), "--ticks", str(ticks), "--scenario", sc,
                                 "--out", out, "--snapshot-every", str(every))
        self.assertEqual(code, 0, err)
        return rows(out)

    def test_khach_dau_tien_o_tick_120_giu_dung_cong_thuc(self):
        with Workdir() as w:
            rs = self.quan(w, {"stock": inst("ca_loc")}, 121)
            arr = events(rs, "customer_arrived")
            self.assertEqual([(e["tick"], e["data"]) for e in arr],
                             [(120, {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"})])
            c = snap_at(rs, 120)["customers"][0]
            self.assertEqual(c["reserved"], ["I1"])  # v1.2: mảng id cá thể
            self.assertEqual((c["state"], c["order_status"], c["order_tick"]), ("waiting", "reserved", 120))
            self.assertEqual(c["patience_ticks_left"], 3600)
            self.assertEqual(snap_at(rs, 121)["customers"][0]["patience_ticks_left"], 3599)

    def test_kho_rong_thi_no_dish(self):
        with Workdir() as w:
            rs = self.quan(w, {"stock": []}, 120)
            self.assertEqual([(e["tick"], e["data"]) for e in events(rs, "no_dish")], [(120, {})])
            self.assertEqual(events(rs, "customer_arrived"), [])

    def test_random_customers_false_khong_sinh_khach(self):
        with Workdir() as w:
            rs = self.quan(w, {"stock": inst("ca_loc"), "random_customers": False}, 200, every=50)
            self.assertEqual(events(rs, "customer_arrived") + events(rs, "no_dish"), [])

    def test_het_ban_trong_thi_bo_luot(self):
        # v1.1 có 4 bàn T1-T4 (Ticket-02 mục 1.3); cả 4 đã có khách dựng sẵn -> tick 120 bỏ lượt,
        # không customer_arrived, không no_dish (kho vẫn còn bong_sung đủ gọi gỏi nếu có bàn trống).
        with Workdir() as w:
            block = {"stock": inst("ca_loc", "ca_loc", "ca_loc", "ca_loc", "bong_sung", "bong_sung"),
                     "customers": [{"id": f"C{i}", "table_id": f"T{i}", "dish_id": "ca_loc_nuong_trui"}
                                   for i in range(1, 5)]}
            rs = self.quan(w, block, 120)
            self.assertEqual(events(rs, "customer_arrived"), [])  # hết bàn trống -> bỏ lượt
            self.assertEqual(events(rs, "no_dish"), [])

    def test_khach_het_kien_nhan_bo_di_tru_uy_tin(self):
        with Workdir() as w:
            block = {"stock": inst("ca_loc"), "random_customers": False,
                     "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                    "patience_ticks_left": 3}]}
            rs = self.quan(w, block, 4)
            left = events(rs, "customer_left")
            self.assertEqual([(e["tick"], e["data"]) for e in left],
                             [(3, {"order_id": "C1", "table_id": "T1", "reason": "patience", "reputation": 2.5})])
            self.assertEqual(snap_at(rs, 3)["customers"], [])

    def test_het_ca_khach_cho_roi_closing_khong_tru_uy_tin(self):
        with Workdir() as w:
            block = {"stock": inst("ca_loc"), "time_left_ticks": 5,
                     "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}
            rs = self.quan(w, block, 10)
            names = [e["name"] for e in events(rs)]
            self.assertEqual(names, ["customer_left", "quan_end"])
            self.assertEqual(events(rs, "customer_left")[0]["data"]["reason"], "closing")
            self.assertEqual(events(rs, "customer_left")[0]["data"]["reputation"], 3.0)

    def test_id_khach_moi_noi_tiep_id_dung_san(self):
        with Workdir() as w:
            block = {"stock": inst("ca_loc", "ca_loc"), "tables": [{"id": "T1", "pos": [9, 2]}],
                     "customers": [{"id": "C7", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                    "patience_ticks_left": 1}]}
            rs = self.quan(w, block, 120)
            self.assertEqual(events(rs, "customer_arrived")[0]["data"]["order_id"], "C8")

    def test_cung_seed_cung_byte(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": inst("ca_loc", "bong_sung", "bong_sung")}})
            outs = []
            for name in ("a.jsonl", "b.jsonl"):
                run_headless("--mode", "quan", "--seed", "9", "--ticks", "1200", "--scenario", sc, "--out", w.path(name))
                with open(w.path(name), "rb") as f:
                    outs.append(f.read())
            self.assertEqual(outs[0], outs[1])

    def test_scenario_mau_thuan_exit_2(self):
        bad = [
            {"stock": inst("ca_loc"), "customers": [{"id": "C1", "table_id": "T1", "dish_id": "pho"}]},
            {"stock": inst("ca_loc"), "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                                     "reserved": ["I9"]}]},  # id không có trong kho
            {"stock": inst("ca_loc"), "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                                     "reserved": {"ca_loc": 1}}]},  # dạng đếm cũ bị từ chối ở v1.2
            {"stock": [], "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating",
                            "order_status": "assigned"}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "order_status": "assigned"}]},
            {"hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
             "stoves": [{"id": "B1", "state": "ready", "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui"}}],
             "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "order_status": "assigned"}]},
        ]
        with Workdir() as w:
            for block in bad:
                sc = write_json(w.path("sc.json"), {"quan": block})
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario", sc,
                                       "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, block)

    def test_inventory_khong_du_cho_khach_giu_exit_2(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": []})
            sc = write_json(w.path("sc.json"), {"quan": {"customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}})
            code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario", sc,
                                   "--inventory", inv, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 2)

    def test_scenario_mau_cua_D_hop_le(self):
        with Workdir() as w:
            rs = self.quan(w, {"random_customers": False, "stock": inst("bong_sung", "bong_sung"), "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "reserved": ["I1", "I2"]}]}, 0)
            self.assertEqual(snap_at(rs, 0)["customers"][0]["order_status"], "reserved")

    def test_scenario_hop_le_tu_cap_reserved(self):
        with Workdir() as w:
            rs = self.quan(w, {"stock": inst("bong_sung", "bong_sung"), "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]}, 0)
            self.assertEqual(snap_at(rs, 0)["customers"][0]["reserved"], ["I1", "I2"])


if __name__ == "__main__":
    unittest.main()
