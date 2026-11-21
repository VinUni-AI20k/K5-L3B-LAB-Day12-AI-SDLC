"""TV5 · Phase 2: lớp màn hình vòng ngày của cửa sổ chơi (chonoi.live_day) trên DaySim thật của TV4,
cùng menu/pause của chonoi.live. Không thay test headless `--mode day` (tests/test_day_cycle.py)."""

import json
import time
import unittest
import urllib.request

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.live import LIVE_BUTTONS, LiveGame, LiveServer
from chonoi.live_day import INTRO_AUTO_TICKS, LiveDaySession

DOCK = {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False}}


def _tuning():
    return load_contract()["tuning"]


class Driver:
    def __init__(self, scenario=None, days=2):
        self.s = LiveDaySession(_tuning(), scenario or {}, 1, days)
        self.li = LiveInputs(LIVE_BUTTONS)

    def step(self, buy=None, **buttons):
        if buttons or buy:
            self.li.set(buy=buy, **buttons)
        rows = self.s.step(self.li.advance())
        if buttons:
            self.li.set(**{k: False for k in buttons})
        return [r["name"] for r in rows], rows

    def screen(self):
        return self.s.snapshot()["screen"]

    def until(self, screen, limit=30000):
        for _ in range(limit):
            if self.screen() == screen:
                return
            self.step()
        raise AssertionError(f"không tới {screen}")


class LiveDayScreensTest(unittest.TestCase):
    def test_intro_holds_sim_then_auto_after_4s(self):
        d = Driver()
        self.assertEqual([r["name"] for r in d.s.initial_events()], ["day_start", "day_plan", "phase_start"])
        t0 = d.s.snapshot()["time_left_ticks"]
        for _ in range(INTRO_AUTO_TICKS - 1):
            d.step()
        snap = d.s.snapshot()
        self.assertEqual((snap["screen"], snap["time_left_ticks"], snap["sim_tick"]), ("day_intro", t0, 0))
        d.step()
        self.assertEqual(d.screen(), "gather")

    def test_key_skips_intro(self):
        d = Driver()
        d.step(**{"continue": True})
        self.assertEqual(d.screen(), "gather")

    def test_dock_evening_intro_uses_real_handover(self):
        d = Driver(DOCK)
        d.step(**{"continue": True})
        names, rows = d.step(interact=True)  # ở bến: cập bến ngay
        self.assertEqual(names[:2], ["gather_end", "phase_start"])
        snap = d.s.snapshot()
        self.assertEqual(snap["screen"], "evening_intro")
        self.assertEqual(snap["phase"], "quan")
        self.assertEqual(snap["handover"], {"bong_sung": 2, "ca_loc": 1})
        self.assertEqual(snap["stock"], {"bong_sung": 2, "ca_loc": 1})
        self.assertEqual(snap["cookable"], {"ca_loc_nuong_trui": 1, "goi_bong_sung": 1})
        tl = snap["time_left_ticks"]
        d.step()
        self.assertEqual(d.s.snapshot()["time_left_ticks"], tl, "màn chờ không bước quán")
        d.step(**{"continue": True})
        self.assertEqual(d.screen(), "quan")

    def test_full_day_result_shop_upgrade_and_summary(self):
        d = Driver({"day": {"money": 200, "earned": 200}, **DOCK}, days=2)
        d.step(**{"continue": True})
        d.step(interact=True)
        d.step(**{"continue": True})
        d.until("day_result")
        snap = d.s.snapshot()
        self.assertEqual(snap["phase"], "shop")
        self.assertIn("served", snap["result"])
        d.step(**{"continue": True})
        self.assertEqual(d.screen(), "shop")
        names, rows = d.step(buy="oxygen")
        self.assertEqual(names, ["bought"])
        money = rows[0]["data"]["money"]
        snap = d.s.snapshot()
        self.assertEqual(snap["upgrades"], {"oxygen": 1})
        self.assertEqual(snap["active_upgrades"], {})
        names, rows = d.step(shop_done=True)
        self.assertEqual(names[:3], ["shop_end", "day_start", "day_plan"])
        snap = d.s.snapshot()
        self.assertEqual((snap["screen"], snap["day"], snap["days_completed"]), ("day_intro", 2, 1))
        self.assertEqual(snap["active_upgrades"], {"oxygen": 1})
        self.assertEqual(snap["player"]["oxygen_max_ticks"], 2700)
        self.assertEqual(snap["money"], money)
        # Ngày cuối chỉ xong khi Shop đóng
        d.step(**{"continue": True})
        d.step(interact=True)
        d.step(**{"continue": True})
        d.until("day_result")
        d.step(**{"continue": True})
        self.assertFalse(d.s.done)
        d.step(shop_done=True)
        self.assertTrue(d.s.done)
        snap = d.s.snapshot()
        self.assertEqual(snap["screen"], "summary")
        self.assertEqual(len(snap["summary"]["history"]), 2)
        self.assertEqual(snap["summary"]["score"], snap["earned"] + 100 * int(snap["reputation"]))

    def test_vendor_sell_and_buy_for_next_evening(self):
        d = Driver({"day": {"money": 100, "earned": 100}, **DOCK}, days=2)
        d.step(**{"continue": True})
        d.step(interact=True)
        d.s.core.sim.shift.random_customers = False  # giữ nguyên kho dư để thử bán
        d.step(**{"continue": True})
        d.until("day_result")
        d.step(**{"continue": True})
        sim = d.s.sim
        self.assertEqual(d.s.snapshot()["stock"], {"bong_sung": 2, "ca_loc": 1})
        _, rows = d.step(buy="sell:ca_loc")
        self.assertEqual(rows[0]["name"], "vendor_trade")
        self.assertEqual(rows[0]["data"], {"action": "sell", "kind": "ca_loc", "price": 20, "money": 120})
        self.assertEqual((sim.money, sim.earned), (120, 120))
        _, rows = d.step(buy="sell:ca_loc")
        self.assertEqual(rows[0]["data"], {"action": "sell:ca_loc", "reason": "out_of_stock"})
        _, rows = d.step(buy="buy:ca_keo")  # floor(10 × 1.5) = 15
        self.assertEqual(rows[0]["data"], {"action": "buy", "kind": "ca_keo", "price": 15, "money": 105})
        self.assertEqual(sim.earned, 120)
        _, rows = d.step(buy="buy:ca_ho")
        self.assertEqual(rows[0]["data"]["reason"], "unknown")
        d.step(shop_done=True)
        d.step(**{"continue": True})
        _, rows = d.step(interact=True)
        end = [r for r in rows if r["name"] == "gather_end"][0]
        self.assertNotIn("ca_keo", end["data"]["inventory"]["items"])  # hàng Chợ tách khỏi gather_end
        snap = d.s.snapshot()
        self.assertEqual(snap["vendor_delivery"], {"ca_keo": 1})
        self.assertEqual(snap["stock"].get("ca_keo"), 1)


class LiveServerDayTest(unittest.TestCase):
    def _get(self, base):
        with urllib.request.urlopen(base + "/state", timeout=5) as r:
            return json.loads(r.read())

    def _post(self, base, path, obj=None):
        req = urllib.request.Request(base + path, data=json.dumps(obj or {}).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status

    def test_menu_start_and_pause_freezes_timers(self):
        server = LiveServer(LiveGame("day", _tuning(), {}, 1, days=1), port=0)
        server.start()
        base = f"http://127.0.0.1:{server.port}"
        try:
            self.assertFalse(self._get(base)["started"])
            time.sleep(0.2)
            self.assertEqual(self._get(base)["tick"], 0, "menu chính chưa chạy mô phỏng")
            self._post(base, "/start")
            self._post(base, "/input", {"continue": True})
            self._post(base, "/input", {"continue": False})
            deadline = time.time() + 3
            while time.time() < deadline and self._get(base)["screen"] != "gather":
                time.sleep(0.05)
            self._post(base, "/input", {"pause": True})
            self._post(base, "/input", {"pause": False})
            time.sleep(0.15)
            a = self._get(base)
            self.assertEqual(a["state"], "paused")
            time.sleep(0.4)
            b = self._get(base)
            self.assertEqual((a["time_left_ticks"], a["sim_tick"]), (b["time_left_ticks"], b["sim_tick"]))
            self.assertGreater(b["tick"], a["tick"], "tick ngoài vẫn tăng khi pause")
            self.assertIn("paused", [e["name"] for e in b["events"]])
            self._post(base, "/input", {"pause": True})
            time.sleep(0.2)
            c = self._get(base)
            self.assertEqual(c["state"], "playing")
            self.assertLess(c["time_left_ticks"], b["time_left_ticks"])
            self.assertEqual(self._post(base, "/menu"), 200)
            self.assertFalse(self._get(base)["started"])
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
