"""Lát 1 Phase 3 (Contract v1.2): giỏ cá thể, hao tươi 0.5/s, spoiled < 30, LIFO, bàn giao file.

Chạy: python -m unittest discover -s tests
"""

import json
import os
import unittest

from helpers import (Workdir, close, events, frames, items, kinds, read_jsonl, run_headless,
                     snapshots, write_json)

BASE = {"random_fish": False, "monsters": []}


def run_gather(w, block, ticks, inputs=None, inv_out=None, every=1):
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks),
            "--scenario", write_json(w.path("sc.json"), {"gather": {**BASE, **block}}),
            "--snapshot-every", str(every), "--out", w.path("o.jsonl")]
    if inputs:
        args += ["--inputs", write_json(w.path("in.json"), inputs)]
    if inv_out:
        args += ["--inventory-out", inv_out]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path("o.jsonl")) if code == 0 else [])


def at(rows, tick):
    return [s for s in snapshots(rows) if s["tick"] == tick][-1]


class Spoil(unittest.TestCase):
    def test_fixture_de_bai_fresh_30_uon_o_tick_1(self):
        """Fixture đề bài: fresh đúng 30, một bước không input -> spoiled ở tick 1."""
        with Workdir() as w:
            code, err, rows = run_gather(w, {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}]}, 1)
            self.assertEqual(code, 0, err)
            sp = events(rows, "spoiled")
            self.assertEqual(len(sp), 1, sp)
            self.assertEqual(sp[0]["tick"], 1)
            self.assertEqual(sp[0]["data"], {"item_id": "I1", "kind": "ca_linh", "location": "hold"})
            self.assertEqual(at(rows, 1)["hold_count"], 1, "hàng ươn vẫn chiếm ô")

    def test_nguong_chinh_xac_khong_lam_tron(self):
        """30.009 - 1/120 = 30.00067 (chưa ươn); 30.008 - 1/120 = 29.99967 (ươn)."""
        with Workdir() as w:
            code, err, rows = run_gather(w, {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 30.009},
                                                      {"id": "I2", "kind": "ca_loc", "fresh": 30.008}]}, 1)
            self.assertEqual(code, 0, err)
            self.assertEqual([e["data"]["item_id"] for e in events(rows, "spoiled")], ["I2"])

    def test_spoiled_mot_lan_va_theo_id(self):
        """Nhiều cá thể cùng vượt ngưỡng: phát theo id (I2 trước I10), mỗi cá thể đúng một lần."""
        with Workdir() as w:
            hold = [{"id": "I10", "kind": "ca_loc", "fresh": 30},
                    {"id": "I2", "kind": "bong_sung", "fresh": 30}]
            code, err, rows = run_gather(w, {"hold": hold}, 120, every=120)
            self.assertEqual(code, 0, err)
            sp = events(rows, "spoiled")
            self.assertEqual([(e["tick"], e["data"]["item_id"]) for e in sp], [(1, "I2"), (1, "I10")])


class Decay(unittest.TestCase):
    def test_hao_0_5_moi_giay_va_kep_day_0(self):
        with Workdir() as w:
            code, err, rows = run_gather(w, {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100},
                                                      {"id": "I2", "kind": "ca_loc", "fresh": 0.004}]}, 60)
            self.assertEqual(code, 0, err)
            h = {i["id"]: i["fresh"] for i in at(rows, 60)["hold"]}
            self.assertTrue(close(h["I1"], 99.5, 0.01), h)
            self.assertEqual(h["I2"], 0, "kẹp đáy 0")

    def test_hang_moi_fresh_100_hao_tu_buoc_sau_va_id_noi_tiep(self):
        """Hái ở bước 1 -> fresh 100 ở tick 1, 100 - 1/120 ở tick 2; id nối tiếp id lớn nhất đã nạp."""
        with Workdir() as w:
            code, err, rows = run_gather(w, {"player": {"pos": [12, 0]},
                                             "hold": [{"id": "I5", "kind": "ca_loc", "fresh": 100}]},
                                         2, inputs=frames({"tick": 0, "interact": True}))
            self.assertEqual(code, 0, err)
            new = at(rows, 1)["hold"][-1]
            self.assertEqual((new["id"], new["kind"], new["fresh"]), ("I6", "bong_dien_dien", 100))
            self.assertTrue(close(at(rows, 2)["hold"][-1]["fresh"], 100 - 1 / 120, 0.01))


class Faint(unittest.TestCase):
    def test_ngat_bo_toan_bo_lifo_roi_faint(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            code, err, rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0,
                                                        "zero_oxy_ticks": 59, "hp": 1},
                                             "hold": items("ca_loc", "bong_sung", "ca_linh")},
                                         5, inv_out=inv)
            self.assertEqual(code, 0, err)
            lost = events(rows, "faint")[0]["data"]["lost"]
            self.assertEqual([i["id"] for i in lost], ["I3", "I2", "I1"], "LIFO theo thứ tự vào giỏ")
            self.assertEqual(kinds(lost), ["ca_linh", "bong_sung", "ca_loc"])
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})


class Scenario(unittest.TestCase):
    def test_hold_sai_schema_ma_2(self):
        bad = [["ca_loc"],                                                    # kho cũ dạng chuỗi
               [{"id": "I1", "kind": "ca_loc"}],                              # thiếu fresh
               [{"id": "I1", "kind": "ca_la", "fresh": 50}],                  # kind lạ
               [{"id": "I1", "kind": "ca_loc", "fresh": 100.5}],              # ngoài miền
               [{"id": "I1", "kind": "ca_loc", "fresh": -1}],
               [{"id": "", "kind": "ca_loc", "fresh": 50}],                   # id rỗng
               [{"id": "I1", "kind": "ca_loc", "fresh": 50}, {"id": "I1", "kind": "ca_linh", "fresh": 50}]]
        for hold in bad:
            with Workdir() as w:
                code, _, _ = run_gather(w, {"hold": hold}, 0)
                self.assertEqual(code, 2, hold)


class Handoff(unittest.TestCase):
    def test_smoke_ban_giao_file_v1_2(self):
        """Smoke đề bài: fresh 100, interact frame 0 -> docked tick 1; file giữ đúng 100 - 1/120."""
        with Workdir() as w:
            inv = w.path("inv.json")
            code, err, rows = run_gather(w, {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}]}, 5,
                                         inputs=frames({"tick": 0, "interact": True}), inv_out=inv)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "gather_end")[0]["tick"], 1)
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved, {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100 - 1 / 120}]})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)

    def test_file_kho_dem_cu_ma_2(self):
        with Workdir() as w:
            for bad in ({"items": {"ca_loc": 1}}, {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 101}]}):
                inv = write_json(w.path("inv.json"), bad)
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                       "--out", w.path("q.jsonl"))
                self.assertEqual(code, 2, bad)

    def test_tick_limit_truoc_gather_end_khong_ghi_file(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            code, err, _ = run_gather(w, {"hold": items("ca_loc")}, 3, inv_out=inv)
            self.assertEqual(code, 0, err)
            self.assertFalse(os.path.exists(inv))


if __name__ == "__main__":
    unittest.main()
