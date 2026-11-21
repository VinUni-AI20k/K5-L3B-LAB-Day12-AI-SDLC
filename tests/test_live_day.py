"""Cửa sổ chơi `chonoi.live --mode day` (Phase 4, AC-P4-11): server cho demo chơi trọn một Ngày.

Kiểm phần server (không kiểm hình vẽ): `/state` ghi `mode` = pha đang chạy + `day_mode`, sự kiện tick 0 (day_start,
day_plan) có sẵn, nút `buy` / `shop_done` / `pause` đi tới DaySim, `/day.js` được phục vụ và index.html nạp nó.
Ngày ngắn: mẫu gather/quan `time_left_ticks: 1` -> vào Shop sau 2 tick; có sẵn 300 tiền để mua Bình oxy cấp 1.
"""

import json
import time
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer

SHORT_DAY = {"day": {"money": 300, "earned": 300},
             "gather": {"time_left_ticks": 1, "random_fish": False},
             "quan": {"time_left_ticks": 1, "random_customers": False}}


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.read()


def _post(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        e.close()
        return e.code


class LiveDayTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.server = LiveServer(LiveGame("day", self.tuning, SHORT_DAY, 1, days=1), port=0)
        self.server.start()
        self.base = f"http://127.0.0.1:{self.server.port}"

    def tearDown(self):
        self.server.stop()

    def state(self):
        return json.loads(_get(self.base + "/state")[1])

    def wait(self, cond, timeout=5):
        deadline = time.time() + timeout
        while time.time() < deadline:
            st = self.state()
            if cond(st):
                return st
            time.sleep(0.03)
        self.fail("hết giờ chờ trạng thái: " + json.dumps(self.state(), ensure_ascii=False)[:300])

    def names(self, st):
        return [e["name"] for e in st["events"]]

    def test_ac_p4_11_mot_ngay_qua_shop_mua_va_dong(self):
        st = self.state()  # Ngày ngắn chạy rất nhanh: lúc đọc có thể đã sang quán, nên kiểm theo sự kiện tick 0
        self.assertTrue(st["day_mode"])
        self.assertEqual((st["mode"], st["day"], st["days_total"]), (st["phase"], 1, 1))
        first = [(e["tick"], e["phase"], e["name"]) for e in st["events"][:3]]
        self.assertEqual(first, [(0, "gather", "day_start"), (0, "gather", "day_plan"), (0, "gather", "phase_start")])
        if st["mode"] in ("gather", "quan"):
            self.assertEqual(st["meta"], self.tuning[st["mode"]])
        st = self.wait(lambda s: s["mode"] == "shop")
        self.assertEqual(st["shop_tuning"], self.tuning["shop"])
        self.assertEqual(_post(self.base + "/input", {"buy": "oxygen"}), 200)
        st = self.wait(lambda s: "bought" in self.names(s))
        bought = [e for e in st["events"] if e["name"] == "bought"][0]["data"]
        price = self.tuning["shop"]["upgrades"]["oxygen"][0]["price"]
        self.assertEqual(bought, {"upgrade": "oxygen", "level": 1, "price": price, "money": 300 - price})
        self.assertEqual(st["upgrades"], {"oxygen": 1})
        self.assertEqual(_post(self.base + "/input", {"shop_done": True}), 200)
        self.assertEqual(_post(self.base + "/input", {"shop_done": False}), 200)
        st = self.wait(lambda s: s["finished"])
        self.assertEqual((st["reason"], st["days_completed"]), ("days_complete", 1))
        self.assertIn("shop_end", self.names(st))

    def test_pause_qua_live(self):
        self.assertEqual(_post(self.base + "/input", {"pause": True}), 200)
        self.assertEqual(_post(self.base + "/input", {"pause": False}), 200)
        st = self.wait(lambda s: s["state"] == "paused")
        t0 = st["sim_tick"]
        time.sleep(0.2)
        self.assertEqual(self.state()["sim_tick"], t0, "pause: sim_tick đứng yên")

    def test_input_sai_va_file_tinh(self):
        self.assertEqual(_post(self.base + "/input", {"buy": ""}), 400)
        self.assertEqual(_post(self.base + "/input", {"pause": "yes"}), 400)
        code, js = _get(self.base + "/day.js")
        self.assertEqual(code, 200)
        self.assertIn(b"day_mode", js)
        self.assertIn(b'<script src="day.js">', _get(self.base + "/")[1])
        code, js = _get(self.base + "/scene.js")   # cảnh nền sông phù sa / nhà bè đêm
        self.assertEqual(code, 200)
        self.assertIn(b"window.SCENE", js)
        self.assertIn(b'<script src="scene.js">', _get(self.base + "/")[1])


if __name__ == "__main__":
    unittest.main()
