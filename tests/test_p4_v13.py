"""Test nền Test Contract v1.3 (LeBao403, Integrator): manifest, kho cá thể ở 1.3, soak_cmd, khung bench_cmd.
Ticket-04 mục 1, 2. Phần vẽ của bench (E) có test riêng.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p "test_p4_v13.py" -v
"""

import copy
import json
import os
import shlex
import subprocess
import time
import unittest

from chonoi import bench
from chonoi.contract import load_contract, validate_commands
from chonoi.errors import BadInput
from chonoi.inventory import read_inventory
from helpers import ROOT, Workdir, frames, read_jsonl, run_headless, snapshots, write_json

CONTRACT = load_contract()


def run_cmd(key, *args):
    cmd = shlex.split(CONTRACT[key])
    p = subprocess.run([*cmd, *args], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stderr


class Manifest(unittest.TestCase):
    def test_v13_khai_lenh(self):
        self.assertEqual(CONTRACT["contract_version"], "1.3")
        self.assertEqual(CONTRACT["bench_cmd"], "python3 -m chonoi.bench")
        self.assertEqual(CONTRACT["soak_cmd"], "python3 -m chonoi.soak")
        self.assertIn("freshness", CONTRACT["tuning"])  # gameplay, kho, JSONL như 1.2

    def test_thieu_lenh_bi_tu_choi(self):
        for key in ("bench_cmd", "soak_cmd"):
            c = copy.deepcopy(CONTRACT)
            c[key] = "  "
            with self.assertRaises(BadInput, msg=key):
                validate_commands("1.3", c)
        validate_commands("1.2", {})  # bản cũ không cần


class InventoryV13(unittest.TestCase):
    def test_kho_ca_the_o_13(self):
        with Workdir() as w:
            p = write_json(w.path("k.json"), {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 97.5}]})
            self.assertEqual(read_inventory(p, "1.3"), [{"id": "I1", "kind": "ca_loc", "u": 23400}])
            with self.assertRaises(BadInput):
                read_inventory(write_json(w.path("d.json"), {"items": {"ca_loc": 1}}), "1.3")

    def test_ban_giao_file_gather_sang_quan(self):
        """Smoke bàn giao theo Ticket-03 ở contract 1.3: cập bến tick 0, quán đọc đúng id, kind, fresh."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}],
                                                           "random_fish": False, "monsters": []}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "42", "--scenario", sc, "--inputs", inp,
                                     "--ticks", "1", "--out", w.path("g.jsonl"), "--inventory-out", w.path("k.json"))
            self.assertEqual(code, 0, err)
            with open(w.path("k.json"), encoding="utf-8") as f:
                saved = json.load(f)["items"]
            self.assertEqual([(x["id"], x["kind"]) for x in saved], [("I1", "ca_linh")])
            code, err = run_headless("--mode", "quan", "--seed", "42", "--inventory", w.path("k.json"),
                                     "--ticks", "0", "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            stock = snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"]
            self.assertEqual([(x["id"], x["kind"]) for x in stock], [("I1", "ca_linh")])
            self.assertAlmostEqual(stock[0]["fresh"], saved[0]["fresh"], delta=0.01)


class Soak(unittest.TestCase):
    def soak(self, w, name, days, seed=7):
        code, err = run_cmd("soak_cmd", "--seed", str(seed), "--days", str(days), "--out", w.path(name))
        self.assertEqual(code, 0, err)
        with open(w.path(name), encoding="utf-8") as f:
            return json.load(f)

    def test_soak_dat_va_dung_cau_truc(self):
        with Workdir() as w:
            r = self.soak(w, "s.json", 3)
        self.assertEqual(set(r), {"days", "days_completed", "crashes", "results", "duration_s"})
        self.assertEqual((r["days"], r["days_completed"], r["crashes"]), (3, 3, 0))
        self.assertEqual([x["day"] for x in r["results"]], [1, 2, 3])
        for x in r["results"]:
            self.assertEqual(set(x), {"day", "earned", "reputation", "score"})
            self.assertEqual(x["score"], x["earned"] + 100 * int(x["reputation"] // 1))
        self.assertGreater(r["results"][-1]["earned"], 0, "bot phải bán được món")

    def test_soak_tat_dinh_bo_qua_thoi_gian_thuc(self):
        with Workdir() as w:
            a, b = self.soak(w, "a.json", 2), self.soak(w, "b.json", 2)
        for r in (a, b):
            r.pop("duration_s")
        self.assertEqual(a, b)

    def test_soak_tham_so_sai_ma_2(self):
        with Workdir() as w:
            for args in (("--seed", "7", "--days", "0"), ("--seed", "x", "--days", "1"), ("--days", "1")):
                code, _ = run_cmd("soak_cmd", *args, "--out", w.path("s.json"))
                self.assertEqual(code, 2, args)


class FakeRenderer:
    """Thay cửa sổ thật: mỗi khung "vẽ" mất ~2 ms."""

    def __init__(self):
        self.opened, self.closed, self.draws = None, False, 0

    def open(self, w, h):
        self.opened = (w, h)

    def draw(self, snapshot):
        assert snapshot["mode"] == "gather"
        self.draws += 1
        time.sleep(0.002)
        return True

    def close(self):
        self.closed = True


class Bench(unittest.TestCase):
    def test_cong_thuc_chi_so(self):
        m = bench.compute_metrics([0.01] * 99 + [0.05], 1.04, 1234.4)
        self.assertEqual((m["frames"], m["measured_s"], m["load_ms"]), (100, 1.04, 1234))
        self.assertAlmostEqual(m["avg_fps"], 100 / 1.04, places=2)
        self.assertAlmostEqual(m["p1_low_fps"], 20.0, places=2)  # ceil(1% × 100) = 1 khung chậm nhất 0.05 s
        m = bench.compute_metrics([0.02] * 150 + [0.1, 0.06], 3.2, 10)
        self.assertAlmostEqual(m["p1_low_fps"], 1 / 0.08, places=2)  # ceil(1.52) = 2 khung: (0.1 + 0.06) / 2

    def test_khung_do_voi_renderer_gia(self):
        r = FakeRenderer()
        m = bench.run(42, 0.3, renderer=r, warmup=0.1)
        self.assertEqual(set(m), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
        self.assertEqual(r.opened, (1280, 720))
        self.assertTrue(r.closed)
        # chỉ kiểm quan hệ giữa các trường, không kiểm tốc độ tuyệt đối (máy chạy test có thể đang bận)
        self.assertGreaterEqual(m["frames"], 1)
        self.assertGreaterEqual(m["measured_s"], 0.3)
        self.assertGreater(r.draws, m["frames"])  # có khung làm nóng không tính
        self.assertAlmostEqual(m["avg_fps"], m["frames"] / m["measured_s"], delta=max(0.5, 0.01 * m["avg_fps"]))
        self.assertLessEqual(m["p1_low_fps"], m["avg_fps"] + 0.01)

    def test_bench_tham_so_sai_ma_2(self):
        with Workdir() as w:
            for args in (("--seed", "42", "--duration", "0"), ("--seed", "42", "--duration", "-1"), ("--duration", "1")):
                code, _ = run_cmd("bench_cmd", *args, "--out", w.path("b.json"))
                self.assertEqual(code, 2, args)
            self.assertFalse(os.path.exists(w.path("b.json")))


if __name__ == "__main__":
    unittest.main()
