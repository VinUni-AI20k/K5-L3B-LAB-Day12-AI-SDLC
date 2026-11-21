"""Test hộp đen Phase 3 (Ticket-03, contract v1.2): kho cá thể + độ tươi.

Mỗi test ghi mã AC-P3-xx (docs/verification/phase-3.md). Chạy với manifest v1.2 tạm (`use_v12_manifest`) khi `main` còn v1.1.
Test chờ lát chưa merge mang @pending: skip mặc định để main xanh; QA_STRICT=1 chạy thật. Lát xong thì QA bỏ @pending.
Còn @pending: AC-P3-01, 02, 03, 10 (hao tươi giỏ + `spoiled` trong gather — chờ lát gather).

Quy ước số: 240 đơn vị / điểm tươi -> giỏ hao 2 đơn vị/tick (0.5/s), kho quán 1 đơn vị/tick (0.25/s).
Fixture cố ý chọn số để KẾT QUẢ không phụ thuộc việc hao 0 hay 1 tick trước khi nấu (vd fresh 50.5 -> giá 30 dù hao hay không).
"""

import os
import unittest

from helpers import Workdir, close, events, run_headless, write_json
from qa_helpers import pending, press, run_case, snap_at, use_v12_manifest
from test_day_p2 import run_day

CA_LOC = "ca_loc_nuong_trui"
TOL = 0.01  # dung sai quan sát độ tươi (Ticket-03 mục JSONL)
SURF, UNDER = [20, 0], [20, 10]

_restore_manifest = None


def setUpModule():
    global _restore_manifest
    _restore_manifest = use_v12_manifest()  # main còn v1.1 -> manifest v1.2 tạm; v1.2 thật thì no-op


def tearDownModule():
    _restore_manifest()


def it(ident: str, kind: str, fresh: float) -> dict:
    return {"id": ident, "kind": kind, "fresh": fresh}


def gsc(**kw) -> dict:
    """Scenario gather cô lập: không nút, không cá, không quái."""
    base = {"nodes": [], "fish": [], "random_fish": False, "monsters": []}
    base.update(kw)
    return base


def qsc(**kw) -> dict:
    base = {"random_customers": False}
    base.update(kw)
    return base


def cust(**kw) -> dict:
    c = {"id": "C1", "table_id": "T1", "dish_id": CA_LOC}
    c.update(kw)
    return c


def ids(items: list) -> list:
    return [x["id"] for x in items]


def spoiled_events(rows) -> list:
    return [(e["tick"], e["data"]["item_id"], e["data"]["location"]) for e in events(rows, "spoiled")]


class Threshold(unittest.TestCase):
    def test_ac_p3_01_vi_du_ticket_uon_o_buoc_dau_dung_nguong_30(self):
        rows, _ = run_case(self, "gather", scenario=gsc(hold=[it("I1", "ca_linh", 30)]), ticks=1)
        self.assertEqual([(e["tick"], e["phase"], e["data"]) for e in events(rows, "spoiled")],
                         [(1, "gather", {"item_id": "I1", "kind": "ca_linh", "location": "hold"})])

    def test_ac_p3_01_fresh_30_5_chua_uon_den_buoc_61(self):
        rows, _ = run_case(self, "gather", scenario=gsc(hold=[it("I1", "ca_linh", 30.5)]), ticks=62)
        self.assertEqual(spoiled_events(rows), [(61, "I1", "hold")])
        self.assertTrue(close(snap_at(rows, 60)["hold"][0]["fresh"], 30.0, TOL))  # 30.0 chưa < 30


class SpoiledOnce(unittest.TestCase):
    def test_ac_p3_02_nhieu_ca_the_cung_vuot_nguong_phat_theo_id_dung_mot_lan(self):
        hold = [it("I2", "ca_loc", 30), it("I1", "ca_linh", 30)]
        rows, _ = run_case(self, "gather", scenario=gsc(hold=hold), ticks=120)
        self.assertEqual(spoiled_events(rows), [(1, "I1", "hold"), (1, "I2", "hold")])


class GatherDecay(unittest.TestCase):
    def test_ac_p3_03_gio_hao_0_5_moi_giay(self):
        rows, _ = run_case(self, "gather", scenario=gsc(hold=[it("I1", "ca_loc", 100)]), ticks=60)
        self.assertTrue(close(snap_at(rows, 60)["hold"][0]["fresh"], 99.5, TOL))

    
    def test_ac_p3_03_hang_moi_hai_duoc_fresh_100_hao_tu_buoc_sau(self):
        nodes = [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}]
        rows, _ = run_case(self, "gather", scenario=gsc(player={"pos": SURF}, nodes=nodes), inputs=press(0, "interact"),
                           ticks=61)
        item = snap_at(rows, 1)["hold"][0]
        self.assertEqual((item["id"], item["kind"], item["fresh"]), ("I1", "bong_sung", 100))
        self.assertTrue(close(snap_at(rows, 61)["hold"][0]["fresh"], 99.5, TOL))


class GatherIds(unittest.TestCase):
    def test_ac_p3_04_id_tiep_tuc_tang_va_hang_uon_van_chiem_o(self):
        nodes = [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}]
        rows, _ = run_case(self, "gather", scenario=gsc(player={"pos": SURF}, nodes=nodes, hold=[it("I1", "ca_loc", 5)]),
                           inputs=press(0, "interact"), ticks=2)
        self.assertEqual(ids(snap_at(rows, 1)["hold"]), ["I1", "I2"])
        full = [it(f"I{i}", "ca_loc", 5) for i in range(1, 13)]  # 12 món ươn vẫn chiếm đủ 12 ô
        rows, _ = run_case(self, "gather", scenario=gsc(player={"pos": SURF}, nodes=nodes, hold=full),
                           inputs=press(0, "interact"), ticks=2)
        self.assertEqual([e["data"] for e in events(rows, "hold_full")],
                         [{"action": "gather", "node_id": "N1", "required": 1, "free": 0}])


class GatherLoss(unittest.TestCase):
    def test_ac_p3_05_ngat_bo_theo_lifo_lost_la_mang_ca_the_kho_rong(self):
        hold = [it("I1", "ca_loc", 90), it("I2", "bong_sung", 80), it("I3", "ca_linh", 70)]
        player = {"pos": UNDER, "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 59}
        rows, kho = run_case(self, "gather", scenario=gsc(player=player, hold=hold), ticks=10, inventory_out=True)
        faint = events(rows, "faint")[0]["data"]
        self.assertEqual((faint["cause"], faint["hp"]), ("choke", 0))
        self.assertEqual([(x["id"], x["kind"]) for x in faint["lost"]],
                         [("I3", "ca_linh"), ("I2", "bong_sung"), ("I1", "ca_loc")])
        for x in faint["lost"]:
            self.assertGreaterEqual(x["fresh"], 69.9)
        self.assertEqual(events(rows, "gather_end")[0]["data"], {"reason": "fainted", "inventory": {"items": []}})
        self.assertEqual(kho, {"items": []})


class FileOut(unittest.TestCase):
    def test_ac_p3_06_cap_ben_ghi_kho_theo_id_khop_gather_end(self):
        hold = [it("I2", "ca_loc", 80), it("I1", "bong_sung", 60)]
        rows, kho = run_case(self, "gather", scenario=gsc(hold=hold), inputs=press(0, "interact"), ticks=5,
                             inventory_out=True)
        self.assertEqual(ids(kho["items"]), ["I1", "I2"])
        self.assertEqual([(x["kind"], round(x["fresh"])) for x in kho["items"]], [("bong_sung", 60), ("ca_loc", 80)])
        end = events(rows, "gather_end")[0]
        self.assertEqual((end["tick"], end["data"]["reason"]), (1, "docked"))
        self.assertEqual(end["data"]["inventory"], kho)

    def test_ac_p3_06_cham_ticks_truoc_gather_end_khong_tao_file(self):
        _, kho = run_case(self, "gather", scenario=gsc(hold=[it("I1", "ca_loc", 80)], player={"pos": UNDER}),
                          ticks=5, inventory_out=True)
        self.assertIsNone(kho)


class Handoff(unittest.TestCase):
    def test_ac_p3_07_smoke_hai_tien_trinh_giu_id_kind_fresh(self):
        hold = [it("I1", "ca_linh", 100)]
        _, kho = run_case(self, "gather", scenario=gsc(hold=hold), inputs=press(0, "interact"), ticks=1, inventory_out=True)
        self.assertEqual(ids(kho["items"]), ["I1"])
        self.assertTrue(close(kho["items"][0]["fresh"], 100, TOL))  # sau một lần hao ở bước gather
        rows, _ = run_case(self, "quan", scenario=qsc(), inventory=kho["items"], ticks=0)
        self.assertEqual(snap_at(rows, 0)["stock"], kho["items"])  # khớp chính xác id, kind, fresh

    def test_ac_p3_07_quan_nhan_ca_hang_uon(self):
        stock = [it("I1", "ca_loc", 10), it("I2", "ca_loc", 90)]
        rows, _ = run_case(self, "quan", scenario=qsc(), inventory=stock, ticks=0)
        self.assertEqual(snap_at(rows, 0)["stock"], stock)

    def test_ac_p3_07_kho_dem_cu_hoac_sai_schema_ma_2(self):
        bad = [{"ca_loc": 1}, [it("I1", "pho_bo", 50)], [it("I1", "ca_loc", 50), it("I1", "ca_linh", 50)],
               [it("I1", "ca_loc", 100.5)], [it("I1", "ca_loc", -1)], [it("", "ca_loc", 50)],
               [{"id": "I1", "kind": "ca_loc"}], [{"id": "I1", "kind": "ca_loc", "fresh": "50"}], "ca_loc"]
        with Workdir() as w:
            for items in bad:
                inv = write_json(w.path("inv.json"), {"items": items})
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--inventory", inv, "--ticks", "0",
                                       "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, items)
                self.assertFalse(os.path.exists(w.path("o.jsonl")), items)

    def test_ac_p3_07_scenario_dem_cu_ma_2(self):
        cases = [("gather", {"hold": ["ca_loc"]}), ("quan", {"stock": {"ca_loc": 1}}),
                 ("gather", {"hold": [it("I1", "ca_loc", 50), it("I1", "ca_loc", 60)]})]
        with Workdir() as w:
            for mode, block in cases:
                sc = write_json(w.path("sc.json"), {mode: block})
                code, _ = run_headless("--mode", mode, "--seed", "1", "--scenario", sc, "--ticks", "0",
                                       "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, block)


class DayHandoff(unittest.TestCase):
    @staticmethod
    def day_sc(hold):
        return {"gather": gsc(hold=hold, time_left_ticks=1), "quan": qsc(time_left_ticks=1)}

    def test_ac_p3_08_ban_giao_cung_tick_hang_khong_hao_them(self):
        rows = run_day(self, scenario=self.day_sc([it("I1", "ca_loc", 80)]), inputs=press(0, "interact"), ticks=2)
        end = events(rows, "gather_end")[0]
        self.assertEqual(end["tick"], 1)
        handed = end["data"]["inventory"]["items"]
        s1 = snap_at(rows, 1)
        self.assertEqual((s1["phase"], s1["phase_tick"]), ("quan", 0))
        self.assertEqual(s1["stock"], handed)  # đúng từng giá trị: không hao thêm trong tick chuyển pha

    def test_ac_p3_08_ngay_ke_cap_id_moi_theo_thu_tu_mang(self):
        hold = [it("I1", "ca_loc", 100)]
        rows = run_day(self, scenario=self.day_sc(hold), ticks=603, days=2)
        self.assertEqual(ids(snap_at(rows, 1)["stock"]), ["I1"])
        s = snap_at(rows, 602)
        self.assertEqual((s["day"], s["phase"]), (2, "gather"))
        self.assertEqual([(x["id"], x["kind"], x["fresh"]) for x in s["hold"]], [("I2", "ca_loc", 100)])

    def test_ac_p3_09_shop_giu_kho_ca_the_va_khong_hao(self):
        rows = run_day(self, scenario=self.day_sc([it("I1", "ca_loc", 80)]), ticks=300)
        a, b = snap_at(rows, 3), snap_at(rows, 300)
        self.assertEqual((a["phase"], b["phase"]), ("shop", "shop"))
        self.assertEqual(ids(a["stock"]), ["I1"])
        self.assertEqual(a["stock"], b["stock"])


class PauseFresh(unittest.TestCase):
    
    def test_ac_p3_10_pause_dung_hao_tuoi(self):
        # Ticket-02 4.2: "Cạnh lên tiếp theo phát resumed" -> tiếp tục bằng một lần NHẤN nữa ở tick 70,
        # không phải thả nút (bản trước thả nút nên game không bao giờ tiếp tục). Assert giữ nguyên.
        inputs = press(10, "pause") + press(70, "pause")
        rows, _ = run_case(self, "gather", scenario=gsc(hold=[it("I1", "ca_loc", 100)]), inputs=inputs, ticks=120)
        self.assertTrue(close(snap_at(rows, 120)["hold"][0]["fresh"], 99.5, TOL))  # chỉ 60 bước chạy thật


class QuanDecay(unittest.TestCase):
    def test_ac_p3_11_kho_quan_hao_0_25_ke_ca_hang_dang_giu_cho(self):
        scen = qsc(stock=[it("I1", "ca_loc", 100)], customers=[cust(reserved=["I1"])])
        rows, _ = run_case(self, "quan", scenario=scen, ticks=60)
        s = snap_at(rows, 60)
        self.assertTrue(close(s["stock"][0]["fresh"], 99.75, TOL))
        self.assertEqual(s["customers"][0]["reserved"], ["I1"])


class ReserveById(unittest.TestCase):
    STOCK = [it("I1", "ca_loc", 60), it("I2", "ca_loc", 90), it("I3", "ca_loc", 90)]

    def test_ac_p3_12_fixture_thieu_reserved_lay_tuoi_nhat_hoa_id_nho(self):
        rows, _ = run_case(self, "quan", scenario=qsc(stock=self.STOCK, customers=[cust()]), ticks=0)
        self.assertEqual(snap_at(rows, 0)["customers"][0]["reserved"], ["I2"])

    def test_ac_p3_12_khach_moi_giu_ca_the_tuoi_nhat(self):
        rows, _ = run_case(self, "quan", scenario={"stock": self.STOCK}, ticks=120, every=120)
        self.assertEqual([e["data"]["dish_id"] for e in events(rows, "customer_arrived")], [CA_LOC])
        self.assertEqual(snap_at(rows, 120)["customers"][0]["reserved"], ["I2"])

    def test_ac_p3_12_cap_theo_order_tick_roi_id_ban(self):
        stock = [it("I1", "ca_loc", 70), it("I2", "ca_loc", 90), it("I3", "ca_loc", 80)]
        customers = [cust(id="C1", table_id="T1", order_tick=10), cust(id="C2", table_id="T2", order_tick=5)]
        rows, _ = run_case(self, "quan", scenario=qsc(stock=stock, customers=customers), ticks=0)
        by_id = {c["id"]: c["reserved"] for c in snap_at(rows, 0)["customers"]}
        self.assertEqual(by_id, {"C2": ["I2"], "C1": ["I3"]})


class SpoilRetry(unittest.TestCase):
    def test_ac_p3_13_giu_cho_vua_uon_thi_nha_het_va_giu_lai_mot_lan(self):
        stock = [it("I1", "ca_loc", 30), it("I2", "ca_loc", 90)]
        rows, _ = run_case(self, "quan", scenario=qsc(stock=stock, customers=[cust(reserved=["I1"])]), ticks=2)
        self.assertEqual(spoiled_events(rows), [(1, "I1", "stock")])
        c = snap_at(rows, 1)["customers"][0]
        self.assertEqual((c["reserved"], c["order_status"]), (["I2"], "reserved"))

    def test_ac_p3_13_khong_du_thi_unfulfillable_khach_van_cho(self):
        rows, _ = run_case(self, "quan", scenario=qsc(stock=[it("I1", "ca_loc", 30)], customers=[cust(reserved=["I1"])]),
                           ticks=5)
        c = snap_at(rows, 5)["customers"][0]
        self.assertEqual((c["reserved"], c["order_status"]), ([], "unfulfillable"))
        self.assertEqual(events(rows, "customer_left"), [])
        self.assertLess(c["patience_ticks_left"], 3600)


class PriceByFreshness(unittest.TestCase):
    def _cook(self, stock, customers, dish_items):
        scen = qsc(player={"pos": [2, 8]}, stock=stock, customers=customers)
        rows, _ = run_case(self, "quan", scenario=scen, inputs=press(0, "interact"), ticks=2)
        started = events(rows, "cook_started")
        self.assertEqual(len(started), 1)
        self.assertEqual(ids(started[0]["data"]["items"]), dish_items)
        return started[0]["data"]

    def test_ac_p3_14_gia_chot_theo_tuoi_floor(self):
        d = self._cook([it("I1", "ca_loc", 50.5)], [cust(reserved=["I1"])], ["I1"])
        self.assertEqual(d["base_price"], 30)  # floor(60 × 50.5 / 100)

    def test_ac_p3_14_gia_theo_trung_binh_nhieu_ca_the(self):
        stock = [it("I2", "bong_sung", 60.5), it("I1", "bong_sung", 80.5)]
        d = self._cook(stock, [cust(dish_id="goi_bong_sung", reserved=["I1", "I2"])], ["I1", "I2"])
        self.assertEqual(d["base_price"], 28)  # floor(40 × 70.5 / 100)

    def test_ac_p3_15_boa_tinh_tren_gia_da_chot(self):
        c = cust(order_status="assigned", reserved=[], base_price=30)
        hand = {"order_id": "C1", "dish_id": CA_LOC, "base_price": 30}
        rows, _ = run_case(self, "quan", scenario=qsc(player={"pos": [9, 2.5]}, hand=hand, customers=[c]),
                           inputs=press(0, "interact"), ticks=2)
        served = events(rows, "served")[0]["data"]
        self.assertEqual((served["base_price"], served["tip"]), (30, 6))  # floor(30 × 0.2)


class SpoiledNotCookable(unittest.TestCase):
    def test_ac_p3_16_hang_uon_khong_dung_nau_no_dish(self):
        rows, _ = run_case(self, "quan", scenario={"stock": [it("I1", "ca_loc", 20)]},
                           ticks=120, every=120)
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "no_dish")], [(120, {})])
        self.assertEqual(events(rows, "customer_arrived"), [])


class FixtureValidation(unittest.TestCase):
    def test_ac_p3_17_giu_cho_mau_thuan_ma_2(self):
        stock = [it("I1", "ca_loc", 80), it("I2", "bong_sung", 80), it("I3", "ca_loc", 10)]
        bad = [
            qsc(stock=stock, customers=[cust(reserved=["I9"])]),                      # id không tồn tại
            qsc(stock=stock, customers=[cust(reserved=["I3"])]),                      # trỏ hàng đã ươn
            qsc(stock=stock, customers=[cust(reserved=["I2"])]),                      # sai công thức
            qsc(stock=stock, customers=[cust(id="C1", reserved=["I1"]),
                                        cust(id="C2", table_id="T2", reserved=["I1"])]),  # dùng chung với đơn khác
            qsc(stock=stock, customers=[cust(reserved={"ca_loc": 1})]),               # reserved kiểu cũ
            qsc(stock=[it("I1", "ca_loc", 80), it("I1", "ca_loc", 70)]),              # id trùng trong kho
        ]
        with Workdir() as w:
            for block in bad:
                path = write_json(w.path("sc.json"), {"quan": block})
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario", path,
                                       "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, block)
                self.assertFalse(os.path.exists(w.path("o.jsonl")))


if __name__ == "__main__":
    unittest.main()
