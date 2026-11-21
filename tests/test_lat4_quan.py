"""Lát 4 (D): bếp, bưng, phục vụ, boa, trả tiền, uy tín, hết ca.

Test gọi thẳng QuanSim với một inp giả để dịch chuyển người chơi tới bếp/bàn; không phụ thuộc
lát của C (khách đến, kiên nhẫn) vì khách được dựng sẵn trong fixture.

Từ Ticket-03 (v1.2) kho là mảng cá thể. `make()` đổi số đếm {loại: số} thành cá thể tươi 100 điểm, và
`reserved` công thức thành mảng id cá thể; logic các test giữ nguyên.
"""

import json
import os
import unittest
from collections import Counter

from helpers import ROOT
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
    TUNING = json.load(f)["tuning"]

STOVE_B1 = [2, 8]
TABLE_T1 = [9, 2]


class Inp:
    def __init__(self, interact=False):
        self._interact = interact
        self.move = (0.0, 0.0)

    def pressed(self, name):
        return name == "interact" and self._interact


def customer(cid="C1", table="T1", dish="goi_bong_sung", order_tick=0, status="reserved",
             state="waiting", patience=None, **kw):
    recipe = dict(TUNING["menu"][dish]["recipe"])
    c = {
        "id": cid, "table_id": table, "dish_id": dish, "order_tick": order_tick,
        "state": state, "patience_ticks_left": 3600 * 1 if patience is None else patience,
        "eat_ticks_left": 0, "order_status": status,
        "reserved": recipe if status == "reserved" else {},
        "base_price": 0, "tip": 0,
    }
    c.update(kw)
    return c


def to_items(counts):
    """{loại: số} -> cá thể public {id, kind, fresh}, id I1, I2, ... theo thứ tự loại.
    Tươi 100 + 1/240 (24001 đơn vị): kho hao 1 đơn vị đúng ở bước nấu, nên giá chốt vẫn đúng 40 như niêm yết."""
    items = []
    for kind in sorted(counts):
        for _ in range(counts[kind]):
            items.append({"id": f"I{len(items) + 1}", "kind": kind, "fresh": 100 + 1 / 240})
    return items


def bind(customers, items):
    """`reserved` công thức {loại: số} -> mảng id cá thể còn trống trong kho."""
    free = list(items)
    for c in customers:
        res = c["reserved"]
        ids = []
        if isinstance(res, dict):
            for kind in sorted(res):
                for _ in range(res[kind]):
                    it = next(i for i in free if i["kind"] == kind)
                    free.remove(it)
                    ids.append(it["id"])
        c["reserved"] = ids
    return customers


def counts(sim):
    """Số cá thể còn trong kho theo loại."""
    return dict(Counter(it["kind"] for it in sim.stock))


def make(customers=(), stock=None, hand=None, stoves=None, pos=None, time_left=None):
    items = to_items(stock or {})
    cs = bind(list(customers), items)
    sc = {"stock": items, "customers": cs, "random_customers": False}
    if hand is not None:
        sc["hand"] = hand
    if stoves is not None:
        sc["stoves"] = stoves
    if time_left is not None:
        sc["time_left_ticks"] = time_left
    sim = QuanSim(TUNING, sc, Streams(1), IdAllocator())
    if pos is not None:
        sim.pos = list(pos)
    return sim


def names(events):
    return [n for n, _ in events]


def data_of(events, name):
    return [d for n, d in events if n == name]


class CookServeCycle(unittest.TestCase):
    def test_vong_day_du_nau_bung_phuc_vu_tra_tien(self):
        sim = make(customers=[customer()], stock={"bong_sung": 2}, pos=STOVE_B1)

        ev = sim.step(Inp(interact=True))
        self.assertEqual(names(ev), ["cook_started"])
        self.assertEqual(counts(sim), {})
        c = sim.customers[0]
        self.assertEqual(c["order_status"], "assigned")
        self.assertEqual(c["reserved"], [])
        self.assertEqual(c["base_price"], 40)
        stove = sim.stoves[0]
        self.assertEqual(stove["state"], "cooking")
        self.assertEqual(stove["cook_ticks_left"], 4 * 60)

        ready = []
        for _ in range(4 * 60):
            ready += sim.step(Inp())
        self.assertIn("dish_ready", names(ready))
        self.assertEqual(sim.stoves[0]["state"], "ready")

        sim.step(Inp(interact=True))  # nhặt món ở bếp
        self.assertEqual(sim.hand, {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40})
        self.assertEqual(sim.stoves[0]["state"], "idle")

        sim.pos = list(TABLE_T1)
        ev = sim.step(Inp(interact=True))
        self.assertEqual(names(ev), ["served"])
        served = data_of(ev, "served")[0]
        self.assertEqual(served["tip"], 8)  # floor(40 * 0.2), kiên nhẫn đầy
        self.assertIsNone(sim.hand)
        self.assertEqual(sim.customers[0]["state"], "eating")

        paid = []
        for _ in range(10 * 60):
            paid += sim.step(Inp())
        p = data_of(paid, "paid")
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0]["amount"], 48)
        self.assertEqual(p[0]["reason"], "finished_eating")
        self.assertEqual(sim.money, 48)
        self.assertEqual(sim.earned, 48)
        self.assertEqual(sim.shift_earned, 48)
        self.assertAlmostEqual(sim.reputation, 3.2)
        self.assertEqual(sim.customers, [])
        score = sim.earned + 100 * int(sim.reputation)
        self.assertEqual(score, 348)


class Rules(unittest.TestCase):
    def test_khong_co_don_reserved_thi_bep_khong_nau(self):
        sim = make(customers=[], stock={"bong_sung": 2}, pos=STOVE_B1)
        self.assertEqual(sim.step(Inp(interact=True)), [])
        self.assertEqual(counts(sim), {"bong_sung": 2})
        self.assertEqual(sim.stoves[0]["state"], "idle")

    def test_dung_mep_ban_kinh_tuong_tac(self):
        sim = make(customers=[customer()], stock={"bong_sung": 2}, pos=[STOVE_B1[0] + 1.5, STOVE_B1[1]])
        self.assertEqual(names(sim.step(Inp(interact=True))), ["cook_started"])

    def test_ngoai_ban_kinh_khong_lam_gi(self):
        # v1.1 có thêm B2 ở [5, 8] (Ticket-02 mục 1.3): đứng lệch theo trục z để ngoài tầm cả B1 lẫn B2.
        sim = make(customers=[customer()], stock={"bong_sung": 2}, pos=[STOVE_B1[0], STOVE_B1[1] - 1.6])
        self.assertEqual(sim.step(Inp(interact=True)), [])
        self.assertEqual(sim.stoves[0]["state"], "idle")

    def test_ready_tang_ready_ticks_tu_buoc_sau(self):
        sim = make(customers=[customer()], stock={"bong_sung": 2}, pos=STOVE_B1)
        sim.step(Inp(interact=True))
        for _ in range(4 * 60):
            sim.step(Inp())
        self.assertEqual(sim.stoves[0]["ready_ticks"], 0)  # vừa chín ở bước này
        sim.step(Inp())
        self.assertEqual(sim.stoves[0]["ready_ticks"], 1)

    def test_tay_day_khong_nhan_mon_thu_hai(self):
        other = {"order_id": "C9", "dish_id": "goi_bong_sung", "base_price": 40}
        sim = make(customers=[customer()], stock={"bong_sung": 2}, pos=STOVE_B1, hand=other)
        sim.step(Inp(interact=True))
        for _ in range(4 * 60):
            sim.step(Inp())
        self.assertEqual(sim.stoves[0]["state"], "ready")
        ev = sim.step(Inp(interact=True))
        self.assertEqual(ev, [])
        self.assertEqual(sim.hand, other)
        self.assertEqual(sim.stoves[0]["state"], "ready")

    def test_boa_bang_0_khi_kien_nhan_duoi_mot_nua(self):
        sim = make(customers=[customer(status="assigned", patience=1000, base_price=40)],
                   hand={"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40}, pos=TABLE_T1)
        ev = sim.step(Inp(interact=True))
        self.assertEqual(data_of(ev, "served")[0]["tip"], 0)

    def test_chua_dung_khach_khong_nhan_mon(self):
        sim = make(customers=[customer(status="assigned", base_price=40)],
                   hand={"order_id": "C7", "dish_id": "goi_bong_sung", "base_price": 40}, pos=TABLE_T1)
        self.assertEqual(sim.step(Inp(interact=True)), [])
        self.assertIsNotNone(sim.hand)

    def test_don_cu_nhat_duoc_nau_truoc(self):
        newer = customer("C2", table="T1", order_tick=50)
        older = customer("C1", table="T1", order_tick=10)
        sim = make(customers=[newer, older], stock={"bong_sung": 4}, pos=STOVE_B1)
        ev = sim.step(Inp(interact=True))
        self.assertEqual(data_of(ev, "cook_started")[0]["order_id"], "C1")

    def test_lau_ghi_items_theo_loai_roi_id(self):
        c = customer("C1", dish="lau_ca_linh_dien_dien", table="T1")
        sim = make(customers=[c], stock={"ca_linh": 3, "bong_dien_dien": 1}, pos=STOVE_B1)
        ev = sim.step(Inp(interact=True))
        items = data_of(ev, "cook_started")[0]["items"]
        self.assertEqual([it["kind"] for it in items], ["bong_dien_dien", "ca_linh", "ca_linh", "ca_linh"])
        self.assertEqual(counts(sim), {})


class ClosingAndDrop(unittest.TestCase):
    def test_het_ca_khach_dang_an_tra_closing(self):
        c = customer(status="served", state="eating", base_price=40, tip=8, eat_ticks_left=500)
        sim = make(customers=[c], time_left=1)
        ev = sim.step(Inp())
        self.assertEqual(names(ev), ["paid", "quan_end"])
        p = data_of(ev, "paid")[0]
        self.assertEqual(p["reason"], "closing")
        self.assertEqual(p["amount"], 48)
        self.assertEqual(sim.money, 48)

    def test_vua_phuc_vu_luc_het_ca_van_tra_tien(self):
        c = customer(status="assigned", base_price=40)
        hand = {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40}
        sim = make(customers=[c], hand=hand, pos=TABLE_T1, time_left=1)
        ev = sim.step(Inp(interact=True))
        self.assertEqual(names(ev), ["served", "paid", "quan_end"])
        self.assertEqual(data_of(ev, "paid")[0]["reason"], "closing")
        self.assertEqual(data_of(ev, "paid")[0]["amount"], 48)  # 40 + boa 8 (kiên nhẫn đầy)
        self.assertEqual(sim.money, 48)

    def test_drop_order_bo_mon_tren_bep_va_tay(self):
        stove = {"id": "B1", "state": "cooking", "cook_ticks_left": 100, "ready_ticks": 0,
                 "dish": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40}}
        sim = make(customers=[], stoves=[stove], hand={"order_id": "C2", "dish_id": "goi_bong_sung",
                                                       "base_price": 40})
        sim._drop_order("C1")
        self.assertEqual(sim.stoves[0]["state"], "idle")
        self.assertIsNone(sim.stoves[0]["dish"])
        self.assertEqual(sim.hand["order_id"], "C2")
        sim._drop_order("C2")
        self.assertIsNone(sim.hand)


if __name__ == "__main__":
    unittest.main()
