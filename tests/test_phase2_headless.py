"""Kiểm tra hộp đen CLI, pause và vòng ngày theo contract v1.1."""

import unittest
import json

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json
from chonoi.contract import load_contract
from chonoi.live import LiveGame


class Phase2HeadlessTests(unittest.TestCase):
    def test_pause_freezes_gameplay_and_resumes_same_step(self):
        with Workdir() as w:
            scenario = write_json(w.path("sc.json"), {"gather": {"random_fish": False, "monsters": []}})
            inputs = write_json(w.path("in.json"), frames(
                {"tick": 0, "pause": True}, {"tick": 1, "pause": False}, {"tick": 2, "pause": True}))
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "3", "--snapshot-every", "1",
                                     "--scenario", scenario, "--inputs", inputs, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            snaps = snapshots(rows)
            self.assertEqual([s["sim_tick"] for s in snaps], [0, 0, 0, 1])
            self.assertEqual([s["state"] for s in snaps], ["playing", "paused", "paused", "playing"])
            self.assertEqual([e["name"] for e in rows if e["type"] == "event"], ["paused", "resumed"])

    def test_day_shop_purchase_then_finish_same_tick(self):
        with Workdir() as w:
            scenario = write_json(w.path("sc.json"), {
                "day": {"money": 200, "earned": 200},
                "gather": {"random_fish": False, "monsters": [], "time_left_ticks": 1},
                "quan": {"time_left_ticks": 1, "random_customers": False}})
            inputs = write_json(w.path("in.json"), frames({"tick": 2, "buy": "oxygen", "shop_done": True}))
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "day", "--seed", "1", "--days", "1", "--ticks", "3",
                                     "--snapshot-every", "1", "--scenario", scenario, "--inputs", inputs, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual([e["name"] for e in rows if e["type"] == "event"],
                             ["day_start", "day_plan", "phase_start", "gather_end", "phase_start",
                              "quan_end", "phase_start", "bought", "shop_end"])
            self.assertEqual(events(rows, "bought")[0]["data"]["money"], 0)
            self.assertEqual(rows[-1]["reason"], "days_complete")
            self.assertEqual(rows[-1]["days_completed"], 1)
            self.assertEqual(rows[-1]["earned"], 200)
            self.assertEqual([s["phase"] for s in snapshots(rows)], ["gather", "quan", "shop", "shop"])

    def test_days_flag_restricted_to_day(self):
        with Workdir() as w:
            out = w.path("out.jsonl")
            for mode, days in (("gather", "1"), ("day", "0"), ("day", "6")):
                code, _ = run_headless("--mode", mode, "--seed", "1", "--ticks", "0", "--days", days, "--out", out)
                self.assertEqual(code, 2)

    def test_purchase_applies_next_day_and_events_keep_correct_day(self):
        with Workdir() as w:
            scenario = write_json(w.path("sc.json"), {
                "day": {"money": 200, "earned": 200},
                "gather": {"random_fish": False, "monsters": [], "time_left_ticks": 1},
                "quan": {"time_left_ticks": 1, "random_customers": False}})
            inputs = write_json(w.path("in.json"), frames(
                {"tick": 2, "buy": "oxygen", "shop_done": True},
                {"tick": 3, "shop_done": False}, {"tick": 5, "shop_done": True}))
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "day", "--seed", "1", "--days", "2", "--ticks", "6",
                                     "--snapshot-every", "1", "--scenario", scenario, "--inputs", inputs, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual([e["day"] for e in events(rows, "shop_end")], [1, 2])
            self.assertEqual([e["day"] for e in events(rows, "day_start")], [1, 2])
            next_day = next(s for s in snapshots(rows) if s["day"] == 2 and s["phase"] == "gather")
            self.assertEqual(next_day["active_upgrades"]["oxygen"], 1)
            self.assertEqual(next_day["player"]["oxygen_max_ticks"], 45 * 60)
            self.assertEqual(rows[-1]["days_completed"], 2)

    def test_live_day_menu_and_pause_stop_gameplay(self):
        game = LiveGame("day", load_contract()["tuning"], {"gather": {"random_fish": False, "monsters": []}}, 1)
        game._tick_once()
        self.assertEqual(game.session.tick, 0)
        self.assertEqual(json.loads(game.state_json())["ui_screen"], "menu")
        game.set_input({"interact": True})
        game._tick_once()
        self.assertEqual(game.ui_screen, "day_intro")
        game.set_input({"interact": False})
        game._tick_once()
        game.set_input({"interact": True})
        game._tick_once()
        self.assertIsNone(game.ui_screen)
        self.assertEqual(game.session.tick, 0)
        game.set_input({"interact": False, "pause": True})
        game._tick_once()
        self.assertTrue(game.session.paused)
        self.assertEqual(game.session.sim_tick, 0)

    def test_default_day_finishes_at_maximum_duration(self):
        with Workdir() as w:
            out = w.path("day.jsonl")
            code, err = run_headless("--mode", "day", "--seed", "1", "--days", "1", "--ticks", "22200",
                                     "--snapshot-every", "3600", "--out", out)
            self.assertEqual(code, 0, err)
            end = read_jsonl(out)[-1]
            self.assertEqual((end["reason"], end["ticks"], end["days_completed"]), ("days_complete", 22200, 1))

    def test_five_days_complete_after_fifth_shop(self):
        with Workdir() as w:
            scenario = write_json(w.path("sc.json"), {
                "gather": {"random_fish": False, "monsters": [], "time_left_ticks": 1},
                "quan": {"time_left_ticks": 1, "random_customers": False}})
            actions = []
            for day in range(5):
                actions.append({"tick": day * 3 + 2, "shop_done": True})
                if day < 4:
                    actions.append({"tick": day * 3 + 3, "shop_done": False})
            inputs = write_json(w.path("in.json"), frames(*actions))
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "day", "--seed", "1", "--days", "5", "--ticks", "15",
                                     "--scenario", scenario, "--inputs", inputs, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual([event["day"] for event in events(rows, "shop_end")], [1, 2, 3, 4, 5])
            self.assertEqual((rows[-1]["reason"], rows[-1]["days_completed"]), ("days_complete", 5))

    def test_day_three_adds_second_crocodile(self):
        with Workdir() as w:
            scenario = write_json(w.path("sc.json"), {
                "gather": {"random_fish": False, "time_left_ticks": 1},
                "quan": {"time_left_ticks": 1, "random_customers": False}})
            inputs = write_json(w.path("in.json"), frames(
                {"tick": 2, "shop_done": True}, {"tick": 3, "shop_done": False},
                {"tick": 5, "shop_done": True}))
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "day", "--seed", "1", "--days", "3", "--ticks", "6",
                                     "--snapshot-every", "1", "--scenario", scenario, "--inputs", inputs, "--out", out)
            self.assertEqual(code, 0, err)
            starts = [s for s in snapshots(read_jsonl(out)) if s["phase"] == "gather"]
            self.assertEqual([[m["id"] for m in s["monsters"]] for s in starts],
                             [["M1"], ["M1"], ["M1", "M2"]])


if __name__ == "__main__":
    unittest.main()
