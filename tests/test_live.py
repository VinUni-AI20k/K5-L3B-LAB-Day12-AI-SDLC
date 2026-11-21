"""Test cửa sổ chơi trực tiếp (chonoi.live). Chỉ dành cho starter Python: nhóm đổi ngôn ngữ thì xóa file này."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.live import LiveGame, LiveServer
from chonoi.scenario import load_scenario


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


class LiveServerTest(unittest.TestCase):
    def test_quan_shows_cook_hint_and_persistent_shortage(self):
        tuning = load_contract()["tuning"]
        game = LiveGame("quan", tuning, {"player": {"pos": [2, 8]}}, 1, {"ca_loc": 1})
        self.assertNotIn("missing_ingredients", json.loads(game.state_json()))
        for _ in range(tuning["quan"]["first_customer_tick"]):
            game._tick_once()
        self.assertEqual(json.loads(game.state_json())["interact_target"], {"id": "B1", "action": "cook_started"})
        game.set_input({"interact": True})
        game._tick_once()
        self.assertEqual(json.loads(game.state_json())["stoves"][0]["state"], "cooking")

        empty = LiveGame("quan", tuning, {}, 1)
        for _ in range(tuning["quan"]["first_customer_tick"] + 3 * tuning["tick_hz"]):
            empty._tick_once()
        self.assertEqual(json.loads(empty.state_json())["missing_ingredients"], {"ca_loc": 1})

    def test_quan_scenario_rejects_active_stove_without_dish(self):
        tuning = load_contract()["tuning"]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "quan.json"
            path.write_text(json.dumps({"quan": {"stoves": [{"id": "B1", "state": "cooking"}]}}), encoding="utf-8")
            with self.assertRaisesRegex(BadInput, r"stoves\.B1.*dish"):
                load_scenario(path, "quan", tuning)

    def test_state_input_and_clean_stop(self):
        tuning = load_contract()["tuning"]
        server = LiveServer(LiveGame("gather", tuning, {}, 1), port=0)  # cổng ngẫu nhiên
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            code, body = _get(base + "/state")
            self.assertEqual(code, 200)
            st = json.loads(body)
            self.assertIn("tick", st)
            self.assertEqual(st["mode"], "gather")
            self.assertEqual(st["player"]["pos"], [2, 0])
            self.assertEqual(_post(base + "/input", {"move": [1, 0], "interact": False, "catch": False}), 200)
            self.assertEqual(_post(base + "/input", {"move": [5, 0]}), 400)
            code, html = _get(base + "/")
            self.assertEqual(code, 200)
            self.assertIn(b"<canvas", html)
            deadline = time.time() + 3
            while time.time() < deadline:
                st2 = json.loads(_get(base + "/state")[1])
                if st2["tick"] > st["tick"] + 3 and st2["player"]["pos"][0] > st["player"]["pos"][0]:
                    break
                time.sleep(0.05)
            self.assertGreater(st2["tick"], st["tick"], "mô phỏng phải chạy nền")
            self.assertGreater(st2["player"]["pos"][0], st["player"]["pos"][0], "input phải tác động tới sim")
        finally:
            server.stop()
        self.assertFalse(server.game._thread.is_alive())
        self.assertFalse(server._thread.is_alive())


if __name__ == "__main__":
    unittest.main()
