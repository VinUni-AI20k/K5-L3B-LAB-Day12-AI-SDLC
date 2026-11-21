"""Quán Phase 2 (Test Contract v1.1 mục 1.3, 2, 4.5 "Quán"), hộp đen qua headless_cmd.
Mỗi test ghi AC tương ứng trong docs/verification/phase-2.md.
Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import json
import os
import unittest

from helpers import ROOT, Workdir, events, read_jsonl, snapshots
from v12_compat import read_jsonl  # v1.2: fixture kho đếm -> kho cá thể (lý do: tests/v12_compat.py)
from test_quan_p1 import customer, run_quan

FULL = {"ca_loc": 9, "ca_linh": 9, "ca_keo": 9, "keo_neo": 9, "bong_dien_dien": 9, "bong_sung": 9}


def contract():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


class QuanV11(unittest.TestCase):
    def test_ac_p2_30_two_stoves_four_tables_six_dishes_from_contract(self):
        c = contract()
        self.assertIn(c["contract_version"], ("1.2", "1.3"))  # v1.2 (TICKET-03) thay 1.1; dữ liệu 2 bếp/4 bàn/6 món giữ
        self.assertEqual(len(c["tuning"]["menu"]), 6)
        with Workdir() as w:
            s = snapshots(run_quan(w, None, ticks=0))[0]
            self.assertEqual([(x["id"], x["pos"]) for x in s["stoves"]], [("B1", [2, 8]), ("B2", [5, 8])])
            self.assertEqual([(x["id"], x["pos"]) for x in s["tables"]],
                             [("T1", [9, 2]), ("T2", [13, 2]), ("T3", [9, 6]), ("T4", [13, 6])])

    def test_ac_p2_31_schedule_120_plus_900k_smallest_free_table(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": FULL}, ticks=2821, every=5000)
            arr = events(rows, "customer_arrived")
            self.assertEqual([(e["tick"], e["data"]["table_id"]) for e in arr],
                             [(120, "T1"), (1020, "T2"), (1920, "T3"), (2820, "T4")])

    def test_ac_p2_32_two_stoves_take_oldest_reserved_by_order_tick_then_table(self):
        with Workdir() as w:
            sc = {"random_customers": False, "player": {"pos": [2, 8]}, "stock": {"ca_loc": 3},
                  "customers": [customer(id="C1", table_id="T2", order_tick=5),
                                customer(id="C2", table_id="T1", order_tick=5),
                                customer(id="C3", table_id="T3", order_tick=3)]}
            inputs = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False, "move": [1, 0]},
                      {"tick": 40, "move": [0, 0]}, {"tick": 60, "interact": True}]
            rows = run_quan(w, sc, inputs, ticks=62, every=100)
            cs = [(e["data"]["stove_id"], e["data"]["order_id"]) for e in events(rows, "cook_started")]
            self.assertEqual(cs, [("B1", "C3"), ("B2", "C2")])
            st = snapshots(rows)[-1]["stoves"]
            self.assertEqual([x["state"] for x in st], ["cooking", "cooking"])

    def test_ac_p2_33_new_dish_lau_mam_recipe_cook_time_price(self):
        with Workdir() as w:
            stock = {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}
            sc = {"random_customers": False, "player": {"pos": [2, 8]}, "stock": stock,
                  "customers": [customer(dish_id="lau_mam")]}
            rows = run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=722, every=1000)
            cs = events(rows, "cook_started")[0]["data"]
            self.assertEqual(cs["items"], ["bong_dien_dien", "ca_keo", "ca_linh", "ca_linh", "keo_neo"])
            self.assertEqual(cs["base_price"], 199)  # v1.2: floor(200 × 99.9958/100), giá chốt theo fresh
            self.assertEqual(events(rows, "dish_ready")[0]["tick"], 1 + 12 * 60)
            self.assertEqual(snapshots(rows)[-1]["stock"], {})

    def test_ac_p2_34_standalone_quan_uses_all_six_dishes(self):
        picks = set()
        for seed in range(1, 25):
            with Workdir() as w:
                rows = run_quan(w, {"stock": FULL}, ticks=120, every=500, seed=seed)
                picks.add(events(rows, "customer_arrived")[0]["data"]["dish_id"])
        self.assertEqual(picks, set(contract()["tuning"]["menu"]))

    def test_ac_p2_35_no_dish_when_table_free_but_nothing_cookable(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_keo": 1, "keo_neo": 1}}, ticks=121, every=500)
            self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [120])


if __name__ == "__main__":
    unittest.main()
