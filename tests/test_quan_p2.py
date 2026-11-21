import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
from helpers import ROOT, Workdir, events, read_jsonl, run_headless, write_json


class Phase2Customers(unittest.TestCase):
    def setUp(self):
        self.tuning = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))["tuning"]
        self.quan = self.tuning["quan"]
        self.no_input = SimpleNamespace(move=(0, 0), pressed=lambda _: False)

    def test_two_open_tables_do_not_reserve_same_portion(self):
        sim = QuanSim(self.tuning, {"stock": {"ca_loc": 1}}, Streams(42), IdAllocator())
        first = self.quan["first_customer_tick"]
        interval = round(self.quan["customer_interval_s"] * self.tuning["tick_hz"])
        for _ in range(first):
            arrivals = sim.step(self.no_input)
        self.assertEqual(arrivals[0][0], "customer_arrived")
        self.assertEqual(sim.customers[0]["reserved"], {"ca_loc": 1})
        self.assertEqual(sim.customers[0]["order_tick"], first)
        for _ in range(interval):
            next_arrival = sim.step(self.no_input)
        self.assertEqual(next_arrival, [("no_dish", {"table_id": "T2"})])
        self.assertEqual(len(sim.customers), 1)

    def test_day_excludes_dishes_outside_plan(self):
        planned = self.tuning["day_plan"][0]["dishes"]
        sim = QuanSim(self.tuning, {"stock": {"ca_keo": 2}}, Streams(42), IdAllocator(),
                      planned_dishes=planned)
        for _ in range(self.quan["first_customer_tick"]):
            arrival = sim.step(self.no_input)
        self.assertEqual(arrival, [("no_dish", {"table_id": "T1"})])

    def test_day_count_does_not_cap_orders(self):
        dish = "ca_loc_nuong_trui"
        sim = QuanSim(self.tuning, {"stock": {"ca_loc": 2}}, Streams(42), IdAllocator(),
                      planned_dishes={dish: 1})
        second = self.quan["first_customer_tick"] + round(
            self.quan["customer_interval_s"] * self.tuning["tick_hz"])
        for _ in range(second):
            sim.step(self.no_input)
        self.assertEqual([(c["table_id"], c["dish_id"]) for c in sim.customers],
                         [("T1", dish), ("T2", dish)])

    def test_quan_reads_new_ingredients_and_uses_full_menu(self):
        with Workdir() as work:
            inventory = write_json(work.path("inventory.json"), {
                "items": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}
            })
            out = work.path("quan.jsonl")
            code, error = run_headless("--mode", "quan", "--seed", "42", "--ticks",
                                       str(self.quan["first_customer_tick"]),
                                       "--inventory", inventory, "--out", out)
            self.assertEqual(code, 0, error)
            arrivals = events(read_jsonl(out), "customer_arrived")
            self.assertEqual([arrival["data"]["dish_id"] for arrival in arrivals], ["lau_mam"])

    def test_day_handoff_filters_plan_and_applies_upgrade_next_day(self):
        with Workdir() as work:
            scenario = write_json(work.path("day.json"), {
                "day": {"money": 200, "earned": 200},
                "gather": {"hold": ["ca_keo", "ca_keo"], "random_fish": False},
                "quan": {"time_left_ticks": 121},
            })
            inputs = write_json(work.path("inputs.json"), {"frames": [
                {"tick": 0, "interact": True},
                {"tick": 122, "buy": "oxygen", "shop_done": True},
            ]})
            out = work.path("day.jsonl")
            code, error = run_headless("--mode", "day", "--days", "2", "--seed", "42",
                                       "--ticks", "123", "--scenario", scenario,
                                       "--inputs", inputs, "--out", out)
            self.assertEqual(code, 0, error)
            rows = read_jsonl(out)
            starts = [(e["tick"], e["phase"]) for e in events(rows, "phase_start")]
            self.assertEqual(starts, [(0, "gather"), (1, "quan"), (122, "shop"), (123, "gather")])
            self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [121])
            night = next(row for row in rows if row["type"] == "snapshot" and row["phase"] == "quan")
            self.assertEqual((night["phase_tick"], night["stock"]), (0, {"ca_keo": 2}))
            next_day = rows[-2]
            self.assertEqual(next_day["active_upgrades"], {"oxygen": 1})
            self.assertEqual(next_day["player"]["oxygen_ticks"], 2700)
            self.assertEqual((next_day["money"], next_day["earned"]), (0, 200))
