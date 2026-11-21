"""TV4 · Kiểm chứng mục D–F qua CLI và JSONL."""
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

DISH = "ca_loc_nuong_trui"
ORDER = {"id": "C7", "table_id": "T1", "dish_id": DISH}
PLATE = {"order_id": "C7", "dish_id": DISH, "base_price": 60}
PRESS = {"tick": 0, "interact": True}


class Kitchen(unittest.TestCase):
    def simulate(self, scenario, ticks, *inputs, invalid=False):
        with Workdir() as w:
            sc = write_json(w.path("s.json"), {"quan": dict(random_customers=False, **scenario)})
            keys = write_json(w.path("keys.json"), frames(*inputs))
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--scenario", sc, "--inputs", keys,
                                     "--out", out, "--ticks", str(ticks), "--snapshot-every", "1")
            if invalid:
                self.assertEqual(code, 2, err)
                self.assertFalse(os.path.exists(out))
                return
            self.assertEqual(code, 0, err)
            return read_jsonl(out)

    def test_cook_pick_serve_pay(self):
        # B1 và T1 cách nhau 2 m. Bấm lần thứ hai đúng bước món chín.
        dish = "lau_ca_linh_dien_dien"
        sc = {"customers": [dict(ORDER, dish_id=dish)], "stock": {"ca_linh": 4, "bong_dien_dien": 1},
              "player": {"pos": [2, 8]}, "tables": [{"id": "T1", "pos": [4, 8]}]}
        rows = self.simulate(sc, 1232, PRESS, {"tick": 599, "interact": False},
                             {"tick": 600, "interact": True}, {"tick": 601, "interact": False, "move": [1, 0]},
                             {"tick": 630, "interact": True, "move": [0, 0]})
        self.assertEqual([(e["tick"], e["name"]) for e in events(rows)], [
            (1, "cook_started"), (601, "dish_ready"), (601, "dish_picked"), (631, "served"), (1231, "paid")])
        start = events(rows)[0]["data"]
        self.assertEqual(start["items"], ["bong_dien_dien", "ca_linh", "ca_linh", "ca_linh"])
        self.assertEqual(start["base_price"], 120)
        states = snapshots(rows)
        self.assertEqual(states[1]["stock"], {"ca_linh": 1})
        self.assertEqual(states[1]["customers"][0]["reserved"], {})
        self.assertEqual(states[601]["hand"], {"order_id": "C7", "dish_id": dish, "base_price": 120})
        self.assertEqual(states[631]["customers"][0]["eat_ticks_left"], 600)
        self.assertIsNone(states[631]["hand"])
        self.assertEqual(states[1230]["money"], 0)
        self.assertEqual(events(rows, "paid")[0]["data"], {"order_id": "C7", "table_id": "T1",
                         "base_price": 120, "tip": 24, "amount": 144, "reason": "finished_eating"})
        self.assertEqual(rows[-1]["score"], 444)
        self.assertIsNone(states[-1]["tables"][0]["customer_id"])

    def test_serve_at_deadline_and_at_closing(self):
        for patience, time_left, tip in [(1, 2, 0), (1801, 1, 12), (1800, 1, 0)]:
            with self.subTest(patience=patience):
                sc = {"hand": PLATE, "player": {"pos": [9, 2]}, "time_left_ticks": time_left,
                      "customers": [dict(ORDER, order_status="assigned", patience_ticks_left=patience)]}
                rows = self.simulate(sc, 5, PRESS)
                self.assertEqual([e["name"] for e in events(rows)], ["served", "paid", "quan_end"])
                served, paid, end = events(rows)
                self.assertEqual(served["data"]["patience_ticks_left"], patience - 1)
                self.assertEqual(paid["tick"], time_left)
                self.assertEqual(paid["data"]["reason"], "closing")
                self.assertEqual(paid["data"]["tip"], tip)
                self.assertEqual(end["data"], {"money": 60 + tip, "earned": 60 + tip, "shift_earned": 60 + tip,
                                               "reason": "time", "reputation": 3.2 if tip else 3})

    def test_waiting_at_close_discards_dish(self):
        sc = {"hand": PLATE, "time_left_ticks": 1,
              "customers": [dict(ORDER, order_status="assigned", patience_ticks_left=1)]}
        rows = self.simulate(sc, 2)
        self.assertEqual([e["name"] for e in events(rows)], ["customer_left", "quan_end"])
        self.assertEqual(events(rows)[0]["data"]["reason"], "closing")
        end = snapshots(rows)[-1]
        self.assertEqual((end["stock"], end["customers"], end["hand"], end["reputation"]), ({}, [], None, 3))

    def test_paid_at_end_of_meal_on_last_tick(self):
        sc = {"time_left_ticks": 1, "reputation": 4.9,
              "customers": [dict(ORDER, order_status="served", state="eating", eat_ticks_left=1,
                                 base_price=60, tip=12)]}
        rows = self.simulate(sc, 3)
        self.assertEqual([e["name"] for e in events(rows)], ["paid", "quan_end"])
        self.assertEqual(events(rows)[0]["data"]["reason"], "finished_eating")
        self.assertEqual(rows[-1]["score"], 572)

    def test_equal_distance_selects_idle_stove_before_table(self):
        sc = {"hand": PLATE, "player": {"pos": [3.5, 8]}, "tables": [{"id": "T1", "pos": [5, 8]}],
              "customers": [dict(ORDER, order_status="assigned")]}
        rows = self.simulate(sc, 1, PRESS)
        self.assertEqual(events(rows), [])
        self.assertEqual(snapshots(rows)[-1]["hand"], PLATE)

    def test_inconsistent_plate_rejected_before_output(self):
        customer = dict(ORDER, order_status="assigned")
        stove = {"id": "B1", "state": "ready", "dish": PLATE}
        for payload in ({}, {"stoves": [stove], "hand": PLATE}, {"hand": dict(PLATE, order_id="C9")},
                        {"hand": dict(PLATE, dish_id="goi_bong_sung")},
                        {"stoves": [dict(stove, state="cooking", cook_ticks_left=0)]}):
            with self.subTest(payload=payload):
                self.simulate(dict(customers=[customer], **payload), 0, invalid=True)
