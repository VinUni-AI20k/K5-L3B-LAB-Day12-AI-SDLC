"""Test UI & QA Phase 2 (common-maker): live.py v1.1 (pause, buy, shop_done, --days) và HUD/màn hình vòng ngày."""

import json
import time
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer, main as live_main


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.read()


def _post(url, obj):
    req = urllib.request.Request(
        url, data=json.dumps(obj).encode(), method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        e.close()
        return e.code


class LiveV11ApiTest(unittest.TestCase):
    def test_pause_buy_shop_done_and_v11_state_fields(self):
        c = load_contract()
        tuning = c["tuning"]
        server = LiveServer(LiveGame("gather", tuning, {}, 1, contract=c), port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            # Kiểm tra pause thực dừng sim_tick và resume chạy tiếp
            self.assertEqual(_post(base + "/input", {"pause": True}), 200)
            self.assertEqual(_post(base + "/input", {"pause": False}), 200)
            deadline = time.time() + 2
            st_paused = None
            while time.time() < deadline:
                st_paused = json.loads(_get(base + "/state")[1])
                if st_paused["state"] == "paused":
                    break
                time.sleep(0.03)
            self.assertEqual(st_paused["state"], "paused")
            sim_t0 = st_paused["sim_tick"]
            time.sleep(0.25)
            st_paused2 = json.loads(_get(base + "/state")[1])
            self.assertEqual(st_paused2["sim_tick"], sim_t0, "sim_tick phải đứng yên khi paused")

            # Resume lại
            self.assertEqual(_post(base + "/input", {"pause": True}), 200)
            self.assertEqual(_post(base + "/input", {"pause": False}), 200)
            deadline = time.time() + 2
            while time.time() < deadline:
                st_res = json.loads(_get(base + "/state")[1])
                if st_res["state"] == "playing" and st_res["sim_tick"] > sim_t0:
                    break
                time.sleep(0.03)
            self.assertEqual(st_res["state"], "playing")
            self.assertGreater(st_res["sim_tick"], sim_t0)

            # Kiểm tra buy / shop_done hợp lệ & sai kiểu
            self.assertEqual(_post(base + "/input", {"shop_done": True, "buy": "oxygen"}), 200)
            self.assertEqual(_post(base + "/input", {"shop_done": False}), 200)
            self.assertEqual(_post(base + "/input", {"buy": ""}), 400)
            self.assertEqual(_post(base + "/input", {"pause": "yes"}), 400)

            # Kiểm tra trường v1.1 trong /state và HUD/màn hình trong /
            self.assertEqual(len(st_res["tuning_menu"]), 6)
            self.assertIn("upgrades", st_res["tuning_shop"])
            self.assertEqual(len(st_res["tuning_day_plan"]), 5)

            code, html = _get(base + "/")
            self.assertEqual(code, 200)
            for tok in (
                "sans-serif", "drawGather", "drawQuan", "computeAvailableStock",
                "dishName", "Kho khả dụng", "Thủy quái!", "Hết hơi!",
                "DayIntro", "EveningIntro", "DayResult", "Shop", "Summary",
                "Lẩu mắm", "Cá kèo nướng", "Canh chua cá lóc",
            ):
                self.assertIn(tok.encode("utf-8"), html, tok)
        finally:
            server.stop()


class LiveCliDayValidationTest(unittest.TestCase):
    def test_days_validation_exit_2(self):
        self.assertEqual(live_main(["--mode", "gather", "--days", "2"]), 2)
        self.assertEqual(live_main(["--mode", "day", "--days", "6"]), 2)


if __name__ == "__main__":
    unittest.main()
