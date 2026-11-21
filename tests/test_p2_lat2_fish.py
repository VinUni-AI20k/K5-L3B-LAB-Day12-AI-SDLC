"""Black-box & integration tests for Phase 2 Lát 2 (fish swim, turn, reflection, spawn, ca_keo, N5/N6)."""

import math
import unittest

from helpers import (
    Workdir,
    close,
    events,
    frames,
    read_jsonl,
    run_headless,
    snapshots,
    write_json,
)


class TestPhase2Lat2Fish(unittest.TestCase):
    def test_fish_swims_at_1_5_mps_and_reflects_on_bounds(self):
        """Fish swims at 1.5 m/s in x in [4, 96] and species depth range, reflecting remaining distance on edges."""
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [2, 0]},
                        "nodes": [],
                        "fish": [
                            {
                                "id": "F1",
                                "kind": "ca_linh",
                                "pos": [95.9, 5.0],
                                "heading_deg": 0.0,
                                "age_ticks": 0,
                            }
                        ],
                    }
                },
            )
            code, err = run_headless(
                "--mode", "gather",
                "--seed", "42",
                "--ticks", "10",
                "--scenario", sc,
                "--snapshot-every", "1",
                "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            snaps = {r["tick"]: r for r in snapshots(read_jsonl(w.path("o.jsonl")))}
            f10 = snaps[10]["fish"][0]
            # 10 ticks * (1.5 / 60) = 0.25 m -> 95.9 + 0.25 = 96.15 -> reflects at 96.0 by 0.15 => x = 95.85, heading ~ 180
            self.assertTrue(close(f10["pos"][0], 95.85, 0.02), f10)
            self.assertTrue(close(f10["heading_deg"], 180.0, 0.5), f10)
            self.assertGreaterEqual(f10["pos"][1], 3.0)
            self.assertLessEqual(f10["pos"][1], 12.0)

    def test_fish_corner_reflection_reverses_both_axes(self):
        """Fish hitting corner of swim bounds reflects both x and depth components."""
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [2, 0]},
                        "nodes": [],
                        "fish": [
                            {
                                "id": "F1",
                                "kind": "ca_linh",
                                "pos": [95.99, 11.99],
                                "heading_deg": 45.0,
                                "age_ticks": 0,
                            }
                        ],
                    }
                },
            )
            code, err = run_headless(
                "--mode", "gather",
                "--seed", "42",
                "--ticks", "5",
                "--scenario", sc,
                "--snapshot-every", "5",
                "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            f5 = snapshots(read_jsonl(w.path("o.jsonl")))[-1]["fish"][0]
            self.assertLess(f5["pos"][0], 96.0)
            self.assertLess(f5["pos"][1], 12.0)
            self.assertTrue(close(f5["heading_deg"], 225.0, 1.0), f5)

    def test_fish_turns_at_120_steps_before_moving_and_is_deterministic_by_seed(self):
        """Fish turns at age_ticks % 120 == 0 before moving; two runs with same seed are byte-identical."""
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [2, 0]},
                        "nodes": [],
                        "fish": [
                            {
                                "id": "F1",
                                "kind": "ca_linh",
                                "pos": [50.0, 8.0],
                                "heading_deg": 0.0,
                                "age_ticks": 119,
                            }
                        ],
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, 0]}))
            for idx in (1, 2):
                code, err = run_headless(
                    "--mode", "gather",
                    "--seed", "7",
                    "--ticks", "2",
                    "--scenario", sc,
                    "--inputs", inp,
                    "--snapshot-every", "1",
                    "--out", w.path(f"o{idx}.jsonl"),
                )
                self.assertEqual(code, 0, err)

            with open(w.path("o1.jsonl"), "rb") as a, open(w.path("o2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())

            snaps = {r["tick"]: r for r in snapshots(read_jsonl(w.path("o1.jsonl")))}
            self.assertTrue(close(snaps[1]["fish"][0]["pos"][0], 50.0 + 1.5 / 60.0, 1e-4))
            self.assertNotAlmostEqual(snaps[2]["fish"][0]["heading_deg"], 0.0, places=2)

    def test_spawn_fish_at_phase_tick_360_and_swims_after_spawn(self):
        """At phase_tick = 360*k (after fish swim), spawns <= 1 fish (>1m from existing) and swims once active."""
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [2, 0]},
                        "nodes": [],
                        "fish": [],
                        "random_fish": True,
                    }
                },
            )
            code, err = run_headless(
                "--mode", "gather",
                "--seed", "123",
                "--ticks", "362",
                "--scenario", sc,
                "--snapshot-every", "360",
                "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            spawned_360 = [e for e in events(rows, "fish_spawned") if e["tick"] == 360]
            self.assertEqual(len(spawned_360), 1)
            ev = spawned_360[0]["data"]
            self.assertIn(ev["kind"], ("ca_linh", "ca_loc", "ca_keo"))

            snaps = {r["tick"]: r for r in snapshots(rows)}
            f360 = [f for f in snaps[360]["fish"] if f["id"] == ev["id"]][0]
            f362 = [f for f in snaps[362]["fish"] if f["id"] == ev["id"]][0]
            self.assertEqual(f360["pos"], ev["pos"])
            self.assertGreater(math.dist(f360["pos"], f362["pos"]), 0.0)

    def test_random_fish_false_disables_swim_and_spawn(self):
        """When random_fish is false, fixture fish stay stationary and no scheduled spawn occurs."""
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [2, 0]},
                        "nodes": [],
                        "fish": [
                            {
                                "id": "F1",
                                "kind": "ca_keo",
                                "pos": [45.0, 24.0],
                                "heading_deg": 0.0,
                                "age_ticks": 120,
                            }
                        ],
                        "random_fish": False,
                    }
                },
            )
            code, err = run_headless(
                "--mode", "gather",
                "--seed", "1",
                "--ticks", "365",
                "--scenario", sc,
                "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "fish_spawned"), [])
            last = snapshots(rows)[-1]
            self.assertEqual(len(last["fish"]), 1)
            self.assertEqual(last["fish"][0]["pos"], [45.0, 24.0])

    def test_catch_ca_keo_yield_2_and_gather_keo_neo_n5_n6(self):
        """Catching ca_keo yields 2; N5 and N6 harvest keo_neo at surface."""
        with Workdir() as w:
            sc_fish = write_json(
                w.path("sc_fish.json"),
                {
                    "gather": {
                        "player": {"pos": [45.0, 24.0]},
                        "nodes": [],
                        "fish": [{"id": "F1", "kind": "ca_keo", "pos": [45.0, 24.0]}],
                        "random_fish": False,
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless(
                "--mode", "gather",
                "--seed", "1",
                "--ticks", "1",
                "--scenario", sc_fish,
                "--inputs", inp,
                "--out", w.path("c.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("c.jsonl"))
            c_evs = events(rows, "fish_caught")
            self.assertEqual(len(c_evs), 1)
            self.assertEqual(c_evs[0]["data"], {"fish_id": "F1", "kind": "ca_keo", "yield": 2})
            self.assertEqual(snapshots(rows)[-1]["hold"], ["ca_keo", "ca_keo"])

            for nid, pos in (("N5", [76.0, 0.0]), ("N6", [90.0, 0.0])):
                sc_node = write_json(
                    w.path(f"sc_{nid}.json"),
                    {
                        "gather": {
                            "player": {"pos": pos},
                            "nodes": [{"id": nid, "kind": "keo_neo", "pos": pos}],
                            "fish": [],
                            "random_fish": False,
                        }
                    },
                )
                inp_n = write_json(w.path(f"in_{nid}.json"), frames({"tick": 0, "interact": True}))
                code_n, err_n = run_headless(
                    "--mode", "gather",
                    "--seed", "1",
                    "--ticks", "1",
                    "--scenario", sc_node,
                    "--inputs", inp_n,
                    "--out", w.path(f"{nid}.jsonl"),
                )
                self.assertEqual(code_n, 0, err_n)
                g_evs = events(read_jsonl(w.path(f"{nid}.jsonl")), "gather")
                self.assertEqual(len(g_evs), 1)
                self.assertEqual(g_evs[0]["data"], {"node_id": nid, "kind": "keo_neo", "amount": 1})


if __name__ == "__main__":
    unittest.main()