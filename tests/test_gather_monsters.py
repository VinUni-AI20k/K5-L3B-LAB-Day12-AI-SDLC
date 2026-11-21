"""Tests cho Cá Sấu Năm Chèo (Phase 2: patrol, chase, recoil, monster_hit, LIFO loss, faint)."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


class GatherMonstersTests(unittest.TestCase):
    def test_spawn_by_day_m1_day1_m2_day3(self):
        with Workdir() as w:
            code, err = run_headless("--mode", "day", "--seed", "1", "--days", "1", "--ticks", "0", "--out", w.path("d1.jsonl"))
            self.assertEqual(code, 0, err)
            s1 = snapshots(read_jsonl(w.path("d1.jsonl")))[0]
            self.assertEqual([m["id"] for m in s1["monsters"]], ["M1"])

            sc = write_json(w.path("sc.json"), {"gather": {"time_left_ticks": 1}, "quan": {"time_left_ticks": 1}})
            code, err = run_headless("--mode", "day", "--seed", "1", "--days", "3", "--ticks", "1500",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("d3.jsonl"))
            self.assertEqual(code, 0, err)
            day3_snaps = [s for s in snapshots(read_jsonl(w.path("d3.jsonl"))) if s.get("day") == 3 and s.get("phase") == "gather"]
            self.assertTrue(day3_snaps)
            self.assertEqual([m["id"] for m in day3_snaps[0]["monsters"]], ["M1", "M2"])

    def test_patrol_chase_hit_lifo_recoil_and_invuln(self):
        m_cfg = tuning_gather()["monsters"]
        sp = m_cfg["species"]["ca_sau"]
        with Workdir() as w:
            # M1 khởi đầu ở [60, 24]. Đặt người chơi ở [61, 24] với 5 món trong giỏ -> trong hit_radius (1.5)
            sc = write_json(w.path("sc.json"), {"gather": {
                "hold": ["ca_loc", "ca_linh", "bong_sung", "keo_neo", "ca_keo"],
                "player": {"pos": [61, 24], "hp": 3},
                "random_fish": False,
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "70",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            hits = events(rows, "monster_hit")
            # Dù ở gần trong 70 tick, invuln_ticks=90 và recoil_ticks=60 nên chỉ trúng đúng 1 lần
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["data"]["monster_id"], "M1")
            self.assertEqual(hits[0]["data"]["hp"], 2)
            # floor(5 * 0.5) = 2 món cuối (LIFO): ca_keo, keo_neo
            self.assertEqual(hits[0]["data"]["lost"], ["ca_keo", "keo_neo"])
            snaps = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual(snaps[1]["hold"], ["ca_loc", "ca_linh", "bong_sung"])
            self.assertEqual(snaps[1]["player"]["invuln_ticks"], m_cfg["invuln_ticks"])
            m1_t1 = snaps[1]["monsters"][0]
            self.assertEqual(m1_t1["state"], "recoil")
            # Sau recoil_ticks (60), M1 quay về patrol
            m1_after = snaps[1 + sp["recoil_ticks"]]["monsters"][0]
            self.assertEqual(m1_after["state"], "patrol")

    def test_faint_by_monster_clears_hold_and_ends_gather(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "hold": ["ca_loc", "bong_sung", "keo_neo"],
                "player": {"pos": [60.5, 24], "hp": 1},
                "random_fish": False,
            }})
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--scenario", sc, "--inventory-out", inv, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            faints = events(rows, "faint")
            self.assertEqual(len(faints), 1)
            self.assertEqual(faints[0]["data"]["cause"], "monster")
            self.assertEqual(rows[-1]["reason"], "fainted")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})

    def test_chase_and_stop_when_surfacing(self):
        with Workdir() as w:
            # Đặt người chơi trong detect_radius (10m) của M1 [60, 24] -> [60, 16] (dist = 8)
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [60, 16]},
                "random_fish": False,
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            snaps = snapshots(read_jsonl(w.path("o.jsonl")))
            self.assertEqual(snaps[1]["monsters"][0]["state"], "chase")
            self.assertLess(snaps[1]["monsters"][0]["pos"][1], 24.0)

            # Ở mặt nước dù gần theo x cũng không bị rượt
            sc_surf = write_json(w.path("sc2.json"), {"gather": {
                "player": {"pos": [60, 0]},
                "random_fish": False,
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc_surf, "--snapshot-every", "1", "--out", w.path("o2.jsonl"))
            self.assertEqual(code, 0, err)
            snaps2 = snapshots(read_jsonl(w.path("o2.jsonl")))
            self.assertEqual(snaps2[1]["monsters"][0]["state"], "patrol")


if __name__ == "__main__":
    unittest.main()
