"""Unit test cho sim/quan Lát 4 (Trần Trung Kiên - ttkien0710)."""

import unittest

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.runner import Session


class QuanLat4Tests(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_stove_cooks_to_ready(self):
        """Bếp đang nấu sau cook_ticks_left tick sẽ chuyển sang ready và bắn dish_ready."""
        sc = {
            "stoves": [{"id": "B1", "state": "cooking", "dish": "ca_loc_nuong_trui", "cook_ticks_left": 3}]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        # Tick 1: cook_ticks_left: 3 -> 2
        evs = s.step(li.advance())
        self.assertEqual(evs, [])
        self.assertEqual(s.sim.stoves[0]["state"], "cooking")
        self.assertEqual(s.sim.stoves[0]["cook_ticks_left"], 2)

        # Tick 2: cook_ticks_left: 2 -> 1
        evs = s.step(li.advance())
        self.assertEqual(evs, [])

        # Tick 3: cook_ticks_left: 1 -> 0 => dish_ready
        evs = s.step(li.advance())
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["name"], "dish_ready")
        self.assertEqual(evs[0]["data"], {"stove_id": "B1", "dish": "ca_loc_nuong_trui"})
        self.assertEqual(s.sim.stoves[0]["state"], "ready")
        self.assertEqual(s.sim.stoves[0]["ready_ticks"], 0)

        # Tick 4: ready_ticks tăng dần
        s.step(li.advance())
        self.assertEqual(s.sim.stoves[0]["ready_ticks"], 1)


if __name__ == "__main__":
    unittest.main()
