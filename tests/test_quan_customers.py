import os
import unittest
from helpers import Workdir, read_jsonl, run_headless, write_json


class TestQuanCustomers(unittest.TestCase):
    def test_customer_arrived_at_tick_120(self):
        """Khách C1 đến đúng tick 120 khi có kho khả dụng."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": {"ca_loc": 2}}})
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "120",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, f"Error: {err}")
            rows = read_jsonl(out)
            evs = [r for r in rows if r["type"] == "event" and r["name"] == "customer_arrived"]
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0]["tick"], 120)
            self.assertEqual(evs[0]["data"]["order_id"], "C1")
            self.assertEqual(evs[0]["data"]["table_id"], "T1")

    def test_customer_patience_and_c5_arrival_at_3720(self):
        """Ở tick 3720 (120 + 3600), C1 hết kiên nhẫn bỏ về và C5 xuất hiện (P2 v1.1: 4 bàn T1-T4)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": {"ca_loc": 5}}})
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "3720",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, f"Error: {err}")
            rows = read_jsonl(out)

            arr = [(r["tick"], r["data"]["order_id"], r["data"]["table_id"])
                   for r in rows if r["type"] == "event" and r["name"] == "customer_arrived"]
            self.assertEqual(arr[:4], [(120, "C1", "T1"), (1020, "C2", "T2"),
                                       (1920, "C3", "T3"), (2820, "C4", "T4")])

            left_evs = [r for r in rows if r["type"] == "event" and r["name"] == "customer_left" and r["tick"] == 3720]
            self.assertEqual(len(left_evs), 1)
            self.assertEqual(left_evs[0]["data"]["reason"], "patience")
            self.assertAlmostEqual(left_evs[0]["data"]["reputation"], 2.5)

            # P2 v1.1: 4 bàn T1–T4 đón C1–C4 ở tick 120/1020/1920/2820; tick 3720 C1 rời T1 (patience) và C5 vào T1
            arrived_evs = [r for r in rows if r["type"] == "event" and r["name"] == "customer_arrived" and r["tick"] == 3720]
            self.assertEqual(len(arrived_evs), 1)
            self.assertEqual(arrived_evs[0]["data"]["order_id"], "C5")
            self.assertEqual(arrived_evs[0]["data"]["table_id"], "T1")

    def test_no_dish_when_stock_empty(self):
        """Khi kho rỗng, ở tick 120 bắn event no_dish."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": {}}})
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "120",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, f"Error: {err}")
            rows = read_jsonl(out)
            evs = [r for r in rows if r["type"] == "event" and r["name"] == "no_dish"]
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0]["tick"], 120)

    def test_closing_khong_tru_uy_tin(self):
        """Hết ca khi khách còn chờ: customer_left closing, uy tín giữ nguyên, đứng trước quan_end."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": {"ca_loc": 1}, "time_left_ticks": 200}})
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "300",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, f"Error: {err}")
            rows = read_jsonl(out)
            evs = [r for r in rows if r["type"] == "event"]
            names = [r["name"] for r in evs]
            self.assertEqual(names, ["customer_arrived", "customer_left", "quan_end"])
            left = evs[1]
            self.assertEqual(left["tick"], 200)
            self.assertEqual(left["data"]["reason"], "closing")
            self.assertAlmostEqual(left["data"]["reputation"], 3.0)
            self.assertEqual(rows[-1]["reason"], "time")

    def test_giu_cho_vuot_ton_exit_2(self):
        """Khách scenario giữ chỗ vượt tồn kho hoặc khác công thức -> mã 2, không ghi JSONL."""
        bad = [
            {"stock": {}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]},
            {"stock": {"ca_loc": 1}, "customers": [{"id": "C1", "table_id": "T1",
                                                    "dish_id": "ca_loc_nuong_trui", "reserved": {"ca_loc": 2}}]},
        ]
        for block in bad:
            with self.subTest(block=block), Workdir() as w:
                sc = write_json(w.path("sc.json"), {"quan": block})
                out = w.path("out.jsonl")
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                       "--scenario", sc, "--out", out)
                self.assertEqual(code, 2)
                self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
