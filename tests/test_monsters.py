import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import LiveInputs
from chonoi.runner import Session
from chonoi.scenario import load_scenario


class MonsterContractTests(unittest.TestCase):
    def test_contract_v11_has_core_phase2_values(self):
        contract = load_contract()
        self.assertEqual(contract["contract_version"], "1.1")
        tuning = contract["tuning"]
        self.assertEqual(len(tuning["quan"]["stoves"]), 2)
        self.assertEqual(len(tuning["quan"]["tables"]), 4)
        self.assertEqual(len(tuning["menu"]), 6)
        self.assertEqual(len(tuning["day_plan"]), 5)
        self.assertIn("shop", tuning)

    def test_inventory_accepts_new_v11_ingredients(self):
        from chonoi.inventory import read_inventory
        import json
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "inventory.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"items": {"ca_keo": 2, "keo_neo": 1}}, f)
            self.assertEqual(read_inventory(path), {"ca_keo": 2, "keo_neo": 1})

    def test_monster_scenario_must_be_underwater(self):
        tuning = load_contract()["tuning"]
        bad = {"monsters": [{"id": "M1", "kind": "ca_sau", "pos": [50, 9]}]}
        with self.assertRaises(BadInput):
            load_scenario = __import__("chonoi.scenario", fromlist=["load_scenario"]).load_scenario
            import tempfile
            import json
            import os
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "bad.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"gather": bad}, f)
                load_scenario(path, "gather", tuning)


class MonsterSimulationTests(unittest.TestCase):
    def test_m1_hit_removes_lifo_half_and_sets_invuln_recoil(self):
        tuning = load_contract()["tuning"]
        scenario = {
            "day": 1,
            "player": {"pos": [50, 14]},
            "hold": ["ca_loc", "ca_linh", "bong_sung", "bong_dien_dien"],
            "monsters": [{
                "id": "M1",
                "kind": "ca_sau",
                "day": 1,
                "pos": [50, 14],
                "heading_deg": 180,
            }],
        }
        session = Session("gather", tuning, scenario, 1)
        events = session.step(LiveInputs().advance())
        names = [row["name"] for row in events]
        self.assertIn("monster_hit", names)
        hit = next(row["data"] for row in events if row["name"] == "monster_hit")
        self.assertEqual(hit["damage"], 1)
        self.assertEqual(hit["removed_count"], 2)
        self.assertEqual(hit["removed"], ["bong_sung", "bong_dien_dien"])
        self.assertEqual(session.sim.hp, 2)
        self.assertEqual(session.sim.invuln_ticks, 90)
        self.assertEqual(session.sim.recoil_ticks, 60)

    def test_m1_faint_clears_hold_and_emits_gather_end(self):
        tuning = load_contract()["tuning"]
        scenario = {
            "day": 1,
            "player": {"pos": [50, 14], "hp": 1},
            "hold": ["ca_loc", "ca_linh"],
            "monsters": [{"id": "M1", "kind": "ca_sau", "day": 1, "pos": [50, 14]}],
        }
        session = Session("gather", tuning, scenario, 1)
        events = session.step(LiveInputs().advance())
        names = [row["name"] for row in events]
        self.assertIn("faint", names)
        self.assertIn("gather_end", names)
        self.assertEqual(session.sim.hold, [])
        self.assertTrue(session.done)
        self.assertEqual(session.sim.reason, "fainted")

    def test_m2_only_active_on_day3(self):
        tuning = load_contract()["tuning"]
        day2 = Session("gather", tuning, {"day": 2}, 1)
        day3 = Session("gather", tuning, {"day": 3}, 1)
        self.assertEqual([m["id"] for m in day2.sim.monsters], [])
        self.assertEqual([m["id"] for m in day3.sim.monsters], ["M2"])


if __name__ == "__main__":
    unittest.main()
