"""P3-03 stock and reservations with the v1.2 tuning."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import BUTTONS_V11, InputPlayer
from chonoi.runner import Session
from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


def item(item_id, fresh=100, kind="ca_loc"):
    return {"id": item_id, "kind": kind, "fresh": fresh}


def customer(customer_id, table="T1", **fields):
    return {"id": customer_id, "table_id": table, "dish_id": "ca_loc_nuong_trui", **fields}


class RestaurantStockTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def quan(self, items, customers=(), **scenario):
        return Session("quan", self.tuning, {
            "stock": items, "customers": list(customers), "random_customers": False, **scenario,
        }, 17)

    @staticmethod
    def step(session, count, frames=()):
        player = InputPlayer(frames, BUTTONS_V11)
        return [event for _ in range(count) for event in session.step(player.advance(session.tick))]

    def test_arrivals_take_freshest_then_natural_id_without_overlapping_claims(self):
        self.tuning["quan"].update(first_customer_tick=1, customer_interval_s=0.1)
        session = self.quan([item("I10", 90), item("I3", 95), item("I2", 90), item("I1", 29)],
                            random_customers=True)
        self.assertEqual([row["name"] for row in self.step(session, 19)],
                         ["customer_arrived", "customer_arrived", "customer_arrived", "no_dish"])
        self.assertEqual([c["reserved"] for c in session.snapshot()["customers"]], [["I3"], ["I2"], ["I10"]])
        self.assertEqual([i["id"] for i in session.snapshot()["stock"]], ["I1", "I2", "I3", "I10"])

    def test_fixture_fills_omitted_claims_in_order_and_respects_explicit_claims(self):
        session = self.quan([item("I9", 100), item("I4", 90), item("I6", 80), item("I8", 70)], [
            customer("C1", "T1", order_tick=2),
            customer("C4", "T3", order_tick=1),
            customer("C2", "T2", order_tick=1),
            customer("C3", "T4", order_tick=3, reserved=["I9"]),
        ])
        self.assertEqual({c["id"]: c["reserved"] for c in session.snapshot()["customers"]},
                         {"C1": ["I8"], "C2": ["I4"], "C3": ["I9"], "C4": ["I6"]})

    def test_spoil_event_crosses_exact_threshold_once_and_sorts_natural_ids(self):
        session = self.quan([item("I10", 30), item("I2", 30), item("I1", 30.25), item("I3", 0.001)])
        rows = self.step(session, 60)
        self.assertEqual([(e["tick"], e["data"]) for e in rows], [
            (1, {"item_id": "I2", "kind": "ca_loc", "location": "stock"}),
            (1, {"item_id": "I10", "kind": "ca_loc", "location": "stock"}),
        ])
        self.assertEqual(session.snapshot()["stock"][0]["fresh"], 30)
        self.assertEqual(session.snapshot()["stock"][2]["fresh"], 0)
        rows = self.step(session, 2)
        self.assertEqual([(e["name"], e["tick"], e["data"]["item_id"]) for e in rows], [("spoiled", 61, "I1")])
        self.assertEqual(len(session.snapshot()["stock"]), 4)

    def test_replacements_follow_order_tick_then_table_and_failed_customer_waits(self):
        session = self.quan([item("I1", 30), item("I2", 30), item("I3", 30), item("I5", 80), item("I4", 80)], [
            customer("C1", "T3", order_tick=5, reserved=["I1"], patience_ticks_left=3),
            customer("C5", "T2", order_tick=4, reserved=["I2"]),
            customer("C4", "T1", order_tick=4, reserved=["I3"]),
        ])
        rows = self.step(session, 1)
        self.assertEqual([e["data"]["item_id"] for e in rows], ["I1", "I2", "I3"])
        customers = {c["id"]: c for c in session.snapshot()["customers"]}
        self.assertEqual(customers["C4"]["reserved"], ["I4"])
        self.assertEqual(customers["C5"]["reserved"], ["I5"])
        self.assertEqual((customers["C1"]["state"], customers["C1"]["order_status"], customers["C1"]["reserved"]),
                         ("waiting", "unfulfillable", []))
        self.assertEqual(self.step(session, 1), [])
        left, = self.step(session, 1)
        self.assertEqual((left["tick"], left["name"], left["data"]["order_id"]), (3, "customer_left", "C1"))

    def test_replacement_releases_entire_claim_before_cooking_and_freezes_price(self):
        session = self.quan([
            item("I9", 31), item("I8", 30, "bong_dien_dien"),
            item("I2", 90), item("I1", 100, "bong_dien_dien"),
        ], [
            customer("C1", dish_id="canh_chua_ca_loc", reserved=["I9", "I8"]),
            customer("C2", "T2", order_status="assigned", reserved=[], base_price=48),
        ], player={"pos": [2, 8]}, stoves=[{
            "id": "B2", "state": "cooking", "cook_ticks_left": 1,
            "dish": {"order_id": "C2", "dish_id": "ca_loc_nuong_trui", "base_price": 48},
        }])
        rows = self.step(session, 1, [{"tick": 0, "interact": True}])
        self.assertEqual([e["name"] for e in rows], ["spoiled", "dish_ready", "cook_started"])
        payload = rows[-1]["data"]
        self.assertEqual([i["id"] for i in payload["items"]], ["I1", "I2"])
        self.assertEqual(payload["base_price"], 85)
        self.assertAlmostEqual(payload["items"][0]["fresh"], 100 - 1 / 240)
        self.assertEqual([i["id"] for i in session.snapshot()["stock"]], ["I8", "I9"])
        self.assertEqual(session.snapshot()["customers"][0]["reserved"], [])
        self.step(session, 40)
        self.assertEqual(session.snapshot()["stoves"][0]["dish"]["base_price"], 85)

    def test_pause_does_not_age_a_held_item_and_exactly_30_is_usable(self):
        session = self.quan([item("I1", 30.25)], [customer("C1")], player={"pos": [2, 8]})
        rows = self.step(session, 62, [
            {"tick": 0, "pause": True}, {"tick": 1, "pause": False},
            {"tick": 2, "pause": True}, {"tick": 61, "interact": True},
        ])
        self.assertEqual(session.sim_tick, 60)
        self.assertEqual([e["name"] for e in rows], ["paused", "resumed", "cook_started"])
        self.assertEqual(rows[-1]["data"]["items"], [item("I1", 30)])
        self.assertEqual(rows[-1]["data"]["base_price"], 18)

    def test_invalid_fixture_claims_are_rejected(self):
        stock = [item("I1"), item("I2", 29), item("I3", 100, "ca_linh")]
        for bad in (
            [customer("C1", reserved=["I1"]), customer("C2", "T2", reserved=["I1"])],
            [customer("C1", reserved=["I1", "I1"])],
            [customer("C1", reserved=["I2"])],
            [customer("C1", reserved=["I3"])],
            [customer("C1", reserved=["I99"])],
            [customer("C1", reserved={"ca_loc": 1})],
            [customer("C1", reserved=["I1"], order_status="unfulfillable")],
        ):
            with self.subTest(customers=bad), self.assertRaises(BadInput):
                self.quan(stock, bad)

    def test_day_receives_item_handoff_and_shop_does_not_decay_stock(self):
        session = Session("day", self.tuning, {"gather": {"time_left_ticks": 1, "hold": [item("I9", 30.25)]},
                                               "quan": {"time_left_ticks": 1}}, 17)
        rows = self.step(session, 1)
        handoff = events(rows, "gather_end")[0]["data"]["inventory"]["items"]
        self.assertEqual((session.snapshot()["phase_tick"], session.snapshot()["stock"]), (0, handoff))
        self.step(session, 1)
        shop_stock = session.snapshot()["stock"]
        self.assertAlmostEqual(shop_stock[0]["fresh"], handoff[0]["fresh"] - 1 / 240)
        self.step(session, 60)
        self.assertEqual(session.snapshot()["stock"], shop_stock)
        self.step(session, 1, [{"tick": session.tick, "shop_done": True}])
        self.assertEqual(session.snapshot()["stock"], [])

    def test_headless_v12_uses_item_files_and_rejects_bad_inputs_before_output(self):
        with Workdir() as work:
            output = work.path("out.jsonl")
            args = ("--mode", "quan", "--seed", "17", "--ticks", "0", "--out", output)
            with patch("helpers.headless_cmd", return_value=[sys.executable, "-m", "chonoi.headless"]):
                for value in ({"ca_loc": 1}, [item("I1"), item("I1")], [item("I1", -1)],
                              [item("I1", 101)], [item("I1", float("nan"))], [item("I1", kind="unknown")]):
                    source = write_json(work.path("stock.json"), {"items": value})
                    code, err = run_headless(*args, "--inventory", source)
                    self.assertEqual(code, 2, err)
                    self.assertFalse(Path(output).exists())
                items = [item("I10", 29.9999), item("I2", 99.99166666666666)]
                source = write_json(work.path("stock.json"), {"items": items})
                code, err = run_headless(*args, "--inventory", source)
                self.assertEqual(code, 0, err)
                self.assertEqual(snapshots(read_jsonl(output))[0]["stock"], [items[1], items[0]])
                Path(output).unlink()
                fixture = write_json(work.path("scenario.json"), {"quan": {
                    "stock": items, "customers": [customer("C1", reserved=["I10"])],
                }})
                code, err = run_headless(*args, "--scenario", fixture)
                self.assertEqual(code, 2, err)
                self.assertFalse(Path(output).exists())
