"""P2-05 coverage for the v1.1 standalone Quán simulation."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


TUNING = load_contract()["tuning"]
Q = TUNING["quan"]
HZ = TUNING["tick_hz"]
FIRST = Q["first_customer_tick"]
INTERVAL = round(Q["customer_interval_s"] * HZ)


def create_sim(scenario=None, inventory=None, tuning=None, **kwargs):
    return QuanSim(tuning or TUNING, scenario or {}, Streams(23), IdAllocator(),
                   inventory=inventory, **kwargs)


def advance(sim, frames, ticks):
    inputs = InputPlayer(frames)
    events = []
    for _ in range(ticks):
        step_events = sim.step(inputs.advance(sim.sim_tick))
        events.extend((sim.sim_tick, name, data) for name, data in step_events)
        if sim.done:
            break
    return events


def taps(*ticks):
    return [frame for tick in ticks for frame in
            ({"tick": tick, "interact": True}, {"tick": tick + 1, "interact": False})]


class StandardLayout(unittest.TestCase):
    def test_v11_layout_and_menu(self):
        sim = create_sim()
        self.assertEqual([(s["id"], s["pos"]) for s in sim.stoves], [("B1", [2, 8]), ("B2", [5, 8])])
        self.assertEqual([(t["id"], t["pos"]) for t in sim.tables], [
            ("T1", [9, 2]), ("T2", [13, 2]), ("T3", [9, 6]), ("T4", [13, 6])])
        self.assertEqual(len(TUNING["menu"]), 6)
        self.assertIn("ca_keo", TUNING["gather"]["fish_yield"])
        self.assertIn("keo_neo", TUNING["gather"]["nodes"][-1]["kind"])

    def test_two_stoves_cook_concurrently_and_low_id_wins_tie(self):
        scenario = {"random_customers": False, "player": {"pos": [3.5, 8]},
                    "customers": [
                        {"id": "K1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 1},
                        {"id": "K2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 2},
                    ]}
        sim = create_sim(scenario, {"ca_loc": 2})
        rows = advance(sim, taps(0), 1)
        sim.pos = [5, 8]
        rows.extend(advance(sim, taps(0, 2), 2))
        starts = [data for _, name, data in rows if name == "cook_started"]
        self.assertEqual([e["stove_id"] for e in starts], ["B1", "B2"])
        self.assertEqual([s["state"] for s in sim.stoves], ["cooking", "cooking"])

    def test_table_stove_equal_distance_prefers_stove(self):
        tuning = copy.deepcopy(TUNING)
        tuning["quan"]["stoves"] = [{"id": "B1", "pos": [5, 8]}]
        tuning["quan"]["tables"] = [{"id": "T1", "pos": [2, 8]}]
        scenario = {"random_customers": False, "player": {"pos": [3.5, 8]}, "hand": None,
                    "customers": [{"id": "K1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}
        sim = create_sim(scenario, {"ca_loc": 1}, tuning)
        rows = advance(sim, taps(0), 1)
        self.assertEqual([name for _, name, _ in rows], ["cook_started"])

    def test_four_smallest_tables_fill_and_fifth_arrival_is_skipped(self):
        tuning = copy.deepcopy(TUNING)
        tuning["quan"]["patience_s"] = 180
        inventory = {"ca_loc": 10}
        sim = create_sim({}, inventory, tuning)
        rows = advance(sim, [], FIRST + 4 * INTERVAL)
        arrivals = [data for _, name, data in rows if name == "customer_arrived"]
        self.assertEqual([e["table_id"] for e in arrivals], ["T1", "T2", "T3", "T4"])
        self.assertEqual(len(sim.customers), 4)
        self.assertNotIn("no_dish", [name for _, name, _ in rows])


class MenuFiltering(unittest.TestCase):
    def test_new_recipes_can_be_reserved(self):
        cases = [
            ("canh_chua_ca_loc", {"ca_loc": 1, "bong_dien_dien": 1}),
            ("ca_keo_nuong", {"ca_keo": 2}),
            ("lau_mam", {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}),
        ]
        for dish_id, recipe in cases:
            with self.subTest(dish_id=dish_id):
                sim = create_sim({}, recipe, allowed_dishes=[dish_id])
                rows = advance(sim, [], FIRST)
                arrival = next(data for _, name, data in rows if name == "customer_arrived")
                self.assertEqual(arrival["dish_id"], dish_id)
                self.assertEqual(sim.customers[0]["reserved"], recipe)

    def test_only_planned_dishes_with_stock_are_eligible(self):
        sim = create_sim({}, {"ca_keo": 2, "bong_sung": 2},
                         allowed_dishes=["ca_keo_nuong", "lau_mam"])
        rows = advance(sim, [], FIRST)
        self.assertEqual([data["dish_id"] for _, name, data in rows if name == "customer_arrived"],
                         ["ca_keo_nuong"])

    def test_unplanned_stock_does_not_prevent_no_dish(self):
        sim = create_sim({}, {"ca_loc": 1}, allowed_dishes=["lau_mam"])
        rows = advance(sim, [], FIRST)
        self.assertIn((FIRST, "no_dish", {}), rows)
        self.assertFalse(sim.customers)

    def test_initial_shift_totals_and_reputation_are_injectable(self):
        sim = create_sim({}, money=500, earned=320, shift_earned=0, reputation=4.5)
        self.assertEqual((sim.money, sim.earned, sim.shift_earned, sim.reputation), (500, 320, 0, 4.5))


class TipsAndClosing(unittest.TestCase):
    def test_tip_threshold_is_inclusive_and_reputation_clamps(self):
        full = round(Q["patience_s"] * HZ)
        half = round(full * Q["tip_min_patience_ratio"])
        for before, expected_tip in ((half + 1, 8), (half, 0)):
            scenario = {"random_customers": False, "player": {"pos": [9, 1.8]},
                        "hand": {"order_id": "K1", "dish_id": "goi_bong_sung", "base_price": 40},
                        "customers": [{"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung",
                                       "order_status": "assigned", "reserved": {},
                                       "patience_ticks_left": before}]}
            sim = create_sim(scenario, reputation=4.9)
            rows = advance(sim, taps(0), 1)
            served = next(data for _, name, data in rows if name == "served")
            self.assertEqual(served["tip"], expected_tip)
            if expected_tip:
                advance(sim, [], round(Q["eat_s"] * HZ))
                self.assertEqual(sim.reputation, Q["reputation_max"])

    def test_closing_settles_eating_and_waiting_without_waiting_penalty(self):
        scenario = {"random_customers": False, "time_left_ticks": 1,
                    "customers": [
                        {"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung",
                         "state": "eating", "order_status": "served", "reserved": {},
                         "eat_ticks_left": 50, "base_price": 40, "tip": 8},
                        {"id": "K2", "table_id": "T2", "dish_id": "goi_bong_sung"},
                    ]}
        sim = create_sim(scenario, reputation=3.0)
        rows = advance(sim, [], 1)
        self.assertEqual([name for _, name, _ in rows], ["paid", "customer_left", "quan_end"])
        self.assertEqual(sim.reputation, 3.2)
        self.assertEqual((sim.money, sim.earned, sim.shift_earned), (48, 48, 48))
        self.assertTrue(sim.done)


if __name__ == "__main__":
    unittest.main()
