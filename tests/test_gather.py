"""Khung test luật mode `gather` (hộp đen: chỉ chạy `headless_cmd`, đọc JSONL + file kho).

Hợp đồng: docs/contracts/README.md (mục 1 kho, 2.2 snapshot, 3.1 sự kiện gather) + docs/clarify.md.
Số liệu luôn đọc từ game.contract.json -> tuning.gather, không hard-code.

Test của luật CHƯA viết được đánh dấu @lat1 / @lat2 (bỏ qua). Làm xong lát nào thì XÓA decorator đó
trên các test tương ứng. Muốn xem chúng chạy (và đỏ) trước khi làm xong:
    CHONOI_PENDING=1 PYTHONPATH=tests:. python3 -m unittest tests.test_gather -v
Test có ghi [giả định #n] phụ thuộc câu clarify số n; PO chốt khác thì sửa test kèm lý do trong commit.
"""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

_RUN_PENDING = bool(os.environ.get("CHONOI_PENDING"))
lat1 = unittest.skipUnless(_RUN_PENDING, "TODO(nhóm, lát 1): oxy / ngạt / Máu / dive-surface")
lat2 = unittest.skipUnless(_RUN_PENDING, "TODO(nhóm, lát 2): hái / bắt cá / giỏ đầy")


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


G = tuning()["gather"]
TICK = tuning()["tick_hz"]
OXY_MAX = int(round(G["oxygen_max_s"] * TICK))
UNDER = [50, 10]   # xa bến, xa nút, xa cá mặc định
SURFACE = [50, 0]


def run_gather(scenario=None, inputs=None, ticks=1, seed=1):
    """Chạy gather; trả (rows, items_trong_file_kho_hoặc_None). Scenario là khối `gather`."""
    with Workdir() as w:
        args = ["--mode", "gather", "--seed", str(seed), "--ticks", str(ticks), "--out", w.path("o.jsonl"),
                "--inventory-out", w.path("inv.json")]
        if scenario is not None:
            args += ["--scenario", write_json(w.path("sc.json"), {"gather": scenario})]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        code, err = run_headless(*args)
        assert code == 0, err
        rows = read_jsonl(w.path("o.jsonl"))
        inv = None
        if os.path.exists(w.path("inv.json")):
            with open(w.path("inv.json"), encoding="utf-8") as f:
                inv = json.load(f)
        return rows, inv


def last(rows):
    return snapshots(rows)[-1]


def names(rows):
    return [e["name"] for e in events(rows)]


# ----------------------------------------------------------------------------- format JSONL (đã có khung)
class JsonlFormat(unittest.TestCase):
    def test_event_row_shape(self):
        rows, _ = run_gather({"time_left_ticks": 2}, ticks=5)
        evs = events(rows)
        self.assertTrue(evs)
        for e in evs:
            self.assertEqual(set(e), {"type", "tick", "phase", "name", "data"})
            self.assertEqual(e["phase"], "gather")

    def test_event_before_snapshot_same_tick(self):
        rows, _ = run_gather({"time_left_ticks": 1}, ticks=5)
        i_ev = next(i for i, r in enumerate(rows) if r["type"] == "event" and r["name"] == "gather_end")
        self.assertEqual(rows[i_ev + 1]["type"], "snapshot")
        self.assertEqual(rows[i_ev + 1]["tick"], rows[i_ev]["tick"])
        self.assertEqual(rows[i_ev + 1]["state"], "finished")

    def test_end_row_matches_gather_end(self):
        rows, inv = run_gather({"time_left_ticks": 1, "hold": ["ca_loc"]}, ticks=5)
        end = rows[-1]
        self.assertEqual(end["type"], "end")
        self.assertEqual(end["reason"], "time")
        self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], inv)

    def test_snapshot_every(self):
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "25", "--snapshot-every", "5",
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual([s["tick"] for s in snapshots(read_jsonl(w.path("o.jsonl")))], [0, 5, 10, 15, 20, 25])


# ----------------------------------------------------------------------------- kho (contract mục 1)
class Inventory(unittest.TestCase):
    def test_docked_writes_sorted_items(self):
        rows, inv = run_gather({"hold": ["bong_sung", "ca_loc", "bong_sung"]}, [{"tick": 0, "interact": True}])
        self.assertEqual(inv, {"items": {"bong_sung": 2, "ca_loc": 1}})
        self.assertEqual(list(inv["items"]), sorted(inv["items"]))

    def test_written_exactly_once_and_only_on_end(self):
        rows, inv = run_gather(ticks=3)
        self.assertIsNone(inv)
        self.assertEqual(rows[-1]["reason"], "tick_limit")

    def test_dock_checked_before_harvest(self):
        rows, _ = run_gather({"nodes": [{"id": "N1", "kind": "bong_sung", "pos": [3, 0]}]},
                             [{"tick": 0, "interact": True}])
        self.assertEqual(names(rows), ["gather_end"])
        self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")

    @lat1
    def test_fainted_writes_empty_inventory(self):
        sc = {"player": {"pos": UNDER, "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": G["choke_interval_ticks"] - 1},
              "hold": ["ca_loc", "bong_sung"]}
        rows, inv = run_gather(sc, ticks=5)
        self.assertEqual(inv, {"items": {}})
        end = events(rows, "gather_end")
        self.assertEqual(len(end), 1)
        self.assertEqual(end[0]["data"], {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual(rows[-1]["reason"], "fainted")


# ----------------------------------------------------------------------------- lát 1: oxy, ngạt, Máu
class Oxygen(unittest.TestCase):
    @lat1
    def test_underwater_drains_one_per_tick(self):
        rows, _ = run_gather({"player": {"pos": UNDER}}, ticks=10)
        self.assertEqual(last(rows)["player"]["oxygen_ticks"], OXY_MAX - 10)

    @lat1
    def test_surface_refills_and_clamps(self):
        rows, _ = run_gather({"player": {"pos": SURFACE, "oxygen_ticks": 100}}, ticks=1)
        self.assertEqual(last(rows)["player"]["oxygen_ticks"], 100 + G["oxygen_refill_per_tick"])
        rows, _ = run_gather({"player": {"pos": SURFACE, "oxygen_ticks": OXY_MAX - 1}}, ticks=1)
        self.assertEqual(last(rows)["player"]["oxygen_ticks"], OXY_MAX)

    @lat1
    def test_oxygen_empty_once(self):
        rows, _ = run_gather({"player": {"pos": UNDER, "oxygen_ticks": 1}}, ticks=10)
        ev = events(rows, "oxygen_empty")
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["tick"], 1)
        self.assertEqual(last(rows)["player"]["oxygen_ticks"], 0)

    @lat1
    def test_choke_every_interval(self):
        n = G["choke_interval_ticks"]
        rows, _ = run_gather({"player": {"pos": UNDER, "oxygen_ticks": 0}}, ticks=2 * n)
        ch = events(rows, "choke")
        self.assertEqual([e["tick"] for e in ch], [n, 2 * n])
        self.assertEqual(last(rows)["player"]["hp"], G["hp_max"] - 2)

    @lat1
    def test_surface_resets_choke_counter(self):
        # bơi từ d=1 lên mặt nước mất ~10 tick < 30 tick còn lại trước khi ngạt
        sc = {"player": {"pos": [50, 1], "oxygen_ticks": 0, "zero_oxy_ticks": 30}}
        rows, _ = run_gather(sc, [{"tick": 0, "move": [0, -1]}], ticks=2 * G["choke_interval_ticks"])
        self.assertEqual(events(rows, "choke"), [])
        self.assertTrue(last(rows)["player"]["at_surface"])
        self.assertEqual(last(rows)["player"]["zero_oxy_ticks"], 0)

    @lat1
    def test_faint_order(self):
        sc = {"player": {"pos": UNDER, "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": G["choke_interval_ticks"] - 1}}
        rows, _ = run_gather(sc, ticks=5)
        self.assertEqual(names(rows)[-2:], ["faint", "gather_end"])
        self.assertEqual(last(rows)["state"], "finished")


class DiveSurface(unittest.TestCase):
    @lat1
    def test_dive_once_when_crossing_down(self):
        rows, _ = run_gather({"player": {"pos": [50, 0]}}, [{"tick": 0, "move": [0, 1]}], ticks=60)
        self.assertEqual(len(events(rows, "dive")), 1)
        self.assertEqual(events(rows, "surface"), [])
        self.assertFalse(last(rows)["player"]["at_surface"])

    @lat1
    def test_surface_once_when_crossing_up(self):
        rows, _ = run_gather({"player": {"pos": [50, 2]}}, [{"tick": 0, "move": [0, -1]}], ticks=60)
        ev = events(rows, "surface")
        self.assertEqual(len(ev), 1)
        self.assertIn("pos", ev[0]["data"])
        self.assertTrue(last(rows)["player"]["at_surface"])


# ----------------------------------------------------------------------------- lát 2: hái, bắt cá, giỏ
class Harvest(unittest.TestCase):
    NODE = {"id": "N1", "kind": "bong_sung", "pos": [20, 0]}

    @lat2
    def test_harvest_ready_node(self):
        rows, _ = run_gather({"player": {"pos": [20, 0]}, "nodes": [self.NODE]}, [{"tick": 0, "interact": True}])
        self.assertEqual(len(events(rows, "gather")), 1)
        s = last(rows)
        self.assertEqual(s["hold"], ["bong_sung"] * G["node_yield"])
        self.assertFalse(s["nodes"][0]["ready"])
        self.assertEqual(s["nodes"][0]["regrow_ticks"], int(round(G["regrow_s"] * TICK)))

    @lat2
    def test_harvest_tie_picks_smaller_id(self):
        nodes = [{"id": "N2", "kind": "bong_sung", "pos": [19, 0]}, {"id": "N1", "kind": "bong_dien_dien", "pos": [21, 0]}]
        rows, _ = run_gather({"player": {"pos": [20, 0]}, "nodes": nodes}, [{"tick": 0, "interact": True}])
        self.assertEqual(last(rows)["hold"], ["bong_dien_dien"] * G["node_yield"])

    @lat2
    def test_no_harvest_underwater_or_out_of_radius(self):
        for pos in ([20, 3], [20 + G["interact_radius"] + 1, 0]):
            rows, _ = run_gather({"player": {"pos": pos}, "nodes": [self.NODE]}, [{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "gather"), [], pos)
            self.assertEqual(last(rows)["hold"], [], pos)

    @lat2
    def test_no_harvest_while_regrowing(self):
        node = dict(self.NODE, regrow_ticks=100)
        rows, _ = run_gather({"player": {"pos": [20, 0]}, "nodes": [node]}, [{"tick": 0, "interact": True}])
        self.assertEqual(events(rows, "gather"), [])

    @lat2
    def test_hold_full_on_harvest(self):
        sc = {"player": {"pos": [20, 0]}, "nodes": [self.NODE], "hold": ["ca_loc"] * G["hold_capacity"]}
        rows, _ = run_gather(sc, [{"tick": 0, "interact": True}])
        self.assertEqual(len(events(rows, "hold_full")), 1)
        self.assertEqual(events(rows, "gather"), [])
        self.assertTrue(last(rows)["nodes"][0]["ready"])

    def test_node_regrown_event(self):  # khung đã có
        node = dict(self.NODE, regrow_ticks=2)
        rows, _ = run_gather({"nodes": [node]}, ticks=5)
        ev = events(rows, "node_regrown")
        self.assertEqual([(e["tick"], e["data"]) for e in ev], [(2, {"node_id": "N1"})])


class Catch(unittest.TestCase):
    FISH = {"id": "F1", "kind": "ca_linh", "pos": [30, 10]}

    @lat2
    def test_catch_adds_yield_and_cooldown(self):
        rows, _ = run_gather({"player": {"pos": [30, 10]}, "fish": [self.FISH]}, [{"tick": 0, "catch": True}])
        self.assertEqual(len(events(rows, "fish_caught")), 1)
        s = last(rows)
        self.assertEqual(s["hold"], ["ca_linh"] * G["fish_yield"]["ca_linh"])
        self.assertEqual(s["player"]["catch_cd_ticks"], int(round(G["catch_cooldown_s"] * TICK)))

    @lat2
    def test_caught_fish_removed(self):  # [giả định #7]
        rows, _ = run_gather({"player": {"pos": [30, 10]}, "fish": [self.FISH]}, [{"tick": 0, "catch": True}])
        self.assertEqual(last(rows)["fish"], [])

    @lat2
    def test_no_catch_on_cooldown_or_surface(self):
        cases = [{"player": {"pos": [30, 10], "catch_cd_ticks": 10}, "fish": [self.FISH]},
                 {"player": {"pos": [30, 0]}, "fish": [dict(self.FISH, pos=[30, 1])]}]
        for sc in cases:
            rows, _ = run_gather(sc, [{"tick": 0, "catch": True}])
            self.assertEqual(events(rows, "fish_caught"), [], sc)

    @lat2
    def test_hold_full_when_batch_does_not_fit(self):  # [giả định #5]
        cap, y = G["hold_capacity"], G["fish_yield"]["ca_linh"]
        sc = {"player": {"pos": [30, 10]}, "fish": [self.FISH], "hold": ["ca_loc"] * (cap - y + 1)}
        rows, _ = run_gather(sc, [{"tick": 0, "catch": True}])
        self.assertEqual(len(events(rows, "hold_full")), 1)
        self.assertEqual(last(rows)["hold_count"], cap - y + 1)
        self.assertEqual(len(last(rows)["fish"]), 1)

    @lat2
    def test_hold_keeps_pick_order(self):
        sc = {"player": {"pos": [30, 10]}, "fish": [self.FISH], "hold": ["bong_sung"]}
        rows, _ = run_gather(sc, [{"tick": 0, "catch": True}])
        self.assertEqual(last(rows)["hold"], ["bong_sung"] + ["ca_linh"] * G["fish_yield"]["ca_linh"])


class Determinism(unittest.TestCase):
    def test_same_seed_same_bytes_with_actions(self):
        inp = [{"tick": 0, "move": [1, 1]}, {"tick": 30, "catch": True}, {"tick": 31, "catch": False},
               {"tick": 60, "move": [-1, -1]}, {"tick": 200, "interact": True}]
        a, _ = run_gather(inputs=inp, ticks=400, seed=3)
        b, _ = run_gather(inputs=inp, ticks=400, seed=3)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
