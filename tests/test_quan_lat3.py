"""Lát 3 (quán): khách theo lịch, chọn món, giữ chỗ nguyên liệu, kiên nhẫn, customer_left, no_dish.

Hộp đen qua headless_cmd như test_smoke_p1.py. Số liệu đọc từ game.contract.json (PRD-0 mục F, Quán).
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_quan_lat3 -v
"""

import json
import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


Q = tuning()["quan"]
MENU = tuning()["menu"]
FIRST = Q["first_customer_tick"]
INTERVAL = int(round(Q["customer_interval_s"] * 60))
PATIENCE = int(round(Q["patience_s"] * 60))
TABLES = sorted(t["id"] for t in Q["tables"])


def run_quan(w, block, ticks, seed=1, every=10):
    sc = write_json(w.path("sc.json"), {"quan": block})
    out = w.path("q.jsonl")
    code, err = run_headless("--mode", "quan", "--seed", str(seed), "--ticks", str(ticks), "--scenario", sc,
                             "--snapshot-every", str(every), "--out", out)
    return code, err, (read_jsonl(out) if code == 0 else None)


def seated_customers(n_tables, dish="ca_loc_nuong_trui"):
    """Một khách chờ ở mỗi bàn (đủ nguyên liệu giữ chỗ) để bàn kín."""
    return [{"id": f"C{i + 1}", "table_id": tid, "dish_id": dish} for i, tid in enumerate(TABLES[:n_tables])]


class Arrival(unittest.TestCase):
    def test_khach_dau_den_dung_first_customer_tick(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": {"ca_loc": 1}}, FIRST)
            self.assertEqual(code, 0, err)
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1)
            self.assertEqual(arr[0]["tick"], FIRST)
            self.assertEqual(arr[0]["data"], {"order_id": "C1", "table_id": TABLES[0], "dish_id": "ca_loc_nuong_trui"})
            c = snapshots(rows)[-1]["customers"][0]
            self.assertEqual((c["state"], c["order_status"], c["order_tick"]), ("waiting", "reserved", FIRST))
            self.assertEqual(c["reserved"], {"ca_loc": 1})
            self.assertEqual(c["patience_ticks_left"], PATIENCE)
            # giữ chỗ không trừ tồn vật lý
            self.assertEqual(snapshots(rows)[-1]["stock"], {"ca_loc": 1})
            self.assertEqual(snapshots(rows)[-1]["tables"][0]["customer_id"], "C1")

    def test_kien_nhan_giam_tu_buoc_sau(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": {"ca_loc": 1}}, FIRST + 2, every=1)
            self.assertEqual(code, 0, err)
            s = {r["tick"]: r for r in snapshots(rows)}
            self.assertEqual(s[FIRST]["customers"][0]["patience_ticks_left"], PATIENCE)
            self.assertEqual(s[FIRST + 1]["customers"][0]["patience_ticks_left"], PATIENCE - 1)
            self.assertEqual(s[FIRST + 2]["customers"][0]["patience_ticks_left"], PATIENCE - 2)

    def test_chi_chon_mon_du_nguyen_lieu(self):
        stock = {"bong_sung": 2, "ca_loc": 1}
        ok = {d for d, m in MENU.items() if all(stock.get(k, 0) >= n for k, n in m["recipe"].items())}
        for seed in range(1, 9):
            with Workdir() as w:
                code, err, rows = run_quan(w, {"stock": stock}, FIRST, seed=seed)
                self.assertEqual(code, 0, err)
                self.assertIn(events(rows, "customer_arrived")[0]["data"]["dish_id"], ok, seed)

    def test_khong_du_mon_phat_no_dish(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {}, FIRST)
            self.assertEqual(code, 0, err)
            nd = events(rows, "no_dish")
            self.assertEqual([(e["tick"], e["data"]) for e in nd], [(FIRST, {})])
            self.assertEqual(events(rows, "customer_arrived"), [])

    def test_giu_cho_lam_mon_khong_con_kha_dung(self):
        """Kho chỉ đủ 1 suất: khách đầu giữ hết, lượt sau (nếu có bàn trống) phải no_dish."""
        if len(TABLES) < 2:
            self.skipTest("cần >= 2 bàn")
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": {"ca_loc": 1}}, FIRST + INTERVAL)
            self.assertEqual(code, 0, err)
            self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [FIRST + INTERVAL])

    def test_het_ban_thi_bo_luot(self):
        with Workdir() as w:
            block = {"stock": {"ca_loc": len(TABLES) + 1}, "customers": seated_customers(len(TABLES))}
            code, err, rows = run_quan(w, block, FIRST)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual(events(rows, "no_dish"), [])

    def test_random_customers_false_tat_khach_tu_sinh(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": {"ca_loc": 3}, "random_customers": False}, FIRST + INTERVAL)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "customer_arrived") + events(rows, "no_dish"), [])


class Leaving(unittest.TestCase):
    def test_het_kien_nhan_roi_ban_tru_uy_tin_roi_khach_moi_vao(self):
        leave = FIRST + PATIENCE
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": {"ca_loc": 1}}, leave)
            self.assertEqual(code, 0, err)
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1)
            self.assertEqual(left[0]["tick"], leave)
            want_rep = max(Q["reputation_min"], Q["reputation_initial"] + Q["left_reputation_delta"])
            self.assertEqual(left[0]["data"], {"order_id": "C1", "table_id": TABLES[0], "reason": "patience",
                                               "reputation": want_rep})
            self.assertAlmostEqual(snapshots(rows)[-1]["reputation"], want_rep, places=2)
            if (leave - FIRST) % INTERVAL == 0:
                # rời bàn (bước 3) trước lượt khách mới (bước 4) trong cùng tick: phần giữ đã nhả, bàn đã trống
                same = [r for r in rows if r["type"] == "event" and r["tick"] == leave]
                names = [r["name"] for r in same]
                self.assertLess(names.index("customer_left"), names.index("customer_arrived"))
                arr = events(rows, "customer_arrived")[-1]["data"]
                self.assertEqual((arr["order_id"], arr["table_id"]), ("C2", TABLES[0]))

    def test_dong_ca_khach_cho_roi_closing_khong_tru_uy_tin(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": {"ca_loc": 1}, "time_left_ticks": FIRST + 30}, FIRST + 100)
            self.assertEqual(code, 0, err)
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1)
            self.assertEqual(left[0]["tick"], FIRST + 30)
            self.assertEqual(left[0]["data"]["reason"], "closing")
            self.assertEqual(left[0]["data"]["reputation"], Q["reputation_initial"])
            names = [r["name"] for r in rows if r["type"] == "event" and r["tick"] == FIRST + 30]
            self.assertEqual(names[-1], "quan_end")
            self.assertEqual(snapshots(rows)[-1]["customers"], [])
            self.assertEqual(rows[-1]["reason"], "time")

    def test_uy_tin_kep_duoi(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": {"ca_loc": 1}, "reputation": Q["reputation_min"]}, FIRST + PATIENCE)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "customer_left")[0]["data"]["reputation"], Q["reputation_min"])


class ScenarioCustomers(unittest.TestCase):
    def test_khach_fixture_mac_dinh_va_suy_ra_giu_cho(self):
        with Workdir() as w:
            block = {"stock": {"ca_loc": 1}, "random_customers": False,
                     "customers": [{"id": "C7", "table_id": TABLES[0], "dish_id": "ca_loc_nuong_trui"}]}
            code, err, rows = run_quan(w, block, 0)
            self.assertEqual(code, 0, err)
            c = snapshots(rows)[0]["customers"][0]
            self.assertEqual({k: c[k] for k in ("id", "state", "order_tick", "patience_ticks_left", "order_status",
                                                "reserved")},
                             {"id": "C7", "state": "waiting", "order_tick": 0, "patience_ticks_left": PATIENCE,
                              "order_status": "reserved", "reserved": {"ca_loc": 1}})

    def test_id_khach_moi_noi_sau_id_fixture(self):
        if len(TABLES) < 2:
            self.skipTest("cần >= 2 bàn")
        with Workdir() as w:
            block = {"stock": {"ca_loc": 2},
                     "customers": [{"id": "C7", "table_id": TABLES[0], "dish_id": "ca_loc_nuong_trui"}]}
            code, err, rows = run_quan(w, block, FIRST)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "customer_arrived")[0]["data"]["order_id"], "C8")

    def test_fixture_mau_thuan_exit_2(self):
        bad = [
            {"stock": {}, "customers": [{"id": "C1", "table_id": TABLES[0], "dish_id": "ca_loc_nuong_trui"}]},
            {"stock": {"ca_loc": 1}, "customers": [{"id": "C1", "table_id": TABLES[0]}]},
            {"stock": {"ca_loc": 1}, "customers": [{"id": "C1", "table_id": TABLES[0], "dish_id": "pho_bo"}]},
            {"stock": {"ca_loc": 2}, "customers": [{"id": "C1", "table_id": TABLES[0],
                                                    "dish_id": "ca_loc_nuong_trui", "reserved": {"ca_loc": 2}}]},
            {"stock": {"ca_loc": 1}, "customers": [{"id": "C1", "table_id": TABLES[0],
                                                    "dish_id": "ca_loc_nuong_trui", "mood": "vui"}]},
            {"stock": {"ca_loc": 1}, "customers": [{"id": "C1", "table_id": TABLES[0],
                                                    "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": -1}]},
        ]
        for block in bad:
            with Workdir() as w:
                code, _, _ = run_quan(w, block, 0)
                self.assertEqual(code, 2, block)


if __name__ == "__main__":
    unittest.main()
