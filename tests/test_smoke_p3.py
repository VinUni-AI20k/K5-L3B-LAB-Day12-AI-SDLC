"""Smoke Phase 3 (TICKET-03 §1): bàn giao kho cá thể qua file, day --days 2, kho đếm -> mã 2.
Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

FIXTURE = {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}], "random_fish": False, "monsters": []}}


class SmokeP3(unittest.TestCase):
    def test_ac_p3_30_handover_file_gather_to_quan_exact(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), FIXTURE)
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc,
                                     "--inputs", inp, "--inventory-out", w.path("kho.json"), "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(w.path("kho.json"), encoding="utf-8") as f:
                kho = json.load(f)["items"]
            self.assertEqual([(x["id"], x["kind"]) for x in kho], [("I1", "ca_linh")])
            self.assertAlmostEqual(kho[0]["fresh"], 100 - 2 / 240, places=2)  # một lần hao ở gather (0.5/s)
            code, err = run_headless("--mode", "quan", "--seed", "1", "--inventory", w.path("kho.json"),
                                     "--ticks", "0", "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            stock = snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"]
            self.assertEqual([(x["id"], x["kind"]) for x in stock], [(x["id"], x["kind"]) for x in kho])
            for a, b in zip(stock, kho):
                self.assertAlmostEqual(a["fresh"], b["fresh"], delta=0.01)

    def test_ac_p3_31_quan_rejects_count_schema_inventory(self):
        with Workdir() as w:
            kho = write_json(w.path("kho.json"), {"items": {"ca_loc": 1}})
            code, _ = run_headless("--mode", "quan", "--seed", "1", "--inventory", kho, "--ticks", "0",
                                   "--out", w.path("q.jsonl"))
            self.assertEqual(code, 2)

    def test_ac_p3_32_day_two_days_handover_same_tick_and_new_ids(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                                                           "random_fish": False, "monsters": []}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False}))
            code, err = run_headless("--mode", "day", "--days", "2", "--seed", "3", "--ticks", "30000",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("d.jsonl"),
                                     "--snapshot-every", "100000")
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("d.jsonl"))
            g_end = events(rows, "gather_end")[0]
            q_open = next(r for r in rows if r["type"] == "snapshot" and r["phase"] == "quan")
            self.assertEqual(q_open["tick"], g_end["tick"])  # bàn giao cùng tick
            self.assertEqual([(x["id"], x["kind"]) for x in q_open["stock"]], [("I1", "ca_loc")])
            self.assertAlmostEqual(q_open["stock"][0]["fresh"], 100 - 2 / 240, places=2)  # không hao thêm
            self.assertEqual(rows[-1]["type"], "end")


if __name__ == "__main__":
    unittest.main()
