"""Kiểm vòng ngày, pause và Shop qua headless_cmd."""

from pathlib import Path
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class DayLoop(unittest.TestCase):
    def run_day(self, w, scenario, ticks, *inputs, days=1, name="day", snapshot_every=1):
        sc = write_json(w.path("scenario.json"), scenario)
        ip = write_json(w.path("inputs.json"), frames(*inputs))
        out = w.path(f"{name}.jsonl")
        code, error = run_headless("--mode", "day", "--days", str(days), "--seed", "42",
                                   "--scenario", sc, "--inputs", ip, "--ticks", str(ticks),
                                   "--snapshot-every", str(snapshot_every), "--out", out)
        self.assertEqual(code, 0, error)
        return read_jsonl(out)

    def test_phase_events_keep_old_phase_and_snapshot_resets_phase_tick(self):
        with Workdir() as w:
            rows = self.run_day(w, {
                "gather": {"hold": ["ca_loc"], "time_left_ticks": 1},
                "quan": {"time_left_ticks": 1},
            }, 5, {"tick": 2, "shop_done": True}, snapshot_every=99)
        self.assertEqual([(e["tick"], e["phase"], e["name"]) for e in events(rows)], [
            (0, "gather", "day_start"), (0, "gather", "day_plan"), (0, "gather", "phase_start"),
            (1, "gather", "gather_end"), (1, "quan", "phase_start"),
            (2, "quan", "quan_end"), (2, "shop", "phase_start"), (3, "shop", "shop_end"),
        ])
        snaps = snapshots(rows)
        self.assertEqual([(s["phase_tick"], s["sim_tick"]) for s in snaps], [(0, 0), (0, 1), (0, 2), (1, 3)])
        self.assertEqual(snaps[1]["stock"], {"ca_loc": 1})
        self.assertEqual(snaps[2]["stock"], {"ca_loc": 1})
        self.assertEqual(rows[-1]["days_completed"], 1)
        self.assertEqual(rows[-1]["reason"], "days_complete")

    def test_pause_freezes_quan_timers_and_resume_runs_same_step(self):
        with Workdir() as w:
            rows = self.run_day(w, {
                "gather": {"time_left_ticks": 1},
                "quan": {
                    "time_left_ticks": 10,
                    "stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 1,
                                "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "assigned", "patience_ticks_left": 8}],
                },
            }, 4, {"tick": 1, "pause": True}, {"tick": 2, "pause": False}, {"tick": 3, "pause": True})
        snaps = snapshots(rows)
        for tick in (2, 3):
            self.assertEqual((snaps[tick]["state"], snaps[tick]["time_left_ticks"]), ("paused", 10))
            self.assertEqual((snaps[tick]["sim_tick"], snaps[tick]["phase_tick"]), (1, 0))
            self.assertEqual(snaps[tick]["stoves"][0]["cook_ticks_left"], 1)
            self.assertEqual(snaps[tick]["customers"][0]["patience_ticks_left"], 8)
        self.assertEqual([(e["tick"], e["name"]) for e in events(rows) if e["tick"] >= 2],
                         [(2, "paused"), (4, "resumed"), (4, "dish_ready")])
        self.assertEqual((snaps[4]["sim_tick"], snaps[4]["phase_tick"]), (2, 1))

    def test_sale_carries_through_days_and_upgrades_apply_when_next_day_opens(self):
        with Workdir() as w:
            rows = self.run_day(w, {
                "day": {"money": 428, "earned": 428},
                "gather": {"time_left_ticks": 1},
                "quan": {"time_left_ticks": 1, "customers": [
                    {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating",
                     "order_status": "served", "eat_ticks_left": 2, "base_price": 60, "tip": 12},
                ]},
            }, 9,
                {"tick": 2, "buy": "oxygen"},
                {"tick": 3, "buy": "hp"},
                {"tick": 4, "buy": "hp"},
                {"tick": 5, "buy": "bad", "shop_done": True},
                {"tick": 8, "shop_done": False}, days=2)
        snaps = snapshots(rows)
        self.assertEqual(snaps[2]["money"], 500)
        self.assertEqual(snaps[2]["reputation"], 3.2)
        self.assertEqual(snaps[3]["upgrades"], {"oxygen": 1})
        self.assertEqual(snaps[3]["active_upgrades"], {})
        self.assertEqual([e["data"]["reason"] for e in events(rows, "buy_failed")], ["funds", "unknown"])
        day_two = snaps[6]
        self.assertEqual((day_two["day"], day_two["phase_tick"], day_two["sim_tick"]), (2, 0, 6))
        self.assertEqual(day_two["active_upgrades"], {"oxygen": 1, "hp": 1})
        self.assertEqual((day_two["player"]["oxygen_ticks"], day_two["player"]["hp"]), (2700, 4))
        self.assertEqual((day_two["money"], day_two["earned"], day_two["score"]), (50, 500, 800))
        self.assertEqual(rows[-1]["days_completed"], 1)  # Đã vào Shop ngày 2, chưa đóng

    def test_last_shop_tick_processes_buy_before_done_and_discards_paused_buy(self):
        with Workdir() as w:
            rows = self.run_day(w, {
                "day": {"money": 600, "earned": 600},
                "gather": {"time_left_ticks": 1}, "quan": {"time_left_ticks": 1},
            }, 700,
                {"tick": 2, "pause": True, "buy": "hp", "shop_done": True},
                {"tick": 3, "pause": False, "shop_done": False, "buy": "hp"},
                {"tick": 4, "pause": True, "buy": "oxygen"},
                {"tick": 603, "buy": "oxygen", "shop_done": True})
        self.assertEqual([(e["tick"], e["data"]["money"]) for e in events(rows, "bought")], [(5, 400), (604, 0)])
        self.assertEqual([e["name"] for e in events(rows) if e["tick"] == 604], ["bought", "shop_end"])
        self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "done"})
        self.assertEqual((rows[-1]["ticks"], rows[-1]["sim_tick"], rows[-1]["days_completed"]), (604, 602, 1))

    def test_five_days_auto_close_and_are_deterministic(self):
        with Workdir() as w:
            scenario = {"gather": {"time_left_ticks": 1}, "quan": {"time_left_ticks": 1}}
            rows = self.run_day(w, scenario, 3100, days=5, name="a", snapshot_every=60)
            self.run_day(w, scenario, 3100, days=5, name="b", snapshot_every=60)
            self.assertEqual(Path(w.path("a.jsonl")).read_bytes(), Path(w.path("b.jsonl")).read_bytes())
        self.assertEqual([e["day"] for e in events(rows, "day_plan")], [1, 2, 3, 4, 5])
        self.assertEqual([e["data"]["reason"] for e in events(rows, "shop_end")], ["time"] * 5)
        self.assertEqual((rows[-1]["ticks"], rows[-1]["days_completed"], rows[-1]["reason"]),
                         (3010, 5, "days_complete"))

    def test_plan_override_filters_menu_and_computes_ingredients(self):
        with Workdir() as w:
            rows = self.run_day(w, {
                "day": {"day_plan": {"1": {"dishes": {"goi_bong_sung": 3}}}},
                "gather": {"time_left_ticks": 1, "hold": ["ca_loc"]},
            }, 121)
        self.assertEqual(events(rows, "day_plan")[0]["data"]["ingredients"], {"bong_sung": 6})
        self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [121])
        self.assertFalse(events(rows, "customer_arrived"))

    def test_faint_hands_off_empty_inventory_to_quan(self):
        with Workdir() as w:
            rows = self.run_day(w, {
                "gather": {"player": {"pos": [20, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                           "hold": ["ca_loc"]},
            }, 1)
        self.assertEqual(events(rows, "gather_end")[0]["data"], {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual((snapshots(rows)[-1]["phase"], snapshots(rows)[-1]["stock"]), ("quan", {}))

    def test_reserved_fixture_is_checked_against_the_actual_handoff(self):
        with Workdir() as w:
            scenario = {
                "gather": {"time_left_ticks": 1, "hold": ["ca_loc"]},
                "quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                        "reserved": {"ca_loc": 1}}]},
            }
            rows = self.run_day(w, scenario, 1)
            self.assertEqual(snapshots(rows)[-1]["customers"][0]["reserved"], {"ca_loc": 1})
            scenario["gather"]["hold"] = []
            sc = write_json(w.path("bad.json"), scenario)
            code, _ = run_headless("--mode", "day", "--seed", "42", "--scenario", sc, "--ticks", "1",
                                   "--out", w.path("bad.jsonl"))
            self.assertEqual(code, 2)

    def test_v11_inputs_are_ignored_outside_their_phase(self):
        with Workdir() as w:
            ip = write_json(w.path("inputs.json"), frames({
                "tick": 0, "attack": True, "photo": True, "shop_done": True, "buy": "oxygen",
            }))
            out = w.path("gather.jsonl")
            code, error = run_headless("--mode", "gather", "--seed", "42", "--ticks", "1", "--inputs", ip, "--out", out)
            self.assertEqual(code, 0, error)
            self.assertEqual(events(read_jsonl(out)), [])
            code, _ = run_headless("--mode", "gather", "--days", "1", "--seed", "42", "--ticks", "0", "--out", out)
            self.assertEqual(code, 2)

    def test_initial_max_upgrade_reports_max_level_and_cannot_charge(self):
        with Workdir() as w:
            rows = self.run_day(w, {
                "day": {"money": 600, "earned": 600, "upgrades": {"oxygen": 2}},
                "gather": {"time_left_ticks": 1, "player": {"oxygen_ticks": 3600}},
                "quan": {"time_left_ticks": 1},
            }, 4, {"tick": 2, "buy": "oxygen"})
        self.assertEqual(snapshots(rows)[0]["player"]["oxygen_max_ticks"], 3600)
        self.assertEqual(events(rows, "buy_failed")[0]["data"], {"action": "oxygen", "reason": "max_level"})
        self.assertEqual(rows[-1]["money"], 600)
