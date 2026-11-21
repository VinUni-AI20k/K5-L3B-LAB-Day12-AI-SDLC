"""Unit tests cho Lát 1 (Oxy, ngạt, Máu, ngất, lặn/nổi, giỏ LIFO) — TV1 phụ trách."""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class TestGatherLat1(unittest.TestCase):
    def test_dive_and_surface_events(self):
        """Bơi từ mặt nước xuống phát dive; bơi từ dưới nước lên phát surface."""
        with Workdir() as w:
            # Bơi xuống từ mặt nước
            inp_down = write_json(w.path("down.json"), frames({"tick": 0, "move": [0, 1]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "30",
                                     "--inputs", inp_down, "--out", w.path("down.jsonl"))
            self.assertEqual(code, 0, err)
            evs = events(read_jsonl(w.path("down.jsonl")), "dive")
            self.assertEqual(len(evs), 1)
            self.assertIn("pos", evs[0]["data"])

            # Bơi lên từ dưới nước
            sc_under = write_json(w.path("under.json"), {"gather": {"player": {"pos": [20, 1.0]}}})
            inp_up = write_json(w.path("up.json"), frames({"tick": 0, "move": [0, -1]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "30",
                                     "--scenario", sc_under, "--inputs", inp_up, "--out", w.path("up.jsonl"))
            self.assertEqual(code, 0, err)
            evs_surf = events(read_jsonl(w.path("up.jsonl")), "surface")
            self.assertEqual(len(evs_surf), 1)
            self.assertIn("pos", evs_surf[0]["data"])

    def test_oxygen_consumption_and_empty_event(self):
        """Dưới nước: trừ 1 oxy/tick, chạm 0 phát oxygen_empty."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5], "oxygen_ticks": 2}
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "3",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("out.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("out.jsonl"))
            snaps = snapshots(rows)
            # tick 0: 2
            self.assertEqual(snaps[0]["player"]["oxygen_ticks"], 2)
            # tick 1: 1
            self.assertEqual(snaps[1]["player"]["oxygen_ticks"], 1)
            # tick 2: 0
            self.assertEqual(snaps[2]["player"]["oxygen_ticks"], 0)
            # Sự kiện oxygen_empty xuất hiện ở tick 2
            empty_evs = events(rows, "oxygen_empty")
            self.assertEqual(len(empty_evs), 1)
            self.assertEqual(empty_evs[0]["tick"], 2)

    def test_oxygen_refill_at_surface(self):
        """Ở mặt nước: hồi oxygen_refill_per_tick (6 tick/tick), kẹp tối đa."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 0], "oxygen_ticks": 100}
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("out.jsonl"))
            self.assertEqual(code, 0, err)
            snaps = snapshots(read_jsonl(w.path("out.jsonl")))
            # tick 1: 100 + 6 = 106
            self.assertEqual(snaps[1]["player"]["oxygen_ticks"], 106)

    def test_choke_decreases_hp(self):
        """Oxy = 0 dưới nước: đếm 60 tick ngạt thì trừ 1 HP, phát choke."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 3}
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("out.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("out.jsonl"))
            choke_evs = events(rows, "choke")
            self.assertEqual(len(choke_evs), 1)
            self.assertEqual(choke_evs[0]["data"]["hp"], 2)
            snap1 = snapshots(rows)[1]
            self.assertEqual(snap1["player"]["hp"], 2)
            self.assertEqual(snap1["player"]["zero_oxy_ticks"], 0)

    def test_faint_empties_hold_and_writes_empty_inventory(self):
        """Máu về 0: ngất (faint), gather_end(fainted), giỏ bị xoá sạch, xuất kho rỗng."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                "hold": [
                    {"id": "I1", "kind": "ca_loc", "fresh": 100},
                    {"id": "I2", "kind": "bong_sung", "fresh": 100},
                ]
            }})
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--scenario", sc, "--inventory-out", inv, "--out", w.path("out.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("out.jsonl"))
            # Event faint và gather_end
            faint_evs = events(rows, "faint")
            self.assertEqual(len(faint_evs), 1)
            self.assertEqual([it["id"] for it in faint_evs[0]["data"]["lost"]], ["I2", "I1"])
            end_evs = events(rows, "gather_end")
            self.assertEqual(len(end_evs), 1)
            self.assertEqual(end_evs[0]["data"]["reason"], "fainted")
            self.assertEqual(end_evs[0]["data"]["inventory"], {"items": []})
            # File kho xuất ra rỗng
            self.assertTrue(os.path.exists(inv))
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})


if __name__ == "__main__":
    unittest.main()
