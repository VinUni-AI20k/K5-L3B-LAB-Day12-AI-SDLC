import json
import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json, frames


class FreshnessBoundaries(unittest.TestCase):
    def test_gather_item_at_threshold_spoils_once_on_first_tick(self):
        with Workdir() as work:
            item = {"id": "I1", "kind": "ca_linh", "fresh": 30}
            scenario = write_json(
                work.path("freshness.json"),
                {
                    "gather": {
                        "hold": [item],
                        "random_fish": False,
                        "monsters": [],
                    }
                },
            )
            output = work.path("gather.jsonl")
            code, stderr = run_headless(
                "--mode", "gather", "--seed", "42", "--ticks", "2",
                "--snapshot-every", "1", "--scenario", scenario, "--out", output,
            )
            self.assertEqual(code, 0, stderr)
            rows = read_jsonl(output)

            spoiled = events(rows, "spoiled")
            self.assertEqual([row["tick"] for row in spoiled], [1])
            self.assertEqual(
                spoiled[0]["data"],
                {"item_id": "I1", "kind": "ca_linh", "location": "hold"},
            )

            by_tick = {row["tick"]: row for row in snapshots(rows)}
            self.assertEqual(by_tick[0]["hold"], [item])
            for tick in (1, 2):
                with self.subTest(tick=tick):
                    hold = by_tick[tick]["hold"]
                    self.assertEqual(len(hold), 1)
                    self.assertEqual((hold[0]["id"], hold[0]["kind"]), ("I1", "ca_linh"))
                    self.assertAlmostEqual(
                        hold[0]["fresh"], 30 - tick * 0.5 / 60, delta=0.01,
                    )

class InventoryHandoff(unittest.TestCase):
    def test_quan_imports_gather_item_with_same_id_and_freshness(self):
        with Workdir() as work:
            scenario = write_json(
                work.path("gather.json"),
                {
                    "gather": {
                        "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}],
                        "random_fish": False,
                        "monsters": [],
                    }
                },
            )
            inputs = write_json(
                work.path("inputs.json"),
                frames({"tick": 0, "interact": True}),
            )
            inventory = work.path("inventory.json")
            gather_out = work.path("gather.jsonl")
            code, stderr = run_headless(
                "--mode", "gather", "--seed", "42", "--ticks", "1",
                "--scenario", scenario, "--inputs", inputs,
                "--inventory-out", inventory, "--out", gather_out,
            )
            self.assertEqual(code, 0, stderr)

            ending = events(read_jsonl(gather_out), "gather_end")
            self.assertEqual(len(ending), 1)
            self.assertEqual(ending[0]["tick"], 1)
            self.assertEqual(ending[0]["data"]["reason"], "docked")
            with open(inventory, encoding="utf-8") as exported:
                payload = json.load(exported)
            self.assertEqual(payload, ending[0]["data"]["inventory"])
            self.assertEqual(len(payload["items"]), 1)
            item = payload["items"][0]
            self.assertEqual((item["id"], item["kind"]), ("I1", "ca_linh"))
            self.assertAlmostEqual(item["fresh"], 100 - 0.5 / 60, delta=0.01)

            quan_out = work.path("quan.jsonl")
            code, stderr = run_headless(
                "--mode", "quan", "--seed", "42", "--ticks", "0",
                "--inventory", inventory, "--out", quan_out,
            )
            self.assertEqual(code, 0, stderr)
            initial = snapshots(read_jsonl(quan_out))[0]
            self.assertEqual((initial["tick"], initial["phase"]), (0, "quan"))
            self.assertEqual(len(initial["stock"]), 1)
            imported = initial["stock"][0]
            self.assertEqual((imported["id"], imported["kind"]), ("I1", "ca_linh"))
            self.assertAlmostEqual(imported["fresh"], item["fresh"], delta=0.01)

class InventorySchema(unittest.TestCase):
    def test_quan_rejects_count_inventory_without_writing_output(self):
        with Workdir() as work:
            inventory = write_json(
                work.path("count-inventory.json"),
                {"items": {"ca_loc": 1}},
            )
            output = work.path("quan.jsonl")
            code, stderr = run_headless(
                "--mode", "quan", "--seed", "42", "--ticks", "0",
                "--inventory", inventory, "--out", output,
            )

            self.assertEqual(code, 2, stderr or f"Unexpected exit code: {code}")
            with self.assertRaises(FileNotFoundError):
                with open(output, encoding="utf-8"):
                    pass


class QuanFreshness(unittest.TestCase):
    def test_spoiled_reservation_is_replaced_before_cooking_and_pricing(self):
        with Workdir() as work:
            scenario = write_json(
                work.path("quan.json"),
                {
                    "quan": {
                        "player": {"pos": [2, 8]},
                        "random_customers": False,
                        "stock": [
                            {"id": "I1", "kind": "ca_loc", "fresh": 30},
                            {"id": "I2", "kind": "ca_loc", "fresh": 80},
                            {"id": "I3", "kind": "ca_loc", "fresh": 90},
                        ],
                        "customers": [
                            {
                                "id": "C1",
                                "table_id": "T1",
                                "dish_id": "ca_loc_nuong_trui",
                                "state": "waiting",
                                "order_status": "reserved",
                                "patience_ticks_left": 3600,
                                "reserved": ["I1"],
                            }
                        ],
                    }
                },
            )
            inputs = write_json(
                work.path("inputs.json"),
                frames({"tick": 0, "interact": True}),
            )
            output = work.path("quan.jsonl")
            code, stderr = run_headless(
                "--mode", "quan", "--seed", "42", "--ticks", "1",
                "--scenario", scenario, "--inputs", inputs, "--out", output,
            )
            self.assertEqual(code, 0, stderr)
            rows = read_jsonl(output)
            relevant = [
                row for row in events(rows)
                if row["name"] in ("spoiled", "cook_started")
            ]
            self.assertEqual(
                [(row["tick"], row["name"]) for row in relevant],
                [(1, "spoiled"), (1, "cook_started")],
            )
            self.assertEqual(
                relevant[0]["data"],
                {"item_id": "I1", "kind": "ca_loc", "location": "stock"},
            )
            cooked = relevant[1]["data"]
            self.assertEqual(cooked["order_id"], "C1")
            self.assertEqual([item["id"] for item in cooked["items"]], ["I3"])
            self.assertEqual(cooked["base_price"], 53)
            self.assertEqual(
                {item["id"] for item in snapshots(rows)[-1]["stock"]},
                {"I1", "I2"},
            )


if __name__ == "__main__":
    unittest.main()
