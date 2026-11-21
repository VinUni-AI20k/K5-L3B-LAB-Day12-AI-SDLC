"""Lát 3 (C), Phase 3: giữ chỗ theo id cá thể, giữ lại khi hàng vừa ươn, bàn giao kho cá thể trong day, Shop.

Manifest còn ở 1.1 trong lúc chuyển nên test dựng tuning v1.2 trong bộ nhớ (như test nền của A). Ticket-03 mục 1.
"""

import copy
import unittest

from chonoi import fresh
from chonoi.contract import FRESHNESS_V12, load_contract
from chonoi.day import DaySession
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.scenario import load_scenario
from chonoi.sim.quan import QuanSim
from helpers import Workdir, write_json

T11 = load_contract()["tuning"]
T12 = dict(copy.deepcopy(T11), freshness=dict(FRESHNESS_V12))


def item(iid, kind="ca_loc", f=100):
    return {"id": iid, "kind": kind, "fresh": f}


class Inp(InputState):
    def __init__(self, interact=False, done=False):
        edges = ({"interact"} if interact else set()) | ({"shop_done"} if done else set())
        super().__init__((0.0, 0.0), set(), edges)


def quan(stock, customers=(), plan=None, random_customers=True):
    sc = {"stock": list(stock), "customers": list(customers), "random_customers": random_customers}
    return QuanSim(T12, sc, Streams(1), IdAllocator(), plan_dishes=plan)


def run(sim, ticks):
    out = []
    for _ in range(ticks):
        out += sim.step(Inp())
    return out


def cust(cid, table, dish="ca_loc_nuong_trui", order_tick=0, **kw):
    return dict({"id": cid, "table_id": table, "dish_id": dish, "order_tick": order_tick}, **kw)


class ReserveById(unittest.TestCase):
    def test_lay_ca_the_tuoi_nhat_hoa_thi_id_nho(self):
        sim = quan([item("I1", f=80), item("I3", f=90), item("I2", f=90)], plan=["ca_loc_nuong_trui"])
        ev = run(sim, 120)
        self.assertEqual([n for n, _ in ev], ["customer_arrived"])
        self.assertEqual(sim.customers[0]["reserved"], ["I2"])  # 90 = 90 -> id nhỏ hơn

    def test_cong_thuc_nhieu_loai_lay_dung_so_luong(self):
        stock = [item("I1", "bong_sung", 60), item("I2", "bong_sung", 95), item("I3", "bong_sung", 70)]
        sim = quan(stock, plan=["goi_bong_sung"])
        run(sim, 120)
        self.assertEqual(sim.customers[0]["reserved"], ["I2", "I3"])  # 2 bông súng tươi nhất, sắp theo id

    def test_hang_uon_khong_dung_de_giu_va_khong_tinh_kha_dung(self):
        sim = quan([item("I1", f=29.99)])  # < 30: ươn
        self.assertEqual(sim.available_stock(), {})
        self.assertEqual([n for n, _ in run(sim, 120)], ["no_dish"])

    def test_dung_nguong_30_van_dung_duoc(self):
        # Kho quán hao 0.25 điểm/giây: 120 tick làm mất 0.5 điểm, nên cá thể phải bắt đầu ở 31 để còn tươi lúc khách đến.
        sim = quan([item("I1", f=31)], plan=["ca_loc_nuong_trui"])
        run(sim, 120)
        self.assertEqual(sim.customers[0]["reserved"], ["I1"])

    def test_hang_da_giu_khong_cho_khach_sau(self):
        sim = quan([item("I1")], plan=["ca_loc_nuong_trui"])
        ev = run(sim, 120 + 900)
        self.assertEqual([n for n, _ in ev], ["customer_arrived", "no_dish"])
        self.assertEqual(sim.available_stock(), {})


class RereserveSpoiled(unittest.TestCase):
    def spoil(self, sim, iid):
        next(it for it in sim.stock if it["id"] == iid)["u"] = fresh.cfg(T12)["spoiled_u"] - 1

    def test_giu_lai_mot_lan_roi_unfulfillable(self):
        sim = quan([item("I1", f=50), item("I2", f=40)], [cust("C1", "T1", reserved=["I1"])], random_customers=False)
        self.spoil(sim, "I1")
        sim._rereserve_spoiled(["I1"], [])
        self.assertEqual((sim.customers[0]["reserved"], sim.customers[0]["order_status"]), (["I2"], "reserved"))
        self.spoil(sim, "I2")
        sim._rereserve_spoiled(["I2"], [])
        self.assertEqual((sim.customers[0]["reserved"], sim.customers[0]["order_status"]), ([], "unfulfillable"))
        self.assertEqual(sim.customers[0]["state"], "waiting")  # chờ tới hết kiên nhẫn

    def test_thu_tu_order_tick_roi_id_ban(self):
        # Hai đơn cùng dính hàng vừa ươn; chỉ còn một con tươi: đơn order_tick nhỏ hơn (bàn T2) lấy trước.
        stock = [item("I1", f=50), item("I2", f=50), item("I3", f=90)]
        cs = [cust("C1", "T1", order_tick=10, reserved=["I1"]), cust("C2", "T2", order_tick=5, reserved=["I2"])]
        sim = quan(stock, cs, random_customers=False)
        self.spoil(sim, "I1")
        self.spoil(sim, "I2")
        sim._rereserve_spoiled(["I1", "I2"], [])
        got = {c["id"]: (c["reserved"], c["order_status"]) for c in sim.customers}
        self.assertEqual(got, {"C2": (["I3"], "reserved"), "C1": ([], "unfulfillable")})

    def test_don_khong_dinh_hang_uon_va_don_assigned_giu_nguyen(self):
        stock = [item("I1", f=50), item("I2", f=80)]
        cs = [cust("C1", "T1", reserved=["I2"]),
              cust("C2", "T2", order_status="assigned", reserved=[])]
        # đơn assigned cần món trên bếp hoặc tay; dựng bằng hand
        sc = {"stock": stock, "customers": cs, "random_customers": False,
              "hand": {"order_id": "C2", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}
        sim = QuanSim(T12, sc, Streams(1), IdAllocator())
        self.spoil(sim, "I1")
        sim._rereserve_spoiled(["I1"], [])
        got = {c["id"]: (c["reserved"], c["order_status"]) for c in sim.customers}
        self.assertEqual(got, {"C1": (["I2"], "reserved"), "C2": ([], "assigned")})


class PrebuiltCustomers(unittest.TestCase):
    def test_thieu_reserved_cap_theo_order_tick_roi_id_ban(self):
        stock = [item("I1", f=70), item("I2", f=90)]
        cs = [cust("C1", "T1", order_tick=20), cust("C2", "T2", order_tick=10)]
        sim = quan(stock, cs, random_customers=False)
        got = {c["id"]: c["reserved"] for c in sim.customers}
        self.assertEqual(got, {"C2": ["I2"], "C1": ["I1"]})  # C2 đến trước lấy con tươi nhất

    def test_thieu_kho_de_cap_bao_loi(self):
        with self.assertRaises(BadInput):
            quan([item("I1", f=20)], [cust("C1", "T1")], random_customers=False)

    def test_reserved_sai_bao_loi(self):
        bad = [
            ([item("I1")], [cust("C1", "T1", reserved=["I9"])]),                                  # không có trong kho
            ([item("I1", f=10)], [cust("C1", "T1", reserved=["I1"])]),                             # đã ươn
            ([item("I1"), item("I2")], [cust("C1", "T1", reserved=["I1"]), cust("C2", "T2", reserved=["I1"])]),
            ([item("I1", "bong_sung")], [cust("C1", "T1", reserved=["I1"])]),                      # sai công thức
            ([item("I1")], [cust("C1", "T1", reserved={"ca_loc": 1})]),                            # dạng đếm cũ
        ]
        for stock, cs in bad:
            with self.subTest(cs=cs), self.assertRaises(BadInput):
                quan(stock, cs, random_customers=False)

    def test_scenario_kiem_reserved_theo_id(self):
        ok = {"quan": {"stock": [item("I1")], "customers": [cust("C1", "T1", reserved=["I1"])]}}
        bad = [
            {"quan": {"stock": [item("I1")], "customers": [cust("C1", "T1", reserved=["I2"])]}},
            {"quan": {"stock": [item("I1", f=29)], "customers": [cust("C1", "T1", reserved=["I1"])]}},
            {"quan": {"stock": [item("I1")], "customers": [cust("C1", "T1", reserved=["I1", "I1"])]}},
            {"quan": {"stock": [item("I1"), item("I2")],
                      "customers": [cust("C1", "T1", reserved=["I1"]), cust("C2", "T2", reserved=["I1"])]}},
        ]
        with Workdir() as w:
            self.assertEqual(load_scenario(write_json(w.path("ok.json"), ok), "quan", T12)["customers"][0]["reserved"],
                             ["I1"])
            for i, data in enumerate(bad):
                with self.subTest(i=i), self.assertRaises(BadInput):
                    load_scenario(write_json(w.path(f"b{i}.json"), data), "quan", T12)


class DayHandover(unittest.TestCase):
    def test_ban_giao_ca_the_ngay_2_cap_id_moi_va_shop_giu_ca_the(self):
        hold = [item("I1", "ca_loc", 100), item("I2", "bong_sung", 80)]
        sess = DaySession(T12, {"gather": {"hold": hold, "random_fish": False, "monsters": []}}, 1, 2)
        sess.step(Inp(interact=True))  # cập bến ở bước 1
        gather_hold = {it["id"]: it["u"] for it in sess.sim.stock}  # quán vừa mở cùng tick
        self.assertEqual(sess.sim.phase, "quan")
        self.assertEqual(sorted(gather_hold), ["I1", "I2"])
        self.assertLessEqual(gather_hold["I1"], 24000)  # đúng u của giỏ lúc cập bến, không qua số thực
        snap = sess.snapshot()
        self.assertEqual([s["id"] for s in snap["stock"]], ["I1", "I2"])
        while sess.sim.phase != "shop":
            sess.step(Inp())
        shop = sess.snapshot()["stock"]
        self.assertTrue(all(set(s) == {"id", "kind", "fresh"} for s in shop))
        before = copy.deepcopy(sess.sim.stock)
        sess.step(Inp())
        self.assertEqual(sess.sim.stock, before)  # Shop không hao
        sess.step(Inp(done=True))
        self.assertEqual((sess.day, sess.sim.phase), (2, "gather"))
        self.assertEqual([(it["id"], it["kind"], it["u"]) for it in sess.sim.hold],
                         [("I3", "ca_loc", 24000), ("I4", "bong_sung", 19200)])  # id mới, kind và fresh như mẫu


if __name__ == "__main__":
    unittest.main()
