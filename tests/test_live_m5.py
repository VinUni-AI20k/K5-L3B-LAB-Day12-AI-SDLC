"""Unit & integration test cho M5 (chonoi.live HUD, /assets/ static serving, gather & quan modes)."""

import json
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.inventory import read_inventory
from chonoi.live import LiveGame, LiveServer


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read()


def _post(url, obj):
    req = urllib.request.Request(
        url,
        data=json.dumps(obj).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read()
        e.close()
        return e.code, json.loads(body or b"{}")


class LiveM5Test(unittest.TestCase):
    def test_gather_hud_and_static_assets_serving(self):
        tuning = load_contract()["tuning"]
        game = LiveGame("gather", tuning, {}, seed=1)
        server = LiveServer(game, port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            # 1. HTML HUD chứa đầy đủ cấu hình ASSET_MANIFEST và 2 chế độ drawGather / drawQuan
            code, ctype, html = _get(base + "/")
            self.assertEqual(code, 200)
            self.assertIn("text/html", ctype)
            self.assertIn(b"ASSET_MANIFEST", html)
            self.assertIn(b"drawGather", html)
            self.assertIn(b"drawQuan", html)

            # 2. Phục vụ ảnh nền gather_bg.png từ /assets/gather_bg.png
            code, ctype, img_bytes = _get(base + "/assets/gather_bg.png")
            self.assertEqual(code, 200)
            self.assertEqual(ctype, "image/png")
            self.assertTrue(img_bytes.startswith(b"\x89PNG"), "Phải là dữ liệu PNG hợp lệ")

            # 3. Chặn path traversal hoặc file không tồn tại
            for bad_path in ("/assets/khong_ton_tai.png", "/assets/../index.html"):
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    _get(base + bad_path)
                self.assertEqual(ctx.exception.code, 404)
                ctx.exception.close()

            # 4. Kiểm tra các trường snapshot buổi sáng (gather) cho HUD
            code, _, body = _get(base + "/state")
            self.assertEqual(code, 200)
            st = json.loads(body)
            self.assertEqual(st["mode"], "gather")
            for field in ("time_left_ticks", "player", "hold", "hold_capacity", "nodes", "fish", "meta", "events"):
                self.assertIn(field, st)
            for p_field in ("pos", "oxygen_ticks", "oxygen_max_ticks", "hp", "hp_max", "zero_oxy_ticks", "catch_cd_ticks", "at_surface"):
                self.assertIn(p_field, st["player"])
        finally:
            server.stop()

    def test_quan_live_hud_state_and_inputs(self):
        tuning = load_contract()["tuning"]
        inv = read_inventory("docs/contracts/inventory.sample.json")
        # Đặt người chơi đứng gần bếp B1 [2, 8] và có sẵn 1 khách chờ tại bàn T1 [9, 2]
        scenario = {
            "player": {"pos": [2.0, 8.0]},
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "order_tick": 0,
                    "state": "waiting",
                    "patience_ticks_left": 3600,
                    "eat_ticks_left": 0,
                    "order_status": "reserved",
                    "reserved": {"ca_loc": 1},
                    "base_price": 60,
                    "tip": 0,
                }
            ],
        }
        game = LiveGame("quan", tuning, scenario, seed=1, inventory=inv)
        server = LiveServer(game, port=0)
        # Không bật thread chạy tự do để bước từng tick tất định qua khóa
        server.httpd_thread_only = True
        import threading
        server._thread = threading.Thread(target=server.httpd.serve_forever, daemon=True)
        server._thread.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            code, _, body = _get(base + "/state")
            self.assertEqual(code, 200)
            st0 = json.loads(body)
            self.assertEqual(st0["mode"], "quan")
            self.assertEqual(st0["stock"], {"bong_sung": 2, "ca_loc": 1})
            self.assertEqual(len(st0["customers"]), 1)
            self.assertEqual(st0["customers"][0]["order_status"], "reserved")

            # Gửi lệnh nhấn E (interact) tại bếp B1 để bắt đầu nấu
            code, resp = _post(base + "/input", {"move": [0, 0], "interact": True, "catch": False})
            self.assertEqual(code, 200)
            self.assertTrue(resp.get("ok"))
            with game._lock:
                game._tick_once()
            _post(base + "/input", {"move": [0, 0], "interact": False, "catch": False})

            _, _, body1 = _get(base + "/state")
            st1 = json.loads(body1)
            self.assertEqual(st1["stoves"][0]["state"], "cooking")
            self.assertEqual(st1["customers"][0]["order_status"], "assigned")
            # Kho vật lý đã trừ 1 ca_loc khi bắt đầu nấu, còn bong_sung: 2
            self.assertEqual(st1["stock"], {"bong_sung": 2})

            # POST /restart khôi phục lại trạng thái ban đầu
            code, _ = _post(base + "/restart", {})
            self.assertEqual(code, 200)
            _, _, body_reset = _get(base + "/state")
            st_reset = json.loads(body_reset)
            self.assertEqual(st_reset["tick"], 0)
            self.assertEqual(st_reset["stoves"][0]["state"], "idle")
        finally:
            server.httpd.shutdown()
            server.httpd.server_close()


if __name__ == "__main__":
    unittest.main()
