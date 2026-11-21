"""Kiểm tra Cá Sấu, va chạm và rơi hàng theo Phase 2."""

import json
import os
import tempfile
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer
from chonoi.runner import Session
from chonoi.scenario import load_scenario
from chonoi.sim.day import DaySim


def monster(ident="M1", pos=(60, 24), **kwargs):
    return {"id": ident, "kind": "ca_sau", "pos": list(pos),
            "waypoints": [[60, 24], [64, 24]], **kwargs}


class CrocodileTests(unittest.TestCase):
    def make_session(self, **scenario):
        scenario.setdefault("random_fish", False)
        scenario.setdefault("nodes", [])
        return Session("gather", load_contract()["tuning"], scenario, 1)

    def step(self, session):
        return session.step(InputPlayer([]).advance(0))

    def test_patrol_and_chase(self):
        session = self.make_session(monsters=[monster()])
        self.step(session)
        croc = session.sim.monsters[0]
        self.assertEqual(croc["state"], "patrol")
        self.assertAlmostEqual(croc["pos"][0], 60 + 1 / 60)
        session.sim.pos = [65, 24]
        self.step(session)
        self.assertEqual(croc["state"], "chase")
        self.assertAlmostEqual(croc["pos"][0], 60 + 1 / 60 + 3 / 60)
        session.sim.pos = [65, 9]
        self.step(session)
        self.assertEqual(croc["state"], "patrol")

    def test_hit_selects_one_and_loses_lifo(self):
        session = self.make_session(player={"pos": [60, 24]},
                                    hold=["ca_loc", "ca_linh", "bong_sung", "ca_loc", "ca_linh"],
                                    monsters=[monster("M10"), monster("M2")])
        events = self.step(session)
        hit = next(e for e in events if e["name"] == "monster_hit")
        self.assertEqual(hit["data"]["monster_id"], "M2")
        self.assertEqual(hit["data"]["lost"], ["ca_linh", "ca_loc"])
        self.assertEqual(session.sim.hold, ["ca_loc", "ca_linh", "bong_sung"])
        self.assertEqual(session.sim.invuln_ticks, 90)
        self.assertEqual(session.sim.monsters[1]["state_ticks_left"], 60)
        self.assertFalse(any(e["name"] == "monster_hit" for e in self.step(session)))

    def test_recoil_sixty_steps_then_patrol(self):
        m = monster(state="recoil", state_ticks_left=60, recoil_dir=[1, 0])
        session = self.make_session(monsters=[m])
        for _ in range(60):
            self.step(session)
        croc = session.sim.monsters[0]
        self.assertEqual(croc["state"], "patrol")
        self.assertEqual(croc["state_ticks_left"], 0)
        self.assertAlmostEqual(croc["pos"][0], 62)

    def test_faint_discards_remaining_hold(self):
        session = self.make_session(player={"pos": [60, 24], "hp": 1},
                                    hold=["ca_loc", "ca_linh", "bong_sung"], monsters=[monster()])
        events = self.step(session)
        self.assertEqual([e["name"] for e in events], ["monster_hit", "faint", "gather_end"])
        self.assertEqual(events[0]["data"]["lost"], ["bong_sung"])
        self.assertEqual(events[1]["data"]["lost"], ["ca_linh", "ca_loc"])
        self.assertEqual(events[2]["data"]["inventory"], {"items": {}})

    def test_invalid_scenario_is_rejected(self):
        with tempfile.TemporaryDirectory() as path:
            filename = os.path.join(path, "scenario.json")
            bad = monster(state="recoil", state_ticks_left=0, recoil_dir=[1, 0])
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({"gather": {"monsters": [bad]}}, f)
            with self.assertRaises(BadInput):
                load_scenario(filename, "gather", load_contract()["tuning"])

    def test_invulnerability_does_not_trigger_recoil_and_expires(self):
        session = self.make_session(player={"pos": [60, 24], "invuln_ticks": 2}, monsters=[monster()])
        self.assertFalse(any(e["name"] == "monster_hit" for e in self.step(session)))
        self.assertEqual(session.sim.monsters[0]["state"], "chase")
        self.assertTrue(any(e["name"] == "monster_hit" for e in self.step(session)))

    def test_choke_precedes_hit_in_same_step(self):
        session = self.make_session(player={"pos": [60, 24], "oxygen_ticks": 0,
                                            "zero_oxy_ticks": 59}, monsters=[monster()])
        self.assertEqual([e["name"] for e in self.step(session)], ["choke", "monster_hit"])
        self.assertEqual(session.sim.hp, 1)

    def test_independent_gather_has_only_day_one_crocodile(self):
        session = self.make_session()
        self.assertEqual([m["id"] for m in session.sim.snapshot()["monsters"]], ["M1"])

    def test_day_cycle_uses_day_specific_monsters(self):
        tuning = load_contract()["tuning"]
        for day, expected in ((1, ["M1"]), (2, ["M1"]), (3, ["M1", "M2"])):
            with self.subTest(day=day):
                sim = DaySim(tuning, {"day": day, "intro_ticks": 1})
                sim.step(InputPlayer([]).advance(0))
                self.assertEqual(sim.phase, "gather")
                self.assertEqual([m["id"] for m in sim.active_sim.snapshot()["monsters"]], expected)

    def test_day_scenario_monsters_replace_default_spawns(self):
        tuning = load_contract()["tuning"]
        for fixture in ([], [monster("M10")]):
            with self.subTest(fixture=fixture):
                sim = DaySim(tuning, {"day": 3, "intro_ticks": 1, "gather": {"monsters": fixture}})
                sim.step(InputPlayer([]).advance(0))
                self.assertEqual([m["id"] for m in sim.active_sim.snapshot()["monsters"]],
                                 [m["id"] for m in fixture])


if __name__ == "__main__":
    unittest.main()
