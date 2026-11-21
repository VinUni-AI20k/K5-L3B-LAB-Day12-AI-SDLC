"""P1-10: luật quán kiểm HỘP ĐEN qua headless (JSONL), theo PRD-0 mục E, F, G.

Bổ sung cho test_quan_slice3.py và test_quan_slice4.py (chạy trong tiến trình, từng luật một):
file này chạy `headless_cmd` thật và chỉ đọc JSONL, kiểm một ca chơi trọn vẹn, công thức điểm, các bất biến
trong mọi snapshot và tính tái lập theo seed. Số liệu đọc từ game.contract.json.
"""

import json
import math
import os
import unittest

from helpers import Workdir, frames, read_jsonl, run_headless, snapshots, write_json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
    TUNING = json.load(f)["tuning"]
Q = TUNING["quan"]
HZ = TUNING["tick_hz"]
MENU = TUNING["menu"]
MULT = TUNING["score"]["reputation_multiplier"]
COOK = round(MENU["goi_bong_sung"]["cook_s"] * HZ)
EAT = round(Q["eat_s"] * HZ)
PRICE = MENU["goi_bong_sung"]["price"]
TIP = int(PRICE * Q["tip_rate"])
FIRST = Q["first_customer_tick"]
EVERY = round(Q["customer_interval_s"] * HZ)
ALL_STOCK = {"ca_loc": 5, "ca_linh": 6, "bong_dien_dien": 3, "bong_sung": 10}


def play(scenario, inputs=(), ticks=1, stock=None, seed=1, every=1):
    """Chạy headless quan; trả (mã thoát, các dòng JSONL, stderr). stock đi qua --inventory."""
    with Workdir() as w:
        args = ["--mode", "quan", "--seed", str(seed), "--ticks", str(ticks), "--out", w.path("o.jsonl"),
                "--snapshot-every", str(every)]
        if scenario is not None:
            args += ["--scenario", write_json(w.path("s.json"), {"quan": scenario})]
        if inputs:
            args += ["--inputs", write_json(w.path("i.json"), frames(*inputs))]
        if stock is not None:
            args += ["--inventory", write_json(w.path("kho.json"), {"items": stock})]
        code, err = run_headless(*args)
        rows = read_jsonl(w.path("o.jsonl")) if os.path.exists(w.path("o.jsonl")) else []
    return code, rows, err


def named(rows, name):
    return [r for r in rows if r["type"] == "event" and r["name"] == name]


def edge(*ticks):
    out = []
    for k in ticks:
        out += [{"tick": k, "interact": True}, {"tick": k + 1, "interact": False}]
    return out


# Người chơi đứng cạnh bếp B1 [2, 8], nấu, bưng món, đi tới bàn T1 [9, 2] (120 tick hướng [0.763, -0.646]), phục vụ.
WALK = [0.763, -0.646]
ONE_DISH_INPUTS = sorted(edge(0, 240, 380) + [{"tick": 250, "move": WALK}, {"tick": 370, "move": [0, 0]}],
                         key=lambda f: f["tick"])
ONE_DISH_SCENARIO = {"random_customers": False, "player": {"pos": [2.5, 7.5]},
                     "customers": [{"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung"}]}


class OneDishShift(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code, cls.rows, cls.err = play(ONE_DISH_SCENARIO, ONE_DISH_INPUTS, ticks=1500, stock={"bong_sung": 2})

    def test_runs_and_events_follow_the_cooking_cycle(self):
        self.assertEqual(self.code, 0, self.err)
        seq = [(r["tick"], r["name"]) for r in self.rows if r["type"] == "event"]
        self.assertEqual(seq, [(1, "cook_started"), (1 + COOK, "dish_ready"), (1 + COOK, "dish_picked"),
                               (381, "served"), (381 + EAT, "paid")])

    def test_money_earned_reputation_and_score_at_the_end(self):
        end = self.rows[-1]
        self.assertEqual(end["type"], "end")
        self.assertEqual((end["money"], end["earned"]), (PRICE + TIP, PRICE + TIP))
        self.assertAlmostEqual(end["reputation"], Q["reputation_initial"] + Q["tip_reputation"])
        self.assertEqual(end["reason"], "tick_limit")  # chưa hết ca: không có quan_end
        self.assertEqual(named(self.rows, "quan_end"), [])

    def test_score_formula_holds_in_every_snapshot_and_the_end_row(self):
        for r in [*snapshots(self.rows), self.rows[-1]]:
            self.assertEqual(r["score"], r["earned"] + MULT * math.floor(r["reputation"]), r.get("tick", r.get("ticks")))

    def test_stock_is_spent_when_cooking_starts_and_never_comes_back(self):
        snaps = snapshots(self.rows)
        self.assertEqual(snaps[0]["stock"], {"bong_sung": 2})
        self.assertTrue(all("bong_sung" not in s["stock"] for s in snaps[1:]))

    def test_table_and_customer_lists_follow_the_customer(self):
        snaps = {s["tick"]: s for s in snapshots(self.rows)}
        self.assertEqual(snaps[0]["tables"][0]["customer_id"], "K1")
        self.assertEqual([c["id"] for c in snaps[500]["customers"]], ["K1"])
        self.assertEqual(snaps[500]["customers"][0]["state"], "eating")
        self.assertEqual(snaps[1500]["customers"], [])
        self.assertIsNone(snaps[1500]["tables"][0]["customer_id"])

    def test_hand_carries_the_dish_between_stove_and_table(self):
        snaps = {s["tick"]: s for s in snapshots(self.rows)}
        self.assertIsNone(snaps[100]["hand"])
        self.assertEqual(snaps[300]["hand"], {"order_id": "K1", "dish_id": "goi_bong_sung", "base_price": PRICE})
        self.assertIsNone(snaps[400]["hand"])

    def test_same_inputs_same_bytes(self):
        again = play(ONE_DISH_SCENARIO, ONE_DISH_INPUTS, ticks=1500, stock={"bong_sung": 2})[1]
        self.assertEqual(again, self.rows)


class Invariants(unittest.TestCase):
    """Chạy ca dài với khách ngẫu nhiên, người chơi đứng yên: bất biến phải đúng ở MỌI snapshot."""

    @classmethod
    def setUpClass(cls):
        cls.runs = {}
        for seed in (1, 2):
            code, rows, err = play({"random_customers": True}, ticks=9000, stock=ALL_STOCK, seed=seed, every=10)
            assert code == 0, err
            cls.runs[seed] = rows

    def test_reputation_stays_within_bounds_and_money_never_drops(self):
        for seed, rows in self.runs.items():
            last = 0
            for s in snapshots(rows):
                self.assertTrue(Q["reputation_min"] <= s["reputation"] <= Q["reputation_max"], (seed, s["tick"]))
                self.assertGreaterEqual(s["money"], last)
                last = s["money"]

    def test_one_customer_per_table_and_reservations_never_exceed_stock(self):
        for seed, rows in self.runs.items():
            for s in snapshots(rows):
                tables = [c["table_id"] for c in s["customers"]]
                self.assertEqual(len(tables), len(set(tables)), (seed, s["tick"]))
                held = {}
                for c in s["customers"]:
                    for kind, n in c.get("reserved", {}).items():
                        held[kind] = held.get(kind, 0) + n
                for kind, n in held.items():
                    self.assertLessEqual(n, s["stock"].get(kind, 0), (seed, s["tick"], kind))

    def test_clock_counts_down_one_per_tick(self):
        for rows in self.runs.values():
            snaps = snapshots(rows)
            for a, b in zip(snaps, snaps[1:]):
                self.assertEqual(a["time_left_ticks"] - b["time_left_ticks"], b["tick"] - a["tick"])

    def test_customers_arrive_only_on_the_schedule(self):
        for seed, rows in self.runs.items():
            ticks = [r["tick"] for r in named(rows, "customer_arrived")]
            self.assertTrue(ticks, seed)
            for t in ticks:
                self.assertEqual((t - FIRST) % EVERY, 0, (seed, t))

    def test_waiting_customers_leave_when_patience_runs_out(self):
        for seed, rows in self.runs.items():
            arrivals = {r["data"]["order_id"]: r["tick"] for r in named(rows, "customer_arrived")}
            for r in named(rows, "customer_left"):
                if r["data"]["reason"] == "patience":
                    self.assertEqual(r["tick"] - arrivals[r["data"]["order_id"]], round(Q["patience_s"] * HZ))


class RandomChoice(unittest.TestCase):
    def first_dish(self, seed):
        _, rows, _ = play({"random_customers": True}, ticks=FIRST, stock=ALL_STOCK, seed=seed, every=FIRST)
        return named(rows, "customer_arrived")[0]["data"]["dish_id"]

    def test_dish_is_reproducible_per_seed_and_varies_across_seeds(self):
        dishes = {seed: self.first_dish(seed) for seed in range(1, 9)}
        self.assertTrue(set(dishes.values()) <= set(MENU))
        self.assertGreaterEqual(len(set(dishes.values())), 2)
        self.assertEqual(self.first_dish(3), dishes[3])

    def test_only_cookable_dishes_are_offered(self):
        for seed in range(1, 6):
            _, rows, _ = play({"random_customers": True}, ticks=FIRST, stock={"ca_loc": 1}, seed=seed, every=FIRST)
            self.assertEqual(named(rows, "customer_arrived")[0]["data"]["dish_id"], "ca_loc_nuong_trui")


class NeverBurns(unittest.TestCase):
    def test_ready_dish_waits_forever_burn_s_is_null(self):
        self.assertIsNone(Q["burn_s"])
        payload = {"order_id": "K1", "dish_id": "goi_bong_sung", "base_price": PRICE}
        scenario = {"random_customers": False, "player": {"pos": [8, 5]},
                    "stoves": [{"id": "B1", "state": "ready", "dish": payload, "ready_ticks": 0}],
                    "customers": [{"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung",
                                   "order_status": "assigned", "reserved": {}, "patience_ticks_left": 9000}]}
        code, rows, err = play(scenario, ticks=5000, every=1000)
        self.assertEqual(code, 0, err)
        self.assertEqual([r for r in rows if r["type"] == "event"], [])
        last = snapshots(rows)[-1]["stoves"][0]
        self.assertEqual((last["state"], last["ready_ticks"], last["dish"]), ("ready", 5000, payload))


class ShiftEnd(unittest.TestCase):
    def test_closing_pays_the_eating_customer_and_ends_the_shift(self):
        scenario = {"random_customers": False, "time_left_ticks": 50,
                    "customers": [{"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                                   "order_status": "served", "eat_ticks_left": 400, "base_price": PRICE,
                                   "tip": TIP, "reserved": {}}]}
        code, rows, err = play(scenario, ticks=100, every=100)
        self.assertEqual(code, 0, err)
        events = [r for r in rows if r["type"] == "event"]
        self.assertEqual([e["name"] for e in events], ["paid", "quan_end"])
        self.assertEqual(events[0]["data"]["reason"], "closing")
        end_event, end_row = events[1]["data"], rows[-1]
        self.assertEqual((end_event["reason"], end_event["money"], end_event["shift_earned"]),
                         ("time", PRICE + TIP, PRICE + TIP))
        self.assertEqual((end_row["reason"], end_row["ticks"]), ("time", 50))
        self.assertEqual(end_row["score"], end_row["earned"] + MULT * math.floor(end_row["reputation"]))


if __name__ == "__main__":
    unittest.main()
