"""QA regression tests for TICKET-02 / Phase 2 contract v1.1.

The tests are intentionally contract-facing.  They expose missing Phase 2
behavior without changing simulation code or weakening Phase 1 assertions.
"""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from chonoi.sim.quan import QuanSim

import sys
from pathlib import Path

# Đảm bảo import được helpers khi chạy trực tiếp mà không cần set PYTHONPATH
_tests_dir = str(Path(__file__).parent)
if _tests_dir not in sys.path:
    sys.path.insert(0, _tests_dir)

try:
    from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json
except ImportError:
    from tests.helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class Input:
    def __init__(self, move=(0.0, 0.0), buttons=()):
        self.move = move
        self.buttons = set(buttons)

    def pressed(self, name):
        return name in self.buttons


def idle():
    return Input()


def tuning():
    return load_contract()["tuning"]


def make_gather(fish, player=None, hold=None, monsters=None, streams=None):
    scenario = {
        "random_fish": False,
        "fish": fish,
        "nodes": [],
    }
    if player:
        scenario["player"] = player
    if hold is not None:
        scenario["hold"] = hold
    if monsters is not None:
        scenario["monsters"] = monsters
    return GatherSim(tuning(), scenario, streams or Streams(7), IdAllocator())


class GatherFishPhase2Tests(unittest.TestCase):
    def test_fish_changes_heading_on_exact_120th_swim_tick(self):
        sim = make_gather([{"id": "F1", "kind": "ca_linh", "pos": [50, 8], "heading_deg": 0}])

        for _ in range(119):
            sim.step(idle())
        before = sim.fish[0]["heading_deg"]
        sim.step(idle())

        self.assertNotEqual(sim.fish[0]["heading_deg"], before)

    def test_fish_reflects_at_x_edge_and_stays_inside_bounds(self):
        sim = make_gather([{"id": "F1", "kind": "ca_linh", "pos": [95.99, 8], "heading_deg": 0}])

        sim.step(idle())

        fish = sim.fish[0]
        self.assertLessEqual(fish["pos"][0], 96.0)
        self.assertGreaterEqual(fish["pos"][0], 4.0)
        self.assertAlmostEqual(fish["heading_deg"] % 360, 180.0, delta=1.0)

    def test_fish_spawns_at_tick_360_with_configured_species_weight(self):
        expected = {
            0.39: "ca_linh",
            0.40: "ca_loc",
            0.70: "ca_keo",
        }
        for probe, kind in expected.items():
            sim = make_gather([
                {"id": f"F{i}", "kind": "ca_linh", "pos": [5 + i * 10, 5], "heading_deg": 0}
                for i in range(8)
            ])

            class Probe:
                def random(self):
                    return probe

                def uniform(self, a, b):
                    return (a + b) / 2

                def choice(self, seq):
                    return seq[0]

            class ProbeStreams:
                def get(self, name):
                    return Probe()

            sim.rng = ProbeStreams()
            emitted = []
            for _ in range(360):
                emitted.extend(sim.step(idle()))
            spawned = [data for name, data in emitted if name == "fish_spawned"]
            self.assertEqual(len(spawned), 1, probe)
            self.assertEqual(spawned[0]["kind"], kind, probe)


class CrocodilePhase2Tests(unittest.TestCase):
    MONSTER = {
        "id": "M1",
        "kind": "ca_sau",
        "pos": [60, 24],
        "waypoints": [[60, 24], [64, 24]],
        "state": "patrol",
    }

    def test_crocodile_patrols_between_waypoints(self):
        sim = make_gather([], player={"pos": [20, 5]}, monsters=[self.MONSTER])
        monsters = sim.snapshot().get("monsters")
        self.assertIsNotNone(monsters, "gather snapshot must expose monsters[] in v1.1")
        start = list(monsters[0]["pos"])

        for _ in range(60):
            sim.step(idle())

        current = sim.snapshot().get("monsters", [{}])[0]
        self.assertNotEqual(current["pos"], start)
        self.assertEqual(current["state"], "patrol")

    def test_crocodile_chases_player_inside_detection_radius(self):
        sim = make_gather([], player={"pos": [65, 24]}, monsters=[self.MONSTER])

        sim.step(idle())

        monsters = sim.snapshot().get("monsters")
        self.assertIsNotNone(monsters, "gather snapshot must expose monsters[] in v1.1")
        self.assertEqual(monsters[0]["state"], "chase")

    def test_crocodile_hit_loses_one_hp_and_half_hold_in_lifo_order(self):
        sim = make_gather(
            [],
            player={"pos": [60, 24], "hp": 3},
            hold=["ca_linh", "bong_sung", "ca_loc", "keo_neo"],
            monsters=[self.MONSTER],
        )

        emitted = sim.step(idle())
        hit = [data for name, data in emitted if name == "monster_hit"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["hp"], 2)
        self.assertEqual(hit[0]["lost"], ["keo_neo", "ca_loc"])
        self.assertEqual(sim.hold, ["ca_linh", "bong_sung"])

    def test_crocodile_is_invulnerable_90_ticks_then_recoils_60_ticks(self):
        sim = make_gather([], player={"pos": [60, 24]}, monsters=[self.MONSTER])

        first = sim.step(idle())
        self.assertTrue(any(name == "monster_hit" for name, _ in first))
        follow_up = []
        for _ in range(90):
            follow_up.extend(sim.step(idle()))
        self.assertFalse(any(name == "monster_hit" for name, _ in follow_up))
        monsters = sim.snapshot().get("monsters")
        self.assertIsNotNone(monsters, "gather snapshot must expose monsters[] in v1.1")
        monster = monsters[0]
        self.assertIn(monster["state"], ("recoil", "patrol", "chase"))


class QuanAndPlanPhase2Tests(unittest.TestCase):
    def setUp(self):
        self.t = tuning()

    def test_quan_has_two_stoves_and_four_tables(self):
        sim = QuanSim(self.t, {}, Streams(1), IdAllocator())
        self.assertEqual([s["id"] for s in sim.stoves], ["B1", "B2"])
        self.assertEqual([tb["id"] for tb in sim.tables], ["T1", "T2", "T3", "T4"])

    def test_each_day_plan_has_expected_dishes_and_ingredients(self):
        plans = {p["day"]: p for p in self.t["day_plan"]}
        self.assertEqual(set(plans), {1, 2, 3, 4, 5})
        for plan in plans.values():
            calculated = {}
            for dish_id, servings in plan["dishes"].items():
                for ingredient, quantity in self.t["menu"][dish_id]["recipe"].items():
                    calculated[ingredient] = calculated.get(ingredient, 0) + quantity * servings
            self.assertEqual(plan["ingredients"], calculated)

    def test_day_headless_announces_d1_to_d5_plan(self):
        for day in range(1, 6):
            with Workdir() as w:
                scenario = write_json(w.path("scenario.json"), {
                    "day": {"day": day, "money": 0, "earned": 0},
                    "gather": {"hold": [], "random_fish": False},
                })
                out = w.path("day.jsonl")
                code, err = run_headless("--mode", "day", "--days", "1", "--seed", "1",
                                         "--ticks", "1", "--scenario", scenario, "--out", out)
                self.assertEqual(code, 0, (day, err))
                day_events = events(read_jsonl(out), "day_plan")
                self.assertEqual(day_events[0]["data"]["dishes"], self.t["day_plan"][day - 1]["dishes"])

    def test_shop_buys_oxygen_at_price_and_applies_next_day(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "day": {"day": 1, "money": 200, "earned": 200},
                "gather": {"hold": [], "random_fish": False},
            })
            inputs = write_json(w.path("inputs.json"), frames(
                {"tick": 0, "buy": "oxygen"}, {"tick": 1, "shop_done": True}
            ))
            out = w.path("day.jsonl")
            code, err = run_headless("--mode", "day", "--days", "2", "--seed", "1",
                                     "--ticks", "10", "--scenario", scenario,
                                     "--inputs", inputs, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            bought = events(rows, "bought")
            self.assertEqual(bought[0]["data"]["price"], 200)
            next_day = [s for s in snapshots(rows) if s.get("day") == 2]
            self.assertTrue(next_day)
            self.assertEqual(next_day[0]["active_upgrades"]["oxygen"], 1)

    def test_pause_freezes_gameplay_tick_and_timer(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "day": {"day": 1, "money": 0, "earned": 0},
                "gather": {"hold": [], "random_fish": False},
            })
            inputs = write_json(w.path("inputs.json"), frames(
                {"tick": 0, "pause": True}, {"tick": 4, "pause": False}
            ))
            out = w.path("day.jsonl")
            code, err = run_headless("--mode", "day", "--days", "1", "--seed", "1",
                                     "--ticks", "6", "--scenario", scenario,
                                     "--inputs", inputs, "--out", out, "--snapshot-every", "1")
            self.assertEqual(code, 0, err)
            paused = [s for s in snapshots(read_jsonl(out)) if s["state"] == "paused"]
            self.assertGreaterEqual(len(paused), 2)
            self.assertEqual(len({s["sim_tick"] for s in paused}), 1)
            self.assertEqual(len({s["phase_tick"] for s in paused}), 1)


if __name__ == "__main__":
    unittest.main()
