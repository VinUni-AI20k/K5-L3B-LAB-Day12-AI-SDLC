"""Kiểm Gather core qua CLI headless theo Ticket 02."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherCore(unittest.TestCase):
    def run_gather(self, w, scenario, ticks, *input_frames):
        scenario_path = write_json(w.path("scenario.json"), {"gather": scenario})
        inputs_path = write_json(w.path("inputs.json"), frames(*input_frames))
        out_path = w.path("gather.jsonl")
        code, err = run_headless(
            "--mode", "gather", "--seed", "42", "--scenario", scenario_path,
            "--inputs", inputs_path, "--ticks", str(ticks), "--snapshot-every", "1",
            "--out", out_path, "--inventory-out", w.path("catch.json"),
        )
        self.assertEqual(code, 0, err)
        return read_jsonl(out_path)

    def test_surface_refills_and_stays_at_maximum(self):
        with Workdir() as w:
            rows = self.run_gather(w, {
                "player": {"pos": [20, 0.5], "oxygen_ticks": 1790},
                "random_fish": False,
            }, 1800)
            players = [row["player"] for row in snapshots(rows)]
            self.assertEqual([p["oxygen_ticks"] for p in players[:3]], [1790, 1796, 1800])
            self.assertTrue(all(p["oxygen_ticks"] == 1800 for p in players[2:]))
            self.assertEqual(events(rows), [])

    def test_dive_event_precedes_oxygen_empty_at_end_position(self):
        with Workdir() as w:
            rows = self.run_gather(w, {
                "player": {"pos": [20, 0.5], "oxygen_ticks": 1},
            }, 2, {"tick": 0, "move": [0, 1]})
            after_dive = snapshots(rows)[1]["player"]
            self.assertGreater(after_dive["pos"][1], 0.5)
            self.assertEqual(
                [(e["tick"], e["name"], e["data"]) for e in events(rows)],
                [(1, "dive", {"pos": after_dive["pos"]}), (1, "oxygen_empty", {"oxygen_ticks": 0})],
            )
            self.assertEqual(after_dive["zero_oxy_ticks"], 1)

    def test_choke_starts_59_ticks_after_empty_and_faint_drops_hold_lifo(self):
        with Workdir() as w:
            rows = self.run_gather(w, {
                "player": {"pos": [20, 4], "oxygen_ticks": 1},
                "hold": ["ca_loc", "bong_sung", "ca_linh"],
            }, 240)
            self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)], [
                (1, "oxygen_empty", {"oxygen_ticks": 0}),
                (60, "choke", {"hp": 2}),
                (120, "choke", {"hp": 1}),
                (180, "choke", {"hp": 0}),
                (180, "faint", {"cause": "choke", "lost": ["ca_linh", "bong_sung", "ca_loc"], "hp": 0}),
                (180, "gather_end", {"reason": "fainted", "inventory": {"items": {}}}),
            ])
            final = snapshots(rows)[-1]
            self.assertEqual(final["hold"], [])
            self.assertEqual(final["hold_count"], 0)
            self.assertEqual(final["player"]["zero_oxy_ticks"], 0)
            self.assertEqual(rows[-1]["reason"], "fainted")
            self.assertEqual(rows[-1]["ticks"], 180)
            with open(w.path("catch.json"), encoding="utf-8") as inventory_file:
                self.assertEqual(json.load(inventory_file), {"items": {}})

    def test_surfacing_on_choke_tick_restores_oxygen(self):
        with Workdir() as w:
            rows = self.run_gather(w, {
                "player": {"pos": [20, 0.501], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
            }, 2, {"tick": 0, "move": [0, -1]})
            after_surface = snapshots(rows)[1]["player"]
            self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)],
                             [(1, "surface", {"pos": after_surface["pos"]})])
            self.assertTrue(after_surface["at_surface"])
            self.assertEqual(after_surface["hp"], 1)
            self.assertEqual(after_surface["oxygen_ticks"], 6)
            self.assertEqual(after_surface["zero_oxy_ticks"], 0)

    def test_faint_precedes_dock_catch_and_timeout(self):
        with Workdir() as w:
            rows = self.run_gather(w, {
                "player": {"pos": [2, 1], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [2, 1]}],
                "time_left_ticks": 1,
            }, 1, {"tick": 0, "interact": True, "catch": True})
            self.assertEqual([e["name"] for e in events(rows)], ["choke", "faint", "gather_end"])
            self.assertEqual(events(rows, "faint")[0]["data"]["lost"], [])
            self.assertEqual([f["id"] for f in snapshots(rows)[-1]["fish"]], ["F1"])
            self.assertEqual(rows[-1]["reason"], "fainted")
