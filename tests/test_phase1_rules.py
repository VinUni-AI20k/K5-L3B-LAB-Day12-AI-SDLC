"""Kiểm tra đầy đủ luật Phase 1 (PRD-0 mục D, E, F, G) cho Gather, Quán và 6 kịch bản Bếp."""

import json
import os
import tempfile
import unittest

from helpers import events, read_jsonl, run_headless, snapshots, write_json

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session


def _inp(move=(0.0, 0.0), interact=False, catch=False):
    edges = set()
    if interact:
        edges.add("interact")
    if catch:
        edges.add("catch")
    return InputState(move, set(edges), edges)


class GatherRulesTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_dive_surface_oxygen_choke_and_faint_lifo(self):
        with tempfile.TemporaryDirectory() as d:
            scen = {
                "gather": {
                    "player": {"pos": [10, 0.5], "oxygen_ticks": 2, "hp": 1},
                    "hold": ["ca_loc", "bong_sung", "ca_linh"],
                    "nodes": [],
                    "fish": [],
                    "random_fish": False,
                }
            }
            inp = {
                "frames": [
                    {"tick": 0, "move": [0, 1]},
                    {"tick": 1, "move": [0, 0]},
                ]
            }
            sp = write_json(os.path.join(d, "s.json"), scen)
            ip = write_json(os.path.join(d, "i.json"), inp)
            out = os.path.join(d, "out.jsonl")
            inv = os.path.join(d, "inv.json")
            rc, err = run_headless(
                "--mode", "gather", "--seed", "1", "--scenario", sp, "--inputs", ip,
                "--ticks", "100", "--out", out, "--inventory-out", inv,
            )
            self.assertEqual(rc, 0, err)
            with open(out, encoding="utf-8") as f:
                rows = [json.loads(line) for line in f]
            ev_names = [(r["tick"], r["name"]) for r in rows if r["type"] == "event"]
            self.assertIn((1, "dive"), ev_names)
            self.assertIn((2, "oxygen_empty"), ev_names)
            self.assertIn((61, "choke"), ev_names)
            faint_ev = next(r for r in rows if r.get("name") == "faint")
            self.assertEqual(faint_ev["tick"], 61)
            self.assertEqual(faint_ev["data"]["lost"], ["ca_linh", "bong_sung", "ca_loc"])
            end_row = rows[-1]
            self.assertEqual(end_row["type"], "end")
            self.assertEqual(end_row["reason"], "fainted")
            self.assertEqual(end_row["ticks"], 61)
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})

    def test_surface_right_before_choke_prevents_choke(self):
        scen = {
            "player": {"pos": [10, 0.51], "vel": [0, -4.0], "oxygen_ticks": 0, "hp": 3, "zero_oxy_ticks": 59},
            "nodes": [],
            "fish": [],
            "random_fish": False,
        }
        sess = Session("gather", self.tuning, scen, 1)
        evs = sess.step(_inp(move=(0.0, -1.0)))
        names = [e["name"] for e in evs]
        self.assertIn("surface", names)
        self.assertNotIn("choke", names)
        self.assertEqual(sess.sim.hp, 3)
        self.assertEqual(sess.sim.zero_oxy_ticks, 0)
        self.assertEqual(sess.sim.oxygen_ticks, 6)

    def test_gather_node_tiebreak_regrow_and_hold_full(self):
        scen = {
            "player": {"pos": [20, 0]},
            "nodes": [
                {"id": "N2", "kind": "bong_sung", "pos": [21, 0]},
                {"id": "N10", "kind": "bong_dien_dien", "pos": [21, 0]},
            ],
            "fish": [],
            "random_fish": False,
        }
        sess = Session("gather", self.tuning, scen, 1)
        evs = sess.step(_inp(interact=True))
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["name"], "gather")
        self.assertEqual(evs[0]["data"], {"node_id": "N2", "kind": "bong_sung", "amount": 1})
        self.assertEqual(sess.sim.hold, ["bong_sung"])

        regrow_ticks = int(round(self.tuning["gather"]["regrow_s"] * 60))
        for _ in range(regrow_ticks - 1):
            sess.step(_inp())
        evs2 = sess.step(_inp(interact=True))
        self.assertEqual([e["name"] for e in evs2], ["node_regrown", "gather"])
        self.assertEqual(evs2[1]["data"]["node_id"], "N2")

        sess.sim.hold = ["ca_loc"] * self.tuning["gather"]["hold_capacity"]
        evs3 = sess.step(_inp(interact=True))
        self.assertEqual(len(evs3), 1)
        self.assertEqual(evs3[0]["name"], "hold_full")
        self.assertEqual(evs3[0]["data"], {"action": "gather", "node_id": "N10", "required": 1, "free": 0})

    def test_catch_fish_cooldown_and_hold_full(self):
        scen = {
            "player": {"pos": [15, 5]},
            "hold": ["ca_loc"] * 10,
            "nodes": [],
            "fish": [
                {"id": "F1", "kind": "ca_linh", "pos": [15, 5]},
                {"id": "F2", "kind": "ca_loc", "pos": [16, 5]},
            ],
            "random_fish": False,
        }
        sess = Session("gather", self.tuning, scen, 1)
        evs = sess.step(_inp(catch=True))
        self.assertEqual(evs[0]["name"], "hold_full")
        self.assertEqual(evs[0]["data"], {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
        self.assertEqual(sess.sim.catch_cd_ticks, 0)
        self.assertEqual(len(sess.sim.fish), 2)

        sess.sim.hold = ["ca_loc"] * 9
        evs2 = sess.step(_inp(catch=True))
        self.assertEqual(evs2[0]["name"], "fish_caught")
        self.assertEqual(evs2[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "yield": 3})
        self.assertEqual(sess.sim.catch_cd_ticks, 30)
        self.assertEqual(len(sess.sim.fish), 1)

        evs3 = sess.step(_inp(catch=True))
        self.assertEqual(evs3, [])


class QuanRulesTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_full_customer_cook_serve_tip_and_closing(self):
        scen = {
            "player": {"pos": [2, 8]},
            "stock": {"ca_loc": 2},
            "random_customers": False,
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"},
            ],
        }
        sess = Session("quan", self.tuning, scen, 1)
        evs = sess.step(_inp(interact=True))
        self.assertEqual([e["name"] for e in evs], ["cook_started"])
        self.assertEqual(evs[0]["data"]["items"], ["ca_loc"])
        self.assertEqual(sess.sim.stock, {"ca_loc": 1})

        for _ in range(359):
            self.assertEqual(sess.step(_inp()), [])
        evs_ready = sess.step(_inp())
        self.assertEqual([e["name"] for e in evs_ready], ["dish_ready"])
        self.assertEqual(sess.sim.stoves[0]["ready_ticks"], 0)

        evs_pick = sess.step(_inp(interact=True))
        self.assertEqual([e["name"] for e in evs_pick], ["dish_picked"])
        self.assertEqual(sess.sim.hand["order_id"], "C1")

        sess.sim.pos = [9.0, 2.0]
        evs_serve = sess.step(_inp(interact=True))
        self.assertEqual([e["name"] for e in evs_serve], ["served"])
        self.assertEqual(evs_serve[0]["data"]["tip"], 12)

        for _ in range(599):
            self.assertEqual(sess.step(_inp()), [])
        evs_paid = sess.step(_inp())
        self.assertEqual([e["name"] for e in evs_paid], ["paid"])
        self.assertEqual(evs_paid[0]["data"]["amount"], 72)
        self.assertEqual(evs_paid[0]["data"]["reason"], "finished_eating")
        self.assertEqual(sess.sim.money, 72)
        self.assertAlmostEqual(sess.sim.reputation, 3.2)

    def test_customer_patience_zero_releases_stove_and_reduces_rep(self):
        scen = {
            "player": {"pos": [2, 8]},
            "stock": {"ca_loc": 1},
            "random_customers": False,
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 2},
            ],
        }
        sess = Session("quan", self.tuning, scen, 1)
        evs1 = sess.step(_inp(interact=True))
        self.assertEqual(evs1[0]["name"], "cook_started")
        evs2 = sess.step(_inp())
        self.assertEqual([e["name"] for e in evs2], ["customer_left"])
        self.assertEqual(evs2[0]["data"]["reason"], "patience")
        self.assertAlmostEqual(sess.sim.reputation, 2.5)
        self.assertEqual(sess.sim.stoves[0]["state"], "idle")
        self.assertIsNone(sess.sim.stoves[0]["dish"])
        self.assertEqual(sess.sim.stock, {})

    def test_customer_spawn_and_no_dish(self):
        scen = {
            "stock": {"ca_loc": 1},
            "random_customers": True,
        }
        sess = Session("quan", self.tuning, scen, 1)
        for _ in range(119):
            self.assertEqual(sess.step(_inp()), [])
        evs = sess.step(_inp())
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["name"], "customer_arrived")
        self.assertEqual(evs[0]["data"]["dish_id"], "ca_loc_nuong_trui")

        sess.sim.customers = []
        sess.sim.stock = {}
        for _ in range(899):
            sess.step(_inp())
        evs_no = sess.step(_inp())
        self.assertEqual([e["name"] for e in evs_no], ["no_dish"])

    def test_scenario_contradictions_return_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            bad_cases = [
                {"quan": {"stock": {}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}},
                {"quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}]}},
                {"quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating", "order_status": "served", "eat_ticks_left": 10}]}},
            ]
            for idx, sc in enumerate(bad_cases):
                sp = write_json(os.path.join(d, f"bad_{idx}.json"), sc)
                out = os.path.join(d, f"out_{idx}.jsonl")
                rc, err = run_headless("--mode", "quan", "--seed", "1", "--scenario", sp, "--ticks", "0", "--out", out)
                self.assertEqual(rc, 2, f"Case {idx} should fail with 2, got {rc}: {err}")


class KitchenScenariosTest(unittest.TestCase):
    """6 kịch bản bếp của Người A (`chonoi/sim/kitchen.py`) gộp chung trong 1 file test."""

    def _run_scen(self, quan_block, frames, ticks, snapshot_every=1):
        with tempfile.TemporaryDirectory() as d:
            scen_path = write_json(os.path.join(d, "scen.json"), {"quan": quan_block})
            inp_path = write_json(os.path.join(d, "inputs.json"), {"frames": frames})
            out_path = os.path.join(d, "out.jsonl")
            rc, err = run_headless(
                "--mode", "quan", "--seed", "1",
                "--scenario", scen_path, "--inputs", inp_path,
                "--ticks", str(ticks), "--snapshot-every", str(snapshot_every),
                "--out", out_path,
            )
            self.assertEqual(rc, 0, f"headless failed: {err}")
            return read_jsonl(out_path)

    def test_01_bat_dau_lau(self):
        quan = {
            "player": {"pos": [2.0, 8.0], "vel": [0, 0]},
            "stock": {"ca_linh": 3, "bong_dien_dien": 1, "ca_loc": 1},
            "hand": None,
            "stoves": [{"id": "B1", "state": "idle", "dish": None, "cook_ticks_left": 0, "ready_ticks": 0}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien", "order_tick": 0,
                           "state": "waiting", "patience_ticks_left": 3600, "order_status": "reserved"}],
            "random_customers": False,
            "time_left_ticks": 3600,
        }
        rows = self._run_scen(quan, [{"tick": 0, "interact": True}], ticks=5)
        evs = events(rows, "cook_started")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["tick"], 1)
        self.assertEqual(evs[0]["data"]["dish_id"], "lau_ca_linh_dien_dien")
        self.assertEqual(evs[0]["data"]["items"], ["bong_dien_dien", "ca_linh", "ca_linh", "ca_linh"])
        self.assertEqual(evs[0]["data"]["base_price"], 120)
        snaps = snapshots(rows)
        self.assertEqual(snaps[1]["stock"], {"ca_loc": 1})
        self.assertEqual(snaps[1]["stoves"][0]["state"], "cooking")
        self.assertEqual(snaps[1]["stoves"][0]["cook_ticks_left"], 600)

    def test_02_chin_mon_va_bung(self):
        quan = {
            "player": {"pos": [2.0, 8.0], "vel": [0, 0]},
            "stock": {},
            "hand": None,
            "stoves": [{"id": "B1", "state": "cooking",
                        "dish": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
                        "cook_ticks_left": 3, "ready_ticks": 0}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_tick": 0,
                           "state": "waiting", "patience_ticks_left": 3000, "order_status": "assigned", "reserved": {}}],
            "random_customers": False,
            "time_left_ticks": 1800,
        }
        rows = self._run_scen(quan, [{"tick": 3, "interact": True}], ticks=5)
        ready_evs = events(rows, "dish_ready")
        pick_evs = events(rows, "dish_picked")
        self.assertEqual(len(ready_evs), 1)
        self.assertEqual(ready_evs[0]["tick"], 3)
        self.assertEqual(len(pick_evs), 1)
        self.assertEqual(pick_evs[0]["tick"], 4)
        snaps = snapshots(rows)
        self.assertEqual(snaps[4]["hand"], {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40})
        self.assertEqual(snaps[4]["stoves"][0]["state"], "idle")

    def test_03_bep_chin_khong_khet(self):
        quan = {
            "player": {"pos": [2.0, 8.0], "vel": [0, 0]},
            "stock": {},
            "hand": None,
            "stoves": [{"id": "B1", "state": "ready",
                        "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                        "cook_ticks_left": 0, "ready_ticks": 600}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 0,
                           "state": "waiting", "patience_ticks_left": 2400, "order_status": "assigned", "reserved": {}}],
            "random_customers": False,
            "time_left_ticks": 1800,
        }
        rows = self._run_scen(quan, [{"tick": 5, "interact": True}], ticks=6)
        snaps = snapshots(rows)
        self.assertEqual(snaps[0]["stoves"][0]["ready_ticks"], 600)
        self.assertEqual(snaps[5]["stoves"][0]["ready_ticks"], 605)
        pick_evs = events(rows, "dish_picked")
        self.assertEqual(len(pick_evs), 1)
        self.assertEqual(pick_evs[0]["tick"], 6)
        self.assertEqual(snaps[6]["hand"]["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(snaps[6]["stoves"][0]["state"], "idle")

    def test_04_mep_ban_kinh_bep(self):
        quan = {
            "player": {"pos": [3.5, 8.0], "vel": [0, 0]},
            "stock": {"ca_loc": 1},
            "hand": None,
            "stoves": [{"id": "B1", "state": "idle", "dish": None, "cook_ticks_left": 0, "ready_ticks": 0}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 0,
                           "state": "waiting", "patience_ticks_left": 3600, "order_status": "reserved"}],
            "random_customers": False,
            "time_left_ticks": 1800,
        }
        rows = self._run_scen(quan, [{"tick": 0, "interact": True}], ticks=2)
        evs = events(rows, "cook_started")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["data"]["dish_id"], "ca_loc_nuong_trui")

    def test_05_bep_trong_khong_don(self):
        quan = {
            "player": {"pos": [2.0, 8.0], "vel": [0, 0]},
            "stock": {"ca_loc": 2, "bong_sung": 2},
            "hand": None,
            "stoves": [{"id": "B1", "state": "idle", "dish": None, "cook_ticks_left": 0, "ready_ticks": 0}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_tick": 0,
                           "state": "eating", "eat_ticks_left": 300, "order_status": "served",
                           "reserved": {}, "base_price": 40, "tip": 8}],
            "random_customers": False,
            "time_left_ticks": 1800,
        }
        rows = self._run_scen(quan, [{"tick": 0, "interact": True}], ticks=2)
        self.assertEqual(events(rows, "cook_started"), [])
        snaps = snapshots(rows)
        self.assertEqual(snaps[-1]["stoves"][0]["state"], "idle")
        self.assertEqual(snaps[-1]["stock"], {"bong_sung": 2, "ca_loc": 2})

    def test_06_khach_bo_di_do_noi(self):
        quan = {
            "player": {"pos": [2.0, 8.0], "vel": [0, 0]},
            "stock": {},
            "hand": None,
            "stoves": [{"id": "B1", "state": "cooking",
                        "dish": {"order_id": "C1", "dish_id": "lau_ca_linh_dien_dien", "base_price": 120},
                        "cook_ticks_left": 300, "ready_ticks": 0}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien", "order_tick": 0,
                           "state": "waiting", "patience_ticks_left": 10, "order_status": "assigned", "reserved": {}}],
            "random_customers": False,
            "time_left_ticks": 1800,
        }
        rows = self._run_scen(quan, [], ticks=12)
        left_evs = events(rows, "customer_left")
        self.assertEqual(len(left_evs), 1)
        self.assertEqual(left_evs[0]["tick"], 10)
        self.assertEqual(left_evs[0]["data"]["reason"], "patience")
        snaps = snapshots(rows)
        self.assertEqual(snaps[10]["stoves"][0]["state"], "idle")
        self.assertIsNone(snaps[10]["stoves"][0]["dish"])
        self.assertEqual(snaps[10]["customers"], [])
        self.assertAlmostEqual(snaps[10]["reputation"], 2.5)


if __name__ == "__main__":
    unittest.main()
