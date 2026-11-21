"""Test hộp đen lát 5 (Ticket-02): --mode day, Shop/nâng cấp, pause ở cả ba mode.

Mã AC-P2-06 (vòng ngày + Shop + cấp) và AC-P2-07 (pause). "Ngày ngắn": mẫu gather/quan có time_left_ticks 1
-> gather_end ở tick 1, quan_end ở tick 2, Shop 600 tick -> shop_end ở tick 602 (một Ngày = 602 tick).
"""

import json
import os
import time
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json
from qa_helpers import pending, press, run_case, snap_at

with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json"),
          encoding="utf-8") as _f:
    TUNING = json.load(_f)["tuning"]
SHOP_TICKS = TUNING["shop"]["max_ticks"]
SHORT = {"gather": {"time_left_ticks": 1, "random_fish": False}, "quan": {"time_left_ticks": 1, "random_customers": False}}
SHOP_START = 2  # bước đầu tiên của Shop trong Ngày ngắn


def short_day(**day_block) -> dict:
    sc = json.loads(json.dumps(SHORT))
    if day_block:
        sc["day"] = day_block
    return sc


def run_day(test, scenario=None, inputs=None, ticks=1000, days=None, every=1, seed=1):
    with Workdir() as w:
        args = ["--mode", "day", "--seed", str(seed), "--ticks", str(ticks), "--snapshot-every", str(every),
                "--out", w.path("o.jsonl")]
        if days is not None:
            args += ["--days", str(days)]
        if scenario is not None:
            args += ["--scenario", write_json(w.path("sc.json"), scenario)]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        code, err = run_headless(*args)
        test.assertEqual(code, 0, err)
        return read_jsonl(w.path("o.jsonl"))


def names_at(rows, tick) -> list:
    return [(e["phase"], e["name"]) for e in events(rows) if e["tick"] == tick]


def buy(tick, action) -> dict:
    return {"tick": tick, "buy": action}


class DayFlow(unittest.TestCase):
    def test_ac_p2_06_tick0_cong_bo_ke_hoach_ngay_1(self):
        rows = run_day(self, ticks=0)
        self.assertEqual([r["name"] for r in rows if r["type"] == "event"], ["day_start", "day_plan", "phase_start"])
        plan = events(rows, "day_plan")[0]
        self.assertEqual((plan["tick"], plan["phase"], plan["day"]), (0, "gather", 1))
        self.assertEqual(plan["data"], {"dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
                                        "ingredients": {"ca_loc": 3, "bong_sung": 6}})
        s = snapshots(rows)[0]
        self.assertEqual((s["mode"], s["phase"], s["phase_tick"], s["day"]), ("day", "gather", 0, 1))
        self.assertEqual((s["upgrades"], s["active_upgrades"]), ({}, {}))
        self.assertEqual(s["day_plan"], plan["data"])

    def test_ac_p2_06_cap_ben_mo_quan_cung_tick_voi_kho_ban_giao(self):
        sc = {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False}}
        rows = run_day(self, scenario=sc, inputs=press(0, "interact"), ticks=2)
        self.assertEqual(names_at(rows, 1), [("gather", "gather_end"), ("quan", "phase_start")])
        s = snap_at(rows, 1)
        self.assertEqual((s["phase"], s["phase_tick"], s["stock"]), ("quan", 0, {"bong_sung": 2, "ca_loc": 1}))
        self.assertEqual(snap_at(rows, 2)["phase_tick"], 1)

    def test_ac_p2_06_ngat_van_mo_quan_voi_kho_rong(self):
        player = {"pos": [20, 10], "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 59}
        sc = {"gather": {"player": player, "hold": ["ca_loc"], "random_fish": False}}
        rows = run_day(self, scenario=sc, ticks=2)
        self.assertEqual(names_at(rows, 1)[-2:], [("gather", "gather_end"), ("quan", "phase_start")])
        self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "fainted")
        self.assertEqual(snap_at(rows, 1)["stock"], {})

    def test_ac_p2_06_shop_tu_dong_sau_600_tick_va_ket_thuc_days_complete(self):
        rows = run_day(self, scenario=short_day(), ticks=5000, every=100)
        self.assertEqual(names_at(rows, 2), [("quan", "quan_end"), ("shop", "phase_start")])
        end = SHOP_START + SHOP_TICKS
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "shop_end")], [(end, {"reason": "time"})])
        last = rows[-1]
        self.assertEqual((last["reason"], last["state"], last["ticks"], last["days_completed"]),
                         ("days_complete", "finished", end, 1))

    def test_ac_p2_06_nhieu_ngay_dung_ke_hoach_D1_D5(self):
        rows = run_day(self, scenario=short_day(), ticks=10_000, days=5, every=1000)
        plans = events(rows, "day_plan")
        self.assertEqual([e["day"] for e in plans], [1, 2, 3, 4, 5])
        want = {p["day"]: {"dishes": p["dishes"], "ingredients": p["ingredients"]} for p in TUNING["day_plan"]}
        for e in plans:
            self.assertEqual(e["data"], want[e["day"]], e["day"])
        day_len = SHOP_START + SHOP_TICKS
        self.assertEqual([e["tick"] for e in events(rows, "day_start")], [day_len * i for i in range(5)])
        self.assertEqual((rows[-1]["days_completed"], rows[-1]["ticks"]), (5, 5 * day_len))

    def test_ac_p2_06_mot_ngay_day_du_22200_tick_duoi_20s(self):
        t0 = time.perf_counter()
        rows = run_day(self, ticks=30_000, every=1000)
        elapsed = time.perf_counter() - t0
        self.assertEqual((rows[-1]["reason"], rows[-1]["ticks"]), ("days_complete", 22_200))
        self.assertEqual([e["tick"] for e in events(rows, "phase_start")], [0, 10_800, 21_600])
        self.assertLess(elapsed, 20, f"một Ngày chạy {elapsed:.1f}s")

    def test_ac_p2_06_cung_seed_giong_tung_byte(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), short_day())
            for i in (1, 2):
                code, err = run_headless("--mode", "day", "--seed", "5", "--days", "2", "--ticks", "2000",
                                         "--scenario", sc, "--out", w.path(f"d{i}.jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("d1.jsonl"), "rb") as a, open(w.path("d2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


class Shop(unittest.TestCase):
    def test_ac_p2_06_mua_tru_money_giu_earned_cap_hien_ngay_hieu_luc_ngay_ke(self):
        sc = short_day(money=500, earned=500)
        inputs = [buy(2, "oxygen"), buy(3, "oxygen"), buy(4, "hp"), buy(5, "weapon"), {"tick": 6, "shop_done": True}]
        rows = run_day(self, scenario=sc, inputs=inputs, ticks=20, days=2)
        got = [(e["tick"], e["name"], e["data"]) for e in events(rows) if e["name"] in ("bought", "buy_failed")]
        self.assertEqual(got, [
            (3, "bought", {"upgrade": "oxygen", "level": 1, "price": 200, "money": 300}),
            (4, "buy_failed", {"action": "oxygen", "reason": "funds"}),
            (5, "bought", {"upgrade": "hp", "level": 1, "price": 250, "money": 50}),
            (6, "buy_failed", {"action": "weapon", "reason": "unknown"}),
        ])
        s3 = snap_at(rows, 3)
        self.assertEqual((s3["phase"], s3["upgrades"], s3["active_upgrades"]), ("shop", {"oxygen": 1}, {}))
        self.assertEqual(s3["time_left_ticks"], SHOP_TICKS - 1)
        s5 = snap_at(rows, 5)
        self.assertEqual((s5["money"], s5["earned"], s5["score"]), (50, 500, 800))
        self.assertEqual(names_at(rows, 7), [("shop", "shop_end"), ("gather", "day_start"),
                                             ("gather", "day_plan"), ("gather", "phase_start")])
        self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "done"})
        s7 = snap_at(rows, 7)
        self.assertEqual((s7["day"], s7["phase"], s7["active_upgrades"]), (2, "gather", {"hp": 1, "oxygen": 1}))
        p = s7["player"]
        self.assertEqual((p["oxygen_max_ticks"], p["oxygen_ticks"], p["hp_max"], p["hp"]), (2700, 2700, 4, 4))

    def test_ac_p2_06_du_dung_gia_van_mua_duoc(self):
        rows = run_day(self, scenario=short_day(money=200, earned=200), inputs=[buy(2, "oxygen")], ticks=4)
        self.assertEqual(events(rows, "bought")[0]["data"]["money"], 0)

    def test_ac_p2_06_cap_toi_da_thi_max_level(self):
        rows = run_day(self, scenario=short_day(money=999, earned=999, upgrades={"oxygen": 2}),
                       inputs=[buy(2, "oxygen")], ticks=4)
        self.assertEqual([e["data"] for e in events(rows, "buy_failed")], [{"action": "oxygen", "reason": "max_level"}])
        self.assertEqual(snap_at(rows, 3)["money"], 999)

    def test_ac_p2_06_buy_ngoai_shop_bi_bo_qua(self):
        rows = run_day(self, scenario=short_day(money=999, earned=999), inputs=[buy(0, "oxygen")], ticks=4)
        self.assertEqual([e for e in events(rows) if e["name"] in ("bought", "buy_failed")], [])

    @pending("lát 4 (_pay)")
    def test_ac_p2_06_tien_va_uy_tin_giu_qua_ngay(self):
        c = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating",
             "order_status": "served", "eat_ticks_left": 300, "base_price": 60, "tip": 12}
        sc = short_day()
        sc["quan"]["customers"] = [c]
        rows = run_day(self, scenario=sc, ticks=1000, days=2, every=1000)
        s = snap_at(rows, SHOP_START + SHOP_TICKS)
        self.assertEqual((s["day"], s["money"], s["earned"]), (2, 72, 72))
        self.assertAlmostEqual(s["reputation"], 3.2, places=2)


class Pause(unittest.TestCase):
    def test_ac_p2_07_pause_gather_dung_dong_ho_va_bo_qua_canh(self):
        inputs = [{"tick": 5, "pause": True}, {"tick": 6, "pause": False},
                  {"tick": 7, "interact": True},  # bấm E khi đang pause (đứng ở bến) -> bỏ qua
                  {"tick": 10, "pause": True}, {"tick": 11, "pause": False}]
        rows, _ = run_case(self, "gather", inputs=inputs, ticks=20)
        self.assertEqual([(e["tick"], e["name"]) for e in events(rows)], [(6, "paused"), (11, "resumed")])
        s = snap_at(rows, 8)
        self.assertEqual((s["state"], s["sim_tick"], s["phase_tick"]), ("paused", 5, 5))
        self.assertEqual(s["time_left_ticks"], snap_at(rows, 5)["time_left_ticks"])
        end = rows[-1]
        self.assertEqual((end["ticks"], end["sim_tick"], end["reason"]), (20, 15, "tick_limit"))

    def test_ac_p2_07_pause_quan_doi_lich_khach(self):
        inputs = [{"tick": 0, "pause": True}, {"tick": 1, "pause": False}, {"tick": 200, "pause": True}]
        rows, _ = run_case(self, "quan", scenario={"stock": {"ca_loc": 1}}, inputs=inputs, ticks=321, every=10)
        self.assertEqual([e["tick"] for e in events(rows, "customer_arrived")], [320])

    def test_ac_p2_07_pause_trong_shop_bo_qua_buy_va_mang_day(self):
        inputs = [{"tick": 2, "pause": True}, {"tick": 3, "pause": False}, buy(4, "oxygen"),
                  {"tick": 5, "pause": True}]
        rows = run_day(self, scenario=short_day(money=500, earned=500), inputs=inputs, ticks=8)
        p = events(rows, "paused")[0]
        self.assertEqual((p["tick"], p["phase"], p["day"]), (3, "shop", 1))
        self.assertEqual(events(rows, "bought"), [])
        self.assertEqual(events(rows, "resumed")[0]["tick"], 6)
        self.assertEqual(snap_at(rows, 6)["time_left_ticks"], SHOP_TICKS - 1)


class Validation(unittest.TestCase):
    def _exit(self, *args, scenario=None):
        with Workdir() as w:
            extra = ["--scenario", write_json(w.path("sc.json"), scenario)] if scenario is not None else []
            code, _ = run_headless(*args, "--seed", "1", "--ticks", "0", *extra, "--out", w.path("o.jsonl"))
            return code, os.path.exists(w.path("o.jsonl"))

    def test_ac_p2_06_co_days_sai_ma_2(self):
        for args in (("--mode", "day", "--days", "0"), ("--mode", "day", "--days", "6"),
                     ("--mode", "gather", "--days", "1")):
            self.assertEqual(self._exit(*args), (2, False), args)

    def test_ac_p2_06_scenario_day_mau_thuan_ma_2(self):
        bad = [{"quan": {"stock": {"ca_loc": 1}}}, {"quan": {"reputation": 4}},
               {"day": {"money": 300, "earned": 100}}, {"day": {"money": 100}},
               {"day": {"upgrades": {"oxygen": 3}}}, {"day": {"upgrades": {"rocket": 1}}},
               {"day": {"day_plan": [{"day": 1, "dishes": {"pho_bo": 1}}]}},
               {"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 3}}]}},
               {"river": {}}]
        for sc in bad:
            self.assertEqual(self._exit("--mode", "day", scenario=sc), (2, False), sc)

    def test_ac_p2_06_scenario_day_hop_le(self):
        ok = {"day": {"money": 200, "earned": 200, "reputation": 4.0, "upgrades": {"hp": 1},
                      "day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 2}}]},
              "gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False}}
        self.assertEqual(self._exit("--mode", "day", scenario=ok), (0, True))


if __name__ == "__main__":
    unittest.main()
