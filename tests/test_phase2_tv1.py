"""TICKET-02: kiểm vòng ngày, pause và Cá Sấu qua headless_cmd."""

from pathlib import Path
import tempfile
import unittest

from helpers import events, frames, read_jsonl, run_headless, snapshots, write_json


class Phase2TV1(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)

    def simulate(self, mode, ticks, scenario, inputs=(), *extra, ok=True):
        sc = write_json(self.work / "fixture.json", scenario)
        inp = write_json(self.work / "inputs.json", frames(*inputs))
        out = self.work / "out.jsonl"
        if out.exists():
            out.unlink()
        code, err = run_headless("--mode", mode, "--seed", "-9", "--ticks", str(ticks), "--scenario", sc,
                                 "--inputs", inp, "--snapshot-every", "1", "--out", out, *extra)
        if ok:
            self.assertEqual(code, 0, err)
            return read_jsonl(out)
        self.assertEqual(code, 2, err)

    def test_monster_faint_lifo_after_choke_opens_empty_quan(self):
        hold = ["bong_sung", "ca_loc", "ca_linh", "ca_linh", "bong_dien_dien"]
        scenario = {"gather": {"player": {"pos": [60, 24], "hp": 2, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                               "hold": hold, "time_left_ticks": 1}}
        rows = self.simulate("day", 1, scenario, [{"tick": 0, "catch": True}])
        step = [r for r in events(rows) if r["tick"] == 1]
        self.assertEqual([r["name"] for r in step], ["choke", "monster_hit", "faint", "gather_end", "phase_start"])
        self.assertEqual(step[1]["data"]["lost"], list(reversed(hold[-2:])))
        self.assertEqual(step[2]["data"]["lost"], list(reversed(hold[:-2])))
        self.assertEqual(step[2]["data"]["cause"], "monster")
        self.assertEqual((step[3]["phase"], step[4]["phase"]), ("gather", "quan"))
        self.assertEqual((snapshots(rows)[-1]["stock"], snapshots(rows)[-1]["phase_tick"]), ({}, 0))

    def test_recoil_tie_break_and_invulnerability(self):
        def monster(name):
            return {"id": name, "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}
        scenario = {"gather": {"player": {"pos": [60, 24]}, "monsters": [monster("M10"), monster("M2")]}}
        rows = self.simulate("gather", 91, scenario)
        hits = events(rows, "monster_hit")
        self.assertEqual([(r["tick"], r["data"]["monster_id"]) for r in hits], [(1, "M2"), (91, "M10")])
        snaps = snapshots(rows)
        self.assertEqual(snaps[1]["monsters"][0]["recoil_dir"], [1.0, 0.0])
        self.assertEqual(snaps[60]["monsters"][0]["state_ticks_left"], 1)
        self.assertEqual((snaps[61]["monsters"][0]["state"], snaps[61]["monsters"][0]["pos"]), ("patrol", [62, 24]))

    def test_pause_shop_buy_then_close_and_activate_next_day(self):
        scenario = {"day": {"money": 200, "earned": 200}, "gather": {"time_left_ticks": 1},
                    "quan": {"time_left_ticks": 1}}
        inputs = [{"tick": 2, "pause": True, "buy": "hp"},
                  {"tick": 3, "pause": False, "buy": "hp"},
                  {"tick": 4, "pause": True, "buy": "oxygen", "shop_done": True}]
        rows = self.simulate("day", 5, scenario, inputs, "--days", "2")
        snaps = snapshots(rows)
        self.assertEqual([r["name"] for r in events(rows) if r["tick"] == 0], ["day_start", "day_plan", "phase_start"])
        self.assertEqual((snaps[3]["state"], snaps[4]["time_left_ticks"], snaps[4]["sim_tick"]), ("paused", 600, 2))
        self.assertEqual([r["name"] for r in events(rows) if r["tick"] == 5],
                         ["resumed", "bought", "shop_end", "day_start", "day_plan", "phase_start"])
        self.assertEqual((snaps[5]["day"], snaps[5]["phase"], snaps[5]["phase_tick"]), (2, "gather", 0))
        self.assertEqual((snaps[5]["money"], snaps[5]["earned"], snaps[5]["score"]), (0, 200, 500))
        self.assertEqual(snaps[5]["active_upgrades"], {"oxygen": 1})
        self.assertEqual(snaps[5]["player"]["oxygen_ticks"], 2700)
        self.assertEqual(rows[-1]["days_completed"], 1)

    def test_last_shop_tick_and_three_day_spawns(self):
        scenario = {"gather": {"time_left_ticks": 1}, "quan": {"time_left_ticks": 1}}
        rows = self.simulate("day", 1806, scenario, [{"tick": 1805, "shop_done": True}], "--days", "3")
        starts = [s for s in snapshots(rows) if s["phase"] == "gather" and s["phase_tick"] == 0]
        self.assertEqual([[m["id"] for m in s["monsters"]] for s in starts], [["M1"], ["M1"], ["M1", "M2"]])
        self.assertEqual([r["data"]["reason"] for r in events(rows, "shop_end")], ["time", "time", "done"])
        self.assertEqual((rows[-1]["reason"], rows[-1]["days_completed"]), ("days_complete", 3))

    def test_plan_override_and_invalid_fixtures(self):
        fixture = {"day": {"day_plan": [{"day": 1, "dishes": {"lau_mam": 2}}]}}
        rows = self.simulate("day", 0, fixture)
        self.assertEqual(events(rows, "day_plan")[0]["data"]["ingredients"],
                         {"ca_linh": 4, "ca_keo": 2, "keo_neo": 2, "bong_dien_dien": 2})
        for bad in ({"day": {"money": 5}}, {"day": {"money": 7, "earned": 6}},
                    {"day": {"upgrades": {"hp": 3}}}, {"quan": {"stock": {}}}):
            with self.subTest(bad=bad):
                self.simulate("day", 0, bad, ok=False)
                self.assertFalse((self.work / "out.jsonl").exists())
        self.simulate("gather", 0, {}, (), "--days", "1", ok=False)
        for count in ("0", "6"):
            self.simulate("day", 0, {}, (), "--days", count, ok=False)

    def test_shop_failure_and_active_level_until_next_day(self):
        scenario = {"day": {"money": 250, "earned": 250, "upgrades": {"oxygen": 2}},
                    "gather": {"time_left_ticks": 1}, "quan": {"time_left_ticks": 1}}
        commands = [{"tick": 2, "buy": "oxygen"}, {"tick": 3, "buy": "hp"},
                    {"tick": 4, "buy": "hp"}, {"tick": 5, "buy": "x", "shop_done": True}]
        rows = self.simulate("day", 6, scenario, commands, "--days", "2")
        self.assertEqual([r["data"]["reason"] for r in events(rows, "buy_failed")],
                         ["max_level", "funds", "unknown"])
        shop = snapshots(rows)[4]
        self.assertEqual(shop["upgrades"], {"oxygen": 2, "hp": 1})
        self.assertEqual(shop["active_upgrades"], {"oxygen": 2})
        player = snapshots(rows)[-1]["player"]
        self.assertEqual((player["hp"], player["hp_max"], player["oxygen_ticks"]), (4, 4, 3600))

    def test_pause_freezes_standalone_modes_and_ignores_held_actions(self):
        for mode in ("gather", "quan"):
            with self.subTest(mode=mode):
                inputs = [{"tick": 0, "pause": True, "interact": True},
                          {"tick": 1, "pause": False}, {"tick": 2, "pause": True}]
                rows = self.simulate(mode, 3, {}, inputs)
                self.assertEqual([r["name"] for r in events(rows)], ["paused", "resumed"])
                self.assertEqual([s["sim_tick"] for s in snapshots(rows)], [0, 0, 0, 1])
                self.assertEqual(rows[-1]["state"], "playing")

    def test_unsafe_depth_patrol_and_choke_during_invulnerability(self):
        monster = {"id": "M1", "kind": "ca_sau", "pos": [60, 10], "waypoints": [[60, 10], [64, 10]]}
        scenario = {"gather": {"player": {"pos": [60, 9.99]}, "monsters": [monster]}}
        rows = self.simulate("gather", 1, scenario)
        self.assertEqual(snapshots(rows)[-1]["monsters"][0]["state"], "patrol")
        self.assertEqual(events(rows), [])
        scenario["gather"]["player"] = {"pos": [60, 10], "invuln_ticks": 2, "hp": 1,
                                         "oxygen_ticks": 0, "zero_oxy_ticks": 59}
        rows = self.simulate("gather", 1, scenario)
        self.assertEqual([r["name"] for r in events(rows)], ["choke", "faint", "gather_end"])

    def test_evening_validates_against_actual_handoff(self):
        dish = "ca_loc_nuong_trui"
        customer = {"id": "C1", "table_id": "T1", "dish_id": dish}
        fixture = {"gather": {"time_left_ticks": 1}, "quan": {"customers": [customer]}}
        self.simulate("day", 1, fixture, ok=False)
        fixture["gather"]["hold"] = ["ca_loc"]
        rows = self.simulate("day", 1, fixture)
        self.assertEqual(snapshots(rows)[-1]["customers"][0]["reserved"], {"ca_loc": 1})
        customer["order_status"] = "assigned"
        self.simulate("day", 1, fixture, ok=False)
        fixture["quan"]["stoves"] = [{"id": "B1", "state": "ready",
                                      "dish": {"dish_id": dish, "order_id": "C1", "base_price": 60}}]
        fixture["quan"]["player"] = {"pos": [2, 8]}
        rows = self.simulate("day", 2, fixture, [{"tick": 1, "interact": True}])
        self.assertEqual(snapshots(rows)[-1]["hand"], fixture["quan"]["stoves"][0]["dish"])
