"""TV3 Phase 3 · AC-P3-03: kho cá thể, hao tươi, spoiled, giữ lại / unfulfillable."""

import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class QuanFreshness(unittest.TestCase):
    def run_quan(self, scenario, ticks, seed=1, inputs=None):
        with Workdir() as w:
            sc = write_json(w.path("s.json"), {"quan": scenario})
            args = [
                "--mode", "quan", "--seed", str(seed), "--ticks", str(ticks),
                "--scenario", sc, "--snapshot-every", "1", "--out", w.path("out.jsonl"),
            ]
            if inputs is not None:
                args.extend(["--inputs", write_json(w.path("in.json"), inputs)])
            code, err = run_headless(*args)
            self.assertEqual(code, 0, err)
            return read_jsonl(w.path("out.jsonl"))

    def test_stock_decays_and_spoiled_event(self):
        """fresh=30 → ươn ở bước đầu quán (0.25/s), spoiled theo id."""
        rows = self.run_quan({
            "stock": [
                {"id": "I2", "kind": "ca_loc", "fresh": 30},
                {"id": "I1", "kind": "ca_linh", "fresh": 30},
            ],
            "random_customers": False,
            "time_left_ticks": 5,
        }, ticks=1)
        spoiled = events(rows, "spoiled")
        self.assertEqual([(e["data"]["item_id"], e["data"]["location"]) for e in spoiled],
                         [("I1", "stock"), ("I2", "stock")])
        snap = snapshots(rows)[-1]
        self.assertTrue(all(u["fresh"] < 30 for u in snap["stock"]))

    def test_reserve_picks_freshest_then_id(self):
        rows = self.run_quan({
            "stock": [
                {"id": "I1", "kind": "ca_loc", "fresh": 80},
                {"id": "I2", "kind": "ca_loc", "fresh": 95},
                {"id": "I3", "kind": "ca_loc", "fresh": 95},
            ],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}],
            "random_customers": False,
            "time_left_ticks": 5,
        }, ticks=0)
        # tươi nhất rồi id nhỏ: I2 trước I3
        self.assertEqual(snapshots(rows)[0]["customers"][0]["reserved"], ["I2"])

    def test_spoiled_reserved_rereserves_or_unfulfillable(self):
        """Phần giữ vừa ươn → nhả toàn bộ, thử giữ lại một lần; thiếu → unfulfillable."""
        # Chỉ 1 cá thể ca_loc; khi ươn không còn hàng tươi để giữ lại.
        rows = self.run_quan({
            "stock": [{"id": "I9", "kind": "ca_loc", "fresh": 30}],
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "reserved": ["I9"], "patience_ticks_left": 9999,
            }],
            "random_customers": False,
            "time_left_ticks": 10,
        }, ticks=1)
        self.assertEqual(events(rows, "spoiled")[0]["data"]["item_id"], "I9")
        c = snapshots(rows)[-1]["customers"][0]
        self.assertEqual(c["order_status"], "unfulfillable")
        self.assertEqual(c["reserved"], [])

    def test_spoiled_rereserve_succeeds_with_fresher_item(self):
        rows = self.run_quan({
            "stock": [
                {"id": "I1", "kind": "ca_loc", "fresh": 30},
                {"id": "I2", "kind": "ca_loc", "fresh": 90},
            ],
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "reserved": ["I1"], "patience_ticks_left": 9999,
            }],
            "random_customers": False,
            "time_left_ticks": 10,
        }, ticks=1)
        c = snapshots(rows)[-1]["customers"][0]
        self.assertEqual(c["order_status"], "reserved")
        self.assertEqual(c["reserved"], ["I2"])

    def test_cook_consumes_ids_and_prices_by_fresh(self):
        """TV3 bàn giao reserved ids; nấu tiêu đúng id và floor(giá × avg_fresh/100)."""
        # Bước 1 hao tươi trước interact: fresh 50 → 50 - 0.25/60
        fresh_after = 50 - 0.25 / 60
        expected_price = int(60 * fresh_after / 100)  # floor via int toward 0 for positive
        rows = self.run_quan({
            "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 50}],
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "reserved": ["I1"],
            }],
            "player": {"pos": [2, 8]},
            "random_customers": False,
            "time_left_ticks": 400,
        }, ticks=1, inputs=frames({"tick": 0, "interact": True}))
        started = events(rows, "cook_started")
        self.assertEqual(len(started), 1)
        self.assertEqual(started[0]["data"]["base_price"], expected_price)
        item = started[0]["data"]["items"][0]
        self.assertEqual(item["id"], "I1")
        self.assertEqual(item["kind"], "ca_loc")
        # JSONL làm tròn 3 chữ số khi xuất
        self.assertAlmostEqual(item["fresh"], fresh_after, places=3)
        self.assertEqual(snapshots(rows)[-1]["stock"], [])

    def test_count_stock_still_works_for_regression(self):
        """Kho đếm v1.1 vẫn chạy (dual mode) cho đến khi TV1 bật 1.2."""
        rows = self.run_quan({
            "stock": {"ca_loc": 1},
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}],
            "random_customers": False,
            "time_left_ticks": 5,
        }, ticks=0)
        self.assertEqual(snapshots(rows)[0]["customers"][0]["reserved"], {"ca_loc": 1})
