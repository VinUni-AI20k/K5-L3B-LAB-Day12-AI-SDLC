"""Test Phase 3 — Lát 2: Độ tươi, cá thể, hao tươi, spoiled, kho cá thể v1.2."""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class FreshnessAndIndividualItems(unittest.TestCase):
    def test_spoiled_event_at_threshold_30(self):
        """Ticket-03 mẫu: Cá thể bắt đầu đúng fresh 30 nên ươn ở bước đầu."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30.0}],
                    "random_fish": False,
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            sp = events(rows, "spoiled")
            self.assertEqual(len(sp), 1)
            self.assertEqual(sp[0]["tick"], 1)
            self.assertEqual(sp[0]["data"], {"item_id": "I1", "kind": "ca_linh", "location": "hold"})

    def test_freshness_decay_in_hold(self):
        """Hao tươi trong giỏ 0.5/s: sau 60 tick (1s), fresh giảm đúng 0.5."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100.0}],
                    "random_fish": False,
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "60",
                                     "--scenario", sc, "--snapshot-every", "60", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            last_snap = snapshots(rows)[-1]
            item = last_snap["hold"][0]
            self.assertEqual(item["id"], "I1")
            self.assertAlmostEqual(item["fresh"], 99.5, places=2)

    def test_harvest_creates_individual_item_fresh_100(self):
        """Hái nút N1 tạo cá thể mới với id I1, fresh=100.0."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [12.0, 0.0]},
                    "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12.0, 0.0]}],
                    "fish": [],
                    "random_fish": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            snap = snapshots(rows)[-1]
            self.assertEqual(len(snap["hold"]), 1)
            item = snap["hold"][0]
            self.assertEqual(item["id"], "I1")
            self.assertEqual(item["kind"], "bong_dien_dien")
            self.assertEqual(item["fresh"], 100.0)

    def test_catch_ca_linh_yield_creates_3_individual_items(self):
        """Bắt ca_linh (yield=3) tạo 3 cá thể riêng biệt I1, I2, I3 đều có fresh=100.0."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [15.0, 5.0]},
                    "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, 5.0]}],
                    "random_fish": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            snap = snapshots(rows)[-1]
            self.assertEqual(len(snap["hold"]), 3)
            self.assertEqual([x["id"] for x in snap["hold"]], ["I1", "I2", "I3"])
            self.assertTrue(all(x["fresh"] == 100.0 for x in snap["hold"]))
            self.assertTrue(all(x["kind"] == "ca_linh" for x in snap["hold"]))

    def test_handover_v12_inventory_file(self):
        """Bàn giao file kho v1.2: mảng cá thể {id, kind, fresh}, quán đọc đúng."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100.0}],
                    "random_fish": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--inputs", inp, "--inventory-out", inv,
                                     "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("items", data)
            self.assertIsInstance(data["items"], list)
            item = data["items"][0]
            self.assertEqual(item["id"], "I1")
            self.assertEqual(item["kind"], "ca_linh")
            self.assertAlmostEqual(item["fresh"], 99.992, places=3)

            # Quán đọc file kho v1.2
            code_q, err_q = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                         "--inventory", inv, "--out", w.path("q.jsonl"))
            self.assertEqual(code_q, 0, err_q)
            q_snap = snapshots(read_jsonl(w.path("q.jsonl")))[0]
            # File kho giữ đủ độ chính xác (TICKET-03 mục 1), JSONL làm tròn 3 số -> id/kind khớp
            # chính xác, fresh theo dung sai quan sát ±0.01.
            self.assertEqual([(x["id"], x["kind"]) for x in q_snap["stock"]],
                             [(x["id"], x["kind"]) for x in data["items"]])
            for a, b in zip(q_snap["stock"], data["items"]):
                self.assertAlmostEqual(a["fresh"], b["fresh"], delta=0.01)

    def test_reject_count_inventory_in_v12(self):
        """Contract v1.2 từ chối file kho đếm kiểu cũ {"items": {"ca_loc": 1}} với mã thoát 2."""
        with Workdir() as w:
            bad_inv = write_json(w.path("bad.json"), {"items": {"ca_loc": 1}})
            code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                   "--inventory", bad_inv, "--out", w.path("q.jsonl"))
            self.assertEqual(code, 2)

    def test_faint_lifo_lost_and_empty_inventory(self):
        """Ngất: lost là mảng cá thể theo thứ tự LIFO, kho xuất rỗng {"items": []}."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [20.0, 2.0], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                    "hold": [
                        {"id": "I1", "kind": "ca_loc", "fresh": 95.0},
                        {"id": "I2", "kind": "bong_sung", "fresh": 98.0},
                    ],
                    "nodes": [],
                    "fish": [],
                    "random_fish": False,
                }
            })
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inventory-out", inv, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            faints = events(rows, "faint")
            self.assertEqual(len(faints), 1)
            lost = faints[0]["data"]["lost"]
            # Thứ tự LIFO: I2 nhặt sau nên đứng trước I1
            self.assertEqual(lost[0]["id"], "I2")
            self.assertEqual(lost[1]["id"], "I1")

            # File kho rỗng
            with open(inv, encoding="utf-8") as f:
                inv_data = json.load(f)
            self.assertEqual(inv_data, {"items": []})


if __name__ == "__main__":
    unittest.main()
