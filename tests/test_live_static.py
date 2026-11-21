"""Test máy chủ live (ADR-0001): file tĩnh của client, mock, chặn thoát khỏi chonoi/web/, nút v1.1 (pause/shop_done/buy)."""

import glob
import json
import os
import re
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import WEB_DIR, LiveGame, LiveServer


def _get(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        e.close()
        return e.code, "", b""


def _post(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        e.close()
        return e.code


class LiveStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LiveServer(LiveGame("gather", load_contract()["tuning"], {}, 1), port=0)
        cls.server.start()
        cls.base = f"http://127.0.0.1:{cls.server.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_index_scripts_all_served(self):
        code, _, html = _get(self.base + "/")
        self.assertEqual(code, 200)
        srcs = re.findall(rb'<script src="([^"]+)"', html)
        self.assertIn(b"js/main.js", srcs)
        self.assertGreaterEqual(len(srcs), 10)
        for src in srcs:
            code, ctype, body = _get(f"{self.base}/{src.decode()}")
            self.assertEqual(code, 200, src)
            self.assertTrue(ctype.startswith("text/javascript"), (src, ctype))
            self.assertTrue(body.strip(), src)

    def test_mock_snapshots_valid(self):
        files = sorted(glob.glob(os.path.join(WEB_DIR, "mock", "*.json")))
        self.assertTrue(files)
        for path in files:
            name = os.path.splitext(os.path.basename(path))[0]
            code, ctype, body = _get(f"{self.base}/mock/{name}.json")
            self.assertEqual(code, 200, name)
            self.assertTrue(ctype.startswith("application/json"), ctype)
            snap = json.loads(body)
            self.assertIn(snap["phase"], ("gather", "quan", "shop"), name)
            if name.startswith("day-"):
                for key in ("day", "day_plan", "upgrades", "active_upgrades"):
                    self.assertIn(key, snap, (name, key))

    def test_blocks_escape_and_unknown_types(self):
        for path in ("/../game.contract.json", "/%2e%2e/game.contract.json", "/..%2f..%2fREADME.md",
                     "/js/../../live.py", "/README.md", "/khong-co.js"):
            self.assertEqual(_get(self.base + path)[0], 404, path)

    def test_state_has_phase_meta_and_menu(self):
        code, _, body = _get(self.base + "/state")
        self.assertEqual(code, 200)
        st = json.loads(body)
        self.assertEqual(st["mode"], "gather")
        self.assertIn("bounds", st["meta"])
        self.assertEqual(st["menu"], load_contract()["tuning"]["menu"])

    def test_v11_buttons_accepted_and_validated(self):
        ok = {"move": [0, 0], "pause": True, "shop_done": False, "attack": False, "photo": False}
        self.assertEqual(_post(self.base + "/input", ok), 200)
        self.assertEqual(_post(self.base + "/input", {"pause": False, "buy": "oxygen"}), 200)
        self.assertEqual(_post(self.base + "/input", {"pause": "yes"}), 400)
        self.assertEqual(_post(self.base + "/input", {"buy": ""}), 400)
        self.assertEqual(_post(self.base + "/input", {"buy": 3}), 400)


class LiveInputsV11Test(unittest.TestCase):
    def test_buy_lasts_one_tick_and_pause_edge(self):
        from chonoi.live import _LiveInputsV11
        li = _LiveInputsV11()
        li.set(None, buy="hp", pause=True)
        li.set(None, pause=False)
        st = li.advance()
        self.assertEqual(st.buy, "hp")
        self.assertTrue(st.pressed("pause"))
        st2 = li.advance()
        self.assertIsNone(st2.buy)
        self.assertFalse(st2.pressed("pause"))


if __name__ == "__main__":
    unittest.main()
