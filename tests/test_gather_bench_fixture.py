"""Smoke & determinism tests cho fixture benchmark Gather Phase 4 (T411 — hỗ trợ TV5).

Kiểm chứng kịch bản đo chuẩn theo TICKET-04 §1:
  - Út Sen đứng yên ở bến [2, 0] (ngoài tầm phát hiện/hit của Cá Sấu).
  - Cá Sấu Năm Chèo M1 tuần tra thực tế trên màn hình ([60, 24] <-> [64, 24], 1.0 m/s).
  - Có sẵn nút rau, đàn cá và giỏ ban đầu để dựng đầy đủ cảnh gather + HUD/FX.
  - Seed 42, chạy đủ 3 s làm nóng + 30 s đo (1980 tick) không kết thúc sớm và tất định từng byte.
  - Nạp và chạy được trực tiếp trên `LiveServer` (cùng ứng dụng web TV5 dùng đo render 1280x720).

Lưu ý: test này chỉ kiểm tính nạp được, tính tất định và hành vi mô phỏng thực của fixture;
không đo hay khẳng định đạt ngưỡng FPS (việc đo render thuộc runner `bench_cmd` của TV5).
"""

import json
import os
import subprocess
import time
import unittest
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer
from chonoi.scenario import load_scenario
from helpers import ROOT, Workdir, events, headless_cmd, read_jsonl, snapshots

BENCH_CONTRACT = os.path.join(ROOT, "tests", "fixtures", "contract-v1.1-gather-bench.json")
BENCH_SCENARIO = os.path.join(ROOT, "tests", "fixtures", "scenario-gather-bench-t411.json")
WARMUP_PLUS_MEASURE_TICKS = (3 + 30) * 60  # 1980 tick = 3 s warm-up + 30 s measure


def _run_bench_headless(*args):
    env = dict(os.environ, CHONOI_CONTRACT=BENCH_CONTRACT)
    p = subprocess.run([*headless_cmd(), *args], cwd=ROOT, capture_output=True, text=True, env=env)
    return p.returncode, p.stderr


class GatherBenchFixtureT411Tests(unittest.TestCase):
    def test_bench_fixture_runs_33s_seed_42_with_real_monster_patrol(self):
        with Workdir() as w:
            out = w.path("bench_headless.jsonl")
            code, err = _run_bench_headless(
                "--mode", "gather",
                "--seed", "42",
                "--ticks", str(WARMUP_PLUS_MEASURE_TICKS),
                "--scenario", BENCH_SCENARIO,
                "--snapshot-every", "60",
                "--out", out,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            snaps = snapshots(rows)
            end = rows[-1]

            # Phiên phải còn đang chơi xuyên suốt 33 s (không bị hit/ngất/kết thúc sớm)
            self.assertEqual(end["type"], "end")
            self.assertEqual(end["ticks"], WARMUP_PLUS_MEASURE_TICKS)
            self.assertEqual(end["state"], "playing")
            self.assertEqual(end["reason"], "tick_limit")
            self.assertEqual(events(rows, "monster_hit"), [])
            self.assertEqual(events(rows, "faint"), [])
            self.assertEqual(events(rows, "gather_end"), [])

            # Người chơi đứng yên ở bến mặt nước, đầy Máu & oxy; đủ rau, cá, giỏ và Cá Sấu M1
            first, last = snaps[0], snaps[-1]
            self.assertEqual(first["player"]["pos"], [2.0, 0.0])
            self.assertEqual(last["player"]["pos"], [2.0, 0.0])
            self.assertTrue(last["player"]["at_surface"])
            self.assertEqual(last["player"]["hp"], last["player"]["hp_max"])
            self.assertEqual(last["player"]["oxygen_ticks"], last["player"]["oxygen_max_ticks"])
            self.assertEqual(len(last["nodes"]), 4)
            self.assertEqual(len(last["fish"]), 6)
            self.assertEqual(len(last["hold"]), 3)

            # Cá Sấu M1 phải tuần tra thực sự (di chuyển qua lại [60, 64] và đổi target_idx nhiều lượt)
            m_xs = [s["monsters"][0]["pos"][0] for s in snaps]
            m_targets = {s["monsters"][0]["target_idx"] for s in snaps}
            self.assertTrue(all(len(s["monsters"]) == 1 and s["monsters"][0]["id"] == "M1" for s in snaps))
            self.assertTrue(all(s["monsters"][0]["state"] == "patrol" for s in snaps))
            self.assertEqual(m_targets, {0, 1})
            self.assertGreaterEqual(max(m_xs) - min(m_xs), 3.9)

    def test_bench_fixture_byte_deterministic_seed_42(self):
        with Workdir() as w:
            out1, out2 = w.path("b1.jsonl"), w.path("b2.jsonl")
            for out in (out1, out2):
                code, err = _run_bench_headless(
                    "--mode", "gather",
                    "--seed", "42",
                    "--ticks", str(WARMUP_PLUS_MEASURE_TICKS),
                    "--scenario", BENCH_SCENARIO,
                    "--snapshot-every", "60",
                    "--out", out,
                )
                self.assertEqual(code, 0, err)
            with open(out1, "rb") as a, open(out2, "rb") as b:
                self.assertEqual(a.read(), b.read())

    def test_bench_fixture_loads_and_patrols_in_live_server(self):
        contract = load_contract(BENCH_CONTRACT)
        tuning = contract["tuning"]
        scenario = load_scenario(BENCH_SCENARIO, "gather", tuning)
        server = LiveServer(LiveGame("gather", tuning, scenario, 42, contract=contract), port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            with urllib.request.urlopen(base + "/", timeout=5) as r:
                self.assertEqual(r.status, 200)
                self.assertIn(b"<canvas", r.read())
            with urllib.request.urlopen(base + "/state", timeout=5) as r:
                st0 = json.loads(r.read())
            self.assertEqual(st0["mode"], "gather")
            self.assertEqual(st0["player"]["pos"], [2.0, 0.0])
            self.assertEqual([m["id"] for m in st0["monsters"]], ["M1"])
            x0 = st0["monsters"][0]["pos"][0]

            deadline = time.time() + 3
            st1 = st0
            while time.time() < deadline:
                with urllib.request.urlopen(base + "/state", timeout=5) as r:
                    st1 = json.loads(r.read())
                if st1["tick"] >= st0["tick"] + 5 and st1["monsters"][0]["pos"][0] != x0:
                    break
                time.sleep(0.05)

            self.assertGreater(st1["tick"], st0["tick"])
            self.assertNotEqual(st1["monsters"][0]["pos"][0], x0, "Cá Sấu M1 phải di chuyển thực trong LiveServer")
            self.assertEqual(st1["player"]["pos"], [2.0, 0.0])
        finally:
            server.stop()
        self.assertFalse(server.game._thread.is_alive())
        self.assertFalse(server._thread.is_alive())


if __name__ == "__main__":
    unittest.main()
