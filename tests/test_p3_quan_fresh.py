"""Phase 3, lát D (Ticket-03): kho quán hao tươi, nấu tiêu đúng cá thể đã giữ, giá theo độ tươi, boa trên giá chốt.

Kho v1.2 là danh sách cá thể. Khách được gắn sau khi dựng sim (không đi qua phần giữ chỗ của C) để test
chỉ phụ thuộc vào phần của D. Dữ liệu freshness lấy đúng chuẩn Ticket-03 khi manifest bật 1.2.
"""

import copy
import json
import os
import unittest

from helpers import ROOT
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

B1 = [2, 8]
T1 = [9, 2]
FRESHNESS = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}

with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
    BASE = json.load(f)["tuning"]


def tuning_v12():
    t = copy.deepcopy(BASE)
    t["freshness"] = dict(FRESHNESS)
    return t


TUNING = tuning_v12()


class Inp:
    def __init__(self, interact=False):
        self._interact = interact
        self.move = (0.0, 0.0)

    def pressed(self, name):
        return name == "interact" and self._interact


def item(iid, kind, fresh):
    """Cá thể public như trong scenario/file kho v1.2."""
    return {"id": iid, "kind": kind, "fresh": fresh}


def make(stock, pos=None):
    sc = {"stock": stock, "random_customers": False}
    sim = QuanSim(TUNING, sc, Streams(1), IdAllocator())
    if pos is not None:
        sim.pos = list(pos)
    return sim


def add_customer(sim, cid, table, dish, reserved_ids, status="reserved", base_price=0, tip=0,
                 state="waiting", eat=0, patience=3600):
    sim.customers.append({
        "id": cid, "table_id": table, "dish_id": dish, "order_tick": 0, "state": state,
        "patience_ticks_left": patience, "eat_ticks_left": eat, "order_status": status,
        "reserved": list(reserved_ids), "base_price": base_price, "tip": tip,
    })


def names(events):
    return [n for n, _ in events]


def data_of(events, name):
    return [d for n, d in events if n == name]


class HaoTuoiKho(unittest.TestCase):
    def test_kho_hao_025_moi_giay(self):
        sim = make([item("I1", "ca_loc", 100.0)])
        for _ in range(60):  # 1 giây: 60 đơn vị = 0.25 điểm
            sim.step(Inp())
        self.assertEqual(sim.stock[0]["u"], 24000 - 60)

    def test_hang_dang_giu_cho_van_hao(self):
        sim = make([item("I1", "bong_sung", 100.0), item("I2", "bong_sung", 100.0)], pos=B1)
        add_customer(sim, "C1", "T1", "goi_bong_sung", ["I1", "I2"])
        for _ in range(10):
            sim.step(Inp())
        self.assertTrue(all(it["u"] == 24000 - 10 for it in sim.stock))

    def test_uon_dung_tick_nguong_30(self):
        # 7200 đơn vị = 30 điểm (chưa ươn). Bước đầu 7201 -> 7200 chưa ươn; bước sau 7199 -> ươn đúng bước này.
        sim = make([item("I1", "ca_loc", 30.0 + 1 / 240)])
        ev1 = sim.step(Inp())
        self.assertEqual(data_of(ev1, "spoiled"), [])
        ev2 = sim.step(Inp())
        spoiled = data_of(ev2, "spoiled")
        self.assertEqual(spoiled, [{"item_id": "I1", "kind": "ca_loc", "location": "stock"}])

    def test_uon_nhieu_ca_the_phat_theo_id(self):
        sim = make([item("I2", "ca_loc", 30.0 + 1 / 240), item("I1", "ca_loc", 30.0 + 1 / 240)])
        ev = []
        ev += sim.step(Inp())
        ev += sim.step(Inp())
        ids = [d["item_id"] for d in data_of(ev, "spoiled")]
        self.assertEqual(ids, ["I1", "I2"])

    def test_uon_phat_mot_lan(self):
        sim = make([item("I1", "ca_loc", 30.0 + 1 / 240)])
        ev = []
        for _ in range(5):
            ev += sim.step(Inp())
        self.assertEqual(len(data_of(ev, "spoiled")), 1)


class NauTheoId(unittest.TestCase):
    def test_nau_tieu_dung_dung_id_da_giu_va_gia_theo_tuoi(self):
        # Hai cá thể tươi 50 điểm (12000 đơn vị) sau 1 bước hao (1 đơn vị/tick) và một cá thể tươi 100 điểm không được giữ.
        # Nên đặt u = 12001 để sau bước nấu còn đúng 12000.
        sim = make([item("I1", "bong_sung", 50.0 + 1 / 240), item("I2", "bong_sung", 50.0 + 1 / 240),
                    item("I3", "bong_sung", 100.0)], pos=B1)
        add_customer(sim, "C1", "T1", "goi_bong_sung", ["I1", "I2"])
        ev = sim.step(Inp(interact=True))
        cs = data_of(ev, "cook_started")
        self.assertEqual(len(cs), 1)
        self.assertEqual([it["id"] for it in cs[0]["items"]], ["I1", "I2"])
        self.assertEqual(cs[0]["base_price"], 20)  # floor(40 × 50 / 100)
        self.assertEqual([it["id"] for it in sim.stock], ["I3"])
        self.assertEqual(sim.customers[0]["base_price"], 20)

    def test_gia_tinh_bang_so_nguyen(self):
        # Hai cá thể tươi 66.67 điểm (16000 đơn vị): floor(40 × 66.67 / 100) = 26, tính bằng số nguyên.
        sim = make([item("I1", "bong_sung", 66.0 + 2 / 3), item("I2", "bong_sung", 66.0 + 2 / 3)], pos=B1)
        add_customer(sim, "C1", "T1", "goi_bong_sung", ["I1", "I2"])
        ev = sim.step(Inp(interact=True))
        self.assertEqual(data_of(ev, "cook_started")[0]["base_price"], 26)


class BoaTrenGiaChot(unittest.TestCase):
    def test_boa_tinh_tren_gia_da_chot(self):
        sim = make([], pos=T1)
        sim.hand = {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 20}
        add_customer(sim, "C1", "T1", "goi_bong_sung", [], status="assigned", base_price=20)
        ev = sim.step(Inp(interact=True))
        self.assertEqual(data_of(ev, "served")[0]["tip"], 4)  # floor(20 × 0.2), không tính trên giá niêm yết 40


if __name__ == "__main__":
    unittest.main()
