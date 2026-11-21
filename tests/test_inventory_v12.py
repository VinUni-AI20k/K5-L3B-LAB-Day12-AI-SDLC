"""Adapter kho v1.2 (TV1, T301–T303). Contract đang chạy vẫn là 1.1 nên test gọi thẳng hàm."""

import json
import math
import os
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inventory import (
    decay_units_per_tick,
    read_inventory,
    units_to_fresh,
    write_inventory,
)
from chonoi.sim.day import DaySim
from chonoi.ids import IdAllocator
from chonoi.rng import Streams

from helpers import ROOT, Workdir


class InventoryV12(unittest.TestCase):
    def test_v11_van_nhan_kho_dem_va_tu_choi_mang(self):
        with Workdir() as w:
            path = w.path("inv.json")
            write_inventory(path, {"ca_loc": 1, "bong_sung": 0}, version="1.1")
            self.assertEqual(read_inventory(path, version="1.1"), {"ca_loc": 1})
            write_inventory(path, [], version="1.2")
            with self.assertRaises(BadInput):
                read_inventory(path, version="1.1")

    def test_v12_tu_choi_kho_dem_id_trung_va_fresh_ngoai_mien(self):
        with Workdir() as w:
            counted = w.path("c.json")
            write_inventory(counted, {"ca_linh": 1}, version="1.1")
            with self.assertRaises(BadInput):
                read_inventory(counted, version="1.2")
            for items in (
                [{"id": "I1", "kind": "ca_linh", "fresh": 30}, {"id": "I1", "kind": "ca_loc", "fresh": 10}],
                [{"id": "I1", "kind": "ca_linh", "fresh": 100.1}],
                [{"id": "I1", "kind": "ca_linh", "fresh": float("nan")}],
                [{"id": "I1", "kind": "ca_linh", "fresh": True}],
                [{"id": "", "kind": "ca_linh", "fresh": 1}],
                [{"id": "I1", "kind": "ca_la", "fresh": 1}],
            ):
                path = w.path("bad.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"items": items}, f)
                with self.assertRaises(BadInput):
                    read_inventory(path, version="1.3")

    def test_ghi_nguyen_tu_sap_id_va_giu_nguong_30(self):
        with Workdir() as w:
            path = w.path("inv.json")
            fresh = units_to_fresh(30 * 240 - 2)  # một tick gather từ đúng 30
            self.assertLess(fresh, 30)
            write_inventory(path, [
                {"id": "I10", "kind": "ca_loc", "fresh": 97.5},
                {"id": "I2", "kind": "ca_linh", "fresh": fresh},
            ], version="1.2")
            self.assertFalse(any(name.endswith(".tmp") for name in os.listdir(w._d.name)))
            loaded = read_inventory(path, version="1.2")
            self.assertEqual([item["id"] for item in loaded], ["I2", "I10"])
            self.assertLess(loaded[0]["fresh"], 30)
            self.assertTrue(math.isclose(loaded[1]["fresh"], 97.5))

    def test_decay_units_khop_de(self):
        self.assertEqual(decay_units_per_tick(0.5), 2)
        self.assertEqual(decay_units_per_tick(0.25), 1)
        fr = load_contract(os.path.join(ROOT, "game.contract.json"))["tuning"]["freshness"]
        self.assertEqual(fr, {
            "initial": 100, "gather_decay_per_s": 0.5,
            "quan_decay_per_s": 0.25, "spoiled_below": 30,
        })


class SoakPlan(unittest.TestCase):
    def test_ngay_6_lap_ke_hoach_ngay_1(self):
        tuning = load_contract()["tuning"]
        sim = DaySim(tuning, {}, Streams(1), IdAllocator(), days=1)
        self.assertEqual(sim._plan_for(6)["dishes"], sim._plan_for(1)["dishes"])
        self.assertEqual(sim._plan_for(10)["dishes"], sim._plan_for(5)["dishes"])
