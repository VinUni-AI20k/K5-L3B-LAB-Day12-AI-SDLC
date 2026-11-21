"""TICKET-04 mục 1: bench_cmd trong game.contract.json tạo bench.json đúng 5 trường (chạy ngắn để test nhanh)."""

import json
import os
import shlex
import subprocess
import unittest

from helpers import ROOT, Workdir


def bench_cmd():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        c = json.load(f)
    assert c["contract_version"] == "1.3"
    return shlex.split(c["bench_cmd"])


class Bench(unittest.TestCase):
    def test_bench_writes_five_fields_consistently(self):
        with Workdir() as w:
            out, frame = w.path("bench.json"), w.path("f.ppm")
            p = subprocess.run([*bench_cmd(), "--seed", "42", "--duration", "0.5", "--warmup", "0.2", "--out", out,
                                "--frame-out", frame], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                r = json.load(f)
            self.assertEqual(set(r), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
            self.assertIsInstance(r["frames"], int)
            self.assertGreater(r["frames"], 0)
            self.assertGreaterEqual(r["measured_s"], 0.5)
            self.assertEqual(round(r["frames"] / r["measured_s"], 2), r["avg_fps"])  # avg_fps = frames / measured_s
            self.assertLessEqual(r["p1_low_fps"], r["avg_fps"] + 1e-6)            # 1% low không nhanh hơn trung bình
            self.assertGreaterEqual(r["load_ms"], 0)
            with open(frame, "rb") as f:                                           # thật sự render 1280×720
                self.assertTrue(f.read(20).startswith(b"P6\n1280 720\n255\n"))

    def test_bad_duration_exit_2(self):
        with Workdir() as w:
            p = subprocess.run([*bench_cmd(), "--seed", "1", "--duration", "0", "--out", w.path("b.json")],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
