"""Test asset tự tạo (Ticket-04, "Tự do sáng tạo": đồ họa + SFX): SVG, sfx.js, route tĩnh của live.py.

Asset chỉ dùng ở client nên test này cũng kiểm headless KHÔNG đọc asset (tắt ở headless, lõi không đổi).
"""

import importlib.util
import json
import os
import re
import shutil
import subprocess
import unittest
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer
from helpers import ROOT

ASSETS = os.path.join(ROOT, "chonoi", "web", "assets")
SVG_NS = "{http://www.w3.org/2000/svg}"
MAX_SVG_BYTES = 8 * 1024


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def svg_names():
    return sorted(f[:-4] for f in os.listdir(ASSETS) if f.endswith(".svg"))


def load_generator():
    spec = importlib.util.spec_from_file_location("gen_assets", os.path.join(ROOT, "tools", "gen_assets.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Svg(unittest.TestCase):
    def test_moi_svg_hop_le_co_viewbox_va_nho(self):
        for name in svg_names():
            path = os.path.join(ASSETS, name + ".svg")
            root = ET.parse(path).getroot()
            self.assertEqual(root.tag, SVG_NS + "svg", name)
            self.assertTrue(root.get("viewBox"), f"{name}: thiếu viewBox")
            self.assertLess(os.path.getsize(path), MAX_SVG_BYTES, name)

    def test_khong_tham_chieu_ngoai_hay_ma_chay(self):
        """Tài sản tự tạo: không <script>, không <image>/href tới URL, không on* handler (an toàn + không phụ thuộc ngoài)."""
        for name in svg_names():
            for el in ET.parse(os.path.join(ASSETS, name + ".svg")).getroot().iter():
                tag = el.tag.replace(SVG_NS, "")
                self.assertNotIn(tag, ("script", "image", "foreignObject", "use"), f"{name}: <{tag}>")
                for attr, value in el.attrib.items():
                    self.assertFalse(attr.startswith("on"), f"{name}: {attr}")
                    self.assertNotRegex(value, r"(?i)https?:|data:|javascript:", f"{name}: {attr}")

    def test_dung_voi_script_sinh_ra(self):
        """File trong repo phải khớp tools/gen_assets.py (không ai sửa tay làm lệch nguồn)."""
        gen = load_generator()
        self.assertEqual(sorted(gen.ASSETS), svg_names())
        for name, text in gen.ASSETS.items():
            self.assertEqual(read("chonoi", "web", "assets", name + ".svg"), text, name)


class Coverage(unittest.TestCase):
    TUNING = load_contract()["tuning"]

    def test_du_asset_cho_moi_mon_loai_ca_cay_va_quai(self):
        names = set(svg_names())
        for dish in self.TUNING["menu"]:
            self.assertIn("dish_" + dish, names)
        for node in self.TUNING["gather"]["nodes"]:
            self.assertIn(node["kind"], names)
        for kind in self.TUNING["gather"]["fish_yield"]:
            self.assertIn(kind, names)
        for spawn in self.TUNING["gather"].get("monsters", {}).get("spawns", []):
            self.assertIn(spawn["kind"], names)
        for needed in ("usen", "dock", "stove", "table", "customer", "warn_monster", "warn_oxygen", "warn_angry"):
            self.assertIn(needed, names)

    def test_client_nap_dung_tap_asset(self):
        html = read("chonoi", "web", "index.html")
        listed = set(re.findall(r'"([a-z_]+)"', re.search(r"const SPRITE_NAMES = \[(.*?)\];", html, re.S).group(1)))
        self.assertEqual(listed, set(svg_names()))
        self.assertIn('src="/assets/sfx.js"', html)


class Sfx(unittest.TestCase):
    JS = read("chonoi", "web", "assets", "sfx.js")

    @staticmethod
    def sim_source() -> str:
        sim = os.path.join(ROOT, "chonoi", "sim")
        return "\n".join(read("chonoi", "sim", fn) for fn in sorted(os.listdir(sim)) if fn.endswith(".py"))

    def test_ten_su_kien_sfx_khop_su_kien_that_cua_sim(self):
        mapped = set(re.findall(r"^    ([a-z_]+):\s+\{ c:", self.JS, re.M))
        self.assertGreaterEqual(len(mapped), 20)
        src = self.sim_source()
        missing = sorted(n for n in mapped if f'"{n}"' not in src)  # tên sự kiện phải xuất hiện trong code sim
        self.assertEqual(missing, [], "tên sự kiện SFX gõ sai / sim không phát")

    def test_moi_am_co_phu_de(self):
        """Phụ đề cho MỌI hiệu ứng đã triển khai (Ticket-04): mỗi mục có chuỗi c: và hàm p:."""
        entries = re.findall(r"^    ([a-z_]+):\s+\{ c: \"([^\"]+)\", p:", self.JS, re.M)
        self.assertEqual(len(entries), len(re.findall(r"^    [a-z_]+:\s+\{ c:", self.JS, re.M)))
        for name, caption in entries:
            self.assertRegex(caption, r"^\[[^\]]+\] .+", name)

    @unittest.skipUnless(shutil.which("node"), "không có node")
    def test_cu_phap_js(self):
        p = subprocess.run(["node", "--check", os.path.join(ASSETS, "sfx.js")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_headless_khong_biet_toi_asset(self):
        """Asset chỉ ở client: sim và các module headless không được nhắc tới thư mục asset."""
        for fn in ("runner.py", "headless.py", "inputs.py", "scenario.py", "contract.py"):
            self.assertNotIn("assets", read("chonoi", fn), fn)
        for fn in os.listdir(os.path.join(ROOT, "chonoi", "sim")):
            if fn.endswith(".py"):
                self.assertNotIn("assets", read("chonoi", "sim", fn), fn)


class Route(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LiveServer(LiveGame("gather", load_contract()["tuning"], {}, 1), port=0)
        cls.server.start()
        cls.base = cls.server.url.rstrip("/")

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def get(self, path):
        try:
            with urllib.request.urlopen(self.base + path, timeout=5) as r:
                return r.status, r.headers.get("Content-Type"), r.read()
        except urllib.error.HTTPError as e:
            e.close()
            return e.code, None, b""

    def test_phuc_vu_svg_va_js(self):
        code, ctype, body = self.get("/assets/usen.svg")
        self.assertEqual((code, ctype), (200, "image/svg+xml"))
        with open(os.path.join(ASSETS, "usen.svg"), "rb") as f:  # so theo byte: Git trên Windows có thể đổi LF thành CRLF
            self.assertEqual(body, f.read())
        code, ctype, _ = self.get("/assets/sfx.js")
        self.assertEqual(code, 200)
        self.assertTrue(ctype.startswith("text/javascript"))

    def test_chan_duong_dan_nguy_hiem_va_loai_file_khac(self):
        for path in ("/assets/..%2fgame.contract.json", "/assets/../../game.contract.json", "/assets/%2e%2e/live.py",
                     "/assets/usen.svg%00.txt", "/assets/.hidden.svg", "/assets/index.html", "/assets/", "/assets/x.py",
                     "/assets/nope.svg", "/assets/sub/usen.svg"):
            self.assertEqual(self.get(path)[0], 404, path)

    def test_state_va_index_van_nhu_cu(self):
        self.assertEqual(self.get("/")[0], 200)
        self.assertIn("player", json.loads(self.get("/state")[2]))


if __name__ == "__main__":
    unittest.main()
