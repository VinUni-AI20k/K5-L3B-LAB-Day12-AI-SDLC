"""Test HUD cảnh báo + tương phản cao (Ticket-04: AC-P4-04, AC-P4-05).

Chạy script thật của chonoi/web/index.html trong Node với canvas giả (tests/js/hud_harness.js). Không có Node thì skip.
Ba cảnh báo phải có CHỮ + BIỂU TƯỢNG (không chỉ màu): thủy quái gần, oxy sắp hết / hết hơi, khách sắp giận.
"""

import json
import os
import shutil
import subprocess
import unittest

from helpers import ROOT

HARNESS = os.path.join(ROOT, "tests", "js", "hud_harness.js")
INDEX = os.path.join(ROOT, "chonoi", "web", "index.html")


def run_harness() -> dict:
    p = subprocess.run(["node", HARNESS, INDEX], capture_output=True, text=True, encoding="utf-8", timeout=60)
    if p.returncode != 0:
        raise AssertionError(p.stderr)
    return json.loads(p.stdout)


@unittest.skipUnless(shutil.which("node"), "không có node")
class Warnings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = run_harness()

    def test_ac_p4_04_thuy_quai_gan_hien_chu(self):
        self.assertEqual(self.r["monster_near"], ["monster"])
        self.assertEqual(self.r["monster_far"], [])
        self.assertEqual(self.r["monster_chase_far"], ["monster"], "quái đang đuổi luôn báo, dù xa")

    def test_ac_p4_04_thuy_quai_ranh_gioi_15m(self):
        """Báo khi cách ≤ 1.5 × bán kính phát hiện (10 m) = 15 m; xa hơn thì không."""
        self.assertEqual(self.r["monster_near"], ["monster"])  # đúng 15 m
        self.assertEqual(self.r["monster_edge"], [])           # 15.1 m

    def test_ac_p4_04_oxy_sap_het_va_het_hoi(self):
        ox = self.r["oxygen"]
        self.assertEqual(ox["1800"], [])
        self.assertEqual(ox["450"], [], "đúng 25% chưa báo")
        self.assertEqual(ox["449"], ["Oxy sắp hết!"])
        self.assertEqual(ox["300"], ["Oxy sắp hết!"])
        self.assertEqual(ox["0"], ["Hết hơi!"])
        self.assertEqual(self.r["oxygen_surface"], [], "ở mặt nước đang hồi oxy nên không báo")

    def test_ac_p4_04_khach_sap_gian(self):
        a = self.r["angry"]
        self.assertEqual(a["3600"], [])
        self.assertEqual(a["900"], [], "đúng 25% chưa báo")
        self.assertEqual(a["899"], ["Khách sắp giận! T1"])
        self.assertEqual(self.r["angry_eating"], [], "khách đang ăn không giận")
        self.assertEqual(self.r["angry_tables"], ["Khách sắp giận! T3, T1"], "liệt kê đúng bàn, bỏ khách còn nhiều kiên nhẫn")
        self.assertEqual(self.r["angry_not_in_gather"], [])

    def test_ac_p4_04_ve_ra_chu_va_bieu_tuong(self):
        g = self.r["drawn_gather"]
        self.assertIn("Thủy quái!", g)
        self.assertIn("Hết hơi!", g)
        self.assertIn("⚠", g, "sprite chưa tải thì vẫn có biểu tượng dự phòng")
        self.assertIn("Khách sắp giận! T1", self.r["drawn_quan"])

    def test_ac_p4_05_tuong_phan_cao_bat_tat(self):
        self.assertTrue(self.r["hc_on"])
        self.assertTrue(self.r["hc_off"])

    def test_ac_p4_05_tuong_phan_cao_chu_dam_va_vien_den(self):
        self.assertEqual(self.r["normal_strokes"], 0, "bình thường không viền chữ")
        self.assertGreater(self.r["hc_strokes"], 0, "tương phản cao: mọi chữ có viền đen")
        self.assertTrue(self.r["hc_all_bold"], "tương phản cao: mọi chữ đậm")


    def test_ac_p4_05_chu_toi_co_vien_trang_khong_thanh_cuc_den(self):
        """Lỗi thật thấy trên ảnh: nhãn bếp B1/B2 (#111) bị viền đen nên thành cục đen. Chữ tối phải có viền TRẮNG."""
        s = self.r["hc_style"]
        for key in ("dark", "dark_brown"):
            self.assertEqual((s[key]["fill"], s[key]["stroke"]), ("#000000", "#ffffff"), key)
        for key in ("dim_rgba", "dim_grey"):
            self.assertEqual((s[key]["fill"], s[key]["stroke"]), ("#ffffff", "#000"), key)
        self.assertEqual((s["light_red"]["fill"], s["light_red"]["stroke"]), ("#ff6b81", "#000"), "chữ sáng giữ màu")
        self.assertIsNone(self.r["normal_style_dark"], "bình thường: không vẽ viền")


class Static(unittest.TestCase):
    def test_phim_h_va_gop_y_trong_hud(self):
        with open(INDEX, encoding="utf-8") as f:
            html = f.read()
        self.assertIn('k === "h"', html)
        self.assertIn("H tương phản", html)
        for icon in ("warn_monster", "warn_oxygen", "warn_angry"):
            self.assertIn(f'"{icon}"', html)
            self.assertTrue(os.path.exists(os.path.join(ROOT, "chonoi", "web", "assets", icon + ".svg")))


if __name__ == "__main__":
    unittest.main()
