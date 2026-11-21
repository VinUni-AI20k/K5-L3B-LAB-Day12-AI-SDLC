"""Adapter v1.2 (TICKET-03 mục 1): cá thể, độ tươi bằng đơn vị, file kho cá thể. Chạy độc lập với version manifest."""

import copy
import json
import os
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inventory import read_inventory, write_inventory
from chonoi.items import (Freshness, ItemIds, decay, is_spoiled, is_v12, new_item, pick_freshest, price_by_fresh,
                          public_list, to_units, validate_public_items)

from helpers import Workdir, write_json

V12 = copy.deepcopy(load_contract()["tuning"])
V12.setdefault("freshness", {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30})
FR = Freshness(V12)


def item(i, kind, fresh):
    return {"id": i, "kind": kind, "fresh_units": to_units(fresh)}


class Units(unittest.TestCase):
    def test_rates_are_exact_integers(self):
        self.assertTrue(is_v12(V12))
        self.assertEqual((FR.initial, FR.gather_per_tick, FR.quan_per_tick, FR.spoiled_below), (24000, 2, 1, 7200))

    def test_fixture_at_30_spoils_on_first_gather_step(self):
        hold = [item("I1", "ca_linh", 30)]
        self.assertFalse(is_spoiled(hold[0], FR))
        self.assertEqual([it["id"] for it in decay(hold, FR.gather_per_tick, FR)], ["I1"])
        self.assertTrue(is_spoiled(hold[0], FR))
        self.assertEqual(decay(hold, FR.gather_per_tick, FR), [], "spoiled đúng một lần")

    def test_spoiled_sorted_by_id_and_clamped_at_zero(self):
        items = [item("I10", "ca_loc", 30), item("I2", "ca_loc", 30.002), item("I3", "ca_loc", 0)]
        self.assertEqual([it["id"] for it in decay(items, 1, FR)], ["I2", "I10"])
        self.assertEqual(items[2]["fresh_units"], 0)

    def test_quan_rate_crosses_30_after_exact_ticks(self):
        it = item("I1", "ca_loc", 30.5)  # 7320 đơn vị -> 120 tick quán còn 7200, tick 121 ươn
        hits = [t for t in range(1, 200) if decay([it], FR.quan_per_tick, FR)]
        self.assertEqual(hits, [121])


class Ids(unittest.TestCase):
    def test_continue_after_reserved(self):
        ids = ItemIds()
        for i in ("I1", "I7", "X3"):
            ids.reserve(i)
        self.assertEqual([ids.new(), ids.new()], ["I8", "I9"])
        self.assertEqual(new_item(ids, "ca_keo", FR), {"id": "I10", "kind": "ca_keo", "fresh_units": 24000})


class PickAndPrice(unittest.TestCase):
    def test_freshest_then_id_skip_spoiled(self):
        stock = [item("I3", "ca_linh", 80), item("I2", "ca_linh", 90), item("I9", "ca_linh", 90),
                 item("I4", "ca_linh", 29.9), item("I5", "ca_loc", 100)]
        self.assertEqual([it["id"] for it in pick_freshest(stock, "ca_linh", 3, FR)], ["I2", "I9", "I3"])
        self.assertEqual(pick_freshest(stock, "ca_linh", 4, FR), [], "cá ươn không dùng nấu")
        self.assertEqual([it["id"] for it in pick_freshest(stock, "ca_linh", 1, FR, exclude={"I2"})], ["I9"])

    def test_price_floor_on_average(self):
        self.assertEqual(price_by_fresh(120, [item("I1", "ca_linh", 100), item("I2", "ca_linh", 97.5)]), 118)
        self.assertEqual(price_by_fresh(60, [item("I1", "ca_loc", 30)]), 18)
        self.assertEqual(price_by_fresh(40, [item("I1", "bong_sung", 99.99), item("I2", "bong_sung", 99.99)]), 39)


class FileV12(unittest.TestCase):
    def test_round_trip_sorted_by_id_and_exact(self):
        with Workdir() as w:
            p = w.path("kho.json")
            hold = [item("I10", "ca_loc", 99.991666), item("I2", "ca_linh", 97.5)]
            hold[0]["fresh_units"] = 23998  # 99.991666... sau 1 bước gather
            write_inventory(p, hold)
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual([it["id"] for it in data["items"]], ["I2", "I10"])
            back = read_inventory(p, v12=True)
            self.assertEqual({it["id"]: it["fresh_units"] for it in back}, {"I2": 23400, "I10": 23998})
            write_inventory(p, [])
            with open(p, encoding="utf-8") as f:
                self.assertEqual(f.read(), '{"items":[]}\n')

    def test_reader_rejects_bad_v12(self):
        bad = [{"items": {"ca_loc": 1}},  # kho đếm v1.1
               {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 101}]},
               {"items": [{"id": "I1", "kind": "ca_loc", "fresh": -0.1}]},
               {"items": [{"id": "I1", "kind": "ca_tra", "fresh": 50}]},
               {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 50}, {"id": "I1", "kind": "ca_loc", "fresh": 40}]},
               {"items": [{"id": "", "kind": "ca_loc", "fresh": 50}]},
               {"items": [{"id": "I1", "kind": "ca_loc"}]},
               {"items": [{"id": "I1", "kind": "ca_loc", "fresh": True}]},
               {"items": [], "money": 0}]
        with Workdir() as w:
            for i, obj in enumerate(bad):
                p = write_json(w.path(f"b{i}.json"), obj)
                with self.assertRaises(BadInput, msg=obj):
                    read_inventory(p, v12=True)
            self.assertEqual(read_inventory(write_json(w.path("ok.json"), {"items": []}), v12=True), [])

    def test_validate_public_items_keeps_order(self):
        arr = [{"id": "I5", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "keo_neo", "fresh": 30}]
        out = validate_public_items(arr)
        self.assertEqual([it["id"] for it in out], ["I5", "I2"])
        self.assertEqual(public_list(out), arr)


if __name__ == "__main__":
    unittest.main()
