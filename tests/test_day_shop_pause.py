"""Lát 4 Phase 2 (AC-P2-40..44): --mode day, Shop, pause. Hộp đen qua headless_cmd, số đọc từ game.contract.json."""

import json
import time
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

with open("game.contract.json", encoding="utf-8") as _f:
    TUNING = json.load(_f)["tuning"]
SHOP = TUNING["shop"]
GATHER_T = int(TUNING["gather"]["duration_s"] * 60)
QUAN_T = int(TUNING["quan"]["duration_s"] * 60)
DOCK_NOW = {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False}}


def run_day(w, *frs, scenario=None, days=1, ticks=60000, seed=1):
    args = ["--mode", "day", "--seed", str(seed), "--days", str(days), "--ticks", str(ticks), "--out", w.path("d.jsonl")]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), scenario)]
    if frs:
        args += ["--inputs", write_json(w.path("in.json"), frames(*frs))]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path("d.jsonl")) if code == 0 else [])


def names(rows):
    return [r["name"] for r in rows if r["type"] == "event"]


# cập bến ở tick 0 -> quán mở ở tick 1, đóng ở 1 + QUAN_T, Shop mở cùng tick
SHOP_OPEN = 1 + QUAN_T


class DayFlow(unittest.TestCase):
    """AC-P2-40: thứ tự đổi pha, bàn giao kho trong bộ nhớ, days_complete."""

    def test_phase_order_and_inventory_handoff(self):
        with Workdir() as w:
            code, err, rows = run_day(w, {"tick": 0, "interact": True}, {"tick": SHOP_OPEN, "shop_done": True},
                                      scenario=DOCK_NOW)
            self.assertEqual(code, 0, err)
            ev = [(r["tick"], r["phase"], r["name"]) for r in rows if r["type"] == "event"
                  and r["name"] in ("day_start", "day_plan", "phase_start", "gather_end", "quan_end", "shop_end")]
            self.assertEqual(ev, [(0, "gather", "day_start"), (0, "gather", "day_plan"), (0, "gather", "phase_start"),
                                  (1, "gather", "gather_end"), (1, "quan", "phase_start"),
                                  (SHOP_OPEN, "quan", "quan_end"), (SHOP_OPEN, "shop", "phase_start"),
                                  (SHOP_OPEN + 1, "shop", "shop_end")])
            self.assertTrue(all(r["day"] == 1 for r in rows if r["type"] == "event"))
            quan0 = [s for s in snapshots(rows) if s["phase"] == "quan" and s["phase_tick"] == 0][0]
            self.assertEqual(quan0["stock"], {"bong_sung": 2, "ca_loc": 1})
            end = rows[-1]
            self.assertEqual((end["reason"], end["days_completed"], end["mode"]), ("days_complete", 1, "day"))

    def test_day_plan_event_matches_preset(self):
        with Workdir() as w:
            code, err, rows = run_day(w, ticks=0)
            self.assertEqual(code, 0, err)
            plan = [r for r in rows if r["type"] == "event" and r["name"] == "day_plan"][0]["data"]
            self.assertEqual(plan, {"dishes": TUNING["day_plan"][0]["dishes"],
                                    "ingredients": TUNING["day_plan"][0]["ingredients"]})
            s = snapshots(rows)[0]
            for k in ("day", "day_plan", "upgrades", "active_upgrades"):
                self.assertIn(k, s)

    def test_faint_still_opens_quan_with_empty_stock(self):
        with Workdir() as w:
            sc = {"gather": {"player": {"pos": [20, 5], "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 59},
                             "hold": ["ca_loc"], "random_fish": False}}
            code, err, rows = run_day(w, scenario=sc, ticks=5)
            self.assertEqual(code, 0, err)
            self.assertEqual(names(rows)[3:7], ["choke", "faint", "gather_end", "phase_start"])
            quan0 = [s for s in snapshots(rows) if s["phase"] == "quan"][0]
            self.assertEqual(quan0["stock"], {})

    def test_tick_limit_reason(self):
        with Workdir() as w:
            code, err, rows = run_day(w, ticks=50)
            self.assertEqual(code, 0, err)
            self.assertEqual((rows[-1]["reason"], rows[-1]["days_completed"]), ("tick_limit", 0))


class Shop(unittest.TestCase):
    """AC-P2-41, AC-P2-42: mua cấp, buy_failed, tự đóng, hiệu lực từ Ngày kế."""

    def _shop(self, w, money, *buys, days=1, extra=()):
        frs = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}]
        frs += [{"tick": SHOP_OPEN + i, "buy": b} for i, b in enumerate(buys)]
        frs += list(extra)
        sc = dict(DOCK_NOW, day={"money": money, "earned": money})
        return run_day(w, *frs, scenario=sc, days=days, ticks=60000)

    def test_exact_price_buys_and_keeps_earned(self):
        price = SHOP["upgrades"]["oxygen"][0]["price"]
        with Workdir() as w:
            code, err, rows = self._shop(w, price, "oxygen")
            self.assertEqual(code, 0, err)
            bought = events(rows, "bought")
            self.assertEqual([e["data"] for e in bought], [{"upgrade": "oxygen", "level": 1, "price": price, "money": 0}])
            s = [s for s in snapshots(rows) if s["phase"] == "shop"][-1]
            self.assertEqual((s["money"], s["earned"], s["upgrades"], s["active_upgrades"]),
                             (0, price, {"oxygen": 1}, {}))

    def test_buy_failed_reasons(self):
        ox = SHOP["upgrades"]["oxygen"]
        total = ox[0]["price"] + ox[1]["price"]
        with Workdir() as w:
            code, err, rows = self._shop(w, total, "oxygen", "oxygen", "oxygen", "hp", "weapon")
            self.assertEqual(code, 0, err)
            self.assertEqual([(r["name"], r["data"].get("reason", r["data"].get("level")))
                              for r in rows if r["type"] == "event" and r["name"] in ("bought", "buy_failed")],
                             [("bought", 1), ("bought", 2), ("buy_failed", "max_level"), ("buy_failed", "funds"),
                              ("buy_failed", "unknown")])

    def test_shop_auto_closes_after_max_ticks(self):
        with Workdir() as w:
            code, err, rows = self._shop(w, 0)
            self.assertEqual(code, 0, err)
            end = events(rows, "shop_end")
            self.assertEqual([(e["tick"], e["data"]["reason"]) for e in end], [(SHOP_OPEN + SHOP["max_ticks"], "time")])

    def test_buy_processed_before_shop_done_same_step(self):
        with Workdir() as w:
            code, err, rows = self._shop(w, 1000, extra=[{"tick": SHOP_OPEN, "buy": "hp", "shop_done": True}])
            self.assertEqual(code, 0, err)
            self.assertEqual([r["name"] for r in rows if r["type"] == "event" and r["tick"] == SHOP_OPEN + 1],
                             ["bought", "shop_end"])

    def test_upgrade_applies_from_next_day(self):
        hp1 = SHOP["upgrades"]["hp"][0]
        ox1 = SHOP["upgrades"]["oxygen"][0]
        with Workdir() as w:
            code, err, rows = self._shop(w, hp1["price"] + ox1["price"], "hp", "oxygen", days=2,
                                         extra=[{"tick": SHOP_OPEN + 2, "shop_done": True}])
            self.assertEqual(code, 0, err)
            day1 = [s for s in snapshots(rows) if s["day"] == 1 and s["phase"] == "gather"][0]
            day2 = [s for s in snapshots(rows) if s["day"] == 2 and s["phase"] == "gather"][0]
            self.assertEqual(day1["player"]["hp_max"], TUNING["gather"]["hp_max"])
            self.assertEqual((day2["player"]["hp_max"], day2["player"]["hp"]), (hp1["hp_max"], hp1["hp_max"]))
            self.assertEqual(day2["player"]["oxygen_max_ticks"], int(ox1["oxygen_max_s"] * 60))
            self.assertEqual(day2["active_upgrades"], {"hp": 1, "oxygen": 1})


class Pause(unittest.TestCase):
    """AC-P2-43: pause chỉ tăng tick ngoài, timer đứng yên, kể cả trong Shop."""

    def test_pause_freezes_gather(self):
        with Workdir() as w:
            out = w.path("g.jsonl")
            inp = write_json(w.path("in.json"), frames({"tick": 5, "pause": True}, {"tick": 6, "pause": False},
                                                       {"tick": 20, "pause": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "30", "--out", out, "--inputs", inp)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual([(e["tick"], e["name"]) for e in rows if e["type"] == "event"
                              and e["name"] in ("paused", "resumed")], [(6, "paused"), (21, "resumed")])
            s = {r["tick"]: r for r in snapshots(rows)}
            self.assertEqual(s[10]["state"], "paused")
            self.assertEqual((s[10]["sim_tick"], s[20]["sim_tick"]), (5, 5))
            self.assertEqual(s[10]["time_left_ticks"], s[20]["time_left_ticks"])
            self.assertEqual((s[30]["sim_tick"], s[30]["state"]), (15, "playing"))
            self.assertEqual(rows[-1]["ticks"], 30)
            self.assertEqual(rows[-1]["sim_tick"], 15)

    def test_pause_ignores_actions_and_freezes_shop(self):
        with Workdir() as w:
            frs = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                   {"tick": SHOP_OPEN, "pause": True}, {"tick": SHOP_OPEN + 1, "pause": False, "buy": "oxygen"},
                   {"tick": SHOP_OPEN + 50, "pause": True}]
            sc = dict(DOCK_NOW, day={"money": 999, "earned": 999})
            code, err, rows = run_day(w, *frs, scenario=sc)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "bought"), [], "buy khi đang pause bị bỏ qua")
            end = events(rows, "shop_end")[0]
            self.assertEqual(end["tick"], SHOP_OPEN + 50 + SHOP["max_ticks"], "Shop đứng yên trong 50 bước pause")


class DayScenario(unittest.TestCase):
    """AC-P2-44: scenario day sai -> mã 2; --days ngoài [1, 5] -> mã 2."""

    def test_invalid_inputs_exit_2(self):
        bad = [{"day": {"money": 300, "earned": 100}}, {"day": {"money": 100}},
               {"quan": {"stock": {"ca_loc": 1}}}, {"quan": {"reputation": 4}},
               {"day": {"upgrades": {"oxygen": 9}}}, {"day": {"upgrades": {"jetpack": 1}}},
               {"day": {"day_plan": [{"day": 1, "dishes": {"pho": 1}}]}},
               {"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 9}}]}},
               {"day": {"bonus": 1}}]
        with Workdir() as w:
            for sc in bad:
                code, _, _ = run_day(w, scenario=sc, ticks=0)
                self.assertEqual(code, 2, sc)
            for days in ("0", "6"):
                code, _ = run_headless("--mode", "day", "--seed", "1", "--days", days, "--ticks", "0",
                                       "--out", w.path("x.jsonl"))
                self.assertEqual(code, 2, days)
            code, _ = run_headless("--mode", "gather", "--seed", "1", "--days", "2", "--ticks", "0",
                                   "--out", w.path("x.jsonl"))
            self.assertEqual(code, 2)

    def test_day_plan_override_recomputes_ingredients(self):
        with Workdir() as w:
            code, err, rows = run_day(w, scenario={"day": {"day_plan": [{"day": 1, "dishes": {"ca_keo_nuong": 2}}]}},
                                      ticks=0)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "day_plan")[0]["data"],
                             {"dishes": {"ca_keo_nuong": 2}, "ingredients": {"ca_keo": 4}})


class Performance(unittest.TestCase):
    """AC-P2-53: headless một Ngày không pause (≤ 22.200 tick) chạy ≤ 20 s."""

    def test_one_day_under_20s(self):
        with Workdir() as w:
            t0 = time.perf_counter()
            code, err, rows = run_day(w, ticks=22200)
            self.assertEqual(code, 0, err)
            self.assertLess(time.perf_counter() - t0, 20)
            self.assertEqual(rows[-1]["days_completed"], 1)


if __name__ == "__main__":
    unittest.main()
