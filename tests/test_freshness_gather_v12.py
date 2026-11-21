"""Kiểm thử Gather v1.2 (Phase 3): kho cá thể, hao 240-đơn vị, ngưỡng ươn fresh=30, LIFO & mã 2 kho cũ."""

import json
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inventory import fresh_to_units, read_inventory, units_to_fresh, write_inventory
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class FreshnessGatherV12Tests(unittest.TestCase):
    def test_240_unit_roundtrip_and_threshold_safety(self):
        for u in range(24001):
            self.assertEqual(fresh_to_units(units_to_fresh(u)), u)
        self.assertLess(fresh_to_units(29.999), 7200)
        self.assertEqual(fresh_to_units(30), 7200)

    def test_spoiled_emitted_exactly_on_crossing_fresh_30_and_sorted_by_id(self):
        # Exact fixture from TICKET-03: hold starts at fresh=30 -> crosses below 30 at tick 1
        sc = {
            "gather": {
                "hold": [
                    {"id": "I10", "kind": "ca_linh", "fresh": 30},
                    {"id": "I2", "kind": "ca_loc", "fresh": 30},
                ],
                "random_fish": False,
                "monsters": [],
            }
        }
        with Workdir() as w:
            out = w.path("spoil.jsonl")
            inv = w.path("inv.json")
            inp = write_json(w.path("i.json"), frames({"tick": 1, "interact": True}))
            c, e = run_headless(
                "--mode", "gather", "--seed", "1",
                "--scenario", write_json(w.path("sc.json"), sc),
                "--inputs", inp,
                "--inventory-out", inv,
                "--ticks", "5", "--out", out,
            )
            self.assertEqual(c, 0, e)
            rows = read_jsonl(out)
            spoiled = [(r["tick"], r["data"]) for r in events(rows, "spoiled")]
            self.assertEqual(spoiled, [
                (1, {"item_id": "I2", "kind": "ca_loc", "location": "hold"}),
                (1, {"item_id": "I10", "kind": "ca_linh", "location": "hold"}),
            ])
            # Reloading written inventory preserves exact < 30 freshness without rounding back to 30
            loaded = read_inventory(inv)
            for it in loaded:
                self.assertLess(it["fresh"], 30)

    def test_newly_harvested_item_does_not_decay_on_acquisition_tick(self):
        sc = {
            "gather": {
                "player": {"pos": [12, 0]},
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
                "random_fish": False,
                "monsters": [],
            }
        }
        inp = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False})
        with Workdir() as w:
            out = w.path("new.jsonl")
            c, e = run_headless(
                "--mode", "gather", "--seed", "1",
                "--scenario", write_json(w.path("sc.json"), sc),
                "--inputs", write_json(w.path("in.json"), inp),
                "--ticks", "2", "--snapshot-every", "1", "--out", out,
            )
            self.assertEqual(c, 0, e)
            snaps = {s["tick"]: s for s in snapshots(read_jsonl(out))}
            self.assertEqual(snaps[1]["hold"], [{"id": "I1", "kind": "bong_dien_dien", "fresh": 100}])
            self.assertAlmostEqual(snaps[2]["hold"][0]["fresh"], 99.991667, places=6)

    def test_old_count_inventory_rejected_with_exit_2(self):
        with Workdir() as w:
            old_inv = write_json(w.path("old.json"), {"items": {"ca_loc": 2}})
            c, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", old_inv, "--out", w.path("q.jsonl"))
            self.assertEqual(c, 2)
            with self.assertRaises(BadInput):
                read_inventory(old_inv)

    def test_day2_reallocates_fresh_item_ids_sequentially(self):
        sc = {
            "gather": {
                "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                "time_left_ticks": 1,
                "random_fish": False,
                "monsters": [],
            },
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        inp = frames(
            {"tick": 0, "interact": True}, {"tick": 1, "interact": False},
            {"tick": 2, "shop_done": True}, {"tick": 3, "shop_done": False},
        )
        with Workdir() as w:
            out = w.path("d2.jsonl")
            c, e = run_headless(
                "--mode", "day", "--days", "2", "--seed", "1",
                "--scenario", write_json(w.path("sc.json"), sc),
                "--inputs", write_json(w.path("in.json"), inp),
                "--ticks", "10", "--snapshot-every", "1", "--out", out,
            )
            self.assertEqual(c, 0, e)
            snaps = snapshots(read_jsonl(out))
            d2_gather = next(s for s in snaps if s["day"] == 2 and s["phase"] == "gather")
            self.assertEqual(d2_gather["hold"], [{"id": "I2", "kind": "ca_loc", "fresh": 100}])

    def test_atomic_inventory_write_and_lifo_monster_drop_objects(self):
        with Workdir() as w:
            inv = w.path("a.json")
            write_inventory(inv, [
                {"id": "I10", "kind": "ca_linh", "fresh": 90},
                {"id": "I2", "kind": "ca_loc", "fresh": 29.995833},
            ])
            loaded = read_inventory(inv)
            self.assertEqual([x["id"] for x in loaded], ["I2", "I10"])


if __name__ == "__main__":
    unittest.main()
