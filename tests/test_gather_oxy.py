"""Gather lát 1 (@justapea25): dive/surface, oxy, ngạt, Máu, ngất, giỏ LIFO.

Phần lớn là test hộp đen qua headless; riêng helper `_add_to_hold` test trực tiếp trên GatherSim.
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


def contract():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


G = contract()["gather"]
OXY_MAX = int(round(G["oxygen_max_s"] * 60))
CHOKE = G["choke_interval_ticks"]


def run_gather(w, scenario, ticks, inputs=None, extra=()):
    sc = write_json(w.path("sc.json"), {"gather": scenario})
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
            "--snapshot-every", "1", "--out", w.path("o.jsonl"), *extra]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), inputs)]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


def by_tick(rows):
    return {r["tick"]: r["player"] for r in snapshots(rows)}


class Oxygen(unittest.TestCase):
    def test_duoi_nuoc_tru_1_moi_tick(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10]}}, 60)
            self.assertEqual(by_tick(rows)[60]["oxygen_ticks"], OXY_MAX - 60)
            self.assertEqual(events(rows, "oxygen_empty"), [])

    def test_mat_nuoc_hoi_va_kep_max(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 0], "oxygen_ticks": 10}}, 2)
            p = by_tick(rows)
            refill = G["oxygen_refill_per_tick"]
            self.assertEqual(p[1]["oxygen_ticks"], 10 + refill)
            self.assertEqual(p[2]["oxygen_ticks"], 10 + 2 * refill)
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 0], "oxygen_ticks": OXY_MAX - 1}}, 1)
            self.assertEqual(by_tick(rows)[1]["oxygen_ticks"], OXY_MAX)

    def test_oxygen_empty_dung_mot_lan(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 3}}, 30)
            ev = events(rows, "oxygen_empty")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["tick"], 3)


class Zone(unittest.TestCase):
    def test_dive_roi_surface(self):
        with Workdir() as w:
            inp = frames({"tick": 0, "move": [0, 1]}, {"tick": 60, "move": [0, -1]})
            rows = run_gather(w, {"player": {"pos": [50, 0]}}, 180, inp)
            dive, surf = events(rows, "dive"), events(rows, "surface")
            self.assertEqual(len(dive), 1)
            self.assertEqual(len(surf), 1)
            self.assertLess(dive[0]["tick"], surf[0]["tick"])
            self.assertGreater(dive[0]["data"]["pos"][1], G["surface_depth"])
            self.assertLessEqual(surf[0]["data"]["pos"][1], G["surface_depth"])


class Choke(unittest.TestCase):
    def test_choke_sau_moi_chu_ky(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0}}, 2 * CHOKE)
            ch = events(rows, "choke")
            self.assertEqual([e["tick"] for e in ch], [CHOKE, 2 * CHOKE])
            self.assertEqual([e["data"]["hp"] for e in ch], [G["hp_max"] - 1, G["hp_max"] - 2])

    def test_len_mat_nuoc_reset_dem_ngat(self):
        with Workdir() as w:
            # ngay dưới mặt nước, đang bơi lên: tick 1 đã lên mặt nước -> không choke dù sắp đủ chu kỳ
            rows = run_gather(w, {"player": {"pos": [50, 0.55], "vel": [0, -G["swim_speed"]], "oxygen_ticks": 0,
                                             "zero_oxy_ticks": CHOKE - 1}}, 1, frames({"tick": 0, "move": [0, -1]}))
            self.assertEqual(len(events(rows, "surface")), 1)
            self.assertEqual(by_tick(rows)[1]["zero_oxy_ticks"], 0)
            self.assertEqual(events(rows, "choke"), [])

    def test_ngat_mat_gio_kho_rong(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            rows = run_gather(w, {"hold": ["ca_loc", "bong_sung"],
                                  "player": {"pos": [50, 10], "oxygen_ticks": 0, "hp": 1,
                                             "zero_oxy_ticks": CHOKE - 1}}, 50,
                              extra=("--inventory-out", inv))
            self.assertEqual(len(events(rows, "faint")), 1)
            end = events(rows, "gather_end")
            self.assertEqual(len(end), 1)
            self.assertEqual(end[0]["tick"], 1)
            self.assertEqual(end[0]["data"], {"reason": "fainted", "inventory": {"items": {}}})
            self.assertEqual(rows[-1]["reason"], "fainted")
            self.assertEqual(snapshots(rows)[-1]["hold"], [])
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


class Hold(unittest.TestCase):
    def make(self, hold):
        return GatherSim(contract(), {"hold": hold, "random_fish": False}, Streams(1), IdAllocator())

    def test_them_vao_cuoi_lifo(self):
        sim, ev = self.make(["ca_loc"]), []
        self.assertTrue(sim._add_to_hold("ca_linh", 3, ev))
        self.assertEqual(sim.hold, ["ca_loc", "ca_linh", "ca_linh", "ca_linh"])
        self.assertEqual(ev, [])

    def test_day_thi_hold_full_khong_them(self):
        cap = G["hold_capacity"]
        sim, ev = self.make(["ca_loc"] * (cap - 2)), []
        self.assertFalse(sim._add_to_hold("ca_linh", 3, ev))
        self.assertEqual(len(sim.hold), cap - 2)
        self.assertEqual(ev[0][0], "hold_full")
        self.assertTrue(sim._add_to_hold("bong_sung", 2, ev))
        self.assertEqual(len(sim.hold), cap)


if __name__ == "__main__":
    unittest.main()
