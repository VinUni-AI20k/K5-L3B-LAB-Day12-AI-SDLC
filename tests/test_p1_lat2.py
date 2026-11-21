"""Test hộp đen Lát 2 (haiquanng): hái nút, bắt cá, cập bến, ghi kho — AC-P1-04, 05, 06.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p1_lat2 -v
Mọi số liệu đọc từ game.contract.json; chỉ chạy headless và đọc JSONL / file kho.
"""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


G = tuning()["gather"]
TICK = tuning()["tick_hz"]
REGROW = int(round(G["regrow_s"] * TICK))
CATCH_CD = int(round(G["catch_cooldown_s"] * TICK))
FAR = [80, 0]  # mặt nước, xa bến


def run_gather(w, scenario, input_frames, ticks, inventory_out=None):
    sc = write_json(w.path("sc.json"), {"gather": scenario})
    inp = write_json(w.path("in.json"), frames(*input_frames))
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc, "--inputs", inp,
            "--out", w.path("o.jsonl"), "--snapshot-every", "1"]
    if inventory_out:
        args += ["--inventory-out", inventory_out]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


def press(tick, button="interact"):
    """Cạnh lên ở `tick`, nhả ở tick sau."""
    return [{"tick": tick, button: True}, {"tick": tick + 1, button: False}]


def node(nid, kind, pos, regrow=0):
    return {"id": nid, "kind": kind, "pos": pos, "regrow_ticks": regrow}


def fish(fid, kind, pos):
    return {"id": fid, "kind": kind, "pos": pos}


class Gather(unittest.TestCase):
    """AC-P1-04: hái chỉ ở mặt nước, đúng mép vẫn hái, hold_full không đổi nút, mọc lại sau regrow_s."""

    def test_gather_at_exact_radius(self):
        with Workdir() as w:
            pos = [FAR[0] + G["interact_radius"], 0]
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": [node("N1", "bong_sung", pos)], "fish": []},
                              press(0), 2)
            ev = events(rows, "gather")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["tick"], 1)
            self.assertEqual(ev[0]["data"], {"node_id": "N1", "kind": "bong_sung", "count": G["node_yield"]})
            snap = [s for s in snapshots(rows) if s["tick"] == 1][0]
            self.assertEqual(snap["hold"], ["bong_sung"] * G["node_yield"])
            self.assertEqual(snap["nodes"][0]["ready"], False)
            self.assertEqual(snap["nodes"][0]["regrow_ticks"], REGROW)

    def test_no_gather_underwater(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 1.5]}, "nodes": [node("N1", "bong_sung", [50, 0])],
                                  "fish": []}, press(0), 2)
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(snapshots(rows)[-1]["hold"], [])

    def test_out_of_radius_nothing(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": [node("N1", "bong_sung", [FAR[0] + 2.01, 0])],
                                  "fish": []}, press(0), 2)
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(events(rows, "hold_full"), [])

    def test_nearest_then_smallest_id(self):
        with Workdir() as w:
            nodes = [node("N2", "bong_sung", [FAR[0] - 1, 0]), node("N1", "bong_dien_dien", [FAR[0] + 1, 0]),
                     node("N3", "bong_sung", [FAR[0] + 0.5, 0])]
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": nodes, "fish": []}, press(0), 2)
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N3")
        with Workdir() as w:
            nodes = [node("N2", "bong_sung", [FAR[0] - 1, 0]), node("N1", "bong_dien_dien", [FAR[0] + 1, 0])]
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": nodes, "fish": []}, press(0), 2)
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N1")

    def test_skip_not_ready_node(self):
        with Workdir() as w:
            nodes = [node("N1", "bong_sung", FAR, regrow=500), node("N2", "bong_dien_dien", [FAR[0] + 1, 0])]
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": nodes, "fish": []}, press(0), 2)
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")

    def test_hold_full_keeps_node(self):
        with Workdir() as w:
            full = ["ca_loc"] * G["hold_capacity"]
            rows = run_gather(w, {"player": {"pos": FAR}, "hold": full,
                                  "nodes": [node("N1", "bong_sung", FAR)], "fish": []}, press(0), 2)
            self.assertEqual(events(rows, "gather"), [])
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1)
            self.assertEqual(hf[0]["data"], {"action": "gather", "node_id": "N1",
                                             "required": G["node_yield"], "free": 0})
            last = snapshots(rows)[-1]
            self.assertEqual(last["hold"], full)
            self.assertEqual(last["nodes"][0]["ready"], True)
            self.assertEqual(last["nodes"][0]["regrow_ticks"], 0)

    def test_regrow_after_regrow_s(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": [node("N1", "bong_sung", FAR)], "fish": []},
                              press(0), REGROW + 3)
            g = events(rows, "gather")[0]["tick"]
            rg = events(rows, "node_regrown")
            self.assertEqual(len(rg), 1)
            self.assertEqual(rg[0]["tick"] - g, REGROW)
            self.assertEqual(rg[0]["data"], {"node_id": "N1"})

    def test_cannot_regather_while_regrowing(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": [node("N1", "bong_sung", FAR)], "fish": []},
                              press(0) + press(5), 8)
            self.assertEqual(len(events(rows, "gather")), 1)
            self.assertEqual(snapshots(rows)[-1]["hold"], ["bong_sung"])


class Catch(unittest.TestCase):
    """AC-P1-05: bắt cá chỉ dưới nước, đủ yield, cooldown, hold_full giữ đàn."""

    def test_catch_yield_and_cooldown(self):
        for kind in ("ca_linh", "ca_loc"):
            with Workdir() as w:
                rows = run_gather(w, {"player": {"pos": [50, 10]}, "nodes": [],
                                      "fish": [fish("F1", kind, [50, 11])]}, press(0, "catch"), 2)
                ev = events(rows, "fish_caught")
                self.assertEqual(len(ev), 1, kind)
                self.assertEqual(ev[0]["data"], {"fish_id": "F1", "kind": kind, "count": G["fish_yield"][kind]})
                snap = [s for s in snapshots(rows) if s["tick"] == 1][0]
                self.assertEqual(snap["hold"], [kind] * G["fish_yield"][kind])
                self.assertEqual(snap["fish"], [])
                self.assertEqual(snap["player"]["catch_cd_ticks"], CATCH_CD)

    def test_no_catch_at_surface(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 0]}, "nodes": [],
                                  "fish": [fish("F1", "ca_loc", [50, 1])]}, press(0, "catch"), 2)
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(len(snapshots(rows)[-1]["fish"]), 1)

    def test_cooldown_blocks_then_allows(self):
        fs = [fish("F1", "ca_loc", [50, 10]), fish("F2", "ca_loc", [50, 11])]
        with Workdir() as w:  # bấm lại ở bước CATCH_CD - 1: còn hồi chiêu
            rows = run_gather(w, {"player": {"pos": [50, 10]}, "nodes": [], "fish": fs},
                              press(0, "catch") + press(CATCH_CD - 1, "catch"), CATCH_CD + 2)
            self.assertEqual(len(events(rows, "fish_caught")), 1)
        with Workdir() as w:  # bấm ở bước CATCH_CD: hết hồi chiêu
            rows = run_gather(w, {"player": {"pos": [50, 10]}, "nodes": [], "fish": fs},
                              press(0, "catch") + press(CATCH_CD, "catch"), CATCH_CD + 2)
            ev = events(rows, "fish_caught")
            self.assertEqual([e["data"]["fish_id"] for e in ev], ["F1", "F2"])
            self.assertEqual(ev[1]["tick"] - ev[0]["tick"], CATCH_CD)

    def test_hold_full_keeps_fish_no_cooldown(self):
        with Workdir() as w:
            hold = ["bong_sung"] * (G["hold_capacity"] - 2)
            rows = run_gather(w, {"player": {"pos": [50, 10]}, "hold": hold, "nodes": [],
                                  "fish": [fish("F1", "ca_linh", [50, 10])]}, press(0, "catch"), 2)
            self.assertEqual(events(rows, "fish_caught"), [])
            hf = events(rows, "hold_full")
            self.assertEqual(hf[0]["data"], {"action": "catch", "fish_id": "F1",
                                             "required": G["fish_yield"]["ca_linh"], "free": 2})
            last = snapshots(rows)[-1]
            self.assertEqual(last["hold"], hold)
            self.assertEqual([f["id"] for f in last["fish"]], ["F1"])
            self.assertEqual(last["player"]["catch_cd_ticks"], 0)

    def test_exact_radius_and_tie_by_id(self):
        with Workdir() as w:
            r = G["catch_radius"]
            fs = [fish("F2", "ca_loc", [50 - r, 10]), fish("F1", "ca_linh", [50 + r, 10])]
            rows = run_gather(w, {"player": {"pos": [50, 10]}, "nodes": [], "fish": fs}, press(0, "catch"), 2)
            self.assertEqual(events(rows, "fish_caught")[0]["data"]["fish_id"], "F1")
        with Workdir() as w:
            fs = [fish("F1", "ca_loc", [50, 12.01])]
            rows = run_gather(w, {"player": {"pos": [50, 10]}, "nodes": [], "fish": fs}, press(0, "catch"), 2)
            self.assertEqual(events(rows, "fish_caught"), [])


class DockAndInventory(unittest.TestCase):
    """AC-P1-06 (phía gather): bến xét trước, bước cuối vẫn vào kho, chạm --ticks thì không ghi kho."""

    def test_dock_at_exact_radius_writes_hold(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            pos = [G["dock_pos"][0] + G["dock_radius"], G["dock_pos"][1]]
            rows = run_gather(w, {"player": {"pos": pos}, "hold": ["ca_loc", "bong_sung"],
                                  "nodes": [node("N1", "bong_sung", pos)], "fish": []}, press(0), 5, inv)
            self.assertEqual(events(rows, "gather"), [])  # bến xét trước hái
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 1, "ca_loc": 1}})

    def test_gather_on_last_tick_counts(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            rows = run_gather(w, {"player": {"pos": FAR}, "time_left_ticks": 1,
                                  "nodes": [node("N1", "bong_sung", FAR)], "fish": []}, press(0), 5, inv)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "time")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 1}})

    def test_catch_on_last_tick_counts(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            run_gather(w, {"player": {"pos": [50, 10]}, "time_left_ticks": 1, "nodes": [],
                           "fish": [fish("F1", "ca_linh", [50, 10])]}, press(0, "catch"), 5, inv)
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"ca_linh": 3}})

    def test_tick_limit_after_gather_no_inventory(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": [node("N1", "bong_sung", FAR)], "fish": []},
                              press(0), 3, inv)
            self.assertEqual(len(events(rows, "gather")), 1)
            self.assertFalse(os.path.exists(inv))
            self.assertEqual(rows[-1]["reason"], "tick_limit")

    def test_full_run_gather_catch_dock_then_quan(self):
        """Hái ở mặt nước, lặn bắt cá, nổi lên rồi về bến; quán đọc đúng kho (smoke hai tiến trình)."""
        with Workdir() as w:
            inv = w.path("inv.json")
            x0 = 10  # ngoài bến
            nodes = [node("N1", "bong_sung", [x0, 0])]
            fs = [fish("F1", "ca_loc", [x0, 3])]
            speed = G["swim_speed"]
            down = int(3 / speed * TICK)  # ~3 đơn vị độ sâu
            back = int((x0 + 1) / speed * TICK) + G["ramp_max_ticks"] + 10  # đủ để chạm mép x = 0 (trong bến)
            fr = press(0)  # hái N1 ở mặt nước
            fr += [{"tick": 5, "move": [0, 1]}, {"tick": 5 + down, "move": [0, 0]}]
            t = 5 + down + 10
            fr += press(t, "catch")  # dưới nước, F1 trong catch_radius
            up = t + 2
            fr += [{"tick": up, "move": [0, -1]}, {"tick": up + down + 30, "move": [-1, 0]},
                   {"tick": up + down + 30 + back, "move": [0, 0]}]
            fr += press(up + down + 30 + back + 5)
            rows = run_gather(w, {"player": {"pos": [x0, 0]}, "nodes": nodes, "fish": fs}, fr, 900, inv)
            self.assertEqual(len(events(rows, "gather")), 1)
            self.assertEqual(len(events(rows, "fish_caught")), 1)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 1, "ca_loc": 1}})
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "0", "--inventory", inv,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], {"bong_sung": 1, "ca_loc": 1})


if __name__ == "__main__":
    unittest.main()
