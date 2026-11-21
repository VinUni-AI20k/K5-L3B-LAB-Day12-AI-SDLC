"""Phase 3 — file kho cá thể (TICKET-03 Test Contract v1.2 §1): đọc/ghi, mã 2, ghi nguyên tử đúng một lần."""

import json
import os
import unittest
from unittest import mock

from chonoi import inventory as inv
from chonoi.contract import load_contract
from chonoi.errors import BadInput
from helpers import Workdir, events, frames, read_jsonl, run_headless, write_json


class FileKhoP3(unittest.TestCase):
    def test_ac_p3_20_contract_v12_freshness(self):
        c = load_contract()
        self.assertIn(c["contract_version"], ("1.2", "1.3"))
        self.assertEqual(c["tuning"]["freshness"],
                         {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30})
        t = c["tuning"]
        self.assertEqual(inv.decay_units_per_tick(t, "gather"), 2)
        self.assertEqual(inv.decay_units_per_tick(t, "quan"), 1)
        self.assertEqual(inv.spoil_threshold_units(t), 7200)

    def test_ac_p3_21_v12_rejects_count_schema_and_bad_schema_code_2(self):
        bad = [
            {"items": {"ca_loc": 1}},                                     # kho đếm
            {"items": {}},                                                # kho đếm rỗng
            {"items": [], "x": 1},
            {"items": [{"id": "I1", "kind": "ca_ho", "fresh": 50}]},      # kind lạ
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 50}, {"id": "I1", "kind": "ca_loc", "fresh": 40}]},
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100.5}]},
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": -0.1}]},
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": "50"}]},
            {"items": [{"id": "I1", "kind": "ca_loc"}]},
            {"items": [{"id": 1, "kind": "ca_loc", "fresh": 50}]},
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 50, "x": 1}]},
        ]
        with Workdir() as w:
            for b in bad:
                p = write_json(w.path("inv.json"), b)
                with self.assertRaises(BadInput, msg=b):
                    inv.read_inventory(p, "1.2")
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", p,
                                       "--out", w.path("q.jsonl"))
                self.assertEqual(code, 2, b)
            for raw in ('{"items":[{"id":"I1","kind":"ca_loc","fresh":NaN}]}',
                        '{"items":[{"id":"I1","kind":"ca_loc","fresh":Infinity}]}'):
                p = w.path("nf.json")
                with open(p, "w") as f:
                    f.write(raw)
                with self.assertRaises(BadInput):
                    inv.read_inventory(p, "1.2")

    def test_ac_p3_22_roundtrip_sorted_by_id_and_exact_at_threshold(self):
        items = [inv.make_item("I10", "ca_loc", 7200), inv.make_item("I2", "ca_linh", 7199),
                 inv.make_item("I1", "keo_neo", 23998)]
        with Workdir() as w:
            p = w.path("k.json")
            inv.write_inventory_atomic(p, items)
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual([i["id"] for i in data["items"]], ["I1", "I2", "I10"])
            back = inv.read_inventory(p, "1.2")
            self.assertEqual({i["id"]: i["units"] for i in back}, {"I1": 23998, "I2": 7199, "I10": 7200})
            thr = 7200
            self.assertEqual([inv.is_spoiled(i, thr) for i in back], [False, True, False])

    def test_ac_p3_23_decay_helper_reports_crossing_once_in_id_order(self):
        items = [inv.make_item("I3", "ca_loc", 7201), inv.make_item("I1", "ca_loc", 7200),
                 inv.make_item("I2", "ca_loc", 100)]
        self.assertEqual([i["id"] for i in inv.decay(items, 2, 7200)], ["I1", "I3"])
        self.assertEqual(inv.decay(items, 2, 7200), [])
        self.assertEqual([i["units"] for i in items], [7197, 7196, 96])

    def test_ac_p3_24_atomic_write_exactly_once_on_gather_end(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                                                           "random_fish": False, "monsters": [], "time_left_ticks": 3}})
            calls = []
            real_replace = os.replace

            def spy(src, dst):
                calls.append((os.path.dirname(os.path.abspath(src)), dst))
                return real_replace(src, dst)

            from chonoi.runner import run as run_sim
            from chonoi.scenario import load_scenario
            tuning = load_contract()["tuning"]
            scenario = load_scenario(sc, "gather", tuning, 1)
            out = w.path("kho.json")
            with mock.patch("chonoi.inventory.os.replace", side_effect=spy):
                run_sim("gather", tuning, scenario, 1, [], 50, w.path("g.jsonl"), 1, inventory_out=out)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0], (os.path.dirname(os.path.abspath(out)), out))  # file tạm cùng thư mục
            self.assertEqual([f for f in os.listdir(os.path.dirname(out)) if f.startswith(".inv-")], [])

    def test_ac_p3_25_tick_limit_before_gather_end_keeps_target(self):
        with Workdir() as w:
            out = w.path("kho.json")
            with open(out, "w") as f:
                f.write("GIU NGUYEN")
            sc = write_json(w.path("sc.json"), {"gather": {"random_fish": False, "monsters": []}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--scenario", sc,
                                     "--inventory-out", out, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(out) as f:
                self.assertEqual(f.read(), "GIU NGUYEN")
            self.assertEqual(events(read_jsonl(w.path("g.jsonl")), "gather_end"), [])

    def test_ac_p3_26_older_version_still_reads_count_schema(self):
        with Workdir() as w:
            p = write_json(w.path("k.json"), {"items": {"ca_loc": 2}})
            self.assertEqual(inv.read_inventory(p, "1.1"), {"ca_loc": 2})


if __name__ == "__main__":
    unittest.main()
