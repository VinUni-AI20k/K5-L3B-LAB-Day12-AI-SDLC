"""Lát 0 Phase 4 (AC-P4-01): Test Contract v1.3 — `contract_version: "1.3"`, `bench_cmd`, `soak_cmd` ở gốc manifest;
gameplay, tuning, kho và JSONL giữ nguyên v1.2 (docs/prd/phase-4.md mục 1 "Đóng gói và phát hành").
"""

import copy
import json
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

with open("game.contract.json", encoding="utf-8") as _f:
    MANIFEST = json.load(_f)


class ManifestV13(unittest.TestCase):
    def test_goc_manifest_khai_ba_lenh_v13(self):
        self.assertEqual(MANIFEST["contract_version"], "1.3")
        self.assertEqual(MANIFEST["bench_cmd"], "python3 -m chonoi.bench")
        self.assertEqual(MANIFEST["soak_cmd"], "python3 -m chonoi.soak")
        self.assertEqual(MANIFEST["headless_cmd"], "python3 -m chonoi.headless")
        self.assertEqual(MANIFEST["tuning"]["freshness"],
                         {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30})
        load_contract()  # manifest thật hợp lệ

    def test_v13_mau_thuan_thi_ma_2(self):
        with Workdir() as w:
            cases = []
            for key in ("bench_cmd", "soak_cmd"):
                m = copy.deepcopy(MANIFEST)
                del m[key]
                cases.append((f"thiếu {key}", m))
                m = copy.deepcopy(MANIFEST)
                m[key] = "  "
                cases.append((f"{key} rỗng", m))
                m = copy.deepcopy(MANIFEST)
                m[key] = ["python3", "-m", "x"]
                cases.append((f"{key} không phải chuỗi", m))
            m = copy.deepcopy(MANIFEST)
            del m["tuning"]["freshness"]
            cases.append(("1.3 thiếu freshness", m))
            for name, m in cases:
                with self.assertRaises(BadInput, msg=name):
                    load_contract(write_json(w.path("m.json"), m))

    def test_ban_cu_van_doc_duoc(self):
        """Code vẫn nhận 1.2 (cùng luật) và 1.1 (không freshness) như Ticket-03 cho phép lúc chuyển."""
        with Workdir() as w:
            m = copy.deepcopy(MANIFEST)
            m["contract_version"] = "1.2"
            load_contract(write_json(w.path("v12.json"), m))
            m["contract_version"] = "1.1"
            del m["tuning"]["freshness"]
            load_contract(write_json(w.path("v11.json"), m))


class GameplayGiuV12(unittest.TestCase):
    def test_smoke_ban_giao_kho_giong_v12(self):
        """Mẫu smoke Ticket-03 chạy trên manifest 1.3: file kho, gather_end và stock của quán khớp id/kind/fresh."""
        hold = [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 30.1}]
        with Workdir() as w:
            inv = w.path("kho.json")
            code, err = run_headless("--mode", "gather", "--seed", "42", "--ticks", "1",
                                     "--scenario", write_json(w.path("sc.json"), {"gather": {"hold": hold}}),
                                     "--inputs", write_json(w.path("in.json"), frames({"tick": 0, "interact": True})),
                                     "--inventory-out", inv, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved, {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 99.992},
                                               {"id": "I2", "kind": "bong_sung", "fresh": 30.092}]})
            self.assertEqual(events(read_jsonl(w.path("g.jsonl")), "gather_end")[0]["data"]["inventory"], saved)
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "0", "--inventory", inv,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], saved["items"])


if __name__ == "__main__":
    unittest.main()
