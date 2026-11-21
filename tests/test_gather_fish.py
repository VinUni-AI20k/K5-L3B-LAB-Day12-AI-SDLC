"""Phase 2 gather: cá bơi, đổi hướng, phản xạ mép và sinh theo lịch."""

import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


def run_gather(w, block, ticks, seed=1):
    scenario = write_json(w.path("scenario.json"), {"gather": block})
    out = w.path("run.jsonl")
    code, err = run_headless("--mode", "gather", "--seed", str(seed), "--ticks", str(ticks),
                             "--scenario", scenario, "--snapshot-every", "1", "--out", out)
    assert code == 0, err
    return read_jsonl(out)


def fish_at(rows, tick):
    snapshot = next(row for row in snapshots(rows) if row["tick"] == tick)
    return snapshot["fish"]


class FishMovement(unittest.TestCase):
    def test_fish_moves_at_configured_speed_and_tracks_age(self):
        with Workdir() as w:
            rows = run_gather(w, {"fish": [{"id": "F1", "kind": "ca_linh",
                                            "pos": [50, 10], "heading_deg": 0}]}, 1)
            fish = fish_at(rows, 1)[0]
            self.assertEqual(fish["pos"], [50.025, 10])
            self.assertEqual(fish["age_ticks"], 1)
            self.assertEqual(fish["heading_deg"], 0)

    def test_fish_turns_at_age_boundary_deterministically(self):
        block = {"fish": [{"id": "F1", "kind": "ca_linh", "pos": [50, 10],
                           "heading_deg": 0, "age_ticks": 119}]}
        with Workdir() as first, Workdir() as second:
            a = fish_at(run_gather(first, block, 1, seed=7), 1)[0]
            b = fish_at(run_gather(second, block, 1, seed=7), 1)[0]
            self.assertEqual(a, b)
            self.assertEqual(a["age_ticks"], 120)
            self.assertNotEqual(a["heading_deg"], 0)

    def test_fish_reflects_at_single_edge(self):
        with Workdir() as w:
            rows = run_gather(w, {"fish": [{"id": "F1", "kind": "ca_loc",
                                            "pos": [95.99, 10], "heading_deg": 0}]}, 1)
            fish = fish_at(rows, 1)[0]
            self.assertEqual(fish["pos"], [95.985, 10])
            self.assertEqual(fish["heading_deg"], 180)

    def test_fish_reflects_both_components_at_corner(self):
        with Workdir() as w:
            rows = run_gather(w, {"fish": [{"id": "F1", "kind": "ca_linh",
                                            "pos": [95.99, 11.99], "heading_deg": 45}]}, 1)
            fish = fish_at(rows, 1)[0]
            self.assertEqual(fish["pos"], [95.992, 11.992])
            self.assertEqual(fish["heading_deg"], 225)

    def test_random_fish_false_keeps_fixture_still_and_disables_spawning(self):
        with Workdir() as w:
            rows = run_gather(w, {
                "random_fish": False,
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [50, 10], "heading_deg": 90}],
            }, 360)
            fish = fish_at(rows, 360)
            self.assertEqual(len(fish), 1)
            self.assertEqual(fish[0]["pos"], [50, 10])
            self.assertEqual(fish[0]["age_ticks"], 0)
            self.assertEqual(events(rows, "fish_spawned"), [])


class FishSpawning(unittest.TestCase):
    def test_initial_population_has_eight_distinct_positions(self):
        with Workdir() as w:
            rows = run_gather(w, {}, 0)
            fish = fish_at(rows, 0)
            self.assertEqual(len(fish), 8)
            self.assertEqual(len({tuple(f["pos"]) for f in fish}), 8)
            self.assertTrue(all(f["age_ticks"] == 0 for f in fish))

    def test_first_spawn_occurs_after_movement_at_spawn_tick(self):
        with Workdir() as w:
            rows = run_gather(w, {"fish": []}, 360, seed=13)
            spawned = events(rows, "fish_spawned")
            self.assertEqual(len(spawned), 1)
            self.assertEqual(spawned[0]["tick"], 360)
            self.assertEqual(set(spawned[0]["data"]), {"id", "kind", "pos"})
            self.assertEqual(spawned[0]["data"]["id"], "F1")
            new_fish = next(f for f in fish_at(rows, 360) if f["id"] == "F1")
            self.assertEqual(new_fish["age_ticks"], 0)

    def test_population_never_exceeds_maximum(self):
        school = [{"id": f"F{i}", "kind": "ca_loc", "pos": [50, 10], "heading_deg": 0}
                  for i in range(1, 13)]
        with Workdir() as w:
            rows = run_gather(w, {"fish": school}, 360)
            self.assertEqual(len(fish_at(rows, 360)), 12)
            self.assertEqual(events(rows, "fish_spawned"), [])


if __name__ == "__main__":
    unittest.main()
