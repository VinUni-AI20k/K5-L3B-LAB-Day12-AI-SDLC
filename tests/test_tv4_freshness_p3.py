"""Kiểm chứng TV4. Ca vòng ngày dùng hai đầu gather/quan khi đã ghép schema cá thể."""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.quan import QuanSim


TUNING = load_contract()["tuning"]


class FreshKitchen(unittest.TestCase):
    def test_consume_only_reserved_items_and_keep_the_price_through_payment(self):
        tuning = dict(TUNING, freshness={"initial": 100})
        sim = QuanSim(tuning, {}, Streams(1), IdAllocator())
        items = [
            {"id": "I10", "kind": "ca_linh", "fresh": 60},
            {"id": "I4", "kind": "ca_linh", "fresh": 100},
            {"id": "I8", "kind": "bong_dien_dien", "fresh": 100},
            {"id": "I2", "kind": "ca_linh", "fresh": 80},
            {"id": "I3", "kind": "ca_linh", "fresh": 40},
        ]
        sim.stock = list(items)
        customer = {"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien",
                    "order_status": "reserved", "order_tick": 0, "patience_ticks_left": sim.patience,
                    "reserved": ["I10", "I8", "I3", "I2"]}
        sim.customers = [customer]
        stove = sim.stoves[0]
        events = []
        sim._start_cooking(stove, events)
        started = events[0][1]
        self.assertEqual([item["id"] for item in started["items"]], ["I8", "I2", "I3", "I10"])
        self.assertEqual(started["base_price"], 84)
        self.assertEqual((sim.stock, customer["reserved"]), ([items[1]], []))
        # Giá chốt nằm trên món, kho còn lại có thể đổi trong lúc nấu/ăn.
        sim.stock[0]["fresh"] = 29
        sim.hand = stove["dish"]
        sim._serve(customer, events)
        sim._pay(customer, "finished_eating", events)
        self.assertEqual([(name, data.get("base_price")) for name, data in events],
                         [("cook_started", 84), ("served", 84), ("paid", 84)])
        self.assertEqual((events[-1][1]["tip"], sim.money, sim.earned), (16, 100, 100))

    def test_floor_with_average_just_below_boundary(self):
        tuning = dict(TUNING, freshness={"initial": 100})
        sim = QuanSim(tuning, {}, Streams(1), IdAllocator())
        for first, expected in ((79.99999999999999, 31), (80, 32)):
            with self.subTest(first=first):
                sim.stock = [{"id": "I1", "kind": "bong_sung", "fresh": first},
                             {"id": "I2", "kind": "bong_sung", "fresh": 80}]
                _, price = sim._consume_reserved_units(["I1", "I2"], 40)
                self.assertEqual(price, expected)


@unittest.skipUnless("freshness" in TUNING, "Cần ghép giỏ TV2, kho quán TV3 và tuning freshness")
class FreshDay(unittest.TestCase):
    def test_day_preserves_stock_and_reissues_ids_after_consumption(self):
        scenario = {
            "gather": {"random_fish": False, "monsters": [], "time_left_ticks": 1,
                       "hold": [{"id": "I10", "kind": "ca_loc", "fresh": 80},
                                {"id": "I2", "kind": "keo_neo", "fresh": 25}]},
            "quan": {"random_customers": False, "time_left_ticks": 1, "player": {"pos": [2, 8]},
                     "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                    "reserved": ["I10"]}]},
        }
        frames = InputPlayer([{"tick": 1, "interact": True}, {"tick": 2, "pause": True},
                              {"tick": 3, "pause": False}, {"tick": 4, "pause": True},
                              {"tick": 5, "shop_done": True}, {"tick": 6, "interact": False},
                              {"tick": 7, "interact": True}], buttons=("pause", "interact", "shop_done"))
        session = Session("day", TUNING, scenario, 1, days=2)
        self.assertEqual([u["id"] for u in session.snapshot()["hold"]], ["I10", "I2"])
        rows = session.step(frames.advance(0))
        stock = session.snapshot()["stock"]
        self.assertEqual(stock, rows[0]["data"]["inventory"]["items"])
        self.assertEqual(session.phase_tick, 0)
        rows = session.step(frames.advance(1))
        self.assertEqual(rows[0]["name"], "cook_started")
        self.assertEqual(rows[0]["data"]["items"][0]["id"], "I10")
        self.assertEqual(rows[0]["data"]["base_price"], 47)
        shop = session.snapshot()["stock"]
        self.assertEqual([u["id"] for u in shop], ["I2"])
        for tick in range(2, 5):
            session.step(frames.advance(tick))
            self.assertEqual(session.snapshot()["stock"], shop)
        session.step(frames.advance(5))
        self.assertEqual([(u["id"], u["fresh"]) for u in session.snapshot()["hold"]], [("I11", 80), ("I12", 25)])
        session.step(frames.advance(6))
        self.assertEqual(session.snapshot()["customers"][0]["reserved"], ["I11"])
        rows = session.step(frames.advance(7))
        self.assertEqual(rows[0]["data"]["items"][0]["id"], "I11")
