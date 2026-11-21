"""P1-04 acceptance tests; fixtures isolate the pending P1-03 arrival system."""

from copy import deepcopy
from pathlib import Path
import json
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer, InputState
from chonoi.live import LiveGame, LiveServer
from chonoi.runner import Session

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json
from test_live import _get, _post


FIXTURES = Path(__file__).parent / "fixtures"


class KitchenServing(unittest.TestCase):
    def setUp(self):
        self.tuning = deepcopy(load_contract()["tuning"])
        self.q = self.tuning["quan"]
        self.menu = self.tuning["menu"]
        self.hz = self.tuning["tick_hz"]
        self.dish_id = next(iter(self.menu))

    def customer(self, **updates):
        c = {"id": "C1", "table_id": "T1", "state": "waiting",
             "order_status": "reserved", "order_tick": 0, "dish_id": self.dish_id,
             "base_price": self.menu[self.dish_id]["price"],
             "reserved": dict(self.menu[self.dish_id]["recipe"]),
             "patience_ticks_left": round(self.q["patience_s"] * self.hz)}
        c.update(updates)
        return c

    @staticmethod
    def dish(c):
        return {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": c["base_price"]}

    def session(self, **block):
        return Session("quan", self.tuning, block, 42)

    @staticmethod
    def step(s, interact=False, move=(0, 0)):
        return s.step(InputState(move, {}, {"interact"} if interact else set()))

    def advance(self, s, count):
        rows = []
        for _ in range(count):
            rows.extend(self.step(s))
        return rows

    def cooking_session(self, **customer_updates):
        c = self.customer(**customer_updates)
        return self.session(player={"pos": self.q["stoves"][0]["pos"]}, customers=[c],
                            stock=dict(self.menu[c["dish_id"]]["recipe"]))

    def assigned_session(self, location="hand", state="ready", **customer_updates):
        c = self.customer(order_status="assigned", reserved={}, **customer_updates)
        block = {"customers": [c]}
        if location == "hand":
            block.update(hand=self.dish(c), player={"pos": self.q["tables"][0]["pos"]})
        else:
            block.update(stoves=[{"id": "B1", "state": state, "dish": self.dish(c),
                                   "cook_ticks_left": 2 if state == "cooking" else 0}],
                         player={"pos": self.q["stoves"][0]["pos"]})
        return self.session(**block)

    def test_cook_consumes_exact_recipe_and_emits_sorted_items_for_each_dish(self):
        for dish_id, config in self.menu.items():
            with self.subTest(dish=dish_id):
                s = self.cooking_session(dish_id=dish_id, base_price=config["price"],
                                         reserved=dict(config["recipe"]))
                rows = self.step(s, True)
                self.assertEqual([r["name"] for r in rows], ["cook_started"])
                self.assertEqual(rows[0]["tick"], 1)
                self.assertEqual(rows[0]["data"], {
                    "stove_id": "B1", "order_id": "C1", "dish_id": dish_id, "base_price": config["price"],
                    "items": [k for k in sorted(config["recipe"]) for _ in range(config["recipe"][k])]})
                self.assertEqual(s.sim.snapshot()["stock"], {})
                self.assertEqual(s.sim.customers[0]["reserved"], {})
                self.assertEqual(s.sim.customers[0]["order_status"], "assigned")
                self.assertEqual(s.sim.stoves[0]["cook_ticks_left"], round(config["cook_s"] * self.hz))
                self.assertEqual(s.sim.money, 0)

    def test_busy_stove_cannot_cook_or_pick(self):
        s = self.cooking_session()
        self.step(s, True)
        before_stock = dict(s.sim.stock)
        self.assertEqual(self.step(s, True), [])
        self.assertIsNone(s.sim.hand)
        self.assertEqual(s.sim.stock, before_stock)
        self.assertEqual(s.sim.stoves[0]["state"], "cooking")

    def test_no_reserved_order_cannot_cook(self):
        for status in (None, "unfulfillable"):
            with self.subTest(status=status):
                customers = [] if status is None else [self.customer(order_status=status, reserved={})]
                s = self.session(player={"pos": [2, 8]}, stock={"ca_loc": 10}, customers=customers)
                self.assertEqual(self.step(s, True), [])
                self.assertEqual(s.sim.stock, {"ca_loc": 10})
                self.assertEqual(s.sim.stoves[0]["state"], "idle")

    def test_oldest_order_then_natural_table_id_and_other_reservation_preserved(self):
        self.q["tables"] += [{"id": "T10", "pos": [10, 2]}, {"id": "T2", "pos": [11, 2]}]
        customers = [self.customer(id="C1", table_id="T1", order_tick=4),
                     self.customer(id="C2", table_id="T10", order_tick=1),
                     self.customer(id="C3", table_id="T2", order_tick=1)]
        stock = {k: qty * 3 for k, qty in self.menu[self.dish_id]["recipe"].items()}
        s = self.session(player={"pos": [2, 8]}, customers=customers, stock=stock)
        self.assertEqual(self.step(s, True)[0]["data"]["order_id"], "C3")
        self.assertEqual(s.sim.customers[0]["reserved"], self.menu[self.dish_id]["recipe"])
        self.assertEqual(s.sim.customers[1]["reserved"], self.menu[self.dish_id]["recipe"])
        self.assertEqual(s.sim.stock, {k: qty * 2 for k, qty in self.menu[self.dish_id]["recipe"].items()})

    def test_insufficient_or_wrong_reservation_does_not_partially_consume(self):
        s = self.cooking_session()
        s.sim.stock.clear()  # Defend against inconsistent future P1-03 mutations.
        self.assertEqual(self.step(s, True), [])
        self.assertEqual(s.sim.customers[0]["order_status"], "reserved")
        self.assertEqual(s.sim.stoves[0]["state"], "idle")
        s.sim.stock = dict(self.menu[self.dish_id]["recipe"])
        s.sim.customers[0]["reserved"] = {}
        self.assertEqual(self.step(s, True), [])
        self.assertEqual(s.sim.stock, self.menu[self.dish_id]["recipe"])

    def test_ready_exact_tick_once_and_ready_ticks_start_next_step_no_burning(self):
        for dish_id, config in self.menu.items():
            with self.subTest(dish=dish_id):
                s = self.cooking_session(dish_id=dish_id, base_price=config["price"],
                                         reserved=dict(config["recipe"]))
                self.step(s, True)
                ticks = round(config["cook_s"] * self.hz)
                self.assertFalse(events(self.advance(s, ticks - 1), "dish_ready"))
                ready = self.step(s)
                self.assertEqual([r["name"] for r in ready], ["dish_ready"])
                self.assertEqual(ready[0]["tick"], ticks + 1)
                self.assertEqual(s.sim.stoves[0]["ready_ticks"], 0)
                self.assertFalse(events(self.advance(s, 1000), "dish_ready"))
                self.assertEqual(s.sim.stoves[0]["state"], "ready")
                self.assertEqual(s.sim.stoves[0]["ready_ticks"], 1000)

    def test_pick_preserves_order_price_and_resets_stove(self):
        s = self.assigned_session(location="stove")
        rows = self.step(s, True)
        self.assertEqual([r["name"] for r in rows], ["dish_picked"])
        self.assertEqual(s.sim.hand, self.dish(s.sim.customers[0]))
        self.assertEqual(s.sim.hand["base_price"], self.menu[self.dish_id]["price"])
        st = s.sim.stoves[0]
        self.assertEqual((st["state"], st["dish"], st["cook_ticks_left"], st["ready_ticks"]),
                         ("idle", None, 0, 0))
        self.assertEqual(self.step(s, True), [])

    def test_full_hand_cannot_pick_or_duplicate_dish(self):
        self.q["tables"].append({"id": "T2", "pos": [10, 2]})
        c1 = self.customer(order_status="assigned", reserved={})
        c2 = self.customer(id="C2", table_id="T2", order_status="assigned", reserved={})
        s = self.session(player={"pos": [2, 8]}, customers=[c1, c2], hand=self.dish(c2),
                         stoves=[{"id": "B1", "state": "ready", "dish": self.dish(c1)}])
        self.assertEqual(self.step(s, True), [])
        self.assertEqual(s.sim.hand, self.dish(c2))
        self.assertEqual(s.sim.stoves[0]["dish"], self.dish(c1))

    def test_wrong_table_order_or_dish_not_served(self):
        self.q["tables"].append({"id": "T2", "pos": [10, 8]})
        s = self.assigned_session()
        s.sim.pos = [10, 8]
        self.assertEqual(self.step(s, True), [])
        s.sim.pos = list(self.q["tables"][0]["pos"])
        for key in ("order_id", "dish_id"):
            with self.subTest(key=key):
                original = s.sim.hand[key]
                s.sim.hand[key] = "wrong"
                self.assertEqual(self.step(s, True), [])
                s.sim.hand[key] = original
        self.assertEqual(s.sim.customers[0]["state"], "waiting")

    def test_euclidean_radius_inclusive_and_outside_rejected(self):
        for offset, allowed in (((0.9, 1.2), True), ((0.90001, 1.2), False), ((1.4, 1.4), False)):
            with self.subTest(offset=offset):
                s = self.assigned_session()
                x, z = self.q["tables"][0]["pos"]
                s.sim.pos = [x + offset[0], z + offset[1]]
                rows = self.step(s, True)
                self.assertEqual(bool(events(rows, "served")), allowed)

    def test_held_interact_does_not_pick_when_cooking_finishes(self):
        s = self.cooking_session()
        player = InputPlayer([{"tick": 0, "interact": True}])
        rows = []
        for tick in range(round(self.menu[self.dish_id]["cook_s"] * self.hz) + 3):
            rows.extend(s.step(player.advance(tick)))
        self.assertEqual(len(events(rows, "cook_started")), 1)
        self.assertEqual(len(events(rows, "dish_ready")), 1)
        self.assertFalse(events(rows, "dish_picked"))
        self.assertIsNone(s.sim.hand)

    def test_nearest_unusable_object_blocks_fallback_and_tie_prefers_stove(self):
        for player_pos in ([2.1, 8], [3, 8]):
            with self.subTest(pos=player_pos):
                self.q["tables"][0]["pos"] = [4, 8]
                s = self.assigned_session()
                s.sim.pos = list(player_pos)
                self.assertEqual(self.step(s, True), [])  # idle stove, no reserved orders
                self.assertIsNotNone(s.sim.hand)
        s.sim.pos = [3.1, 8]
        self.assertEqual([r["name"] for r in self.step(s, True)], ["served"])

    def test_equal_distance_stoves_use_natural_id_and_only_one_action(self):
        self.q["stoves"] += [{"id": "B10", "pos": [5, 8]}, {"id": "B2", "pos": [5, 8]}]
        s = self.cooking_session()
        s.sim.pos = [5, 8]
        rows = self.step(s, True)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["data"]["stove_id"], "B2")

    def test_movement_precedes_interaction(self):
        s = self.cooking_session()
        s.sim.pos = [3.51, 8]
        s.sim.vel = [-self.q["walk_speed"], 0]
        self.assertEqual([r["name"] for r in self.step(s, True, (-1, 0))], ["cook_started"])

    def test_tips_for_all_prices_payment_delayed_and_once(self):
        expected = {"ca_loc_nuong_trui": (60, 12), "goi_bong_sung": (40, 8),
                    "lau_ca_linh_dien_dien": (120, 24)}
        for dish_id, (base, tip) in expected.items():
            with self.subTest(dish=dish_id):
                s = self.assigned_session(dish_id=dish_id, base_price=base)
                served = self.step(s, True)
                self.assertEqual(served[0]["data"]["tip"], tip)
                self.assertEqual(s.sim.money, 0)
                self.assertEqual(s.sim.earned, 0)
                eat_ticks = round(self.q["eat_s"] * self.hz)
                self.assertEqual(s.sim.customers[0]["eat_ticks_left"], eat_ticks)
                self.assertFalse(events(self.advance(s, eat_ticks - 1), "paid"))
                paid = self.step(s)
                self.assertEqual(paid[0]["tick"], eat_ticks + 1)
                self.assertEqual(paid[0]["data"], {"order_id": "C1", "table_id": "T1", "base_price": base,
                                                   "tip": tip, "amount": base + tip, "reason": "finished_eating"})
                self.assertEqual((s.sim.money, s.sim.earned, s.sim.shift_earned), (base + tip,) * 3)
                self.assertFalse(events(self.advance(s, 2), "paid"))
                self.assertEqual(s.sim.snapshot()["tables"][0]["customer_id"], None)
                self.assertEqual(s.sim.customers, [])
                self.assertEqual(s.sim.reputation, 3.2)

    def test_tip_boundary_uses_patience_after_decrement(self):
        maximum = round(self.q["patience_s"] * self.hz)
        boundary = round(maximum * self.q["tip_min_patience_ratio"])
        for remaining, tipped in ((boundary + 1, True), (boundary, False)):
            with self.subTest(remaining=remaining):
                s = self.assigned_session(patience_ticks_left=remaining)
                data = self.step(s, True)[0]["data"]
                self.assertEqual(data["patience_ticks_left"], remaining - 1)
                self.assertEqual(data["tip"] > 0, tipped)

    def test_reputation_clamps_high_and_low_without_float_drift(self):
        s = self.assigned_session()
        s.sim.reputation = 4.9
        self.step(s, True)
        self.advance(s, round(self.q["eat_s"] * self.hz))
        self.assertEqual(s.sim.reputation, self.q["reputation_max"])
        s = self.cooking_session(patience_ticks_left=1)
        s.sim.reputation = 0.1
        self.step(s)
        self.assertEqual(s.sim.reputation, self.q["reputation_min"])
        s.sim.reputation = 3.0
        for _ in range(10):
            s.sim._change_reputation(self.q["tip_reputation"])
        self.assertEqual(s.sim.reputation, 5.0)

    def test_nondefault_tuning_controls_cook_eat_tip_carry_and_movement(self):
        self.tuning["tick_hz"] = 30
        self.hz = 30
        self.q["eat_s"] = 2
        self.q["tip_rate"] = 0.29
        s = self.cooking_session(base_price=100)
        self.step(s, True)
        self.assertEqual(s.sim.stoves[0]["cook_ticks_left"], round(self.menu[self.dish_id]["cook_s"] * 30))
        s = self.assigned_session(base_price=100)
        served = self.step(s, True)
        self.assertEqual(served[0]["data"]["tip"], 29)
        self.assertEqual(s.sim.customers[0]["eat_ticks_left"], 60)
        self.q["carry_limit"] = 0
        s = self.assigned_session(location="stove")
        self.assertEqual(self.step(s, True), [])
        self.assertIsNone(s.sim.hand)

    def test_serve_on_zero_patience_tick_is_allowed(self):
        s = self.assigned_session(patience_ticks_left=1)
        rows = self.step(s, True)
        self.assertEqual([r["name"] for r in rows], ["served"])
        self.assertEqual(rows[0]["data"]["patience_ticks_left"], 0)
        self.assertEqual(rows[0]["data"]["tip"], 0)
        self.assertEqual(s.sim.customers[0]["state"], "eating")

    def test_serve_on_closing_tick_gets_paid_then_end_once(self):
        s = self.assigned_session()
        s.sim.time_left_ticks = 1
        rows = self.step(s, True)
        self.assertEqual([r["name"] for r in rows], ["served", "paid", "quan_end"])
        self.assertEqual(rows[1]["data"]["reason"], "closing")
        self.assertEqual(rows[2]["data"], {"reason": "time", "money": 72, "earned": 72,
                                           "shift_earned": 72, "reputation": 3.2})
        self.assertEqual(self.step(s, True), [])

    def test_closing_pays_eating_and_releases_waiting_without_penalty(self):
        self.q["tables"].append({"id": "T2", "pos": [10, 2]})
        eating = self.customer(state="eating", order_status="served", reserved={}, tip=12, eat_ticks_left=100)
        waiting = self.customer(id="C2", table_id="T2", patience_ticks_left=1)
        s = self.session(customers=[eating, waiting], stock={"ca_loc": 1}, time_left_ticks=1)
        rows = self.step(s)
        self.assertEqual([r["name"] for r in rows], ["paid", "customer_left", "quan_end"])
        self.assertEqual(rows[0]["data"]["reason"], "closing")
        self.assertEqual(rows[1]["data"]["reason"], "closing")
        self.assertEqual(s.sim.reputation, 3.2)
        self.assertEqual(s.sim.stock, {"ca_loc": 1})
        self.assertEqual(s.sim.customers, [])

    def test_eating_finishes_normally_before_closing_settlement(self):
        c = self.customer(state="eating", order_status="served", reserved={}, tip=12, eat_ticks_left=1)
        s = self.session(customers=[c], time_left_ticks=1)
        rows = self.step(s)
        self.assertEqual([r["name"] for r in rows], ["paid", "quan_end"])
        self.assertEqual(rows[0]["data"]["reason"], "finished_eating")

    def test_closing_discards_all_unserved_dish_locations_without_refund(self):
        for location, state in (("stove", "cooking"), ("stove", "ready"), ("hand", "ready")):
            with self.subTest(location=location, state=state):
                s = self.assigned_session(location=location, state=state)
                s.sim.time_left_ticks = 1
                rows = self.step(s)
                self.assertEqual([r["name"] for r in rows], ["customer_left", "quan_end"])
                self.assertEqual(s.sim.customers, [])
                self.assertEqual(s.sim.stoves[0]["state"], "idle")
                self.assertIsNone(s.sim.hand)
                self.assertEqual(s.sim.stock, {})
                self.assertEqual(s.sim.reputation, self.q["reputation_initial"])

    def test_final_tick_keeps_ready_event_before_closing_cleanup(self):
        s = self.assigned_session(location="stove", state="cooking")
        s.sim.stoves[0]["cook_ticks_left"] = 1
        s.sim.time_left_ticks = 1
        rows = self.step(s)
        self.assertEqual([r["name"] for r in rows], ["dish_ready", "customer_left", "quan_end"])
        self.assertEqual(s.sim.stoves[0]["state"], "idle")

    def test_service_on_both_zero_patience_and_closing_tick(self):
        s = self.assigned_session(patience_ticks_left=1)
        s.sim.time_left_ticks = 1
        rows = self.step(s, True)
        self.assertEqual([r["name"] for r in rows], ["served", "paid", "quan_end"])
        self.assertEqual(rows[1]["data"]["amount"], 60)
        self.assertEqual(rows[1]["data"]["tip"], 0)
        self.assertEqual(s.sim.reputation, self.q["reputation_initial"])

    def test_payment_adds_to_existing_totals_and_no_tip_preserves_reputation(self):
        s = self.assigned_session(patience_ticks_left=1)
        s.sim.money, s.sim.earned, s.sim.shift_earned = 17, 31, 23
        self.step(s, True)
        self.advance(s, round(self.q["eat_s"] * self.hz))
        self.assertEqual((s.sim.money, s.sim.earned, s.sim.shift_earned), (77, 91, 83))
        self.assertEqual(s.sim.reputation, self.q["reputation_initial"])

    def test_leave_clears_cooking_ready_and_hand_without_refund(self):
        for location, state in (("stove", "cooking"), ("stove", "ready"), ("hand", "ready")):
            with self.subTest(location=location, state=state):
                s = self.assigned_session(location=location, state=state, patience_ticks_left=1)
                rows = self.step(s)
                self.assertEqual([r["name"] for r in rows], ["customer_left"])
                self.assertEqual(rows[0]["data"]["reason"], "patience")
                self.assertEqual(s.sim.customers, [])
                self.assertIsNone(s.sim.hand)
                self.assertEqual(s.sim.stoves[0]["state"], "idle")
                self.assertEqual(s.sim.stock, {})
                self.assertEqual(s.sim.money, 0)
                self.assertEqual(s.sim.reputation, 2.5)
                self.assertEqual(self.step(s), [])

    def test_reserved_leave_releases_claim_without_consuming_stock(self):
        s = self.cooking_session(patience_ticks_left=1)
        self.step(s)
        self.assertEqual(s.sim.stock, self.menu[self.dish_id]["recipe"])
        self.assertEqual(s.sim.customers, [])

    def test_timeout_after_cook_started_does_not_refund_consumed_inventory(self):
        s = self.cooking_session(patience_ticks_left=2)
        self.assertEqual(self.step(s, True)[0]["name"], "cook_started")
        self.assertEqual(self.step(s)[0]["name"], "customer_left")
        self.assertEqual(s.snapshot()["stock"], {})
        self.assertEqual(s.sim.customers, [])
        self.assertEqual(s.sim.stoves[0]["state"], "idle")

    def test_ready_then_pick_on_same_tick_and_no_decrement_of_new_eating_timer(self):
        s = self.assigned_session(location="stove", state="cooking")
        s.sim.stoves[0]["cook_ticks_left"] = 1
        rows = self.step(s, True)
        self.assertEqual([r["name"] for r in rows], ["dish_ready", "dish_picked"])
        self.assertEqual(s.sim.stoves[0]["state"], "idle")
        s.sim.pos = list(self.q["tables"][0]["pos"])
        self.step(s, True)
        self.assertEqual(s.sim.customers[0]["eat_ticks_left"], round(self.q["eat_s"] * self.hz))

    def test_ready_events_are_sorted_by_natural_stove_id(self):
        self.q["stoves"] += [{"id": "B10", "pos": [5, 8]}, {"id": "B2", "pos": [6, 8]}]
        self.q["tables"] += [{"id": "T2", "pos": [10, 2]}, {"id": "T3", "pos": [11, 2]}]
        customers = [self.customer(id=f"C{i}", table_id=f"T{i}",
                                   order_status="assigned", reserved={}) for i in (1, 2, 3)]
        stoves = [{"id": sid, "state": "cooking", "cook_ticks_left": 1, "dish": self.dish(c)}
                  for sid, c in zip(("B10", "B2", "B1"), customers)]
        s = self.session(customers=customers, stoves=stoves)
        self.assertEqual([r["data"]["stove_id"] for r in self.step(s)], ["B1", "B2", "B10"])

    def test_minimal_customer_fixture_uses_contract_defaults(self):
        c = {"id": "C1", "table_id": "T1", "dish_id": self.dish_id}
        s = self.session(customers=[c], stock=self.menu[self.dish_id]["recipe"], player={"pos": [2, 8]})
        c = s.snapshot()["customers"][0]
        self.assertEqual(c["reserved"], self.menu[self.dish_id]["recipe"])
        self.assertEqual(c["state"], "waiting")
        self.assertEqual(c["order_status"], "reserved")
        self.assertEqual(c["order_tick"], 0)
        self.assertEqual(c["eat_ticks_left"], 0)
        self.assertEqual(c["patience_ticks_left"], round(self.q["patience_s"] * self.hz))
        self.assertNotIn("order_id", c)
        self.assertNotIn("patience_max_ticks", c)
        row = self.step(s, True)[0]
        self.assertEqual(row["data"]["order_id"], "C1")

    def test_payment_and_leaving_order_follow_table_ids_instead_of_customer_ids(self):
        self.q["tables"] += [{"id": "T10", "pos": [10, 2]}, {"id": "T2", "pos": [11, 2]}]
        for state in ("waiting", "eating"):
            with self.subTest(state=state):
                options = ({"patience_ticks_left": 1} if state == "waiting" else
                           {"state": "eating", "order_status": "served", "reserved": {},
                            "tip": 12, "eat_ticks_left": 1})
                customers = [self.customer(id="C1", table_id="T10", **options),
                             self.customer(id="C10", table_id="T2", **options)]
                s = self.session(customers=customers, stock={"ca_loc": 2})
                rows = self.step(s)
                self.assertEqual([r["data"]["order_id"] for r in rows], ["C10", "C1"])
                if state == "waiting":
                    self.assertEqual([r["data"]["reputation"] for r in rows], [2.5, 2.0])

    def test_invalid_ownership_and_overreservation_exit_2_before_output(self):
        c = self.customer()
        invalid = [
            {"customers": [c], "stock": {}},
            {"customers": [dict(c, order_status="assigned", reserved={})]},
            {"customers": [dict(c, state="eating", order_status="served", reserved={}, eat_ticks_left=1)]},
            {"stoves": [{"id": "B1", "state": "ready", "dish": self.dish(c)}]},
            {"customers": [dict(c, order_status="assigned", reserved={})], "hand": self.dish(c),
             "stoves": [{"id": "B1", "state": "ready", "dish": self.dish(c)}]},
            {"customers": [dict(c, order_id="O1")], "stock": c["reserved"]},
            {"customers": [dict(c, order_status="assigned", reserved={})], "hand": self.dish(c),
             "stoves": [{"id": "B1", "state": "cooking", "dish": self.dish(c), "cook_ticks_left": 0}]},
            {"customers": [dict(c, state="eating", order_status="served", reserved={},
                                tip=12, eat_ticks_left=0)]},
            {"stoves": [{"id": "B1", "pos": [17, 8]}]},
            {"tables": [{"id": "T1", "pos": [9, -1]}]},
            {"customers": [dict(c, order_status="assigned", reserved={}, base_price=0)],
             "hand": dict(self.dish(c), base_price=0)},
        ]
        with Workdir() as w:
            for i, block in enumerate(invalid):
                with self.subTest(case=i):
                    sc = write_json(w.path(f"bad{i}.json"), {"quan": block})
                    out = w.path(f"bad{i}.jsonl")
                    code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "1",
                                             "--scenario", sc, "--out", out)
                    self.assertEqual(code, 2, err)
                    self.assertFalse(Path(out).exists())


class KitchenIntegration(unittest.TestCase):
    def test_headless_full_shift_events_snapshots_and_deterministic_bytes(self):
        with Workdir() as w:
            for i in (1, 2):
                code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "10800",
                                         "--scenario", str(FIXTURES / "p1_04_quan.json"),
                                         "--inputs", str(FIXTURES / "p1_04_inputs.json"),
                                         "--snapshot-every", "1", "--out", w.path(f"run{i}.jsonl"))
                self.assertEqual(code, 0, err)
            self.assertEqual(Path(w.path("run1.jsonl")).read_bytes(), Path(w.path("run2.jsonl")).read_bytes())
            rows = read_jsonl(w.path("run1.jsonl"))
            self.assertEqual([(r["tick"], r["name"]) for r in events(rows)],
                             [(1, "cook_started"), (361, "dish_ready"), (361, "dish_picked"),
                              (398, "served"), (998, "paid"), (10800, "quan_end")])
            by_tick = {r["tick"]: r for r in snapshots(rows)}
            self.assertEqual(by_tick[0]["stock"], {"ca_loc": 1})
            self.assertEqual(by_tick[1]["stoves"][0]["state"], "cooking")
            self.assertEqual(by_tick[360]["stoves"][0]["cook_ticks_left"], 1)
            self.assertEqual(by_tick[361]["hand"]["base_price"], 60)
            self.assertIsNone(by_tick[398]["hand"])
            self.assertEqual(by_tick[398]["customers"][0]["state"], "eating")
            self.assertEqual(by_tick[398]["money"], 0)
            self.assertEqual(by_tick[998]["money"], 72)
            self.assertEqual(by_tick[998]["reputation"], 3.2)
            self.assertEqual(by_tick[998]["customers"], [])
            self.assertEqual(rows[-1]["state"], "finished")
            self.assertEqual(rows[-1]["ticks"], 10800)

    def test_live_http_quan_input_snapshot_payment_and_restart(self):
        tuning = load_contract()["tuning"]
        scenario = json.loads((FIXTURES / "p1_04_quan.json").read_text(encoding="utf-8"))["quan"]
        c = scenario["customers"][0]
        c.update(order_status="assigned", reserved={})
        scenario["stock"] = {}
        scenario["hand"] = KitchenServing.dish(c)
        scenario["player"]["pos"] = [4, 8]
        scenario["time_left_ticks"] = 1
        game = LiveGame("quan", tuning, scenario, 42)
        server = LiveServer(game, port=0)
        # Real HTTP handler/input and the same Session as headless, with manual
        # ticks to avoid racing a one-tick closing fixture against wall time.
        from threading import Thread
        server._thread = Thread(target=server.httpd.serve_forever, daemon=True)
        server._thread.start()
        try:
            self.assertIn(b"<canvas", _get(server.url)[1])
            self.assertEqual(_post(server.url + "input", {"interact": True}), 200)
            with game._lock:
                game._tick_once()
            snap = json.loads(_get(server.url + "state")[1])
            self.assertIsNone(snap["error"])
            self.assertEqual(snap["money"], 72)
            self.assertEqual([r["name"] for r in snap["events"]], ["served", "paid", "quan_end"])
            self.assertEqual(_post(server.url + "restart", {}), 200)
            restart = json.loads(_get(server.url + "state")[1])
            self.assertEqual(restart["tick"], 0)
            self.assertEqual(restart["money"], 0)
            self.assertEqual(restart["customers"][0]["state"], "waiting")
            self.assertEqual(restart["hand"]["base_price"], 60)
            self.assertEqual(scenario["customers"][0]["state"], "waiting")
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
