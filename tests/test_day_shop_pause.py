"""Kiểm thử Phase 2 (v1.1): DaySim D1-D5, Shop, chuyển pha cùng tick, pause/resumed 3 chế độ."""

import time
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class DayShopPauseTests(unittest.TestCase):
    def test_day1_full_headless_completes_under_budget_and_deterministic(self):
        with Workdir() as w:
            o1 = w.path("d1a.jsonl")
            o2 = w.path("d1b.jsonl")
            t0 = time.monotonic()
            c1, e1 = run_headless("--mode", "day", "--days", "1", "--seed", "7", "--ticks", "25000", "--out", o1)
            elapsed = time.monotonic() - t0
            c2, e2 = run_headless("--mode", "day", "--days", "1", "--seed", "7", "--ticks", "25000", "--out", o2)
            self.assertEqual(c1, 0, e1)
            self.assertEqual(c2, 0, e2)
            self.assertLess(elapsed, 20.0)
            with open(o1, "rb") as f1, open(o2, "rb") as f2:
                self.assertEqual(f1.read(), f2.read())
            rows = read_jsonl(o1)
            end = rows[-1]
            self.assertEqual(end["type"], "end")
            self.assertEqual(end["reason"], "days_complete")
            self.assertEqual(end["days_completed"], 1)
            self.assertEqual(end["sim_tick"], 22200)
            names = [r["name"] for r in events(rows)]
            self.assertIn("day_start", names)
            self.assertIn("day_plan", names)
            self.assertIn("gather_end", names)
            self.assertIn("quan_end", names)
            self.assertIn("shop_end", names)

    def test_shop_buy_before_shop_done_failures_and_next_day_upgrades(self):
        # Day 1 dock tick 0, short quan (1 tick), then Shop: buy oxygen lv1 (200), buy_failed max/funds/unknown,
        # close with buy+shop_done on same tick, verify active_upgrades takes effect on Day 2!
        sc = {
            "day": {"money": 350, "earned": 350},
            "gather": {"time_left_ticks": 1, "random_fish": False, "monsters": []},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        # Tick 0: gather ends -> same tick phase_start(quan);
        # Tick 1: quan ends -> same tick phase_start(shop);
        # Tick 2 (shop): buy oxygen (200->150 left);
        # Tick 3 (shop): buy hp (250 > 150 -> funds);
        # Tick 4 (shop): buy bogus (-> unknown);
        # Tick 5 (shop): buy oxygen lv2 (400 > 150 -> funds) & shop_done=true -> day 1 shop closes, day 2 starts!
        inp = frames(
            {"tick": 0, "interact": True},
            {"tick": 1, "interact": False},
            {"tick": 2, "buy": "oxygen"},
            {"tick": 4, "buy": "unknown_item"},
            {"tick": 5, "buy": "hp", "shop_done": True},
        )
        with Workdir() as w:
            out = w.path("days.jsonl")
            code, err = run_headless(
                "--mode", "day", "--days", "2", "--seed", "1",
                "--scenario", write_json(w.path("sc.json"), sc),
                "--inputs", write_json(w.path("in.json"), inp),
                "--ticks", "10", "--snapshot-every", "1", "--out", out,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            bought = events(rows, "bought")
            self.assertEqual(len(bought), 1)
            self.assertEqual(bought[0]["data"], {"upgrade": "oxygen", "level": 1, "price": 200, "money": 150})
            fails = [e["data"] for e in events(rows, "buy_failed")]
            self.assertEqual(fails, [
                {"action": "unknown_item", "reason": "unknown"},
                {"action": "hp", "reason": "funds"},
            ])
            snaps = snapshots(rows)
            # Tick 3 is during day 1 shop after buying oxygen lv1: upgrades={oxygen:1}, active_upgrades={}
            s_shop = next(s for s in snaps if s["day"] == 1 and s["phase"] == "shop" and s["tick"] == 3)
            self.assertEqual(s_shop["upgrades"], {"oxygen": 1})
            self.assertEqual(s_shop["active_upgrades"], {})
            self.assertEqual(s_shop["earned"], 350)
            self.assertEqual(s_shop["money"], 150)

            # Tick 6 is Day 2 gather start -> active_upgrades has oxygen: 1 -> oxygen_max_ticks == 2700!
            s_d2 = next(s for s in snaps if s["day"] == 2 and s["phase"] == "gather")
            self.assertEqual(s_d2["active_upgrades"], {"oxygen": 1})
            self.assertEqual(s_d2["player"]["oxygen_max_ticks"], 2700)

    def test_shop_buy_and_shop_done_on_final_shop_tick_and_max_level(self):
        # Enter shop at tick 2 (gather 1 tick time, quan 1 tick time), wait 599 shop ticks,
        # on last shop tick 601 (time_left goes 1->0) buy hp lv1, then day 1 done. Also test max_level.
        sc = {
            "day": {"money": 1000, "earned": 1000, "upgrades": {"hp": 2}},
            "gather": {"time_left_ticks": 1, "random_fish": False, "monsters": []},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        inp = frames({"tick": 2, "buy": "hp"}, {"tick": 601, "buy": "oxygen", "shop_done": True})
        with Workdir() as w:
            out = w.path("last.jsonl")
            code, err = run_headless(
                "--mode", "day", "--days", "1", "--seed", "1",
                "--scenario", write_json(w.path("sc.json"), sc),
                "--inputs", write_json(w.path("in.json"), inp),
                "--ticks", "700", "--out", out,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(events(rows, "buy_failed")[0]["data"], {"action": "hp", "reason": "max_level"})
            self.assertEqual(events(rows, "bought")[0]["data"]["upgrade"], "oxygen")
            self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "done"})
            self.assertEqual(rows[-1]["reason"], "days_complete")

    def test_day_plans_d1_to_d5_over_5_days(self):
        sc = {
            "gather": {"time_left_ticks": 1, "random_fish": False, "monsters": []},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        # Skip each shop on tick 2, 5, 8, 11, 14 (release on next tick)
        inp = frames(
            {"tick": 2, "shop_done": True}, {"tick": 3, "shop_done": False},
            {"tick": 5, "shop_done": True}, {"tick": 6, "shop_done": False},
            {"tick": 8, "shop_done": True}, {"tick": 9, "shop_done": False},
            {"tick": 11, "shop_done": True}, {"tick": 12, "shop_done": False},
            {"tick": 14, "shop_done": True}, {"tick": 15, "shop_done": False},
        )
        with Workdir() as w:
            out = w.path("five.jsonl")
            code, err = run_headless(
                "--mode", "day", "--days", "5", "--seed", "1",
                "--scenario", write_json(w.path("sc.json"), sc),
                "--inputs", write_json(w.path("in.json"), inp),
                "--ticks", "100", "--out", out,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            plans = events(rows, "day_plan")
            self.assertEqual([p["day"] for p in plans], [1, 2, 3, 4, 5])
            self.assertEqual(rows[-1]["days_completed"], 5)
            self.assertEqual(rows[-1]["reason"], "days_complete")

    def test_pause_freezes_sim_and_resumes_immediately_across_modes(self):
        # Test pause in gather (verify tick advances, sim_tick & time_left freeze, resumed executes)
        inp = frames(
            {"tick": 1, "pause": True},
            {"tick": 2, "pause": False, "interact": True},  # ignored while paused!
            {"tick": 3, "interact": False},
            {"tick": 4, "pause": True},  # resumed on tick 4->5 AND executes gameplay immediately!
        )
        with Workdir() as w:
            out = w.path("p.jsonl")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1",
                "--scenario", write_json(w.path("sc.json"), {"gather": {"hold": ["ca_loc"], "random_fish": False, "monsters": []}}),
                "--inputs", write_json(w.path("in.json"), inp),
                "--ticks", "6", "--snapshot-every", "1", "--out", out,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual([(e["tick"], e["name"]) for e in events(rows)], [(2, "paused"), (5, "resumed")])
            snaps = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual(snaps[2]["state"], "paused")
            self.assertEqual(snaps[2]["sim_tick"], 1)
            self.assertEqual(snaps[4]["sim_tick"], 1)
            self.assertEqual(snaps[5]["state"], "playing")
            self.assertEqual(snaps[5]["sim_tick"], 2)
            # Never docked on tick 2 while paused
            self.assertEqual(events(rows, "gather_end"), [])

        # Also test pause during shop & quan
        sc_day = {
            "gather": {"time_left_ticks": 1, "random_fish": False, "monsters": []},
            "quan": {"time_left_ticks": 2, "random_customers": False},
        }
        inp_day = frames(
            {"tick": 1, "pause": True},   # paused in quan
            {"tick": 2, "pause": False},
            {"tick": 3, "pause": True},   # resumed in quan (quan progresses tick 1->2? step happens!)
            {"tick": 4, "pause": False},
            {"tick": 5, "pause": True},   # pause in shop
            {"tick": 6, "pause": False, "shop_done": True},  # ignored in pause
            {"tick": 7, "pause": True, "shop_done": False},  # resumed in shop
        )
        with Workdir() as w:
            out = w.path("pday.jsonl")
            c, e = run_headless(
                "--mode", "day", "--days", "1", "--seed", "1",
                "--scenario", write_json(w.path("scd.json"), sc_day),
                "--inputs", write_json(w.path("ind.json"), inp_day),
                "--ticks", "10", "--snapshot-every", "1", "--out", out,
            )
            self.assertEqual(c, 0, e)
            rows = read_jsonl(out)
            self.assertEqual(len(events(rows, "paused")), 2)
            self.assertEqual(len(events(rows, "resumed")), 2)
            self.assertEqual(events(rows, "shop_end"), [])

    def test_holding_interact_across_phase_transition_does_not_retrigger(self):
        # Hold interact=true on tick 0 (docks gather); keep held at tick 1 (quan) -> must NOT press interact
        sc = {
            "gather": {"time_left_ticks": 2, "random_fish": False, "monsters": []},
            "quan": {
                "player": {"pos": [2, 8]},
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": {"ca_loc": 1}}],
            },
        }
        # Give gather 1 ca_loc in hold so quan gets stock {"ca_loc": 1}
        sc["gather"]["hold"] = ["ca_loc"]
        inp = frames({"tick": 0, "interact": True})  # stayed True at tick 1, 2
        with Workdir() as w:
            out = w.path("hold.jsonl")
            c, e = run_headless(
                "--mode", "day", "--days", "1", "--seed", "1",
                "--scenario", write_json(w.path("sc.json"), sc),
                "--inputs", write_json(w.path("in.json"), inp),
                "--ticks", "3", "--out", out,
            )
            self.assertEqual(c, 0, e)
            rows = read_jsonl(out)
            self.assertEqual(events(rows, "cook_started"), [])

    def test_day_mode_and_scenario_validation_errors(self):
        with Workdir() as w:
            out = w.path("e.jsonl")
            self.assertEqual(run_headless("--mode", "gather", "--days", "1", "--seed", "1", "--ticks", "0", "--out", out)[0], 2)
            self.assertEqual(run_headless("--mode", "day", "--days", "6", "--seed", "1", "--ticks", "0", "--out", out)[0], 2)
            for bad in (
                {"quan": {"stock": {"ca_loc": 1}}},
                {"quan": {"reputation": 4.0}},
                {"day": {"money": 100}},
                {"day": {"money": 200, "earned": 100}},
            ):
                with self.subTest(bad=bad):
                    code, _ = run_headless(
                        "--mode", "day", "--seed", "1", "--ticks", "0",
                        "--scenario", write_json(w.path("b.json"), bad), "--out", out,
                    )
                    self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
