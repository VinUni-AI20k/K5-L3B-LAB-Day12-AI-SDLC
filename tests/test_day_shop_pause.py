"""Unit tests cho Phase 2 Lát 4 (`--mode day`, Shop & nâng cấp, `pause`/`resumed`)."""

import copy
import json
import os
import tempfile
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.headless import main as headless_main
from chonoi.inputs import BUTTONS_V11, InputPlayer, load_frames
from chonoi.runner import Session
from chonoi.scenario import load_scenario

from helpers import items, kind_counts, stock_of


def _tuning():
    return copy.deepcopy(load_contract()["tuning"])


def _step_all(sess, frames, ticks):
    ip = InputPlayer(frames, buttons=BUTTONS_V11)
    events = []
    for k in range(ticks):
        if sess.done:
            break
        events.extend(sess.step(ip.advance(k)))
    return events


class DayShopPauseTests(unittest.TestCase):
    def test_day_cycle_shop_upgrade_applies_next_day_and_discards_leftover(self):
        t = _tuning()
        sc = {
            "day": {"money": 250, "earned": 250},
            "gather": {"fish": [], "random_fish": False, "hold": items("ca_loc", "bong_sung", "bong_sung"), "time_left_ticks": 1},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        sess = Session("day", t, sc, seed=1, days=2)
        init = sess.initial_events()
        self.assertEqual([e["name"] for e in init], ["day_start", "day_plan", "phase_start"])
        self.assertEqual(init[0]["day"], 1)

        # Tick 0: gather hết giờ -> phase_start(quan) cùng tick
        ev0 = sess.step(InputPlayer([], buttons=BUTTONS_V11).advance(0))
        self.assertEqual([(e["name"], e["phase"]) for e in ev0], [("gather_end", "gather"), ("phase_start", "quan")])
        self.assertEqual(sess.snapshot()["phase"], "quan")
        self.assertEqual(sess.snapshot()["phase_tick"], 0)

        # Tick 1: quan hết giờ -> phase_start(shop) cùng tick, shop giữ stock dư từ ca
        ev1 = sess.step(InputPlayer([], buttons=BUTTONS_V11).advance(0))
        self.assertEqual([(e["name"], e["phase"]) for e in ev1], [("quan_end", "quan"), ("phase_start", "shop")])
        snap_shop = sess.snapshot()
        self.assertEqual(snap_shop["phase"], "shop")
        self.assertEqual(kind_counts(snap_shop["stock"]), {"bong_sung": 2, "ca_loc": 1})

        # Tick 2: mua oxygen cấp 1 (giá 200) + bấm shop_done cùng bước -> sang Ngày 2 với active_upgrades["oxygen"] == 1
        ip = InputPlayer([{"tick": 0, "buy": "oxygen", "shop_done": True}], buttons=BUTTONS_V11)
        ev2 = sess.step(ip.advance(0))
        self.assertEqual([e["name"] for e in ev2], ["bought", "shop_end", "day_start", "day_plan", "phase_start"])
        self.assertEqual(ev2[0]["data"], {"upgrade": "oxygen", "level": 1, "price": 200, "money": 50})
        self.assertEqual(ev2[1]["data"], {"reason": "done"})

        snap_d2 = sess.snapshot()
        self.assertEqual(snap_d2["day"], 2)
        self.assertEqual(snap_d2["phase"], "gather")
        self.assertEqual(snap_d2["upgrades"], {"oxygen": 1})
        self.assertEqual(snap_d2["active_upgrades"], {"oxygen": 1})
        self.assertEqual(snap_d2["player"]["oxygen_max_ticks"], 45 * 60)
        self.assertEqual(snap_d2["player"]["oxygen_ticks"], 45 * 60)
        self.assertEqual(snap_d2["money"], 50)
        self.assertEqual(snap_d2["earned"], 250)

    def test_shop_buy_failures_and_auto_close_after_max_ticks(self):
        t = _tuning()
        t["shop"]["max_ticks"] = 3
        sc = {
            "day": {"money": 100, "earned": 100},
            "gather": {"fish": [], "random_fish": False, "time_left_ticks": 1},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        sess = Session("day", t, sc, seed=1, days=1)
        frames = [
            {"tick": 2, "buy": "oxygen"},     # thiếu tiền (100 < 200) -> funds
            {"tick": 3, "buy": "la_gi_do"},   # không hỗ trợ -> unknown
        ]
        evs = _step_all(sess, frames, ticks=10)
        failed = [e for e in evs if e["name"] == "buy_failed"]
        self.assertEqual(failed[0]["data"], {"action": "oxygen", "reason": "funds"})
        self.assertEqual(failed[1]["data"], {"action": "la_gi_do", "reason": "unknown"})
        shop_end = next(e for e in evs if e["name"] == "shop_end")
        self.assertEqual(shop_end["data"], {"reason": "time"})
        self.assertTrue(sess.done)
        self.assertEqual(sess.end_row()["reason"], "days_complete")
        self.assertEqual(sess.end_row()["days_completed"], 1)

    def test_pause_freezes_timers_and_resume_runs_same_step(self):
        t = _tuning()
        sc = {"time_left_ticks": 10, "random_customers": False}
        sess = Session("quan", t, sc, seed=1)
        frames = [
            {"tick": 0, "pause": True},
            {"tick": 1, "pause": False},
            {"tick": 2, "pause": True},   # resume tại tick 2 và chạy 1 bước quan luôn
        ]
        ip = InputPlayer(frames, buttons=BUTTONS_V11)
        e0 = sess.step(ip.advance(0))
        self.assertEqual([e["name"] for e in e0], ["paused"])
        self.assertEqual(sess.snapshot()["state"], "paused")
        self.assertEqual(sess.snapshot()["tick"], 1)
        self.assertEqual(sess.snapshot()["sim_tick"], 0)
        self.assertEqual(sess.snapshot()["time_left_ticks"], 10)

        e1 = sess.step(ip.advance(1))
        self.assertEqual(e1, [])
        self.assertEqual(sess.snapshot()["tick"], 2)
        self.assertEqual(sess.snapshot()["sim_tick"], 0)
        self.assertEqual(sess.snapshot()["time_left_ticks"], 10)

        e2 = sess.step(ip.advance(2))
        self.assertEqual([e["name"] for e in e2], ["resumed"])
        self.assertEqual(sess.snapshot()["state"], "playing")
        self.assertEqual(sess.snapshot()["tick"], 3)
        self.assertEqual(sess.snapshot()["sim_tick"], 1)
        self.assertEqual(sess.snapshot()["time_left_ticks"], 9)

    def test_day_scenario_forbids_quan_stock_and_reputation(self):
        t = _tuning()
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "bad.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"quan": {"stock": stock_of({"ca_loc": 1})}}, f)
            with self.assertRaises(BadInput):
                load_scenario(p, "day", t)

    def test_headless_day_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            sc_p = os.path.join(tmp, "sc.json")
            in_p = os.path.join(tmp, "in.json")
            out_p = os.path.join(tmp, "out.jsonl")
            with open(sc_p, "w", encoding="utf-8") as f:
                json.dump({
                    "day": {"money": 250, "earned": 250},
                    "gather": {"fish": [], "random_fish": False, "time_left_ticks": 1},
                    "quan": {"time_left_ticks": 1, "random_customers": False},
                }, f)
            with open(in_p, "w", encoding="utf-8") as f:
                json.dump({"frames": [{"tick": 2, "buy": "hp", "shop_done": True}]}, f)
            code = headless_main([
                "--mode", "day", "--days", "1", "--seed", "7",
                "--scenario", sc_p, "--inputs", in_p, "--ticks", "20", "--out", out_p,
            ])
            self.assertEqual(code, 0)
            with open(out_p, encoding="utf-8") as f:
                rows = [json.loads(line) for line in f]
            self.assertEqual(rows[-1]["type"], "end")
            self.assertEqual(rows[-1]["reason"], "days_complete")
            self.assertEqual(rows[-1]["days_completed"], 1)
            self.assertEqual(rows[-1]["money"], 0)


if __name__ == "__main__":
    unittest.main()
