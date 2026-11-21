import math
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


def build_sim(scenario=None, seed=1):
    return GatherSim(load_contract()["tuning"], scenario or {}, Streams(seed), IdAllocator())


def idle():
    return InputState((0.0, 0.0), {}, set())


def press(button):
    return InputState((0.0, 0.0), {button: True}, {button})


class GatherFish(unittest.TestCase):
    def test_initial_schools_use_eight_distinct_species_valid_points(self):
        sim = build_sim()

        self.assertEqual(len(sim.fish), 8)
        self.assertEqual([fish["id"] for fish in sim.fish], [f"F{i}" for i in range(1, 9)])
        self.assertEqual(len({tuple(fish["pos"]) for fish in sim.fish}), 8)
        for fish in sim.fish:
            low, high = sim.t["fish_depths"][fish["kind"]]
            self.assertLessEqual(low, fish["pos"][1])
            self.assertLessEqual(fish["pos"][1], high)
            self.assertEqual(fish["age_ticks"], 0)

    def test_school_moves_at_configured_speed_and_turns_on_120th_swim_step(self):
        sim = build_sim({
            "fish": [{"id": "F7", "kind": "ca_linh", "pos": [20, 6],
                      "heading_deg": 0, "age_ticks": 0}],
        })
        for _ in range(60):
            sim.step(idle())
        self.assertAlmostEqual(sim.fish[0]["pos"][0], 21.5)
        self.assertAlmostEqual(sim.fish[0]["pos"][1], 6)
        self.assertEqual(sim.fish[0]["age_ticks"], 60)

        turning = build_sim({
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20, 6],
                      "heading_deg": 0, "age_ticks": 119}],
        }, seed=23)
        expected = Streams(23).get("fish_turn").uniform(0.0, 360.0)
        turning.step(idle())
        self.assertEqual(turning.fish[0]["age_ticks"], 120)
        self.assertEqual(turning.fish[0]["heading_deg"], expected)

    def test_reflection_preserves_remaining_distance_at_edges_and_corner(self):
        fish = {"pos": [95.5, 6.0], "heading_deg": 0.0}
        GatherSim._move_fish_with_reflection(fish, 1.0, [4.0, 96.0], [3.0, 12.0])
        self.assertAlmostEqual(fish["pos"][0], 95.5)
        self.assertAlmostEqual(fish["pos"][1], 6.0)
        self.assertAlmostEqual(fish["heading_deg"], 180.0)

        corner = {"pos": [95.5, 11.5], "heading_deg": 45.0}
        GatherSim._move_fish_with_reflection(corner, 1.0, [4.0, 96.0], [3.0, 12.0])
        self.assertAlmostEqual(corner["pos"][0], 96.0 - math.cos(math.radians(45)) * (1.0 - math.sqrt(0.5)))
        self.assertAlmostEqual(corner["pos"][1], 12.0 - math.sin(math.radians(45)) * (1.0 - math.sqrt(0.5)))
        self.assertAlmostEqual(corner["heading_deg"], 225.0)

    def test_catch_uses_pre_movement_position_and_removes_school(self):
        sim = build_sim({
            "player": {"pos": [20, 10]},
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [22, 10], "heading_deg": 0}],
        })

        events_out = sim.step(press("catch"))

        self.assertEqual([name for name, _ in events_out if name == "fish_caught"], ["fish_caught"])
        self.assertEqual(sim.hold, [
            {"id": f"I{i}", "kind": "ca_linh", "fresh": sim.initial_fresh}
            for i in range(1, 4)
        ])
        self.assertEqual(sim.fish, [])

    def test_new_species_yield_and_new_node_kind(self):
        catch_sim = build_sim({
            "player": {"pos": [20, 23]},
            "fish": [{"id": "F1", "kind": "ca_keo", "pos": [20, 25]}],
        })
        caught = catch_sim.step(press("catch"))
        self.assertEqual(caught[0][1]["yield"], 2)
        self.assertEqual(catch_sim.hold, [
            {"id": "I1", "kind": "ca_keo", "fresh": catch_sim.initial_fresh},
            {"id": "I2", "kind": "ca_keo", "fresh": catch_sim.initial_fresh},
        ])

        gather_sim = build_sim({"player": {"pos": [76, 0]}})
        gathered = gather_sim.step(press("interact"))
        self.assertEqual(gathered[0][0], "gather")
        self.assertEqual(gathered[0][1]["kind"], "keo_neo")
        self.assertEqual(gather_sim.inventory_items(), [
            {"id": "I1", "kind": "keo_neo", "fresh": 100},
        ])

    def test_spawns_at_360_after_swimming_and_new_school_moves_next_tick(self):
        first = build_sim(seed=31)
        second = build_sim(seed=31)
        spawn_events = []
        for _ in range(360):
            spawn_events.extend(first.step(idle()))
            second.step(idle())

        spawned = [data for name, data in spawn_events if name == "fish_spawned"]
        self.assertEqual(len(spawned), 1)
        self.assertEqual(set(spawned[0]), {"id", "kind", "pos"})
        self.assertEqual(spawned[0]["id"], "F9")
        self.assertEqual(len(first.fish), 9)
        new_school = next(fish for fish in first.fish if fish["id"] == "F9")
        self.assertEqual(new_school["age_ticks"], 0)
        self.assertEqual(first.snapshot()["fish"], second.snapshot()["fish"])

        old_pos = list(new_school["pos"])
        first.step(idle())
        self.assertEqual(new_school["age_ticks"], 1)
        self.assertNotEqual(new_school["pos"], old_pos)

    def test_spawn_respects_capacity_and_random_fish_false_freezes_fixtures(self):
        fixture = build_sim({
            "fish": [{"id": "F30", "kind": "ca_linh", "pos": [20, 6]}],
        }, seed=8)
        fixture.phase_tick = 359
        spawned = fixture.step(idle())
        self.assertEqual(next(data["id"] for name, data in spawned if name == "fish_spawned"), "F31")

        full = build_sim(seed=4)
        for i in range(9, 13):
            full.fish.append({
                "id": f"F{i}",
                "kind": "ca_keo",
                "pos": [10.0 + i, 25.0],
                "heading_deg": 0.0,
                "age_ticks": 0,
            })
            full.ids.reserve(f"F{i}")
        full.phase_tick = 359
        self.assertNotIn("fish_spawned", [name for name, _ in full.step(idle())])
        self.assertEqual(len(full.fish), 12)

        fixture = build_sim({
            "random_fish": False,
            "fish": [{"id": "F20", "kind": "ca_keo", "pos": [20, 25],
                      "heading_deg": 45, "age_ticks": 5}],
        })
        initial = list(fixture.fish[0]["pos"])
        for _ in range(360):
            self.assertNotIn("fish_spawned", [name for name, _ in fixture.step(idle())])
        self.assertEqual(fixture.fish[0]["pos"], initial)
        self.assertEqual(fixture.fish[0]["age_ticks"], 5)

    def test_scenario_age_ticks_and_species_bands_are_validated(self):
        with Workdir() as work:
            scenario = write_json(work.path("gather.json"), {
                "gather": {
                    "fish": [{"id": "F30", "kind": "ca_keo", "pos": [20, 25],
                              "heading_deg": 90, "age_ticks": 119}],
                }
            })
            out = work.path("valid.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "5", "--ticks", "0",
                                     "--scenario", scenario, "--out", out)
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(out))[0]["fish"][0]["age_ticks"], 119)

            for fish in (
                {"id": "F1", "kind": "ca_keo", "pos": [20, 10]},
                {"id": "F1", "kind": "ca_linh", "pos": [20, 6], "age_ticks": -1},
            ):
                bad = write_json(work.path("bad.json"), {"gather": {"fish": [fish]}})
                self.assertEqual(run_headless("--mode", "gather", "--seed", "5", "--ticks", "0",
                                              "--scenario", bad, "--out", work.path("bad.jsonl"))[0], 2)

    def test_jsonl_spawn_event_and_same_seed_are_byte_deterministic(self):
        with Workdir() as work:
            outputs = [work.path("a.jsonl"), work.path("b.jsonl")]
            for output in outputs:
                code, err = run_headless("--mode", "gather", "--seed", "42", "--ticks", "720",
                                         "--snapshot-every", "360", "--out", output)
                self.assertEqual(code, 0, err)
            with open(outputs[0], "rb") as a, open(outputs[1], "rb") as b:
                self.assertEqual(a.read(), b.read())
            rows = read_jsonl(outputs[0])
            spawned = events(rows, "fish_spawned")
            self.assertEqual([row["tick"] for row in spawned], [360, 720])
            snapshot_360 = next(row for row in snapshots(rows) if row["tick"] == 360)
            self.assertTrue(all("age_ticks" in fish for fish in snapshot_360["fish"]))


if __name__ == "__main__":
    unittest.main()
