"""Unit & headless black-box tests for Gather Lát 2 (harvesting, regrowth, fishing, docking, inventory export)."""

import json
import os
import unittest

from helpers import (
    Workdir,
    events,
    frames,
    read_jsonl,
    run_headless,
    snapshots,
    write_json,
)


def tuning_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


class TestGatherLat2(unittest.TestCase):
    def test_gather_surface_node_exact_edge_and_regrow(self):
        """Harvests ready surface node at exact interact_radius, sets regrow_ticks, and emits node_regrown."""
        g = tuning_gather()
        regrow_ticks = int(round(g["regrow_s"] * 60))
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [20, 0]},
                        "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [22, 0]}],
                        "fish": [],
                        "random_fish": False,
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless(
                "--mode", "gather",
                "--seed", "1",
                "--ticks", str(regrow_ticks + 1),
                "--scenario", sc,
                "--inputs", inp,
                "--snapshot-every", "1",
                "--out", w.path("out.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("out.jsonl"))

            g_evs = events(rows, "gather")
            self.assertEqual(len(g_evs), 1)
            self.assertEqual(g_evs[0]["tick"], 1)
            self.assertEqual(
                g_evs[0]["data"],
                {"node_id": "N1", "kind": "bong_dien_dien", "amount": g["node_yield"]},
            )

            snaps = {r["tick"]: r for r in snapshots(rows)}
            self.assertEqual(snaps[1]["hold"], ["bong_dien_dien"])
            self.assertEqual(snaps[1]["nodes"][0]["regrow_ticks"], regrow_ticks)
            self.assertFalse(snaps[1]["nodes"][0]["ready"])

            reg_evs = events(rows, "node_regrown")
            self.assertEqual(len(reg_evs), 1)
            self.assertEqual(reg_evs[0]["tick"], 1 + regrow_ticks)
            self.assertEqual(reg_evs[0]["data"], {"node_id": "N1"})
            self.assertTrue(snaps[1 + regrow_ticks]["nodes"][0]["ready"])

    def test_gather_underwater_ignored_and_tie_break_by_id(self):
        """Cannot harvest when underwater (d > surface_depth); ties at surface pick smallest Unicode id."""
        with Workdir() as w:
            # 1) Underwater -> ignored
            sc_under = write_json(
                w.path("sc_under.json"),
                {
                    "gather": {
                        "player": {"pos": [20, 1.0]},
                        "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
                        "fish": [],
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc_under, "--inputs", inp, "--out", w.path("u.jsonl"),
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(events(read_jsonl(w.path("u.jsonl")), "gather"), [])

            # 2) Equidistant nodes N10 vs N2 -> N2 wins (natural id sort)
            sc_tie = write_json(
                w.path("sc_tie.json"),
                {
                    "gather": {
                        "player": {"pos": [20, 0]},
                        "nodes": [
                            {"id": "N10", "kind": "bong_sung", "pos": [21, 0]},
                            {"id": "N2", "kind": "bong_dien_dien", "pos": [19, 0]},
                        ],
                        "fish": [],
                    }
                },
            )
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc_tie, "--inputs", inp, "--out", w.path("t.jsonl"),
            )
            self.assertEqual(code, 0, err)
            g_evs = events(read_jsonl(w.path("t.jsonl")), "gather")
            self.assertEqual(len(g_evs), 1)
            self.assertEqual(g_evs[0]["data"]["node_id"], "N2")

    def test_gather_hold_full_leaves_node_ready(self):
        """Full hold emits hold_full and does not consume/reset the plant node."""
        g = tuning_gather()
        cap = g["hold_capacity"]
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [20, 0]},
                        "hold": ["ca_loc"] * cap,
                        "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
                        "fish": [],
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1)
            self.assertEqual(
                hf[0]["data"],
                {"action": "gather", "node_id": "N1", "required": g["node_yield"], "free": 0},
            )
            self.assertTrue(snapshots(rows)[-1]["nodes"][0]["ready"])

    def test_catch_underwater_removes_fish_and_sets_cooldown(self):
        """Catching underwater adds full yield, removes fish school, and enforces catch_cooldown_s."""
        g = tuning_gather()
        cd_ticks = int(round(g["catch_cooldown_s"] * 60))
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [15, 5]},
                        "nodes": [],
                        "fish": [
                            {"id": "F1", "kind": "ca_linh", "pos": [15, 5]},
                            {"id": "F2", "kind": "ca_loc", "pos": [15.5, 5]},
                        ],
                    }
                },
            )
            # Press catch at tick 0 (succeeds), release at 1, press at 2 during cooldown (ignored),
            # release at cd_ticks-1, press at cd_ticks (succeeds on F2).
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "catch": True},
                    {"tick": 1, "catch": False},
                    {"tick": 2, "catch": True},
                    {"tick": 3, "catch": False},
                    {"tick": cd_ticks, "catch": True},
                ),
            )
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", str(cd_ticks + 1),
                "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            caught = events(rows, "fish_caught")
            self.assertEqual(len(caught), 2)
            self.assertEqual(
                caught[0]["data"],
                {"fish_id": "F1", "kind": "ca_linh", "yield": g["fish_yield"]["ca_linh"]},
            )
            self.assertEqual(
                caught[1]["data"],
                {"fish_id": "F2", "kind": "ca_loc", "yield": g["fish_yield"]["ca_loc"]},
            )
            last = snapshots(rows)[-1]
            self.assertEqual(last["fish"], [])
            self.assertEqual(last["hold"], ["ca_linh"] * 3 + ["ca_loc"])

    def test_catch_surface_ignored_and_hold_full_no_cooldown(self):
        """Catch at surface does nothing; catch when hold lacks space emits hold_full without cooldown or removal."""
        g = tuning_gather()
        cap = g["hold_capacity"]
        with Workdir() as w:
            # 1) Surface catch ignored
            sc_surf = write_json(
                w.path("sc_surf.json"),
                {
                    "gather": {
                        "player": {"pos": [15, 0.5]},
                        "nodes": [],
                        "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 1.0]}],
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc_surf, "--inputs", inp, "--out", w.path("s.jsonl"),
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(events(read_jsonl(w.path("s.jsonl")), "fish_caught"), [])

            # 2) Only 2 free slots, ca_linh needs 3 -> hold_full, fish stays, cooldown stays 0
            sc_full = write_json(
                w.path("sc_full.json"),
                {
                    "gather": {
                        "player": {"pos": [15, 5]},
                        "hold": ["bong_sung"] * (cap - 2),
                        "nodes": [],
                        "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}],
                    }
                },
            )
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc_full, "--inputs", inp, "--out", w.path("f.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("f.jsonl"))
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1)
            self.assertEqual(
                hf[0]["data"],
                {"action": "catch", "fish_id": "F1", "required": 3, "free": 2},
            )
            last = snapshots(rows)[-1]
            self.assertEqual(len(last["fish"]), 1)
            self.assertEqual(last["player"]["catch_cd_ticks"], 0)

    def test_dock_priority_over_harvest_and_last_tick_collect(self):
        """Docking takes priority over overlapping harvest node; harvesting on final tick still enters inventory."""
        g = tuning_gather()
        with Workdir() as w:
            # 1) Node inside dock radius: interact docks immediately without harvesting
            sc_dock = write_json(
                w.path("sc_dock.json"),
                {
                    "gather": {
                        "player": {"pos": [2, 0]},
                        "hold": ["ca_loc"],
                        "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [2, 0]}],
                        "fish": [],
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv1 = w.path("inv1.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "5",
                "--scenario", sc_dock, "--inputs", inp,
                "--inventory-out", inv1, "--out", w.path("d.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("d.jsonl"))
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
            with open(inv1, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"ca_loc": 1}})

            # 2) Harvest on final tick (time_left_ticks == 1) still enters inventory on time end
            sc_last = write_json(
                w.path("sc_last.json"),
                {
                    "gather": {
                        "player": {"pos": [20, 0]},
                        "time_left_ticks": 1,
                        "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [20, 0]}],
                        "fish": [],
                    }
                },
            )
            inv2 = w.path("inv2.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "5",
                "--scenario", sc_last, "--inputs", inp,
                "--inventory-out", inv2, "--out", w.path("l.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows2 = read_jsonl(w.path("l.jsonl"))
            self.assertEqual(events(rows2, "gather_end")[0]["data"]["reason"], "time")
            with open(inv2, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_dien_dien": g["node_yield"]}})


if __name__ == "__main__":
    unittest.main()