"""Quán lát 4 (@minhthu27): nấu, bưng, phục vụ, tiền, boa, uy tín, quan_end. Hộp đen qua headless.

Schema khách theo docs/contracts/customer.md. Test dùng `random_customers: false` nên không phụ thuộc lát 3.
"""

import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

COOK = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
AT_STOVE = {"pos": [2, 8]}


def run(block, fr, ticks, w):
    block = dict({"random_customers": False}, **block)
    sc = write_json(w.path("sc.json"), {"quan": block})
    inp = write_json(w.path("in.json"), frames(*fr))
    out = w.path("o.jsonl")
    code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
                             "--inputs", inp, "--out", out)
    assert code == 0, err
    return read_jsonl(out)


def names(rows):
    return [e["name"] for e in events(rows)]


class QuanService(unittest.TestCase):
    def test_bep_nhan_don_tru_kho_va_nau(self):
        with Workdir() as w:
            rows = run({"stock": {"ca_loc": 1}, "customers": [COOK], "player": AT_STOVE},
                       [{"tick": 0, "interact": True}], 400, w)
            cs = events(rows, "cook_started")[0]
            self.assertEqual(cs["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui"})
            self.assertEqual(cs["tick"], 1)
            self.assertEqual(events(rows, "dish_ready")[0]["tick"], 1 + 360)
            first = snapshots(rows)[1]  # sau khi nhận đơn
            self.assertEqual(first["stock"], {})
            self.assertEqual(first["customers"][0]["order_status"], "assigned")
            self.assertEqual(first["customers"][0]["reserved"], {})

    def test_luong_day_du_den_paid(self):
        with Workdir() as w:
            fr = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                  {"tick": 361, "interact": True}, {"tick": 362, "interact": False, "move": [0.76, -0.65]},
                  {"tick": 500, "move": [0, 0]}, {"tick": 520, "interact": True}]
            rows = run({"stock": {"ca_loc": 1}, "customers": [COOK], "player": AT_STOVE}, fr, 1300, w)
            n = names(rows)
            for e in ("cook_started", "dish_ready", "dish_picked", "served", "paid"):
                self.assertIn(e, n)
            self.assertEqual(n.index("dish_picked") < n.index("served") < n.index("paid"), True)
            paid = events(rows, "paid")[0]["data"]
            self.assertEqual(paid, {"order_id": "C1", "table_id": "T1", "base_price": 60, "tip": 12,
                                    "amount": 72, "reason": "eaten"})
            end = rows[-1]
            self.assertEqual(end["money"], 72)
            self.assertEqual(end["earned"], 72)
            self.assertAlmostEqual(end["reputation"], 3.2)
            self.assertEqual(snapshots(rows)[-1]["customers"], [])
            self.assertIsNone(snapshots(rows)[-1]["hand"])

    def test_thieu_nguyen_lieu_khong_nau(self):
        with Workdir() as w:
            rows = run({"stock": {}, "customers": [dict(COOK, order_status="assigned", reserved={})],
                        "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                        "player": AT_STOVE}, [{"tick": 0, "interact": True}], 5, w)
            self.assertNotIn("cook_started", names(rows))  # không có đơn reserved nào để nhận

    def test_khong_nau_don_unfulfillable(self):
        with Workdir() as w:
            c = dict(COOK, order_status="unfulfillable", reserved={})
            rows = run({"stock": {"ca_loc": 1}, "customers": [c], "player": AT_STOVE},
                       [{"tick": 0, "interact": True}], 5, w)
            self.assertNotIn("cook_started", names(rows))

    def test_khach_an_xong_tra_tien_va_roi_ban(self):
        with Workdir() as w:
            c = dict(COOK, dish_id="goi_bong_sung", state="eating", order_status="served",
                     eat_ticks_left=3, base_price=40, tip=0, reserved={})
            rows = run({"customers": [c]}, [], 5, w)
            self.assertEqual(events(rows, "paid")[0]["tick"], 3)
            self.assertEqual(events(rows, "paid")[0]["data"]["amount"], 40)
            self.assertAlmostEqual(rows[-1]["reputation"], 3.0)  # không boa: uy tín giữ nguyên
            self.assertEqual(snapshots(rows)[-1]["customers"], [])

    def test_kien_nhan_thap_khong_boa(self):
        with Workdir() as w:
            # tay đã cầm món của C1 và đứng cạnh T1; kiên nhẫn dưới 50% -> không boa
            c = dict(COOK, patience_ticks_left=100, reserved={}, order_status="assigned")  # hand giữ món của C1
            hand = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
            rows = run({"customers": [c], "hand": hand, "player": {"pos": [9, 2]}},
                       [{"tick": 0, "interact": True}], 2, w)
            self.assertEqual(events(rows, "served")[0]["data"],
                             {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                              "patience_ticks_left": 99, "base_price": 60, "tip": 0})
            cust = snapshots(rows)[-1]["customers"][0]
            self.assertEqual((cust["state"], cust["order_status"], cust["tip"]), ("eating", "served", 0))

    def test_phuc_vu_nham_ban_khong_duoc(self):
        with Workdir() as w:
            # C1 ngồi T1 giữ món trên tay; C2 ngồi T2 (đang đứng cạnh T2) không phải chủ đơn
            c1 = dict(COOK, order_status="assigned", reserved={})
            c2 = {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "stock": None}
            c2.pop("stock")
            hand = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
            rows = run({"stock": {"bong_sung": 2}, "customers": [c1, c2], "hand": hand,
                        "player": {"pos": [13, 2]}}, [{"tick": 0, "interact": True}], 2, w)
            self.assertNotIn("served", names(rows))

    def test_het_ca_khach_dang_an_tra_ngay_roi_quan_end(self):
        with Workdir() as w:
            c = dict(COOK, state="eating", order_status="served", eat_ticks_left=500, base_price=60, tip=12,
                     reserved={})
            rows = run({"customers": [c], "time_left_ticks": 3}, [], 10, w)
            n = names(rows)
            self.assertEqual(n[-2:], ["paid", "quan_end"])
            self.assertEqual(events(rows, "paid")[0]["data"]["reason"], "closing")
            end_ev = events(rows, "quan_end")[0]["data"]
            self.assertEqual((end_ev["reason"], end_ev["money"], end_ev["earned"]), ("time", 72, 72))

    def test_cung_seed_giong_byte(self):
        with Workdir() as w:
            kw = ({"stock": {"ca_loc": 1}, "customers": [COOK], "player": AT_STOVE},
                  [{"tick": 0, "interact": True}], 500, w)
            self.assertEqual(run(*kw), run(*kw))


if __name__ == "__main__":
    unittest.main()
