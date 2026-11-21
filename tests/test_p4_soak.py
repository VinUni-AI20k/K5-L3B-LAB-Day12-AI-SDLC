"""Phase 4 (TICKET-04, contract v1.3): soak 10 Ngày + schema bench + khóa gốc bench_cmd/soak_cmd."""

import copy
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import bench  # noqa: E402
import soak  # noqa: E402
from chonoi import contract  # noqa: E402
from chonoi.errors import BadInput  # noqa: E402


def _gameplay(res):
    return {k: v for k, v in res.items() if k != "duration_s"}


class SoakP4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = soak.soak(7, 10)
        cls.b = soak.soak(7, 10)

    def test_ten_days_pass(self):
        r = self.a
        self.assertEqual(r["days"], 10)
        self.assertEqual(r["days_completed"], 10, r.get("error"))
        self.assertEqual(r["crashes"], 0)
        self.assertEqual([x["day"] for x in r["results"]], list(range(1, 11)))
        for x in r["results"]:
            self.assertEqual(set(x), {"day", "earned", "reputation", "score"})

    def test_bot_actually_plays_and_progress_carries(self):
        earned = [x["earned"] for x in self.a["results"]]
        self.assertGreater(earned[-1], 0)
        self.assertEqual(earned, sorted(earned))  # earned tích lũy xuyên Ngày, không reset

    def test_deterministic(self):
        self.assertEqual(_gameplay(self.a), _gameplay(self.b))

    def test_cli_writes_out(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "soak.json")
            self.assertEqual(soak.main(["--seed", "3", "--days", "6", "--out", out]), 0)
            with open(out, encoding="utf-8") as f:
                r = json.load(f)
            self.assertEqual(set(r), {"days", "days_completed", "crashes", "results", "duration_s"})
            self.assertEqual(r["days_completed"], 6)


class BenchSchemaP4(unittest.TestCase):
    STUB = {"avg_fps": 60.0, "p1_low_fps": 55.5, "frames": 1800, "measured_s": 30.0, "load_ms": 1234}

    def test_stub_ok(self):
        bench.validate(dict(self.STUB))

    def test_rejects_extra_or_missing_keys(self):
        bad = dict(self.STUB, extra=1)
        with self.assertRaises(ValueError):
            bench.validate(bad)
        bad = dict(self.STUB)
        del bad["load_ms"]
        with self.assertRaises(ValueError):
            bench.validate(bad)

    def test_rejects_inconsistent_avg(self):
        with self.assertRaises(ValueError):
            bench.validate(dict(self.STUB, avg_fps=70.0))

    def test_no_browser_exits_nonzero(self):
        old = os.environ.get("CHONOI_BROWSER")
        os.environ["CHONOI_BROWSER"] = "/khong/co/trinh/duyet"
        try:
            with tempfile.TemporaryDirectory() as d:
                self.assertEqual(bench.main(["--seed", "42", "--duration", "1", "--out", os.path.join(d, "b.json")]), 2)
        finally:
            if old is None:
                del os.environ["CHONOI_BROWSER"]
            else:
                os.environ["CHONOI_BROWSER"] = old

    def test_proof_artifact_schema(self):
        p = os.path.join(ROOT, "docs", "proof", "phase-4", "bench.json")
        if not os.path.exists(p):
            self.skipTest("chưa có docs/proof/phase-4/bench.json")
        with open(p, encoding="utf-8") as f:
            bench.validate(json.load(f))


class ContractV13(unittest.TestCase):
    def test_version_and_root_keys(self):
        c = contract.load_contract()
        self.assertEqual(c["contract_version"], "1.3")
        self.assertTrue(c["bench_cmd"].strip())
        self.assertTrue(c["soak_cmd"].strip())

    def test_missing_root_key_rejected(self):
        c = contract.load_contract()
        for k in ("bench_cmd", "soak_cmd"):
            bad = copy.deepcopy(c)
            del bad[k]
            with self.assertRaises(BadInput):
                contract.validate_root(bad)
        old = copy.deepcopy(c)
        old["contract_version"] = "1.2"
        del old["bench_cmd"]
        contract.validate_root(old)  # v1.2 không bắt buộc


if __name__ == "__main__":
    unittest.main()
