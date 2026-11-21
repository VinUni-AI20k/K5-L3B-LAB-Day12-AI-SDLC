"""P3-04 Quán itemized stock, freshness and freshness-priced cooking rules."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


TUNING = load_contract()["tuning"]
FRESH = TUNING["freshness"]
Q = TUNING["quan"]
HZ = TUNING["tick_hz"]
FIRST = Q["first_customer_tick"]


def item(ident, kind="ca_loc", fresh=100):
    return {"id": ident, "kind": kind, "fresh": fresh}


def customer(ident, table, item_ids, order_tick=0):
    return {"id": ident, "table_id": table, "dish_id": "ca_loc_nuong_trui",
            "order_tick": order_tick, "reserved": item_ids}


def sim(scenario=None, stock=(), tuning=None):
    return QuanSim(tuning or TUNING, scenario or {}, Streams(4), IdAllocator(), inventory=list(stock))


def step_many(s, count):
    inputs = InputPlayer([])
    events = []
    for _ in range(count):
        events.extend(s.step(inputs.advance(s.sim_tick)))
    return events


class FreshnessAndReservation(unittest.TestCase):
    def test_count_adapter_and_locked_freshness_price_for_tip(self):
        adapted = QuanSim(TUNING, {}, Streams(4), IdAllocator(), inventory={"ca_loc": 1},
                          contract_version="1.2")
        self.assertEqual(adapted.stock[0]["kind"], "ca_loc")
        self.assertEqual(adapted.stock[0]["fresh"], FRESH["fresh_max"] * FRESH["units_per_point"])

        scenario = {"random_customers": False, "player": {"pos": [9, 1.8]},
                    "hand": {"order_id": "K1", "dish_id": "ca_loc_nuong_trui", "base_price": 13},
                    "customers": [{"id": "K1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "assigned", "reserved": []}]}
        s = sim(scenario, [item("I1")])
        player = InputPlayer([{"tick": 0, "interact": True}])
        rows = s.step(player.advance(0))
        served = next(data for name, data in rows if name == "served")
        self.assertEqual((served["base_price"], served["tip"]), (13, 2))

    def test_quan_decay_includes_reserved_stock_and_spoil_event_is_id_sorted(self):
        stocks = [item("I10", fresh=30.004), item("I2", fresh=30.004)]
        scenario = {"random_customers": False,
                    "customers": [customer("K1", "T1", ["I10"]), customer("K2", "T2", ["I2"])]}
        t = copy.deepcopy(TUNING)
        t["quan"]["tables"] += [{"id": "T2", "pos": [13, 2]}]
        s = sim(scenario, stocks, t)
        self.assertEqual(s.stock[0]["fresh"], round(30.004 * FRESH["units_per_point"]))
        events = step_many(s, 2)
        spoiled = [data["item_id"] for name, data in events if name == "spoiled"]
        self.assertEqual(spoiled, ["I2", "I10"])
        self.assertEqual(s.stock[0]["fresh"], round(30.004 * FRESH["units_per_point"]) - 2)

    def test_spoiled_orders_release_then_re_reserve_once_in_order(self):
        stocks = [item("I1", fresh=30.004), item("I2", fresh=30.004), item("I3", fresh=31)]
        scenario = {"random_customers": False,
                    "customers": [customer("K2", "T2", ["I2"], order_tick=2),
                                  customer("K1", "T1", ["I1"], order_tick=1)]}
        t = copy.deepcopy(TUNING)
        t["quan"]["tables"] += [{"id": "T2", "pos": [13, 2]}]
        s = sim(scenario, stocks, t)
        step_many(s, 2)
        customers = {c["id"]: c for c in s.customers}
        self.assertEqual((customers["K1"]["order_status"], customers["K1"]["reserved"]),
                         ("reserved", ["I3"]))
        self.assertEqual((customers["K2"]["order_status"], customers["K2"]["reserved"]),
                         ("unfulfillable", []))

    def test_reservation_uses_freshest_then_id_order(self):
        s = sim(stock=[item("I10", fresh=80), item("I2", fresh=80)])
        events = step_many(s, FIRST)
        self.assertTrue(any(name == "customer_arrived" for name, _ in events))
        self.assertEqual(s.customers[0]["reserved"], ["I2"])
        self.assertEqual(s.snapshot()["customers"][0]["reserved"], ["I2"])

    def test_freshness_price_and_itemized_cook_payload(self):
        stocks = [item("I10", "ca_loc", 80), item("I2", "bong_dien_dien", 60)]
        s = sim({"random_customers": False, "player": {"pos": [2, 8]},
                 "customers": [{"id": "K1", "table_id": "T1", "dish_id": "canh_chua_ca_loc",
                                "reserved": ["I10", "I2"]}]}, stocks)
        inputs = InputPlayer([{"tick": 0, "interact": True}])
        rows = s.step(inputs.advance(0))
        event = next(data for name, data in rows if name == "cook_started")
        decay = round(FRESH["decay_per_s"]["quan"] * FRESH["units_per_point"] / HZ)
        fresh_units = sum(round(x["fresh"] * FRESH["units_per_point"]) - decay for x in stocks)
        expected = TUNING["menu"]["canh_chua_ca_loc"]["price"] * fresh_units // (
            100 * FRESH["units_per_point"] * len(stocks))
        self.assertEqual(event["base_price"], expected)
        self.assertEqual([(x["kind"], x["id"]) for x in event["items"]],
                         [("bong_dien_dien", "I2"), ("ca_loc", "I10")])
        self.assertEqual(set(event["items"][0]), {"id", "kind", "fresh"})


if __name__ == "__main__":
    unittest.main()
