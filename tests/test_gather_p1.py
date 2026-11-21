"""Luật gather Phase 1 (lát 1 + lát 2), hộp đen qua headless_cmd. Mỗi test ghi AC tương ứng trong
docs/verification/phase-1.md. Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import json
import os
import unittest

from helpers import Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json


def run_gather(w, scenario, inputs=None, ticks=10, inv_out=False, every=1):
    sc = write_json(w.path("sc.json"), {"gather": scenario})
    args = ["--mode", "gather", "--seed", "1", "--scenario", sc, "--ticks", str(ticks),
            "--out", w.path("g.jsonl"), "--snapshot-every", str(every)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inv_out:
        args += ["--inventory-out", w.path("kho.json")]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("g.jsonl"))


def snap_at(rows, tick):
    return next(s for s in snapshots(rows) if s["tick"] == tick)


BASE = {"nodes": [], "random_fish": False}


class Lat1BoiOxyBienGio(unittest.TestCase):
    def test_ac_p1_01_dive_and_surface_events(self):
        with Workdir() as w:
            rows = run_gather(w, dict(BASE), [{"tick": 0, "move": [0, 1]}, {"tick": 30, "move": [0, -1]}], ticks=60)
            dive, surf = events(rows, "dive"), events(rows, "surface")
            self.assertEqual(len(dive), 1)
            self.assertGreater(dive[0]["data"]["pos"][1], 0.5)
            self.assertEqual(len(surf), 1)
            self.assertLessEqual(surf[0]["data"]["pos"][1], 0.5)
            self.assertLess(dive[0]["tick"], surf[0]["tick"])

    def test_ac_p1_02_oxygen_drains_underwater_and_refills_at_surface(self):
        with Workdir() as w:
            rows = run_gather(w, dict(BASE, player={"pos": [50, 10], "oxygen_ticks": 100}), ticks=10)
            self.assertEqual(snap_at(rows, 10)["player"]["oxygen_ticks"], 90)
        with Workdir() as w:
            rows = run_gather(w, dict(BASE, player={"pos": [50, 0], "oxygen_ticks": 1790}), ticks=3)
            self.assertEqual(snap_at(rows, 1)["player"]["oxygen_ticks"], 1796)
            self.assertEqual(snap_at(rows, 2)["player"]["oxygen_ticks"], 1800)  # kẹp tối đa

    def test_ac_p1_03_oxygen_empty_then_choke_at_t_plus_59(self):
        with Workdir() as w:
            rows = run_gather(w, dict(BASE, player={"pos": [50, 10], "oxygen_ticks": 1}), ticks=125, every=200)
            empty = events(rows, "oxygen_empty")
            self.assertEqual([e["tick"] for e in empty], [1])
            self.assertEqual(empty[0]["data"], {"oxygen_ticks": 0})
            chokes = events(rows, "choke")
            self.assertEqual([e["tick"] for e in chokes], [60, 120])
            self.assertEqual([e["data"]["hp"] for e in chokes], [2, 1])

    def test_ac_p1_04_faint_drops_hold_lifo_and_empty_inventory(self):
        with Workdir() as w:
            sc = dict(BASE, player={"pos": [50, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                      hold=["ca_loc", "bong_sung", "ca_linh"])
            rows = run_gather(w, sc, ticks=10, inv_out=True)
            faint = events(rows, "faint")
            self.assertEqual(len(faint), 1)
            self.assertEqual(faint[0]["data"], {"cause": "choke", "lost": ["ca_linh", "bong_sung", "ca_loc"], "hp": 0})
            names = [e["name"] for e in events(rows)]
            self.assertEqual(names, ["choke", "faint", "gather_end"])
            end = events(rows, "gather_end")[0]["data"]
            self.assertEqual(end, {"reason": "fainted", "inventory": {"items": {}}})
            self.assertEqual(rows[-1]["reason"], "fainted")
            with open(w.path("kho.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})

    def test_ac_p1_05_surfacing_on_choke_tick_avoids_choke(self):
        with Workdir() as w:
            sc = dict(BASE, player={"pos": [50, 0.52], "vel": [0, -4], "oxygen_ticks": 0, "zero_oxy_ticks": 59})
            rows = run_gather(w, sc, [{"tick": 0, "move": [0, -1]}], ticks=2)
            self.assertEqual(events(rows, "choke"), [])
            self.assertEqual(snap_at(rows, 1)["player"]["oxygen_ticks"], 6)
            self.assertEqual(snap_at(rows, 1)["player"]["zero_oxy_ticks"], 0)

    def test_ac_p1_06_bounds_clamp_and_kill_outward_velocity(self):
        with Workdir() as w:
            rows = run_gather(w, dict(BASE, player={"pos": [0.01, 0]}), [{"tick": 0, "move": [-1, -1]}], ticks=20)
            s = snap_at(rows, 20)
            self.assertEqual(s["player"]["pos"], [0, 0])
            self.assertEqual(s["player"]["vel"], [0, 0])


class Lat2HaiBatBenKho(unittest.TestCase):
    def test_ac_p1_07_gather_at_exact_radius_edge(self):
        with Workdir() as w:
            sc = {"player": {"pos": [20, 0], "heading_deg": 0}, "hold": ["ca_loc", "bong_sung"],
                  "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [22, 0]}], "fish": [], "random_fish": False,
                  "time_left_ticks": 120}
            rows = run_gather(w, sc, [{"tick": 0, "interact": True}], ticks=2)
            ev = events(rows, "gather")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["tick"], 1)
            self.assertEqual(ev[0]["data"], {"node_id": "N1", "kind": "bong_dien_dien", "amount": 1})
            s = snap_at(rows, 1)
            self.assertEqual(s["hold"], ["ca_loc", "bong_sung", "bong_dien_dien"])
            self.assertEqual(s["nodes"][0]["regrow_ticks"], 1200)
            self.assertFalse(s["nodes"][0]["ready"])

    def test_ac_p1_08_nearest_node_tie_breaks_by_id(self):
        with Workdir() as w:
            sc = dict(BASE, player={"pos": [20, 0]},
                      nodes=[{"id": "N10", "kind": "bong_sung", "pos": [21, 0]},
                             {"id": "N2", "kind": "bong_dien_dien", "pos": [19, 0]}])
            rows = run_gather(w, sc, [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")

    def test_ac_p1_09_gather_only_at_surface_and_hold_full(self):
        node = [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}]
        with Workdir() as w:
            rows = run_gather(w, dict(BASE, player={"pos": [20, 1]}, nodes=node), [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual(events(rows, "gather") + events(rows, "hold_full"), [])
        with Workdir() as w:
            rows = run_gather(w, dict(BASE, player={"pos": [20, 0]}, nodes=node, hold=["ca_loc"] * 12),
                              [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual(events(rows, "hold_full")[0]["data"],
                             {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
            self.assertTrue(snap_at(rows, 1)["nodes"][0]["ready"])

    def test_ac_p1_10_node_regrown_then_gatherable_same_step(self):
        with Workdir() as w:
            sc = dict(BASE, player={"pos": [20, 0]}, nodes=[{"id": "N1", "kind": "bong_sung", "pos": [20, 0], "regrow_ticks": 1}])
            rows = run_gather(w, sc, [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual([e["name"] for e in events(rows)], ["node_regrown", "gather"])

    def test_ac_p1_11_catch_whole_yield_at_edge_and_remove_school(self):
        with Workdir() as w:
            sc = dict(BASE, player={"pos": [30, 10]}, fish=[{"id": "F1", "kind": "ca_linh", "pos": [32, 10]}])
            rows = run_gather(w, sc, [{"tick": 0, "catch": True}], ticks=1)
            ev = events(rows, "fish_caught")
            self.assertEqual(ev[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "yield": 3})
            s = snap_at(rows, 1)
            self.assertEqual(s["hold"], ["ca_linh"] * 3)
            self.assertEqual(s["fish"], [])
            self.assertEqual(s["player"]["catch_cd_ticks"], 30)

    def test_ac_p1_12_catch_cooldown_reusable_from_t_plus_L(self):
        fish = [{"id": "F1", "kind": "ca_loc", "pos": [30, 10]}, {"id": "F2", "kind": "ca_loc", "pos": [30.5, 10]}]
        for press, expect in ((29, 1), (30, 2)):
            with Workdir() as w:
                rows = run_gather(w, dict(BASE, player={"pos": [30, 10]}, fish=fish),
                                  [{"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": press, "catch": True}],
                                  ticks=40, every=100)
                caught = events(rows, "fish_caught")
                self.assertEqual(len(caught), expect, press)
                if expect == 2:
                    self.assertEqual(caught[1]["tick"], 31)

    def test_ac_p1_13_catch_hold_full_keeps_school_and_no_cooldown(self):
        with Workdir() as w:
            sc = dict(BASE, player={"pos": [30, 10]}, hold=["ca_loc"] * 10,
                      fish=[{"id": "F1", "kind": "ca_linh", "pos": [31, 10]}])
            rows = run_gather(w, sc, [{"tick": 0, "catch": True}], ticks=1)
            self.assertEqual(events(rows, "hold_full")[0]["data"],
                             {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
            s = snap_at(rows, 1)
            self.assertEqual(len(s["fish"]), 1)
            self.assertEqual(s["player"]["catch_cd_ticks"], 0)

    def test_ac_p1_14_catch_ignored_at_surface_and_out_of_range(self):
        with Workdir() as w:
            sc = dict(BASE, player={"pos": [30, 0]}, fish=[{"id": "F1", "kind": "ca_loc", "pos": [30, 1]}])
            rows = run_gather(w, sc, [{"tick": 0, "catch": True}], ticks=1)
            self.assertEqual(events(rows), [])
        with Workdir() as w:
            sc = dict(BASE, player={"pos": [30, 10]}, fish=[{"id": "F1", "kind": "ca_loc", "pos": [32.5, 10]}])
            rows = run_gather(w, sc, [{"tick": 0, "catch": True}], ticks=1)
            self.assertEqual(events(rows), [])
            self.assertEqual(snap_at(rows, 1)["player"]["catch_cd_ticks"], 0)

    def test_ac_p1_15_time_end_keeps_hold_and_writes_inventory(self):
        with Workdir() as w:
            sc = dict(BASE, player={"pos": [60, 12]}, hold=["ca_loc", "ca_linh"], time_left_ticks=5)
            rows = run_gather(w, sc, ticks=100, inv_out=True)
            end = events(rows, "gather_end")
            self.assertEqual(end[0]["tick"], 5)
            self.assertEqual(end[0]["data"]["reason"], "time")
            self.assertEqual(end[0]["data"]["inventory"], {"items": {"ca_linh": 1, "ca_loc": 1}})
            self.assertEqual(rows[-1]["reason"], "time")
            with open(w.path("kho.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), end[0]["data"]["inventory"])

    def test_ac_p1_16_tick_limit_does_not_write_inventory(self):
        with Workdir() as w:
            rows = run_gather(w, dict(BASE), ticks=5, inv_out=True)
            self.assertEqual(rows[-1]["reason"], "tick_limit")
            self.assertFalse(os.path.exists(w.path("kho.json")))

    def test_ac_p1_17_dock_at_any_depth_inside_radius(self):
        with Workdir() as w:
            rows = run_gather(w, dict(BASE, player={"pos": [2, 3]}, hold=["bong_sung"]),
                              [{"tick": 0, "interact": True}], ticks=5, inv_out=True)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
            self.assertTrue(close(snapshots(rows)[-1]["player"]["pos"][1], 3))

    def test_ac_p1_18_full_default_run_catches_with_preset(self):
        """Bắt được đàn của bố trí mặc định (không scenario cá).

        Cập nhật Phase 2 (v1.1 §1.1): preset không còn là 6 đàn đứng yên F1 [15,5]...; đầu ca sinh 8 đàn
        theo seed và đàn bơi, nên không lặn theo đường cố định tới F1 nữa. Thay bằng: đọc vị trí đàn ở
        tick 0 của lượt mặc định, rồi đặt người chơi đúng chỗ đàn đó (cùng seed) và bắt ở bước đầu —
        bắt xét vị trí cá TRƯỚC khi bơi nên vẫn trúng."""
        with Workdir() as w:
            fish0 = snap_at(run_gather(w, {}, ticks=0), 0)["fish"]
        self.assertEqual(len(fish0), 8)
        # tránh Cá Sấu M1 tuần tra [60,24]–[64,24]
        target = next(f for f in fish0 if min(abs(f["pos"][0] - 62), 99) > 14)
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": target["pos"]}}, [{"tick": 0, "catch": True}], ticks=1)
            caught = events(rows, "fish_caught")
            self.assertEqual(len(caught), 1)
            self.assertEqual(caught[0]["data"]["fish_id"], target["id"])

if __name__ == "__main__":
    unittest.main()
