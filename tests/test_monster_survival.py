"""P2-02: Cá Sấu Năm Chèo, va chạm, ngất và nâng cấp Gather."""

import copy
import json
import os
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from chonoi.sim.monsters import init_monsters, step_monsters

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


def fixture(ident="M1", pos=None, state="patrol", **extra):
    pos = pos or [60, 24]
    return {"id": ident, "kind": "ca_sau", "pos": pos,
            "waypoints": [list(pos), [min(pos[0] + 4, 100), pos[1]]],
            "state": state, **extra}


class MonsterSurvival(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.g = self.tuning["gather"]

    def sim(self, block=None, day=1, upgrades=None):
        return GatherSim(self.tuning, block or {}, Streams(1), IdAllocator(),
                         day=day, active_upgrades=upgrades)

    def monster_step(self, monsters, player, hp=3, invuln=0, hold=None):
        hold = [] if hold is None else hold
        return step_monsters(monsters, self.g, player, hp, invuln, hold)

    def test_spawn_days_override_and_snapshot_order(self):
        self.assertEqual([m["id"] for m in init_monsters(self.g, {}, day=1)], ["M1"])
        self.assertEqual([m["id"] for m in init_monsters(self.g, {}, day=3)], ["M1", "M2"])
        self.assertEqual(init_monsters(self.g, {"monsters": []}, day=3), [])
        s = self.sim({"monsters": [fixture("M10"), fixture("M2")]})
        self.assertEqual([m["id"] for m in s.snapshot()["monsters"]], ["M2", "M10"])
        self.assertEqual(s.snapshot()["monsters"][0]["target_idx"], 1)
        self.assertIn("invuln_ticks", s.snapshot()["player"])

    def test_patrol_reaches_waypoint_then_targets_other_on_next_step(self):
        monsters = init_monsters(self.g, {"monsters": [fixture()]})
        for _ in range(240):
            self.monster_step(monsters, [0, 0], invuln=1)
        self.assertAlmostEqual(monsters[0]["pos"][0], 64)
        self.assertEqual(monsters[0]["target_idx"], 0)
        self.monster_step(monsters, [0, 0], invuln=1)
        self.assertLess(monsters[0]["pos"][0], 64)

    def test_chase_detection_and_exit_thresholds(self):
        monsters = init_monsters(self.g, {"monsters": [fixture()]})
        self.monster_step(monsters, [70, 24], invuln=1)
        self.assertEqual(monsters[0]["state"], "chase")
        self.assertAlmostEqual(monsters[0]["pos"][0], 60 + 3 / 60)
        self.monster_step(monsters, [100, 24], invuln=1)
        self.assertEqual(monsters[0]["state"], "patrol")
        monsters[0]["state"] = "chase"
        self.monster_step(monsters, [60, 9], invuln=1)
        self.assertEqual(monsters[0]["state"], "patrol")
        monsters[0]["pos"] = [60, 24]
        self.monster_step(monsters, [70.001, 24], invuln=1)
        self.assertEqual(monsters[0]["state"], "patrol")

    def test_hit_nearest_numeric_id_lifo_and_one_per_tick(self):
        monsters = init_monsters(self.g, {"monsters": [
            fixture("M10", [60, 24]), fixture("M2", [60, 24])]})
        hold = ["ca_loc", "ca_linh", "bong_sung", "bong_dien_dien", "ca_loc"]
        hp, invuln, rows, fainted = self.monster_step(monsters, [60, 24], hold=hold)
        self.assertFalse(fainted)
        self.assertEqual(hp, 2)
        self.assertEqual(invuln, 90)
        self.assertEqual(rows, [("monster_hit", {"monster_id": "M2", "hp": 2,
                                                  "lost": ["ca_loc", "bong_dien_dien"],
                                                  "pos": [60, 24]})])
        self.assertEqual(hold, ["ca_loc", "ca_linh", "bong_sung"])
        self.assertEqual(next(m for m in monsters if m["id"] == "M2")["state"], "recoil")
        self.assertEqual(next(m for m in monsters if m["id"] == "M10")["state"], "chase")
        monsters = init_monsters(self.g, {"monsters": [
            fixture("M1", [61.4, 24]), fixture("M2", [60.6, 24])]})
        _, _, rows, _ = self.monster_step(monsters, [60, 24])
        self.assertEqual(rows[0][1]["monster_id"], "M2", "khoảng cách ưu tiên trước id")

    def test_monster_hit_reports_player_position_after_movement(self):
        s = self.sim({"player": {"pos": [60, 24]},
                      "monsters": [fixture(pos=[60, 24])]})
        rows = s.step(InputPlayer([{"tick": 0, "move": [1, 0]}]).advance(0))
        self.assertGreater(s.pos[0], 60)
        self.assertEqual(rows[0][0], "monster_hit")
        self.assertEqual(rows[0][1]["pos"], [round(s.pos[0], 3), round(s.pos[1], 3)])

    def test_hit_at_post_move_radius_edge_and_depth_gate(self):
        monsters = init_monsters(self.g, {"monsters": [fixture(pos=[61.55, 10], state="chase")]})
        hp, _, rows, _ = self.monster_step(monsters, [60, 10])
        self.assertEqual(hp, 2)
        self.assertEqual(rows[0][0], "monster_hit")
        monsters = init_monsters(self.g, {"monsters": [fixture(pos=[60, 10])]})
        hp, _, rows, _ = self.monster_step(monsters, [60, 9.99])
        self.assertEqual((hp, rows), (3, []))

    def test_invulnerability_ends_at_t_plus_90(self):
        monsters = init_monsters(self.g, {"monsters": [fixture(pos=[60, 24])]})
        hp, invuln, rows, _ = self.monster_step(monsters, [60, 24])
        self.assertEqual(rows[0][0], "monster_hit")
        for tick in range(1, 90):
            invuln -= 1
            hp, invuln, rows, _ = self.monster_step(monsters, [60, 24], hp, invuln)
            self.assertFalse(rows, tick)
        invuln -= 1
        hp, invuln, rows, _ = self.monster_step(monsters, [60, 24], hp, invuln)
        self.assertEqual(rows[0][0], "monster_hit")
        self.assertEqual(hp, 1)

    def test_recoil_60_steps_coincident_direction_and_boundary(self):
        monsters = init_monsters(self.g, {"monsters": [fixture(pos=[60, 24])]})
        _, invuln, rows, _ = self.monster_step(monsters, [60, 24])
        self.assertEqual(rows[0][0], "monster_hit")
        self.assertEqual(monsters[0]["pos"], [60, 24], "hit tick chưa lùi")
        self.assertEqual(monsters[0]["recoil_dir"], [1.0, 0.0])
        for tick in range(60):
            _, _, rows, _ = self.monster_step(monsters, [60, 24], invuln=invuln)
            self.assertEqual(rows, [])
            if tick < 59:
                self.assertEqual(monsters[0]["state"], "recoil")
        self.assertAlmostEqual(monsters[0]["pos"][0], 62)
        self.assertEqual(monsters[0]["state"], "patrol")
        self.assertIsNone(monsters[0]["recoil_dir"])
        edge = init_monsters(self.g, {"monsters": [fixture(pos=[100, 30], state="recoil",
            state_ticks_left=1, recoil_dir=[1.0, 0.0])]})
        self.monster_step(edge, [100, 30])
        self.assertEqual(edge[0]["pos"], [100, 30])

    def test_recoil_finishing_tick_cannot_hit(self):
        monsters = init_monsters(self.g, {"monsters": [fixture(pos=[60, 24], state="recoil",
            state_ticks_left=1, recoil_dir=[1.0, 0.0])]})
        hp, _, rows, _ = self.monster_step(monsters, [60, 24])
        self.assertEqual((hp, rows, monsters[0]["state"]), (3, [], "patrol"))
        hp, _, rows, _ = self.monster_step(monsters, [60, 24])
        self.assertEqual((hp, rows[0][0]), (2, "monster_hit"))

    def test_monster_faint_loses_remaining_hold_and_inventory_empty(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {"gather": {
                "player": {"pos": [60, 24], "hp": 1},
                "hold": ["ca_loc", "ca_linh", "bong_sung", "bong_dien_dien", "ca_loc"]}})
            inventory = w.path("inventory.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", scenario, "--inventory-out", inventory,
                                     "--out", w.path("out.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("out.jsonl"))
            self.assertEqual([e["name"] for e in events(rows)], ["monster_hit", "faint", "gather_end"])
            self.assertEqual(events(rows, "monster_hit")[0]["data"]["lost"],
                             ["ca_loc", "bong_dien_dien"])
            self.assertEqual(events(rows, "faint")[0]["data"],
                             {"cause": "monster", "lost": ["bong_sung", "ca_linh", "ca_loc"], "hp": 0})
            self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": []})
            with open(inventory, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

    def test_choke_before_monster_hit_and_choke_ignores_invuln(self):
        s = self.sim({"player": {"pos": [60, 24], "oxygen_ticks": 0,
                                 "zero_oxy_ticks": 59, "hp": 2},
                      "hold": ["ca_loc", "ca_linh", "bong_sung", "bong_dien_dien"]})
        rows = s.step(InputPlayer([]).advance(0))
        self.assertEqual([name for name, _ in rows],
                         ["choke", "monster_hit", "faint", "gather_end"])
        self.assertEqual(rows[1][1]["lost"], ["bong_dien_dien", "bong_sung"])
        self.assertEqual(rows[2][1]["lost"], ["ca_linh", "ca_loc"])
        s = self.sim({"player": {"pos": [20, 24], "oxygen_ticks": 0,
                                 "zero_oxy_ticks": 59, "invuln_ticks": 10, "hp": 2},
                      "monsters": []})
        rows = s.step(InputPlayer([]).advance(0))
        self.assertEqual(rows[0][0], "choke")
        self.assertEqual(s.hp, 1)
        s = self.sim({"player": {"pos": [60, 24], "oxygen_ticks": 0,
                                 "zero_oxy_ticks": 59, "hp": 1},
                      "hold": ["ca_loc"]})
        rows = s.step(InputPlayer([]).advance(0))
        self.assertEqual([name for name, _ in rows], ["choke", "faint", "gather_end"])
        self.assertEqual(rows[-1][1]["inventory"], {"items": []})

    def test_active_upgrade_limits_and_day_spawn(self):
        s = self.sim(day=3, upgrades={"oxygen": 1, "hp": 2})
        self.assertEqual((s.oxygen_max, s.oxygen_ticks, s.hp_max, s.hp), (2700, 2700, 5, 5))
        self.assertEqual([m["id"] for m in s.snapshot()["monsters"]], ["M1", "M2"])
        s = self.sim(upgrades={"oxygen": 2, "hp": 1})
        self.assertEqual((s.oxygen_max, s.hp_max), (3600, 4))
        tuning = copy.deepcopy(self.tuning)
        tuning["shop"] = {"upgrades": {"oxygen": [{"level": 1, "oxygen_max_s": 50}],
                                          "hp": [{"level": 1, "hp_max": 6}]}}
        s = GatherSim(tuning, {}, Streams(1), IdAllocator(), active_upgrades={"oxygen": 1, "hp": 1})
        self.assertEqual((s.oxygen_max, s.hp_max), (3000, 6))

    def test_scenario_validation_bad_monsters_exit_2_before_output(self):
        bad = [
            [fixture("M1"), fixture("M1")],
            [fixture(kind="unknown")],
            [fixture(pos=[60, 9])],
            [{**fixture(), "waypoints": [[60, 24]]}],
            [{**fixture(), "waypoints": [[60, 24], [60, 31]]}],
            [{**fixture(), "target_idx": 2}],
            [{**fixture(), "target_idx": 1.0}],
            [{**fixture(), "state": "unknown"}],
            [{**fixture(), "state": "recoil", "state_ticks_left": 0, "recoil_dir": [1, 0]}],
            [{**fixture(), "state": "recoil", "state_ticks_left": 10, "recoil_dir": [2, 0]}],
            [{**fixture(), "state": "patrol", "recoil_dir": [1, 0]}],
        ]
        for monsters in bad:
            with self.subTest(monsters=monsters), Workdir() as w:
                scenario = write_json(w.path("scenario.json"), {"gather": {"monsters": monsters}})
                out = w.path("out.jsonl")
                code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0",
                                       "--scenario", scenario, "--out", out)
                self.assertEqual(code, 2)
                self.assertFalse(os.path.exists(out))

    def test_headless_fixture_and_deterministic_bytes(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {"gather": {"monsters": [fixture()]}})
            for i in (1, 2):
                code, err = run_headless("--mode", "gather", "--seed", "7", "--ticks", "80",
                                         "--scenario", scenario, "--out", w.path(f"out{i}.jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("out1.jsonl"), "rb") as a, open(w.path("out2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())
            self.assertEqual(snapshots(read_jsonl(w.path("out1.jsonl")))[0]["monsters"][0]["id"], "M1")


if __name__ == "__main__":
    unittest.main()
