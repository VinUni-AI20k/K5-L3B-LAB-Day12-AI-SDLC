"""Test headless cho Lát 1 theo Test Contract v1.0, mục E, F và G."""

import json
import math
import unittest
from pathlib import Path

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherCore(unittest.TestCase):
    def run_gather(self, workdir, scenario, ticks, *inputs, snapshot_every=1, run="gather"):
        fixture = {"random_fish": False, "nodes": [], **scenario}
        scenario_path = write_json(workdir.path("scenario.json"), {"gather": fixture})
        inputs_path = write_json(workdir.path("inputs.json"), frames(*inputs))
        out = workdir.path(f"{run}.jsonl")
        inventory = workdir.path(f"{run}.inventory.json")
        code, err = run_headless(
            "--mode", "gather", "--seed", "42", "--ticks", str(ticks),
            "--snapshot-every", str(snapshot_every), "--scenario", scenario_path,
            "--inputs", inputs_path, "--out", out, "--inventory-out", inventory,
        )
        self.assertEqual(code, 0, err)
        return read_jsonl(out)

    def test_oxygen_and_transition_events_follow_depth_after_movement(self):
        player = {"pos": [20, 0.49], "vel": [0, 4], "oxygen_ticks": 15}
        with Workdir() as w:
            rows = self.run_gather(
                w, {"player": player}, 10,
                {"tick": 0, "move": [0, 1]}, {"tick": 2, "move": [0, -1]},
            )

        players = {s["tick"]: s["player"] for s in snapshots(rows)}
        self.assertEqual([players[t]["oxygen_ticks"] for t in range(11)],
                         [15, 14, 13, 12, 11, 10, 9, 8, 7, 13, 19])
        self.assertEqual([players[t]["at_surface"] for t in range(11)],
                         [True] + [False] * 8 + [True, True])
        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)], [
            (1, "dive", {"pos": [20, 0.557]}),
            (9, "surface", {"pos": [20, 0.49]}),
        ])

    def test_surface_threshold_is_inclusive_and_refill_caps_at_max(self):
        player = {"pos": [20, 0.5], "oxygen_ticks": 1797}
        with Workdir() as w:
            rows = self.run_gather(w, {"player": player}, 2)

        self.assertEqual([s["player"]["oxygen_ticks"] for s in snapshots(rows)],
                         [1797, 1800, 1800])
        self.assertTrue(all(s["player"]["at_surface"] for s in snapshots(rows)))
        self.assertEqual(events(rows), [])

    def test_oxygen_stays_at_zero_and_empty_is_emitted_only_on_depletion(self):
        player = {"pos": [20, 5], "oxygen_ticks": 2}
        with Workdir() as w:
            rows = self.run_gather(w, {"player": player}, 4)

        self.assertEqual([s["player"]["oxygen_ticks"] for s in snapshots(rows)], [2, 1, 0, 0, 0])
        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)],
                         [(2, "oxygen_empty", {"oxygen_ticks": 0})])

    def test_dive_precedes_oxygen_empty_on_the_same_tick(self):
        player = {"pos": [20, 0.5], "vel": [0, 4], "oxygen_ticks": 1}
        with Workdir() as w:
            rows = self.run_gather(w, {"player": player}, 1, {"tick": 0, "move": [0, 1]})

        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)], [
            (1, "dive", {"pos": [20, 0.567]}),
            (1, "oxygen_empty", {"oxygen_ticks": 0}),
        ])

    def test_first_choke_is_59_ticks_after_depletion_then_every_60_ticks(self):
        player = {"pos": [20, 5], "oxygen_ticks": 3}
        with Workdir() as w:
            rows = self.run_gather(w, {"player": player}, 122)

        exhaustion = events(rows, "oxygen_empty")
        self.assertEqual([e["tick"] for e in exhaustion], [3])
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "choke")],
                         [(62, {"hp": 2}), (122, {"hp": 1})])
        players = {s["tick"]: s["player"] for s in snapshots(rows)}
        self.assertEqual([players[t]["zero_oxy_ticks"] for t in (2, 3, 61, 62, 122)],
                         [0, 1, 59, 0, 0])
        self.assertEqual(players[61]["hp"], 3)
        self.assertEqual(rows[-1]["reason"], "tick_limit")

    def test_surfacing_on_the_choke_tick_refills_oxygen_and_spares_hp(self):
        player = {"pos": [20, 0.51], "oxygen_ticks": 1}
        with Workdir() as w:
            rows = self.run_gather(w, {"player": player}, 62, {"tick": 59, "move": [0, -1]})

        self.assertEqual([(e["tick"], e["name"]) for e in events(rows)],
                         [(1, "oxygen_empty"), (60, "surface")])
        players = {s["tick"]: s["player"] for s in snapshots(rows)}
        self.assertEqual(players[59]["zero_oxy_ticks"], 59)
        self.assertFalse(players[59]["at_surface"])
        self.assertEqual(players[60]["zero_oxy_ticks"], 0)
        self.assertEqual(players[60]["oxygen_ticks"], 6)
        self.assertEqual(players[60]["hp"], 3)
        self.assertTrue(players[60]["at_surface"])

    def test_reaching_exact_surface_depth_on_choke_tick_spares_hp(self):
        player = {"pos": [20, 0.625], "vel": [0, -2.5],
                  "oxygen_ticks": 0, "zero_oxy_ticks": 57, "hp": 1}
        with Workdir() as w:
            rows = self.run_gather(w, {"player": player}, 3, {"tick": 0, "move": [0, -0.625]})

        # Từ 0.625 m, bơi lên 3 tick ở 2.5 m/s đưa người chơi tới đúng 0.5 m.
        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)],
                         [(3, "surface", {"pos": [20, 0.5]})])
        final = snapshots(rows)[-1]["player"]
        self.assertEqual((final["oxygen_ticks"], final["zero_oxy_ticks"], final["hp"]), (6, 0, 1))
        self.assertTrue(final["at_surface"])

    def test_depth_just_beyond_surface_threshold_still_consumes_oxygen(self):
        player = {"pos": [20, math.nextafter(0.5, math.inf)], "oxygen_ticks": 2}
        with Workdir() as w:
            rows = self.run_gather(w, {"player": player}, 1)

        final = snapshots(rows)[-1]["player"]
        self.assertFalse(final["at_surface"])
        self.assertEqual(final["oxygen_ticks"], 1)

    def test_faint_preempts_actions_and_timeout_and_exports_empty_inventory(self):
        for x in (2, 20):  # Trong bến hoặc ngoài bến với cá ở đúng vị trí.
            with self.subTest(x=x), Workdir() as w:
                scenario = {
                    "player": {"pos": [x, 1], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                    "hold": ["bong_sung", "ca_loc", "bong_sung", "ca_linh"],
                    "fish": [{"id": "F1", "kind": "ca_loc", "pos": [x, 1]}],
                    "time_left_ticks": 1,
                }
                inventory = Path(w.path("gather.inventory.json"))
                write_json(inventory, {"items": {"ca_loc": 2}})
                rows = self.run_gather(
                    w, scenario, 5, {"tick": 0, "interact": True, "catch": True},
                    snapshot_every=10,
                )
                self.assertEqual(json.loads(inventory.read_bytes()), {"items": {}})
                self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)], [
                    (1, "choke", {"hp": 0}),
                    (1, "faint", {"cause": "choke",
                                  "lost": ["ca_linh", "bong_sung", "ca_loc", "bong_sung"], "hp": 0}),
                    (1, "gather_end", {"reason": "fainted", "inventory": {"items": {}}}),
                ])
                self.assertEqual([r["type"] for r in rows],
                                 ["snapshot", "event", "event", "event", "snapshot", "end"])
                final = rows[-2]
                self.assertEqual((final["tick"], final["state"], final["time_left_ticks"]),
                                 (1, "finished", 0))
                self.assertEqual((final["player"]["hp"], final["player"]["zero_oxy_ticks"]), (0, 0))
                self.assertEqual((final["hold"], final["hold_count"]), ([], 0))
                self.assertEqual([fish["id"] for fish in final["fish"]], ["F1"])
                self.assertEqual((rows[-1]["reason"], rows[-1]["ticks"]), ("fainted", 1))

    def test_same_seed_and_inputs_produce_identical_jsonl_and_inventory(self):
        scenario = {
            "player": {"pos": [20, 5], "oxygen_ticks": 2, "hp": 1},
            "hold": ["ca_loc", "bong_sung"],
        }
        inputs = ({"tick": 0, "move": [1, 0]}, {"tick": 12, "move": [0, 0]})
        with Workdir() as w:
            for run in ("first", "second"):
                rows = self.run_gather(w, scenario, 100, *inputs, snapshot_every=10, run=run)
                self.assertEqual((rows[-1]["reason"], rows[-1]["ticks"]), ("fainted", 61))
            for suffix in (".jsonl", ".inventory.json"):
                self.assertEqual(Path(w.path("first" + suffix)).read_bytes(),
                                 Path(w.path("second" + suffix)).read_bytes())

    def test_movement_into_dock_on_final_tick_keeps_inventory(self):
        scenario = {
            "player": {"pos": [5.05, 0], "vel": [-4, 0]},
            "hold": ["bong_sung"],
            "time_left_ticks": 1,
        }
        with Workdir() as w:
            rows = self.run_gather(
                w, scenario, 1, {"tick": 0, "move": [-1, 0], "interact": True},
            )
            inventory = json.loads(Path(w.path("gather.inventory.json")).read_bytes())

        final = snapshots(rows)[-1]
        self.assertEqual(final["player"]["pos"], [4.983, 0])
        self.assertEqual((final["time_left_ticks"], rows[-1]["reason"]), (0, "docked"))
        self.assertEqual(events(rows, "gather_end")[0]["data"],
                         {"reason": "docked", "inventory": {"items": {"bong_sung": 1}}})
        self.assertEqual(inventory, {"items": {"bong_sung": 1}})

    def test_timeout_underwater_keeps_inventory(self):
        scenario = {
            "player": {"pos": [20, 5], "oxygen_ticks": 2},
            "hold": ["ca_loc"],
            "time_left_ticks": 2,
        }
        with Workdir() as w:
            rows = self.run_gather(w, scenario, 5)
            inventory = json.loads(Path(w.path("gather.inventory.json")).read_bytes())

        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)], [
            (2, "oxygen_empty", {"oxygen_ticks": 0}),
            (2, "gather_end", {"reason": "time", "inventory": {"items": {"ca_loc": 1}}}),
        ])
        self.assertEqual((rows[-1]["reason"], rows[-1]["ticks"]), ("time", 2))
        self.assertEqual(inventory, {"items": {"ca_loc": 1}})
