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