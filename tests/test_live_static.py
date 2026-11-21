"""chonoi.live phục vụ file tĩnh trong chonoi/web/ (pixi.min.js) và chặn đọc ra ngoài thư mục web."""
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer


def _status(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read(64)
    except urllib.error.HTTPError as e:
        return e.code, "", b""


class LiveStaticTest(unittest.TestCase):
    def test_pixi_served_and_traversal_blocked(self):
        tuning = load_contract()["tuning"]
        server = LiveServer(LiveGame("gather", tuning, {}, 1), port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            code, ctype, head = _status(base + "/pixi.min.js")
            self.assertEqual(code, 200)
            self.assertIn("javascript", ctype)
            self.assertGreater(len(head), 0)
            self.assertEqual(_status(base + "/khong-co.js")[0], 404)
            self.assertEqual(_status(base + "/../live.py")[0], 404)
            self.assertEqual(_status(base + "/%2e%2e/live.py")[0], 404)
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
