"""Kiểm đường truyền manifest/day/upgrades tới catch qua headless_cmd thật.

Chạy khi owner đã ghép shop.net + metadata hooks, hoặc qua command kiểm trong
thư mục tạm với --with-integration-patches. Không đổi manifest gốc để bật test.
"""

import json
from pathlib import Path
import shutil
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class NetDayRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        c = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))
        cls.contract = c
        cls.g = c["tuning"]["gather"]
        if "net" not in c["tuning"].get("shop", {}).get("upgrades", {}):
            raise unittest.SkipTest("Net day CLI requires Integrator's shop data + extension/upgrades hooks")

    def run_day(self, level, fish, *, hold=(), ticks=1, inputs=None):
        with Workdir() as w:
            sc = write_json(w.path("scenario.json"), {"day": {"upgrades": {"net": level}},
                    "gather": {"player": {"pos": [50, 10]}, "nodes": [], "fish": fish,
                               "hold": list(hold), "random_fish": False, "monsters": []}})
            inp = write_json(w.path("inputs.json"), frames(*(inputs or [{"tick": 0, "catch": True}])))
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "day", "--days", "1", "--seed", "1", "--ticks", str(ticks),
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            return read_jsonl(out)

    @staticmethod
    def fish(ident, x, kind="ca_loc"):
        return {"id": ident, "kind": kind, "pos": [x, 10], "heading_deg": 0}

    def test_level_zero_uses_nearest_core_target(self):
        rows = self.run_day(0, [self.fish("F2", 51.5), self.fish("F10", 51)])
        self.assertEqual([e["data"]["fish_id"] for e in events(rows, "fish_caught")], ["F10"])

    def test_two_net_levels_reach_radius_and_limit_in_id_order(self):
        fish = [self.fish("F10", 51), self.fish("F2", 54), self.fish("F3", 56), self.fish("F20", 56.001)]
        for level, expected in ((1, ["F2", "F10"]), (2, ["F2", "F3", "F10"])):
            with self.subTest(level=level):
                rows = self.run_day(level, fish)
                caught = events(rows, "fish_caught")
                self.assertEqual([e["data"]["fish_id"] for e in caught], expected)
                self.assertTrue(all(e["day"] == 1 for e in caught))

    def test_full_school_does_not_block_later_smaller_school(self):
        rows = self.run_day(1, [self.fish("F2", 51, "ca_linh"), self.fish("F10", 52)],
                            hold=["bong_sung"] * (self.g["hold_capacity"] - 1))
        # Bỏ event mở pha (day_start/day_plan/phase_start) — chỉ xét event của cú bắt
        caught_events = [e["name"] for e in events(rows) if e["name"] in ("hold_full", "fish_caught")]
        self.assertEqual(caught_events, ["hold_full", "fish_caught"])
        self.assertEqual([f["id"] for f in snapshots(rows)[-1]["fish"]], ["F2"])

    def test_net_cooldown_allows_second_press_exactly_30_ticks_later(self):
        rows = self.run_day(1, [self.fish(f"F{i}", 51) for i in range(1, 5)], ticks=31,
                            inputs=[{"tick": 0, "catch": True}, {"tick": 1, "catch": False},
                                    {"tick": 28, "catch": True}, {"tick": 29, "catch": False},
                                    {"tick": 30, "catch": True}])
        self.assertEqual([e["tick"] for e in events(rows, "fish_caught")], [1, 1, 31, 31])

    def test_no_fish_does_not_start_cooldown(self):
        rows = self.run_day(2, [])
        self.assertEqual(events(rows, "fish_caught"), [])
        self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"], 0)

    def test_current_manifest_reaches_real_headless_and_pushes_for_480_ticks(self):
        # Verify metadata wiring through the real CLI without enabling the P3 inventory schema.
        # Increased oxygen is test data so the player survives the entire scheduled current.
        with Workdir() as w:
            shutil.copytree(Path(ROOT) / "chonoi", w.path("chonoi"),
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            c = json.loads(json.dumps(self.contract))
            c["extensions"] = ["current"]
            c["tuning"]["gather"]["current"] = {"interval_ticks": 1800, "warning_ticks": 120,
                        "duration_ticks": 480, "min_depth": 10, "speed": 1.5}
            c["tuning"]["gather"]["oxygen_max_s"] = 120
            write_json(w.path("game.contract.json"), c)
            sc = write_json(w.path("scenario.json"), {"gather": {"player": {"pos": [50, 10]},
                        "random_fish": False, "monsters": [], "fish": [self.fish("F1", 20)]}})
            out = w.path("current.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2280", "--scenario", sc,
                                     "--out", out, "--snapshot-every", "1", cwd=w.path("."))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            by_tick = {s["tick"]: s for s in snapshots(rows)}
            direction = by_tick[1800]["current"]["direction"]
            self.assertIn(direction, (-1, 1))
            self.assertEqual(events(rows, "current_warning")[0]["tick"], 1680)
            self.assertAlmostEqual(by_tick[1800]["player"]["pos"][0], 50 + direction * 0.025, delta=0.001)
            self.assertAlmostEqual(by_tick[2279]["player"]["pos"][0], 50 + direction * 12, delta=0.001)
            self.assertEqual(by_tick[2280]["player"]["pos"], by_tick[2279]["player"]["pos"])
            self.assertEqual(by_tick[2280]["fish"][0]["pos"], [20, 10])
            self.assertEqual(by_tick[2280]["player"]["vel"], [0, 0])
            self.assertEqual([(e["tick"], e["data"]["reason"]) for e in events(rows, "current_end")], [(2280, "elapsed")])


if __name__ == "__main__":
    unittest.main()
