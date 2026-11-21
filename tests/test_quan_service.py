"""Kiểm thử phục vụ Quán theo PRD-0 + kho cá thể v1.2."""

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


def _reserved_customer(cid="C1", table_id="T1", dish_id="ca_loc_nuong_trui", patience=3600, order_tick=0, reserved=None):
    return {
        "id": cid,
        "table_id": table_id,
        "dish_id": dish_id,
        "order_tick": order_tick,
        "state": "waiting",
        "patience_ticks_left": patience,
        "eat_ticks_left": 0,
        "order_status": "reserved",
        "reserved": reserved if reserved is not None else ["I1"],
    }


def _stock(*kinds):
    return [{"id": f"I{i}", "kind": k, "fresh": 100} for i, k in enumerate(kinds, 1)]


class QuanServiceTests(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_cook_countdown_ready_ticks_and_pickup_at_stove(self):
        sc = {
            "player": {"pos": [2, 8]},
            "stock": _stock("ca_loc", "ca_loc"),
            "random_customers": False,
            "customers": [_reserved_customer()],
        }
        sim = QuanSim(self.tuning, sc, Streams(1), IdAllocator())

        ev1 = sim.step(_inp(interact=True))
        self.assertIn(("cook_started", {
            "stove_id": "B1",
            "order_id": "C1",
            "dish_id": "ca_loc_nuong_trui",
            "items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
            "base_price": 60,
        }), ev1)
        self.assertEqual([it["id"] for it in sim.stock], ["I2"])
        self.assertEqual(sim.customers[0]["reserved"], [])
        self.assertEqual(sim.customers[0]["order_status"], "assigned")
        self.assertEqual(sim.stoves[0]["state"], "cooking")
        self.assertEqual(sim.stoves[0]["dish"], {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60})

        cook_ticks = round(self.tuning["menu"]["ca_loc_nuong_trui"]["cook_s"] * self.tuning["tick_hz"])
        ready_events = []
        for _ in range(cook_ticks):
            ready_events.extend(sim.step(_inp()))
        self.assertIn(("dish_ready", {
            "stove_id": "B1",
            "order_id": "C1",
            "dish_id": "ca_loc_nuong_trui",
        }), ready_events)
        self.assertEqual(sim.stoves[0]["state"], "ready")
        self.assertEqual(sim.stoves[0]["ready_ticks"], 0)

        sim.step(_inp())
        self.assertEqual(sim.stoves[0]["ready_ticks"], 1)

        ev_pick = sim.step(_inp(interact=True))
        self.assertIn(("dish_picked", {
            "stove_id": "B1",
            "order_id": "C1",
            "dish_id": "ca_loc_nuong_trui",
        }), ev_pick)
        self.assertEqual(sim.hand, {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60})
        self.assertEqual(sim.stoves[0]["state"], "idle")
        self.assertIsNone(sim.stoves[0]["dish"])

    def test_nearest_interact_only_no_fallback_and_tie_stove_before_table(self):
        payload = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        sc = {
            "player": {"pos": [5.0, 5.0]},
            "stock": _stock("ca_loc"),
            "random_customers": False,
            "hand": payload,
            "stoves": [{"id": "B1", "pos": [4.1, 5.0]}],
            "tables": [{"id": "T1", "pos": [6.2, 5.0]}],
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "order_status": "assigned", "reserved": [],
            }],
        }
        sim = QuanSim(self.tuning, sc, Streams(1), IdAllocator())
        self.assertEqual(sim.step(_inp(interact=True)), [])
        self.assertEqual(sim.hand, payload)

        sc_tie = {
            "player": {"pos": [5.0, 5.0]},
            "stock": _stock("ca_loc", "ca_loc"),
            "random_customers": False,
            "hand": {"order_id": "C2", "dish_id": "goi_bong_sung", "base_price": 40},
            "stoves": [{"id": "B1", "pos": [4.0, 5.0]}],
            "tables": [{"id": "T1", "pos": [6.0, 5.0]}, {"id": "T2", "pos": [6.0, 5.0]}],
            "customers": [
                _reserved_customer("C1", "T1"),
                {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "order_status": "assigned", "reserved": []},
            ],
        }
        sim_tie = QuanSim(self.tuning, sc_tie, Streams(1), IdAllocator())
        ev_tie = sim_tie.step(_inp(interact=True))
        self.assertEqual([e[0] for e in ev_tie], ["cook_started"])

    def test_oldest_order_by_order_tick_then_table_id(self):
        self.tuning["quan"]["tables"] = [
            {"id": "T1", "pos": [9, 2]},
            {"id": "T2", "pos": [13, 2]},
            {"id": "T10", "pos": [13, 6]},
        ]
        sc = {
            "player": {"pos": [2, 8]},
            "random_customers": False,
            "stock": _stock("ca_loc", "ca_loc", "ca_loc"),
            "customers": [
                _reserved_customer("C1", "T10", order_tick=5, reserved=["I1"]),
                _reserved_customer("C2", "T2", order_tick=5, reserved=["I2"]),
                _reserved_customer("C3", "T1", order_tick=10, reserved=["I3"]),
            ],
        }
        sim = QuanSim(self.tuning, sc, Streams(1), IdAllocator())
        ev = sim.step(_inp(interact=True))
        self.assertEqual(ev[0][1]["order_id"], "C2")

    def test_serve_eat_paid_with_floor_tip_and_reputation_cap(self):
        sc = {
            "player": {"pos": [9, 2]},
            "random_customers": False,
            "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
            "reputation": 4.9,
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "patience_ticks_left": 3000, "order_status": "assigned", "reserved": [],
            }],
        }
        sim = QuanSim(self.tuning, sc, Streams(1), IdAllocator())

        ev_serve = sim.step(_inp(interact=True))
        self.assertIn(("served", {
            "order_id": "C1",
            "table_id": "T1",
            "dish_id": "ca_loc_nuong_trui",
            "patience_ticks_left": 2999,
            "base_price": 60,
            "tip": 12,
        }), ev_serve)
        self.assertIsNone(sim.hand)
        self.assertEqual(sim.customers[0]["state"], "eating")
        self.assertEqual(sim.customers[0]["order_status"], "served")

        eat_ticks = round(self.tuning["quan"]["eat_s"] * self.tuning["tick_hz"])
        paid_events = []
        for _ in range(eat_ticks):
            paid_events.extend(sim.step(_inp()))

        self.assertIn(("paid", {
            "order_id": "C1",
            "table_id": "T1",
            "base_price": 60,
            "tip": 12,
            "amount": 72,
            "reason": "finished_eating",
        }), paid_events)
        self.assertEqual(sim.money, 72)
        self.assertEqual(sim.earned, 72)
        self.assertEqual(sim.shift_earned, 72)
        self.assertEqual(sim.reputation, 5.0)
        self.assertEqual(sim.customers, [])

    def test_serve_slow_customer_and_exact_patience_zero_still_valid(self):
        sc = {
            "player": {"pos": [9, 2]},
            "random_customers": False,
            "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
            "reputation": 3.0,
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "patience_ticks_left": 1, "order_status": "assigned", "reserved": [],
            }],
        }
        sim = QuanSim(self.tuning, sc, Streams(1), IdAllocator())
        ev_serve = sim.step(_inp(interact=True))
        self.assertEqual(ev_serve[0][1]["patience_ticks_left"], 0)
        self.assertEqual(ev_serve[0][1]["tip"], 0)

        eat_ticks = round(self.tuning["quan"]["eat_s"] * self.tuning["tick_hz"])
        paid_events = []
        for _ in range(eat_ticks):
            paid_events.extend(sim.step(_inp()))

        self.assertIn(("paid", {
            "order_id": "C1",
            "table_id": "T1",
            "base_price": 60,
            "tip": 0,
            "amount": 60,
            "reason": "finished_eating",
        }), paid_events)
        self.assertEqual(sim.reputation, 3.0)

    def test_closing_pays_newly_served_and_drops_waiting_without_rep_loss(self):
        sc = {
            "player": {"pos": [9, 2]},
            "random_customers": False,
            "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
            "reputation": 3.0,
            "time_left_ticks": 1,
            "stock": _stock("ca_loc"),
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                 "patience_ticks_left": 3000, "order_status": "assigned", "reserved": []},
                _reserved_customer("C2", "T2", patience=10),
            ],
        }
        sim = QuanSim(self.tuning, sc, Streams(1), IdAllocator())
        evs = sim.step(_inp(interact=True))
        self.assertEqual([e[0] for e in evs], ["served", "paid", "customer_left", "quan_end"])
        self.assertEqual(evs[1][1]["reason"], "closing")
        self.assertEqual(evs[2][1], {"order_id": "C2", "table_id": "T2", "reason": "closing", "reputation": 3.2})
        self.assertEqual(evs[3][1]["shift_earned"], 72)

    def test_shift_end_emits_quan_end_with_score_and_headless_deterministic(self):
        sc = {
            "player": {"pos": [9, 2]},
            "random_customers": False,
            "reputation": 3.2,
            "time_left_ticks": 5,
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "state": "eating",
                    "patience_ticks_left": 2000,
                    "eat_ticks_left": 2,
                    "order_status": "served",
                    "reserved": [],
                    "base_price": 60,
                    "tip": 12,
                }
            ],
        }
        sess = Session("quan", self.tuning, sc, seed=1)
        all_events = []
        while not sess.done:
            all_events.extend(sess.step(_inp()))
        end_evs = [e for e in all_events if e["name"] == "quan_end"]
        self.assertEqual(len(end_evs), 1)
        self.assertEqual(end_evs[0]["data"], {
            "reason": "time",
            "money": 72,
            "earned": 72,
            "shift_earned": 72,
            "reputation": 3.4,
        })
        self.assertEqual(sess.end_row()["score"], 72 + 300)

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


if __name__ == "__main__":
    unittest.main()
