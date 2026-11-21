"""Test hộp đen buổi tối (quan) theo PRD-0 mục F "Quán", D (fixture), E (sự kiện).

Mỗi test ghi mã AC-P1-xx (bảng chi tiết: docs/verification/phase-1-qa-tests.md). Lát 1–4 đã merge nên mọi test chạy thật.
Số trong test suy từ preset (patience 60 s = 3600 tick, eat 10 s = 600, cook cá lóc 6 s = 360, giá 60, boa 20%).
"""

import os
import unittest

from helpers import Workdir, close, events, run_headless, write_json
from qa_helpers import press, run_case, snap_at
from legacy_v11 import setUpModule, tearDownModule  # noqa: F401  v1.2: fixture kho đếm chạy trên manifest v1.1 tạm, xem tests/legacy_v11.py

CA_LOC = "ca_loc_nuong_trui"
NEAR_STOVE = [2, 8]       # đúng vị trí B1
NEAR_TABLE = [9, 2.5]     # cách T1 [9,2] 0.5 m


def sc(**kw) -> dict:
    base = {"random_customers": False}
    base.update(kw)
    return base


def customer(**kw) -> dict:
    c = {"id": "C1", "table_id": "T1", "dish_id": CA_LOC}
    c.update(kw)
    return c


def hand_payload() -> dict:
    return {"order_id": "C1", "dish_id": CA_LOC, "base_price": 60}


def data_at(rows, name) -> list:
    return [(e["tick"], e["data"]) for e in events(rows, name)]


def one(test, rows, name) -> dict:
    """data của sự kiện `name`, bắt buộc xuất hiện đúng một lần."""
    found = events(rows, name)
    test.assertEqual(len(found), 1, f"cần đúng 1 sự kiện {name}, có {len(found)}")
    return found[0]["data"]


class Customers(unittest.TestCase):
    def test_ac_p1_20_khach_dau_o_first_customer_tick_va_giu_cho(self):
        rows, _ = run_case(self, "quan", scenario={"stock": {"ca_loc": 1}}, ticks=121)
        arrived = events(rows, "customer_arrived")
        self.assertEqual([e["tick"] for e in arrived], [120])
        d = arrived[0]["data"]
        self.assertEqual((d["table_id"], d["dish_id"]), ("T1", CA_LOC))
        s = snap_at(rows, 120)
        c = s["customers"][0]
        self.assertEqual(c["id"], d["order_id"])
        self.assertEqual((c["state"], c["order_status"], c["reserved"]), ("waiting", "reserved", {"ca_loc": 1}))
        self.assertEqual((c["order_tick"], c["patience_ticks_left"]), (120, 3600))
        self.assertEqual(s["tables"][0]["customer_id"], c["id"])
        self.assertEqual(s["stock"], {"ca_loc": 1}, "giữ chỗ chưa trừ tồn vật lý")
        self.assertEqual(snap_at(rows, 121)["customers"][0]["patience_ticks_left"], 3599)

    def test_ac_p1_21_chi_chon_mon_du_nguyen_lieu(self):
        for seed in range(1, 6):
            rows, _ = run_case(self, "quan", scenario={"stock": {"bong_sung": 2, "ca_linh": 3}}, ticks=120,
                               seed=seed, every=120)
            self.assertEqual([e["data"]["dish_id"] for e in events(rows, "customer_arrived")], ["goi_bong_sung"], seed)

    def test_ac_p1_22_khong_mon_nao_du_thi_no_dish(self):
        rows, _ = run_case(self, "quan", ticks=120, every=120)
        self.assertEqual(data_at(rows, "no_dish"), [(120, {})])
        self.assertEqual(events(rows, "customer_arrived"), [])

    def test_ac_p1_22_het_ban_thi_bo_luot_va_luot_sau_dung_lich(self):
        # v1.1 có 4 bàn (T1–T4): khách fixture ngồi sẵn T2–T4 (kiên nhẫn đầy, rời ở tick 3600) để chỉ còn T1,
        # giữ đúng ý test P1 "hết bàn thì bỏ lượt" (lát 0 đổi: preset P1 chỉ có 1 bàn).
        others = [customer(id=f"C{i}", table_id=f"T{i}") for i in (2, 3, 4)]
        rows, _ = run_case(self, "quan", scenario={"stock": {"ca_loc": 5}, "customers": others}, ticks=3721, every=100)
        self.assertEqual([e["tick"] for e in events(rows, "customer_arrived")], [120, 3720])
        self.assertEqual(events(rows, "no_dish"), [])
        self.assertEqual([(e["tick"], e["data"]["table_id"], e["data"]["reason"]) for e in events(rows, "customer_left")],
                         [(3600, "T2", "patience"), (3600, "T3", "patience"), (3600, "T4", "patience"),
                          (3720, "T1", "patience")])

    def test_ac_p1_23_het_kien_nhan_roi_ban_tru_uy_tin_nha_giu_cho(self):
        scen = sc(stock={"bong_sung": 2}, customers=[customer(dish_id="goi_bong_sung", patience_ticks_left=5)])
        rows, _ = run_case(self, "quan", scenario=scen, ticks=6)
        self.assertEqual(data_at(rows, "customer_left"),
                         [(5, {"order_id": "C1", "table_id": "T1", "reason": "patience", "reputation": 2.5})])
        s = snap_at(rows, 5)
        self.assertEqual((s["customers"], s["tables"][0]["customer_id"]), ([], None))
        self.assertEqual(s["stock"], {"bong_sung": 2})
        self.assertTrue(close(s["reputation"], 2.5, tol=0.01))
        self.assertEqual(s["score"], 200)


class Kitchen(unittest.TestCase):
    def test_ac_p1_24_25_nau_xong_roi_bung(self):
        scen = sc(player={"pos": NEAR_STOVE}, stock={"ca_loc": 1}, customers=[customer()])
        rows, _ = run_case(self, "quan", scenario=scen, inputs=press(0, "interact") + press(365, "interact"), ticks=367)
        self.assertEqual(data_at(rows, "cook_started"),
                         [(1, {"stove_id": "B1", "order_id": "C1", "dish_id": CA_LOC, "items": ["ca_loc"], "base_price": 60})])
        s1 = snap_at(rows, 1)
        self.assertEqual(s1["stock"], {})
        self.assertEqual((s1["stoves"][0]["state"], s1["stoves"][0]["cook_ticks_left"]), ("cooking", 360))
        self.assertEqual((s1["customers"][0]["order_status"], s1["customers"][0]["reserved"]), ("assigned", {}))
        ready = events(rows, "dish_ready")
        self.assertEqual(len(ready), 1)
        self.assertLessEqual(abs(ready[0]["tick"] - 361), 2)
        self.assertEqual(ready[0]["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": CA_LOC})
        self.assertEqual(data_at(rows, "dish_picked"), [(366, {"stove_id": "B1", "order_id": "C1", "dish_id": CA_LOC})])
        s = snap_at(rows, 366)
        self.assertEqual((s["hand"], s["stoves"][0]["state"]), (hand_payload(), "idle"))


class ServeAndPay(unittest.TestCase):
    def _serve(self, patience: int, ticks: int):
        c = customer(order_status="assigned", reserved={}, base_price=60, patience_ticks_left=patience)
        scen = sc(player={"pos": NEAR_TABLE}, hand=hand_payload(), customers=[c])
        return run_case(self, "quan", scenario=scen, inputs=press(0, "interact"), ticks=ticks, every=100)[0]

    def test_ac_p1_26_27_phuc_vu_an_xong_tra_tien_co_boa(self):
        rows = self._serve(3600, 602)
        self.assertEqual(data_at(rows, "served"),
                         [(1, {"order_id": "C1", "table_id": "T1", "dish_id": CA_LOC,
                               "patience_ticks_left": 3599, "base_price": 60, "tip": 12})])
        paid = events(rows, "paid")
        self.assertEqual(len(paid), 1)
        self.assertLessEqual(abs(paid[0]["tick"] - 601), 2)
        self.assertEqual(paid[0]["data"], {"order_id": "C1", "table_id": "T1", "base_price": 60, "tip": 12,
                                           "amount": 72, "reason": "finished_eating"})
        end = rows[-1]
        self.assertEqual((end["money"], end["earned"], end["score"]), (72, 72, 372))
        self.assertTrue(close(end["reputation"], 3.2, tol=0.01))

    def test_ac_p1_27_kien_nhan_duoi_nguong_khong_boa(self):
        rows = self._serve(1000, 602)
        self.assertEqual(one(self, rows, "served")["tip"], 0)
        self.assertEqual(one(self, rows, "paid")["amount"], 60)
        self.assertTrue(close(rows[-1]["reputation"], 3.0, tol=0.01))

    def test_ac_p1_26_phuc_vu_dung_tick_kien_nhan_ve_0_van_hop_le(self):
        rows = self._serve(1, 3)
        self.assertEqual(one(self, rows, "served")["patience_ticks_left"], 0)
        self.assertEqual(events(rows, "customer_left"), [])


class Closing(unittest.TestCase):
    def test_ac_p1_28_het_ca_khach_cho_roi_closing_khong_tru_uy_tin(self):
        scen = sc(stock={"bong_sung": 2}, customers=[customer(dish_id="goi_bong_sung")], time_left_ticks=5)
        rows, _ = run_case(self, "quan", scenario=scen, ticks=10)
        self.assertEqual([e["name"] for e in events(rows)], ["customer_left", "quan_end"])
        self.assertEqual(events(rows, "customer_left")[0]["data"]["reason"], "closing")
        self.assertEqual(events(rows, "quan_end")[0]["data"],
                         {"reason": "time", "money": 0, "earned": 0, "shift_earned": 0, "reputation": 3.0})
        self.assertEqual((rows[-1]["reason"], rows[-1]["ticks"]), ("time", 5))

    def test_ac_p1_28_het_ca_khach_dang_an_tra_tien_closing(self):
        c = customer(state="eating", order_status="served", eat_ticks_left=300, base_price=60, tip=12)
        rows, _ = run_case(self, "quan", scenario=sc(customers=[c], time_left_ticks=5), ticks=10)
        self.assertEqual(one(self, rows, "paid")["reason"], "closing")
        q = one(self, rows, "quan_end")
        self.assertEqual((q["money"], q["earned"], q["shift_earned"]), (72, 72, 72))
        self.assertEqual(rows[-1]["score"], 372)


class FixtureValidation(unittest.TestCase):
    """Mỗi fixture chỉ sai ĐÚNG MỘT điều (kho đủ), để mã 2 đến từ đúng luật cần kiểm."""

    def _assert_exit_2(self, blocks):
        with Workdir() as w:
            for block in blocks:
                path = write_json(w.path("sc.json"), {"quan": block})
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                       "--scenario", path, "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, block)
                self.assertFalse(os.path.exists(w.path("o.jsonl")))

    def test_ac_p1_29_mon_la_giu_khac_cong_thuc_giu_qua_ton_ma_2(self):
        self._assert_exit_2([
            sc(stock={"ca_loc": 1}, customers=[customer(dish_id="pho_bo")]),
            sc(stock={"ca_loc": 2}, customers=[customer(reserved={"ca_loc": 2})]),
            sc(stock={}, customers=[customer(reserved={"ca_loc": 1})]),
        ])

    def test_ac_p1_29_don_va_mon_tren_tay_bep_mau_thuan_ma_2(self):
        stock = {"ca_loc": 1}
        self._assert_exit_2([
            # tay cầm món của đơn còn `reserved`
            sc(stock=stock, hand=hand_payload(), customers=[customer(order_status="reserved")]),
            # đơn assigned nhưng không có món ở bếp hay trên tay
            sc(customers=[customer(order_status="assigned", reserved={}, base_price=60)]),
            # món trên tay khác món của đơn
            sc(hand={"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
               customers=[customer(order_status="assigned", reserved={}, base_price=60)]),
            # khách eating thiếu timer ăn dương và base_price/tip đã chốt
            sc(customers=[customer(state="eating", order_status="served")]),
        ])


class Determinism(unittest.TestCase):
    def test_ac_p1_30_quan_cung_seed_giong_tung_byte(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 3, "bong_sung": 4, "ca_linh": 3, "bong_dien_dien": 1}})
            for i in (1, 2):
                code, err = run_headless("--mode", "quan", "--seed", "9", "--inventory", inv, "--ticks", "3000",
                                         "--out", w.path(f"q{i}.jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("q1.jsonl"), "rb") as a, open(w.path("q2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
