"""Unit & integration tests độc lập cho Lát 4 (US4: Bếp, bưng, phục vụ, tiền, boa, uy tín, đóng ca).

Chủ: Phạm Quốc Huy (pqhuy454).
Kiểm chứng toàn bộ Acceptance Scenarios 1–9 của US4 và FR-034, FR-035, FR-040..FR-046
mà không cần phụ thuộc hoàn thành US3 (dùng khách dựng sẵn qua scenario).
"""

import json
import math
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer
from chonoi.runner import Session
from chonoi.scenario import load_scenario
from chonoi.sim import ledger, pick, quan_kitchen


def _tuning():
    return load_contract()["tuning"]


def _step_n(sess, frames_list, n):
    player = InputPlayer(frames_list)
    all_events = []
    for _ in range(n):
        if sess.done:
            break
        inp = player.advance(sess.tick)
        all_events.extend(sess.step(inp))
    return all_events


def _ev_names(events):
    return [e["name"] for e in events]


class TestQuanKitchenUS4(unittest.TestCase):
    def test_us4_01_02_03_04_full_cycle_with_tip_and_reputation(self):
        """AS1-AS4: Nấu -> dish_ready -> dish_picked -> served (>=50% kiên nhẫn) -> paid (boa + uy tín +0.2)."""
        t = _tuning()
        # Đặt khách C1 tại T1 [9,2] gọi lẩu cá linh (120k, nấu 10s = 600 tick), kiên nhẫn 3000 (sau 603 tick còn 2397 >= 1800)
        sc = {
            "player": {"pos": [2, 8]},
            "stock": {"ca_linh": 3, "bong_dien_dien": 1},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish": "lau_ca_linh_dien_dien",
                "state": "waiting", "patience_ticks": 3000,
                "reserved": {"ca_linh": 3, "bong_dien_dien": 1},
            }],
        }
        sess = Session("quan", t, sc, seed=1)
        # Tick 0: bấm interact tại B1 -> cook_started, tiêu nguyên liệu khỏi kho
        evs = _step_n(sess, [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}], 1)
        self.assertEqual(_ev_names(evs), ["cook_started"])
        self.assertEqual(evs[0]["data"], {"stove_id": "B1", "dish": "lau_ca_linh_dien_dien", "customer_id": "C1"})
        self.assertEqual(sess.sim.stock, {})
        self.assertEqual(sess.sim.stoves[0]["state"], "cooking")
        self.assertEqual(sess.sim.stoves[0]["cook_ticks_left"], 600)

        # Chạy 600 tick -> bếp chuyển ready và phát dish_ready ở tick thứ 600
        evs_cook = _step_n(sess, [], 600)
        self.assertEqual(_ev_names(evs_cook), ["dish_ready"])
        self.assertEqual(evs_cook[0]["data"], {"stove_id": "B1", "dish": "lau_ca_linh_dien_dien"})
        self.assertEqual(sess.sim.stoves[0]["state"], "ready")

        # Lấy món tại B1 -> dish_picked, tay cầm món, bếp về idle
        evs_pick = _step_n(sess, [{"tick": sess.tick, "interact": True}, {"tick": sess.tick + 1, "interact": False}], 1)
        self.assertEqual(_ev_names(evs_pick), ["dish_picked"])
        self.assertEqual(sess.sim.stoves[0]["state"], "idle")
        self.assertEqual(sess.sim.hand, {"dish": "lau_ca_linh_dien_dien", "customer_id": "C1"})

        # Di chuyển tới bàn T1 [9, 2] và phục vụ -> served (tip = floor(120 * 0.2) = 24)
        sess.sim.pos = [9.0, 2.0]
        evs_serve = _step_n(sess, [{"tick": sess.tick, "interact": True}, {"tick": sess.tick + 1, "interact": False}], 1)
        self.assertEqual(_ev_names(evs_serve), ["served"])
        self.assertEqual(evs_serve[0]["data"], {"customer_id": "C1", "dish": "lau_ca_linh_dien_dien", "tip": 24})
        self.assertIsNone(sess.sim.hand)
        self.assertEqual(sess.sim.customers[0]["state"], "eating")
        self.assertEqual(sess.sim.customers[0]["eat_ticks"], 600)
        # Uy tín CHƯA tăng lúc phục vụ, chỉ tăng lúc trả tiền
        self.assertEqual(sess.sim.reputation, 3.0)

        # Ăn 600 tick -> paid (144k), uy tín +0.2 = 3.2, khách rời danh sách
        evs_eat = _step_n(sess, [], 600)
        self.assertEqual(_ev_names(evs_eat), ["paid"])
        self.assertEqual(evs_eat[0]["data"], {"customer_id": "C1", "amount": 144, "tip": 24})
        self.assertEqual(sess.sim.money, 144)
        self.assertEqual(sess.sim.earned, 144)
        self.assertEqual(sess.sim.shift_earned, 144)
        self.assertEqual(sess.sim.reputation, 3.2)
        self.assertEqual(sess.sim.customers, [])
        # AS9: score = earned + 100 * floor(reputation) = 144 + 300 = 444
        self.assertEqual(sess.snapshot()["score"], 444)

    def test_us4_05_no_tip_when_patience_below_half(self):
        """AS5: Phục vụ khi kiên nhẫn < 50% (< 1800) -> không boa, uy tín không đổi."""
        t = _tuning()
        sc = {
            "player": {"pos": [9, 2]},
            "hand": {"dish": "ca_loc_nuong_trui", "customer_id": "C1"},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish": "ca_loc_nuong_trui",
                "state": "waiting", "patience_ticks": 1799, "reserved": {},
            }],
        }
        sess = Session("quan", t, sc, seed=1)
        evs = _step_n(sess, [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}], 1)
        self.assertEqual(evs[0]["name"], "served")
        self.assertEqual(evs[0]["data"]["tip"], 0)
        evs_eat = _step_n(sess, [], 600)
        self.assertEqual(evs_eat[0]["data"], {"customer_id": "C1", "amount": 60, "tip": 0})
        self.assertEqual(sess.sim.reputation, 3.0)

    def test_us4_06_serve_at_zero_patience_is_valid(self):
        """AS6: Phục vụ khi kiên nhẫn vừa chạm 0 vẫn hợp lệ và không boa."""
        t = _tuning()
        sc = {
            "player": {"pos": [9, 2]},
            "hand": {"dish": "goi_bong_sung", "customer_id": "C1"},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish": "goi_bong_sung",
                "state": "waiting", "patience_ticks": 0, "reserved": {},
            }],
        }
        sess = Session("quan", t, sc, seed=1)
        evs = _step_n(sess, [{"tick": 0, "interact": True}], 1)
        self.assertEqual(_ev_names(evs), ["served"])
        self.assertEqual(sess.sim.customers[0]["state"], "eating")

    def test_us4_07_tie_break_stove_before_table_and_no_fallback(self):
        """AS7: Cách đều bếp và bàn -> chọn bếp trước; nếu bếp không dùng được thì KHÔNG fallback sang bàn."""
        t = _tuning()
        # B1 ở [5, 5], T1 ở [7, 5], player ở [6, 5] -> cách đều 1.0m (<= 1.5m).
        # B1 đang nấu (không dùng được), tay đang cầm đúng món của C1 ở T1 -> phải KHÔNG phục vụ T1!
        sc = {
            "player": {"pos": [6, 5]},
            "stoves": [{"id": "B1", "pos": [5, 5], "state": "cooking", "dish": "ca_loc_nuong_trui", "cook_ticks_left": 100}],
            "tables": [{"id": "T1", "pos": [7, 5]}],
            "hand": {"dish": "goi_bong_sung", "customer_id": "C1"},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish": "goi_bong_sung",
                "state": "waiting", "patience_ticks": 3000, "reserved": {},
            }],
        }
        sess = Session("quan", t, sc, seed=1)
        evs = _step_n(sess, [{"tick": 0, "interact": True}], 1)
        self.assertEqual(evs, [])
        self.assertIsNotNone(sess.sim.hand)
        self.assertEqual(sess.sim.customers[0]["state"], "waiting")

    def test_us4_08_close_shift_pays_eating_immediately(self):
        """AS8: Hết ca -> khách đang ăn trả tiền ngay trước quan_end."""
        t = _tuning()
        sc = {
            "time_left_ticks": 1,
            "customers": [{
                "id": "C1", "table_id": "T1", "dish": "ca_loc_nuong_trui",
                "state": "eating", "eat_ticks": 500, "tip": 12, "reserved": {},
            }],
        }
        sess = Session("quan", t, sc, seed=1)
        evs = _step_n(sess, [], 1)
        self.assertEqual(_ev_names(evs), ["paid", "quan_end"])
        self.assertEqual(evs[0]["data"], {"customer_id": "C1", "amount": 72, "tip": 12})
        self.assertEqual(evs[1]["data"]["money"], 72)
        self.assertEqual(evs[1]["data"]["reputation"], 3.2)

    def test_discard_dish_for_departed_customer(self):
        """FR-034: Khi khách rời đi, món của khách đó trên bếp hoặc trên tay bị bỏ."""
        t = _tuning()
        sc = {
            "stoves": [{"id": "B1", "state": "cooking", "dish": "ca_loc_nuong_trui", "customer_id": "C1", "cook_ticks_left": 50}],
            "hand": {"dish": "goi_bong_sung", "customer_id": "C2"},
        }
        sess = Session("quan", t, sc, seed=1)
        quan_kitchen.discard_dish_for(sess.sim, "C1")
        self.assertEqual(sess.sim.stoves[0]["state"], "idle")
        self.assertIsNone(sess.sim.stoves[0]["dish"])
        self.assertIsNotNone(sess.sim.hand)
        quan_kitchen.discard_dish_for(sess.sim, "C2")
        self.assertIsNone(sess.sim.hand)

    def test_ledger_reputation_clamp_and_float_precision(self):
        """Uy tín kẹp [0, 5] và không bị lỗi float 4.9999999 khi cộng 0.2 nhiều lần."""
        t = _tuning()
        sess = Session("quan", t, {}, seed=1)
        for _ in range(10):
            ledger.add_reputation(sess.sim, 0.2)
        self.assertEqual(sess.sim.reputation, 5.0)
        self.assertEqual(math.floor(sess.sim.reputation), 5)
        ledger.add_reputation(sess.sim, -10.0)
        self.assertEqual(sess.sim.reputation, 0.0)

    def test_snapshot_hides_internal_underscore_fields(self):
        """Trường nội bộ _cooking không được lộ ra snapshot."""
        t = _tuning()
        sc = {
            "customers": [{
                "id": "C1", "table_id": "T1", "dish": "ca_loc_nuong_trui",
                "state": "waiting", "patience_ticks": 3000, "reserved": {},
            }],
        }
        sess = Session("quan", t, sc, seed=1)
        snap_c = sess.snapshot()["customers"][0]
        self.assertFalse(any(k.startswith("_") for k in snap_c))

    def test_validate_scenario_rejects_invalid_kitchen_fixtures(self):
        """FR-035: Fixture bếp/tay/khách ăn sai mâu thuẫn -> raise BadInput (mã thoát 2)."""
        t = _tuning()
        bad_blocks = [
            {"hand": {"dish": "mon_khong_ton_tai"}},
            {"stoves": [{"id": "B1", "state": "cooking", "dish": "ca_loc_nuong_trui", "cook_ticks_left": 0}]},
            {"stoves": [{"id": "B1", "state": "idle", "dish": "ca_loc_nuong_trui"}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish": "ca_loc_nuong_trui", "state": "eating"}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish": "ca_loc_nuong_trui", "state": "unknown"}]},
        ]
        for blk in bad_blocks:
            with self.assertRaises(BadInput, msg=str(blk)):
                quan_kitchen.validate_scenario(blk, t)

    def test_pick_nearest_natural_id_tiebreak(self):
        """pick.nearest phá hòa theo (dist, rank, id_key): B2 trước B10."""
        cands = [(0, {"id": "B10", "pos": [1, 0]}), (0, {"id": "B2", "pos": [1, 0]})]
        res = pick.nearest([0, 0], cands, 1.5)
        self.assertEqual(res[1]["id"], "B2")


if __name__ == "__main__":
    unittest.main()
