import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
from helpers import counts, items


class QuanLat3(unittest.TestCase):
    def make_sim(self, stock=None, scenario=None, seed=9):
        tuning = load_contract()["tuning"]
        tuning["quan"]["first_customer_tick"] = 1
        tuning["quan"]["customer_interval_s"] = 1 / 60
        return QuanSim(tuning, {"stock": stock or [], **(scenario or {})}, Streams(seed), IdAllocator())

    @staticmethod
    def idle_input():
        return InputState((0.0, 0.0), {}, set())

    def test_arrival_reserves_recipe_and_uses_seeded_id(self):
        sim = self.make_sim(items("ca_loc", "bong_sung", "bong_sung"))
        events = sim.step(self.idle_input())
        self.assertEqual(events[0][0], "customer_arrived")
        self.assertEqual(sim.customers[0]["id"], "C1")
        customer = sim.customers[0]
        self.assertEqual(customer["table_id"], "T1")
        # v1.2: reserved là mảng id cá thể — đúng công thức về số lượng theo loại
        by_id = {it["id"]: it for it in sim.stock}
        self.assertEqual(counts([by_id[x] for x in customer["reserved"]]), sim.menu[customer["dish_id"]]["recipe"])
        expected = {"ca_loc": 1, "bong_sung": 2}
        for kind, qty in sim.menu[customer["dish_id"]]["recipe"].items():
            expected[kind] -= qty
        # _available() (bản tích hợp với lát 4) bỏ khóa bằng 0; thiếu khóa nghĩa là 0.
        self.assertEqual(sim._available(), {k: v for k, v in expected.items() if v > 0})
        self.assertEqual(customer["patience_ticks_left"], sim.t["patience_s"] * 60)

    def test_no_dish_does_not_create_customer(self):
        sim = self.make_sim()
        events = sim.step(self.idle_input())
        self.assertEqual(events, [("no_dish", {})])
        self.assertEqual(sim.customers, [])

    def test_patience_expiry_releases_reservation_and_clamps_reputation(self):
        customer = {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                    "state": "waiting", "order_status": "reserved", "reserved": ["I1", "I2"],  # v1.2: id cá thể
                    "patience_ticks_left": 1}
        sim = self.make_sim(items("bong_sung", "bong_sung"), {"customers": [customer], "random_customers": False,
                                                "reputation": 0.1})
        events = sim.step(self.idle_input())
        self.assertEqual(events[0], ("customer_left", {"order_id": "C1", "table_id": "T1",
                                                         "reason": "patience", "reputation": 0}))
        self.assertEqual(sim.customers, [])
        self.assertEqual(counts(sim.stock), {"bong_sung": 2})  # v1.2: nhả giữ chỗ, cá thể vẫn trong kho
        self.assertEqual(sim._available(), {"bong_sung": 2})

    def test_spoiled_reserved_item_is_released_and_rereserved_once_by_id(self):
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 30},
            {"id": "I2", "kind": "ca_loc", "fresh": 90},
            {"id": "I3", "kind": "ca_loc", "fresh": 70},
        ]
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "state": "waiting", "order_status": "reserved", "reserved": ["I1"],
                    "patience_ticks_left": 100}
        sim = self.make_sim(stock, {"customers": [customer], "random_customers": False})

        first_events = sim.step(self.idle_input())
        self.assertEqual([e for e in first_events if e[0] == "spoiled"], [
            ("spoiled", {"item_id": "I1", "kind": "ca_loc", "location": "stock"}),
        ])
        self.assertEqual(sim.customers[0]["reserved"], ["I2"])
        self.assertEqual(sim.customers[0]["order_status"], "reserved")

        second_events = sim.step(self.idle_input())
        self.assertEqual([e for e in second_events if e[0] == "spoiled"], [])
        self.assertEqual(sim.customers[0]["reserved"], ["I2"])
        self.assertEqual(sim.customers[0]["order_status"], "reserved")


if __name__ == "__main__":
    unittest.main()
