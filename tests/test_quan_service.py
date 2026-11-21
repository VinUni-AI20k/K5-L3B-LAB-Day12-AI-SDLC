"""Unit and headless tests for Quan Lát 4 (cooking, serving, tips, score)."""

import json
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.quan import QuanSim
from helpers import Workdir, events, read_jsonl, run_headless


def _inp(move=(0.0, 0.0), interact=False):
    edges = {"interact"} if interact else set()
    return InputState(move, {"interact": interact, "catch": False}, edges)


def _waiting_customer(cid="C1", table_id="T1", dish="ca_loc_nuong_trui", patience=3600, reserved=None):
    return {
        "id": cid,
        "table_id": table_id,
        "dish": dish,
        "state": "waiting",
        "patience_ticks": patience,
        "eat_ticks_left": 0,
        "reserved": reserved if reserved is not None else {"ca_loc": 1},
    }


class QuanServiceTests(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_cook_countdown_ready_and_pickup_at_stove(self):
        sc = {
            "player": {"pos": [2, 8]},
            "stock": {"ca_loc": 2},
            "customers": [_waiting_customer()],
        }
        sim = QuanSim(self.tuning, sc, Streams(1), IdAllocator())

        ev1 = sim.step(_inp(interact=True))
        self.assertIn(("cook_started", {"stove_id": "B1", "dish": "ca_loc_nuong_trui"}), ev1)
        self.assertEqual(sim.stock["ca_loc"], 1)
        self.assertEqual(sim.customers[0]["reserved"], {})
        self.assertEqual(sim.stoves[0]["state"], "cooking")

        cook_ticks = round(self.tuning["menu"]["ca_loc_nuong_trui"]["cook_s"] * self.tuning["tick_hz"])
        ready_events = []
        for _ in range(cook_ticks):
            ready_events.extend(sim.step(_inp()))
        self.assertIn(("dish_ready", {"stove_id": "B1", "dish": "ca_loc_nuong_trui"}), ready_events)
        self.assertEqual(sim.stoves[0]["state"], "ready")

        ev_pick = sim.step(_inp(interact=True))
        self.assertIn(("dish_picked", {"dish": "ca_loc_nuong_trui"}), ev_pick)
        self.assertEqual(sim.hand, "ca_loc_nuong_trui")
        self.assertEqual(sim.stoves[0]["state"], "idle")

    def test_interact_priority_distance_then_stove_before_table_then_id(self):
        sc = {
            "player": {"pos": [5, 5]},
            "stock": {"ca_loc": 2},
            "hand": "ca_loc_nuong_trui",
            "stoves": [{"id": "B1", "pos": [4, 5], "state": "ready", "dish": "goi_bong_sung"}],
            "tables": [{"id": "T1", "pos": [6, 5]}],
            "customers": [_waiting_customer(dish="ca_loc_nuong_trui")],
        }
        sim = QuanSim(self.tuning, sc, Streams(1), IdAllocator())
        ev = sim.step(_inp(interact=True))
        self.assertTrue(any(name == "served" for name, _ in ev))

        sc2 = {
            "player": {"pos": [5, 5]},
            "stock": {"ca_loc": 2},
            "stoves": [{"id": "B1", "pos": [4, 5]}],
            "tables": [{"id": "T1", "pos": [6, 5]}],
            "customers": [_waiting_customer()],
        }
        sim2 = QuanSim(self.tuning, sc2, Streams(1), IdAllocator())
        ev2 = sim2.step(_inp(interact=True))
        self.assertTrue(any(name == "cook_started" for name, _ in ev2))

    def test_serve_eat_paid_with_tip_and_reputation_cap(self):
        sc = {
            "player": {"pos": [9, 2]},
            "hand": "ca_loc_nuong_trui",
            "stock": {"ca_loc": 1},
            "reputation": 4.9,
            "customers": [_waiting_customer(patience=3000, reserved={})],
        }
        sim = QuanSim(self.tuning, sc, Streams(1), IdAllocator())

        ev_serve = sim.step(_inp(interact=True))
        self.assertIn(("served", {"table_id": "T1", "dish": "ca_loc_nuong_trui"}), ev_serve)
        self.assertIsNone(sim.hand)
        self.assertEqual(sim.customers[0]["state"], "eating")

        eat_ticks = round(self.tuning["quan"]["eat_s"] * self.tuning["tick_hz"])
        paid_events = []
        for _ in range(eat_ticks):
            paid_events.extend(sim.step(_inp()))

        self.assertIn(("paid", {"customer_id": "C1", "money": 60, "tip": 12}), paid_events)
        self.assertEqual(sim.money, 72)
        self.assertEqual(sim.earned, 72)
        self.assertEqual(sim.shift_earned, 72)
        self.assertEqual(sim.reputation, 5.0)
        self.assertEqual(sim.customers, [])

    def test_serve_slow_customer_gives_no_tip(self):
        sc = {
            "player": {"pos": [9, 2]},
            "hand": "ca_loc_nuong_trui",
            "reputation": 3.0,
            "customers": [_waiting_customer(patience=1000, reserved={})],
        }
        sim = QuanSim(self.tuning, sc, Streams(1), IdAllocator())
        sim.step(_inp(interact=True))

        eat_ticks = round(self.tuning["quan"]["eat_s"] * self.tuning["tick_hz"])
        paid_events = []
        for _ in range(eat_ticks):
            paid_events.extend(sim.step(_inp()))

        self.assertIn(("paid", {"customer_id": "C1", "money": 60, "tip": 0}), paid_events)
        self.assertEqual(sim.money, 60)
        self.assertEqual(sim.reputation, 3.0)

    def test_shift_end_emits_quan_end_with_score_and_headless_deterministic(self):
        sc = {
            "player": {"pos": [9, 2]},
            "hand": "ca_loc_nuong_trui",
            "reputation": 3.2,
            "time_left_ticks": 5,
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish": "ca_loc_nuong_trui",
                    "state": "eating",
                    "patience_ticks": 2000,
                    "eat_ticks_left": 2,
                    "reserved": {},
                }
            ],
        }
        sess = Session("quan", self.tuning, sc, seed=1)
        all_events = []
        while not sess.done:
            all_events.extend(sess.step(_inp()))
        end_evs = [e for e in all_events if e["name"] == "quan_end"]
        self.assertEqual(len(end_evs), 1)
        self.assertEqual(end_evs[0]["data"]["score"], 72 + 100 * 3)
        self.assertEqual(sess.end_row()["score"], 372)

        with Workdir() as w:
            sc_path = w.path("sc.json")
            out1 = w.path("o1.jsonl")
            out2 = w.path("o2.jsonl")
            with open(sc_path, "w", encoding="utf-8") as f:
                json.dump({"quan": sc}, f)
            c1, e1 = run_headless("--mode", "quan", "--seed", "1", "--ticks", "10", "--scenario", sc_path, "--out", out1)
            c2, e2 = run_headless("--mode", "quan", "--seed", "1", "--ticks", "10", "--scenario", sc_path, "--out", out2)
            self.assertEqual(c1, 0, e1)
            self.assertEqual(c2, 0, e2)
            with open(out1, "rb") as f1, open(out2, "rb") as f2:
                self.assertEqual(f1.read(), f2.read())
            rows = read_jsonl(out1)
            self.assertEqual(len(events(rows, "quan_end")), 1)
