"""AC-P4-02: benchmark canvas thật, tính toán phía server (không cần browser để unit test)."""
import json
import os
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from chonoi.bench import BenchRun, main, make_bench_server
from chonoi.contract import load_contract


def _post(url, body):
    req = urllib.request.Request(url, method="POST", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as exc:
        with exc:
            return exc.code, json.load(exc)


class BenchMath(unittest.TestCase):
    def test_average_and_one_percent_low_uses_slowest_frames(self):
        run = BenchRun(time.perf_counter())
        run.mark_first_frame()
        # 99 khung 10ms + 1 khung 100ms: 100 frames, 1% worst là đúng 1 khung 100ms.
        out = run.submit({"frame_intervals_ms": [10] * 99 + [100]})
        self.assertEqual(set(out), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
        self.assertEqual(out["frames"], 100)
        self.assertEqual(out["measured_s"], 1.09)
        self.assertAlmostEqual(out["avg_fps"], 100 / 1.09, delta=0.001)
        self.assertEqual(out["p1_low_fps"], 10.0)
        self.assertGreaterEqual(out["load_ms"], 0)

    def test_slowest_ceiling_and_mean_of_slowest(self):
        run = BenchRun(time.perf_counter())
        run.mark_first_frame()
        # 201 frames: ceil(2.01)=3 => worst 100, 50, 25ms => p1 low 3 / .175
        out = run.submit({"frame_intervals_ms": [10] * 198 + [25, 50, 100]})
        self.assertAlmostEqual(out["p1_low_fps"], 3 / .175, delta=0.001)

    def test_expected_duration_rejects_gross_overrun(self):
        run = BenchRun(time.perf_counter() - 5, expected_duration=1)
        run.mark_first_frame()
        # Vong rAF bi tam dung: 3 giay elapsed khong phai 1 giay lien tuc.
        with self.assertRaisesRegex(ValueError, "vượt quá giới hạn"):
            run.submit({"frame_intervals_ms": [100] * 30})
        self.assertIsNone(run.data)

    def test_failure_reason_sets_done_without_fps(self):
        run = BenchRun(time.perf_counter())
        run.fail("tab bị ẩn")
        self.assertTrue(run.done.is_set())
        self.assertIsNone(run.data)
        self.assertEqual(run.error, "tab bị ẩn")
        with self.assertRaises(ValueError):
            run.fail("thử lại")

    def test_reject_bad_samples_and_duplicate(self):
        run = BenchRun(time.perf_counter())
        with self.assertRaises(ValueError):
            run.submit({"frame_intervals_ms": [10]})
        run.mark_first_frame()
        for bad in ([], [0], [-1], [float("nan")], [float("inf")], [True], ["15"]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                run.submit({"frame_intervals_ms": bad})
        run.submit({"frame_intervals_ms": [20]})
        with self.assertRaises(ValueError):
            run.submit({"frame_intervals_ms": [20]})


class BenchHttp(unittest.TestCase):
    def test_real_live_server_bench_routes_and_canvas_script(self):
        server, run = make_bench_server(load_contract()["tuning"], seed=42, started=time.perf_counter())
        server.start()
        try:
            base = server.url.rstrip("/")
            with urllib.request.urlopen(base + "/?bench=1&duration=1", timeout=5) as resp:
                content = resp.read().decode()
            self.assertIn("bench (Hùng)", content)
            self.assertIn('fetch("/bench"', content)
            self.assertIn('fetch("/bench-error"', content)
            self.assertIn('document.hidden', content)
            with urllib.request.urlopen(base + "/state", timeout=5) as resp:
                snap = json.load(resp)
            self.assertEqual(snap["mode"], "gather")
            self.assertTrue(snap["fish"], "cảnh benchmark phải có đàn cá")
            self.assertTrue(snap["monsters"], "cảnh benchmark phải có Cá Sấu")
            self.assertEqual(snap["player"]["pos"], [2, 0], "Út Sen phải đứng ở bến")
            self.assertIn("hold", snap)  # độ tươi v1.2 có trong engine Gather
            self.assertEqual(_post(base + "/bench", {"frame_intervals_ms": [20]})[0], 400)
            self.assertEqual(_post(base + "/bench-start", {})[0], 200)
            self.assertEqual(_post(base + "/bench", {"frame_intervals_ms": [20, 20]})[0], 200)
            self.assertTrue(run.done.wait(2))
            self.assertEqual(run.data["frames"], 2)
            self.assertEqual(run.data["avg_fps"], 50)
            self.assertEqual(_post(base + "/bench", {"frame_intervals_ms": [20]})[0], 400)
            self.assertEqual(_post(base + "/input", {"move": [0, 0]})[0], 200)
        finally:
            server.stop()

    def test_http_browser_failure_wakes_waiter(self):
        server, run = make_bench_server(load_contract()["tuning"], 42, time.perf_counter(), duration=30)
        server.start()
        try:
            base = server.url.rstrip("/")
            self.assertEqual(_post(base + "/bench-error", {"error": "tab mất tiêu điểm"})[0], 200)
            self.assertTrue(run.done.wait(2))
            self.assertIsNone(run.data)
            self.assertEqual(run.error, "tab mất tiêu điểm")
            self.assertEqual(_post(base + "/bench", {"frame_intervals_ms": [20]})[0], 400)
        finally:
            server.stop()

    def test_reject_submission_before_full_measurement(self):
        server, run = make_bench_server(load_contract()["tuning"], 42, time.perf_counter(), duration=1)
        server.start()
        try:
            base = server.url.rstrip("/")
            self.assertEqual(_post(base + "/bench-start", {})[0], 200)
            self.assertEqual(_post(base + "/bench", {"frame_intervals_ms": [20]})[0], 400)
            self.assertFalse(run.done.is_set())
        finally:
            server.stop()

    def test_failure_keeps_previous_benchmark_file_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bench.json")
            previous = '{"avg_fps": 9.41}\n'
            with open(path, "w", encoding="utf-8") as f:
                f.write(previous)
            with patch("chonoi.bench.webbrowser.open", return_value=False):
                self.assertEqual(main(["--duration", "1", "--out", path]), 1)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.read(), previous)

    def test_no_browser_does_not_write_artificial_fps(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bench.json")
            with patch("chonoi.bench.webbrowser.open", return_value=False):
                self.assertEqual(main(["--seed", "42", "--duration", "1", "--out", path]), 1)
            self.assertFalse(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
