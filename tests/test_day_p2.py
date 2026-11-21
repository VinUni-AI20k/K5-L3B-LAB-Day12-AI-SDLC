"""Vòng Ngày, Shop, nâng cấp và pause (Test Contract v1.1 mục 2, 4.1–4.5), hộp đen qua headless_cmd.
Mỗi test ghi AC tương ứng trong docs/verification/phase-2.md.
Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import json
import os
import time
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json
from v12_compat import read_jsonl, write_json  # v1.2: fixture kho đếm -> kho cá thể (lý do: tests/v12_compat.py)

# Ngày ngắn: gather và quán hết giờ sau 1 bước -> Shop mở ở tick 2 (time_left_ticks tối thiểu là 1)
SHORT = {"gather": {"time_left_ticks": 1}, "quan": {"time_left_ticks": 1}}
SHOP_OPEN = 2  # tick Shop mở với SHORT; bước Shop đầu tiên đọc input tick 2


def plan_of(day):
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return next(p for p in json.load(f)["tuning"]["day_plan"] if p["day"] == day)


def run_day(w, scenario=None, inputs=None, ticks=30000, days=None, every=10, mode="day", seed=1):
    args = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--out", w.path("d.jsonl"),
            "--snapshot-every", str(every)]
    if days is not None:
        args += ["--days", str(days)]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), scenario)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("d.jsonl"))


def code_of(w, scenario=None, extra=()):
    out = w.path("bad.jsonl")
    args = ["--mode", "day", "--seed", "1", "--ticks", "5", "--out", out, *extra]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("bad.json"), scenario)]
    return run_headless(*args)[0], os.path.exists(out)


def names(rows):
    return [(e["tick"], e["phase"], e["day"], e["name"]) for e in events(rows)]


class VongNgay(unittest.TestCase):
    def test_ac_p2_50_day_plan_announced_d1_to_d5(self):
        with Workdir() as w:
            rows = run_day(w, SHORT, days=5, every=1000)
            plans = events(rows, "day_plan")
            self.assertEqual([e["day"] for e in plans], [1, 2, 3, 4, 5])
            for e in plans:
                p = plan_of(e["day"])
                self.assertEqual(e["data"], {"dishes": p["dishes"], "ingredients": p["ingredients"]})
            self.assertEqual(plans[0]["tick"], 0)
            self.assertEqual(rows[-1]["reason"], "days_complete")
            self.assertEqual(rows[-1]["days_completed"], 5)

    def test_ac_p2_51_phase_order_same_tick_and_envelopes(self):
        with Workdir() as w:
            rows = run_day(w, SHORT, days=2, every=1000)
            ev = names(rows)
            self.assertEqual(ev[:3], [(0, "gather", 1, "day_start"), (0, "gather", 1, "day_plan"),
                                      (0, "gather", 1, "phase_start")])
            self.assertIn((1, "gather", 1, "gather_end"), ev)
            self.assertLess(ev.index((1, "gather", 1, "gather_end")), ev.index((1, "quan", 1, "phase_start")))
            self.assertLess(ev.index((2, "quan", 1, "quan_end")), ev.index((2, "shop", 1, "phase_start")))
            # Shop tự đóng sau 600 tick hoạt động -> Ngày 2 dựng ngay tick đó
            i = ev.index((602, "shop", 1, "shop_end"))
            self.assertEqual(ev[i + 1:i + 4], [(602, "gather", 2, "day_start"), (602, "gather", 2, "day_plan"),
                                              (602, "gather", 2, "phase_start")])
            snaps = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual((snaps[1]["phase"], snaps[1]["phase_tick"]), ("quan", 0))
            self.assertEqual((snaps[2]["phase"], snaps[2]["phase_tick"], snaps[2]["time_left_ticks"]), ("shop", 0, 600))
            self.assertEqual((snaps[602]["phase"], snaps[602]["day"], snaps[602]["phase_tick"]), ("gather", 2, 0))
            for s in snaps.values():
                for k in ("day", "day_plan", "upgrades", "active_upgrades"):
                    self.assertIn(k, s)
            self.assertEqual(rows[-1]["days_completed"], 2)

    def test_ac_p2_52_faint_opens_quan_with_empty_stock(self):
        sc = {"gather": {"hold": ["ca_loc", "bong_sung"],
                         "player": {"pos": [20, 5], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59}}}
        with Workdir() as w:
            rows = run_day(w, sc, ticks=3, every=1)
            end = events(rows, "gather_end")[0]
            self.assertEqual((end["tick"], end["data"]["reason"]), (1, "fainted"))
            self.assertEqual(events(rows, "faint")[0]["data"]["lost"], ["bong_sung", "ca_loc"])
            s = next(s for s in snapshots(rows) if s["tick"] == 1)
            self.assertEqual((s["phase"], s["stock"]), ("quan", {}))
            self.assertIn((1, "quan", 1, "phase_start"), names(rows))

    def test_ac_p2_53_menu_filtered_by_day_plan_before_stock(self):
        dock = [{"tick": 0, "interact": True}]
        with Workdir() as w:  # ca_kèo nướng nấu được nhưng không thuộc kế hoạch D1 -> no_dish
            rows = run_day(w, {"gather": {"hold": ["ca_keo", "ca_keo"]}}, dock, ticks=125, every=1000)
            self.assertEqual(snapshots(rows)[1]["stock"] if snapshots(rows)[1]["tick"] == 1 else None, {"ca_keo": 2})
            self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [121])
        for seed in range(1, 6):
            with Workdir() as w:
                rows = run_day(w, {"gather": {"hold": ["ca_keo", "ca_keo", "ca_loc"]}}, dock, ticks=125,
                               every=1000, seed=seed)
                self.assertEqual(events(rows, "customer_arrived")[0]["data"]["dish_id"], "ca_loc_nuong_trui")

    def test_ac_p2_54_money_earned_reputation_carry_over(self):
        eater = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating",
                 "order_status": "served", "eat_ticks_left": 300, "base_price": 60, "tip": 12}
        sc = {"day": {"money": 100, "earned": 300, "reputation": 4.0},
              "gather": {"time_left_ticks": 1}, "quan": {"time_left_ticks": 1, "customers": [eater]}}
        with Workdir() as w:
            rows = run_day(w, sc, days=2, every=1000)
            s0 = snapshots(rows)[0]
            self.assertEqual((s0["money"], s0["earned"], s0["reputation"]), (100, 300, 4.0))
            shop1 = next(s for s in snapshots(rows) if s["tick"] == 2)
            self.assertEqual((shop1["money"], shop1["earned"]), (172, 372))
            self.assertAlmostEqual(shop1["reputation"], 4.2)
            day2 = next(s for s in snapshots(rows) if s["tick"] == 602)
            self.assertEqual((day2["day"], day2["money"], day2["earned"]), (2, 172, 372))
            end = rows[-1]
            self.assertEqual((end["money"], end["earned"], end["days_completed"]), (244, 444, 2))
            self.assertAlmostEqual(end["reputation"], 4.4)
            self.assertEqual(end["score"], 444 + 400)


class Shop(unittest.TestCase):
    def test_ac_p2_60_buy_exact_price_deducts_money_keeps_earned(self):
        sc = dict(SHORT, day={"money": 200, "earned": 200})
        with Workdir() as w:
            rows = run_day(w, sc, [{"tick": SHOP_OPEN, "buy": "oxygen"}, {"tick": SHOP_OPEN + 1, "buy": "oxygen"}],
                           ticks=SHOP_OPEN + 2, every=1)
            b = events(rows, "bought")
            self.assertEqual(b[0]["data"], {"upgrade": "oxygen", "level": 1, "price": 200, "money": 0})
            self.assertEqual(b[0]["phase"], "shop")
            self.assertEqual(events(rows, "buy_failed")[0]["data"], {"action": "oxygen", "reason": "funds"})
            s = snapshots(rows)[-1]
            self.assertEqual((s["money"], s["earned"], s["score"]), (0, 200, 200 + 300))
            self.assertEqual((s["upgrades"], s["active_upgrades"]), ({"oxygen": 1}, {}))

    def test_ac_p2_61_buy_failed_max_level_and_unknown(self):
        sc = dict(SHORT, day={"money": 5000, "earned": 5000, "upgrades": {"hp": 2}})
        with Workdir() as w:
            inputs = [{"tick": SHOP_OPEN, "buy": "hp"}, {"tick": SHOP_OPEN + 1, "buy": "weapon"},
                      {"tick": SHOP_OPEN + 2, "buy": "buy:ca_loc"}]
            rows = run_day(w, sc, inputs, ticks=SHOP_OPEN + 3, every=1)
            self.assertEqual([e["data"] for e in events(rows, "buy_failed")],
                             [{"action": "hp", "reason": "max_level"}, {"action": "weapon", "reason": "unknown"},
                              {"action": "buy:ca_loc", "reason": "unknown"}])
            self.assertEqual(snapshots(rows)[-1]["money"], 5000)

    def test_ac_p2_62_buy_processed_before_shop_done_same_step(self):
        sc = dict(SHORT, day={"money": 250, "earned": 250})
        with Workdir() as w:
            rows = run_day(w, sc, [{"tick": SHOP_OPEN, "buy": "hp", "shop_done": True}], every=1000)
            self.assertEqual([e["name"] for e in events(rows) if e["phase"] == "shop" and e["name"] != "phase_start"],
                             ["bought", "shop_end"])
            self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "done"})
            self.assertEqual(events(rows, "shop_end")[0]["tick"], SHOP_OPEN + 1)
            self.assertEqual((rows[-1]["reason"], rows[-1]["days_completed"]), ("days_complete", 1))

    def test_ac_p2_63_shop_auto_closes_after_600_ticks_and_last_step_buy(self):
        sc = dict(SHORT, day={"money": 200, "earned": 200})
        with Workdir() as w:
            rows = run_day(w, sc, [{"tick": SHOP_OPEN + 599, "buy": "oxygen"}], every=1000)
            end = events(rows, "shop_end")[0]
            self.assertEqual((end["tick"], end["data"]), (SHOP_OPEN + 600, {"reason": "time"}))
            self.assertEqual(events(rows, "bought")[0]["tick"], SHOP_OPEN + 600)
            self.assertEqual(rows[-1]["days_completed"], 1)

    def test_ac_p2_64_shop_done_on_last_step_is_done(self):
        with Workdir() as w:
            rows = run_day(w, SHORT, [{"tick": SHOP_OPEN + 599, "shop_done": True}], every=1000)
            self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "done"})

    def test_ac_p2_65_upgrades_effective_only_from_next_day(self):
        sc = dict(SHORT, day={"money": 450, "earned": 450})
        inputs = [{"tick": SHOP_OPEN, "buy": "oxygen"}, {"tick": SHOP_OPEN + 1, "buy": "hp", "shop_done": True}]
        with Workdir() as w:
            rows = run_day(w, sc, inputs, days=2, every=1)
            snaps = {s["tick"]: s for s in snapshots(rows)}
            shop = snaps[SHOP_OPEN + 1]
            self.assertEqual((shop["phase"], shop["upgrades"], shop["active_upgrades"]), ("shop", {"oxygen": 1}, {}))
            d1 = snaps[0]["player"]
            self.assertEqual((d1["oxygen_max_ticks"], d1["hp_max"]), (1800, 3))
            day2 = snaps[SHOP_OPEN + 2]
            self.assertEqual((day2["day"], day2["phase"], day2["phase_tick"]), (2, "gather", 0))
            self.assertEqual(day2["active_upgrades"], {"hp": 1, "oxygen": 1})
            p = day2["player"]
            self.assertEqual((p["oxygen_ticks"], p["oxygen_max_ticks"], p["hp"], p["hp_max"]), (2700, 2700, 4, 4))
            self.assertEqual(day2["money"], 0)


class Pause(unittest.TestCase):
    def test_ac_p2_40_pause_freezes_quan_schedule_and_ignores_actions(self):
        inputs = [{"tick": 0, "pause": True}, {"tick": 1, "pause": False, "interact": True},
                  {"tick": 4, "pause": True}]
        with Workdir() as w:
            out = w.path("q.jsonl")
            sc = write_json(w.path("sc.json"), {"quan": {"stock": {"ca_loc": 1}, "player": {"pos": [2, 8]}}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "130", "--out", out,
                                     "--scenario", sc, "--inputs", write_json(w.path("i.json"), frames(*inputs)),
                                     "--snapshot-every", "1")
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            ev = [(e["tick"], e["name"]) for e in events(rows)]
            self.assertEqual(ev[:2], [(1, "paused"), (5, "resumed")])
            snaps = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual((snaps[3]["state"], snaps[3]["sim_tick"], snaps[3]["phase_tick"]), ("paused", 0, 0))
            self.assertEqual(snaps[3]["time_left_ticks"], 10800)
            self.assertEqual((snaps[5]["state"], snaps[5]["sim_tick"]), ("playing", 1))
            self.assertNotIn("cook_started", [n for _, n in ev])  # cạnh interact lúc pause bị bỏ
            self.assertIn((124, "customer_arrived"), ev)  # lịch 120 tính theo sim_tick: lệch đúng 4 tick pause

    def test_ac_p2_41_pause_in_gather_freezes_clock(self):
        with Workdir() as w:
            out = w.path("g.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10", "--out", out,
                                     "--inputs", write_json(w.path("i.json"), frames({"tick": 0, "pause": True})),
                                     "--snapshot-every", "1")
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual([e["name"] for e in events(rows)], ["paused"])
            s = snapshots(rows)[-1]
            self.assertEqual((s["state"], s["sim_tick"], s["time_left_ticks"]), ("paused", 0, 10800))
            self.assertEqual(rows[-1]["state"], "paused")

    def test_ac_p2_42_pause_in_shop_freezes_timer_and_ignores_buy(self):
        sc = dict(SHORT, day={"money": 200, "earned": 200})
        inputs = [{"tick": SHOP_OPEN, "pause": True}, {"tick": SHOP_OPEN + 1, "pause": False, "buy": "oxygen"},
                  {"tick": SHOP_OPEN + 10, "pause": True}]
        with Workdir() as w:
            rows = run_day(w, sc, inputs, every=1)
            self.assertEqual(events(rows, "bought"), [])
            ev = [(e["tick"], e["day"], e["name"]) for e in events(rows) if e["name"] in ("paused", "resumed", "shop_end")]
            self.assertEqual(ev, [(SHOP_OPEN + 1, 1, "paused"), (SHOP_OPEN + 11, 1, "resumed"),
                                  (SHOP_OPEN + 610, 1, "shop_end")])
            s = next(s for s in snapshots(rows) if s["tick"] == SHOP_OPEN + 5)
            self.assertEqual((s["state"], s["phase"], s["time_left_ticks"]), ("paused", "shop", 600))


class FixtureVaCli(unittest.TestCase):
    def test_ac_p2_70_day_scenario_and_cli_validation_exit_2(self):
        bad = [
            {"day": {"money": 300, "earned": 200}},
            {"day": {"money": 100}},                                   # có tiền đầu kỳ nhưng thiếu earned
            {"quan": {"stock": {"ca_loc": 1}}},
            {"quan": {"reputation": 4}},
            {"day": {"day_plan": [{"day": 1, "dishes": {"ca_loc_nuong_trui": 1}, "ingredients": {"ca_loc": 2}}]}},
            {"day": {"day_plan": [{"day": 1, "dishes": {"pho_bo": 1}}]}},
            {"day": {"upgrades": {"oxygen": 3}}},
            {"day": {"upgrades": {"weapon": 1}}},
            {"day": {"bonus": 1}},
            {"quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_keo_nuong",
                                     "order_status": "unfulfillable"}]}},  # món ngoài kế hoạch D1
        ]
        for sc in bad:
            with Workdir() as w:
                code, wrote = code_of(w, sc)
                self.assertEqual(code, 2, sc)
                self.assertFalse(wrote, sc)
        for extra in (("--days", "0"), ("--days", "6"), ("--days", "x")):
            with Workdir() as w:
                self.assertEqual(code_of(w, None, extra)[0], 2, extra)

    def test_ac_p2_71_day_plan_override_recomputes_ingredients(self):
        sc = dict(SHORT, day={"day_plan": [{"day": 1, "dishes": {"lau_mam": 2}}]})
        with Workdir() as w:
            rows = run_day(w, sc, ticks=1, every=1)
            self.assertEqual(events(rows, "day_plan")[0]["data"],
                             {"dishes": {"lau_mam": 2},
                              "ingredients": {"bong_dien_dien": 2, "ca_keo": 2, "ca_linh": 4, "keo_neo": 2}})

    def test_ac_p2_72_rule_conflict_at_quan_open_exit_2(self):
        # khách mẫu giữ chỗ nhưng kho thực lúc mở quán rỗng -> mâu thuẫn -> mã 2, không để lại đầu ra
        sc = {"gather": {"time_left_ticks": 1},
              "quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                      "reserved": {"ca_loc": 1}}]}}
        with Workdir() as w:
            code, wrote = code_of(w, sc)
            self.assertEqual((code, wrote), (2, False))


class HieuNang(unittest.TestCase):
    def test_ac_p2_80_one_day_without_pause_under_20s(self):
        with Workdir() as w:
            t0 = time.perf_counter()
            rows = run_day(w, None, ticks=22200, every=10)
            elapsed = time.perf_counter() - t0
            self.assertEqual((rows[-1]["ticks"], rows[-1]["reason"]), (22200, "days_complete"))
            self.assertLessEqual(elapsed, 20.0)


if __name__ == "__main__":
    unittest.main()
