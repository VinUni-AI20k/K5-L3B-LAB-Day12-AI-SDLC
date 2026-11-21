"""Quán v1.2 (TICKET-03 §1 "Độ tươi"): hao 0.25/s, spoiled, giữ theo id, giữ lại một lần, giá chốt theo fresh.
Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

AT_STOVE = [2, 8]
AT_TABLE = [9, 2]


def it(i, kind, fresh):
    return {"id": i, "kind": kind, "fresh": fresh}


def cust(cid="C1", table="T1", dish="ca_loc_nuong_trui", tick=0, **kw):
    c = {"id": cid, "table_id": table, "dish_id": dish, "order_tick": tick}
    c.update(kw)
    return c


def run_quan(w, sc, inputs=None, ticks=10, every=1):
    args = ["--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--out", w.path("q.jsonl"),
            "--snapshot-every", str(every), "--scenario", write_json(w.path("sc.json"), {"quan": sc})]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("q.jsonl"))


def code_of(w, sc):
    return run_headless("--mode", "quan", "--seed", "1", "--ticks", "1", "--out", w.path("x.jsonl"),
                        "--scenario", write_json(w.path("bad.json"), {"quan": sc}))[0]


class DoTuoiQuan(unittest.TestCase):
    def test_ac_p3_01_quan_decay_quarter_per_second_exact(self):
        with Workdir() as w:
            rows = run_quan(w, {"random_customers": False, "stock": [it("A1", "ca_loc", 30.25)]}, ticks=61)
            snap = {s["tick"]: s["stock"][0]["fresh"] for s in snapshots(rows)}
            self.assertEqual(snap[0], 30.25)
            self.assertAlmostEqual(snap[60], 30.0, places=2)  # 60 tick = 1 s -> -0.25, đúng ngưỡng: chưa ươn
            self.assertAlmostEqual(snap[61], 30.0 - 1 / 240, places=2)
            sp = events(rows, "spoiled")
            self.assertEqual([(e["tick"], e["data"]) for e in sp],
                             [(61, {"item_id": "A1", "kind": "ca_loc", "location": "stock"})])

    def test_ac_p3_02_spoiled_once_in_id_order_and_kept_in_stock(self):
        with Workdir() as w:
            st = [it("A10", "ca_loc", 30), it("A2", "ca_linh", 30), it("A3", "bong_sung", 0.1)]
            rows = run_quan(w, {"random_customers": False, "stock": st}, ticks=200, every=50)
            sp = events(rows, "spoiled")
            self.assertEqual([(e["tick"], e["data"]["item_id"]) for e in sp], [(1, "A2"), (1, "A10")])
            self.assertEqual([x["id"] for x in snapshots(rows)[-1]["stock"]], ["A2", "A3", "A10"])  # vẫn chiếm chỗ
            self.assertEqual(snapshots(rows)[-1]["stock"][1]["fresh"], 0)  # kẹp đáy 0

    def test_ac_p3_03_reserve_freshest_tie_by_id(self):
        with Workdir() as w:
            st = [it("S1", "ca_loc", 50), it("S3", "ca_loc", 90), it("S2", "ca_loc", 90)]
            rows = run_quan(w, {"random_customers": False, "stock": st, "customers": [cust()]}, ticks=0)
            self.assertEqual(snapshots(rows)[0]["customers"][0]["reserved"], ["S2"])

    def test_ac_p3_04_spoiled_reservation_released_and_rereserved_once(self):
        with Workdir() as w:
            st = [it("S1", "ca_loc", 30), it("S2", "ca_loc", 80), it("S3", "ca_loc", 30)]
            cs = [cust("C1", "T1", reserved=["S1"]), cust("C2", "T2", tick=0, reserved=["S3"])]
            rows = run_quan(w, {"random_customers": False, "stock": st, "customers": cs}, ticks=3)
            self.assertEqual([e["data"]["item_id"] for e in events(rows, "spoiled")], ["S1", "S3"])
            s1 = next(s for s in snapshots(rows) if s["tick"] == 1)
            c1, c2 = s1["customers"]
            self.assertEqual((c1["order_status"], c1["reserved"]), ("reserved", ["S2"]))
            self.assertEqual((c2["order_status"], c2["reserved"]), ("unfulfillable", []))
            self.assertEqual(c2["state"], "waiting")  # khách chờ tới hạn kiên nhẫn
            self.assertEqual(len(events(rows, "spoiled")), 2)  # không phát lại

    def test_ac_p3_05_price_locked_floor_mean_fresh_items_sorted(self):
        with Workdir() as w:
            st = [it("B2", "bong_sung", 50), it("B1", "bong_sung", 100), it("L1", "ca_loc", 100)]
            sc = {"random_customers": False, "player": {"pos": AT_STOVE}, "stock": st,
                  "customers": [cust(dish="goi_bong_sung")]}
            rows = run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=3)
            cs = events(rows, "cook_started")[0]
            self.assertEqual(cs["tick"], 1)
            # floor(40 × mean(100 − 1/240, 50 − 1/240) / 100) = floor(29.998..) = 29
            self.assertEqual(cs["data"]["base_price"], 29)
            self.assertEqual([x["id"] for x in cs["data"]["items"]], ["B1", "B2"])
            self.assertAlmostEqual(cs["data"]["items"][1]["fresh"], 50 - 1 / 240, places=2)
            s = snapshots(rows)[-1]
            self.assertEqual([x["id"] for x in s["stock"]], ["L1"])  # tiêu đúng các id đã giữ
            self.assertEqual(s["stoves"][0]["dish"]["base_price"], 29)  # món chín giữ giá đã chốt

    def test_ac_p3_06_tip_on_locked_price(self):
        with Workdir() as w:
            hand = {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 29}
            sc = {"random_customers": False, "player": {"pos": AT_TABLE}, "hand": hand,
                  "customers": [cust(dish="goi_bong_sung", order_status="assigned")]}
            rows = run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=2)
            d = events(rows, "served")[0]["data"]
            self.assertEqual((d["base_price"], d["tip"]), (29, 5))  # floor(29 × 0.2)

    def test_ac_p3_07_spoiled_items_cannot_cook(self):
        with Workdir() as w:
            st = [it("S1", "ca_loc", 20)]
            rows = run_quan(w, {"random_customers": False, "stock": st, "customers": [cust()]}, ticks=0)
            c = snapshots(rows)[0]["customers"][0]
            self.assertEqual((c["order_status"], c["reserved"]), ("unfulfillable", []))
        with Workdir() as w:
            rows = run_quan(w, {"stock": [it("S1", "ca_loc", 20)]}, ticks=121, every=500)
            self.assertEqual(len(events(rows, "no_dish")), 1)
            self.assertEqual(events(rows, "customer_arrived"), [])

    def test_ac_p3_08_bad_reserved_or_stock_code_2(self):
        bad = [
            {"stock": [it("S1", "ca_loc", 20)], "customers": [cust(reserved=["S1"])]},        # trỏ hàng ươn
            {"stock": [it("S1", "ca_loc", 90)], "customers": [cust(reserved=["X9"])]},        # id không có
            {"stock": [it("S1", "ca_loc", 90)], "customers": [cust(reserved=["S1"]),
                                                              cust("C2", "T2", reserved=["S1"])]},  # dùng chung
            {"stock": [it("S1", "bong_sung", 90)], "customers": [cust(reserved=["S1"])]},     # sai công thức
            {"stock": {"ca_loc": 1}},                                                         # kho đếm cũ
            {"stock": [it("S1", "ca_loc", 101)]},                                             # fresh ngoài miền
            {"stock": [it("S1", "ca_loc", 50), it("S1", "ca_loc", 60)]},                      # id trùng
            {"stock": [it("S1", "ca_la", 50)]},                                               # kind lạ
        ]
        for sc in bad:
            with self.subTest(sc=sc), Workdir() as w:
                self.assertEqual(code_of(w, sc), 2)

    def test_ac_p3_09_pause_stops_decay(self):
        with Workdir() as w:
            sc = {"random_customers": False, "stock": [it("A1", "ca_loc", 50)]}
            rows = run_quan(w, sc, [{"tick": 0, "pause": True}, {"tick": 1, "pause": False}], ticks=5)
            last = snapshots(rows)[-1]
            self.assertEqual(last["sim_tick"], 0)
            self.assertEqual(last["stock"][0]["fresh"], 50)


if __name__ == "__main__":
    unittest.main()
