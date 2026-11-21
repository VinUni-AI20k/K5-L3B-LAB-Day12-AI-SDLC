"""P3-05: giao cá thể qua các pha bằng giao diện P3-04 dự kiến."""

import unittest
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.freshness import Freshness
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.day import DaySim
from chonoi.sim.shop import ShopSim


T = load_contract()["tuning"]
F = Freshness(T)


class QuanFixture:
    """Đầu nhận v1.2 cho test giao diện, không mô phỏng luật phục vụ của P3-04."""

    def __init__(self, tuning, scenario, streams, ids, *, inventory, contract_version,
                 money, earned, reputation, **kwargs):
        if contract_version != "1.2" or not isinstance(inventory, list):
            raise AssertionError("Quán phải nhận mảng cá thể v1.2")
        self.stock = inventory
        self.money, self.earned, self.reputation = money, earned, reputation
        self.time_left_ticks, self.done = 1, False

    def snapshot(self):
        return {"stock": self.stock}

    def step(self, inp):
        self.time_left_ticks, self.done = 0, True
        return [("quan_end", {"reason": "time"})]


class DayFreshHandoffTests(unittest.TestCase):
    @patch("chonoi.sim.day.QuanSim", QuanFixture)
    def test_same_tick_handoff_and_new_ids_on_next_day(self):
        src = {"id": "I8", "kind": "bong_sung", "fresh": F.to_points(F.max_units)}
        sim = DaySim(T, {"gather": {"hold": [src], "time_left_ticks": 1, "random_fish": False, "monsters": []}},
                     Streams(1), 2, contract_version="1.2")
        inp = InputPlayer([]).advance(0)
        events = sim.step(inp)
        amount = F.to_points(F.max_units - F.decay("gather"))
        expected = [{**src, "fresh": amount}]
        self.assertEqual(events, [
            ("gather_end", {"reason": "time", "inventory": {"items": expected}}, {"phase": "gather", "day": 1}),
            ("phase_start", {}, {"phase": "quan", "day": 1}),
        ])
        self.assertEqual((sim.sim_tick, sim.phase_tick), (1, 0))
        self.assertEqual(sim.snapshot()["stock"], expected)
        self.assertEqual(sim.current.time_left_ticks, 1)
        sim.step(inp)
        self.assertEqual(sim.phase, "shop")
        self.assertEqual(sim.snapshot()["stock"], expected)
        sim.step(inp)
        self.assertEqual(sim.snapshot()["stock"], expected)
        done = InputPlayer([{"tick": 0, "shop_done": True}]).advance(0)
        sim.step(done)
        self.assertEqual((sim.day, sim.phase, sim.phase_tick), (2, "gather", 0))
        self.assertEqual(sim.snapshot()["hold"], [{**src, "id": "I9"}])
        self.assertEqual(src["id"], "I8")

    def test_shop_copies_stock_and_never_ages_individuals(self):
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": F.to_points(F.spoil_units)}]
        shop = ShopSim(T, stock=stock, money=0, earned=0, reputation=3)
        before = shop.snapshot()["stock"]
        for _ in range(T["shop"]["max_ticks"]):
            shop.step()
        self.assertEqual(shop.snapshot()["stock"], before)
        shop.snapshot()["stock"][0]["fresh"] = 0
        self.assertEqual(shop.snapshot()["stock"], stock)
        empty = ShopSim(T, stock=[], money=0, earned=0, reputation=3)
        self.assertEqual(empty.snapshot()["stock"], [])
