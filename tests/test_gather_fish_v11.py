"""Hồi quy cho đàn cá v1.1 và nguyên liệu mới của Gather."""

import math
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


class GatherFishV11(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.g = self.tuning["gather"]

    def build(self, scenario=None, seed=7):
        return GatherSim(self.tuning, scenario or {}, Streams(seed), IdAllocator())

    def test_initial_schools_use_unique_points_and_seed(self):
        fish = self.build().snapshot()["fish"]
        self.assertEqual(fish, self.build().snapshot()["fish"])
        self.assertEqual(len(fish), self.g["fish_initial"])
        self.assertEqual(len({tuple(school["pos"]) for school in fish}), len(fish))
        for school in fish:
            x, depth = school["pos"]
            self.assertIn(x, self.g["fish_spawn_x"])
            self.assertIn(depth, self.g["fish_spawn_depths"][school["kind"]])
            self.assertEqual(school["age_ticks"], 0)

    def test_reflects_remaining_distance_in_both_axes(self):
        speed_step = self.g["fish_speed"] / self.tuning["tick_hz"]
        dx = speed_step / math.sqrt(2)
        x_max, d_max = self.g["fish_x"][1], self.g["fish_depths"]["ca_linh"][1]
        for start_gap, expected_gap in ((dx, 0), (dx / 2, dx / 2)):
            with self.subTest(start_gap=start_gap):
                sim = self.build({"fish": [{
                    "id": "F1", "kind": "ca_linh", "heading_deg": 45,
                    "pos": [x_max - start_gap, d_max - start_gap],
                }]})
                sim.step(InputPlayer([]).advance(0))
                fish = sim.fish[0]
                self.assertAlmostEqual(fish["pos"][0], x_max - expected_gap)
                self.assertAlmostEqual(fish["pos"][1], d_max - expected_gap)
                self.assertAlmostEqual(fish["heading_deg"], 225)

    def test_turn_happens_before_swimming_on_turn_tick(self):
        age = self.g["fish_turn_ticks"] - 1
        sim = self.build({"fish": [{
            "id": "F1", "kind": "ca_linh", "heading_deg": 0, "age_ticks": age,
            "pos": [20, 8],
        }]})
        sim.step(InputPlayer([]).advance(0))
        fish = sim.snapshot()["fish"][0]
        expected_heading = Streams(7).get("fish_turn").random() * 360
        expected_angle = math.radians(expected_heading)
        step_length = self.g["fish_speed"] / self.tuning["tick_hz"]
        self.assertEqual(fish["age_ticks"], age + 1)
        self.assertAlmostEqual(fish["heading_deg"], expected_heading)
        self.assertAlmostEqual(fish["pos"][0], 20 + math.cos(expected_angle) * step_length)
        self.assertAlmostEqual(fish["pos"][1], 8 + math.sin(expected_angle) * step_length)

    def test_spawn_schedule_uses_elapsed_phase_ticks_and_respects_cap(self):
        interval, cap = self.g["fish_spawn_ticks"], self.g["fish_max"]
        sim = self.build({"fish": [], "time_left_ticks": (cap + 2) * interval})
        inputs = InputPlayer([])
        for tick in range(1, (cap + 1) * interval + 1):
            events = sim.step(inputs.advance(tick - 1))
            spawns = [data for name, data in events if name == "fish_spawned"]
            if tick % interval == 0 and tick <= cap * interval:
                self.assertEqual(len(spawns), 1, tick)
                new = sim.snapshot()["fish"][-1]
                self.assertEqual(spawns[0], {key: new[key] for key in ("id", "kind", "pos")})
                self.assertEqual(new["age_ticks"], 0)
                for other in sim.fish[:-1]:
                    self.assertGreater(
                        math.dist(new["pos"], other["pos"]), self.g["fish_spawn_clearance"],
                    )
            else:
                self.assertEqual(spawns, [], tick)
        self.assertEqual(len(sim.fish), cap)

    def test_static_fish_fixture_does_not_swim_or_spawn(self):
        initial = [{"id": "F10", "kind": "ca_keo", "pos": [15, 24]}]
        sim = self.build({"fish": initial, "random_fish": False})
        before = sim.snapshot()["fish"]
        inputs = InputPlayer([])
        for tick in range(self.g["fish_spawn_ticks"] + 1):
            self.assertEqual(sim.step(inputs.advance(tick)), [])
        self.assertEqual(sim.snapshot()["fish"], before)
        self.assertEqual(sim.snapshot()["fish"][0]["age_ticks"], 0)

    def test_new_ingredients_enter_hold_and_export_inventory(self):
        fish = {"id": "F1", "kind": "ca_keo", "pos": [15, 24]}
        sim = self.build({"player": {"pos": fish["pos"]}, "fish": [fish]})
        inputs = InputPlayer([{"tick": 0, "catch": True}])
        self.assertEqual(sim.step(inputs.advance(0)), [
            ("fish_caught", {"fish_id": "F1", "kind": "ca_keo", "yield": 2}),
        ])
        self.assertEqual(sim.inventory_items(), {"ca_keo": 2})

        node = next(node for node in self.g["nodes"] if node["id"] == "N5")
        sim = self.build({"player": {"pos": node["pos"]}})
        inputs = InputPlayer([{"tick": 0, "interact": True}])
        self.assertEqual(sim.step(inputs.advance(0)), [
            ("gather", {"node_id": "N5", "kind": "keo_neo", "amount": 1}),
        ])
        self.assertEqual(sim.inventory_items(), {"keo_neo": 1})
