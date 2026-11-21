"""Lát 2 (gather): hái nút, bắt cá, cập bến, file kho. Hộp đen qua headless_cmd, theo PRD-0 mục F + G."""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

FULL = [{"id": f"I{i}", "kind": "ca_loc", "fresh": 100} for i in range(1, 13)]


def run(w, scenario, inputs, ticks, inv_out=None):
    args = ["--mode", "gather", "--seed", "1", "--scenario", write_json(w.path("s.json"), {"gather": scenario}),
            "--inputs", write_json(w.path("i.json"), inputs), "--ticks", str(ticks), "--out", w.path("o.jsonl")]
    if inv_out:
        args += ["--inventory-out", inv_out]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


def press(key, *ticks):
    """Ấn rồi nhả `key` ở mỗi tick cho trước."""
    return frames(*[f for t in ticks for f in ({"tick": t, key: True}, {"tick": t + 1, key: False})])


class Harvest(unittest.TestCase):
    def test_edge_radius_and_tie_by_id(self):
        nodes = [{"id": "N2", "kind": "bong_sung", "pos": [22, 0]}, {"id": "N1", "kind": "bong_dien_dien", "pos": [18, 0]}]
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [20, 0]}, "nodes": nodes, "fish": []}, press("interact", 0, 2), 4)
            got = [e["data"]["node_id"] for e in events(rows, "gather")]
            self.assertEqual(got, ["N1", "N2"])
            self.assertEqual([it["kind"] for it in snapshots(rows)[-1]["hold"]], ["bong_dien_dien", "bong_sung"])
            regrow = {n["id"]: n["regrow_ticks"] for n in snapshots(rows)[-1]["nodes"]}
            self.assertGreater(regrow["N1"], 0)

    def test_hold_full_keeps_node(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [20, 0]}, "hold": FULL, "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}],
                           "fish": []}, press("interact", 0), 2)
            self.assertEqual([e["data"] for e in events(rows, "hold_full")],
                             [{"action": "gather", "node_id": "N1", "required": 1, "free": 0}])
            self.assertTrue(snapshots(rows)[-1]["nodes"][0]["ready"])

    def test_no_harvest_under_water(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [20, 1]}, "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
                           "fish": []}, press("interact", 0), 2)
            self.assertEqual(events(rows, "gather"), [])


class Catch(unittest.TestCase):
    FISH = [{"id": "F5", "kind": "ca_loc", "pos": [15, 6]}, {"id": "F1", "kind": "ca_linh", "pos": [15, 4]}]

    def test_tie_by_id_and_cooldown(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [15, 5]}, "nodes": [], "fish": self.FISH, "random_fish": False},
                       press("catch", 0, 2, 29, 31), 40)
            caught = [(e["tick"], e["data"]) for e in events(rows, "fish_caught")]
            # F1 ở tick 1; ấn ở tick 2 và 29 còn hồi chiêu (30 tick); ấn ở 31 bắt F5
            self.assertEqual(caught, [(1, {"fish_id": "F1", "kind": "ca_linh", "yield": 3}),
                                      (32, {"fish_id": "F5", "kind": "ca_loc", "yield": 1})])

    def test_no_catch_at_surface(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [15, 0]}, "nodes": [], "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 1]}]},
                       press("catch", 0), 2)
            self.assertEqual(events(rows, "fish_caught") + events(rows, "hold_full"), [])

    def test_hold_full_no_cooldown_no_other_fish(self):
        with Workdir() as w:
            hold10 = [{"id": f"I{i}", "kind": "ca_loc", "fresh": 100} for i in range(1, 11)]
            rows = run(w, {"player": {"pos": [15, 5]}, "hold": hold10, "nodes": [],
                           "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}, {"id": "F2", "kind": "ca_loc", "pos": [15, 6]}]},
                       press("catch", 0, 2), 4)
            full = events(rows, "hold_full")
            self.assertEqual([e["tick"] for e in full], [1, 3])  # ấn lại ngay vẫn xét -> không có hồi chiêu
            self.assertEqual(full[0]["data"], {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
            self.assertEqual(events(rows, "fish_caught"), [])


class DockInventory(unittest.TestCase):
    def test_dock_writes_hold_as_inventory(self):
        with Workdir() as w:
            inv = w.path("kho.json")
            hold = [
                {"id": "I1", "kind": "ca_loc", "fresh": 100},
                {"id": "I2", "kind": "bong_sung", "fresh": 100},
                {"id": "I3", "kind": "bong_sung", "fresh": 100},
            ]
            rows = run(w, {"hold": hold}, frames({"tick": 0, "interact": True}), 1, inv)
            end = events(rows, "gather_end")[0]["data"]
            self.assertEqual(end["reason"], "docked")
            expected = {"items": [
                {"id": "I1", "kind": "ca_loc", "fresh": 99.991667},
                {"id": "I2", "kind": "bong_sung", "fresh": 99.991667},
                {"id": "I3", "kind": "bong_sung", "fresh": 99.991667},
            ]}
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), expected)
            self.assertEqual(end["inventory"], expected)

    def test_tick_limit_writes_no_inventory(self):
        with Workdir() as w:
            inv = w.path("kho.json")
            run(w, {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}, frames(), 5, inv)
            self.assertFalse(os.path.exists(inv))


if __name__ == "__main__":
    unittest.main()
