"""QA Phase 3 (common-maker): HUD độ tươi (Test Contract v1.2) và smoke bàn giao kho theo Ticket-03.

- Test HUD: kiểm `chonoi/web/index.html` có đủ phần đọc kho cá thể và nhãn ƯƠN, và vẫn đọc được kho đếm (v1.1).
- Test bàn giao kho v1.2 (`SmokeHandoffV12`): chỉ chạy khi manifest đã bật `contract_version` 1.2. Trước đó bị bỏ qua, không báo xanh giả.
- Test bàn giao kho v1.1 (`SmokeHandoffV11`): chỉ chạy khi manifest còn ở 1.1 (regression kho đếm).
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "chonoi", "web", "index.html")


def contract_version():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)["contract_version"]


def run_headless(*args):
    return subprocess.run([sys.executable, "-m", "chonoi.headless", *args], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8")


def read_rows(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class HudFreshnessTokensTest(unittest.TestCase):
    """HUD phải cho đọc độ tươi và nhận ra hàng ươn (DoD Phase 3), vẫn sans-serif, vẫn đọc kho đếm."""

    @classmethod
    def setUpClass(cls):
        with open(HTML, encoding="utf-8") as f:
            cls.html = f.read()

    def test_ui_co_do_tuoi_va_nhan_uon(self):
        for token in ("ƯƠN", "SPOILED_BELOW = 30", "itemFresh", "isSpoiledItem", "freshColor",
                      "drawFreshStockLine", "Độ tươi kho", "Tươi TB"):
            self.assertIn(token, self.html, f"HUD thiếu phần độ tươi: {token}")

    def test_kho_kha_dung_chi_tinh_hang_chua_uon_chua_giu(self):
        # Hai nhánh: kho cá thể (mảng, loại hàng ươn và hàng đã giữ theo id) và kho đếm (v1.1).
        self.assertIn("Array.isArray(stock)", self.html)
        self.assertIn("held.has(it.id)", self.html)
        self.assertIn("computeAvailableStock", self.html)
        self.assertIn("Kho khả dụng", self.html)

    def test_van_con_cac_token_hud_cu(self):
        for token in ("sans-serif", "Thủy quái!", "Hết hơi!", "drawGather", "drawQuan", "dishName"):
            self.assertIn(token, self.html)

    def test_nguong_on_khop_hop_dong(self):
        # Ticket-03: ươn khi fresh < 30. Ngưỡng cảnh báo phải cao hơn ngưỡng ươn.
        import re
        spoiled = int(re.search(r"SPOILED_BELOW\s*=\s*(\d+)", self.html).group(1))
        warn = int(re.search(r"WARN_BELOW\s*=\s*(\d+)", self.html).group(1))
        self.assertEqual(spoiled, 30)
        self.assertGreater(warn, spoiled)

    def test_che_do_demo_chi_bat_bang_query(self):
        # Dữ liệu giả để QA xem HUD v1.2 phải tắt mặc định (không đụng sim, không đổi headless).
        self.assertIn('get("demo") === "fresh"', self.html)
        self.assertIn("if (DEMO_FRESH) applyDemoFresh(s);", self.html)


@unittest.skipUnless(contract_version() == "1.2", "chỉ chạy khi manifest bật contract_version 1.2")
class SmokeHandoffV12(unittest.TestCase):
    """Ticket-03 mục QA: hold I1 ca_linh fresh 100, interact ở frame 0, rồi quan --inventory --ticks 0."""

    def test_ban_giao_kho_ca_the_chinh_xac(self):
        with tempfile.TemporaryDirectory() as d:
            sc = os.path.join(d, "dock.json")
            inp = os.path.join(d, "in.json")
            inv = os.path.join(d, "catch.json")
            with open(sc, "w", encoding="utf-8") as f:
                json.dump({"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}],
                                      "random_fish": False, "monsters": []}}, f)
            with open(inp, "w", encoding="utf-8") as f:
                json.dump({"frames": [{"tick": 0, "interact": True}]}, f)
            g = run_headless("--mode", "gather", "--seed", "42", "--scenario", sc, "--inputs", inp,
                             "--ticks", "1", "--out", os.path.join(d, "g.jsonl"), "--inventory-out", inv)
            self.assertEqual(g.returncode, 0, g.stderr)
            q = run_headless("--mode", "quan", "--seed", "42", "--inventory", inv, "--ticks", "0",
                             "--out", os.path.join(d, "q.jsonl"))
            self.assertEqual(q.returncode, 0, q.stderr)
            with open(inv, encoding="utf-8") as f:
                kho = json.load(f)
            self.assertEqual(list(kho), ["items"])
            self.assertIsInstance(kho["items"], list)
            self.assertEqual([(i["id"], i["kind"]) for i in kho["items"]], [("I1", "ca_linh")])
            snap0 = [r for r in read_rows(os.path.join(d, "q.jsonl")) if r["type"] == "snapshot"][0]
            self.assertEqual(snap0["stock"], kho["items"])
            # một lần hao ở bước gather (1 bước): 100 - 1/120
            self.assertAlmostEqual(kho["items"][0]["fresh"], 100 - 1 / 120, places=6)

    def test_kho_dem_bi_tu_choi_o_v12(self):
        with tempfile.TemporaryDirectory() as d:
            inv = os.path.join(d, "old.json")
            with open(inv, "w", encoding="utf-8") as f:
                json.dump({"items": {"ca_loc": 1}}, f)
            q = run_headless("--mode", "quan", "--seed", "1", "--inventory", inv, "--ticks", "0",
                             "--out", os.path.join(d, "q.jsonl"))
            self.assertEqual(q.returncode, 2)


@unittest.skipUnless(contract_version() == "1.1", "regression kho đếm, chỉ khi manifest còn 1.1")
class SmokeHandoffV11(unittest.TestCase):
    def test_ban_giao_kho_dem(self):
        with tempfile.TemporaryDirectory() as d:
            sc = os.path.join(d, "dock.json")
            inp = os.path.join(d, "in.json")
            inv = os.path.join(d, "catch.json")
            with open(sc, "w", encoding="utf-8") as f:
                json.dump({"gather": {"hold": ["ca_linh", "ca_linh", "bong_sung"], "random_fish": False, "monsters": []}}, f)
            with open(inp, "w", encoding="utf-8") as f:
                json.dump({"frames": [{"tick": 0, "interact": True}]}, f)
            g = run_headless("--mode", "gather", "--seed", "42", "--scenario", sc, "--inputs", inp,
                             "--ticks", "1", "--out", os.path.join(d, "g.jsonl"), "--inventory-out", inv)
            self.assertEqual(g.returncode, 0, g.stderr)
            q = run_headless("--mode", "quan", "--seed", "42", "--inventory", inv, "--ticks", "0",
                             "--out", os.path.join(d, "q.jsonl"))
            self.assertEqual(q.returncode, 0, q.stderr)
            with open(inv, encoding="utf-8") as f:
                kho = json.load(f)
            self.assertEqual(kho, {"items": {"bong_sung": 1, "ca_linh": 2}})
            snap0 = [r for r in read_rows(os.path.join(d, "q.jsonl")) if r["type"] == "snapshot"][0]
            self.assertEqual(snap0["stock"], kho["items"])


if __name__ == "__main__":
    unittest.main()
