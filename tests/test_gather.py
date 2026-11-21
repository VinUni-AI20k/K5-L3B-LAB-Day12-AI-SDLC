"""Test luật buổi sáng (`gather`) — Lát 1: dive/surface, oxy, ngạt, ngất, giỏ."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def _tuning_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


class GatherSlice1Test(unittest.TestCase):
    def test_dive_and_surface_events(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [20, 0]}}})
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "move": [0, 1]},
                {"tick": 30, "move": [0, -1]},
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "80",
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            dives = events(rows, "dive")
            surfaces = events(rows, "surface")
            self.assertEqual(len(dives), 1)
            self.assertEqual(len(surfaces), 1)
            self.assertGreater(dives[0]["data"]["pos"][1], _tuning_gather()["surface_depth"])
            self.assertLessEqual(surfaces[0]["data"]["pos"][1], _tuning_gather()["surface_depth"])
            self.assertLess(dives[0]["tick"], surfaces[0]["tick"])

    def test_oxygen_drain_and_refill_clamped(self):
        g = _tuning_gather()
        omax = int(round(g["oxygen_max_s"] * 60))
        refill = int(g["oxygen_refill_per_tick"])
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [20, 5], "oxygen_ticks": 100}}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("drain.jsonl"))
            self.assertEqual(code, 0, err)
            snaps = snapshots(read_jsonl(w.path("drain.jsonl")))
            self.assertEqual(snaps[-1]["player"]["oxygen_ticks"], 90)

            sc2 = write_json(w.path("sc2.json"), {"gather": {"player": {"pos": [20, 0], "oxygen_ticks": omax - 10}}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc2, "--snapshot-every", "1", "--out", w.path("refill.jsonl"))
            self.assertEqual(code, 0, err)
            snaps2 = {r["tick"]: r for r in snapshots(read_jsonl(w.path("refill.jsonl")))}
            self.assertEqual(snaps2[1]["player"]["oxygen_ticks"], min(omax, omax - 10 + refill))
            self.assertEqual(snaps2[5]["player"]["oxygen_ticks"], omax)

    def test_oxygen_empty_choke_and_surface_resets_zero_oxy(self):
        g = _tuning_gather()
        choke_iv = int(g["choke_interval_ticks"])
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5], "oxygen_ticks": 2, "hp": 3},
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(2 + choke_iv + 5),
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            empties = events(rows, "oxygen_empty")
            chokes = events(rows, "choke")
            self.assertEqual(len(empties), 1)
            self.assertEqual(empties[0]["tick"], 2)
            self.assertEqual(len(chokes), 1)
            self.assertEqual(chokes[0]["tick"], 2 + choke_iv)
            self.assertEqual(chokes[0]["data"]["hp"], 2)

            # Lên mặt nước reset zero_oxy_ticks về 0
            sc2 = write_json(w.path("sc2.json"), {"gather": {
                "player": {"pos": [20, 0.6], "oxygen_ticks": 0, "zero_oxy_ticks": 50, "hp": 3},
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, -1]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "20",
                                     "--scenario", sc2, "--inputs", inp, "--out", w.path("o2.jsonl"))
            self.assertEqual(code, 0, err)
            rows2 = read_jsonl(w.path("o2.jsonl"))
            self.assertEqual(events(rows2, "choke"), [])
            last_p = snapshots(rows2)[-1]["player"]
            self.assertEqual(last_p["zero_oxy_ticks"], 0)
            self.assertGreater(last_p["oxygen_ticks"], 0)

    def test_faint_clears_hold_and_writes_empty_inventory(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                "hold": ["ca_loc", "bong_sung"],
                "time_left_ticks": 1,
            }})
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--scenario", sc, "--inventory-out", inv, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            names = [e["name"] for e in events(rows)]
            self.assertEqual(names, ["choke", "faint", "gather_end"])
            end_ev = events(rows, "gather_end")[0]
            self.assertEqual(end_ev["data"]["reason"], "fainted")
            self.assertEqual(end_ev["data"]["inventory"], {"items": {}})
            self.assertEqual(rows[-1]["reason"], "fainted")
            self.assertEqual(snapshots(rows)[-1]["hold"], [])
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


class GatherSlice2Test(unittest.TestCase):
    def test_gather_node_tiebreak_regrow_and_surface_only(self):
        g = _tuning_gather()
        regrow_ticks = int(round(g["regrow_s"] * 60))
        with Workdir() as w:
            # Hai nút cùng khoảng cách -> chọn id nhỏ hơn (N2 trước N10)
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 0]},
                "nodes": [
                    {"id": "N10", "kind": "bong_sung", "pos": [21, 0]},
                    {"id": "N2", "kind": "bong_dien_dien", "pos": [19, 0]},
                ],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(regrow_ticks + 2),
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            ge = events(rows, "gather")
            self.assertEqual(len(ge), 1)
            self.assertEqual(ge[0]["data"]["node_id"], "N2")
            self.assertEqual(ge[0]["data"]["kind"], "bong_dien_dien")
            self.assertEqual(snapshots(rows)[-1]["hold"], ["bong_dien_dien"])
            regrown = events(rows, "node_regrown")
            self.assertEqual(len(regrown), 1)
            self.assertEqual(regrown[0]["data"]["node_id"], "N2")
            self.assertEqual(regrown[0]["tick"], 1 + regrow_ticks)

            # Dưới nước không hái được nút ở mặt nước
            sc_under = write_json(w.path("sc_under.json"), {"gather": {
                "player": {"pos": [12, 1.0]},
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
                "random_fish": False,
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc_under, "--inputs", inp, "--out", w.path("u.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(events(read_jsonl(w.path("u.jsonl")), "gather"), [])

    def test_gather_node_hold_full_keeps_node_ready(self):
        cap = int(_tuning_gather()["hold_capacity"])
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [12, 0]},
                "hold": ["ca_loc"] * cap,
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(len(events(rows, "hold_full")), 1)
            self.assertTrue(snapshots(rows)[-1]["nodes"][0]["ready"])

    def test_dock_has_priority_over_gather(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [2, 0]},
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [2, 0]}],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")

    def test_catch_fish_yield_cooldown_surface_and_hold_full(self):
        g = _tuning_gather()
        cap = int(g["hold_capacity"])
        cd = int(round(g["catch_cooldown_s"] * 60))
        with Workdir() as w:
            # Bắt ca_linh (yield=3), rồi bấm lại ngay trong cooldown -> bị chặn; hết cooldown bắt tiếp F2
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [15, 5]},
                "fish": [
                    {"id": "F1", "kind": "ca_linh", "pos": [15, 5]},
                    {"id": "F2", "kind": "ca_loc", "pos": [15.5, 5]},
                ],
            }})
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "catch": True},
                {"tick": 1, "catch": False},
                {"tick": 5, "catch": True},
                {"tick": 6, "catch": False},
                {"tick": cd, "catch": True},
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(cd + 2),
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            caught = events(rows, "fish_caught")
            self.assertEqual(len(caught), 2)
            self.assertEqual(caught[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "count": 3})
            self.assertEqual(caught[1]["data"], {"fish_id": "F2", "kind": "ca_loc", "count": 1})
            self.assertEqual(snapshots(rows)[-1]["hold"], ["ca_linh", "ca_linh", "ca_linh", "ca_loc"])
            self.assertEqual(snapshots(rows)[-1]["fish"], [])

            # Mặt nước không bắt được cá
            sc_surf = write_json(w.path("sc_surf.json"), {"gather": {
                "player": {"pos": [15, 0.5]},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [15, 1.0]}],
            }})
            inp_once = write_json(w.path("in1.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc_surf, "--inputs", inp_once, "--out", w.path("s.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(events(read_jsonl(w.path("s.jsonl")), "fish_caught"), [])

            # Giỏ còn 1 chỗ, bắt ca_linh (yield=3) -> lấy 1, không tràn giỏ, phát fish_caught + hold_full
            sc_part = write_json(w.path("sc_part.json"), {"gather": {
                "player": {"pos": [15, 5]},
                "hold": ["ca_loc"] * (cap - 1),
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}],
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc_part, "--inputs", inp_once, "--out", w.path("p.jsonl"))
            self.assertEqual(code, 0, err)
            rows_p = read_jsonl(w.path("p.jsonl"))
            self.assertEqual(events(rows_p, "fish_caught")[0]["data"]["count"], 1)
            self.assertEqual(len(events(rows_p, "hold_full")), 1)
            self.assertEqual(len(snapshots(rows_p)[-1]["hold"]), cap)


if __name__ == "__main__":
    unittest.main()
