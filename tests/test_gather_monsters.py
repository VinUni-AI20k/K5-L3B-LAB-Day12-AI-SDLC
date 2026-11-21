"""Unit tests cho Cá Sấu Năm Chèo (M1, M2), va chạm, rơi hàng LIFO, recoil, bất tử và ngất — TV1 phụ trách."""

import json
import math
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class TestGatherMonsters(unittest.TestCase):
    def test_monster_spawns_by_day(self):
        """Ngày 1 chỉ có M1; Ngày 3 có cả M1 và M2."""
        with Workdir() as w:
            # Ngày 1 (mặc định)
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0",
                                     "--out", w.path("d1.jsonl"))
            self.assertEqual(code, 0, err)
            snap1 = snapshots(read_jsonl(w.path("d1.jsonl")))[0]
            monsters1 = snap1["monsters"]
            self.assertEqual(len(monsters1), 1)
            self.assertEqual(monsters1[0]["id"], "M1")
            self.assertEqual(monsters1[0]["pos"], [60.0, 24.0])
            self.assertEqual(monsters1[0]["state"], "patrol")

            # Ngày 3
            sc_d3 = write_json(w.path("sc_d3.json"), {"gather": {"day": 3}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc_d3, "--out", w.path("d3.jsonl"))
            self.assertEqual(code, 0, err)
            snap3 = snapshots(read_jsonl(w.path("d3.jsonl")))[0]
            monsters3 = snap3["monsters"]
            self.assertEqual(len(monsters3), 2)
            self.assertEqual([m["id"] for m in monsters3], ["M1", "M2"])

    def test_patrol_movement_between_waypoints(self):
        """M1 tuần tra 1.0 m/s giữa [60, 24] và [64, 24]."""
        with Workdir() as w:
            # 60 tick = 1 giây -> M1 đi 1.0 m từ [60, 24] tới [61, 24]
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "60",
                                     "--out", w.path("patrol.jsonl"))
            self.assertEqual(code, 0, err)
            snap = snapshots(read_jsonl(w.path("patrol.jsonl")))[-1]
            m1 = snap["monsters"][0]
            self.assertEqual(m1["id"], "M1")
            self.assertAlmostEqual(m1["pos"][0], 61.0, places=1)
            self.assertEqual(m1["pos"][1], 24.0)

    def test_detect_chase_and_exit_radius(self):
        """Người chơi ở d >= 10 và cách <= 10m -> Cá sấu rượt theo ở 3.0 m/s; thoát khi > 16m hoặc d < 10."""
        with Workdir() as w:
            # Người chơi ở [60, 15] (cách [60, 24] là 9m <= 10m, d = 15 >= 10)
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [60.0, 15.0]}
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--out", w.path("chase.jsonl"))
            self.assertEqual(code, 0, err)
            snap = snapshots(read_jsonl(w.path("chase.jsonl")))[-1]
            m1 = snap["monsters"][0]
            self.assertEqual(m1["state"], "chase")
            # M1 bơi hướng lên phía người chơi (d giảm từ 24 về phía 15)
            self.assertLess(m1["pos"][1], 24.0)

            # Người chơi ở d < 10 (ví dụ [60, 5]) -> không bị chase
            sc_shallow = write_json(w.path("sc_shallow.json"), {"gather": {
                "player": {"pos": [60.0, 5.0]}
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc_shallow, "--out", w.path("shallow.jsonl"))
            self.assertEqual(code, 0, err)
            snap_shallow = snapshots(read_jsonl(w.path("shallow.jsonl")))[-1]
            self.assertEqual(snap_shallow["monsters"][0]["state"], "patrol")

    def test_hit_reduces_hp_drops_half_lifo_and_sets_invuln(self):
        """Khoảng cách <= 1.5m ở d >= 10: mất 1 HP, rơi floor(hold/2) LIFO, bất tử 90 tick, quái vào recoil 60 tick."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [60.0, 23.5]},  # cách [60, 24] đúng 0.5m <= 1.5m
                "hold": [
                    {"id": "I1", "kind": "ca_loc", "fresh": 100},
                    {"id": "I2", "kind": "ca_linh", "fresh": 100},
                    {"id": "I3", "kind": "ca_keo", "fresh": 100},
                    {"id": "I4", "kind": "bong_dien_dien", "fresh": 100},
                ]  # 4 món
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--out", w.path("hit.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("hit.jsonl"))
            hit_evs = events(rows, "monster_hit")
            self.assertEqual(len(hit_evs), 1)
            hit_data = hit_evs[0]["data"]
            self.assertEqual(hit_data["monster_id"], "M1")
            self.assertEqual(hit_data["hp"], 2)  # 3 - 1 = 2
            # Bỏ floor(4/2) = 2 món theo LIFO (nhặt sau mất trước)
            self.assertEqual([it["id"] for it in hit_data["lost"]], ["I4", "I3"])
            self.assertEqual([it["kind"] for it in hit_data["lost"]], ["bong_dien_dien", "ca_keo"])

            snap = snapshots(rows)[-1]
            self.assertEqual(snap["player"]["hp"], 2)
            self.assertEqual(snap["player"]["invuln_ticks"], 90)
            self.assertEqual([it["id"] for it in snap["hold"]], ["I1", "I2"])

            # Quái vào recoil
            m1 = snap["monsters"][0]
            self.assertEqual(m1["state"], "recoil")
            self.assertEqual(m1["state_ticks_left"], 60)

    def test_faint_from_monster_hit(self):
        """Khi bị hit và HP chạm 0 -> ngất với cause='monster', mất sạch giỏ, kho rỗng."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [60.0, 23.5], "hp": 1},
                "hold": [
                    {"id": "I1", "kind": "ca_loc", "fresh": 100},
                    {"id": "I2", "kind": "ca_linh", "fresh": 100},
                ]
            }})
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--scenario", sc, "--inventory-out", inv, "--out", w.path("faint.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("faint.jsonl"))
            faint_evs = events(rows, "faint")
            self.assertEqual(len(faint_evs), 1)
            self.assertEqual(faint_evs[0]["data"]["cause"], "monster")
            self.assertEqual(faint_evs[0]["data"]["hp"], 0)
            self.assertEqual([it["id"] for it in faint_evs[0]["data"]["lost"]], ["I1"])

            end_evs = events(rows, "gather_end")
            self.assertEqual(len(end_evs), 1)
            self.assertEqual(end_evs[0]["data"]["reason"], "fainted")
            self.assertEqual(end_evs[0]["data"]["inventory"], {"items": []})


if __name__ == "__main__":
    unittest.main()
