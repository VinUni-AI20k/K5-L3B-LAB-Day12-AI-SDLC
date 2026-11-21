"""Quán lát 4 (@minhthu27): nấu, bưng, phục vụ, tiền, boa, uy tín, quan_end. Hộp đen qua headless."""

import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

# Người chơi đứng cạnh bếp B1 (2,8) và bàn T1 (9,2): ta dịch chuyển bằng pos của scenario.
BASE = {"stock": {"ca_loc": 1}, "random_customers": False,
        "customers": [{"id": "C1", "table_id": "T1", "dish": "ca_loc_nuong_trui", "state": "waiting",
                       "patience_ticks": 3600}]}


def run(block, fr, ticks, w):
    sc = write_json(w.path("sc.json"), {"quan": block})
    inp = write_json(w.path("in.json"), frames(*fr))
    out = w.path("o.jsonl")
    code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
                             "--inputs", inp, "--out", out)
    assert code == 0, err
    return read_jsonl(out)


def names(rows):
    return [e["name"] for e in events(rows)]


class QuanService(unittest.TestCase):
    def test_nau_chin_bung_phuc_vu_tra_tien(self):
        with Workdir() as w:
            blk = dict(BASE, player={"pos": [2, 8]})
            fr = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                  {"tick": 400, "interact": True}, {"tick": 401, "interact": False}]
            rows = run(blk, fr, 400, w)
            self.assertEqual(names(rows)[:2], ["cook_started", "dish_ready"])
            self.assertEqual(snapshots(rows)[1]["stock"], {})

    def test_luong_day_du_den_paid(self):
        with Workdir() as w:
            # đứng ở bếp nấu, nhấc món; chuyển sang bàn bằng scenario không được -> đi bộ
            blk = dict(BASE, player={"pos": [2, 8]})
            fr = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                  {"tick": 361, "interact": True}, {"tick": 362, "interact": False, "move": [0.76, -0.65]},
                  {"tick": 500, "move": [0, 0]}, {"tick": 520, "interact": True}]
            rows = run(blk, fr, 1300, w)
            n = names(rows)
            for e in ("cook_started", "dish_ready", "dish_picked", "served", "paid"):
                self.assertIn(e, n)
            paid = events(rows, "paid")[0]["data"]
            self.assertEqual(paid["price"], 60)
            self.assertEqual(paid["tip"], 12)  # patience còn > 50%
            end = rows[-1]
            self.assertEqual(end["money"], 72)
            self.assertAlmostEqual(end["reputation"], 3.2)

    def test_khong_du_nguyen_lieu_khong_nau(self):
        with Workdir() as w:
            blk = dict(BASE, stock={}, player={"pos": [2, 8]})
            rows = run(blk, [{"tick": 0, "interact": True}], 5, w)
            self.assertNotIn("cook_started", names(rows))

    def test_khach_dang_an_tra_tien_khong_boa_khi_kien_nhan_thap(self):
        with Workdir() as w:
            c = {"id": "C1", "table_id": "T1", "dish": "goi_bong_sung", "state": "eating",
                 "patience_ticks": 100, "eat_ticks": 3}
            rows = run({"customers": [c], "random_customers": False}, [], 5, w)
            paid = events(rows, "paid")[0]["data"]
            self.assertEqual((paid["price"], paid["tip"]), (40, 0))
            self.assertAlmostEqual(rows[-1]["reputation"], 3.0)
            self.assertEqual(snapshots(rows)[-1]["customers"], [])

    def test_bep_nhan_don_cua_khach_cho(self):
        with Workdir() as w:
            blk = dict(BASE, player={"pos": [2, 8]})
            rows = run(blk, [{"tick": 0, "interact": True}], 3, w)
            self.assertIn("cook_started", names(rows))

    def test_quan_end_khi_het_gio_va_tinh_tien(self):
        with Workdir() as w:
            rows = run({"time_left_ticks": 3}, [], 10, w)
            end_ev = events(rows, "quan_end")[0]["data"]
            self.assertEqual(end_ev["reason"], "time")
            self.assertEqual(end_ev["money"], 0)

    def test_cung_seed_giong_byte(self):
        with Workdir() as w:
            blk = dict(BASE, player={"pos": [2, 8]})
            fr = [{"tick": 0, "interact": True}]
            a = run(blk, fr, 500, w)
            b = run(blk, fr, 500, w)
            self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
