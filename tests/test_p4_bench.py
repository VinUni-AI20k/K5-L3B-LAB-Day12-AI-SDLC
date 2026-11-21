"""Test benchmark có render (Phase 4, Phase4.md mục 1). Module: qa/bench.

| AC        | Nhóm test | Nội dung                                                                        |
|-----------|-----------|---------------------------------------------------------------------------------|
| AC-P4-01  | Compute   | công thức 5 trường: avg_fps, p1_low_fps (max(1, ceil(0.01·frames)) khung chậm nhất), frames, measured_s |
| AC-P4-02  | Cli       | tham số sai → mã 2, thiếu Chrome → mã 1 (không treo)                             |
| AC-P4-03  | Real      | chạy thật `chonoi.bench` ngắn, bench.json có đủ 5 trường đúng kiểu (bỏ qua nếu máy không có Chrome) |

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p "test_p4_bench.py" -v
"""

import json
import os
import subprocess
import sys
import unittest
from unittest import mock

from chonoi import bench
from helpers import ROOT, Workdir

FIELDS = {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"}


class Compute(unittest.TestCase):
    """AC-P4-01 — công thức chỉ số."""

    def test_compute_01_steady_60fps(self):
        """600 khung đều 1000/60 ms: 60 FPS, 1% low cũng 60 FPS, 10 s."""
        r = bench.compute([1000 / 60] * 600, 800)
        self.assertEqual(set(r), FIELDS)
        self.assertEqual(r["frames"], 600)
        self.assertAlmostEqual(r["avg_fps"], 60.0, places=1)
        self.assertAlmostEqual(r["p1_low_fps"], 60.0, places=1)
        self.assertAlmostEqual(r["measured_s"], 10.0, places=2)
        self.assertEqual(r["load_ms"], 800)

    def test_compute_02_p1_low_uses_slowest_one_percent(self):
        """100 khung: 99 khung 10 ms và 1 khung 100 ms. max(1, ceil(0.01×100)) = 1 khung chậm nhất → 1/0.1 s = 10 FPS."""
        r = bench.compute([10.0] * 99 + [100.0], 0)
        self.assertEqual(r["p1_low_fps"], 10.0)
        self.assertAlmostEqual(r["avg_fps"], 100 / 1.09, places=1)   # 100 khung trong 1.09 s

    def test_compute_03_ceil_for_non_round_frame_counts(self):
        """250 khung → ceil(2.5) = 3 khung chậm nhất: ba khung 50 ms, trung bình 50 ms → 20 FPS."""
        r = bench.compute([10.0] * 247 + [50.0] * 3, 0)
        self.assertEqual(r["p1_low_fps"], 20.0)

    def test_compute_04_few_frames_use_at_least_one(self):
        """Dưới 100 khung vẫn lấy ít nhất 1 khung chậm nhất."""
        r = bench.compute([20.0, 20.0, 40.0], 0)
        self.assertEqual(r["p1_low_fps"], 25.0)
        self.assertEqual(r["frames"], 3)


class Cli(unittest.TestCase):
    """AC-P4-02 — tham số và lỗi môi trường."""

    def test_cli_01_bad_duration_exit_2(self):
        with Workdir() as w:
            self.assertEqual(bench.main(["--seed", "42", "--duration", "0", "--out", w.path("b.json")]), 2)
            self.assertFalse(os.path.exists(w.path("b.json")))

    def test_cli_02_missing_args_exit_2(self):
        with self.assertRaises(SystemExit) as cm:
            bench.main(["--seed", "42"])
        self.assertEqual(cm.exception.code, 2)

    def test_cli_03_no_browser_exit_1_without_hanging(self):
        with Workdir() as w, mock.patch.object(bench, "find_chrome", return_value=None):
            self.assertEqual(bench.main(["--seed", "42", "--duration", "1", "--out", w.path("b.json")]), 1)
            self.assertFalse(os.path.exists(w.path("b.json")))


@unittest.skipUnless(bench.find_chrome() and not os.environ.get("CHONOI_SKIP_BENCH"),
                     "cần Chrome/Chromium/Edge để chạy benchmark thật (đặt CHROME_BIN)")
class Real(unittest.TestCase):
    """AC-P4-03 — chạy thật qua dòng lệnh, đúng cấu trúc bench.json."""

    def test_real_01_bench_json_has_five_fields(self):
        with Workdir() as w:
            out = w.path("bench.json")
            p = subprocess.run([sys.executable, "-m", "chonoi.bench", "--seed", "42", "--duration", "2", "--out", out],
                               cwd=ROOT, capture_output=True, text=True, timeout=120)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                r = json.load(f)
            self.assertEqual(set(r), FIELDS)
            self.assertIsInstance(r["frames"], int)
            self.assertGreater(r["frames"], 10)
            self.assertAlmostEqual(r["measured_s"], 2.0, delta=0.5)
            self.assertGreater(r["avg_fps"], 0)
            self.assertGreater(r["p1_low_fps"], 0)
            self.assertLessEqual(r["p1_low_fps"], r["avg_fps"] + 1e-6)
            self.assertGreater(r["load_ms"], 0)


if __name__ == "__main__":
    unittest.main()
