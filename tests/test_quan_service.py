import unittest

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.runner import Session


class QuanService(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_reserved_order_is_cooked_then_picked_and_served(self):
        scenario = {
            "player": {"pos": [2, 8]},
            "stock": {"bong_sung": 2},
            "random_customers": False,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_tick": 1}],
        }
        session = Session("quan", self.tuning, scenario, 1)
        controls = LiveInputs()
        started = session.step(controls.advance())
        self.assertEqual([r["name"] for r in started], ["cook_started"])
        self.assertEqual(started[0]["data"]["items"], {"bong_sung": 2})
        self.assertEqual(session.sim.stock["bong_sung"], 0)
        self.assertEqual(session.sim.customers[0]["order_status"], "assigned")

        ready_events = []
        for _ in range(4 * 60):
            ready_events.extend(session.step(controls.advance()))
        self.assertIn("dish_ready", [r["name"] for r in ready_events])
        controls.set(interact=True)
        picked = session.step(controls.advance())
        self.assertEqual([r["name"] for r in picked], ["dish_picked"])
        self.assertEqual(session.sim.hand["order_id"], "C1")

        controls.set(interact=False)
        controls.advance()
        session.sim.pos = list(self.tuning["quan"]["tables"][0]["pos"])
        controls.set(interact=True)
        served = session.step(controls.advance())
        self.assertEqual([r["name"] for r in served], ["served"])
        self.assertEqual(served[0]["data"]["tip"], 8)
        self.assertEqual(session.sim.customers[0]["order_status"], "served")

    def test_finished_meal_is_paid_after_eating_ticks(self):
        scenario = {
            "random_customers": False,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                            "order_status": "served", "eat_ticks_left": 1, "base_price": 40, "tip": 8}],
        }
        session = Session("quan", self.tuning, scenario, 1)
        rows = session.step(LiveInputs().advance())
        self.assertEqual([r["name"] for r in rows], ["paid"])
        self.assertEqual(rows[0]["data"], {"order_id": "C1", "table_id": "T1", "base_price": 40,
                                            "tip": 8, "amount": 48, "reason": "finished_eating"})
        self.assertEqual(session.sim.earned, 48)
        self.assertEqual(session.sim.reputation, 3.2)

    def test_closing_collects_eating_order_without_waiting_for_timer(self):
        scenario = {
            "time_left_ticks": 1,
            "random_customers": False,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                            "order_status": "served", "eat_ticks_left": 5, "base_price": 40, "tip": 8}],
        }
        session = Session("quan", self.tuning, scenario, 1)
        rows = session.step(LiveInputs().advance())
        self.assertEqual([r["name"] for r in rows], ["paid", "quan_end"])
        self.assertEqual(rows[0]["data"]["reason"], "closing")
        self.assertEqual(session.sim.earned, 48)
        self.assertEqual(session.sim.reputation, 3.2)
        self.assertTrue(session.done)


if __name__ == "__main__":
    unittest.main()
