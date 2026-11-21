"""Unit & black-box tests cho Lát 2 Gather (hái nút, bắt cá, cập bến, xuất kho)."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


class GatherHarvestAndCatchTests(unittest.TestCase):
    def test_harvest_nearest_node_tiebreak_regrow_and_lifo(self):
        g = tuning_gather()
        regrow_ticks = int(round(g["regrow_s"] * 60))
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "hold": ["ca_loc"],
                "player": {"pos": [20, 0]},
                "nodes": [
                    {"id": "N10", "kind": "bong_sung", "pos": [21, 0]},
                    {"id": "N2", "kind": "bong_dien_dien", "pos": [21, 0]},
                ],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1",
                                     "--ticks", str(regrow_ticks + 2),
                                     "--scenario", sc, "--inputs", inp,
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            g_ev = events(rows, "gather")
            self.assertEqual(len(g_ev), 1)
            self.assertEqual(g_ev[0]["data"]["node_id"], "N2")
            self.assertEqual(g_ev[0]["data"]["kind"], "bong_dien_dien")
            regrown = events(rows, "node_regrown")
            self.assertEqual(len(regrown), 1)
            self.assertEqual(regrown[0]["data"]["node_id"], "N2")
            self.assertEqual(regrown[0]["tick"], 1 + regrow_ticks)
            last_snap = snapshots(rows)[-1]
            self.assertEqual(last_snap["hold"], ["ca_loc", "bong_dien_dien"])

    def test_harvest_blocked_underwater_and_dock_priority(self):
        with Workdir() as w:
            # Dưới nước không hái được nút dù trong bán kính
            sc_under = write_json(w.path("sc1.json"), {"gather": {
                "player": {"pos": [12, 1.0]},
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc_under, "--inputs", inp,
                                     "--out", w.path("o1.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(events(read_jsonl(w.path("o1.jsonl")), "gather"), [])

            # Ở bến: ưu tiên cập bến hơn hái nút
            sc_dock = write_json(w.path("sc2.json"), {"gather": {
                "player": {"pos": [2, 0]},
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [2, 0]}],
                "random_fish": False,
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc_dock, "--inputs", inp,
                                     "--out", w.path("o2.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o2.jsonl"))
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")

    def test_catch_fish_underwater_cooldown_and_hold_full(self):
        g = tuning_gather()
        cap = g["hold_capacity"]
        cd = int(round(g["catch_cooldown_s"] * 60))
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "hold": ["bong_sung"] * (cap - 2),
                "player": {"pos": [20, 10]},
                "random_fish": False,
                "fish": [
                    {"id": "F10", "kind": "ca_loc", "pos": [21, 10]},
                    {"id": "F2", "kind": "ca_linh", "pos": [21, 10]},
                    {"id": "F3", "kind": "ca_loc", "pos": [20.5, 10]},
                ],
            }})
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "catch": True},
                {"tick": 1, "catch": False},
                {"tick": 2, "catch": True},
                {"tick": cd + 1, "catch": False},
                {"tick": cd + 2, "catch": True},
                {"tick": 2 * cd + 2, "catch": False},
                {"tick": 2 * cd + 3, "catch": True},
            ))
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1",
                                     "--ticks", str(2 * cd + 10),
                                     "--scenario", sc, "--inputs", inp,
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            caught = events(rows, "fish_caught")
            self.assertEqual(
                [(e["tick"], e["data"]) for e in caught],
                [(1, {"fish_id": "F3", "kind": "ca_loc", "yield": 1})],
            )
            # Còn một ô nhưng F2 cần toàn bộ yield. Không thử F10 dù nó vừa.
            failed_catch = {"action": "catch", "fish_id": "F2",
                            "required": g["fish_yield"]["ca_linh"], "free": 1}
            self.assertEqual(
                [(e["tick"], e["data"]) for e in events(rows, "hold_full")],
                [(cd + 3, failed_catch), (2 * cd + 4, failed_catch)],
            )
            last_snap = snapshots(rows)[-1]
            self.assertEqual(last_snap["hold_count"], cap - 1)
            self.assertEqual(last_snap["player"]["catch_cd_ticks"], 0)
            self.assertEqual([f["id"] for f in last_snap["fish"]], ["F2", "F10"])

            # Không bắt cá khi ở mặt nước
            sc_surf = write_json(w.path("sc_s.json"), {"gather": {
                "player": {"pos": [20, 0]},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20, 1.0]}],
            }})
            inp_s = write_json(w.path("in_s.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc_surf, "--inputs", inp_s,
                                     "--out", w.path("o_s.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(events(read_jsonl(w.path("o_s.jsonl")), "fish_caught"), [])

            # Hái + bắt cá rồi cập bến xuất kho
            sc_inv = write_json(w.path("sc_i.json"), {"gather": {
                "player": {"pos": [2, 0]},
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [2, 0]}],
                "hold": ["ca_loc", "ca_linh"],
                "random_fish": False,
            }})
            inp_inv = write_json(w.path("in_i.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc_inv, "--inputs", inp_inv,
                                     "--inventory-out", inv, "--out", w.path("o_i.jsonl"))
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"ca_linh": 1, "ca_loc": 1}})


if __name__ == "__main__":
    unittest.main()
