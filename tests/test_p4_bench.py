"""P4-03: benchmark ghi số đo của một cảnh Gather được vẽ thật."""

import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from chonoi.bench import DIVER, HEIGHT, WIDTH, GatherRaster
from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session


class BenchTests(unittest.TestCase):
    def test_raster_follows_player_snapshot(self):
        contract = load_contract()
        tuning = contract["tuning"]
        session = Session("gather", tuning, {}, seed=1,
                          contract_version=contract["contract_version"])
        raster = GatherRaster(tuning["gather"])
        raster.render(session.snapshot())
        initial = bytes(raster.pixels)
        inp = InputState((0, 1), {}, set())
        for _ in range(tuning["tick_hz"]):
            session.step(inp)
        snapshot = session.snapshot()
        raster.render(snapshot)

        self.assertEqual(len(initial), WIDTH * HEIGHT * 3)
        self.assertEqual(len(raster.pixels), len(initial))
        self.assertNotEqual(initial, raster.pixels)
        x, depth = snapshot["player"]["pos"]
        px = raster.left + round((x - raster.min_x) * raster.scale)
        py = raster.surface + round((depth - raster.min_depth) * raster.scale)
        offset = (py * WIDTH + px) * 3
        self.assertEqual(raster.pixels[offset:offset + 3], DIVER)

    def test_cli_writes_five_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bench.json"
            proc = subprocess.run(
                [sys.executable, "-m", "chonoi.bench", "--seed", "42", "--duration", "0.05", "--warmup", "0",
                 "--out", str(output)],
                capture_output=True, text=True, encoding="utf-8", timeout=30,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(set(report), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
        self.assertIs(type(report["frames"]), int)
        self.assertTrue(all(math.isfinite(n) and n > 0 for n in report.values()))
        self.assertGreaterEqual(report["measured_s"], 0.05)
        self.assertAlmostEqual(report["avg_fps"], report["frames"] / report["measured_s"])
        self.assertLessEqual(report["p1_low_fps"], report["avg_fps"] + 1e-9)

    def test_warmup_is_not_measured_and_seconds_is_still_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bench.json"
            proc = subprocess.run(
                [sys.executable, "-m", "chonoi.bench", "--seconds", "0.05", "--warmup", "0.4", "--out", str(output)],
                capture_output=True, text=True, encoding="utf-8", timeout=30,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertGreaterEqual(report["measured_s"], 0.05)
        self.assertLess(report["measured_s"], 0.3)  # 0,4 s làm nóng không nằm trong thời lượng đo

    def test_defaults_match_ticket_command(self):
        proc = subprocess.run([sys.executable, "-m", "chonoi.bench", "--help"], capture_output=True, text=True,
                              encoding="utf-8", timeout=30)
        self.assertIn("--duration", proc.stdout)
        self.assertIn("mặc định: 30", proc.stdout)
        self.assertIn("mặc định: 3)", proc.stdout)
        self.assertIn("mặc định: 42", proc.stdout)

    def test_cli_rejects_negative_warmup(self):
        proc = subprocess.run([sys.executable, "-m", "chonoi.bench", "--warmup", "-1", "--out", "unused.json"],
                              capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_cli_rejects_non_finite_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bench.json"
            output.write_text("{}", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-m", "chonoi.bench", "--duration", "inf", "--out", str(output)],
                capture_output=True, text=True, encoding="utf-8", timeout=30,
            )
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "{}")
