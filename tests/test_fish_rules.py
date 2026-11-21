"""P2 ticket 02: test hộp đen qua CLI/JSONL, chạy khi có prefactor v1.1.

Contract gốc không bị sửa. Ca cần tuning khác chạy một bản sao package với
manifest tạm, dùng nguyên validator và headless_cmd của repo.
"""

import copy
import json
import math
from pathlib import Path
import shutil
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class FishRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))
        cls.g = cls.contract["tuning"]["gather"]
        cls.hz = cls.contract["tuning"]["tick_hz"]
        if "fish_speed" not in cls.g:
            raise unittest.SkipTest("P2 fish CLI tests require ticket 01 / contract v1.1; P1 regression still runs")

    def run_gather(self, block=None, ticks=1, inputs=(), seed=1, tuning=None):
        with Workdir() as w:
            args = ["--mode", "gather", "--seed", str(seed), "--ticks", str(ticks),
                    "--snapshot-every", "1", "--out", w.path("out.jsonl")]
            if block is not None:
                args += ["--scenario", write_json(w.path("scenario.json"), {"gather": block})]
            if inputs:
                args += ["--inputs", write_json(w.path("inputs.json"), frames(*inputs))]
            cwd = ROOT
            if tuning:
                cwd = w.path(".")
                shutil.copytree(Path(ROOT) / "chonoi", w.path("chonoi"),
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                contract = copy.deepcopy(self.contract)
                contract["tuning"]["gather"].update(tuning)
                write_json(w.path("game.contract.json"), contract)
            code, err = run_headless(*args, cwd=cwd)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("out.jsonl"))
            return rows, Path(w.path("out.jsonl")).read_bytes()

    @staticmethod
    def fish(ident="F1", kind="ca_linh", pos=None, heading=0, age=0):
        return {"id": ident, "kind": kind, "pos": pos or [50, 5],
                "heading_deg": heading, "age_ticks": age}

    def assert_heading(self, actual, expected):
        self.assertAlmostEqual((actual - expected + 180) % 360 - 180, 0, delta=0.002)

    def spawn_fixture(self, open_kind=None, offset=0):
        """Điểm sinh x=50, chặn mọi điểm trừ loài cần thử; số liệu ca kiểm riêng."""
        depths = self.g["fish_spawn_depths"]
        fish = []
        for kind, points in sorted(depths.items()):
            if kind == open_kind:
                continue
            for depth in points:
                fish.append(self.fish(f"F{len(fish) + 1}", kind, [50 + offset, depth]))
        return {"fish_spawn_x": [50], "fish_spawn_ticks": 1}, fish

    def test_initial_eight_unique_schools_from_manifest(self):
        rows, _ = self.run_gather(ticks=0)
        fish = snapshots(rows)[0]["fish"]
        self.assertEqual(len(fish), 8)
        self.assertEqual(len({tuple(f["pos"]) for f in fish}), 8)
        self.assertEqual({f["kind"] for f in fish}, set(self.g["fish_weights"]))
        for f in fish:
            self.assertIn(f["pos"][0], self.g["fish_spawn_x"])
            self.assertIn(f["pos"][1], self.g["fish_spawn_depths"][f["kind"]])
            self.assertEqual(f["age_ticks"], 0)

    def test_three_species_swim_at_configured_speed(self):
        for kind, limits in self.g["fish_depths"].items():
            with self.subTest(kind=kind):
                depth = sum(limits) / 2
                rows, _ = self.run_gather({"fish": [self.fish(kind=kind, pos=[50, depth])]}, ticks=self.hz)
                fish = snapshots(rows)[-1]["fish"][0]
                self.assertAlmostEqual(fish["pos"][0], 50 + self.g["fish_speed"], delta=0.002)
                self.assertAlmostEqual(fish["pos"][1], depth, delta=0.002)
                self.assertEqual(fish["age_ticks"], self.hz)

    def test_turn_at_tick_120_before_movement(self):
        turn = self.g["fish_turn_ticks"]
        rows, _ = self.run_gather({"fish": [self.fish(pos=[50, 7])]}, ticks=turn)
        before, after = snapshots(rows)[-2:]
        a, b = before["fish"][0], after["fish"][0]
        self.assert_heading(a["heading_deg"], 0)
        self.assertNotEqual(b["heading_deg"], 0)
        angle = math.radians(b["heading_deg"])
        step = self.g["fish_speed"] / self.hz
        self.assertAlmostEqual(b["pos"][0] - a["pos"][0], math.cos(angle) * step, delta=0.002)
        self.assertAlmostEqual(b["pos"][1] - a["pos"][1], math.sin(angle) * step, delta=0.002)

    def test_reflect_remaining_distance_at_each_edge(self):
        xlo, xhi = self.g["fish_x"]
        dlo, dhi = self.g["fish_depths"]["ca_linh"]
        step = self.g["fish_speed"] / self.hz
        inset = step / 4
        cases = [([xhi - inset, 7], 0, [xhi - (step - inset), 7], 180),
                 ([xlo + inset, 7], 180, [xlo + (step - inset), 7], 0),
                 ([50, dhi - inset], 90, [50, dhi - (step - inset)], 270),
                 ([50, dlo + inset], 270, [50, dlo + (step - inset)], 90)]
        for pos, heading, expected, reflected in cases:
            with self.subTest(heading=heading):
                rows, _ = self.run_gather({"fish": [self.fish(pos=pos, heading=heading)]})
                fish = snapshots(rows)[-1]["fish"][0]
                for actual, target in zip(fish["pos"], expected):
                    self.assertAlmostEqual(actual, target, delta=0.001)
                self.assert_heading(fish["heading_deg"], reflected)

    def test_exact_wall_contact_points_inward_on_that_tick(self):
        hi = self.g["fish_x"][1]
        step = self.g["fish_speed"] / self.hz
        rows, _ = self.run_gather({"fish": [self.fish(pos=[hi - step, 7])]}, ticks=2)
        fish = [s["fish"][0] for s in snapshots(rows)]
        self.assertEqual(fish[1]["pos"][0], hi)
        self.assert_heading(fish[1]["heading_deg"], 180)
        self.assertAlmostEqual(fish[2]["pos"][0], hi - step, delta=0.001)

    def test_corner_reflects_both_components(self):
        xhi = self.g["fish_x"][1]
        dhi = self.g["fish_depths"]["ca_linh"][1]
        step = self.g["fish_speed"] / self.hz / math.sqrt(2)
        inset = step / 2
        rows, _ = self.run_gather({"fish": [self.fish(pos=[xhi - inset, dhi - inset], heading=45)]})
        fish = snapshots(rows)[-1]["fish"][0]
        self.assertAlmostEqual(fish["pos"][0], xhi - inset, delta=0.001)
        self.assertAlmostEqual(fish["pos"][1], dhi - inset, delta=0.001)
        self.assert_heading(fish["heading_deg"], 225)

    def test_multiple_wall_crossings_preserve_distance(self):
        rows, _ = self.run_gather({"fish": [self.fish(pos=[50, 7])]},
                                 tuning={"fish_x": [49.99, 50.01], "fish_speed": 6})
        fish = snapshots(rows)[-1]["fish"][0]
        self.assertAlmostEqual(fish["pos"][0], 50, delta=0.001)
        self.assert_heading(fish["heading_deg"], 180)

    def test_every_school_stays_in_its_species_depth_band(self):
        rows, _ = self.run_gather(ticks=2500)
        for snap in snapshots(rows):
            self.assertLessEqual(len(snap["fish"]), self.g["fish_max"])
            for fish in snap["fish"]:
                x, depth = fish["pos"]
                lo, hi = self.g["fish_depths"][fish["kind"]]
                self.assertTrue(self.g["fish_x"][0] <= x <= self.g["fish_x"][1])
                self.assertTrue(lo <= depth <= hi, (snap["tick"], fish))

    def test_random_false_disables_default_fish_and_spawning(self):
        rows, _ = self.run_gather({"random_fish": False}, ticks=self.g["fish_spawn_ticks"] + 1)
        self.assertTrue(all(s["fish"] == [] for s in snapshots(rows)))
        self.assertEqual(events(rows, "fish_spawned"), [])

    def test_random_false_freezes_fixture_but_increases_age(self):
        fixture = self.fish(heading=237, age=17)
        ticks = self.g["fish_spawn_ticks"] + 1
        rows, _ = self.run_gather({"random_fish": False, "fish": [fixture]}, ticks=ticks)
        fish = snapshots(rows)[-1]["fish"][0]
        self.assertEqual(fish["pos"], fixture["pos"])
        self.assertEqual(fish["heading_deg"], fixture["heading_deg"])
        self.assertEqual(fish["age_ticks"], 17 + ticks)
        self.assertEqual(events(rows, "fish_spawned"), [])

    def test_empty_fixture_overrides_initial_fish_and_first_spawn_is_tick_360(self):
        interval = self.g["fish_spawn_ticks"]
        rows, _ = self.run_gather({"fish": []}, ticks=interval)
        self.assertEqual(snapshots(rows)[0]["fish"], [])
        self.assertEqual(snapshots(rows)[-2]["fish"], [])
        spawned = events(rows, "fish_spawned")
        self.assertEqual(len(spawned), 1)
        self.assertEqual(spawned[0]["tick"], interval)

    def test_spawn_schedule_cap_and_newborn_waits_one_step(self):
        interval = self.g["fish_spawn_ticks"]
        rows, _ = self.run_gather(ticks=interval * 5 + 1)
        spawned = events(rows, "fish_spawned")
        self.assertEqual([e["tick"] for e in spawned], [interval * n for n in range(1, 5)])
        self.assertEqual([e["data"]["id"] for e in spawned], ["F9", "F10", "F11", "F12"])
        self.assertEqual(len(snapshots(rows)[-1]["fish"]), self.g["fish_max"])
        by_tick = {s["tick"]: s for s in snapshots(rows)}
        first = spawned[0]
        for event in spawned:
            self.assertEqual(set(event["data"]), {"id", "kind", "pos"})
            fish = by_tick[event["tick"]]["fish"]
            newborn = next(f for f in fish if f["id"] == event["data"]["id"])
            self.assertEqual(newborn["age_ticks"], 0)
            self.assertEqual(newborn["pos"], event["data"]["pos"])
            for other in fish:
                if other["id"] != newborn["id"]:
                    self.assertGreater(math.dist(newborn["pos"], other["pos"]),
                                       self.g["fish_spawn_clearance"] - 0.002)
        before = next(f for f in by_tick[interval]["fish"] if f["id"] == first["data"]["id"])
        after = next(f for f in by_tick[interval + 1]["fish"] if f["id"] == before["id"])
        self.assertEqual(after["age_ticks"], 1)
        self.assertAlmostEqual(math.dist(before["pos"], after["pos"]),
                               self.g["fish_speed"] / self.hz, delta=0.002)

    def test_full_population_skips_spawn(self):
        points = [(x, d) for x in self.g["fish_spawn_x"] for d in self.g["fish_spawn_depths"]["ca_linh"]]
        fish = [self.fish(f"F{i + 1}", pos=list(pos)) for i, pos in enumerate(points[:self.g["fish_max"]])]
        rows, _ = self.run_gather({"fish": fish}, ticks=self.g["fish_spawn_ticks"] * 2)
        self.assertEqual(len(snapshots(rows)[-1]["fish"]), self.g["fish_max"])
        self.assertEqual(events(rows, "fish_spawned"), [])

    def test_blocked_spawn_points_skip_turn(self):
        tuning, fish = self.spawn_fixture()
        rows, _ = self.run_gather({"fish": fish}, tuning=tuning)
        self.assertEqual(events(rows, "fish_spawned"), [])
        self.assertEqual(len(snapshots(rows)[-1]["fish"]), len(fish))

    def test_weighted_choice_renormalizes_over_available_species(self):
        tuning, fish = self.spawn_fixture(open_kind="ca_keo")
        for seed in range(8):
            with self.subTest(seed=seed):
                rows, _ = self.run_gather({"fish": fish}, seed=seed, tuning=tuning)
                spawned = events(rows, "fish_spawned")
                self.assertEqual(len(spawned), 1)
                self.assertEqual(spawned[0]["data"]["kind"], "ca_keo")
                self.assertIn(spawned[0]["data"]["pos"][1], self.g["fish_spawn_depths"]["ca_keo"])

    def test_clearance_is_strictly_greater_than_one(self):
        step = self.g["fish_speed"] / self.hz
        for extra, expected in ((0, 0), (0.000001, 1)):
            with self.subTest(extra=extra):
                tuning, fish = self.spawn_fixture(offset=self.g["fish_spawn_clearance"] + step)
                for f in fish:
                    f["heading_deg"] = 180
                fish[0]["pos"][0] += extra
                rows, _ = self.run_gather({"fish": fish}, tuning=tuning)
                self.assertEqual(len(events(rows, "fish_spawned")), expected)

    def test_spawn_clearance_is_checked_after_swimming(self):
        tuning, fish = self.spawn_fixture(offset=self.g["fish_spawn_clearance"])
        rows, _ = self.run_gather({"fish": fish}, tuning=tuning)
        self.assertEqual(len(events(rows, "fish_spawned")), 1)

    def test_newborn_cannot_be_caught_until_next_step(self):
        tuning, fish = self.spawn_fixture()
        free = fish.pop(0)
        # Cá đầu theo kind là ca_keo: chọn một điểm sâu của loài đó.
        pos = free["pos"]
        rows, _ = self.run_gather({"fish": fish, "player": {"pos": pos}}, ticks=3,
                                 inputs=[{"tick": 0, "catch": True}, {"tick": 1, "catch": False},
                                         {"tick": 2, "catch": True}], tuning=tuning)
        spawned = events(rows, "fish_spawned")
        caught = events(rows, "fish_caught")
        self.assertEqual(spawned[0]["tick"], 1)
        self.assertEqual([e["tick"] for e in caught], [3])
        self.assertEqual(caught[0]["data"]["fish_id"], spawned[0]["data"]["id"])

    def test_catch_three_species_keeps_whole_school_rule(self):
        for kind, amount in self.g["fish_yield"].items():
            with self.subTest(kind=kind):
                depth = sum(self.g["fish_depths"][kind]) / 2
                rows, _ = self.run_gather({"random_fish": False, "player": {"pos": [50, depth]},
                                          "fish": [self.fish(kind=kind, pos=[50, depth])]},
                                         inputs=[{"tick": 0, "catch": True}])
                self.assertEqual([e["data"] for e in events(rows, "fish_caught")],
                                 [{"fish_id": "F1", "kind": kind, "yield": amount}])
                self.assertEqual(snapshots(rows)[-1]["hold"], [kind] * amount)
                self.assertEqual(snapshots(rows)[-1]["fish"], [])
                self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"],
                                 round(self.g["catch_cooldown_s"] * self.hz))

    def test_catch_uses_position_after_fish_swimming(self):
        for start, heading, count in ((52.01, 180, 1), (51.99, 0, 0)):
            with self.subTest(start=start):
                rows, _ = self.run_gather({"player": {"pos": [50, 5]},
                                          "fish": [self.fish(pos=[start, 5], heading=heading)]},
                                         inputs=[{"tick": 0, "catch": True}])
                self.assertEqual(len(events(rows, "fish_caught")), count)

    def test_full_hold_does_not_try_smaller_school_or_start_cooldown(self):
        rows, _ = self.run_gather({"random_fish": False, "player": {"pos": [50, 10]},
                                  "hold": ["bong_sung"] * (self.g["hold_capacity"] - 2),
                                  "fish": [self.fish(pos=[50, 10]), self.fish("F2", "ca_loc", [51, 10])]},
                                 inputs=[{"tick": 0, "catch": True}])
        self.assertEqual([e["data"] for e in events(rows, "hold_full")],
                         [{"action": "catch", "fish_id": "F1", "required": self.g["fish_yield"]["ca_linh"], "free": 2}])
        self.assertEqual(len(snapshots(rows)[-1]["fish"]), 2)
        self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"], 0)

    def test_spawn_id_continues_after_caught_fixture_id(self):
        interval = self.g["fish_spawn_ticks"]
        rows, _ = self.run_gather({"player": {"pos": [50, 5]}, "fish": [self.fish("F99")]},
                                 ticks=interval * 2, inputs=[{"tick": 0, "catch": True}])
        self.assertEqual(events(rows, "fish_caught")[0]["data"]["fish_id"], "F99")
        self.assertEqual([e["data"]["id"] for e in events(rows, "fish_spawned")], ["F100", "F101"])

    def test_spawn_rng_and_turns_ignore_fixture_list_order(self):
        fish = [self.fish("F10", pos=[50, 7]), self.fish("F2", "ca_loc", [70, 14])]
        _, first = self.run_gather({"fish": fish}, ticks=self.g["fish_spawn_ticks"])
        _, second = self.run_gather({"fish": list(reversed(fish))}, ticks=self.g["fish_spawn_ticks"])
        self.assertEqual(first, second)

    def test_same_seed_is_byte_identical_different_seed_changes_fish(self):
        ticks = self.g["fish_spawn_ticks"] * 2
        _, first = self.run_gather(ticks=ticks, seed=17)
        _, second = self.run_gather(ticks=ticks, seed=17)
        _, other = self.run_gather(ticks=ticks, seed=18)
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)

    def test_speed_turn_spawn_and_cap_are_read_from_data(self):
        tuning = {"fish_speed": 2.4, "fish_turn_ticks": 4, "fish_spawn_ticks": 7, "fish_max": 9}
        rows, _ = self.run_gather(ticks=14, tuning=tuning)
        by_tick = {s["tick"]: s for s in snapshots(rows)}
        initial = by_tick[0]["fish"][0]
        after = by_tick[1]["fish"][0]
        self.assertAlmostEqual(after["pos"][0] - initial["pos"][0], 2.4 / self.hz, delta=0.002)
        self.assertNotEqual(by_tick[4]["fish"][0]["heading_deg"], by_tick[3]["fish"][0]["heading_deg"])
        self.assertEqual([e["tick"] for e in events(rows, "fish_spawned")], [7])
        self.assertEqual(len(by_tick[14]["fish"]), 9)


if __name__ == "__main__":
    unittest.main()
