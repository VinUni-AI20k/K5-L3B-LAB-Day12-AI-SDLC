"""P4-03: benchmark ghi số đo của một cảnh Gather được vẽ thật."""

import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from time import perf_counter_ns
from unittest import mock

from chonoi import bench
from chonoi.bench import BAR_FRESH, BAR_SPOILED, DIVER, HEIGHT, WIDTH, GatherRaster
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

    def test_scene_matches_ticket_diver_idle_at_dock_with_fish_monster_and_freshness(self):
        """Ticket-04: buổi sáng lặn có độ tươi, cá bơi, Cá Sấu Năm Chèo; Út Sen đứng yên ở bến."""
        contract = load_contract()
        tuning = contract["tuning"]
        snaps = bench.scene_snapshots(tuning, 42, contract["contract_version"])
        self.assertEqual({tuple(s["player"]["pos"]) for s in snaps}, {tuple(tuning["gather"]["dock_pos"])})
        self.assertGreater(len(snaps[0]["fish"]), 0)
        self.assertEqual(len(snaps[0]["monsters"]), 1)
        self.assertNotEqual(snaps[0]["fish"], snaps[-1]["fish"])  # cá bơi
        self.assertNotEqual(snaps[0]["monsters"], snaps[-1]["monsters"])  # Cá Sấu tuần tra
        first, last = snaps[0]["hold"], snaps[-1]["hold"]
        self.assertEqual(len(first), len(bench.SCENE_HOLD))
        below = tuning["freshness"]["spoiled_below"]
        self.assertTrue(any(i["fresh"] < below for i in first) and any(i["fresh"] >= below for i in first))
        self.assertTrue(all(b["fresh"] < a["fresh"] for a, b in zip(first, last)))  # độ tươi hao theo thời gian

    def test_freshness_hud_draws_fresh_and_spoiled_bars(self):
        contract = load_contract()
        tuning = contract["tuning"]
        raster = GatherRaster(tuning["gather"], tuning["freshness"])
        snap = bench.scene_snapshots(tuning, 42, contract["contract_version"], ticks=0)[0]
        raster.render(snap)

        def color(slot):
            x, y = 22, HEIGHT - 28 - 16 * slot + 5
            offset = (y * WIDTH + x) * 3
            return bytes(raster.pixels[offset:offset + 3])

        self.assertEqual(color(0), BAR_FRESH)  # cá thể 100 điểm
        self.assertEqual(color(len(snap["hold"]) - 1), BAR_SPOILED)  # cá thể 20 điểm: ươn
        no_hud = GatherRaster(tuning["gather"])  # contract không có freshness thì không vẽ HUD
        no_hud.render(snap)
        self.assertNotEqual(bytes(no_hud.pixels), bytes(raster.pixels))

    def test_load_ms_counts_from_launch(self):
        with mock.patch.object(bench, "_LAUNCH_NS", perf_counter_ns() - 5_000_000_000):
            report = bench.benchmark(0.01, 42, 0)
        self.assertGreaterEqual(report["load_ms"], 5000)

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
