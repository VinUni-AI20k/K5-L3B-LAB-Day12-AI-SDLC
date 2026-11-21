"""Unit tests cho Phase 3 (M6.1-M6.3): freshness helper, inventory v1.2 (từ chối kho đếm mã 2) & scenario v1.2."""

import json
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.freshness import (
    FRESH_SCALE,
    calc_fresh_base_price,
    calc_tip,
    decay_units_per_tick,
    from_units,
    is_spoiled_units,
    to_units,
)
from chonoi.inventory import read_inventory, write_inventory_v12
from chonoi.scenario import load_scenario
from helpers import Workdir, write_json


class FreshnessHelperM6(unittest.TestCase):
    def test_exact_threshold_30_and_decay_units(self):
        self.assertEqual(decay_units_per_tick(0.5, 60), 2)
        self.assertEqual(decay_units_per_tick(0.25, 60), 1)
        u = to_units(30)
        self.assertEqual(u, 30 * FRESH_SCALE)
        self.assertFalse(is_spoiled_units(u, 30))
        # Giảm 1 tick gather (-2 đơn vị) -> ươn ngay ở tick 1
        u_after = u - decay_units_per_tick(0.5, 60)
        self.assertTrue(is_spoiled_units(u_after, 30))
        self.assertLess(from_units(u_after), 30.0)

    def test_exact_price_floor_and_tip(self):
        # 2 nguyên liệu fresh 100 và 50 -> avg = 75 -> 40 * 75 / 100 = 30
        bp = calc_fresh_base_price(40, [to_units(100), to_units(50)])
        self.assertEqual(bp, 30)
        self.assertEqual(calc_tip(bp, 0.2), 6)
        # 1 nguyên liệu fresh 99.9 -> floor(60 * 99.9 / 100) = 59
        self.assertEqual(calc_fresh_base_price(60, [to_units(99.9)]), 59)


class InventoryAndScenarioV12M6(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_inventory_v12_read_write_and_reject_counting_schema(self):
        with Workdir() as w:
            p_v12 = w.path("inv_v12.json")
            write_inventory_v12(p_v12, [
                {"id": "I10", "kind": "ca_loc", "fresh": 97.5},
                {"id": "I2", "kind": "ca_linh", "fresh": 100},
            ])
            with open(p_v12, encoding="utf-8") as f:
                raw = json.load(f)
            self.assertEqual([x["id"] for x in raw["items"]], ["I2", "I10"])
            loaded = read_inventory(p_v12, contract_version="1.2")
            self.assertEqual(len(loaded), 2)

            # File kho đếm v1.1 phải bị từ chối (BadInput -> mã 2) khi đọc ở v1.2
            p_old = write_json(w.path("inv_v11.json"), {"items": {"ca_loc": 1}})
            with self.assertRaises(BadInput):
                read_inventory(p_old, contract_version="1.2")

            # ID trùng hoặc fresh ngoài [0, 100] -> BadInput
            for bad in (
                {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I1", "kind": "ca_linh", "fresh": 80}]},
                {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 101}]},
                {"items": [{"id": "I1", "kind": "ca_loc", "fresh": -1}]},
            ):
                p_bad = write_json(w.path("bad.json"), bad)
                with self.assertRaises(BadInput):
                    read_inventory(p_bad, contract_version="1.2")

    def test_scenario_v12_valid_and_conflicts(self):
        with Workdir() as w:
            # Hợp lệ: gather.hold mảng cá thể
            sc_g = write_json(w.path("g.json"), {
                "gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}], "random_fish": False, "monsters": []}
            })
            self.assertEqual(len(load_scenario(sc_g, "gather", self.tuning, contract_version="1.2")["hold"]), 1)

            # Hợp lệ: quan.stock mảng cá thể + reserved bằng id cá thể chưa ươn
            sc_q_ok = write_json(w.path("q_ok.json"), {
                "quan": {
                    "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 80}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}],
                }
            })
            load_scenario(sc_q_ok, "quan", self.tuning, contract_version="1.2")

            # Mâu thuẫn ở v1.2 -> BadInput
            bad_quan_cases = [
                # kho đếm ở v1.2
                {"stock": {"ca_loc": 1}},
                # reserved trỏ tới cá thể đã ươn (fresh < 30)
                {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 29.9}],
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]},
                # 2 đơn dùng chung 1 id cá thể
                {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 90}],
                 "customers": [
                     {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
                     {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
                 ]},
                # reserved thiếu cá thể so với công thức (gỏi bông súng cần 2 bong_sung)
                {"stock": [{"id": "I1", "kind": "bong_sung", "fresh": 90}],
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "reserved": ["I1"]}]},
                # bỏ trống reserved nhưng kho chỉ có cá thể đã ươn
                {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 10}],
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]},
            ]
            for i, qb in enumerate(bad_quan_cases):
                p = write_json(w.path(f"q_bad_{i}.json"), {"quan": qb})
                with self.assertRaises(BadInput, msg=str(qb)):
                    load_scenario(p, "quan", self.tuning, contract_version="1.2")


if __name__ == "__main__":
    unittest.main()
