"""Black-box checks of Test Contract v1.1 day, Shop and pause."""

import os
import unittest
from math import hypot
from pathlib import Path

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json
from chonoi.inventory import items_to_counts


class DayContractTest(unittest.TestCase):
    def setUp(self):
        self.work = self.enterContext(Workdir())
        self.short_day = {
            "gather": {"time_left_ticks": 1, "random_fish": False, "monsters": []},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }

    def run_game(self, ticks, *, days=None, scenario=None, frames=(), snapshot_every=1,
                 mode="day", filename="out.jsonl", extra=(), expected=0):
        out = self.work.path(filename)
        args = []
        if days is not None:
            args.extend(("--days", str(days)))
        if scenario is not None:
            args.extend(("--scenario", write_json(self.work.path("scenario.json"), scenario)))
        if frames:
            args.extend(("--inputs", write_json(self.work.path("inputs.json"), {"frames": list(frames)})))
        code, err = run_headless("--mode", mode, "--seed", "17", "--ticks", str(ticks), "--out", out,
                                 "--snapshot-every", str(snapshot_every), *args, *extra)
        self.assertEqual(code, expected, err)
        if expected == 0:
            return read_jsonl(out)
        self.assertFalse(os.path.exists(out))

    def test_one_full_day_stops_at_shop_timeout_with_boundary_snapshots(self):
        rows = self.run_game(22201, days=1, snapshot_every=10000)
        lifecycle = {"day_start", "day_plan", "phase_start", "gather_end", "quan_end", "shop_end"}
        transitions = [(e["tick"], e["phase"], e["name"], e["day"]) for e in events(rows)
                       if e["name"] in lifecycle]
        self.assertEqual(transitions, [
            (0, "gather", "day_start", 1), (0, "gather", "day_plan", 1), (0, "gather", "phase_start", 1),
            (10800, "gather", "gather_end", 1), (10800, "quan", "phase_start", 1),
            (21600, "quan", "quan_end", 1), (21600, "shop", "phase_start", 1),
            (22200, "shop", "shop_end", 1),
        ])
        snaps = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual(len(snaps), len(snapshots(rows)))
        self.assertEqual((snaps[10800]["phase"], snaps[10800]["phase_tick"]), ("quan", 0))
        self.assertEqual((snaps[21600]["phase_tick"], snaps[21600]["time_left_ticks"]), (0, 600))
        self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "time"})
        self.assertEqual(events(rows, "fish_spawned")[0]["tick"], 360)
        self.assertEqual((rows[-1]["ticks"], rows[-1]["sim_tick"], rows[-1]["days_completed"]), (22200, 22200, 1))
        self.assertEqual(rows[-1]["reason"], "days_complete")

    def test_five_short_days_publish_each_standard_plan_and_stay_deterministic(self):
        frames = [{"tick": k, "shop_done": k % 3 == 2} for k in range(15)]
        rows = self.run_game(15, days=5, scenario=self.short_day, frames=frames)
        self.run_game(15, days=5, scenario=self.short_day, frames=frames, filename="second.jsonl")
        self.assertEqual(Path(self.work.path("out.jsonl")).read_bytes(),
                         Path(self.work.path("second.jsonl")).read_bytes())
        plans = events(rows, "day_plan")
        self.assertEqual([plan["tick"] for plan in plans], [0, 3, 6, 9, 12])
        self.assertEqual([plan["day"] for plan in plans], [1, 2, 3, 4, 5])
        self.assertEqual([sum(plan["data"]["ingredients"].values()) for plan in plans], [9, 10, 12, 9, 10])
        self.assertEqual(rows[-1]["days_completed"], 5)

    def test_faint_opens_quan_with_empty_stock_on_same_tick(self):
        self.short_day["gather"].update(
            player={"pos": [20, 5], "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 59},
            hold=["ca_loc", "bong_sung"],
        )
        rows = self.run_game(1, scenario=self.short_day)
        outcomes = [(e["tick"], e["phase"], e["name"]) for e in events(rows) if e["tick"]]
        self.assertEqual(outcomes, [
            (1, "gather", "choke"), (1, "gather", "faint"), (1, "gather", "gather_end"),
            (1, "quan", "phase_start"),
        ])
        self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": []})
        evening = snapshots(rows)[-1]
        self.assertEqual((evening["phase"], evening["phase_tick"], evening["stock"]), ("quan", 0, []))

    def test_shop_purchases_and_failures_apply_to_next_day(self):
        self.short_day["day"] = {"money": 850, "earned": 900, "reputation": 4.1}
        commands = ["oxygen", "hp", "oxygen", "oxygen", "hp", "invalid"]
        frames = [{"tick": k, "buy": cmd} for k, cmd in enumerate(commands, start=2)]
        frames.append({"tick": 8, "shop_done": True})
        rows = self.run_game(9, days=2, scenario=self.short_day, frames=frames)
        self.assertEqual([e["data"] for e in events(rows, "bought")], [
            {"upgrade": "oxygen", "level": 1, "price": 200, "money": 650},
            {"upgrade": "hp", "level": 1, "price": 250, "money": 400},
            {"upgrade": "oxygen", "level": 2, "price": 400, "money": 0},
        ])
        self.assertEqual([e["data"] for e in events(rows, "buy_failed")], [
            {"action": "oxygen", "reason": "max_level"},
            {"action": "hp", "reason": "funds"},
            {"action": "invalid", "reason": "unknown"},
        ])
        snaps = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual(snaps[8]["upgrades"], {"oxygen": 2, "hp": 1})
        self.assertEqual(snaps[8]["active_upgrades"], {})
        next_day = snaps[9]
        self.assertEqual((next_day["day"], next_day["phase_tick"], next_day["hold"]), (2, 0, []))
        self.assertEqual(next_day["active_upgrades"], next_day["upgrades"])
        self.assertEqual((next_day["player"]["oxygen_ticks"], next_day["player"]["hp"]), (3600, 4))
        self.assertEqual((next_day["money"], next_day["earned"], next_day["score"]), (0, 900, 1300))
        self.assertEqual((rows[-1]["reason"], rows[-1]["days_completed"]), ("tick_limit", 1))

    def test_day_carries_actual_kitchen_pay_and_starts_second_day_with_full_capacity(self):
        self.short_day["day"] = {"money": 128, "earned": 128}
        self.short_day["gather"]["hold"] = ["ca_loc"]
        self.short_day["quan"]["customers"] = [{
            "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating",
            "order_status": "served", "eat_ticks_left": 2, "base_price": 60, "tip": 12,
        }]
        rows = self.run_game(3, days=2, scenario=self.short_day,
                             frames=[{"tick": 2, "buy": "oxygen", "shop_done": True}])
        self.assertEqual([e["data"]["amount"] for e in events(rows, "paid")], [72])
        self.assertEqual(items_to_counts(snapshots(rows)[2]["stock"]), {"ca_loc": 1})
        self.assertEqual([e["data"]["money"] for e in events(rows, "bought")], [0])
        self.assertEqual((rows[-1]["money"], rows[-1]["earned"], rows[-1]["reputation"]), (0, 200, 3.2))
        self.assertEqual(snapshots(rows)[-1]["player"]["oxygen_max_ticks"], 2700)

    def test_gather_kitchen_and_shop_run_together(self):
        self.short_day["day"] = {"money": 128, "earned": 128}
        self.short_day["gather"]["hold"] = ["ca_loc"]
        self.short_day["quan"].update(
            time_left_ticks=1200,
            player={"pos": [2, 8]},
            customers=[{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}],
        )
        distance = hypot(7, 6)
        frames = [
            {"tick": 0, "interact": True, "buy": "oxygen"},
            {"tick": 1, "interact": False}, {"tick": 2, "interact": True},
            {"tick": 3, "interact": False}, {"tick": 362, "interact": True},
            {"tick": 363, "interact": False, "move": [7 / distance, -6 / distance]},
            {"tick": 501, "interact": True, "move": [0, 0]},
            {"tick": 1201, "buy": "oxygen", "shop_done": True},
        ]
        rows = self.run_game(1202, days=2, scenario=self.short_day, frames=frames, snapshot_every=1000)
        actions = {"cook_started", "dish_ready", "dish_picked", "served", "paid", "bought", "shop_end"}
        self.assertEqual([(event["name"], event["tick"]) for event in events(rows) if event["name"] in actions], [
            ("cook_started", 3), ("dish_ready", 363), ("dish_picked", 363),
            ("served", 502), ("paid", 1102), ("bought", 1202), ("shop_end", 1202),
        ])
        self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
        self.assertEqual(snapshots(rows)[-2]["stock"], [])
        self.assertEqual((snapshots(rows)[-1]["day"], snapshots(rows)[-1]["player"]["oxygen_ticks"]), (2, 2700))
        self.assertEqual((rows[-1]["money"], rows[-1]["earned"]), (0, 200))

    def test_pause_freezes_gather_and_shop_without_replaying_actions(self):
        self.short_day["day"] = {"money": 200, "earned": 200}
        self.short_day["gather"]["time_left_ticks"] = 2
        self.short_day["quan"]["time_left_ticks"] = 2
        frames = [
            {"tick": 0, "pause": True}, {"tick": 1, "pause": True, "interact": True},
            {"tick": 2, "pause": False}, {"tick": 3, "pause": True},
            {"tick": 4, "pause": False}, {"tick": 7, "pause": True, "buy": "oxygen"},
            {"tick": 8, "pause": False, "shop_done": True}, {"tick": 9, "pause": True, "buy": "oxygen"},
            {"tick": 10, "shop_done": False}, {"tick": 11, "shop_done": True},
        ]
        rows = self.run_game(12, scenario=self.short_day, frames=frames)
        snaps = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual([e["tick"] for e in events(rows, "paused")], [1, 8])
        self.assertEqual([e["tick"] for e in events(rows, "resumed")], [4, 10])
        self.assertEqual((snaps[3]["state"], snaps[3]["sim_tick"], snaps[3]["time_left_ticks"]), ("paused", 0, 2))
        self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "time")
        self.assertEqual((snaps[9]["phase_tick"], snaps[9]["time_left_ticks"], snaps[9]["money"]), (0, 600, 200))
        self.assertEqual((snaps[10]["phase_tick"], snaps[10]["time_left_ticks"]), (1, 599))
        self.assertEqual([e["tick"] for e in events(rows, "bought")], [10])
        self.assertEqual([e["tick"] for e in events(rows, "shop_end")], [12])
        self.assertEqual((rows[-1]["ticks"], rows[-1]["sim_tick"]), (12, 7))

    def test_buy_precedes_shop_done_on_final_tick(self):
        self.short_day["day"] = {"money": 500, "earned": 500, "upgrades": {"hp": 1}}
        rows = self.run_game(602, scenario=self.short_day,
                             frames=[{"tick": 601, "buy": "hp", "shop_done": True}])
        self.assertEqual([(e["name"], e["data"]) for e in events(rows) if e["tick"] == 602], [
            ("bought", {"upgrade": "hp", "level": 2, "price": 500, "money": 0}),
            ("shop_end", {"reason": "done"}),
        ])
        self.assertEqual(snapshots(rows)[-1]["upgrades"], {"hp": 2})
        self.assertEqual(snapshots(rows)[-1]["active_upgrades"], {"hp": 1})

    def test_day_plan_filters_orders_but_serving_target_does_not_cap_them(self):
        self.short_day["day"] = {"day_plan": [{"day": 1, "dishes": {"ca_loc_nuong_trui": 1}}]}
        self.short_day["gather"]["hold"] = ["ca_loc", "ca_loc", "ca_keo", "ca_keo"]
        self.short_day["quan"] = {"time_left_ticks": 2000}
        rows = self.run_game(1021, scenario=self.short_day, snapshot_every=1300)
        self.assertEqual(events(rows, "day_plan")[0]["data"]["ingredients"], {"ca_loc": 1})
        self.assertEqual([row["data"]["dish_id"] for row in events(rows, "customer_arrived")],
                         ["ca_loc_nuong_trui", "ca_loc_nuong_trui"])
        self.assertEqual(items_to_counts(snapshots(rows)[1]["stock"]), {"ca_keo": 2, "ca_loc": 2})

    def test_quan_standalone_can_sell_dish_outside_day_one_plan(self):
        rows = self.run_game(120, mode="quan", scenario={"quan": {"stock": {"ca_keo": 2}}})
        self.assertEqual(events(rows, "customer_arrived")[0]["data"]["dish_id"], "ca_keo_nuong")

    def test_pause_freezes_quan_schedule_and_timer(self):
        rows = self.run_game(123, mode="quan", scenario={"quan": {"stock": {"ca_keo": 2}}},
                             frames=[{"tick": 118, "pause": True}, {"tick": 119, "pause": False},
                                     {"tick": 121, "pause": True}])
        snaps = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual((snaps[121]["phase_tick"], snaps[121]["sim_tick"]), (118, 118))
        self.assertEqual(snaps[121]["time_left_ticks"], snaps[118]["time_left_ticks"])
        self.assertEqual(events(rows, "customer_arrived")[0]["tick"], 123)

    def test_day_rejects_invalid_args_fixtures_and_late_reservations(self):
        for days in (0, 6):
            self.run_game(0, days=days, expected=2)
        self.run_game(0, mode="gather", days=1, expected=2)
        self.run_game(0, extra=("--inventory", "unused.json"), expected=2)
        self.run_game(0, extra=("--inventory-out", "unused.json"), expected=2)
        self.run_game(1, frames=[{"tick": 0, "buy": ""}], expected=2)
        bad = [
            {"day": {"money": 200}}, {"day": {"upgrades": {"hp": 3}}},
            {"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 2}, "ingredients": {"bong_sung": 2}}]}},
            {"quan": {"stock": {}}}, {"quan": {"reputation": 1}},
        ]
        for scenario in bad:
            with self.subTest(scenario=scenario):
                self.run_game(0, scenario=scenario, expected=2)
        self.short_day["quan"]["customers"] = [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"},
        ]
        self.run_game(1, scenario=self.short_day, expected=2)
        self.short_day["gather"]["hold"] = ["ca_keo", "ca_keo"]
        self.short_day["quan"]["customers"][0]["dish_id"] = "ca_keo_nuong"
        self.run_game(1, scenario=self.short_day, expected=2)
