"""P2-03: kiểm thứ tự bước, phản xạ, sinh cá và fixture v1.1."""

from copy import deepcopy
import math
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.runner import Session
from helpers import Workdir, read_jsonl, run_headless, write_json


TUNING = load_contract()["tuning"]
G = TUNING["gather"]
SPAWN = G["fish_spawn_ticks"]
TURN = G["fish_turn_ticks"]
DISTANCE = G["fish_speed"] / TUNING["tick_hz"]


def school(ident="F1", *, pos=None, heading=0, age=0, kind="ca_linh"):
    return {"id": ident, "kind": kind, "pos": [30, 5] if pos is None else pos,
            "heading_deg": heading, "age_ticks": age}


def advance(session, ticks, frames=()):
    inputs = InputPlayer(frames)
    rows = []
    for _ in range(ticks):
        if session.done:
            break
        rows.extend(session.step(inputs.advance(session.tick)))
    return rows


class FishDynamicsTests(unittest.TestCase):
    def test_initial_schools_are_seeded_at_distinct_points(self):
        first = Session("gather", TUNING, {}, 17).snapshot()["fish"]
        self.assertEqual(first, Session("gather", TUNING, {}, 17).snapshot()["fish"])
        self.assertNotEqual(first, Session("gather", TUNING, {}, 23).snapshot()["fish"])
        self.assertEqual(len(first), G["fish_initial"])
        self.assertEqual(len({tuple(f["pos"]) for f in first}), G["fish_initial"])
        self.assertEqual([f["id"] for f in first], [f"F{i + 1}" for i in range(len(first))])
        for fish in first:
            self.assertIn(fish["pos"][0], G["fish_spawn_x"])
            self.assertIn(fish["pos"][1], G["fish_spawn_depths"][fish["kind"]])
            self.assertEqual(fish["age_ticks"], 0)

    def test_turn_uses_fish_age_before_movement(self):
        sess = Session("gather", TUNING, {"fish": [school(age=TURN - 2)]}, 17)
        advance(sess, 1)
        before = sess.snapshot()["fish"][0]
        self.assertEqual((before["age_ticks"], before["heading_deg"]), (TURN - 1, 0))
        advance(sess, 1)
        after = sess.snapshot()["fish"][0]
        angle = Streams(17).get("fish_turn").random() * math.tau
        self.assertEqual(after["age_ticks"], TURN)
        self.assertAlmostEqual(after["heading_deg"], math.degrees(angle))
        self.assertAlmostEqual(after["pos"][0], before["pos"][0] + math.cos(angle) * DISTANCE)
        self.assertAlmostEqual(after["pos"][1], before["pos"][1] + math.sin(angle) * DISTANCE)

    def test_reflection_keeps_remaining_distance_at_edge_and_corner(self):
        edge_x, edge_d = G["fish_x"][1], G["fish_depths"]["ca_linh"][1]
        diagonal = DISTANCE / math.sqrt(2)
        sess = Session("gather", TUNING, {"fish": [
            school("F1", pos=[edge_x - DISTANCE / 4, 5]),
            school("F2", pos=[edge_x - diagonal / 2, edge_d - diagonal / 2], heading=45),
        ]}, 17)
        advance(sess, 1)
        edge, corner = sess.snapshot()["fish"]
        self.assertAlmostEqual(edge["pos"][0], edge_x - DISTANCE * 3 / 4)
        self.assertAlmostEqual(edge["heading_deg"], 180)
        self.assertAlmostEqual(corner["pos"][0], edge_x - diagonal / 2)
        self.assertAlmostEqual(corner["pos"][1], edge_d - diagonal / 2)
        self.assertAlmostEqual(corner["heading_deg"], 225)

    def test_spawn_schedule_clearance_age_and_cap(self):
        sess = Session("gather", TUNING, {"fish": [school("F42")]}, 17)
        self.assertEqual(advance(sess, SPAWN - 1), [])
        rows = advance(sess, 1)
        fish, spawned = sess.snapshot()["fish"]
        self.assertEqual([(r["tick"], r["name"], r["data"]) for r in rows], [
            (SPAWN, "fish_spawned", {k: spawned[k] for k in ("id", "kind", "pos")}),
        ])
        self.assertEqual((spawned["id"], spawned["age_ticks"]), ("F43", 0))
        self.assertGreater(math.dist(fish["pos"], spawned["pos"]), G["fish_spawn_clearance"])
        advance(sess, 1)
        self.assertEqual(sess.snapshot()["fish"][1]["age_ticks"], 1)
        rows = advance(sess, (G["fish_max"] - 1) * SPAWN)
        self.assertEqual([r["tick"] for r in rows], [i * SPAWN for i in range(2, G["fish_max"])])
        self.assertEqual(len(sess.snapshot()["fish"]), G["fish_max"])

    def test_exact_clearance_is_blocked_for_every_species(self):
        tuning = deepcopy(TUNING)
        g = tuning["gather"]
        x = g["fish_spawn_x"][0]
        g["fish_speed"] = 0
        g["fish_spawn_x"] = [x]
        g["fish_spawn_depths"] = {kind: depths[:1] for kind, depths in g["fish_spawn_depths"].items()}
        schools = [school(f"F{i + 1}", kind=kind, pos=[x, ds[0] + g["fish_spawn_clearance"]])
                   for i, (kind, ds) in enumerate(g["fish_spawn_depths"].items())]
        sess = Session("gather", tuning, {"fish": schools}, 17)
        self.assertEqual(advance(sess, SPAWN), [])
        self.assertEqual(len(sess.snapshot()["fish"]), len(schools))

    def test_freeze_catch_before_swim_and_no_spawn_on_last_tick(self):
        frozen = school(age=TURN - 1)
        sess = Session("gather", TUNING, {"fish": [frozen], "random_fish": False}, 17)
        self.assertEqual(advance(sess, SPAWN), [])
        self.assertEqual(sess.snapshot()["fish"], [frozen])

        sess = Session("gather", TUNING, {"player": {"pos": [30, 5]}, "fish": [
            school(pos=[30 + G["catch_radius"], 5]),
        ]}, 17)
        self.assertEqual([r["name"] for r in advance(sess, 1, [{"tick": 0, "catch": True}])], ["fish_caught"])

        sess = Session("gather", TUNING, {"fish": [school()], "time_left_ticks": SPAWN}, 17)
        self.assertEqual([r["name"] for r in advance(sess, SPAWN)], ["gather_end"])
        self.assertEqual(sess.snapshot()["fish"][0]["age_ticks"], SPAWN - 1)

    def test_cli_accepts_frozen_age_and_rejects_invalid_age(self):
        with Workdir() as w:
            path, out = w.path("scenario.json"), w.path("out.jsonl")
            args = ("--mode", "gather", "--scenario", path, "--seed", "1", "--ticks", "1", "--out", out)
            for invalid in (-1, True, 0.5):
                write_json(path, {"gather": {"fish": [school(age=invalid)]}})
                self.assertEqual(run_headless(*args)[0], 2)
            write_json(path, {"gather": {"fish": [school(pos=[30, 1], age=7)], "random_fish": False}})
            code, err = run_headless(*args)
            self.assertEqual(code, 0, err)
            self.assertEqual(read_jsonl(out)[-2]["fish"][0]["age_ticks"], 7)
