"""Phase 4: benchmark artifact and a 10-day deterministic soak."""

import unittest

from chonoi.benchmark import benchmark
from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.day import DaySim
from chonoi.soak import soak


class Phase4Tools(unittest.TestCase):
    def test_contract_declares_phase4_commands(self):
        contract = load_contract()
        self.assertEqual(contract["contract_version"], "1.3")
        # Nhóm chọn bản có render làm bench_cmd chính thức (chonoi.bench); bản headless chonoi.benchmark vẫn có và được kiểm riêng bên dưới.
        self.assertIn("chonoi.bench", contract["bench_cmd"])
        self.assertIn("soak", contract["soak_cmd"])

    def test_day_six_to_ten_repeat_five_day_plan(self):
        tuning = load_contract()["tuning"]
        sim = DaySim(tuning, {}, Streams(7), IdAllocator(), days=10)
        self.assertEqual(sim._plan_for_day(6)["dishes"], sim._plan_for_day(1)["dishes"])
        self.assertEqual(sim._plan_for_day(10)["dishes"], sim._plan_for_day(5)["dishes"])

    def test_benchmark_emits_five_required_metrics(self):
        result = benchmark(42, 0.03)
        self.assertEqual(set(result), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
        self.assertGreater(result["frames"], 0)
        self.assertGreater(result["measured_s"], 0)

    def test_soak_completes_ten_days_deterministically(self):
        first = soak(7, 10)
        second = soak(7, 10)
        self.assertEqual((first["days"], first["days_completed"], first["crashes"]), (10, 10, 0))
        self.assertEqual([row["day"] for row in first["results"]], list(range(1, 11)))
        self.assertEqual(set(first["results"][0]), {"day", "earned", "reputation", "score"})
        self.assertEqual(first["results"], second["results"])
