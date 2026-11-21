"""P4-02 (AC-P4-01): game.contract.json 1.3 khai `bench_cmd` và `soak_cmd` ở gốc; chạy lệnh khai báo như hộp đen."""

import json
import os
import subprocess
import unittest

from helpers import ROOT, Workdir, contract_cmd, write_json

from chonoi.contract import load_contract
from chonoi.errors import BadInput

with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as _f:
    RAW = json.load(_f)


def load_variant(**changes):
    """Nạp bản sao của contract với các khóa gốc đổi hoặc bỏ (None = bỏ)."""
    data = {**RAW}
    for k, v in changes.items():
        if v is None:
            data.pop(k, None)
        else:
            data[k] = v
    with Workdir() as w:
        return load_contract(write_json(w.path("c.json"), data))


class Manifest(unittest.TestCase):
    def test_v13_declares_both_commands_at_root(self):
        self.assertEqual(RAW["contract_version"], "1.3")
        self.assertEqual((RAW["bench_cmd"], RAW["soak_cmd"]), ("python3 -m chonoi.bench", "python3 -m chonoi.soak"))
        self.assertEqual(load_contract()["contract_version"], "1.3")

    def test_v13_requires_both_commands(self):
        for key in ("bench_cmd", "soak_cmd"):
            with self.assertRaises(BadInput, msg=key):
                load_variant(**{key: None})

    def test_commands_must_be_non_empty_parsable_strings(self):
        for bad in ("", "   ", 5, ["python3"], 'python3 -m "chonoi.bench'):
            with self.assertRaises(BadInput, msg=repr(bad)):
                load_variant(bench_cmd=bad)

    def test_older_versions_do_not_need_the_commands(self):
        for version in ("1.1", "1.2"):
            c = load_variant(contract_version=version, bench_cmd=None, soak_cmd=None)
            self.assertNotIn("bench_cmd", c)

    def test_other_commands_unchanged(self):
        self.assertEqual(RAW["headless_cmd"], "python3 -m chonoi.headless")


class DeclaredCommands(unittest.TestCase):
    def run_cmd(self, key, *args):
        return subprocess.run([*contract_cmd(key), *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=120)

    def test_bench_cmd_runs_with_the_ticket_arguments_shape(self):
        with Workdir() as w:
            p = self.run_cmd("bench_cmd", "--seed", "42", "--duration", "0.05", "--warmup", "0", "--out", w.path("b.json"))
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(w.path("b.json"), encoding="utf-8") as f:
                data = json.load(f)
        self.assertEqual(set(data), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})

    def test_soak_cmd_runs_with_the_ticket_arguments_shape(self):
        with Workdir() as w:
            p = self.run_cmd("soak_cmd", "--seed", "7", "--days", "1", "--out", w.path("s.json"))
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(w.path("s.json"), encoding="utf-8") as f:
                data = json.load(f)
        self.assertEqual(set(data), {"days", "days_completed", "crashes", "results", "duration_s"})
        self.assertEqual((data["days"], data["days_completed"], data["crashes"]), (1, 1, 0))


if __name__ == "__main__":
    unittest.main()
