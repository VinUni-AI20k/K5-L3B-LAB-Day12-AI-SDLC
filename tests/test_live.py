"""Test cửa sổ chơi trực tiếp (chonoi.live). Chỉ dành cho starter Python: nhóm đổi ngôn ngữ thì xóa file này."""

import json
import os
import tempfile
import time
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer


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


class LiveInventoryPersistenceTest(unittest.TestCase):
    def test_gather_writes_inventory_immediately(self):
        tuning = load_contract()["tuning"]
        with tempfile.TemporaryDirectory() as d:
            inventory_path = os.path.join(d, "inventory.json")
            with open(inventory_path, "w", encoding="utf-8") as f:
                json.dump({"items": {"ca_loc": 2}}, f)
            scenario = {
                "player": {"pos": [12, 0]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
                "random_fish": False,
            }
            game = LiveGame("gather", tuning, scenario, 1, inventory_out=inventory_path)
            game.inputs.set(interact=True)
            game._tick_once()
            with open(inventory_path, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 1, "ca_loc": 2}})

            game.restart()
            game.inputs.set(interact=True)
            game._tick_once()
            with open(inventory_path, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 2, "ca_loc": 2}})


if __name__ == "__main__":
    unittest.main()
