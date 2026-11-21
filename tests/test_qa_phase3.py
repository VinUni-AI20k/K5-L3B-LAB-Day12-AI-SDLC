"""QA acceptance tests for Contract v1.2 freshness and handoff behavior."""

import unittest

from helpers import Workdir, close, events, frames, items, kinds_of, read_jsonl, run_headless, snapshots, write_json


class Phase3FreshnessQA(unittest.TestCase):
    def test_gather_threshold_spoils_once_at_tick_one(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "gather": {"hold": items("ca_linh", fresh=30), "random_fish": False, "monsters": []}
            })
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "2", "--snapshot-every", "1",
                "--scenario", scenario, "--out", w.path("gather.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("gather.jsonl"))
            spoiled = events(rows, "spoiled")
            self.assertEqual(
                [(row["tick"], row["data"]) for row in spoiled],
                [(1, {"item_id": "I1", "kind": "ca_linh", "location": "hold"})],
            )
            hold = next(row["hold"] for row in snapshots(rows) if row["tick"] == 1)
            self.assertTrue(close(hold[0]["fresh"], 30 - 1 / 120, 0.01))

    def test_spoiled_reserved_item_releases_and_reholds_order_once(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "quan": {
                    "stock": items("ca_loc", fresh=30) + items("ca_loc", fresh=100, start=2),
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "reserved": ["I1"],
                    }],
                    "random_customers": False,
                }
            })
            code, err = run_headless(
                "--mode", "quan", "--seed", "1", "--ticks", "2", "--scenario", scenario,
                "--out", w.path("quan.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("quan.jsonl"))
            self.assertEqual(
                [(row["tick"], row["data"]) for row in events(rows, "spoiled")],
                [(1, {"item_id": "I1", "kind": "ca_loc", "location": "stock"})],
            )
            snapshot = snapshots(rows)[-1]
            customer = next(c for c in snapshot["customers"] if c["id"] == "C1")
            self.assertEqual((customer["order_status"], customer["reserved"]), ("reserved", ["I2"]))
            self.assertEqual([item["id"] for item in snapshot["stock"]], ["I1", "I2"])

    def test_cook_price_floors_after_freshness_adjustment(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "quan": {
                    "player": {"pos": [2, 8], "vel": [0, 0]},
                    "stock": items("ca_loc", fresh=50),
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "reserved": ["I1"],
                    }],
                    "random_customers": False,
                }
            })
            inputs = write_json(w.path("inputs.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless(
                "--mode", "quan", "--seed", "1", "--ticks", "1", "--scenario", scenario,
                "--inputs", inputs, "--out", w.path("quan.jsonl"),
            )
            self.assertEqual(code, 0, err)
            started = events(read_jsonl(w.path("quan.jsonl")), "cook_started")
            self.assertEqual(len(started), 1)
            self.assertEqual(started[0]["data"]["base_price"], 29)
            used = started[0]["data"]["items"]
            self.assertEqual([(item["id"], item["kind"]) for item in used], [("I1", "ca_loc")])
            self.assertTrue(close(used[0]["fresh"], 50 - 1 / 240, 0.01))

    def test_day_handoff_preserves_gather_freshness_in_same_tick(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "gather": {"hold": items("ca_linh"), "random_fish": False}
            })
            inputs = write_json(w.path("inputs.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless(
                "--mode", "day", "--seed", "1", "--ticks", "1", "--snapshot-every", "1",
                "--scenario", scenario, "--inputs", inputs, "--out", w.path("day.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("day.jsonl"))
            self.assertEqual(events(rows, "gather_end")[0]["tick"], 1)
            self.assertEqual(events(rows, "phase_start")[-1]["phase"], "quan")
            quan = next(row for row in snapshots(rows) if row["tick"] == 1)
            self.assertEqual(quan["phase"], "quan")
            self.assertEqual([item["id"] for item in quan["stock"]], ["I1"])
            self.assertEqual(kinds_of(quan["stock"]), ["ca_linh"])
            self.assertTrue(close(quan["stock"][0]["fresh"], 100 - 1 / 120, 0.01))


if __name__ == "__main__":
    unittest.main()
