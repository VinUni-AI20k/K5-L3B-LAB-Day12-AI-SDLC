import unittest

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.live import LiveGame
from chonoi.runner import Session


class QuanLeftovers(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_live_only_and_thirty_game_minutes(self):
        live = LiveGame("quan", self.tuning, {}, 42)
        headless = Session("quan", self.tuning, {}, 42)
        # ca 180 s thật = 3 giờ game -> 30 phút game = 30 s = 1800 tick
        cfg = self.tuning["live"]
        seconds_per_game_minute = self.tuning["quan"]["duration_s"] / (cfg["quan_shift_game_hours"] * 60)
        expected = round(cfg["leftover_lifetime_game_minutes"] * seconds_per_game_minute * self.tuning["tick_hz"])
        self.assertEqual(live.session.sim.leftover_lifetime_ticks, expected)
        self.assertEqual(expected, 1800)  # với contract hiện tại
        self.assertLess(expected, self.tuning["quan"]["duration_s"] * self.tuning["tick_hz"])
        self.assertIsNone(headless.sim.leftover_lifetime_ticks)

    def test_return_and_reuse_without_consuming_stock_again(self):
        sim = LiveGame("quan", self.tuning, {}, 42).session.sim
        stove = sim.stoves[0]
        stove.update(state="ready", dish="ca_loc_nuong_trui", order_id="O9")
        sim._stove_interact(stove, [])
        original_deadline = sim.hand["expires_at_tick"]
        sim.tick = self.tuning["quan"]["first_customer_tick"]
        sim._stove_interact(stove, [])
        self.assertIsNone(sim.hand)
        self.assertEqual(sim.stored_dishes[0]["expires_at_tick"], original_deadline)
        sim._spawn_customer([])
        customer, = sim.customers
        self.assertEqual(customer["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(customer["reserved"], {})
        sim._stove_interact(stove, [])
        self.assertEqual(sim.hand["order_id"], customer["order_id"])
        self.assertEqual(sim.hand["expires_at_tick"], original_deadline)
        sim._table_interact(sim.tables[0], [])
        self.assertEqual(customer["state"], "eating")
        self.assertEqual(sim.stock, {})

    def test_unclaimed_dish_expires_at_original_deadline(self):
        sim = LiveGame("quan", self.tuning, {"random_customers": False}, 42).session.sim
        stove = sim.stoves[0]
        stove.update(state="ready", dish="ca_loc_nuong_trui", order_id="O9")
        sim._stove_interact(stove, [])
        deadline = sim.hand["expires_at_tick"]
        sim.tick = deadline - 2
        sim._stove_interact(stove, [])
        idle = LiveInputs().advance()
        self.assertEqual(sim.step(idle), [])
        self.assertEqual(len(sim.stored_dishes), 1)
        event, = sim.step(idle)
        self.assertEqual(event, ("dish_discarded", {"dish_id": "ca_loc_nuong_trui"}))
        self.assertEqual(sim.stored_dishes, [])
