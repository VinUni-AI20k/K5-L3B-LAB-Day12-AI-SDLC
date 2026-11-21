"""Test hộp đen cho contract v1.1 (ticket 01 Phase 2): manifest, `day`, schema scenario mới."""

import json
import unittest

from helpers import Workdir, read_jsonl, run_headless, snapshots, write_json


class Manifest(unittest.TestCase):
    def test_contract_v11_shape(self):
        with open("game.contract.json", encoding="utf-8") as f:
            c = json.load(f)
        self.assertEqual(c["contract_version"], "1.1")
        g = c["tuning"]["gather"]
        self.assertEqual(len(g["fish_initial"]), 8)
        self.assertEqual(len(c["tuning"]["menu"]), 6)
        self.assertEqual(set(g["fish_yield"]), {"ca_linh", "ca_loc", "ca_keo"})
        self.assertEqual({n["kind"] for n in g["nodes"]}, {"bong_dien_dien", "bong_sung", "keo_neo"})
        self.assertEqual(len(g["monsters"]["spawns"]), 2)
        self.assertEqual(len(c["tuning"]["day_plan"]), 5)
        self.assertIn("net", c["extensions"])


class DayMode(unittest.TestCase):
    def test_day_ticks_zero_has_day_fields(self):
        with Workdir() as w:
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--out", w.path("d.jsonl"))
            self.assertEqual(code, 0, err)
            snap = snapshots(read_jsonl(w.path("d.jsonl")))[0]
            self.assertEqual(snap["mode"], "day")
            self.assertEqual(snap["phase"], "gather")
            for key in ("day", "day_plan", "upgrades", "active_upgrades"):
                self.assertIn(key, snap)
            self.assertEqual(snap["day"], 1)
            self.assertEqual(snap["day_plan"]["ingredients"], {"ca_loc": 3, "bong_sung": 6})

    def test_days_bounds_and_mode(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            for bad in ("0", "6", "-1"):
                code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--days", bad, "--out", out)
                self.assertEqual(code, 2, bad)
            # --days chỉ dùng với day
            code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--days", "2", "--out", out)
            self.assertEqual(code, 2)
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--days", "3", "--out", out)
            self.assertEqual(code, 0, err)

    def test_day_scenario_rejects_stock_and_reputation(self):
        with Workdir() as w:
            for block in ({"quan": {"stock": {"ca_loc": 1}}}, {"quan": {"reputation": 4.0}}):
                sc = write_json(w.path("sc.json"), {"day": {}, **block})
                code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "0",
                                         "--scenario", sc, "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, (block, err))

    def test_day_scenario_unknown_field(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"day": {"khong_co": 1}})
            code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "0",
                                   "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 2)

    def test_day_scenario_accepts_gather_and_quan_templates(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"day": {"money": 200, "earned": 200},
                                                "gather": {"hold": [], "random_fish": False},
                                                "quan": {"player": {"pos": [8, 5]}}})
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)


class ScenarioV11(unittest.TestCase):
    def test_fish_age_ticks(self):
        with Workdir() as w:
            ok = write_json(w.path("ok.json"), {"gather": {
                "random_fish": False,
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5], "age_ticks": 5}]}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0",
                                     "--scenario", ok, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            bad = write_json(w.path("bad.json"), {"gather": {
                "random_fish": False,
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5], "age_ticks": -1}]}})
            self.assertEqual(run_headless("--mode", "gather", "--seed", "1", "--ticks", "0",
                                          "--scenario", bad, "--out", w.path("o.jsonl"))[0], 2)

    def test_monsters_fixture(self):
        with Workdir() as w:
            ok = write_json(w.path("ok.json"), {"gather": {"random_fish": False, "monsters": [
                {"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}]}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0",
                                     "--scenario", ok, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            bad = write_json(w.path("bad.json"), {"gather": {"monsters": [
                {"id": "M1", "kind": "ca_ho", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}]}})
            self.assertEqual(run_headless("--mode", "gather", "--seed", "1", "--ticks", "0",
                                          "--scenario", bad, "--out", w.path("o.jsonl"))[0], 2)

    def test_player_invuln_and_attack_cooldown_accepted(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"invuln_ticks": 10, "attack_cd_ticks": 5}}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
