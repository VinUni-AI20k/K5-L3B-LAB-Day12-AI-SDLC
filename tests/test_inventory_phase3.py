import json
import os
import sys
import unittest
from pathlib import Path

_tests_dir = str(Path(__file__).parent)
if _tests_dir not in sys.path:
    sys.path.insert(0, _tests_dir)

from chonoi.errors import BadInput
from chonoi.inventory import read_inventory, write_inventory, validate_items
from helpers import Workdir, run_headless, write_json


class InventoryPhase3Tests(unittest.TestCase):
    def test_v12_valid_inventory_roundtrip(self):
        items = [
            {"id": "I2", "kind": "ca_loc", "fresh": 97.5},
            {"id": "I1", "kind": "ca_linh", "fresh": 100.0},
        ]
        with Workdir() as w:
            path = w.path("inv.json")
            write_inventory(path, items)
            loaded = read_inventory(path, contract_version="1.2")
            # Kiểm tra xuất file sắp xếp theo id (I1 trước I2)
            self.assertEqual(loaded, [
                {"id": "I1", "kind": "ca_linh", "fresh": 100.0},
                {"id": "I2", "kind": "ca_loc", "fresh": 97.5},
            ])

    def test_v12_rejects_counting_inventory(self):
        with Workdir() as w:
            path = write_json(w.path("inv.json"), {"items": {"ca_loc": 1}})
            with self.assertRaises(BadInput):
                read_inventory(path, contract_version="1.2")

    def test_v12_rejects_duplicate_id(self):
        bad_items = [
            {"id": "I1", "kind": "ca_linh", "fresh": 100},
            {"id": "I1", "kind": "ca_loc", "fresh": 90},
        ]
        with self.assertRaises(BadInput):
            validate_items(bad_items)

    def test_v12_rejects_unknown_kind(self):
        bad_items = [{"id": "I1", "kind": "ca_voi", "fresh": 100}]
        with self.assertRaises(BadInput):
            validate_items(bad_items)

    def test_v12_rejects_fresh_out_of_bounds(self):
        for bad_fresh in (-0.1, 100.1, "100", float("inf"), float("nan")):
            with self.assertRaises(BadInput):
                validate_items([{"id": "I1", "kind": "ca_linh", "fresh": bad_fresh}])

    def test_v12_empty_inventory_is_valid(self):
        with Workdir() as w:
            path = w.path("inv_empty.json")
            write_inventory(path, [])
            loaded = read_inventory(path, contract_version="1.2")
            self.assertEqual(loaded, [])

    def test_headless_quan_rejects_counting_inventory_with_exit_code_2(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 1}})
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--inventory", inv, "--out", out)
            self.assertEqual(code, 2, "Contract v1.2 phải từ chối kho đếm theo loại với mã thoát 2")
            self.assertIn("Contract v1.2 không hỗ trợ kho đếm theo loại", err)

    def test_headless_quan_accepts_v12_inventory_with_exit_code_0(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {
                "items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]
            })
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--inventory", inv, "--out", out)
            self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
