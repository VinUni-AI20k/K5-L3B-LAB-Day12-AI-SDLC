"""Test luật `quan` (buổi tối: mở quán) — Phase 1. Module: quan · Vai: QA.

Kiểu HỘP ĐEN qua `headless_cmd`; số liệu đọc từ game.contract.json. Căn cứ luật: PRD-0.md mục D (scenario),
E (output), F (Quán), G (kho). Bước k đọc frame tick=k và ghi event ở tick k+1.
Fixture khách theo mục D: {id, table_id, dish_id, order_tick, state, patience_ticks_left, eat_ticks_left,
order_status, reserved, base_price, tip}; payload món {order_id, dish_id, base_price}.

Mã AC do nhóm tự đặt (PRD-0 chỉ gợi ý dạng `AC-P1-xx`); dùng để điền docs/verification/phase-1.md:

| AC        | Nhóm test | Luật được kiểm (PRD-0)                                           |
|-----------|-----------|------------------------------------------------------------------|
| AC-P1-06  | Khach     | F: khách đến theo lịch, chọn món đủ kho, giữ chỗ, no_dish        |
| AC-P1-07  | Bep       | F: nấu (tiêu nguyên liệu), món chín, bưng, phục vụ               |
| AC-P1-08  | Tien      | F: trả tiền, boa theo kiên nhẫn, uy tín                          |
| AC-P1-09  | HetGio    | F: hết kiên nhẫn, hết ca (khách ăn trả ngay, khách chờ closing)  |
| AC-P1-10  | Di        | F: đi lại, chặn biên                                             |

Test sẽ ĐỎ cho tới khi luật tương ứng được viết (TODO trong chonoi/sim/quan.py). Không sửa test cho xanh khi luật sai.
Chạy: PYTHONPATH=tests:. python3 -m unittest test_rules_quan -v
"""

import unittest

from helpers import Workdir, events, frames
from rules_common import at, contract_tuning, run_mode

LOC = "ca_loc_nuong_trui"
PRICE_LOC = 60  # menu.ca_loc_nuong_trui.price trong preset


def run(w, block, **kw):
    return run_mode(w, "quan", block, **kw)


def tuning():
    return contract_tuning("quan")


def only(rows, name):
    ev = events(rows, name)
    assert len(ev) == 1, f"cần đúng 1 event {name}, có {len(ev)}"
    return ev[0]


def cust(cid="C1", **kw):
    """Khách fixture mặc định: chờ ở T1, gọi cá lóc nướng trui, giữ 1 cá lóc."""
    c = {"id": cid, "table_id": "T1", "dish_id": LOC, "order_tick": 0, "state": "waiting",
         "order_status": "reserved", "reserved": {"ca_loc": 1}}
    c.update(kw)
    return c


class Khach(unittest.TestCase):
    """AC-P1-06 — khách đến, chọn món, giữ chỗ."""

    def test_khach_01_first_customer_on_schedule_reserves_recipe(self):
        """Tick first_customer_tick: `customer_arrived` ở T1; khách giữ đúng công thức; chưa có khách trước đó.
        Kho chỉ đủ 1 món (cá lóc) nên món được chọn phải là cá lóc nướng trui."""
        first = tuning()["first_customer_tick"]
        with Workdir() as w:
            rows = run(w, {"stock": {"ca_loc": 1}}, ticks=first)
            self.assertEqual(at(rows, first - 1)["customers"], [])
            ev = only(rows, "customer_arrived")
            self.assertEqual(ev["tick"], first)
            self.assertEqual(ev["data"]["table_id"], "T1")
            self.assertEqual(ev["data"]["dish_id"], LOC)
            c = at(rows, first)["customers"][0]
            self.assertEqual(c["reserved"], {"ca_loc": 1})
            self.assertEqual(c["order_tick"], first)
            self.assertEqual(ev["data"]["order_id"], c["id"])

    def test_khach_02_no_dish_when_stock_insufficient(self):
        """Có bàn trống mà không món nào đủ nguyên liệu: `no_dish` {}, không có khách."""
        first = tuning()["first_customer_tick"]
        with Workdir() as w:
            rows = run(w, {"stock": {"bong_sung": 1}}, ticks=first)
            self.assertEqual(only(rows, "no_dish")["data"], {})
            self.assertEqual(at(rows, first)["customers"], [])

    def test_khach_03_no_free_table_skips_turn(self):
        """Không còn bàn trống thì bỏ lượt: không `customer_arrived`, không `no_dish`.
        Lý do cập nhật test (v1.1, TICKET-02 mục 1.3): quán có 4 bàn T1–T4 nên fixture
        phải chiếm đủ cả 4 bàn mới còn ý nghĩa 'hết bàn'; giữ chỗ phải khớp tồn kho."""
        first = tuning()["first_customer_tick"]
        with Workdir() as w:
            sc = {"stock": {"ca_loc": 4},
                  "customers": [cust(f"C{i}", table_id=f"T{i}", patience_ticks_left=first + 100)
                                for i in range(1, 5)]}
            rows = run(w, sc, ticks=first)
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual(events(rows, "no_dish"), [])

    def test_khach_04_random_customers_false_disables_arrivals(self):
        """random_customers:false tắt khách tự sinh."""
        first = tuning()["first_customer_tick"]
        with Workdir() as w:
            rows = run(w, {"stock": {"ca_loc": 1}, "random_customers": False}, ticks=first + 5)
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual(at(rows, first + 5)["customers"], [])


class Bep(unittest.TestCase):
    """AC-P1-07 — nấu, món chín, bưng, phục vụ."""

    def test_bep_01_cook_started_consumes_reserved_stock(self):
        """interact cạnh bếp idle: lấy đơn reserved, tiêu nguyên liệu giữ, `cook_started`, bếp cooking đủ cook_s × 60."""
        with Workdir() as w:
            sc = {"stock": {"ca_loc": 1}, "random_customers": False, "player": {"pos": [2, 7.5]},
                  "customers": [cust()]}
            rows = run(w, sc, inp=frames({"tick": 0, "interact": True}), ticks=1)
            d = only(rows, "cook_started")["data"]
            self.assertEqual((d["stove_id"], d["order_id"], d["dish_id"]), ("B1", "C1", LOC))
            self.assertEqual(d["items"], ["ca_loc"])
            self.assertEqual(d["base_price"], PRICE_LOC)
            s = at(rows, 1)
            b1 = next(b for b in s["stoves"] if b["id"] == "B1")
            self.assertEqual(b1["state"], "cooking")
            self.assertEqual(b1["cook_ticks_left"], 6 * 60)
            self.assertEqual(s["stock"], {})
            self.assertEqual(s["customers"][0]["order_status"], "assigned")
            self.assertEqual(s["customers"][0]["reserved"], {})

    def test_bep_02_dish_ready_then_pick_up(self):
        """Món nấu xong → `dish_ready`, ready_ticks = 0; interact nhận món: `dish_picked`, tay có payload, bếp idle."""
        dish = {"order_id": "C1", "dish_id": LOC, "base_price": PRICE_LOC}
        with Workdir() as w:
            sc = {"random_customers": False, "player": {"pos": [2, 7.5]},
                  "customers": [cust(order_status="assigned", reserved={})],
                  "stoves": [{"id": "B1", "state": "cooking", "dish": dish, "cook_ticks_left": 3}]}
            inp = frames({"tick": 5, "interact": True})
            rows = run(w, sc, inp=inp, ticks=6)
            self.assertEqual(only(rows, "dish_ready")["tick"], 3)
            self.assertEqual(only(rows, "dish_ready")["data"]["stove_id"], "B1")
            self.assertEqual(only(rows, "dish_picked")["tick"], 6)
            s = at(rows, 6)
            self.assertEqual(s["hand"], dish)
            self.assertEqual(next(b for b in s["stoves"] if b["id"] == "B1")["state"], "idle")

    def test_bep_03_serve_order_to_customer_table(self):
        """Tay có món đúng đơn, interact cạnh bàn: `served` {order_id,table_id,dish_id,patience_ticks_left,base_price,tip};
        khách chuyển eating với timer ăn đầy; tay trống."""
        dish = {"order_id": "C1", "dish_id": LOC, "base_price": PRICE_LOC}
        t = tuning()
        with Workdir() as w:
            sc = {"random_customers": False, "player": {"pos": [9, 2.5]}, "hand": dish,
                  "customers": [cust(order_status="assigned", reserved={})]}
            rows = run(w, sc, inp=frames({"tick": 0, "interact": True}), ticks=1)
            d = only(rows, "served")["data"]
            self.assertEqual((d["order_id"], d["table_id"], d["dish_id"], d["base_price"]),
                             ("C1", "T1", LOC, PRICE_LOC))
            self.assertEqual(d["tip"], int(PRICE_LOC * t["tip_rate"]))
            s = at(rows, 1)
            self.assertIsNone(s["hand"])
            c = s["customers"][0]
            self.assertEqual(c["state"], "eating")
            self.assertEqual(c["eat_ticks_left"], t["eat_s"] * 60)

    def test_bep_04_wrong_order_not_served(self):
        """Món của đơn khác không phục vụ được cho khách này (bỏ lượt, tay giữ nguyên)."""
        dish = {"order_id": "C9", "dish_id": LOC, "base_price": PRICE_LOC}
        with Workdir() as w:
            sc = {"random_customers": False, "player": {"pos": [9, 2.5]}, "hand": dish,
                  "customers": [cust(order_status="assigned", reserved={})]}
            rows = run(w, sc, inp=frames({"tick": 0, "interact": True}), ticks=1)
            self.assertEqual(events(rows, "served"), [])


class Tien(unittest.TestCase):
    """AC-P1-08 — boa, trả tiền, uy tín."""

    def serve(self, patience_left):
        dish = {"order_id": "C1", "dish_id": LOC, "base_price": PRICE_LOC}
        with Workdir() as w:
            sc = {"random_customers": False, "player": {"pos": [9, 2.5]}, "hand": dish,
                  "customers": [cust(order_status="assigned", reserved={}, patience_ticks_left=patience_left)]}
            rows = run(w, sc, inp=frames({"tick": 0, "interact": True}), ticks=1)
            return only(rows, "served")["data"]

    def test_tien_01_tip_when_patience_ratio_enough(self):
        """Kiên nhẫn còn ≥ tip_min_patience_ratio: boa = floor(giá × tip_rate) (= 12 với giá 60, tỷ lệ 0.2)."""
        self.assertEqual(self.serve(patience_left=3000)["tip"], 12)

    def test_tien_02_no_tip_when_patience_low(self):
        """Kiên nhẫn dưới ngưỡng boa: boa 0."""
        self.assertEqual(self.serve(patience_left=100)["tip"], 0)

    def test_tien_03_paid_after_eating_and_reputation_bonus(self):
        """Ăn xong: `paid` {amount = giá + boa, reason finished_eating}, khách rời bàn, tiền/earned tăng, uy tín +tip_reputation."""
        t = tuning()
        with Workdir() as w:
            sc = {"random_customers": False,
                  "customers": [cust(state="eating", order_status="served", reserved={},
                                     eat_ticks_left=3, base_price=PRICE_LOC, tip=12)]}
            rows = run(w, sc, ticks=3)
            d = only(rows, "paid")
            self.assertEqual(d["tick"], 3)
            self.assertEqual(d["data"], {"order_id": "C1", "table_id": "T1", "base_price": PRICE_LOC, "tip": 12,
                                         "amount": 72, "reason": "finished_eating"})
            s = at(rows, 3)
            self.assertEqual((s["money"], s["earned"]), (72, 72))
            self.assertAlmostEqual(s["reputation"], t["reputation_initial"] + t["tip_reputation"], places=2)
            self.assertEqual(s["customers"], [])
            self.assertEqual(s["score"], 72 + 100 * 3)

    def test_tien_04_no_reputation_bonus_without_tip(self):
        """Boa 0 thì uy tín không đổi khi thu tiền."""
        with Workdir() as w:
            sc = {"random_customers": False,
                  "customers": [cust(state="eating", order_status="served", reserved={},
                                     eat_ticks_left=2, base_price=PRICE_LOC, tip=0)]}
            rows = run(w, sc, ticks=2)
            self.assertAlmostEqual(at(rows, 2)["reputation"], tuning()["reputation_initial"], places=2)


class HetGio(unittest.TestCase):
    """AC-P1-09 — hết kiên nhẫn và hết ca."""

    def test_het_01_patience_runs_out(self):
        """Khách waiting hết kiên nhẫn khi ca còn giờ: `customer_left` reason patience, uy tín + left_reputation_delta,
        nhả phần giữ (kho còn nguyên vì chưa nấu)."""
        t = tuning()
        with Workdir() as w:
            sc = {"stock": {"ca_loc": 1}, "random_customers": False, "customers": [cust(patience_ticks_left=5)]}
            rows = run(w, sc, ticks=6)
            ev = only(rows, "customer_left")
            self.assertEqual(ev["tick"], 5)
            self.assertEqual(ev["data"]["reason"], "patience")
            self.assertEqual((ev["data"]["order_id"], ev["data"]["table_id"]), ("C1", "T1"))
            self.assertAlmostEqual(ev["data"]["reputation"], t["reputation_initial"] + t["left_reputation_delta"], places=2)
            s = at(rows, 6)
            self.assertEqual(s["customers"], [])
            self.assertEqual(s["stock"], {"ca_loc": 1})

    def test_het_02_reputation_clamped_at_min(self):
        """Uy tín không xuống dưới reputation_min."""
        with Workdir() as w:
            sc = {"random_customers": False, "reputation": 0.2, "stock": {"ca_loc": 1},
                  "customers": [cust(patience_ticks_left=2)]}
            rows = run(w, sc, ticks=3)
            self.assertAlmostEqual(at(rows, 3)["reputation"], tuning()["reputation_min"], places=2)

    def test_het_03_closing_waiting_customer_leaves_without_penalty(self):
        """Hết ca: khách còn chờ rời với reason closing, không trừ uy tín; rồi `quan_end`."""
        with Workdir() as w:
            sc = {"random_customers": False, "time_left_ticks": 3, "stock": {"ca_loc": 1}, "customers": [cust()]}
            rows = run(w, sc, ticks=10)
            self.assertEqual(only(rows, "customer_left")["data"]["reason"], "closing")
            end = only(rows, "quan_end")
            self.assertEqual(end["tick"], 3)
            self.assertAlmostEqual(end["data"]["reputation"], tuning()["reputation_initial"], places=2)
            self.assertEqual(rows[-1]["reason"], "time")

    def test_het_04_closing_eating_customer_pays_immediately(self):
        """Hết ca: khách đang ăn trả ngay (reason closing) rồi `quan_end` với shift_earned đúng."""
        with Workdir() as w:
            sc = {"random_customers": False, "time_left_ticks": 3,
                  "customers": [cust(state="eating", order_status="served", reserved={},
                                     eat_ticks_left=500, base_price=PRICE_LOC, tip=12)]}
            rows = run(w, sc, ticks=10)
            self.assertEqual(only(rows, "paid")["data"]["reason"], "closing")
            self.assertEqual(only(rows, "paid")["data"]["amount"], 72)
            end = only(rows, "quan_end")["data"]
            self.assertEqual((end["money"], end["earned"], end["shift_earned"]), (72, 72, 72))


class Di(unittest.TestCase):
    """AC-P1-10 — đi lại."""

    def test_di_01_walk_stays_in_bounds(self):
        """Đi chéo mãi vào góc: bị chặn đúng biên trên của x và z."""
        b = tuning()["bounds"]
        with Workdir() as w:
            rows = run(w, {}, inp=frames({"tick": 0, "move": [1, 1]}), ticks=600, every=600)
            self.assertEqual(tuple(at(rows, 600)["player"]["pos"]), (b["x"][1], b["z"][1]))


if __name__ == "__main__":
    unittest.main()
