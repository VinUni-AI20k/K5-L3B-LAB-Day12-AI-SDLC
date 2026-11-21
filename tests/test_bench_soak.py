"""v1.3 (TICKET-04): bench_cmd / soak_cmd khai ở manifest, chạy được và xuất đúng cấu trúc JSON."""

import json
import shlex
import subprocess
import sys
import unittest

from helpers import Workdir

with open("game.contract.json", encoding="utf-8") as _f:
    C = json.load(_f)


def cmd(key):
    parts = shlex.split(C[key])
    if parts[0] in ("python3", "python"):
        parts[0] = sys.executable
    return parts


class ManifestV13(unittest.TestCase):
    def test_version_and_commands(self):
        self.assertEqual(C["contract_version"], "1.3")
        self.assertIn("freshness", C["tuning"], "gameplay, kho, JSONL theo v1.2")
        for key in ("bench_cmd", "soak_cmd", "headless_cmd", "run_cmd", "build_cmd"):
            self.assertTrue(C[key].strip(), key)


class Soak(unittest.TestCase):
    def run_soak(self, w, seed, days, name):
        out = w.path(name)
        p = subprocess.run([*cmd("soak_cmd"), "--seed", str(seed), "--days", str(days), "--out", out],
                           capture_output=True, text=True)
        with open(out, encoding="utf-8") as f:
            return p.returncode, p.stderr, json.load(f)

    def test_ten_days_no_crash_and_deterministic(self):
        with Workdir() as w:
            code, err, a = self.run_soak(w, 7, 10, "a.json")
            self.assertEqual(code, 0, err)
            self.assertEqual(set(a), {"days", "days_completed", "crashes", "results", "duration_s"})
            self.assertEqual((a["days"], a["days_completed"], a["crashes"]), (10, 10, 0))
            self.assertEqual([r["day"] for r in a["results"]], list(range(1, 11)))
            self.assertTrue(all(set(r) == {"day", "earned", "reputation", "score"} for r in a["results"]))
            _, _, b = self.run_soak(w, 7, 10, "b.json")
            a.pop("duration_s"), b.pop("duration_s")
            self.assertEqual(a, b, "so tất định bỏ số đo thời gian thực")


class Bench(unittest.TestCase):
    def test_bench_json_shape(self):
        with Workdir() as w:
            out = w.path("bench.json")
            p = subprocess.run([*cmd("bench_cmd"), "--seed", "42", "--duration", "1", "--out", out],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                b = json.load(f)
            self.assertEqual(set(b), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
            self.assertGreater(b["frames"], 0)
            self.assertAlmostEqual(b["avg_fps"], b["frames"] / b["measured_s"], delta=0.05)
            self.assertLessEqual(b["p1_low_fps"], b["avg_fps"] + 0.01)


if __name__ == "__main__":
    unittest.main()
