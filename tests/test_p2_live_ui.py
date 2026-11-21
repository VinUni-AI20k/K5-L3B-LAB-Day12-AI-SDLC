"""P2-08: menu, pause, HUD và Shop trong cửa sổ chơi (chonoi.live). Chỉ dành cho starter Python.

Phần lớn test gọi thẳng LiveGame._tick_once() (không chạy luồng nền) để tất định.
"""

import contextlib
import io
import json
import unittest
import urllib.error
import urllib.request

from chonoi import live
from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.live import LiveGame, LiveServer

TUNING = load_contract()["tuning"]
SHOP = TUNING["shop"]["upgrades"]


def state(game):
    return json.loads(game.state_json())


def names(st):
    return [e["name"] for e in st["events"]]


def quick_day(money=0):
    """Scenario day: gather và quán mỗi pha 1 tick để vào Shop ngay."""
    return {"day": {"money": money, "earned": money},
            "gather": {"time_left_ticks": 1}, "quan": {"time_left_ticks": 1}}


class Menu(unittest.TestCase):
    def test_menu_then_start_day(self):
        game = LiveGame(None, TUNING, {}, 7)
        st = state(game)
        self.assertEqual(st["screen"], "menu")
        self.assertEqual(st["modes"], ["gather", "quan", "day"])
        self.assertEqual(st["days_max"], len(TUNING["day_plan"]))
        self.assertEqual(st["seed"], 7)
        game._tick_once()  # menu: không có sim, không lỗi
        with self.assertRaises(ValueError):
            game.set_input({"move": [1, 0]})

        game.begin({"mode": "day", "days": 2})
        st = state(game)
        self.assertEqual((st["screen"], st["mode"], st["phase"], st["day"], st["days_total"]),
                         ("game", "day", "gather", 1, 2))
        self.assertEqual(names(st), ["day_start", "day_plan", "phase_start"])
        self.assertEqual(st["meta"], TUNING["gather"])
        self.assertFalse(st["fixed_mode"])

        game.to_menu()
        self.assertEqual(state(game)["screen"], "menu")

    def test_start_rejects_bad_body_and_fixed_mode(self):
        game = LiveGame(None, TUNING, {}, 1)
        for body in ({"mode": "shop"}, {"mode": "day", "days": 0},
                     {"mode": "day", "days": len(TUNING["day_plan"]) + 1}, {"mode": "day", "days": True}):
            with self.assertRaises(ValueError, msg=body):
                game.begin(body)
        fixed = LiveGame("gather", TUNING, {}, 1)
        self.assertTrue(state(fixed)["fixed_mode"])
        with self.assertRaises(ValueError):
            fixed.begin({"mode": "quan"})
        with self.assertRaises(ValueError):
            fixed.to_menu()


class Pause(unittest.TestCase):
    def test_pause_freezes_gameplay_and_resume(self):
        game = LiveGame("gather", TUNING, {}, 1)
        game.set_input({"move": [1, 0]})
        game._tick_once()
        game.set_input({"pause": True})
        game._tick_once()
        st = state(game)
        self.assertEqual(st["state"], "paused")
        self.assertEqual(names(st)[-1], "paused")
        frozen = (st["sim_tick"], st["player"]["pos"])
        for _ in range(5):
            game._tick_once()
        st = state(game)
        self.assertEqual((st["sim_tick"], st["player"]["pos"]), frozen)
        self.assertGreater(st["tick"], frozen[0])
        game.set_input({"pause": False})
        game.set_input({"pause": True})
        game._tick_once()
        st = state(game)
        self.assertEqual(st["state"], "playing")
        self.assertIn("resumed", names(st))


class Shop(unittest.TestCase):
    def to_shop(self, money):
        game = LiveGame("day", TUNING, quick_day(money), 1)
        for _ in range(2):
            game._tick_once()
        st = state(game)
        self.assertEqual(st["phase"], "shop")
        self.assertEqual(st["meta"], TUNING["shop"])
        return game

    def test_buy_once_then_shop_done_finishes_day(self):
        price = SHOP["oxygen"][0]["price"]
        game = self.to_shop(price)
        game.set_input({"buy": "oxygen"})
        game._tick_once()
        game._tick_once()  # lệnh mua chỉ dùng một lần
        st = state(game)
        bought = [e for e in st["events"] if e["name"] == "bought"]
        self.assertEqual([e["data"] for e in bought],
                         [{"upgrade": "oxygen", "level": 1, "price": price, "money": 0}])
        self.assertEqual(st["upgrades"]["oxygen"], 1)
        game.set_input({"shop_done": True})
        game._tick_once()
        st = state(game)
        self.assertTrue(st["finished"])
        self.assertEqual(st["reason"], "days_complete")

    def test_buy_without_money_fails(self):
        game = self.to_shop(0)
        game.set_input({"buy": "hp"})
        game._tick_once()
        last = state(game)["events"][-1]
        self.assertEqual((last["name"], last["data"]["reason"]), ("buy_failed", "funds"))

    def test_live_inputs_buy_is_one_shot(self):
        li = LiveInputs()
        li.set(buy="hp")
        self.assertEqual(li.advance().buy, "hp")
        self.assertIsNone(li.advance().buy)


def _post(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        e.close()
        return e.code


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.read()


class Http(unittest.TestCase):
    def test_menu_start_menu_over_http(self):
        server = LiveServer(LiveGame(None, TUNING, {}, 1), port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            self.assertEqual(json.loads(_get(base + "/state"))["screen"], "menu")
            self.assertEqual(_post(base + "/input", {"move": [1, 0]}), 400)
            self.assertEqual(_post(base + "/start", {"mode": "nope"}), 400)
            self.assertEqual(_post(base + "/start", {"mode": "day", "days": 1}), 200)
            self.assertEqual(json.loads(_get(base + "/state"))["mode"], "day")
            self.assertEqual(_post(base + "/input", {"pause": True}), 200)
            self.assertEqual(_post(base + "/input", {"buy": ""}), 400)
            self.assertEqual(_post(base + "/input", {"shop_done": 1}), 400)
            self.assertEqual(_post(base + "/menu", {}), 200)
            self.assertEqual(json.loads(_get(base + "/state"))["screen"], "menu")
            html = _get(base + "/")
            for marker in ("drawMenu", "drawShop", "Tạm dừng", "dayHud"):
                self.assertIn(marker.encode(), html)
        finally:
            server.stop()

    def test_cli_rejects_bad_flags(self):
        for argv in (["--days", "9", "--mode", "day"], ["--scenario", "x.json"], ["--mode", "gather", "--days", "2"]):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(live.main(argv + ["--port", "0"]), 2, argv)


if __name__ == "__main__":
    unittest.main()
