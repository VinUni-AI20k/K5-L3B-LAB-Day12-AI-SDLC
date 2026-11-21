import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.headless import main as headless_main
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer, InputState, load_frames
from chonoi.live import LiveGame
from chonoi.rng import Streams
from chonoi.runner import Session, run
from chonoi.sim.quan import QuanSim


class QuanStockoutTests(unittest.TestCase):
    def setUp(self):
        self.tuning = copy.deepcopy(load_contract()["tuning"])

    def _events(self, sim, count):
        player = InputPlayer([])
        return [
            (tick + 1, name, data)
            for tick in range(count)
            for name, data in sim.step(player.advance(tick))
        ]

    def test_empty_cookable_menu_emits_no_dish_without_customer(self):
        sim = QuanSim(self.tuning, {"stock": {}, "random_customers": True},
                      Streams(1), IdAllocator())

        events = self._events(sim, self.tuning["quan"]["first_customer_tick"])

        self.assertIn((self.tuning["quan"]["first_customer_tick"], "no_dish", {}), events)
        self.assertEqual(sim.customers, [])

    def test_stockout_customer_can_accept_substitute_or_leave(self):
        menu_filter = ["ca_keo_nuong", "ca_loc_nuong_trui"]
        seed = next(
            candidate for candidate in range(100)
            if Streams(candidate).get("customer_dish").choice(sorted(menu_filter)) == "ca_loc_nuong_trui"
        )
        sim = QuanSim(
            self.tuning, {"stock": {"ca_keo": 2}, "random_customers": True},
            Streams(seed), IdAllocator(), menu_filter=menu_filter,
        )

        events = self._events(sim, self.tuning["quan"]["first_customer_tick"])

        self.assertIn("customer_arrived", [name for _, name, _ in events])
        customer = sim.customers[0]
        self.assertEqual(customer["state"], "choosing")
        self.assertEqual(customer["dish_id"], "ca_loc_nuong_trui")

        choice = InputState((0, 0), {}, set(), customer_choice={
            "customer_id": customer["id"], "dish_id": "ca_keo_nuong",
        })
        chosen_events = sim.step(choice)
        self.assertIn("customer_substituted", [name for name, _ in chosen_events])
        self.assertEqual(customer["state"], "waiting")
        self.assertEqual(customer["reserved"], {"ca_keo": 2})

        leave_sim = QuanSim(
            self.tuning, {"stock": {"ca_keo": 2}, "random_customers": True},
            Streams(seed), IdAllocator(), menu_filter=menu_filter,
        )
        self._events(leave_sim, self.tuning["quan"]["first_customer_tick"])
        leave_customer = leave_sim.customers[0]
        reputation = leave_sim.reputation
        leave = InputState((0, 0), {}, set(), customer_choice={
            "customer_id": leave_customer["id"], "dish_id": "leave",
        })
        leave_events = leave_sim.step(leave)
        self.assertIn("customer_left", [name for name, _ in leave_events])
        self.assertEqual(leave_sim.customers, [])
        self.assertEqual(leave_sim._available_stock(), {"ca_keo": 2})
        self.assertEqual(leave_sim.reputation, reputation + self.tuning["quan"]["left_reputation_delta"])

    def test_cook_start_persists_consumed_stock(self):
        with tempfile.TemporaryDirectory() as directory:
            inventory_path = str(Path(directory) / "inventory.json")
            Path(inventory_path).write_text(
                json.dumps({"items": {"ca_loc": 2}}), encoding="utf-8"
            )
            out_path = str(Path(directory) / "run.jsonl")
            scenario = {
                "player": {"pos": [2, 8]},
                "random_customers": False,
                "time_left_ticks": 10,
                "customers": [{
                    "id": "C1", "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                }],
            }

            run(
                "quan", self.tuning, scenario, 1,
                [{"tick": 0, "interact": True}], 1, out_path, 1,
                inventory={"ca_loc": 2}, inventory_path=inventory_path,
            )

            self.assertEqual(
                json.loads(Path(inventory_path).read_text(encoding="utf-8")),
                {"items": {"ca_loc": 1}},
            )

    def test_live_cook_start_persists_consumed_stock(self):
        with tempfile.TemporaryDirectory() as directory:
            inventory_path = str(Path(directory) / "inventory.json")
            Path(inventory_path).write_text(
                json.dumps({"items": {"ca_loc": 2}}), encoding="utf-8"
            )
            scenario = {
                "player": {"pos": [2, 8]},
                "random_customers": False,
                "time_left_ticks": 10,
                "customers": [{
                    "id": "C1", "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                }],
            }
            game = LiveGame("quan", self.tuning, scenario, 1, inventory={"ca_loc": 2},
                            inventory_path=inventory_path)

            game.set_input({"interact": True})
            game._tick_once()

            self.assertEqual(
                json.loads(Path(inventory_path).read_text(encoding="utf-8")),
                {"items": {"ca_loc": 1}},
            )

    def test_live_customer_choice_reaches_quan_sim(self):
        scenario = {
            "stock": {"ca_keo": 2},
            "random_customers": False,
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "lau_mam",
                "state": "choosing",
            }],
        }
        game = LiveGame("quan", self.tuning, scenario, 1)

        with self.assertRaises(ValueError):
            game.set_input({"customer_choice": None})
        game.set_input({"customer_choice": {"customer_id": "C1", "dish_id": "ca_keo_nuong"}})
        game._tick_once()

        self.assertIn("customer_substituted", [event["name"] for event in game.events])
        self.assertEqual(game.session.sim.customers[0]["dish_id"], "ca_keo_nuong")

    def test_day_cook_start_persists_harvested_and_remaining_stock(self):
        with tempfile.TemporaryDirectory() as directory:
            inventory_path = str(Path(directory) / "inventory.json")
            Path(inventory_path).write_text(
                json.dumps({"items": {"ca_loc": 2}}), encoding="utf-8"
            )
            out_path = str(Path(directory) / "day.jsonl")
            tuning = copy.deepcopy(self.tuning)
            tuning["day_plan"] = {
                "1": {"dishes": {"ca_loc_nuong_trui": 1}, "ingredients": {}},
            }
            scenario = {
                "day": {"days": 1},
                "gather": {"time_left_ticks": 1, "random_fish": False, "nodes": []},
                "quan": {
                    "player": {"pos": [2, 8]},
                    "time_left_ticks": 10,
                    "random_customers": False,
                    "customers": [{
                        "id": "C1", "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                    }],
                },
            }

            run(
                "day", tuning, scenario, 1,
                [{"tick": 1, "interact": True}], 2, out_path, 1,
                inventory={"ca_loc": 2}, inventory_path=inventory_path, days=1,
            )

            self.assertEqual(
                json.loads(Path(inventory_path).read_text(encoding="utf-8")),
                {"items": {"ca_loc": 1}},
            )

    def test_headless_day_creates_default_inventory_after_gather(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scenario_path = root / "scenario.json"
            scenario_path.write_text(json.dumps({
                "day": {"days": 1},
                "gather": {
                    "time_left_ticks": 1, "hold": ["ca_loc"],
                    "random_fish": False, "nodes": [], "fish": [],
                },
                "quan": {"random_customers": False},
            }), encoding="utf-8")
            output_path = root / "run.jsonl"
            previous_directory = os.getcwd()
            try:
                os.chdir(directory)
                code = headless_main([
                    "--mode", "day", "--days", "1", "--seed", "1", "--ticks", "1",
                    "--scenario", str(scenario_path), "--out", str(output_path),
                ])
            finally:
                os.chdir(previous_directory)

            self.assertEqual(code, 0)
            self.assertEqual(
                json.loads((root / "inventory.json").read_text(encoding="utf-8")),
                {"items": {"ca_loc": 1}},
            )

    def test_headless_customer_choice_frame_is_typed_and_one_shot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inputs.json"
            path.write_text(json.dumps({"frames": [{
                "tick": 0,
                "customer_choice": {"customer_id": "C1", "dish_id": "leave"},
            }]}), encoding="utf-8")

            frames = load_frames(str(path), allow_customer_choice=True)
            self.assertEqual(
                InputPlayer(frames).advance(0).customer_choice,
                {"customer_id": "C1", "dish_id": "leave"},
            )

            with self.assertRaises(BadInput):
                load_frames(str(path))

    def test_extra_stock_survives_shop_to_next_day(self):
        scenario = {
            "day": {"days": 2},
            "gather": {"time_left_ticks": 1, "random_fish": False, "nodes": []},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        session = Session("day", self.tuning, scenario, 1, inventory={"ca_loc": 2}, days=2)

        session.step(InputState((0, 0), {}, set()))
        session.step(InputState((0, 0), {}, set()))
        session.step(InputState((0, 0), {"shop_done": True}, {"shop_done"}))

        self.assertEqual(session.sim.day, 2)
        self.assertEqual(session.sim.stock, {"ca_loc": 2})
        session.step(InputState((0, 0), {}, set()))
        self.assertEqual(session.sim.phase, "quan")
        self.assertEqual(session.sim.inventory_items(), {"ca_loc": 2})


if __name__ == "__main__":
    unittest.main()
