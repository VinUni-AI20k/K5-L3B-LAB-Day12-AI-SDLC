"""Test lát 1 (hộp đen qua headless_cmd): dive/surface, oxy, ngạt, ngất, giỏ LIFO.

Nguồn luật: PRD-0 mục E (event) và mục F "Gather". Preset: surface_depth = 0.5,
oxygen_max_s = 30 (1800 tick), oxygen_refill_per_tick = 6, choke_interval_ticks = 60,
hp_max = 3, swim_speed = 4, ramp_max_ticks = 6.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_gather_slice1 -v
"""

import json
import os
import unittest

from helpers import (Workdir, close, events, frames, read_jsonl, run_headless,
                     snapshots, write_json)
from helpers import counts, items, kinds  # v1.2 kho cá thể


class Oxygen(unittest.TestCase):
    def test_dive_surface_events_va_pos(self):
        """Lặn xuống rồi nổi lên: đúng một dive, một surface, data pos khớp snapshot cùng tick."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [50, 0.3]},
                                                           "fish": [], "random_fish": False}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, 1]},
                                                       {"tick": 40, "move": [0, -1]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "100",
                                     "--scenario", sc, "--inputs", inp,
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            dive = events(rows, "dive")
            surf = events(rows, "surface")
            self.assertEqual(len(dive), 1, dive)
            self.assertEqual(len(surf), 1, surf)
            self.assertLess(dive[0]["tick"], surf[0]["tick"])
            for ev in (*dive, *surf):
                self.assertIn("pos", ev["data"], ev)
                snap = {r["tick"]: r for r in snapshots(rows)}[ev["tick"]]
                self.assertEqual(ev["data"]["pos"], snap["player"]["pos"], ev)
            # pos lúc dive phải thật sự dưới nước, lúc surface ở mặt nước
            self.assertGreater(dive[0]["data"]["pos"][1], 0.5, dive)
            self.assertTrue(surf[0]["data"]["pos"][1] <= 0.5, surf)

    def test_oxygen_empty_va_choke_dung_tick(self):
        """oxy = 5, dưới nước: oxygen_empty tick 5 (vừa chạm 0), choke tick 64 (= 5 + 59), đếm reset."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [50, 10], "oxygen_ticks": 5},
                                                           "fish": [], "random_fish": False}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "70",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            empty = events(rows, "oxygen_empty")
            self.assertEqual(len(empty), 1, empty)
            self.assertEqual(empty[0]["tick"], 5)
            self.assertEqual(empty[0]["data"], {"oxygen_ticks": 0})
            choke = events(rows, "choke")
            self.assertEqual(len(choke), 1, choke)
            self.assertEqual(choke[0]["tick"], 64, choke)
            self.assertEqual(choke[0]["data"], {"hp": 2}, choke)
            s = {r["tick"]: r for r in snapshots(rows)}
            self.assertEqual(s[64]["player"]["hp"], 2)
            self.assertEqual(s[64]["player"]["zero_oxy_ticks"], 0, "đủ 60 tick thì đặt lại đếm về 0")
            self.assertEqual(s[65]["player"]["zero_oxy_ticks"], 1, "đếm lại từ đầu nếu vẫn dưới nước")
            self.assertEqual(rows[-1]["reason"], "tick_limit")
            self.assertEqual(rows[-1]["state"], "playing")
            self.assertEqual(len(events(rows, "faint")), 0)

    def test_noi_hoi_oxy_va_reset_dem(self):
        """Ở mặt nước: hồi oxygen_refill_per_tick/tick kẹp max, zero_oxy_ticks giữ 0."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [50, 0], "oxygen_ticks": 100},
                                                           "fish": [], "random_fish": False}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            s = {r["tick"]: r for r in snapshots(read_jsonl(w.path("o.jsonl")))}
            self.assertEqual(s[10]["player"]["oxygen_ticks"], 160)  # 100 + 10 × 6
            self.assertEqual(s[10]["player"]["zero_oxy_ticks"], 0)
            self.assertEqual(len(events(read_jsonl(w.path("o.jsonl")), "oxygen_empty")), 0)

    def test_noi_dung_buoc_dang_le_ngat_khong_choke(self):
        """Nổi lên đúng bước mà đếm ngạt sẽ đủ 60: hồi oxy, không choke, không trừ Máu."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [50, 0.51], "oxygen_ticks": 0,
                                                                      "zero_oxy_ticks": 59, "hp": 3},
                                                           "fish": [], "random_fish": False}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, -1]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--scenario", sc, "--inputs", inp,
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(len(events(rows, "choke")), 0, "nổi kịp thì không ngạt")
            self.assertEqual(len(events(rows, "faint")), 0)
            surf = events(rows, "surface")
            self.assertEqual(len(surf), 1, surf)
            self.assertEqual(surf[0]["tick"], 1)
            s = {r["tick"]: r for r in snapshots(rows)}
            self.assertEqual(s[1]["player"]["hp"], 3)
            self.assertEqual(s[1]["player"]["oxygen_ticks"], 6, "hồi oxy ngay bước nổi lên")
            self.assertEqual(s[1]["player"]["zero_oxy_ticks"], 0)

    def test_ngat_bo_gio_lifo_va_kho_rong(self):
        """Máu 1, oxy 0 dưới nước: choke tick 60 -> faint, giỏ bỏ theo LIFO, kho rỗng, dừng ngay."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [50, 10], "oxygen_ticks": 0, "hp": 1},
                                                           "hold": items(*["ca_loc", "bong_sung", "ca_linh"]),
                                                           "fish": [], "random_fish": False}})
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "70",
                                     "--scenario", sc, "--inventory-out", inv,
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            choke = events(rows, "choke")
            self.assertEqual(choke[0]["tick"], 60)
            self.assertEqual(choke[0]["data"], {"hp": 0})
            faint = events(rows, "faint")
            self.assertEqual(len(faint), 1, faint)
            self.assertEqual(faint[0]["tick"], 60)
            self.assertEqual({**faint[0]["data"], "lost": kinds(faint[0]["data"]["lost"])}, {"cause": "choke", "hp": 0,
                                                "lost": ["ca_linh", "bong_sung", "ca_loc"]},
                             "lost theo thứ tự bỏ LIFO (nhặt sau bỏ trước)")
            ends = events(rows, "gather_end")
            self.assertEqual(len(ends), 1)
            self.assertEqual(ends[0]["tick"], 60)
            self.assertEqual(ends[0]["data"], {"reason": "fainted", "inventory": {"items": []}})
            last = snapshots(rows)[-1]
            self.assertEqual(last["state"], "finished")
            self.assertEqual(last["player"]["hp"], 0)
            self.assertEqual(kinds(last["hold"]), [])
            self.assertEqual(last["hold_count"], 0)
            self.assertEqual(rows[-1]["reason"], "fainted")
            self.assertEqual(rows[-1]["state"], "finished")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

    def test_ngat_thang_truoc_het_gio(self):
        """Ngạt đúng bước ca cũng hết giờ: faint thắng, chỉ một gather_end, không reason time."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [50, 10], "oxygen_ticks": 0, "hp": 1},
                                                           "hold": items(*["ca_loc"]), "time_left_ticks": 60,
                                                           "fish": [], "random_fish": False}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "70",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            ends = events(rows, "gather_end")
            self.assertEqual(len(ends), 1, ends)
            self.assertEqual(ends[0]["data"]["reason"], "fainted", "ngạt xử lý trước, dừng bước ngay")
            self.assertEqual(rows[-1]["reason"], "fainted")
            self.assertEqual(rows[-1]["state"], "finished")


if __name__ == "__main__":
    unittest.main()
