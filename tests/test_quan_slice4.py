"""Unit tests cho Lát 4 (Quán): bếp, bưng, phục vụ, tiền, boa, uy tín, hết ca."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session


def _base_tuning():
    return copy.deepcopy(load_contract()["tuning"])


def _run_quan(scenario, frames, ticks, tuning=None):
    t = tuning or _base_tuning()
    sess = Session("quan", t, scenario, seed=42)
    ip = InputPlayer(frames)
    all_events = []
    for k in range(ticks):
        if sess.done:
            break
        all_events.extend(sess.step(ip.advance(k)))
    return sess, all_events


class QuanSlice4Tests(unittest.TestCase):
    def test_full_cook_pick_serve_pay_with_tip(self):
        # Đứng ngay tại bếp B1 [2, 8], nấu gỏi bông súng (cook_s=4 -> 240 tick, price=40, tip=8)
        sc = {
            "player": {"pos": [2, 8]},
            "stock": {"bong_sung": 2},
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}],
            "random_customers": False,
        }
        # Tick 0: interact bếp -> cook_started
        sess, evs = _run_quan(sc, [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}], ticks=245)
        names = [e["name"] for e in evs]
        self.assertIn("cook_started", names)
        self.assertIn("dish_ready", names)
        cs = next(e for e in evs if e["name"] == "cook_started")
        self.assertEqual(cs["data"]["items"], ["bong_sung", "bong_sung"])
        self.assertEqual(cs["data"]["base_price"], 40)
        self.assertEqual(sess.sim.stock["bong_sung"], 0)

        # Kiểm tra ready_ticks: cook_started ở bước 0 (sau _tick_timers) -> dish_ready ở bước 240 (tick 241, ready_ticks=0),
        # thêm 4 bước (241..244) đến tick 245 -> ready_ticks == 4
        snap = sess.snapshot()
        self.assertEqual(snap["stoves"][0]["state"], "ready")
        self.assertEqual(snap["stoves"][0]["ready_ticks"], 4)

        # Nhấc món tại tick 245, dịch chuyển về bàn T1 [9, 2] ở scenario mới
        sc2 = {
            "player": {"pos": [2, 8]},
            "stoves": [{"id": "B1", "state": "ready", "dish": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40}}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned"}],
            "random_customers": False,
        }
        sess2, evs2 = _run_quan(sc2, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual([e["name"] for e in evs2], ["dish_picked"])
        self.assertEqual(sess2.sim.hand["order_id"], "C1")
        self.assertEqual(sess2.sim.stoves[0]["state"], "idle")

        # Phục vụ tại bàn T1 [9, 2] và đợi ăn xong (eat_s=10 -> 600 tick)
        sc3 = {
            "player": {"pos": [9, 2]},
            "hand": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned"}],
            "random_customers": False,
        }
        sess3, evs3 = _run_quan(sc3, [{"tick": 0, "interact": True}], ticks=601)
        served = next(e for e in evs3 if e["name"] == "served")
        self.assertEqual(served["data"]["tip"], 8)
        paid = next(e for e in evs3 if e["name"] == "paid")
        self.assertEqual(paid["data"], {
            "order_id": "C1", "table_id": "T1", "base_price": 40, "tip": 8, "amount": 48, "reason": "finished_eating",
        })
        self.assertEqual(sess3.sim.money, 48)
        self.assertEqual(sess3.sim.earned, 48)
        self.assertAlmostEqual(sess3.sim.reputation, 3.2)

    def test_no_tip_when_patience_below_threshold(self):
        # patience_s=60 -> 3600 tick; tip_min_patience_ratio=0.5 -> cần >= 1800 sau bước 1
        sc = {
            "player": {"pos": [9, 2]},
            "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "order_status": "assigned", "patience_ticks_left": 1800,
            }],
            "random_customers": False,
        }
        # Sau bước 1, patience_ticks_left giảm còn 1799 < 1800 -> tip = 0
        sess, evs = _run_quan(sc, [{"tick": 0, "interact": True}], ticks=601)
        served = next(e for e in evs if e["name"] == "served")
        self.assertEqual(served["data"]["tip"], 0)
        self.assertEqual(sess.sim.money, 60)
        self.assertAlmostEqual(sess.sim.reputation, 3.0)

    def test_closing_pays_eating_and_leaves_waiting_without_rep_loss(self):
        sc = {
            "player": {"pos": [9, 2]},
            "hand": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                "order_status": "assigned", "patience_ticks_left": 100,
            }],
            "time_left_ticks": 1,
            "random_customers": False,
        }
        # Phục vụ đúng tick cuối -> eating và trả tiền ngay với reason="closing"
        sess, evs = _run_quan(sc, [{"tick": 0, "interact": True}], ticks=1)
        names = [e["name"] for e in evs]
        self.assertEqual(names, ["served", "paid", "quan_end"])
        self.assertEqual(evs[1]["data"]["reason"], "closing")
        self.assertTrue(sess.done)

        # Khách waiting lúc hết giờ -> rời với reason="closing", không trừ uy tín, dọn món trên bếp/tay
        sc_wait = {
            "player": {"pos": [8, 5]},
            "stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 50,
                        "dish": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40}}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned"}],
            "time_left_ticks": 1,
            "random_customers": False,
        }
        sess2, evs2 = _run_quan(sc_wait, [], ticks=1)
        self.assertEqual([e["name"] for e in evs2], ["customer_left", "quan_end"])
        self.assertEqual(evs2[0]["data"]["reason"], "closing")
        self.assertAlmostEqual(sess2.sim.reputation, 3.0)
        self.assertEqual(sess2.sim.stoves[0]["state"], "idle")

    def test_interact_priority_does_not_fall_through(self):
        # Đặt bếp B1 và bàn T1 cùng tầm, bếp gần hơn nhưng đang cooking -> bỏ lượt, không tương tác bàn
        sc = {
            "player": {"pos": [2.2, 8.0]},
            "hand": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
            "stoves": [{"id": "B1", "pos": [2.0, 8.0], "state": "cooking", "cook_ticks_left": 10,
                        "dish": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40}}],
            "tables": [{"id": "T1", "pos": [3.0, 8.0]}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned"}],
            "random_customers": False,
        }
        sess, evs = _run_quan(sc, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(evs, [])
        self.assertIsNotNone(sess.sim.hand)

    def test_serve_at_exact_zero_patience_tick_succeeds(self):
        sc = {
            "player": {"pos": [9, 2]},
            "hand": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                "order_status": "assigned", "patience_ticks_left": 1,
            }],
            "random_customers": False,
        }
        sess, evs = _run_quan(sc, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual([e["name"] for e in evs], ["served"])
        self.assertEqual(evs[0]["data"]["tip"], 0)
        self.assertEqual(sess.sim.customers[0]["state"], "eating")

    def test_cook_picks_oldest_order_then_table_id(self):
        # C2 có order_tick nhỏ hơn -> nấu trước; nếu cùng order_tick thì T2 trước T10
        t = _base_tuning()
        t["quan"]["tables"] = [{"id": "T1", "pos": [9, 2]}, {"id": "T2", "pos": [11, 2]}, {"id": "T10", "pos": [13, 2]}]
        sc = {
            "player": {"pos": [2, 8]},
            "stock": {"bong_sung": 4, "ca_loc": 1},
            "customers": [
                {"id": "C10", "table_id": "T10", "dish_id": "goi_bong_sung", "order_tick": 5},
                {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "order_tick": 5},
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 10},
            ],
            "random_customers": False,
        }
        sess, evs = _run_quan(sc, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(evs[0]["name"], "cook_started")
        self.assertEqual(evs[0]["data"]["order_id"], "C2")

    def test_patience_leave_cleans_hand_and_reduces_reputation_without_refund(self):
        sc = {
            "player": {"pos": [8, 5]},
            "stock": {"bong_sung": 0},
            "hand": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                "order_status": "assigned", "patience_ticks_left": 1,
            }],
            "random_customers": False,
        }
        sess, evs = _run_quan(sc, [], ticks=1)
        self.assertEqual([e["name"] for e in evs], ["customer_left"])
        self.assertEqual(evs[0]["data"]["reason"], "patience")
        self.assertAlmostEqual(sess.sim.reputation, 2.5)
        self.assertIsNone(sess.sim.hand)
        self.assertEqual(sess.sim.customers, [])
        self.assertEqual(sess.sim.stock["bong_sung"], 0)


if __name__ == "__main__":
    unittest.main()
