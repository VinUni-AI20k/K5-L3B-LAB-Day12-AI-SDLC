import json
import unittest
from pathlib import Path

from chonoi.inputs import InputState
from chonoi.runner import Session


class FishMotionTest(unittest.TestCase):
    def session(self, seed=1, **scenario):
        path = Path(__file__).resolve().parents[1] / "game.contract.json"
        tuning = json.loads(path.read_text(encoding="utf-8"))["tuning"]
        tuning["gather"]["fish_yield"]["ca_keo"] = 2
        tuning["gather"]["nodes"].extend([
            {"id": "N5", "kind": "keo_neo", "pos": [76, 0]},
            {"id": "N6", "kind": "keo_neo", "pos": [90, 0]},
        ])
        tuning["gather"].update(
            fish_motion={"speed": 3, "turn_every_ticks": 3,
                         "max_turn_deg": 25, "min_depth": 1},
            fish_initial=[{"id": "F10", "kind": "ca_loc", "pos": [100, 5],
                           "heading_deg": 0}],
            fish_spawn_schedule=[
                {"tick": 2, "kind": "ca_linh", "pos": [20, 8], "heading_deg": 0},
                {"tick": 2, "kind": "ca_loc", "pos": [40, 16], "heading_deg": 180},
            ],
        )
        return Session("gather", tuning, scenario, seed)

    def advance(self, session):
        session.step(InputState((0, 0), {}, set()))
        return session.snapshot()["fish"]

    def test_boundary_and_spawn_ticks(self):
        session = self.session()
        fish = self.advance(session)
        self.assertEqual([school["id"] for school in fish], ["F10"])
        self.assertEqual(fish[0]["pos"], [100, 5])
        self.assertEqual(fish[0]["heading_deg"], 180)

        fish = self.advance(session)
        self.assertEqual([school["id"] for school in fish], ["F10", "F11", "F12"])
        self.assertLess(fish[0]["pos"][0], 100)
        self.assertEqual(fish[1]["pos"], [20, 8])
        self.assertEqual(len(self.advance(session)), 3)

    def test_turns_are_repeatable_and_seeded(self):
        first, repeat, other = self.session(), self.session(), self.session(seed=2)
        for _ in range(2):
            self.assertEqual(self.advance(first), self.advance(repeat))
            self.advance(other)
        turned = self.advance(first)
        self.assertEqual(turned, self.advance(repeat))
        self.assertNotEqual(turned, self.advance(other))
        self.assertNotEqual(turned[0]["heading_deg"], 180)

    def test_scenario_overrides_suppress_scheduled_spawns(self):
        for scenario in ({"fish": []}, {"random_fish": False}):
            with self.subTest(scenario=scenario):
                session = self.session(**scenario)
                self.advance(session)
                self.assertEqual(self.advance(session), [])

    def test_new_ingredients_enter_inventory_with_updated_tuning(self):
        fishing = self.session(
            player={"pos": [25, 10]},
            fish=[{"id": "F1", "kind": "ca_keo", "pos": [25, 10]}],
        )
        fishing.step(InputState((0, 0), {}, {"catch"}))
        self.assertEqual(fishing.sim.inventory_items(), {"ca_keo": 2})

        for node_x in (76, 90):
            with self.subTest(node_x=node_x):
                harvesting = self.session(player={"pos": [node_x, 0]})
                harvesting.step(InputState((0, 0), {}, {"interact"}))
                self.assertEqual(harvesting.sim.inventory_items(), {"keo_neo": 1})
