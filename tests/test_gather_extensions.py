"""Black-box component probes: net, độ tươi và current qua API manifest công khai.

Không sửa contract gốc và không thay validator/kho bằng mock. P3 schema migration
và nối shop/day thuộc ticket của Integrator, được theo dõi riêng trong proof.
"""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from helpers import ROOT, events, snapshots


class GatherComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))

    def manifest(self, *, fresh=False, net=False, current=False, current_tuning=None):
        c = copy.deepcopy(self.base)
        c["extensions"] = []
        if fresh:
            c["contract_version"] = "1.2"
            c["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5,
                              "quan_decay_per_s": 0.25, "spoiled_below": 30}
        if net:
            c["extensions"].append("net")
            c["tuning"].setdefault("shop", {}).setdefault("upgrades", {})["net"] = [
                {"level": 1, "price": 250, "radius": 4.0, "max_schools": 2},
                {"level": 2, "price": 500, "radius": 6.0, "max_schools": 3}]
        if current:
            c["extensions"].append("current")
            c["tuning"]["gather"]["current"] = current_tuning or {
                "interval_ticks": 1800, "duration_ticks": 480, "warning_ticks": 120,
                "min_depth": 10, "speed": 1.5}
        return c

    def probe(self, contract=None, scenario=None, steps=None, upgrades=None, phases=None, seed=1):
        request = {"contract": contract or self.manifest(),
                   "scenario": {"player": {"pos": [50, 10]}, "nodes": [], "fish": [],
                                "random_fish": False, "monsters": [], **(scenario or {})},
                   "steps": steps if steps is not None else [{}], "upgrades": upgrades or {}, "seed": seed}
        if phases is not None:
            request = {"phases": phases}
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(('tests', '.')), PYTHONIOENCODING='utf-8')
        result = subprocess.run([sys.executable, "-m", "gather_component_probe"], input=json.dumps(request),
                                cwd=ROOT, env=env, capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines()], result.stdout

    @staticmethod
    def fish(ident, x, kind="ca_loc"):
        return {"id": ident, "kind": kind, "pos": [x, 10], "heading_deg": 0}

    @staticmethod
    def item(ident="I1", fresh=100, kind="ca_loc"):
        return {"id": ident, "kind": kind, "fresh": fresh}

    def test_net_level_zero_matches_core_bytes(self):
        scenario = {"fish": [self.fish("F2", 51), self.fish("F10", 50.5)]}
        args = {"scenario": scenario, "steps": [{"catch": True}]}
        _, base = self.probe(**args)
        _, net = self.probe(self.manifest(net=True), upgrades={"net": 0}, **args)
        self.assertEqual(base, net)

    def test_net_disabled_ignores_bought_level(self):
        scenario = {"fish": [self.fish("F2", 51), self.fish("F10", 53)]}
        _, base = self.probe(scenario=scenario, steps=[{"catch": True}])
        c = self.manifest(net=True)
        c["extensions"] = []
        _, disabled = self.probe(c, scenario, [{"catch": True}], {"net": 2})
        self.assertEqual(base, disabled)

    def test_net_levels_radius_limits_and_numeric_id_order(self):
        fish = [self.fish("F10", 51), self.fish("F2", 54), self.fish("F3", 56), self.fish("F20", 56.001)]
        for level, expected in ((1, ["F2", "F10"]), (2, ["F2", "F3", "F10"])):
            with self.subTest(level=level):
                rows, _ = self.probe(self.manifest(net=True), {"fish": fish}, [{"catch": True}], {"net": level})
                self.assertEqual([e["data"]["fish_id"] for e in events(rows, "fish_caught")], expected)

    def test_net_full_school_is_kept_and_later_school_is_tried(self):
        c = self.manifest(net=True)
        capacity = c["tuning"]["gather"]["hold_capacity"]
        scenario = {"hold": ["bong_sung"] * (capacity - 1),
                    "fish": [self.fish("F2", 51, "ca_linh"), self.fish("F10", 52)]}
        rows, _ = self.probe(c, scenario, [{"catch": True}], {"net": 1})
        self.assertEqual([e["name"] for e in events(rows)], ["hold_full", "fish_caught"])
        self.assertEqual(events(rows, "hold_full")[0]["data"],
                         {"action": "catch", "fish_id": "F2", "required": 3, "free": 1})
        self.assertEqual([f["id"] for f in snapshots(rows)[-1]["fish"]], ["F2"])
        self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"], 30)

    def test_net_all_full_and_no_targets_do_not_start_cooldown(self):
        c = self.manifest(net=True)
        for scenario in ({"fish": []}, {"fish": [self.fish("F1", 60)]},
                         {"hold": ["ca_loc"] * c["tuning"]["gather"]["hold_capacity"],
                          "fish": [self.fish("F1", 51)]}):
            with self.subTest(scenario=scenario):
                rows, _ = self.probe(c, scenario, [{"catch": True}], {"net": 2})
                self.assertEqual(events(rows, "fish_caught"), [])
                self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"], 0)

    def test_net_counts_successes_and_respects_cooldown(self):
        scenario = {"fish": [self.fish(f"F{i}", 51) for i in range(1, 5)]}
        steps = [{"catch": True}, {"catch": False}, {"catch": True}]
        rows, _ = self.probe(self.manifest(net=True), scenario, steps, {"net": 1})
        self.assertEqual([e["data"]["fish_id"] for e in events(rows, "fish_caught")], ["F1", "F2"])

    def test_fresh_catch_allocates_one_id_per_item_and_starts_at_100(self):
        rows, _ = self.probe(self.manifest(fresh=True), {"fish": [self.fish("F1", 50, "ca_linh")]},
                             [{"catch": True}, {}])
        received = events(rows, "fish_caught")[0]["data"]["item_ids"]
        self.assertEqual(received, ["I1", "I2", "I3"])
        first, second = snapshots(rows)[1:]
        self.assertEqual([i["fresh"] for i in first["hold"]], [100, 100, 100])
        self.assertTrue(all(abs(i["fresh"] - (100 - 2 / 240)) < 0.001 for i in second["hold"]))

    def test_fresh_gather_preserves_existing_age_and_reserves_fixture_id(self):
        rows, _ = self.probe(self.manifest(fresh=True),
                             {"player": {"pos": [50, 0]}, "hold": [self.item("I99", 80)],
                              "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [50, 0]}]},
                             [{"interact": True}])
        self.assertEqual(events(rows, "gather")[0]["data"]["item_ids"], ["I100"])
        hold = snapshots(rows)[-1]["hold"]
        self.assertEqual(hold[-1], self.item("I100", 100, "bong_sung"))
        self.assertAlmostEqual(hold[0]["fresh"], 80 - 2 / 240, delta=0.001)

    def test_spoiled_at_30_fires_once_in_numeric_id_order(self):
        scenario = {"hold": [self.item("I10", 30), self.item("I2", 30), self.item("I1", 29)]}
        rows, _ = self.probe(self.manifest(fresh=True), scenario, [{}] * 3)
        spoiled = events(rows, "spoiled")
        self.assertEqual([(e["tick"], e["data"]) for e in spoiled],
                         [(1, {"item_id": "I2", "kind": "ca_loc", "location": "hold"}),
                          (1, {"item_id": "I10", "kind": "ca_loc", "location": "hold"})])
        self.assertEqual(snapshots(rows)[-1]["hold_count"], 3)

    def test_spoiled_threshold_uses_unrounded_integer_units(self):
        # 7202 units -> 7200 at tick 1 (still fresh), 7198 at tick 2 (spoiled).
        rows, _ = self.probe(self.manifest(fresh=True), {"hold": [self.item(fresh=7202 / 240)]}, [{}] * 2)
        self.assertEqual([e["tick"] for e in events(rows, "spoiled")], [2])
        self.assertEqual(snapshots(rows)[1]["hold"][0]["fresh"], 30)

    def test_freshness_clamps_at_zero(self):
        rows, _ = self.probe(self.manifest(fresh=True), {"hold": [self.item(fresh=0.004)]}, [{}] * 3)
        self.assertEqual(snapshots(rows)[-1]["hold"][0]["fresh"], 0)
        self.assertEqual(events(rows, "spoiled"), [])

    def test_fractional_decay_from_data_keeps_exact_integer_units(self):
        c = self.manifest(fresh=True)
        c["freshness"]["gather_decay_per_s"] = 0.1
        rows, _ = self.probe(c, {"hold": [self.item(fresh=30)]}, [{}] * 5)
        self.assertEqual([e["tick"] for e in events(rows, "spoiled")], [3])
        self.assertAlmostEqual(snapshots(rows)[-1]["hold"][0]["fresh"], 30 - 2 / 240, delta=0.001)

    def test_spoiled_items_still_fill_hold(self):
        c = self.manifest(fresh=True)
        hold = [self.item(f"I{i + 1}", 0) for i in range(c["tuning"]["gather"]["hold_capacity"])]
        rows, _ = self.probe(c, {"hold": hold, "fish": [self.fish("F1", 50)]}, [{"catch": True}])
        self.assertEqual(events(rows, "fish_caught"), [])
        self.assertEqual(events(rows, "hold_full")[0]["data"]["free"], 0)
        self.assertEqual(snapshots(rows)[-1]["hold_count"], len(hold))

    def test_fresh_faint_lifo_payload_and_empty_handoff(self):
        scenario = {"player": {"pos": [50, 10], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                    "hold": [self.item("I2", 90), self.item("I10", 80)]}
        rows, _ = self.probe(self.manifest(fresh=True), scenario)
        lost = events(rows, "faint")[0]["data"]["lost"]
        self.assertEqual([i["id"] for i in lost], ["I10", "I2"])
        self.assertTrue(all(set(i) == {"id", "kind", "fresh"} for i in lost))
        self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": []})

    def test_fresh_timeout_and_dock_handoff_keep_current_freshness(self):
        for scenario, step in (({"time_left_ticks": 1}, {}),
                               ({"player": {"pos": [2, 0]}}, {"interact": True})):
            with self.subTest(scenario=scenario):
                rows, _ = self.probe(self.manifest(fresh=True),
                                     {"hold": [self.item("I10", 80), self.item("I2", 90)], **scenario}, [step])
                items = events(rows, "gather_end")[0]["data"]["inventory"]["items"]
                self.assertEqual([i["id"] for i in items], ["I2", "I10"])
                self.assertAlmostEqual(items[0]["fresh"], 90 - 2 / 240, delta=0.001)

    def test_pause_caller_freezes_freshness_and_current_timers(self):
        config = {"interval_ticks": 2, "warning_ticks": 1, "duration_ticks": 3, "min_depth": 10, "speed": 1.5}
        rows, _ = self.probe(self.manifest(fresh=True, current=True, current_tuning=config),
                             {"hold": [self.item()], "current_direction": 1},
                             [{}, {}, {"advance": False}, {"advance": False}, {}])
        snaps = snapshots(rows)
        self.assertEqual(snaps[2], snaps[3])
        self.assertEqual(snaps[3], snaps[4])
        self.assertLess(snaps[5]["hold"][0]["fresh"], snaps[4]["hold"][0]["fresh"])

    def test_item_ids_continue_across_phases_with_shared_allocator(self):
        c = self.manifest(fresh=True)
        phase = {"contract": c, "scenario": {"player": {"pos": [50, 10]}, "random_fish": False,
                 "fish": [self.fish("F1", 50)], "nodes": [], "monsters": []}, "steps": [{"catch": True}]}
        rows, _ = self.probe(phases=[phase, {**phase, "day": 2}])
        self.assertEqual([e["data"]["item_ids"] for e in events(rows, "fish_caught")], [["I1"], ["I2"]])

    def test_net_fresh_items_get_unique_ids_for_every_caught_school(self):
        rows, _ = self.probe(self.manifest(fresh=True, net=True),
                             {"fish": [self.fish("F2", 51, "ca_linh"), self.fish("F10", 52)]},
                             [{"catch": True}], {"net": 2})
        self.assertEqual([e["data"]["item_ids"] for e in events(rows, "fish_caught")],
                         [["I1", "I2", "I3"], ["I4"]])
        self.assertEqual(len({i["id"] for i in snapshots(rows)[-1]["hold"]}), 4)

    @staticmethod
    def monster_config():
        return {"species": {"ca_sau": {"patrol_speed": 1, "chase_speed": 3, "detect_radius": 10,
                "exit_radius": 16, "depths": [10, 30], "hit_radius": 1.5,
                "recoil_ticks": 60, "recoil_dist": 2}}, "spawns": [], "invuln_ticks": 90, "loss_ratio": 0.5}

    def test_monster_loss_and_faint_export_individuals_in_lifo_order(self):
        c = self.manifest(fresh=True, current=True, current_tuning={"interval_ticks": 1, "warning_ticks": 0,
                             "duration_ticks": 480, "min_depth": 10, "speed": 1.5})
        c["tuning"]["gather"]["monsters"] = self.monster_config()
        rows, _ = self.probe(c, {"player": {"pos": [50, 10], "hp": 1}, "current_direction": 1,
                             "hold": [self.item(f"I{i}", 80) for i in range(1, 6)],
                             "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [50, 10],
                                           "waypoints": [[50, 10], [51, 10]]}]})
        lost = events(rows, "monster_hit")[0]["data"]["lost"]
        faint = events(rows, "faint")[0]["data"]["lost"]
        self.assertEqual([i["id"] for i in lost], ["I5", "I4"])
        self.assertEqual([i["id"] for i in faint], ["I3", "I2", "I1"])
        self.assertTrue(all(set(i) == {"id", "kind", "fresh"} for i in lost + faint))
        names = [e["name"] for e in events(rows)]
        self.assertLess(names.index("current_end"), names.index("faint"))
        self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": []})

    def test_current_does_not_change_monster_patrol(self):
        c = self.manifest(current=True, current_tuning={"interval_ticks": 1, "warning_ticks": 0,
                             "duration_ticks": 480, "min_depth": 10, "speed": 1.5})
        c["tuning"]["gather"]["monsters"] = self.monster_config()
        rows, _ = self.probe(c, {"player": {"pos": [100, 10]}, "current_direction": 1,
                             "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [20, 10],
                                           "waypoints": [[20, 10], [21, 10]]}]})
        self.assertAlmostEqual(snapshots(rows)[-1]["monsters"][0]["pos"][0], 20 + 1 / 60, delta=0.001)

    def test_current_runs_again_and_each_cycle_ends_once(self):
        c = self.manifest(current=True, current_tuning={"interval_ticks": 4, "warning_ticks": 1,
                             "duration_ticks": 2, "min_depth": 10, "speed": 1.5})
        rows, _ = self.probe(c, {"current_direction": -1}, [{}] * 10)
        self.assertEqual([e["tick"] for e in events(rows, "current_warning")], [3, 7])
        self.assertEqual([e["tick"] for e in events(rows, "current_end")], [6, 10])

    def test_current_dock_emits_phase_end_before_gather_end(self):
        c = self.manifest(current=True, current_tuning={"interval_ticks": 1, "warning_ticks": 0,
                             "duration_ticks": 480, "min_depth": 10, "speed": 1.5})
        rows, _ = self.probe(c, {"player": {"pos": [2, 0]}, "current_direction": -1}, [{"interact": True}])
        names = [e["name"] for e in events(rows)]
        self.assertLess(names.index("current_end"), names.index("gather_end"))
        self.assertEqual(events(rows, "current_end")[0]["data"]["reason"], "phase_end")

    def test_current_default_warning_start_and_end_ticks(self):
        rows, _ = self.probe(self.manifest(current=True),
                             {"player": {"pos": [50, 0]}, "current_direction": 1}, [{}] * 2280)
        by_tick = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "current_warning")],
                         [(1680, {"starts_at_phase_tick": 1800})])
        self.assertIsNone(by_tick[1799]["current"])
        self.assertEqual(by_tick[1800]["current"], {"direction": 1, "ticks_left": 480})
        self.assertEqual(by_tick[2279]["current"]["ticks_left"], 1)
        self.assertIsNone(by_tick[2280]["current"])
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "current_end")],
                         [(2280, {"direction": 1, "reason": "elapsed"})])

    def test_current_start_depth_and_velocity_not_accumulated(self):
        config = {"interval_ticks": 2, "warning_ticks": 1, "duration_ticks": 3, "min_depth": 10, "speed": 1.5}
        for depth, shift in ((9.999, 0), (10, 0.025)):
            with self.subTest(depth=depth):
                rows, _ = self.probe(self.manifest(current=True, current_tuning=config),
                                     {"player": {"pos": [50, depth]}, "current_direction": 1}, [{}, {}, {}])
                snaps = snapshots(rows)
                self.assertAlmostEqual(snaps[2]["player"]["pos"][0], 50 + shift, delta=0.001)
                self.assertAlmostEqual(snaps[3]["player"]["pos"][0], 50 + 2 * shift, delta=0.001)
                self.assertEqual(snaps[3]["player"]["vel"], [0, 0])

    def test_current_uses_start_depth_when_crossing_threshold(self):
        config = {"interval_ticks": 1, "warning_ticks": 0, "duration_ticks": 3, "min_depth": 10, "speed": 1.5}
        rows, _ = self.probe(self.manifest(current=True, current_tuning=config),
                             {"player": {"pos": [50, 9.999]}, "current_direction": 1}, [{"move": [0, 1]}])
        self.assertGreater(snapshots(rows)[-1]["player"]["pos"][1], 10)
        self.assertEqual(snapshots(rows)[-1]["player"]["pos"][0], 50)

    def test_current_clamps_player_and_does_not_push_fish_or_monster(self):
        config = {"interval_ticks": 1, "warning_ticks": 0, "duration_ticks": 3, "min_depth": 10, "speed": 1.5}
        rows, _ = self.probe(self.manifest(current=True, current_tuning=config),
                             {"player": {"pos": [100, 10]}, "current_direction": 1,
                              "fish": [self.fish("F1", 80)]}, [{}])
        last = snapshots(rows)[-1]
        self.assertEqual(last["player"]["pos"][0], 100)
        self.assertEqual(last["fish"][0]["pos"], [80, 10])
        self.assertEqual(last["player"]["vel"], [0, 0])

    def test_current_disabled_is_byte_identical_to_core(self):
        c = self.manifest(current=True)
        c["extensions"] = []
        _, base = self.probe(steps=[{}] * 10)
        _, disabled = self.probe(c, steps=[{}] * 10)
        self.assertEqual(base, disabled)

    def test_random_current_false_disables_schedule(self):
        c = self.manifest(current=True, current_tuning={"interval_ticks": 2, "warning_ticks": 1,
                             "duration_ticks": 3, "min_depth": 10, "speed": 1.5})
        rows, _ = self.probe(c, {"random_current": False, "current_direction": 1}, [{}] * 10)
        self.assertEqual(events(rows, "current_warning"), [])
        self.assertEqual(events(rows, "current_end"), [])
        self.assertTrue(all(s["current"] is None for s in snapshots(rows)))

    def test_current_phase_end_precedes_timeout_and_faint(self):
        config = {"interval_ticks": 1, "warning_ticks": 0, "duration_ticks": 480, "min_depth": 10, "speed": 1.5}
        for player, reason in (({"pos": [50, 10]}, "time"),
                               ({"pos": [50, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1}, "fainted")):
            with self.subTest(reason=reason):
                rows, _ = self.probe(self.manifest(current=True, current_tuning=config),
                                     {"player": player, "time_left_ticks": 1, "current_direction": -1})
                names = [e["name"] for e in events(rows)]
                self.assertLess(names.index("current_end"), names.index("gather_end"))
                if reason == "fainted":
                    self.assertLess(names.index("current_end"), names.index("faint"))
                self.assertEqual(events(rows, "current_end")[0]["data"], {"direction": -1, "reason": "phase_end"})
                self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], reason)

    def test_current_seed_and_freshness_are_deterministic_bytes(self):
        c = self.manifest(fresh=True, current=True, current_tuning={"interval_ticks": 3, "warning_ticks": 1,
                             "duration_ticks": 1, "min_depth": 10, "speed": 1.5})
        args = {"contract": c, "scenario": {"hold": [self.item()]}, "steps": [{}] * 10, "seed": 41}
        self.assertEqual(self.probe(**args)[1], self.probe(**args)[1])


if __name__ == "__main__":
    unittest.main()
