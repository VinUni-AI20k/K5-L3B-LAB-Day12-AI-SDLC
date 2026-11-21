"""Kiểm tra 3 cảnh báo và chế độ Tương phản cao (Phase 4 — Người A) trong `chonoi/web/index.html`."""

import os
import unittest

WEB_HTML = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "chonoi", "web", "index.html",
)


class UIAlertsAndContrastTest(unittest.TestCase):
    def test_ui_has_three_alerts_and_high_contrast_toggle(self):
        with open(WEB_HTML, encoding="utf-8") as f:
            html = f.read()
        # 1. Thủy quái đến gần
        self.assertIn("THỦY QUÁI ĐẾN GẦN", html)
        # 2. Oxy sắp hết (< 20%)
        self.assertIn("OXY SẮP HẾT", html)
        self.assertIn("oxygenPercent < 20", html)
        # 3. Khách sắp giận
        self.assertIn("Khách sắp bỏ về!", html)
        self.assertIn("😠", html)
        # 4. High Contrast Mode (toggle button + phím tắt H)
        self.assertIn("toggleHighContrast", html)
        self.assertIn("hc-btn", html)


if __name__ == "__main__":
    unittest.main()
