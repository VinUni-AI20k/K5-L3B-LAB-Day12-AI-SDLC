"""Unit tests cho Phase 3 (ngominhcuong): chốt giá theo độ tươi, tip trên giá chốt, và ID xuyên ngày."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import BUTTONS_V11, InputPlayer
from chonoi.runner import Session


def _tuning():
    return copy.deepcopy(load_contract()["tuning"])


class QuanPriceDayIdTests(unittest.TestCase):
    def test_cook_started_locks_floor_freshness_price_and_tip(self):
        t = _tuning()
        # lau_ca_linh_dien_dien giá niêm yết 120: dùng 3 ca_linh (fresh 80, 70, 75) + 1 bong_dien_dien (fresh 75)
        # avg_fresh = 300 / 4 = 75.0 -> base_price = floor(120 * 75 / 100) = 90; tip = floor(90 * 0.2) = 18
        sc = {
            "player": {"pos": [2, 8]},
            "stock": [
                {"id": "I10", "kind": "ca_linh", "fresh": 80},
                {"id": "I2", "kind": "ca_linh", "fresh": 70},
                {"id": "I3", "kind": "ca_linh", "fresh": 75},
                {"id": "I1", "kind": "bong_dien_dien", "fresh": 75},
            ],
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien",
                "order_status": "reserved", "reserved": ["I1", "I10", "I2", "I3"],
            }],
            "random_customers": False,
        }
        sess = Session("quan", t, sc, seed=1)
        ip = InputPlayer([{"tick": 0, "interact": True}, {"tick": 1, "interact": False}], buttons=BUTTONS_V11)
        evs = []
        for k in range(605):
            evs.extend(sess.step(ip.advance(k)))

        cs = next(e for e in evs if e["name"] == "cook_started")
        self.assertEqual(cs["data"]["base_price"], 90)
        # Sắp theo kind rồi id: bong_dien_dien (I1) trước ca_linh (I2, I3, I10)
        self.assertEqual([x["id"] for x in cs["data"]["items"]], ["I1", "I2", "I3", "I10"])
        self.assertEqual(sess.snapshot()["stock"], [])

        # Bưng từ B1 -> phục vụ T1 bằng scenario tiếp nối
        sc2 = {
            "player": {"pos": [9, 2]},
            "stock": [],
            "hand": {"order_id": "C1", "dish_id": "lau_ca_linh_dien_dien", "base_price": 90},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien",
                "order_status": "assigned",
            }],
            "random_customers": False,
        }
        sess2 = Session("quan", t, sc2, seed=1)
        ip2 = InputPlayer([{"tick": 0, "interact": True}], buttons=BUTTONS_V11)
        evs2 = []
        for k in range(601):
            evs2.extend(sess2.step(ip2.advance(k)))
        served = next(e for e in evs2 if e["name"] == "served")
        self.assertEqual(served["data"]["base_price"], 90)
        self.assertEqual(served["data"]["tip"], 18)
        paid = next(e for e in evs2 if e["name"] == "paid")
        self.assertEqual(paid["data"]["amount"], 108)

    def test_day_preserves_day1_ids_and_allocates_new_ids_on_day2(self):
        t = _tuning()
        sc = {
            "gather": {
                "fish": [], "random_fish": False,
                "hold": [
                    {"id": "I1", "kind": "ca_loc", "fresh": 90},
                    {"id": "I2", "kind": "bong_sung", "fresh": 80},
                ],
                "time_left_ticks": 1,
            },
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        sess = Session("day", t, sc, seed=1, days=2)
        d1_sc = sess.sim._prepare_gather_scenario()
        # Ngày 1 giữ nguyên id I1, I2 từ mẫu
        self.assertEqual([x["id"] for x in d1_sc["hold"]], ["I1", "I2"])
        self.assertEqual(sess.sim.item_ids.new("I"), "I3")

        # Qua Ngày 2 tự cấp id mới I3, I4 cho hold mẫu theo thứ tự mảng
        sess2 = Session("day", t, sc, seed=1, days=2)
        sess2.sim.day = 2
        d2_sc = sess2.sim._prepare_gather_scenario()
        self.assertEqual([x["id"] for x in d2_sc["hold"]], ["I3", "I4"])
        self.assertEqual([x["kind"] for x in d2_sc["hold"]], ["ca_loc", "bong_sung"])
        self.assertEqual([x["fresh"] for x in d2_sc["hold"]], [90, 80])
        self.assertEqual(sess2.sim.item_ids.new("I"), "I5")


if __name__ == "__main__":
    unittest.main()
