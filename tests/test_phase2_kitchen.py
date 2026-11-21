"""Kiểm tra phần Bếp (Người A — `chonoi/sim/kitchen.py`) theo chuẩn Phase 2 (TICKET-02):
- 2 bếp B1 [2,8], B2 [5,8] nấu song song và chín theo thứ tự id.
- 6 món & 6 nguyên liệu chuẩn Phase 2 (gồm `lau_mam`, `canh_chua_ca_loc`, `ca_keo_nuong`).
- Mở rộng Cháy món (`burn_s: 20` -> 1200 ticks): đúng 1200 vẫn bưng được, > 1200 phát `dish_burnt` và thử giữ lại nguyên liệu.
"""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session


def _inp(move=(0.0, 0.0), interact=False):
    edges = {"interact"} if interact else set()
    return InputState(move, set(edges), edges)


def _p2_tuning(burn_s=None):
    t = copy.deepcopy(load_contract()["tuning"])
    t["quan"]["stoves"] = [{"id": "B1", "pos": [2, 8]}, {"id": "B2", "pos": [5, 8]}]
    t["quan"]["tables"] = [
        {"id": "T1", "pos": [9, 2]},
        {"id": "T2", "pos": [13, 2]},
        {"id": "T3", "pos": [9, 6]},
        {"id": "T4", "pos": [13, 6]},
    ]
    t["quan"]["burn_s"] = burn_s
    t["menu"].update({
        "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
        "ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
        "lau_mam": {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, "cook_s": 12, "price": 200},
    })
    return t


class Phase2KitchenTest(unittest.TestCase):
    def test_two_stoves_parallel_and_new_dishes(self):
        tuning = _p2_tuning()
        scen = {
            "player": {"pos": [2, 8]},
            "stock": {"ca_linh": 2, "ca_keo": 3, "keo_neo": 1, "bong_dien_dien": 1},
            "random_customers": False,
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "lau_mam", "order_tick": 10},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_keo_nuong", "order_tick": 20},
            ],
        }
        sess = Session("quan", tuning, scen, 1)
        # B1 nhận C1 (lau_mam, 12s = 720 ticks)
        evs1 = sess.step(_inp(interact=True))
        self.assertEqual(evs1[0]["name"], "cook_started")
        self.assertEqual(evs1[0]["data"]["stove_id"], "B1")
        self.assertEqual(evs1[0]["data"]["items"], ["bong_dien_dien", "ca_keo", "ca_linh", "ca_linh", "keo_neo"])
        self.assertEqual(evs1[0]["data"]["base_price"], 200)

        # Di chuyển sang B2 [5, 8] nhận C2 (ca_keo_nuong, 6s = 360 ticks)
        sess.sim.pos = [5.0, 8.0]
        evs2 = sess.step(_inp(interact=True))
        self.assertEqual(evs2[0]["name"], "cook_started")
        self.assertEqual(evs2[0]["data"]["stove_id"], "B2")
        self.assertEqual(evs2[0]["data"]["items"], ["ca_keo", "ca_keo"])
        self.assertEqual(sess.sim.stock, {})

        # Sau 359 tick nữa -> B2 chín trước
        for _ in range(359):
            sess.step(_inp())
        evs_b2 = sess.step(_inp())
        self.assertEqual([(e["name"], e["data"]["stove_id"]) for e in evs_b2], [("dish_ready", "B2")])

    def test_burn_boundary_1200_ok_and_1201_burns(self):
        tuning = _p2_tuning(burn_s=20)
        # Đúng 1200 tick vẫn bưng được
        scen_ok = {
            "player": {"pos": [2, 8]},
            "stock": {},
            "stoves": [{"id": "B1", "state": "ready", "ready_ticks": 1199,
                        "dish": {"order_id": "C1", "dish_id": "ca_keo_nuong", "base_price": 70}}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_keo_nuong",
                           "order_status": "assigned", "reserved": {}}],
            "random_customers": False,
        }
        sess_ok = Session("quan", tuning, scen_ok, 1)
        evs_ok = sess_ok.step(_inp(interact=True))
        self.assertEqual([e["name"] for e in evs_ok], ["dish_picked"])
        self.assertEqual(sess_ok.sim.hand["dish_id"], "ca_keo_nuong")

        # Quá 1200 (1201) -> dish_burnt, đủ kho -> reserved, thiếu kho -> unfulfillable
        for stock, expected_status in [({"ca_keo": 2}, "reserved"), ({"ca_keo": 1}, "unfulfillable")]:
            scen_burn = {
                "player": {"pos": [2, 8]},
                "stock": stock,
                "stoves": [{"id": "B1", "state": "ready", "ready_ticks": 1200,
                            "dish": {"order_id": "C1", "dish_id": "ca_keo_nuong", "base_price": 70}}],
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_keo_nuong",
                               "order_status": "assigned", "reserved": {}}],
                "random_customers": False,
            }
            sess_b = Session("quan", tuning, scen_burn, 1)
            evs_b = sess_b.step(_inp(interact=False))
            self.assertEqual([e["name"] for e in evs_b], ["dish_burnt"])
            self.assertEqual(evs_b[0]["data"]["order_status"], expected_status)
            self.assertEqual(sess_b.sim.stoves[0]["state"], "idle")
            self.assertIsNone(sess_b.sim.hand)
            self.assertEqual(sess_b.sim.customers[0]["order_status"], expected_status)


if __name__ == "__main__":
    unittest.main()
