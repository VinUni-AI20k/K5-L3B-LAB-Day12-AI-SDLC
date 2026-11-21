"""Smoke Phase 2 (Test Contract v1.1 mục 5): gather --inventory-out -> quan --inventory (6 loại),
day --days 1 trọn vòng, tất định byte. Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json
from v12_compat import counts, read_jsonl, write_json  # v1.2: fixture kho đếm -> kho cá thể (lý do: tests/v12_compat.py)


class SmokeP2(unittest.TestCase):
    def test_ac_p2_90_integration_gather_to_quan_tick0_stock(self):
        hold = ["ca_loc", "ca_keo", "ca_keo", "keo_neo", "bong_sung", "bong_sung", "ca_linh"]
        with Workdir() as w:
            sc = write_json(w.path("dock.json"), {"gather": {"hold": hold, "random_fish": False}})
            di = write_json(w.path("di.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "42", "--scenario", sc, "--inputs", di,
                                     "--ticks", "5", "--out", w.path("g.jsonl"), "--inventory-out", w.path("kho.json"))
            self.assertEqual(code, 0, err)
            want = {"bong_sung": 2, "ca_keo": 2, "ca_linh": 1, "ca_loc": 1, "keo_neo": 1}
            with open(w.path("kho.json"), encoding="utf-8") as f:
                # v1.2: file kho là mảng cá thể; so số lượng theo loại
                self.assertEqual(counts(json.load(f)["items"]), want)
            g_end = events(read_jsonl(w.path("g.jsonl")), "gather_end")[0]["data"]
            self.assertEqual(g_end["inventory"], {"items": want})
            code, err = run_headless("--mode", "quan", "--seed", "42", "--inventory", w.path("kho.json"),
                                     "--ticks", "0", "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], want)

    def test_ac_p2_91_day_one_full_loop_and_deterministic(self):
        outs = []
        for _ in range(2):
            with Workdir() as w:
                code, err = run_headless("--mode", "day", "--days", "1", "--seed", "7", "--ticks", "30000",
                                         "--out", w.path("d.jsonl"), "--snapshot-every", "600")
                self.assertEqual(code, 0, err)
                with open(w.path("d.jsonl"), "rb") as f:
                    outs.append(f.read())
                rows = read_jsonl(w.path("d.jsonl"))
                end = rows[-1]
                self.assertEqual((end["mode"], end["reason"], end["days_completed"], end["ticks"]),
                                 ("day", "days_complete", 1, 22200))
                self.assertEqual([e["name"] for e in events(rows) if e["name"] in
                                  ("day_start", "phase_start", "gather_end", "quan_end", "shop_end")],
                                 ["day_start", "phase_start", "gather_end", "phase_start", "quan_end",
                                  "phase_start", "shop_end"])
        self.assertEqual(outs[0], outs[1])


if __name__ == "__main__":
    unittest.main()
