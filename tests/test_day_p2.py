"""Phase 2 #4 — `--mode day`, Shop, pause (TICKET-02 mục 2, Test Contract v1.1 mục 4.1–4.5). Test hộp đen qua headless."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

DAY_TICKS = 10800 + 10800 + 600  # gather + quán + Shop tự đóng, không pause


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


def run_day(w, *extra, scenario=None, inputs=None, ticks=DAY_TICKS * 5 + 10, every=1000):
    args = ["--mode", "day", "--seed", "4", "--ticks", str(ticks), "--snapshot-every", str(every),
            "--out", w.path("d.jsonl"), *extra]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), scenario)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("d.jsonl"))


class DayLoop(unittest.TestCase):
    def test_one_day_phase_order_and_end(self):
        with Workdir() as w:
            rows = run_day(w)
            first = [(r["tick"], r["phase"], r["day"], r["name"]) for r in rows[:3]]
            self.assertEqual(first, [(0, "gather", 1, "day_start"), (0, "gather", 1, "day_plan"),
                                     (0, "gather", 1, "phase_start")])
            self.assertEqual(rows[1]["data"], {k: tuning()["day_plan"][0][k] for k in ("dishes", "ingredients")})
            self.assertEqual(rows[3]["type"], "snapshot")
            names = [(r["tick"], r["phase"], r["name"]) for r in events(rows)
                     if r["name"] in ("gather_end", "phase_start", "quan_end", "shop_end")]
            self.assertEqual(names, [(0, "gather", "phase_start"), (10800, "gather", "gather_end"),
                                     (10800, "quan", "phase_start"), (21600, "quan", "quan_end"),
                                     (21600, "shop", "phase_start"), (22200, "shop", "shop_end")])
            end = rows[-1]
            self.assertEqual((end["ticks"], end["reason"], end["days_completed"], end["mode"]),
                             (DAY_TICKS, "days_complete", 1, "day"))

    def test_five_days_announce_plans_d1_to_d5(self):
        with Workdir() as w:
            rows = run_day(w, "--days", "5", every=5000)
            plans = [(r["day"], r["data"]) for r in events(rows, "day_plan")]
            want = [(p["day"], {"dishes": p["dishes"], "ingredients": p["ingredients"]}) for p in tuning()["day_plan"]]
            self.assertEqual(plans, want)
            self.assertEqual((rows[-1]["days_completed"], rows[-1]["reason"]), (5, "days_complete"))
            self.assertTrue(all(s["day"] in (1, 2, 3, 4, 5) and "active_upgrades" in s for s in snapshots(rows)))

    def test_tick_limit_before_shop_closes_is_not_a_completed_day(self):
        with Workdir() as w:
            rows = run_day(w, ticks=DAY_TICKS - 1)
            self.assertEqual((rows[-1]["reason"], rows[-1]["days_completed"]), ("tick_limit", 0))


class ShopAndUpgrades(unittest.TestCase):
    SCEN = {"day": {"money": 700, "earned": 700}, "gather": {"hold": ["ca_loc"], "random_fish": False}}
    # tick 0 cập bến -> quán từ tick 1, đóng ca tick 10801 -> Shop từ 10801
    BUYS = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
            {"tick": 10801, "buy": "oxygen"}, {"tick": 10802, "buy": "hp"}, {"tick": 10803, "buy": "oxygen"},
            {"tick": 10804, "buy": "laser"}, {"tick": 10805, "shop_done": True}]

    def test_buy_flow_and_upgrade_active_from_next_day(self):
        with Workdir() as w:
            rows = run_day(w, "--days", "2", scenario=self.SCEN, inputs=self.BUYS, every=100)
            shop = [(r["tick"], r["name"], r["data"]) for r in events(rows)
                    if r["name"] in ("bought", "buy_failed", "shop_end")][:5]
            self.assertEqual(shop, [
                (10802, "bought", {"upgrade": "oxygen", "level": 1, "price": 200, "money": 500}),
                (10803, "bought", {"upgrade": "hp", "level": 1, "price": 250, "money": 250}),
                (10804, "buy_failed", {"action": "oxygen", "reason": "funds"}),
                (10805, "buy_failed", {"action": "laser", "reason": "unknown"}),
                (10806, "shop_end", {"reason": "done"})])
            ends = [(r["day"], r["name"]) for r in events(rows) if r["tick"] == 10806]
            self.assertEqual(ends, [(1, "shop_end"), (2, "day_start"), (2, "day_plan"), (2, "phase_start")])
            d2 =next(s for s in snapshots(rows) if s["day"] == 2 and s["phase"] == "gather")
            self.assertEqual(d2["active_upgrades"], {"hp": 1, "oxygen": 1})
            self.assertEqual((d2["player"]["oxygen_max_ticks"], d2["player"]["hp_max"], d2["player"]["hp"]),
                             (2700, 4, 4))
            self.assertEqual((d2["money"], d2["earned"]), (250, 700))  # trừ money, giữ earned

    def test_bought_level_shows_now_but_not_active_until_next_day(self):
        with Workdir() as w:
            rows = run_day(w, scenario=self.SCEN, inputs=self.BUYS, ticks=10804)  # dừng giữa Shop
            last = snapshots(rows)[-1]
            self.assertEqual((last["phase"], last["tick"]), ("shop", 10804))
            self.assertEqual((last["upgrades"], last["active_upgrades"]), ({"hp": 1, "oxygen": 1}, {}))
            self.assertEqual(last["time_left_ticks"], 600 - 3)

    def test_exact_price_buys_and_max_level_fails(self):
        with Workdir() as w:
            scen = {"day": {"money": 400, "earned": 400, "upgrades": {"oxygen": 1}},
                    "gather": {"random_fish": False}}
            inp = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                   {"tick": 10801, "buy": "oxygen"}, {"tick": 10802, "buy": "oxygen"}]
            rows = run_day(w, scenario=scen, inputs=inp, every=100)
            got = [(r["name"], r["data"]) for r in events(rows) if r["name"] in ("bought", "buy_failed")]
            self.assertEqual(got, [("bought", {"upgrade": "oxygen", "level": 2, "price": 400, "money": 0}),
                                   ("buy_failed", {"action": "oxygen", "reason": "max_level"})])
            self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "time"})


class Pause(unittest.TestCase):
    def test_pause_freezes_gameplay_and_ignores_actions(self):
        for mode in ("gather", "quan"):
            with Workdir() as w:
                inp = frames({"tick": 0, "move": [1, 1]}, {"tick": 5, "pause": True},
                             {"tick": 6, "pause": False, "interact": True}, {"tick": 7, "interact": False},
                             {"tick": 20, "pause": True}, {"tick": 21, "pause": False})
                code, err = run_headless("--mode", mode, "--seed", "1", "--ticks", "30", "--snapshot-every", "1",
                                         "--inputs", write_json(w.path("in.json"), inp), "--out", w.path("o.jsonl"))
                self.assertEqual(code, 0, err)
                rows = read_jsonl(w.path("o.jsonl"))
                self.assertEqual([(r["tick"], r["name"]) for r in events(rows) if r["name"] in ("paused", "resumed")],
                                 [(6, "paused"), (21, "resumed")], mode)
                s = {r["tick"]: r for r in snapshots(rows)}
                self.assertEqual([s[t]["state"] for t in (5, 6, 20, 21)], ["playing", "paused", "paused", "playing"])
                for t in (6, 7, 20):
                    self.assertEqual((s[t]["sim_tick"], s[t]["phase_tick"], s[t]["time_left_ticks"], s[t]["player"]["pos"]),
                                     (s[5]["sim_tick"], s[5]["phase_tick"], s[5]["time_left_ticks"], s[5]["player"]["pos"]))
                self.assertEqual(s[21]["sim_tick"], 6)  # resumed chạy gameplay ngay trong bước đó
                self.assertEqual((rows[-1]["ticks"], rows[-1]["sim_tick"]), (30, 15))

    def test_pause_in_shop_stops_auto_close_timer(self):
        with Workdir() as w:
            inp = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                   {"tick": 10900, "pause": True}, {"tick": 10901, "pause": False},
                   {"tick": 11000, "pause": True}]
            rows = run_day(w, scenario={"gather": {"random_fish": False}}, inputs=inp, every=100)
            self.assertEqual(events(rows, "shop_end")[0]["tick"], 10801 + 600 + 100)


class DayValidation(unittest.TestCase):
    def test_bad_day_args_and_scenarios_exit_2(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            for args in (("--mode", "day", "--days", "0"), ("--mode", "day", "--days", "6"),
                         ("--mode", "gather", "--days", "1")):
                self.assertEqual(run_headless(*args, "--seed", "1", "--ticks", "0", "--out", out)[0], 2, args)
            for sc in ({"quan": {"stock": {"ca_loc": 1}}}, {"quan": {"reputation": 4}},
                       {"day": {"money": 300, "earned": 100}}, {"day": {"money": 100}},
                       {"day": {"upgrades": {"oxygen": 3}}}, {"day": {"bonus": 1}},
                       {"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 9}}]}}):
                p = write_json(w.path("sc.json"), sc)
                self.assertEqual(run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--scenario", p,
                                              "--out", out)[0], 2, sc)
            self.assertFalse(__import__("os").path.exists(out))

    def test_day_plan_override_recomputes_ingredients(self):
        with Workdir() as w:
            rows = run_day(w, scenario={"day": {"day_plan": [{"day": 1, "dishes": {"lau_mam": 2}}]}}, ticks=0)
            self.assertEqual(events(rows, "day_plan")[0]["data"], {
                "dishes": {"lau_mam": 2},
                "ingredients": {"bong_dien_dien": 2, "ca_keo": 2, "ca_linh": 4, "keo_neo": 2}})


if __name__ == "__main__":
    unittest.main()
