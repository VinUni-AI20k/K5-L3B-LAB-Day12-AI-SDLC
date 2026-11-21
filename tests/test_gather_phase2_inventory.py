import json
import tempfile
import unittest
from pathlib import Path

from chonoi.inventory import (
    validate_items, write_inventory, read_inventory,
    hold_to_items,
)
from chonoi.scenario import load_scenario


TUNING = json.loads(
    Path("game.contract.json").read_text(encoding="utf-8")
)["tuning"]


class GatherPhase2InventoryTests(unittest.TestCase):

    def test_new_ingredients_accepted(self):
        result = validate_items({
            "ca_keo": 2,
            "keo_neo": 1,
        })
        self.assertEqual(result, {
            "ca_keo": 2,
            "keo_neo": 1,
        })

    def test_inventory_roundtrip(self):
        items = hold_to_items([
            "keo_neo", "ca_keo", "ca_keo"
        ])
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "inventory.json")
            write_inventory(path, items)
            loaded = read_inventory(path)
        self.assertEqual(loaded, {
            "ca_keo": 2,
            "keo_neo": 1,
        })

    def test_new_node_scenario(self):
        scenario = {
            "gather": {
                "nodes": [{
                    "id": "N5",
                    "kind": "keo_neo",
                    "pos": [76, 0],
                }],
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.json"
            path.write_text(json.dumps(scenario), encoding="utf-8")
            result = load_scenario(
                str(path), "gather", TUNING
            )
        self.assertEqual(
            result["nodes"][0]["kind"], "keo_neo"
        )

    def test_new_fish_scenario(self):
        scenario = {
            "gather": {
                "fish": [{
                    "id": "F9",
                    "kind": "ca_keo",
                    "pos": [45, 24],
                    "heading_deg": 0,
                }],
                "hold": ["keo_neo", "ca_keo"],
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.json"
            path.write_text(json.dumps(scenario), encoding="utf-8")
            result = load_scenario(
                str(path), "gather", TUNING
            )
        self.assertEqual(
            result["fish"][0]["kind"], "ca_keo"
        )
        self.assertEqual(len(result["hold"]), 2)


if __name__ == "__main__":
    unittest.main()
