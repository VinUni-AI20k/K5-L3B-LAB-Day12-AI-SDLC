"""Lát 3 Phase 3 (quán, phần khách) — giữ chỗ theo id cá thể, giữ lại khi hàng vừa ươn (Ticket-03, contract v1.2).

Bổ sung cho test QA `test_fresh_p3.py` (ReserveById, SpoilRetry, SpoiledNotCookable, FixtureValidation) ở các nhánh
QA chưa phủ: nhiều đơn cùng bị ươn trong một tick, kho đến từ `--inventory`, công thức nhiều loại.
Chạy headless với manifest v1.2 tạm qua CHONOI_CONTRACT (như test_lat0_v12.py) vì `main` còn chạy v1.1.

AC-P3-12 (giữ theo id), AC-P3-13 (giữ lại khi vừa ươn), AC-P3-17 (fixture mâu thuẫn -> mã 2).
"""

import os
import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json
from test_lat0_v12 import manifest_v12

CA_LOC = "ca_loc_nuong_trui"   # ca_loc ×1
LAU = "lau_ca_linh_dien_dien"  # ca_linh ×3 + bong_dien_dien ×1


def it(ident, kind, fresh):
    return {"id": ident, "kind": kind, "fresh": fresh}


class V12(unittest.TestCase):
    def setUp(self):
        self.w = Workdir().__enter__()
        self.old = os.environ.get("CHONOI_CONTRACT")
        os.environ["CHONOI_CONTRACT"] = write_json(self.w.path("contract.json"), manifest_v12())

    def tearDown(self):
        if self.old is None:
            os.environ.pop("CHONOI_CONTRACT", None)
        else:
            os.environ["CHONOI_CONTRACT"] = self.old
        self.w.__exit__(None, None, None)

    def run_quan(self, block, ticks, inventory=None):
        args = ["--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--snapshot-every", "1",
                "--scenario", write_json(self.w.path("sc.json"), {"quan": block}), "--out", self.w.path("q.jsonl")]
        if inventory is not None:
            args += ["--inventory", write_json(self.w.path("inv.json"), {"items": inventory})]
        code, err = run_headless(*args)
        return code, err, (read_jsonl(self.w.path("q.jsonl")) if code == 0 else None)

    def customers_at(self, rows, tick):
        snap = next(s for s in snapshots(rows) if s["tick"] == tick)
        return {c["id"]: (c["reserved"], c["order_status"]) for c in snap["customers"]}


class SpoilRetryOrder(V12):
    def test_ac_p3_13_hai_don_cung_uon_don_som_hon_giu_lai_truoc(self):
        """I1, I2 cùng ươn ở tick 1; chỉ còn I3 dùng được -> đơn order_tick nhỏ hơn (C2) giữ lại được, C1 unfulfillable."""
        block = {"random_customers": False,
                 "stock": [it("I1", "ca_loc", 30), it("I2", "ca_loc", 30), it("I3", "ca_loc", 90)],
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": CA_LOC, "order_tick": 10, "reserved": ["I1"]},
                               {"id": "C2", "table_id": "T2", "dish_id": CA_LOC, "order_tick": 5, "reserved": ["I2"]}]}
        code, err, rows = self.run_quan(block, 2)
        self.assertEqual(code, 0, err)
        self.assertEqual([e["data"]["item_id"] for e in events(rows, "spoiled") if e["tick"] == 1], ["I1", "I2"])
        self.assertEqual(self.customers_at(rows, 1), {"C1": ([], "unfulfillable"), "C2": (["I3"], "reserved")})
        # thử giữ lại đúng một lần: tick sau không đổi nữa
        self.assertEqual(self.customers_at(rows, 2), self.customers_at(rows, 1))

    def test_ac_p3_13_nha_het_moi_don_bi_anh_huong_roi_moi_giu_lai(self):
        """Gỏi bông súng cần 2. C1 giữ [I1 ươn, I2], C2 (order_tick nhỏ hơn) giữ [I3 ươn, I4]. Nhả hết cả hai đơn
        rồi giữ lại theo order_tick: C2 lấy được I2 + I4, C1 unfulfillable (clarify #20)."""
        stock = [it("I1", "bong_sung", 30), it("I2", "bong_sung", 90),
                 it("I3", "bong_sung", 30), it("I4", "bong_sung", 90)]
        block = {"random_customers": False, "stock": stock,
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_tick": 10,
                                "reserved": ["I1", "I2"]},
                               {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "order_tick": 5,
                                "reserved": ["I3", "I4"]}]}
        code, err, rows = self.run_quan(block, 1)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.customers_at(rows, 1), {"C1": ([], "unfulfillable"), "C2": (["I2", "I4"], "reserved")})

    def test_ac_p3_13_khong_dung_ca_the_cua_don_khac_dang_giu(self):
        """C1 vừa ươn chỉ được giữ lại từ cá thể chưa ai giữ; I3 đang thuộc C2 (không ươn) thì không lấy."""
        block = {"random_customers": False,
                 "stock": [it("I1", "ca_loc", 30), it("I3", "ca_loc", 90)],
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": CA_LOC, "reserved": ["I1"]},
                               {"id": "C2", "table_id": "T2", "dish_id": CA_LOC, "reserved": ["I3"]}]}
        code, err, rows = self.run_quan(block, 1)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.customers_at(rows, 1), {"C1": ([], "unfulfillable"), "C2": (["I3"], "reserved")})


class MultiKind(V12):
    def test_ac_p3_12_cong_thuc_nhieu_loai_lay_tuoi_nhat_moi_loai(self):
        stock = [it("I1", "ca_linh", 50), it("I2", "ca_linh", 95), it("I3", "ca_linh", 95), it("I4", "ca_linh", 80),
                 it("I5", "bong_dien_dien", 40), it("I6", "bong_dien_dien", 99)]
        block = {"random_customers": False, "stock": stock,
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": LAU}]}
        code, err, rows = self.run_quan(block, 0)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.customers_at(rows, 0), {"C1": (["I2", "I3", "I4", "I6"], "reserved")})


class FromInventory(V12):
    def test_ac_p3_12_kho_tu_inventory_cap_giu_cho_tuoi_nhat(self):
        inv = [it("I1", "ca_loc", 60), it("I2", "ca_loc", 90)]
        block = {"random_customers": False, "customers": [{"id": "C1", "table_id": "T1", "dish_id": CA_LOC}]}
        code, err, rows = self.run_quan(block, 0, inventory=inv)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.customers_at(rows, 0), {"C1": (["I2"], "reserved")})

    def test_ac_p3_17_kho_tu_inventory_giu_cho_mau_thuan_ma_2(self):
        inv = [it("I1", "ca_loc", 80), it("I2", "bong_sung", 80), it("I3", "ca_loc", 10)]
        bad = [["I9"], ["I3"], ["I2"]]  # id không có trong kho, trỏ hàng đã ươn, sai công thức
        for reserved in bad:
            block = {"random_customers": False,
                     "customers": [{"id": "C1", "table_id": "T1", "dish_id": CA_LOC, "reserved": reserved}]}
            code, _, _ = self.run_quan(block, 0, inventory=inv)
            self.assertEqual(code, 2, reserved)
            self.assertFalse(os.path.exists(self.w.path("q.jsonl")), reserved)

    def test_ac_p3_17_kho_tu_inventory_khong_du_de_cap_ma_2(self):
        block = {"random_customers": False, "customers": [{"id": "C1", "table_id": "T1", "dish_id": CA_LOC}]}
        code, _, _ = self.run_quan(block, 0, inventory=[it("I1", "ca_loc", 10)])  # chỉ có hàng ươn
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
