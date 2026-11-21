"""Phase 2, lát 3 (D): 2 bếp, 4 bàn, 6 món. Dữ liệu đọc từ game.contract.json v1.1."""

import copy
import json
import os
import unittest

from helpers import ROOT
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

B1, B2 = [2, 8], [5, 8]
T1, T2, T3, T4 = [9, 2], [13, 2], [9, 6], [13, 6]

with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
    TUNING = json.load(f)["tuning"]


class Inp:
    def __init__(self, interact=False):
        self._interact = interact
        self.move = (0.0, 0.0)

    def pressed(self, name):
        return name == "interact" and self._interact


def customer(cid, table, dish="goi_bong_sung", order_tick=0):
    recipe = dict(TUNING["menu"][dish]["recipe"])
    return {"id": cid, "table_id": table, "dish_id": dish, "order_tick": order_tick,
            "state": "waiting", "patience_ticks_left": 3600, "eat_ticks_left": 0,
            "order_status": "reserved", "reserved": recipe, "base_price": 0, "tip": 0}


def make(customers=(), stock=None, pos=None, tuning=None, random_customers=False):
    sc = {"stock": dict(stock or {}), "customers": list(customers),
          "random_customers": random_customers}
    sim = QuanSim(tuning or TUNING, sc, Streams(1), IdAllocator())
    if pos is not None:
        sim.pos = list(pos)
    return sim


def names(events):
    return [n for n, _ in events]


def data_of(events, name):
    return [d for n, d in events if n == name]


class HaiBep(unittest.TestCase):
    def test_hai_bep_nau_song_song_hai_don(self):
        sim = make(customers=[customer("C1", "T1", order_tick=0), customer("C2", "T2", order_tick=1)],
                   stock={"bong_sung": 4}, pos=B1)
        ev = sim.step(Inp(interact=True))
        self.assertEqual(data_of(ev, "cook_started")[0]["stove_id"], "B1")
        self.assertEqual(data_of(ev, "cook_started")[0]["order_id"], "C1")
        sim.pos = list(B2)
        ev = sim.step(Inp(interact=True))
        self.assertEqual(data_of(ev, "cook_started")[0]["stove_id"], "B2")
        self.assertEqual(data_of(ev, "cook_started")[0]["order_id"], "C2")
        states = {s["id"]: s["state"] for s in sim.snapshot()["stoves"]}
        self.assertEqual(states, {"B1": "cooking", "B2": "cooking"})
        self.assertEqual(sim.stock.get("bong_sung", 0), 0)

    def test_bep_dang_nau_van_nhan_don_o_bep_con_lai(self):
        sim = make(customers=[customer("C1", "T1", order_tick=0), customer("C2", "T2", order_tick=1)],
                   stock={"bong_sung": 4}, pos=B1)
        sim.step(Inp(interact=True))
        for _ in range(4 * 60 + 1):  # B1 chín
            sim.step(Inp())
        self.assertEqual(sim.stoves[0]["state"], "ready")
        sim.pos = list(B2)
        ev = sim.step(Inp(interact=True))
        self.assertEqual(data_of(ev, "cook_started")[0]["order_id"], "C2")

    def test_dung_giua_hai_bep_chon_bep_gan_hon(self):
        tuning = copy.deepcopy(TUNING)
        tuning["quan"]["interact_radius"] = 3.0  # cho cả hai bếp trong tầm
        sim = make(customers=[customer("C1", "T1")], stock={"bong_sung": 2}, pos=[4.0, 8.0], tuning=tuning)
        ev = sim.step(Inp(interact=True))
        self.assertEqual(data_of(ev, "cook_started")[0]["stove_id"], "B2")  # B2 cách 1.0, B1 cách 2.0

    def test_dung_dung_giua_hai_bep_hoa_thi_chon_bep_co_id_nho(self):
        sim = make(customers=[customer("C1", "T1")], stock={"bong_sung": 2}, pos=[3.5, 8.0])
        ev = sim.step(Inp(interact=True))  # B1 và B2 đều cách 1.5 m, hòa theo id
        self.assertEqual(data_of(ev, "cook_started")[0]["stove_id"], "B1")


class BonBan(unittest.TestCase):
    def test_bon_khach_ngoi_bon_ban_theo_id(self):
        sim = make(stock={"bong_sung": 100, "ca_loc": 100, "ca_linh": 100, "bong_dien_dien": 100,
                          "ca_keo": 100, "keo_neo": 100},
                   tuning=TUNING, random_customers=True)
        arrived = []
        for _ in range(2821):  # khách tick 120, 1020, 1920, 2820
            arrived += data_of(sim.step(Inp()), "customer_arrived")
        self.assertEqual(len(arrived), 4)
        tables = [c["table_id"] for c in sim.customers]
        self.assertEqual(sorted(tables), ["T1", "T2", "T3", "T4"])
        occupied = {tb["id"]: tb["customer_id"] for tb in sim.snapshot()["tables"]}
        self.assertEqual(sorted(occupied), ["T1", "T2", "T3", "T4"])
        self.assertTrue(all(occupied[t] for t in ["T1", "T2", "T3", "T4"]))


class TraTienTheoBan(unittest.TestCase):
    def test_hai_khach_an_xong_cung_luc_tra_tien_theo_id_ban(self):
        # C1 ngồi T2, C2 ngồi T1: trả tiền theo id bàn (T1 trước T2), không theo id khách.
        def eating(cid, table):
            return {"id": cid, "table_id": table, "dish_id": "goi_bong_sung", "order_tick": 0,
                    "state": "eating", "patience_ticks_left": 3600, "eat_ticks_left": 0,
                    "order_status": "served", "reserved": {}, "base_price": 40, "tip": 0}
        sim = make(customers=[eating("C1", "T2"), eating("C2", "T1")], pos=[0, 0])
        ev = sim.step(Inp())
        paid = data_of(ev, "paid")
        self.assertEqual([p["order_id"] for p in paid], ["C2", "C1"])


class MonMoi(unittest.TestCase):
    def test_lau_mam_nau_12_giay_gia_200(self):
        c = customer("C1", "T1", dish="lau_mam")
        sim = make(customers=[c],
                   stock={"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, pos=B1)
        ev = sim.step(Inp(interact=True))
        cs = data_of(ev, "cook_started")[0]
        self.assertEqual(cs["base_price"], 200)
        self.assertEqual(cs["items"], ["bong_dien_dien", "ca_keo", "ca_linh", "ca_linh", "keo_neo"])
        self.assertEqual(sim.stoves[0]["cook_ticks_left"], 12 * 60)

    def test_du_6_mon_trong_menu(self):
        self.assertEqual(len(TUNING["menu"]), 6)
        self.assertEqual(set(TUNING["menu"]), {"ca_loc_nuong_trui", "goi_bong_sung", "lau_ca_linh_dien_dien",
                                               "canh_chua_ca_loc", "ca_keo_nuong", "lau_mam"})


if __name__ == "__main__":
    unittest.main()
