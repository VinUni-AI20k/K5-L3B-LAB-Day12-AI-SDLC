"""Lát 3 (C), Phase 2: vòng ngày `--mode day` (DaySession) và Shop (ShopSim). Ticket-02 mục 2, 4.2-4.5."""

import json
import os
import time
import unittest

from helpers import ROOT, Workdir, run_headless, write_json
from chonoi.inputs import InputState
from chonoi.shop import ShopSim

with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
    TUNING = json.load(f)["tuning"]

DAY_TICKS = 10800 + 10800 + 600  # gather + quan + Shop, không pause


def rows(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def events(rs, *names):
    return [r for r in rs if r["type"] == "event" and (not names or r["name"] in names)]


def last_snap(rs):
    return [r for r in rs if r["type"] == "snapshot"][-1]


class DayLoop(unittest.TestCase):
    def day(self, w, *args, scenario=None, frames=None, ticks=DAY_TICKS):
        out = w.path("out.jsonl")
        cmd = ["--mode", "day", "--seed", "1", "--ticks", str(ticks), "--out", out, "--snapshot-every", "600"]
        if scenario is not None:
            cmd += ["--scenario", write_json(w.path("sc.json"), scenario)]
        if frames is not None:
            cmd += ["--inputs", write_json(w.path("in.json"), {"frames": frames})]
        code, err = run_headless(*cmd, *args)
        self.assertEqual(code, 0, err)
        return rows(out)

    def test_mot_ngay_khong_input_dung_thu_tu_pha_va_tick(self):
        with Workdir() as w:
            t0 = time.monotonic()
            rs = self.day(w)
            self.assertLess(time.monotonic() - t0, 20)  # một Ngày không pause chạy headless dưới 20 s
        flow = [(r["tick"], r["phase"], r["day"], r["name"])
                for r in events(rs, "day_start", "day_plan", "phase_start", "gather_end", "quan_end", "shop_end")]
        self.assertEqual(flow, [
            (0, "gather", 1, "day_start"), (0, "gather", 1, "day_plan"), (0, "gather", 1, "phase_start"),
            (10800, "gather", 1, "gather_end"), (10800, "quan", 1, "phase_start"),
            (21600, "quan", 1, "quan_end"), (21600, "shop", 1, "phase_start"),
            (22200, "shop", 1, "shop_end"),
        ])
        self.assertEqual(rs[0]["name"], "day_start")  # event tick 0 ghi trước snapshot tick 0
        self.assertEqual(events(rs, "day_plan")[0]["data"],
                         {"dishes": TUNING["day_plan"][0]["dishes"], "ingredients": TUNING["day_plan"][0]["ingredients"]})
        end = rs[-1]
        self.assertEqual((end["reason"], end["days_completed"], end["ticks"]), ("days_complete", 1, DAY_TICKS))

    def test_snapshot_doi_pha_ghi_pha_moi_phase_tick_0(self):
        with Workdir() as w:
            rs = self.day(w, ticks=10800)
        s = last_snap(rs)
        self.assertEqual((s["tick"], s["phase"], s["phase_tick"], s["day"], s["mode"]), (10800, "quan", 0, 1, "day"))
        for key in ("day_plan", "upgrades", "active_upgrades", "stock", "customers"):
            self.assertIn(key, s)

    def test_hai_ngay_ngay_2_mo_ngay_khi_shop_dong(self):
        with Workdir() as w:
            rs = self.day(w, "--days", "2", ticks=2 * DAY_TICKS)
        d2 = [(r["tick"], r["day"], r["name"]) for r in events(rs, "day_start", "day_plan") if r["day"] == 2]
        self.assertEqual(d2, [(DAY_TICKS, 2, "day_start"), (DAY_TICKS, 2, "day_plan")])
        self.assertEqual(events(rs, "day_plan")[1]["data"]["dishes"], TUNING["day_plan"][1]["dishes"])
        self.assertEqual((rs[-1]["reason"], rs[-1]["days_completed"]), ("days_complete", 2))

    def test_het_tick_truoc_khi_xong_ngay(self):
        with Workdir() as w:
            rs = self.day(w, ticks=100)
        self.assertEqual((rs[-1]["reason"], rs[-1]["days_completed"], rs[-1]["state"]), ("tick_limit", 0, "playing"))

    def test_cap_ben_mang_hang_vao_quan_khach_goi_mon_ke_hoach(self):
        sc = {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False}}
        with Workdir() as w:
            rs = self.day(w, scenario=sc, frames=[{"tick": 0, "interact": True}], ticks=121)
        self.assertEqual([(r["tick"], r["data"]["reason"]) for r in events(rs, "gather_end")], [(1, "docked")])
        arrived = events(rs, "customer_arrived")
        self.assertEqual([r["tick"] for r in arrived], [121])  # phase_tick 120 của quán mở ở tick 1
        self.assertIn(arrived[0]["data"]["dish_id"], TUNING["day_plan"][0]["dishes"])

    def test_mua_nang_cap_hieu_luc_tu_ngay_ke(self):
        # Cập bến ngay -> quán chạy hết 10.800 bước (tick 2..10801) -> Shop mở ở tick 10801.
        sc = {"day": {"money": 450, "earned": 450}, "gather": {"random_fish": False}}
        frames = [{"tick": 0, "interact": True},
                  {"tick": 10801, "buy": "oxygen"},          # 450 >= 200: mua cấp 1
                  {"tick": 10802, "buy": "oxygen"},          # 250 < 400: funds
                  {"tick": 10803, "buy": "weapon"},          # mở rộng chưa bật: unknown
                  {"tick": 10804, "shop_done": True}]
        with Workdir() as w:
            rs = self.day(w, "--days", "2", scenario=sc, frames=frames, ticks=10806)
        shop = [(r["tick"], r["name"], r["data"]) for r in events(rs, "bought", "buy_failed", "shop_end")]
        self.assertEqual(shop, [
            (10802, "bought", {"upgrade": "oxygen", "level": 1, "price": 200, "money": 250}),
            (10803, "buy_failed", {"action": "oxygen", "reason": "funds"}),
            (10804, "buy_failed", {"action": "weapon", "reason": "unknown"}),
            (10805, "shop_end", {"reason": "done"}),
        ])
        s = last_snap(rs)  # Ngày 2 đã mở ở tick 10805
        self.assertEqual((s["day"], s["phase"], s["money"], s["earned"]), (2, "gather", 250, 450))
        self.assertEqual((s["upgrades"], s["active_upgrades"]), ({"oxygen": 1}, {"oxygen": 1}))
        self.assertEqual(s["player"]["oxygen_max_ticks"], 2700)  # 45 s

    def test_pause_dung_dong_ho_shop(self):
        sc = {"gather": {"random_fish": False}}
        frames = [{"tick": 0, "interact": True},
                  {"tick": 10801, "pause": True}, {"tick": 10802, "pause": False},
                  {"tick": 10900, "pause": True}]
        with Workdir() as w:
            rs = self.day(w, scenario=sc, frames=frames, ticks=11000)
        self.assertEqual([(r["tick"], r["name"]) for r in events(rs, "paused", "resumed")],
                         [(10802, "paused"), (10901, "resumed")])
        s = last_snap(rs)
        self.assertEqual(s["phase"], "shop")
        self.assertEqual(s["phase_tick"], 11000 - 10801 - 99)  # 99 bước pause (10802..10900) không tính
        self.assertEqual(s["sim_tick"], 11000 - 99)


class Inp(InputState):
    def __init__(self, buy=None, done=False):
        super().__init__((0.0, 0.0), set(), {"shop_done"} if done else set(), buy)


class Shop(unittest.TestCase):
    def shop(self, money, upgrades=None, stock=None):
        return ShopSim(TUNING, stock or {}, {"money": money, "earned": money, "reputation": 3.0}, upgrades or {})

    def test_du_dung_gia_van_mua(self):
        s = self.shop(200)
        self.assertEqual(s.step(Inp("oxygen")), [("bought", {"upgrade": "oxygen", "level": 1, "price": 200, "money": 0})])
        self.assertEqual((s.money, s.earned, s.upgrades), (0, 200, {"oxygen": 1}))

    def test_da_toi_da(self):
        s = self.shop(1000, upgrades={"hp": 2})
        self.assertEqual(s.step(Inp("hp")), [("buy_failed", {"action": "hp", "reason": "max_level"})])
        self.assertEqual((s.money, s.upgrades), (1000, {"hp": 2}))

    def test_buy_truoc_shop_done_cung_buoc(self):
        s = self.shop(250)
        self.assertEqual([n for n, _ in s.step(Inp("hp", done=True))], ["bought", "shop_end"])
        self.assertTrue(s.done)

    def test_tu_dong_sau_600_buoc_va_snapshot_kho_du(self):
        s = self.shop(0, stock={"ca_loc": 2, "bong_sung": 0})
        self.assertEqual(s.snapshot(), {"stock": {"ca_loc": 2}})
        for _ in range(599):
            self.assertEqual(s.step(Inp()), [])
        self.assertEqual(s.step(Inp()), [("shop_end", {"reason": "time"})])
        self.assertEqual((s.phase_tick, s.time_left_ticks, s.reason), (600, 0, "time"))


if __name__ == "__main__":
    unittest.main()
