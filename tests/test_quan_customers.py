import os
import unittest
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session
from helpers import ROOT, Workdir, events, read_jsonl, run_headless, snapshots, write_json


class QuanCustomersTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_headless_customer_reserves_from_inventory_at_scheduled_tick(self):
        first = self.tuning["quan"]["first_customer_tick"]
        with Workdir() as work:
            inventory = write_json(work.path("kho.json"), {"items": [
                {"id": "I1", "kind": "ca_loc", "fresh": 100.0},
                {"id": "I2", "kind": "bong_sung", "fresh": 100.0}]})
            out = work.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "17", "--ticks", str(first),
                                     "--snapshot-every", "1", "--inventory", inventory, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
        before, after = snapshots(rows)[-2:]
        self.assertEqual(before["customers"], [])
        self.assertEqual([(item["id"], item["kind"]) for item in after["stock"]],
                         [("I1", "ca_loc"), ("I2", "bong_sung")])
        self.assertAlmostEqual(after["stock"][0]["fresh"], 100 - first * 0.25 / self.tuning["tick_hz"])
        self.assertEqual(len(after["customers"]), 1)
        customer = after["customers"][0]
        self.assertEqual(customer["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(customer["reserved"], ["I1"])
        self.assertEqual(customer["state"], "waiting")
        self.assertEqual(customer["order_status"], "reserved")
        self.assertEqual(customer["order_tick"], first)
        self.assertEqual(customer["patience_ticks_left"],
                         round(self.tuning["quan"]["patience_s"] * self.tuning["tick_hz"]))
        arrival, = events(rows, "customer_arrived")
        self.assertEqual(arrival["tick"], first)
        self.assertEqual(arrival["data"], {
            "order_id": customer["id"], "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
        })
        self.assertEqual(after["tables"][0]["customer_id"], customer["id"])

    def test_expiry_refunds_only_held_stock_and_releases_table(self):
        self.tuning["quan"]["tables"].append({"id": "T2", "pos": [8, 2]})
        scenario = {
            "stock": {"ca_loc": 1}, "random_customers": False,
            "hand": {"order_id": "C2", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 1},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned",
                 "patience_ticks_left": 1, "reserved": {}},
            ],
        }
        session = Session("quan", self.tuning, scenario, seed=17)
        self.assertEqual(session.snapshot()["stock"], {"ca_loc": 1})
        player = InputPlayer([])
        departures = session.step(player.advance(0))
        quan = self.tuning["quan"]
        expected_reputation = quan["reputation_initial"]
        for event, order_id, table_id in zip(departures, ("C1", "C2"), ("T1", "T2"), strict=True):
            expected_reputation += quan["left_reputation_delta"]
            self.assertEqual(event["name"], "customer_left")
            self.assertEqual(event["data"], {
                "order_id": order_id, "table_id": table_id, "reason": "patience",
                "reputation": expected_reputation,
            })
        self.assertEqual(session.snapshot()["stock"], {"ca_loc": 1})
        self.assertIsNone(session.snapshot()["hand"])
        self.assertEqual(session.snapshot()["customers"], [])
        self.assertTrue(all(table["customer_id"] is None for table in session.snapshot()["tables"]))
        self.assertEqual(session.step(player.advance(1)), [])
        self.assertEqual(session.snapshot()["stock"], {"ca_loc": 1})

    def test_two_tables_cannot_reserve_the_same_ingredient(self):
        quan = self.tuning["quan"]
        quan["tables"].append({"id": "T2", "pos": [8, 2]})
        session = Session("quan", self.tuning, {"stock": {"ca_loc": 1}}, seed=17)
        first = quan["first_customer_tick"]
        second = first + round(quan["customer_interval_s"] * self.tuning["tick_hz"])
        player = InputPlayer([])
        actual = []
        for tick in range(second):
            actual.extend(session.step(player.advance(tick)))
        self.assertEqual([(event["name"], event["tick"]) for event in actual],
                         [("customer_arrived", first), ("no_dish", second)])
        self.assertEqual(actual[-1]["data"], {})
        self.assertEqual(session.snapshot()["stock"], {"ca_loc": 1})
        self.assertEqual(session.snapshot()["tables"][1]["customer_id"], None)

    def test_closing_releases_reserved_order_without_penalty_or_new_customer(self):
        quan = self.tuning["quan"]
        quan["first_customer_tick"] = 1
        scenario = {
            "stock": {"ca_loc": 1}, "time_left_ticks": 1,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                           "patience_ticks_left": 1}],
        }
        session = Session("quan", self.tuning, scenario, seed=17)
        rows = session.step(InputPlayer([]).advance(0))
        self.assertEqual([row["name"] for row in rows], ["customer_left", "quan_end"])
        self.assertEqual(rows[0]["data"], {
            "order_id": "C1", "table_id": "T1", "reason": "closing",
            "reputation": quan["reputation_initial"],
        })
        self.assertEqual(session.snapshot()["customers"], [])
        self.assertEqual(session.snapshot()["stock"], {"ca_loc": 1})

    def test_customer_fixture_conflicts_fail_before_output(self):
        customer = {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}
        dish = {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40}
        assigned = dict(customer, order_status="assigned")
        cases = {
            "over-reserved": {"stock": {"bong_sung": 1}, "customers": [customer]},
            "wrong-recipe": {"stock": {"ca_loc": 1}, "customers": [dict(customer, reserved={"ca_loc": 1})]},
            "assigned-without-dish": {"customers": [assigned]},
            "duplicate-dish": {
                "customers": [assigned], "hand": dish,
                "stoves": [{"id": "B1", "state": "ready", "dish": dish}],
            },
            "eating-without-tip": {
                "customers": [dict(customer, order_status="served", state="eating", eat_ticks_left=1,
                                   base_price=40)],
            },
        }
        with Workdir() as work:
            for case, scenario in cases.items():
                with self.subTest(case=case):
                    fixture = write_json(work.path("scenario.json"), {"quan": scenario})
                    out = work.path(f"{case}.jsonl")
                    code, err = run_headless("--mode", "quan", "--seed", "17", "--ticks", "0",
                                             "--scenario", fixture, "--out", out)
                    self.assertEqual(code, 2, err)
                    self.assertFalse(os.path.exists(out))

    def test_seeded_orders_are_byte_stable(self):
        with Workdir() as work:
            inventory = os.path.join(ROOT, "docs", "contracts", "inventory.sample.json")
            outputs = [work.path(name) for name in ("first.jsonl", "second.jsonl")]
            for out in outputs:
                code, err = run_headless("--mode", "quan", "--seed", "17", "--ticks", "600",
                                         "--inventory", inventory, "--out", out)
                self.assertEqual(code, 0, err)
            self.assertEqual(Path(outputs[0]).read_bytes(), Path(outputs[1]).read_bytes())
