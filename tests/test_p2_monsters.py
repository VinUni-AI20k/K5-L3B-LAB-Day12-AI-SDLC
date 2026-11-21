"""P2-04: Cá Sấu, Máu, ngạt (Ticket-02 mục 1.2). Số liệu đọc từ game.contract.json."""

import json
import math
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.scenario import load_scenario
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.gather import GatherSim
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

TUNING = load_contract()["tuning"]
G = TUNING["gather"]
M = G["monsters"]
SP = M["species"]["ca_sau"]
HZ = TUNING["tick_hz"]
LO, HI = SP["depths"]
MID = (LO + HI) / 2


def croc(pos, ident="M1", **kw):
    return {"id": ident, "kind": "ca_sau", "pos": pos, **kw}


def scenario(monsters, **player):
    return {"fish": [], "nodes": [], "monsters": monsters,
            "player": {"pos": [50, MID], "oxygen_ticks": 1000, **player}}


def run(sess, ticks, *fr):
    inputs = InputPlayer(list(fr))
    rows = []
    for _ in range(ticks):
        if sess.done:
            break
        rows.extend(sess.step(inputs.advance(sess.tick)))
    return rows


def evs(rows, name):
    return [r for r in rows if r["type"] == "event" and r["name"] == name]


class DefaultLayout(unittest.TestCase):
    def test_spawns_follow_from_day(self):
        for day in (1, 2, 3, 5):
            sim = GatherSim(TUNING, {}, Streams(1), IdAllocator(), day=day)
            want = sorted(sp["id"] for sp in M["spawns"] if sp["from_day"] <= day)
            self.assertEqual([m["id"] for m in sim.snapshot()["monsters"]], want)

    def test_standalone_gather_uses_day_one(self):
        snap = Session("gather", TUNING, {}, 1).snapshot()
        self.assertEqual([m["id"] for m in snap["monsters"]], ["M1"])
        self.assertEqual(snap["monsters"][0]["state"], "patrol")
        self.assertEqual(snap["player"]["invuln_ticks"], 0)

    def test_empty_monsters_disables(self):
        sess = Session("gather", TUNING, scenario([]), 1)
        self.assertEqual(sess.snapshot()["monsters"], [])


class Movement(unittest.TestCase):
    def test_patrol_moves_to_waypoint_then_next(self):
        step = SP["patrol_speed"] / HZ
        wps = [[20, MID], [20 + 2 * step, MID]]
        sess = Session("gather", TUNING, scenario([croc([20, MID], waypoints=wps)], pos=[2, 0]), 1)
        run(sess, 1)  # ở waypoint 0 rồi -> chuyển sang waypoint 1
        m = sess.snapshot()["monsters"][0]
        self.assertEqual((m["pos"], m["waypoint_index"]), ([20.0, MID], 1))
        run(sess, 1)
        self.assertAlmostEqual(sess.snapshot()["monsters"][0]["pos"][0], 20 + step)

    def test_detect_then_chase_at_chase_speed(self):
        gap = SP["detect_radius"]
        sess = Session("gather", TUNING, scenario([croc([50 + gap, MID])]), 1)
        run(sess, 1)
        m = sess.snapshot()["monsters"][0]
        self.assertEqual(m["state"], "chase")
        self.assertAlmostEqual(m["pos"][0], 50 + gap - SP["chase_speed"] / HZ)

    def test_outside_detect_keeps_patrol(self):
        gap = SP["detect_radius"] + 0.5
        sess = Session("gather", TUNING, scenario([croc([50 + gap, MID])]), 1)
        run(sess, 1)
        self.assertEqual(sess.snapshot()["monsters"][0]["state"], "patrol")

    def test_chase_ends_past_exit_radius_or_at_surface(self):
        gap = (SP["detect_radius"] + SP["exit_radius"]) / 2  # trong vùng trễ: vẫn đuổi
        sess = Session("gather", TUNING, scenario([croc([50 + gap, MID], state="chase")]), 1)
        run(sess, 1)
        self.assertEqual(sess.snapshot()["monsters"][0]["state"], "chase")
        far = SP["exit_radius"] + 1
        sess = Session("gather", TUNING, scenario([croc([50 + far, MID], state="chase")]), 1)
        run(sess, 1)
        self.assertEqual(sess.snapshot()["monsters"][0]["state"], "patrol")
        sess = Session("gather", TUNING, scenario([croc([52, LO], state="chase")], pos=[50, 0]), 1)
        run(sess, 1)
        self.assertEqual(sess.snapshot()["monsters"][0]["state"], "patrol")

    def test_monster_stays_in_species_depths(self):
        sess = Session("gather", TUNING, scenario([croc([50, LO])], pos=[50, LO - SP["hit_radius"] - 1]), 1)
        rows = run(sess, 60)
        self.assertEqual(evs(rows, "monster_hit"), [])
        self.assertTrue(all(s["monsters"][0]["pos"][1] >= LO for s in snapshots(rows)))


class Hits(unittest.TestCase):
    def test_hit_costs_hp_half_hold_and_sets_invuln_and_recoil(self):
        hold = ["ca_loc", "bong_sung", "ca_linh", "ca_linh", "keo_neo"]
        sc = {**scenario([croc([51, MID])]), "hold": hold}
        sess = Session("gather", TUNING, sc, 1)
        rows = run(sess, 1)
        n = math.floor(len(hold) * M["loss_ratio"])
        self.assertEqual([e["data"] for e in evs(rows, "monster_hit")], [
            {"monster_id": "M1", "kind": "ca_sau", "hp": G["hp_max"] - 1, "lost": hold[::-1][:n]}])
        snap = sess.snapshot()
        self.assertEqual(snap["hold"], hold[:len(hold) - n])
        self.assertEqual(snap["player"]["hp"], G["hp_max"] - 1)
        self.assertEqual(snap["player"]["invuln_ticks"], M["invuln_ticks"])
        m = snap["monsters"][0]
        self.assertEqual((m["state"], m["recoil_ticks_left"]), ("recoil", SP["recoil_ticks"]))

    def test_recoil_moves_away_total_recoil_dist_then_patrols(self):
        sess = Session("gather", TUNING, scenario([croc([51, MID], waypoints=[[51, MID]])]), 1)
        run(sess, 1)
        x0 = sess.snapshot()["monsters"][0]["pos"][0]
        run(sess, 1)
        self.assertAlmostEqual(sess.snapshot()["monsters"][0]["pos"][0], x0 + SP["recoil_dist"] / SP["recoil_ticks"])
        run(sess, SP["recoil_ticks"] - 1)
        m = sess.snapshot()["monsters"][0]
        self.assertAlmostEqual(m["pos"][0], x0 + SP["recoil_dist"])
        self.assertEqual((m["state"], m["recoil_ticks_left"]), ("patrol", 0))

    def test_invuln_blocks_hits_but_counts_down(self):
        sess = Session("gather", TUNING, scenario([croc([50, MID])], invuln_ticks=3), 1)
        rows = run(sess, 2)
        self.assertEqual(evs(rows, "monster_hit"), [])
        self.assertEqual(sess.snapshot()["player"]["invuln_ticks"], 1)
        rows = run(sess, 1)
        self.assertEqual(len(evs(rows, "monster_hit")), 1)

    def test_invuln_does_not_block_choke(self):
        sc = scenario([], oxygen_ticks=1, hp=2, invuln_ticks=M["invuln_ticks"])
        sess = Session("gather", TUNING, sc, 1)
        rows = run(sess, G["choke_interval_ticks"])
        self.assertEqual([e["data"] for e in evs(rows, "choke")], [{"hp": 1}])

    def test_last_hp_faints_with_monster_cause(self):
        hold = ["ca_loc", "bong_sung", "ca_linh"]
        sess = Session("gather", TUNING, {**scenario([croc([50, MID])], hp=1), "hold": hold}, 1)
        rows = run(sess, 5)
        n = math.floor(len(hold) * M["loss_ratio"])
        names = [(r["name"], r["data"]) for r in rows if r["type"] == "event"]
        self.assertEqual(names, [
            ("monster_hit", {"monster_id": "M1", "kind": "ca_sau", "hp": 0, "lost": hold[::-1][:n]}),
            ("faint", {"cause": "monster", "lost": hold[::-1][n:], "hp": 0}),
            ("gather_end", {"reason": "fainted", "inventory": {"items": {}}}),
        ])
        self.assertTrue(sess.done)


class ScenarioAndHeadless(unittest.TestCase):
    def headless(self, sc, ticks=120, move=(0, 0)):
        with Workdir() as w:
            path = write_json(w.path("s.json"), {"gather": sc})
            inp = write_json(w.path("i.json"), frames({"tick": 0, "move": list(move)}))
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "3", "--ticks", str(ticks),
                                     "--scenario", path, "--inputs", inp, "--out", out)
            if code != 0:
                return code, err
            with open(out, "rb") as f:
                return code, f.read()

    def test_bad_scenarios_exit_2(self):
        for bad in ([croc([50, LO - 1])], [croc([50, MID], kind="ca_la")], [croc([50, MID], speed=1)],
                    [croc([50, MID], state="recoil")], [croc([50, MID]), croc([60, MID])]):
            self.assertEqual(self.headless({"monsters": bad})[0], 2, bad)
        self.assertEqual(self.headless({"player": {"invuln_ticks": M["invuln_ticks"] + 1}})[0], 2)

    def test_v10_tuning_rejects_invuln_and_monsters(self):
        g10 = {k: v for k, v in G.items() if k != "monsters"}
        g10["fish_initial"] = []  # dạng v1.0: danh sách đàn cá cố định
        t10 = {**TUNING, "gather": g10}
        with Workdir() as w:
            for block in ({"player": {"invuln_ticks": 1}}, {"monsters": []}):
                path = write_json(w.path("s.json"), {"gather": block})
                with self.assertRaises(BadInput):
                    load_scenario(path, "gather", t10)

    def test_headless_is_deterministic_and_emits_hits(self):
        sc = scenario([croc([60, MID])], pos=[50, MID])
        a, b = self.headless(sc, 600), self.headless(sc, 600)
        self.assertEqual(a[0], 0, a[1])
        self.assertEqual(a, b)
        rows = [json.loads(x) for x in a[1].splitlines()]
        self.assertTrue(events(rows, "monster_hit"))


if __name__ == "__main__":
    unittest.main()
