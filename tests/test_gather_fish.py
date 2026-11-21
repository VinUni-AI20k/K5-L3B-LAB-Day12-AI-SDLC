"""Gather v1.1 (TICKET-02 mục 1.1): cá sinh theo seed, cá bơi, sinh thêm theo lịch — test hộp đen."""

import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json
from test_gather_lat1 import run_gather, snap_at, tuning_gather


def run_seed(w, seed, ticks=0, block=None):
    """Chạy headless gather với seed tùy ý; block=None thì không truyền --scenario."""
    args = ["--mode", "gather", "--seed", str(seed), "--ticks", str(ticks), "--out", w.path(f"s{seed}.jsonl")]
    if block is not None:
        args += ["--scenario", write_json(w.path(f"sc{seed}.json"), {"gather": block})]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path(f"s{seed}.jsonl"))


def one_fish(kind, x, d, heading):
    return {"fish": [{"id": "F1", "kind": kind, "pos": [x, d], "heading_deg": heading}]}


def f1(rows, tick):
    return [f for f in snap_at(rows, tick)["fish"] if f["id"] == "F1"][0]


SEED1 = [("F1", "ca_loc", [30.0, 10.0]), ("F2", "ca_linh", [15.0, 5.0]), ("F3", "ca_loc", [15.0, 10.0]),
         ("F4", "ca_linh", [45.0, 10.0]), ("F5", "ca_loc", [60.0, 10.0]), ("F6", "ca_loc", [75.0, 16.0]),
         ("F7", "ca_loc", [45.0, 16.0]), ("F8", "ca_keo", [45.0, 24.0])]
SEED1_HEADING = [121.406, 65.82, 149.927, 285.173, 213.344, 266.545, 289.577, 331.834]
SEED2 = [("F1", "ca_keo", [45.0, 24.0]), ("F2", "ca_loc", [45.0, 16.0]), ("F3", "ca_linh", [45.0, 10.0]),
         ("F4", "ca_keo", [60.0, 24.0]), ("F5", "ca_linh", [90.0, 10.0]), ("F6", "ca_linh", [30.0, 5.0]),
         ("F7", "ca_keo", [45.0, 27.0]), ("F8", "ca_linh", [15.0, 5.0])]


def triples(snap):
    return [(f["id"], f["kind"], f["pos"]) for f in snap["fish"]]


class FishInitial(unittest.TestCase):
    def test_f01_seed1_initial_schools(self):
        with Workdir() as w:
            s = snapshots(run_seed(w, 1))[0]
            self.assertEqual(len(s["fish"]), tuning_gather()["fish_initial"])
            self.assertEqual(triples(s), SEED1)
            for f, h in zip(s["fish"], SEED1_HEADING):
                self.assertAlmostEqual(f["heading_deg"], h, places=2)
                self.assertEqual(f["age_ticks"], 0)

    def test_f02_initial_points_valid_and_distinct(self):
        t = tuning_gather()
        with Workdir() as w:
            for seed in range(1, 11):
                fish = snapshots(run_seed(w, seed))[0]["fish"]
                self.assertEqual(len(fish), t["fish_initial"])
                pts = [tuple(f["pos"]) for f in fish]
                self.assertEqual(len(set(pts)), len(pts), seed)
                for f in fish:
                    self.assertIn(f["pos"][0], t["fish_spawn_x"])
                    self.assertIn(f["pos"][1], t["fish_spawn_depths"][f["kind"]])
                    self.assertTrue(0 <= f["heading_deg"] < 360)

    def test_f03_same_seed_same_fish_other_seed_differs(self):
        with Workdir() as w:
            a = snapshots(run_seed(w, 2))[0]["fish"]
            b = snapshots(run_seed(w, 2))[0]["fish"]
            self.assertEqual(a, b)
            self.assertEqual(triples({"fish": a}), SEED2)
            self.assertNotEqual(triples({"fish": a}), SEED1)

    def test_f04_random_fish_false_no_default_fish(self):
        with Workdir() as w:
            self.assertEqual(snap_at(run_gather(w, {"random_fish": False}, ticks=0), 0)["fish"], [])

    def test_f05_fixture_fish_replaces_initial(self):
        with Workdir() as w:
            s = snap_at(run_gather(w, {"fish": [{"id": "F1", "kind": "ca_linh", "pos": [50, 5]}]}, ticks=0), 0)
            self.assertEqual(s["fish"], [{"id": "F1", "pos": [50.0, 5.0], "kind": "ca_linh",
                                          "heading_deg": 0.0, "age_ticks": 0}])


class FishSwim(unittest.TestCase):
    def test_s01_swim_speed(self):
        with Workdir() as w:
            f = f1(run_gather(w, one_fish("ca_linh", 50, 5, 0), ticks=10), 10)
            self.assertAlmostEqual(f["pos"][0], 50 + tuning_gather()["fish_speed"] / 60 * 10, places=6)
            self.assertAlmostEqual(f["pos"][1], 5.0, places=6)
            self.assertEqual(f["age_ticks"], 10)
            self.assertEqual(f["heading_deg"], 0.0)

    def test_s02_turn_at_age_120_before_move(self):
        n = tuning_gather()["fish_turn_ticks"]
        with Workdir() as w:
            f = f1(run_gather(w, one_fish("ca_linh", 50, 5, 0), ticks=n - 1), n - 1)
            self.assertEqual((f["age_ticks"], f["heading_deg"]), (n - 1, 0.0))
            f = f1(run_gather(w, one_fish("ca_linh", 50, 5, 0), ticks=n), n)
            self.assertEqual(f["age_ticks"], n)
            self.assertAlmostEqual(f["heading_deg"], 88.473, places=2)
            self.assertAlmostEqual(f["pos"][0], 52.976, places=2)
            self.assertAlmostEqual(f["pos"][1], 5.025, places=2)

    def test_s03_reflect_at_x_edge(self):
        with Workdir() as w:
            f = f1(run_gather(w, one_fish("ca_keo", 95.99, 25, 0), ticks=1), 1)
            self.assertAlmostEqual(f["pos"][0], 95.985, places=6)
            self.assertAlmostEqual(f["pos"][1], 25.0, places=6)
            self.assertAlmostEqual(f["heading_deg"], 180.0, places=6)

    def test_s04_reflect_at_depth_band(self):
        with Workdir() as w:
            f = f1(run_gather(w, one_fish("ca_linh", 50, 11.99, 90), ticks=1), 1)
            self.assertAlmostEqual(f["pos"][0], 50.0, places=6)
            self.assertAlmostEqual(f["pos"][1], 11.985, places=6)
            self.assertAlmostEqual(f["heading_deg"], 270.0, places=6)

    def test_s05_reflect_at_corner_flips_both(self):
        with Workdir() as w:
            f = f1(run_gather(w, one_fish("ca_linh", 3.99, 3.01, 225), ticks=1), 1)
            self.assertAlmostEqual(f["pos"][0], 4.0277, places=3)
            self.assertAlmostEqual(f["pos"][1], 3.0077, places=3)
            self.assertAlmostEqual(f["heading_deg"], 45.0, places=6)

    def test_s06_catch_uses_position_before_swim(self):
        t = tuning_gather()
        block = {"player": {"pos": [20, 5]}, "nodes": [],
                 **one_fish("ca_loc", 20 + t["catch_radius"], 5, 0)}
        with Workdir() as w:
            rows = run_gather(w, block, [{"tick": 0, "catch": True}], ticks=1)
            self.assertEqual([(e["tick"], e["data"]["fish_id"]) for e in events(rows, "fish_caught")], [(1, "F1")])

    def test_s07_no_swim_on_time_end_step(self):
        with Workdir() as w:
            rows = run_gather(w, {"time_left_ticks": 1, **one_fish("ca_linh", 50, 5, 0)}, ticks=5)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "time")
            f = f1(rows, 1)
            self.assertEqual((f["pos"], f["age_ticks"]), ([50.0, 5.0], 0))

    def test_s08_random_fish_false_fixture_static(self):
        with Workdir() as w:
            rows = run_gather(w, {"random_fish": False, **one_fish("ca_linh", 50, 5, 0)}, ticks=400)
            self.assertEqual(snap_at(rows, 400)["fish"], [{"id": "F1", "pos": [50.0, 5.0], "kind": "ca_linh",
                                                          "heading_deg": 0.0, "age_ticks": 0}])
            self.assertEqual(events(rows, "fish_spawned"), [])


class FishSpawn(unittest.TestCase):
    def test_p01_default_seed1_full_shift(self):
        t = tuning_gather()
        ticks = int(round(t["duration_s"] * 60))
        with Workdir() as w:
            rows = run_seed(w, 1, ticks=ticks)
            self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "fish_spawned")], [
                (360, {"id": "F9", "kind": "ca_loc", "pos": [60.0, 10.0]}),
                (720, {"id": "F10", "kind": "ca_linh", "pos": [30.0, 10.0]}),
                (1080, {"id": "F11", "kind": "ca_linh", "pos": [30.0, 10.0]}),
                (1440, {"id": "F12", "kind": "ca_linh", "pos": [15.0, 10.0]})])
            snaps = snapshots(rows)
            self.assertEqual(len(snaps[-1]["fish"]), t["fish_max"])
            for s in snaps:
                for f in s["fish"]:
                    lo, hi = t["fish_depths"][f["kind"]]
                    self.assertTrue(t["fish_x"][0] <= f["pos"][0] <= t["fish_x"][1], (s["tick"], f))
                    self.assertTrue(lo <= f["pos"][1] <= hi, (s["tick"], f))

    def test_p02_new_fish_joins_next_step(self):
        n = tuning_gather()["fish_spawn_ticks"]
        with Workdir() as w:
            rows = run_gather(w, one_fish("ca_linh", 50, 5, 0), ticks=n + 1)
            self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "fish_spawned")],
                             [(n, {"id": "F2", "kind": "ca_loc", "pos": [30.0, 10.0]})])
            s = snap_at(rows, n)
            self.assertEqual([(f["id"], f["age_ticks"]) for f in s["fish"]], [("F1", n), ("F2", 0)])
            s = snap_at(rows, n + 1)
            self.assertEqual([(f["id"], f["age_ticks"]) for f in s["fish"]], [("F1", n + 1), ("F2", 1)])

    def test_p03_no_spawn_at_cap(self):
        t = tuning_gather()
        cap, n = t["fish_max"], t["fish_spawn_ticks"]
        fish = [{"id": f"F{i + 1}", "kind": "ca_keo", "pos": [10 + 6 * i, 25]} for i in range(cap)]
        with Workdir() as w:
            rows = run_gather(w, {"fish": fish}, ticks=n + 1)
            self.assertEqual(events(rows, "fish_spawned"), [])
            self.assertEqual(len(snap_at(rows, n + 1)["fish"]), cap)


if __name__ == "__main__":
    unittest.main()
