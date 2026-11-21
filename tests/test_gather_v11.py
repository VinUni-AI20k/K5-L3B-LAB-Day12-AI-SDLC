"""Kiểm thử Gather v1.1 (Phase 2): 8 đàn cá bơi/phản xạ/đổi hướng/sinh, Cá Sấu M1/M2, hit/LIFO/recoil/ngất."""

import math
import unittest

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from helpers import Workdir, events, read_jsonl, run_headless, write_json


def _inp(move=(0.0, 0.0), edges=()):
    return InputState(move, {}, set(edges))


class GatherV11Tests(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_quan_reserves_new_v11_ingredients_through_cli(self):
        for dish_id in ("ca_keo_nuong", "lau_mam"):
            with self.subTest(dish_id=dish_id), Workdir() as w:
                recipe = self.tuning["menu"][dish_id]["recipe"]
                scenario = write_json(w.path("scenario.json"), {"quan": {
                    "random_customers": False, "stock": recipe,
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish_id,
                                   "reserved": recipe}]}})
                code, err = run_headless("--mode", "quan", "--ticks", "0", "--seed", "1",
                                         "--scenario", scenario, "--out", w.path("out.jsonl"))
                self.assertEqual(code, 0, err)
                snapshot = read_jsonl(w.path("out.jsonl"))[0]
                self.assertEqual(snapshot["customers"][0]["reserved"], recipe)

    def test_invalid_gather_tuning_is_rejected(self):
        bad = [
            ("fish_spawn_x", [1000]),
            ("fish_spawn_x", [True]),
            ("fish_depths", []),
            ("fish_depths", {"ca_linh": ["3", 12]}),
            ("fish_spawn_depths", {"ca_linh": [None]}),
            ("fish_speed", float("nan")),
            ("start_heading_deg", float("inf")),
        ]
        for key, value in bad:
            with self.subTest(key=key, value=value):
                tuning = load_contract()["tuning"]
                tuning["gather"][key] = value
                with self.assertRaises(BadInput):
                    validate_tuning(tuning)
        for spawn in (None, dict(self.tuning["gather"]["monsters"]["spawns"][0], pos=[60, 1]),
                      dict(self.tuning["gather"]["monsters"]["spawns"][0], waypoints=[[60, 1], [64, 24]])):
            with self.subTest(spawn=spawn):
                tuning = load_contract()["tuning"]
                tuning["gather"]["monsters"]["spawns"] = [spawn]
                with self.assertRaises(BadInput):
                    validate_tuning(tuning)

    def test_monster_scenario_validation_through_cli(self):
        monster = dict(self.tuning["gather"]["monsters"]["spawns"][0])
        monster.pop("from_day")
        for override in ({"pos": [60, 1]}, {"target_idx": 1.0},
                         {"state": "recoil", "state_ticks_left": 1, "recoil_dir": [2, 0]},
                         {"state": "recoil", "state_ticks_left": 0, "recoil_dir": [1, 0]}):
            with self.subTest(override=override), Workdir() as w:
                scenario = write_json(w.path("scenario.json"), {"gather": {
                    "monsters": [dict(monster, **override)]}})
                code, err = run_headless("--mode", "gather", "--ticks", "1", "--seed", "1",
                                         "--scenario", scenario, "--out", w.path("out.jsonl"))
                self.assertEqual(code, 2, err)

    def test_monster_faint_cli_is_deterministic_and_writes_empty_inventory(self):
        import json

        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {"gather": {
                "random_fish": False, "player": {"pos": [60, 15], "hp": 1},
                "hold": ["keo_neo", "ca_keo", "ca_loc"],
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 15],
                              "waypoints": [[60, 24], [64, 24]]}]}})
            inventory = write_json(w.path("inventory.json"), {"items": {"ca_loc": 1}})
            for name in ("first", "repeat"):
                code, err = run_headless("--mode", "gather", "--ticks", "3", "--seed", "7",
                                         "--scenario", scenario, "--inventory-out", inventory,
                                         "--out", w.path(name + ".jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("first.jsonl"), "rb") as first, open(w.path("repeat.jsonl"), "rb") as repeat:
                self.assertEqual(first.read(), repeat.read())
            rows = read_jsonl(w.path("first.jsonl"))
            hits = events(rows)
            self.assertEqual([e["name"] for e in hits], ["monster_hit", "faint", "gather_end"])
            self.assertEqual(hits[0]["data"]["lost"], ["ca_loc"])
            self.assertEqual(hits[1]["data"], {"cause": "monster", "lost": ["ca_keo", "keo_neo"], "hp": 0})
            with open(inventory, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})

    def test_seeded_initial_fish_8_unique_positions_and_deterministic(self):
        s1 = GatherSim(self.tuning, {}, Streams(7), IdAllocator())
        s2 = GatherSim(self.tuning, {}, Streams(7), IdAllocator())
        snap1 = s1.snapshot()["fish"]
        snap2 = s2.snapshot()["fish"]
        self.assertEqual(snap1, snap2)
        self.assertEqual(len(snap1), 8)
        pts = {tuple(f["pos"]) for f in snap1}
        self.assertEqual(len(pts), 8)

    def test_fish_swim_turn_at_120_and_edge_reflection(self):
        # Test edge reflection + corner reflection + turn before moving at age_ticks == 120
        sc = {
            "random_fish": True,
            "fish": [
                {"id": "F1", "kind": "ca_linh", "pos": [95.99, 3.01], "heading_deg": 315.0, "age_ticks": 0},
                {"id": "F2", "kind": "ca_loc", "pos": [50.0, 14.0], "heading_deg": 0.0, "age_ticks": 119},
            ],
            "monsters": [],
        }
        sim = GatherSim(self.tuning, sc, Streams(3), IdAllocator())
        sim.step(_inp())
        snap = {f["id"]: f for f in sim.snapshot()["fish"]}
        # F1 hits both x=96 and d=3 corner, reflecting x and d back into bounds
        self.assertLessEqual(snap["F1"]["pos"][0], 96.0)
        self.assertGreaterEqual(snap["F1"]["pos"][1], 3.0)
        # Heading reflected across both axes (315 -> 135 deg)
        self.assertAlmostEqual(snap["F1"]["heading_deg"], 135.0, delta=0.2)
        self.assertEqual(snap["F1"]["age_ticks"], 1)
        # F2 reached age_ticks 120 -> turned before moving so did not move strictly +x
        self.assertEqual(snap["F2"]["age_ticks"], 120)
        self.assertNotAlmostEqual(snap["F2"]["heading_deg"], 0.0, delta=0.01)

    def test_periodic_fish_spawn_at_360_and_cap_12(self):
        sim = GatherSim(self.tuning, {"monsters": []}, Streams(11), IdAllocator())
        spawned = []
        for _ in range(360):
            spawned.extend(sim.step(_inp()))
        sp = [d for name, d in spawned if name == "fish_spawned"]
        self.assertEqual(len(sp), 1)
        self.assertEqual(len(sim.fish), 9)
        self.assertEqual(next(f["age_ticks"] for f in sim.snapshot()["fish"] if f["id"] == sp[0]["id"]), 0)

        # Verify cap at 12
        for _ in range(360 * 5):
            sim.step(_inp())
        self.assertLessEqual(len(sim.fish), 12)

    def test_random_fish_false_freezes_fish_and_disables_spawn(self):
        sc = {
            "random_fish": False,
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20.0, 5.0], "heading_deg": 0.0}],
            "monsters": [],
        }
        sim = GatherSim(self.tuning, sc, Streams(1), IdAllocator())
        evs = []
        for _ in range(360):
            evs.extend(sim.step(_inp()))
        self.assertEqual(sim.snapshot()["fish"][0]["pos"], [20.0, 5.0])
        self.assertEqual([e for e in evs if e[0] == "fish_spawned"], [])

    def test_crocodile_m1_day1_and_m2_day3_patrol_chase_hit_recoil_faint(self):
        sim_d1 = GatherSim(self.tuning, {}, Streams(1), IdAllocator(), day=1)
        self.assertEqual([m["id"] for m in sim_d1.snapshot()["monsters"]], ["M1"])
        sim_d3 = GatherSim(self.tuning, {}, Streams(1), IdAllocator(), day=3)
        self.assertEqual([m["id"] for m in sim_d3.snapshot()["monsters"]], ["M1", "M2"])

        # Patrol flip + chase trigger at d >= 10, dist <= 10, exit > 16
        sc = {
            "random_fish": False,
            "player": {"pos": [60.0, 15.0], "hp": 2},
            "hold": ["ca_loc", "bong_sung", "ca_linh"],
            "monsters": [{
                "id": "M1", "kind": "ca_sau", "pos": [61.0, 15.0],
                "waypoints": [[60.0, 24.0], [64.0, 24.0]], "target_idx": 1,
            }],
        }
        sim = GatherSim(self.tuning, sc, Streams(1), IdAllocator())
        evs1 = sim.step(_inp())
        # Starts in chase (dist 1.0 <= 10 and player d=15 >= 10), hits player -> LIFO drops floor(3*0.5)=1 (ca_linh)
        self.assertEqual([e[0] for e in evs1], ["monster_hit"])
        hit = evs1[0][1]
        self.assertEqual(hit["monster_id"], "M1")
        self.assertEqual(hit["hp"], 1)
        self.assertEqual(hit["lost"], ["ca_linh"])
        self.assertEqual(sim.hold, ["ca_loc", "bong_sung"])
        self.assertEqual(sim.invuln_ticks, 90)
        self.assertEqual(sim.monsters[0]["state"], "recoil")
        self.assertEqual(sim.monsters[0]["state_ticks_left"], 60)

        # Wait 60 ticks of recoil: ends at tick 61, returns to patrol without hit on final recoil tick
        for _ in range(60):
            evs = sim.step(_inp())
            self.assertEqual([e for e in evs if e[0] == "monster_hit"], [])
        self.assertEqual(sim.monsters[0]["state"], "patrol")
        self.assertIsNone(sim.monsters[0]["recoil_dir"])

        # Second fatal hit when invuln expired: drops floor(2*0.5)=1 (bong_sung), then faint drops remaining LIFO (ca_loc)
        sc_fatal = {
            "random_fish": False,
            "player": {"pos": [60.0, 15.0], "hp": 1, "invuln_ticks": 0},
            "hold": ["ca_loc", "bong_sung"],
            "monsters": [{
                "id": "M1", "kind": "ca_sau", "pos": [60.0, 15.0],
                "waypoints": [[60.0, 24.0], [64.0, 24.0]],
            }],
        }
        sim_fatal = GatherSim(self.tuning, sc_fatal, Streams(1), IdAllocator())
        fevs = sim_fatal.step(_inp())
        self.assertEqual([e[0] for e in fevs], ["monster_hit", "faint", "gather_end"])
        self.assertEqual(fevs[0][1]["lost"], ["bong_sung"])
        self.assertEqual(fevs[1][1], {"cause": "monster", "lost": ["ca_loc"], "hp": 0})
        self.assertEqual(fevs[2][1], {"reason": "fainted", "inventory": {"items": {}}})


if __name__ == "__main__":
    unittest.main()
