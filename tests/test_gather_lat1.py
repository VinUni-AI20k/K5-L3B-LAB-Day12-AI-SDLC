"""Lát 1 — oxy / dive-surface / ngạt / ngất / API giỏ. Hộp đen qua headless + unit API hold."""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def sc_underwater(*, oxygen_ticks, zero_oxy_ticks=0, hp=3, hold=None, time_left_ticks=10_000):
    return {
        "gather": {
            "player": {
                "pos": [20, 5],
                "vel": [0, 0],
                "oxygen_ticks": oxygen_ticks,
                "zero_oxy_ticks": zero_oxy_ticks,
                "hp": hp,
            },
            "hold": hold or [],
            "nodes": [],
            "fish": [],
            "random_fish": False,
            "time_left_ticks": time_left_ticks,
        }
    }


class HoldApi(unittest.TestCase):
    def _sim(self, hold=None):
        tuning = load_contract()["tuning"]
        return GatherSim(tuning, {"hold": hold or [], "nodes": [], "fish": [], "random_fish": False},
                         Streams(1), IdAllocator())

    def test_can_hold_and_push_lifo_order(self):
        sim = self._sim()
        cap = sim.t["hold_capacity"]
        self.assertEqual(sim.free_hold_slots(), cap)
        self.assertTrue(sim.can_hold(1))
        sim.push_hold(["ca_loc", "bong_sung"])
        self.assertEqual(sim.hold, ["ca_loc", "bong_sung"])
        self.assertEqual(sim.free_hold_slots(), cap - 2)
        self.assertFalse(sim.can_hold(cap))
        self.assertTrue(sim.can_hold(cap - 2))


class OxygenChokeFaint(unittest.TestCase):
    def test_dive_and_surface_events(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [20, 0], "vel": [0, 0]},
                    "nodes": [], "fish": [], "random_fish": False,
                    "time_left_ticks": 500,
                }
            })
            # bơi xuống vài tick rồi nổi lên
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "move": [0, 1]},
                {"tick": 40, "move": [0, -1]},
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--scenario", sc,
                                     "--inputs", inp, "--ticks", "120", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertTrue(events(rows, "dive"), "phải có dive khi xuống dưới biên mặt nước")
            self.assertTrue(events(rows, "surface"), "phải có surface khi nổi lại")

    def test_oxygen_empty_then_first_choke_at_t_plus_59(self):
        """Oxy 1 dưới nước → empty ở tick 1; ngạt lần đầu ở tick 60 (= t+59)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), sc_underwater(oxygen_ticks=1, zero_oxy_ticks=0, hp=3))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, 0]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--scenario", sc,
                                     "--inputs", inp, "--ticks", "60", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            empty = events(rows, "oxygen_empty")
            self.assertEqual(len(empty), 1)
            self.assertEqual(empty[0]["tick"], 1)
            chokes = events(rows, "choke")
            self.assertEqual(len(chokes), 1)
            self.assertEqual(chokes[0]["tick"], 60)
            self.assertEqual(chokes[0]["data"]["hp"], 2)
            snap = snapshots(rows)[-1]["player"]
            self.assertEqual(snap["hp"], 2)
            self.assertEqual(snap["oxygen_ticks"], 0)
            self.assertEqual(snap["zero_oxy_ticks"], 0)

    def test_surface_on_choke_step_skips_choke(self):
        """Nổi đúng bước đáng lẽ ngạt → hồi oxy, không choke."""
        tuning = load_contract()["tuning"]
        speed = float(tuning["gather"]["swim_speed"])
        # d vừa > surface_depth; đã có vận tốc lên đủ để về mặt nước trong 1 bước
        sim = GatherSim(
            tuning,
            {
                "player": {
                    "pos": [20, 0.51],
                    "vel": [0.0, -speed],
                    "oxygen_ticks": 0,
                    "zero_oxy_ticks": 59,
                    "hp": 3,
                },
                "hold": [], "nodes": [], "fish": [], "random_fish": False,
                "time_left_ticks": 1000,
            },
            Streams(1), IdAllocator(),
        )
        sim._tgt = (0.0, -speed)
        sim._ramp_left = 0
        li = LiveInputs()
        li.set(move=[0, -1])
        ev = sim.step(li.advance())
        names = [n for n, _ in ev]
        self.assertIn("surface", names)
        self.assertNotIn("choke", names)
        self.assertGreater(sim.oxygen_ticks, 0)
        self.assertEqual(sim.zero_oxy_ticks, 0)
        self.assertEqual(sim.hp, 3)

    def test_faint_drops_hold_lifo_and_empty_inventory(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), sc_underwater(
                oxygen_ticks=0, zero_oxy_ticks=59, hp=1,
                hold=["ca_loc", "bong_sung", "ca_linh"],
            ))
            inv_out = w.path("catch.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--scenario", sc,
                "--ticks", "1", "--out", w.path("o.jsonl"), "--inventory-out", inv_out,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "choke")[0]["data"]["hp"], 0)
            faint = events(rows, "faint")[0]
            self.assertEqual(faint["data"]["cause"], "choke")
            self.assertEqual(faint["data"]["hp"], 0)
            self.assertEqual(faint["data"]["lost"], ["ca_linh", "bong_sung", "ca_loc"])
            end = events(rows, "gather_end")[0]
            self.assertEqual(end["data"]["reason"], "fainted")
            self.assertEqual(end["data"]["inventory"], {"items": {}})
            with open(inv_out, encoding="utf-8") as f:
                import json
                self.assertEqual(json.load(f), {"items": {}})


if __name__ == "__main__":
    unittest.main()
