import json
import unittest
from pathlib import Path
from helpers import Workdir, read_jsonl, run_headless, write_json


class GatherBoundaries(unittest.TestCase):
    def test_faint_at_choke_boundary_drops_hold_and_writes_empty_inventory(self):
        with Workdir() as work:
            scenario = write_json(
                work.path("scenario.json"),
                {
                    "gather": {
                        "player": {
                            "pos": [10, 5],
                            "hp": 1,
                            "oxygen_ticks": 0,
                            "zero_oxy_ticks": 59,
                        },
                        "random_fish": False,
                        "hold": ["ca_loc", "bong_sung"],
                    }
                },
            )
            output = work.path("gather.jsonl")
            inventory = work.path("inventory.json")
            code, stderr = run_headless(
                "--mode", "gather", "--seed", "42", "--ticks", "1",
                "--scenario", scenario, "--out", output,
                "--inventory-out", inventory,
            )
            self.assertEqual(code, 0, stderr)

            rows = read_jsonl(output)
            self.assertEqual((rows[0]["type"], rows[0]["tick"]), ("snapshot", 0))
            tick_one = [row for row in rows if row.get("tick") == 1]
            self.assertEqual(
                [row.get("name", row["type"]) for row in tick_one],
                ["choke", "faint", "gather_end", "snapshot"],
            )
            self.assertEqual(tick_one[1]["data"]["lost"], ["bong_sung", "ca_loc"])
            self.assertEqual(tick_one[3]["hold"], [])
            self.assertEqual(rows[-1]["type"], "end")
            self.assertEqual(rows[-1]["reason"], "fainted")

            with open(inventory, encoding="utf-8") as file:
                exported_inventory = json.load(file)
            self.assertEqual(exported_inventory, {"items": {}})
            self.assertEqual(tick_one[2]["data"]["inventory"], exported_inventory)

class HeadlessValidation(unittest.TestCase):
    def test_invalid_gather_fixture_preserves_existing_outputs(self):
        with Workdir() as work:
            scenario = write_json(
                work.path("invalid.json"),
                {"gather": {"player": {"hp": 0}}},
            )
            output = Path(work.path("gather.jsonl"))
            inventory = Path(work.path("inventory.json"))
            original_output = b'{"type":"previous_run"}\n'
            original_inventory = b'{"items":{"ca_loc":1}}\n'
            output.write_bytes(original_output)
            inventory.write_bytes(original_inventory)

            code, stderr = run_headless(
                "--mode", "gather", "--seed", "42", "--ticks", "1",
                "--scenario", scenario, "--out", str(output),
                "--inventory-out", str(inventory),
            )

            self.assertEqual(code, 2, stderr)
            self.assertEqual(output.read_bytes(), original_output)
            self.assertEqual(inventory.read_bytes(), original_inventory)