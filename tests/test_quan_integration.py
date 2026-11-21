"""Regression tests for merging P1-03 arrivals with P1-04 kitchen/settlement."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session
from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


FIXTURES = Path(__file__).parent / "fixtures"


class QuanIntegration(unittest.TestCase):
    def setUp(self):
        self.tuning = deepcopy(load_contract()["tuning"])
        self.q = self.tuning["quan"]
        self.hz = self.tuning["tick_hz"]
        self.first = self.q["first_customer_tick"]
        self.dish_id = "ca_loc_nuong_trui"
        self.menu = self.tuning["menu"][self.dish_id]
        self.cook_ticks = round(self.menu["cook_s"] * self.hz)

    @staticmethod
    def step(session, interact=False):
        return session.step(InputState((0, 0), {}, {"interact"} if interact else set()))

    def spawned_session(self, **updates):
        scenario = {"stock": dict(self.menu["recipe"]),
                    "player": {"pos": list(self.q["stoves"][0]["pos"])}}
        scenario.update(updates)
        session = Session("quan", self.tuning, scenario, seed=42)
        rows = []
        for _ in range(self.first):
            # An interact on the arrival tick cannot cook a newly spawned order.
            rows.extend(self.step(session, interact=True))
        self.assertEqual([r["name"] for r in rows], ["customer_arrived"])
        self.assertEqual(session.sim.stoves[0]["state"], "idle")
        self.assertEqual(session.sim.customers[0]["patience_ticks_left"],
                         round(self.q["patience_s"] * self.hz))
        return session

    def test_headless_spawn_cook_serve_pay_is_deterministic(self):
        # Reuse the movement route, but create the customer through the real scheduler.
        fixture = json.loads((FIXTURES / "p1_04_quan.json").read_text(encoding="utf-8"))
        fixture["quan"].pop("customers")
        fixture["quan"]["random_customers"] = True
        inputs = json.loads((FIXTURES / "p1_04_inputs.json").read_text(encoding="utf-8"))
        for frame in inputs["frames"]:
            frame["tick"] += self.first
        with Workdir() as work:
            scenario = write_json(work.path("scenario.json"), fixture)
            controls = write_json(work.path("inputs.json"), inputs)
            outputs = [work.path(name) for name in ("first.jsonl", "second.jsonl")]
            for out in outputs:
                code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "1200",
                                         "--scenario", scenario, "--inputs", controls,
                                         "--snapshot-every", "1", "--out", out)
                self.assertEqual(code, 0, err)
            self.assertEqual(Path(outputs[0]).read_bytes(), Path(outputs[1]).read_bytes())
            rows = read_jsonl(outputs[0])
        self.assertEqual([(r["tick"], r["name"]) for r in rows if r["type"] == "event"], [
            (self.first, "customer_arrived"), (self.first + 1, "cook_started"),
            (self.first + 361, "dish_ready"), (self.first + 361, "dish_picked"),
            (self.first + 398, "served"),
            (self.first + round(self.q["customer_interval_s"] * self.hz), "no_dish"),
            (self.first + 998, "paid"),
        ])
        before_cook = next(s for s in snapshots(rows) if s["tick"] == self.first)
        after_cook = next(s for s in snapshots(rows) if s["tick"] == self.first + 1)
        patience = round(self.q["patience_s"] * self.hz)
        self.assertEqual(before_cook["customers"][0]["patience_ticks_left"], patience)
        self.assertEqual(after_cook["customers"][0]["patience_ticks_left"], patience - 1)
        self.assertEqual(before_cook["stock"], self.menu["recipe"])
        self.assertEqual(after_cook["stock"], {})
        self.assertEqual(len(events(rows, "paid")), 1)
        self.assertEqual((rows[-1]["money"], rows[-1]["earned"], rows[-1]["reputation"],
                          rows[-1]["score"]), (72, 72, 3.2, 372))

    def test_spawned_customer_timeout_cleans_each_dish_location_once(self):
        for location in ("cooking", "ready", "hand"):
            with self.subTest(location=location):
                session = self.spawned_session()
                self.assertEqual(self.step(session, True)[0]["name"], "cook_started")
                if location != "cooking":
                    for _ in range(self.cook_ticks):
                        self.step(session)
                    self.assertEqual(session.sim.stoves[0]["state"], "ready")
                if location == "hand":
                    self.assertEqual(self.step(session, True)[0]["name"], "dish_picked")
                customer = session.sim.customers[0]
                customer["patience_ticks_left"] = 1
                rows = self.step(session)
                self.assertEqual([r["name"] for r in rows], ["customer_left"])
                self.assertEqual(rows[0]["data"]["order_id"], customer["id"])
                self.assertEqual(rows[0]["data"]["reason"], "patience")
                self.assertEqual(session.sim.reputation,
                                 self.q["reputation_initial"] + self.q["left_reputation_delta"])
                self.assertEqual(session.sim.customers, [])
                self.assertEqual(session.sim.snapshot()["stock"], {})
                self.assertEqual(session.sim.stoves[0]["state"], "idle")
                self.assertIsNone(session.sim.hand)
                self.assertEqual(self.step(session), [])

    def test_spawned_customer_served_at_zero_patience_on_closing_tick(self):
        closing_tick = self.first + 1 + self.cook_ticks + 2
        session = self.spawned_session(time_left_ticks=closing_tick)
        self.step(session, True)
        for _ in range(self.cook_ticks):
            self.step(session)
        self.step(session, True)
        customer = session.sim.customers[0]
        customer["patience_ticks_left"] = 1
        session.sim.pos = list(session.sim.tables[0]["pos"])
        rows = self.step(session, True)
        self.assertEqual([r["name"] for r in rows], ["served", "paid", "quan_end"])
        self.assertTrue(all(r["tick"] == closing_tick for r in rows))
        self.assertEqual(rows[0]["data"]["patience_ticks_left"], 0)
        self.assertEqual(rows[1]["data"]["reason"], "closing")
        self.assertEqual(rows[1]["data"]["amount"], self.menu["price"])
        self.assertEqual(session.sim.money, self.menu["price"])
        self.assertEqual(session.sim.reputation, self.q["reputation_initial"])
        self.assertEqual(session.sim.customers, [])
        self.assertTrue(session.done)
        self.assertEqual(self.step(session), [])
