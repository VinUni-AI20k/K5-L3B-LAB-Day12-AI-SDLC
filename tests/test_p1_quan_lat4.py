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

    def test_interact_cook_started_and_pick(self):
        """Đứng cạnh bếp idle bấm interact -> cook_started; khi ready bấm interact -> dish_picked."""
        stove_pos = self.tuning["quan"]["stoves"][0]["pos"]
        sc = {
            "player": {"pos": list(stove_pos)},
            "stock": {"ca_loc": 2},
            "customers": [{"id": "C1", "table_id": "T1", "order": "ca_loc_nuong_trui"}]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        # Bấm interact -> bắt đầu nấu
        li.set(interact=True)
        evs = s.step(li.advance())
        cook_ev = [e for e in evs if e["name"] == "cook_started"]
        self.assertEqual(len(cook_ev), 1)
        self.assertEqual(cook_ev[0]["data"], {"stove_id": "B1", "dish": "ca_loc_nuong_trui"})
        self.assertEqual(s.sim.stoves[0]["state"], "cooking")
        # Nguyên liệu trong kho giảm 1
        self.assertEqual(s.sim.stock.get("ca_loc", 0), 1)

        # Thả nút tương tác rồi chờ bếp chín
        li.set(interact=False)
        s.sim.stoves[0]["cook_ticks_left"] = 1
        evs = s.step(li.advance())  # Bếp chín -> dish_ready
        self.assertTrue(any(e["name"] == "dish_ready" for e in evs))
        self.assertEqual(s.sim.stoves[0]["state"], "ready")

        # Bấm interact lần 2 -> nhấc món lên tay
        li.set(interact=True)
        evs = s.step(li.advance())
        pick_ev = [e for e in evs if e["name"] == "dish_picked"]
        self.assertEqual(len(pick_ev), 1)
        self.assertEqual(pick_ev[0]["data"], {"stove_id": "B1", "dish": "ca_loc_nuong_trui"})
        self.assertEqual(s.sim.hand, "ca_loc_nuong_trui")
        self.assertEqual(s.sim.stoves[0]["state"], "idle")

    def test_serve_dish_to_table(self):
        """Cầm món đứng cạnh bàn khách -> served, khách chuyển sang eating."""
        table_pos = self.tuning["quan"]["tables"][0]["pos"]
        sc = {
            "player": {"pos": list(table_pos)},
            "hand": "ca_loc_nuong_trui",
            "customers": [{"id": "C1", "table_id": "T1", "order": "ca_loc_nuong_trui", "state": "waiting"}]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        # Bấm interact -> phục vụ món
        li.set(interact=True)
        evs = s.step(li.advance())
        serve_ev = [e for e in evs if e["name"] == "served"]
        self.assertEqual(len(serve_ev), 1)
        self.assertEqual(serve_ev[0]["data"], {"customer_id": "C1", "table_id": "T1", "dish": "ca_loc_nuong_trui"})
        self.assertIsNone(s.sim.hand)
        self.assertEqual(s.sim.customers[0]["state"], "eating")

    def test_interact_priority_stove_before_table(self):
        """Nếu bếp và bàn cùng khoảng cách, ưu tiên bếp trước bàn."""
        sc = {
            "player": {"pos": [5.0, 5.0]},
            "stoves": [{"id": "B1", "pos": [5.0, 6.0], "state": "ready", "dish": "ca_loc_nuong_trui"}],
            "tables": [{"id": "T1", "pos": [5.0, 4.0]}],  # cùng khoảng cách = 1.0
            "stock": {}
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        li.set(interact=True)
        evs = s.step(li.advance())
        # Ưu tiên bếp B1 -> nhấc đĩa
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["name"], "dish_picked")
        self.assertEqual(s.sim.hand, "ca_loc_nuong_trui")


if __name__ == "__main__":
    unittest.main()
