"""Lát 1 Phase 2 (BLong1501): 8 đàn đầu ca, cá bơi, phản xạ mép, sinh cá — AC-P2-10..13.

Chạy:
    $env:PYTHONPATH="tests;."; py -m unittest tests.test_gather_p2_fish -v
"""

import json
import math
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


def run_gather(w, block, inputs=(), ticks=1, seed=1, snapshot_every=1):
    sc = write_json(w.path("sc.json"), {"gather": block})
    inp = write_json(w.path("in.json"), frames(*inputs))
    code, err = run_headless(
        "--mode", "gather", "--seed", str(seed), "--ticks", str(ticks),
        "--scenario", sc, "--inputs", inp, "--snapshot-every", str(snapshot_every),
        "--out", w.path("g.jsonl"),
    )
    return code, err, (read_jsonl(w.path("g.jsonl")) if code == 0 else [])


class InitialSchools(unittest.TestCase):
    """AC-P2-10: 8 đàn đầu ca ở 8 điểm khác nhau, id F1..F8."""

    def test_default_spawns_8_distinct_schools(self):
        t = tuning_gather()
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "7", "--ticks", "0", "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            s = snapshots(read_jsonl(w.path("g.jsonl")))[0]
            fish = s["fish"]
            self.assertEqual(len(fish), t["fish_initial"])
            self.assertEqual([f["id"] for f in fish], [f"F{i}" for i in range(1, t["fish_initial"] + 1)])
            coords = [tuple(f["pos"]) for f in fish]
            self.assertEqual(len(set(coords)), len(coords))
            for f in fish:
                self.assertIn(f["kind"], t["fish_weights"])
                self.assertEqual(f["age_ticks"], 0)


class FishSwimAndReflect(unittest.TestCase):
    """AC-P2-11: cá bơi 1.5 m/s, đổi hướng tại bước bơi 120, phản xạ mép & góc."""

    def test_swim_speed_and_turn_at_120(self):
        t = tuning_gather()
        step_d = t["fish_speed"] / 60.0
        turn = t["fish_turn_ticks"]
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [2, 0]},
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20, 6], "heading_deg": 0}],
            }, ticks=turn, snapshot_every=1)
            self.assertEqual(code, 0, err)
            snaps = snapshots(rows)
            # 119 bước đầu giữ nguyên hướng 0°
            f_119 = snaps[turn - 1]["fish"][0]
            self.assertAlmostEqual(f_119["pos"][0], 20 + (turn - 1) * step_d, delta=0.01)
            self.assertAlmostEqual(f_119["pos"][1], 6.0, delta=0.01)
            self.assertEqual(f_119["age_ticks"], turn - 1)
            # Bước thứ 120 đổi hướng trước khi di chuyển
            f_120 = snaps[turn]["fish"][0]
            self.assertEqual(f_120["age_ticks"], turn)
            self.assertNotAlmostEqual(f_120["heading_deg"], 0.0, delta=0.1)

    def test_reflect_horizontal_and_vertical_edges(self):
        t = tuning_gather()
        step_d = t["fish_speed"] / 60.0
        x_lo, x_hi = t["fish_x"]
        d_lo, d_hi = t["fish_depths"]["ca_linh"]
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [2, 0]},
                "fish": [
                    {"id": "F1", "kind": "ca_linh", "pos": [x_lo + step_d * 0.25, 6], "heading_deg": 180},
                    {"id": "F2", "kind": "ca_linh", "pos": [50, d_hi - step_d * 0.25], "heading_deg": 90},
                ],
            }, ticks=1, snapshot_every=1)
            self.assertEqual(code, 0, err)
            f1, f2 = snapshots(rows)[-1]["fish"]
            # Phản xạ ngang: đi 0.25*step_d tới mép, dội lại 0.75*step_d, hướng 180 -> 0
            self.assertAlmostEqual(f1["pos"][0], x_lo + step_d * 0.75, delta=0.005)
            self.assertAlmostEqual(f1["heading_deg"] % 360, 0.0, delta=0.1)
            # Phản xạ dọc: chạm đáy cá linh d_hi, dội lên 0.75*step_d, hướng 90 -> 270
            self.assertAlmostEqual(f2["pos"][1], d_hi - step_d * 0.75, delta=0.005)
            self.assertAlmostEqual(f2["heading_deg"] % 360, 270.0, delta=0.1)

    def test_reflect_corner_flips_both_components(self):
        t = tuning_gather()
        step_d = t["fish_speed"] / 60.0
        x_lo, _ = t["fish_x"]
        d_lo, _ = t["fish_depths"]["ca_linh"]
        d_step = step_d * math.cos(math.radians(45))
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [2, 0]},
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [x_lo + d_step, d_lo + d_step], "heading_deg": 225}],
            }, ticks=1, snapshot_every=1)
            self.assertEqual(code, 0, err)
            f = snapshots(rows)[-1]["fish"][0]
            self.assertAlmostEqual(f["pos"][0], x_lo, delta=0.005)
            self.assertAlmostEqual(f["pos"][1], d_lo, delta=0.005)
            self.assertAlmostEqual(f["heading_deg"], 45.0, delta=0.1)


class FishSpawnAndOrder(unittest.TestCase):
    """AC-P2-12 & AC-P2-13: sinh tại 360·k, trần 12, bắt trước khi bơi, random_fish:false."""

    def test_spawn_at_360_and_respects_cap(self):
        t = tuning_gather()
        sp = t["fish_spawn_ticks"]
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [2, 0]},
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20, 6], "heading_deg": 0}],
            }, ticks=sp, snapshot_every=1)
            self.assertEqual(code, 0, err)
            sp_ev = events(rows, "fish_spawned")
            self.assertEqual(len(sp_ev), 1)
            self.assertEqual(sp_ev[0]["tick"], sp)
            self.assertEqual(sp_ev[0]["data"]["id"], "F2")
            f2 = [f for f in snapshots(rows)[-1]["fish"] if f["id"] == "F2"][0]
            self.assertEqual(f2["age_ticks"], 0)
            self.assertEqual(f2["pos"], sp_ev[0]["data"]["pos"])

        # Trần fish_max (12): không sinh thêm
        full_fish = [{"id": f"F{i}", "kind": "ca_linh", "pos": [15 + i * 2, 6], "heading_deg": 0}
                     for i in range(1, t["fish_max"] + 1)]
        with Workdir() as w:
            code, err, rows = run_gather(w, {"player": {"pos": [2, 0]}, "fish": full_fish}, ticks=sp, snapshot_every=sp)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "fish_spawned"), [])

    def test_catch_uses_pre_swim_position(self):
        t = tuning_gather()
        r = t["catch_radius"]
        # Cá đặt đúng mép bán kính bắt, nhưng hướng bơi ra xa (0°)
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [20, 6]},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20 + r, 10], "heading_deg": 0}],
            }, inputs=[{"tick": 0, "catch": True}], ticks=1)
            # Đặt người chơi cùng độ sâu d=10 để khoảng cách đúng bằng catch_radius
            self.assertEqual(code, 0, err)
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [20, 10]},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20 + r, 10], "heading_deg": 0}],
            }, inputs=[{"tick": 0, "catch": True}], ticks=1)
            self.assertEqual(code, 0, err)
            self.assertEqual(len(events(rows, "fish_caught")), 1)

    def test_random_fish_false_stops_swim_and_spawn(self):
        sp = tuning_gather()["fish_spawn_ticks"]
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [2, 0]},
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20, 6], "heading_deg": 0}],
                "random_fish": False,
            }, ticks=sp, snapshot_every=sp)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "fish_spawned"), [])
            f1 = snapshots(rows)[-1]["fish"][0]
            self.assertEqual(f1["pos"], [20.0, 6.0])
            self.assertEqual(f1["age_ticks"], 0)


if __name__ == "__main__":
    unittest.main()
