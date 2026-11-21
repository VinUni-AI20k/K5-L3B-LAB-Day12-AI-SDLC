"""P1-07: quán lát 4 — nấu, bưng, phục vụ, trả tiền, boa, uy tín, hết ca (PRD-0 mục E, F).

Số liệu đọc từ game.contract.json. Chạy trong tiến trình qua Session. Để một người đứng được gần cả bếp lẫn bàn,
test dùng bản sao tuning đặt bếp B1 ở [9, 3] (gần bàn T1 ở [9, 2]); người chơi đứng ở [9, 3.2] thì bếp gần hơn bàn,
đứng ở [9, 1.8] thì bàn gần hơn bếp. interact_radius là 1.5.
"""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session

T = load_contract()["tuning"]
Q = T["quan"]
HZ = T["tick_hz"]
MENU = T["menu"]
NEAR_STOVE = [9, 3.2]
NEAR_TABLE = [9, 1.8]
COOK = round(MENU["goi_bong_sung"]["cook_s"] * HZ)
EAT = round(Q["eat_s"] * HZ)
PATIENCE = round(Q["patience_s"] * HZ)
PRICE = MENU["goi_bong_sung"]["price"]
TIP = int(PRICE * Q["tip_rate"])  # 40 * 0.2 = 8 (số nguyên, không sát ngưỡng làm tròn)


def tuning(extra_tables=(), stoves=(("B1", [9, 3]),), edit=None):
    t = copy.deepcopy(T)
    t["quan"]["stoves"] = [{"id": i, "pos": pos} for i, pos in stoves]
    base = [tb for tb in t["quan"]["tables"] if tb["id"] == "T1"]  # bố cục P1: một bàn T1, thêm bàn qua extra_tables
    t["quan"]["tables"] = base + [{"id": i, "pos": pos} for i, pos in extra_tables]
    if edit:
        edit(t)
    return t


def taps(*ticks):
    """Nhấn interact (cạnh lên) ở từng tick, nhả ngay tick kế."""
    frames = []
    for k in ticks:
        frames += [{"tick": k, "interact": True}, {"tick": k + 1, "interact": False}]
    return frames


def run(scenario, frames=(), ticks=1, stock=None, t=None):
    sess = Session("quan", t or tuning(), {"random_customers": False, **scenario}, 1, inventory=stock)
    player = InputPlayer(sorted(frames, key=lambda f: f["tick"]))
    rows = []
    while sess.tick < ticks and not sess.done:
        rows.extend(sess.step(player.advance(sess.tick)))
    return sess, rows


def named(rows, name):
    return [r for r in rows if r["name"] == name]


def cust(cid="K1", table="T1", dish="goi_bong_sung", **extra):
    return {"id": cid, "table_id": table, "dish_id": dish, **extra}


def payload(order="K1", dish="goi_bong_sung", price=PRICE):
    return {"order_id": order, "dish_id": dish, "base_price": price}


def assigned(cid="K1", table="T1", **extra):
    return cust(cid, table, order_status="assigned", reserved={}, **extra)


def eating(cid="K1", table="T1", left=EAT, price=PRICE, tip=TIP, **extra):
    return cust(cid, table, state="eating", order_status="served", eat_ticks_left=left, base_price=price, tip=tip,
                reserved={}, **extra)


class Cooking(unittest.TestCase):
    def test_start_cooking_payload_and_effects(self):
        sess, rows = run({"player": {"pos": NEAR_STOVE}, "customers": [cust()]}, taps(0), stock={"bong_sung": 2})
        self.assertEqual([(r["tick"], r["name"], r["data"]) for r in rows], [
            (1, "cook_started", {"stove_id": "B1", "order_id": "K1", "dish_id": "goi_bong_sung",
                                 "items": ["bong_sung", "bong_sung"], "base_price": PRICE})])
        c, stove = sess.sim.customers[0], sess.sim.stoves[0]
        self.assertEqual((c["order_status"], c["reserved"]), ("assigned", {}))
        self.assertEqual((stove["state"], stove["dish"]), ("cooking", payload()))
        self.assertEqual((stove["cook_ticks_left"], stove["ready_ticks"]), (COOK, 0))
        self.assertEqual(sess.sim.stock.get("bong_sung", 0), 0)

    def test_takes_oldest_order_then_lowest_table(self):
        two = ((("T2", [13, 2]),))
        scenario = {"player": {"pos": NEAR_STOVE},
                    "customers": [cust("K1", "T1", order_tick=5), cust("K2", "T2", order_tick=2)]}
        _, rows = run(scenario, taps(0), stock={"bong_sung": 4}, t=tuning(extra_tables=two))
        self.assertEqual(named(rows, "cook_started")[0]["data"]["order_id"], "K2")
        scenario["customers"] = [cust("K1", "T1", order_tick=3), cust("K2", "T2", order_tick=3)]
        _, rows = run(scenario, taps(0), stock={"bong_sung": 4}, t=tuning(extra_tables=two))
        self.assertEqual(named(rows, "cook_started")[0]["data"]["order_id"], "K1")

    def test_missing_stock_skips_the_turn(self):
        sess, rows = run({"player": {"pos": NEAR_STOVE}, "customers": [cust()]}, taps(0), stock={})
        self.assertEqual(rows, [])
        self.assertEqual(sess.sim.stoves[0]["state"], "idle")
        self.assertEqual(sess.sim.customers[0]["order_status"], "reserved")

    def test_ingredients_are_not_refunded_when_the_customer_leaves(self):
        scenario = {"player": {"pos": NEAR_STOVE}, "customers": [cust(patience_ticks_left=3)]}
        sess, rows = run(scenario, taps(0), ticks=5, stock={"bong_sung": 2})
        self.assertEqual([r["data"]["reason"] for r in named(rows, "customer_left")], ["patience"])
        self.assertEqual(sess.sim.stock.get("bong_sung", 0), 0)
        self.assertEqual((sess.sim.stoves[0]["state"], sess.sim.stoves[0]["dish"]), ("idle", None))

    def test_order_without_known_dish_is_not_cooked_and_does_not_crash(self):
        scenario = {"player": {"pos": NEAR_STOVE}, "customers": [{"id": "K1", "table_id": "T1"}]}
        sess, rows = run(scenario, taps(0), stock={"bong_sung": 2})
        self.assertEqual(rows, [])
        self.assertEqual(sess.sim.stoves[0]["state"], "idle")

    def test_dish_ready_after_cook_time_and_ready_ticks_count_from_the_next_step(self):
        sess, rows = run({"player": {"pos": NEAR_STOVE}, "customers": [cust()]}, taps(0), ticks=1 + COOK,
                         stock={"bong_sung": 2})
        ready = named(rows, "dish_ready")
        self.assertEqual([(r["tick"], r["data"]) for r in ready],
                         [(1 + COOK, {"stove_id": "B1", "order_id": "K1", "dish_id": "goi_bong_sung"})])
        self.assertEqual((sess.sim.stoves[0]["state"], sess.sim.stoves[0]["ready_ticks"]), ("ready", 0))
        sess, _ = run({"player": {"pos": NEAR_STOVE}, "customers": [cust()]}, taps(0), ticks=1 + COOK + 5,
                      stock={"bong_sung": 2})
        self.assertEqual(sess.sim.stoves[0]["ready_ticks"], 5)

    def test_pick_up_needs_a_free_hand(self):
        ready = {"id": "B1", "state": "ready", "dish": payload(), "ready_ticks": 3}
        scenario = {"player": {"pos": NEAR_STOVE}, "stoves": [ready], "customers": [assigned()]}
        sess, rows = run(scenario, taps(0))
        self.assertEqual([r["data"] for r in named(rows, "dish_picked")],
                         [{"stove_id": "B1", "order_id": "K1", "dish_id": "goi_bong_sung"}])
        self.assertEqual(sess.sim.hand, payload())
        self.assertEqual((sess.sim.stoves[0]["state"], sess.sim.stoves[0]["dish"]), ("idle", None))
        busy = {**scenario, "hand": payload("K9"), "customers": [assigned(), assigned("K9", "T2")]}
        sess, rows = run(busy, taps(0), t=tuning(extra_tables=(("T2", [13, 2]),)))
        self.assertEqual(named(rows, "dish_picked"), [])
        self.assertEqual(sess.sim.stoves[0]["state"], "ready")


class Interact(unittest.TestCase):
    def test_only_one_interact_per_step(self):
        stoves = (("B1", [9, 3]), ("B2", [9, 3]))
        scenario = {"player": {"pos": NEAR_STOVE}, "customers": [cust("K1", "T1"), cust("K2", "T2")]}
        t = tuning(extra_tables=(("T2", [13, 2]),), stoves=stoves)
        sess, rows = run(scenario, taps(0), stock={"bong_sung": 4}, t=t)
        self.assertEqual([r["data"]["stove_id"] for r in named(rows, "cook_started")], ["B1"])
        self.assertEqual(sess.sim.stoves[1]["state"], "idle")

    def test_nearest_object_wins(self):
        scenario = {"player": {"pos": NEAR_TABLE}, "hand": payload(), "customers": [assigned()]}
        _, rows = run(scenario, taps(0))
        self.assertEqual(len(named(rows, "served")), 1)

    def test_stove_wins_over_table_at_equal_distance(self):
        scenario = {"player": {"pos": [9, 2.5]}, "hand": payload(), "customers": [assigned()]}
        sess, rows = run(scenario, taps(0))
        self.assertEqual(named(rows, "served"), [])  # bếp (idle, không có đơn) được chọn trước nên bỏ lượt
        self.assertEqual(sess.sim.hand, payload())

    def test_empty_table_chosen_as_nearest_wastes_the_turn(self):
        stoves = (("B1", [9, 2.4]),)
        t = tuning(extra_tables=(("T2", [9, 1.1]),), stoves=stoves)
        scenario = {"player": {"pos": [9, 1.2]}, "customers": [cust("K1", "T1")]}
        sess, rows = run(scenario, taps(0), stock={"bong_sung": 2}, t=t)
        self.assertEqual(rows, [])  # T2 (trống) gần nhất; bếp xa hơn nên không được chọn
        self.assertEqual(sess.sim.stoves[0]["state"], "idle")

    def test_object_out_of_radius_is_ignored(self):
        scenario = {"player": {"pos": [9, 3 + Q["interact_radius"] + 0.5]}, "customers": [cust()]}
        sess, rows = run(scenario, taps(0), stock={"bong_sung": 2})
        self.assertEqual(rows, [])


class Serving(unittest.TestCase):
    def test_serve_matching_order(self):
        scenario = {"player": {"pos": NEAR_TABLE}, "hand": payload(), "customers": [assigned()]}
        sess, rows = run(scenario, taps(0))
        self.assertEqual([(r["tick"], r["data"]) for r in named(rows, "served")], [
            (1, {"order_id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung",
                 "patience_ticks_left": PATIENCE - 1, "base_price": PRICE, "tip": TIP})])
        c = sess.sim.customers[0]
        self.assertEqual((c["state"], c["order_status"], c["eat_ticks_left"]), ("eating", "served", EAT))
        self.assertEqual((c["base_price"], c["tip"]), (PRICE, TIP))
        self.assertIsNone(sess.sim.hand)

    def test_wrong_order_is_ignored(self):
        scenario = {"player": {"pos": NEAR_TABLE}, "hand": payload("K2"), "customers": [assigned()]}
        sess, rows = run(scenario, taps(0))
        self.assertEqual(named(rows, "served"), [])
        self.assertEqual(sess.sim.hand, payload("K2"))
        self.assertEqual(sess.sim.customers[0]["state"], "waiting")

    def test_tip_needs_half_of_the_patience_left_after_the_timer_step(self):
        full = round(Q["patience_s"] * HZ)
        half = round(full * Q["tip_min_patience_ratio"])
        for left_before, expected in ((half + 1, TIP), (half, 0)):  # bước 1 giảm 1 tick trước khi tính
            scenario = {"player": {"pos": NEAR_TABLE}, "hand": payload(),
                        "customers": [assigned(patience_ticks_left=left_before)]}
            _, rows = run(scenario, taps(0))
            self.assertEqual(named(rows, "served")[0]["data"]["tip"], expected, left_before)

    def test_tip_uses_exact_arithmetic(self):
        # 100 * 0.29 = 28.999999999999996 trong số thực: phải ra 29
        t = tuning(edit=lambda tt: tt["quan"].update(tip_rate=0.29))
        scenario = {"player": {"pos": NEAR_TABLE}, "hand": payload(price=100), "customers": [assigned()]}
        _, rows = run(scenario, taps(0), t=t)
        self.assertEqual(named(rows, "served")[0]["data"]["tip"], 29)

    def test_serving_on_the_tick_patience_reaches_zero_is_valid(self):
        scenario = {"player": {"pos": NEAR_TABLE}, "hand": payload(),
                    "customers": [assigned(patience_ticks_left=1)]}
        sess, rows = run(scenario, taps(0))
        self.assertEqual([r["name"] for r in rows], ["served"])  # không bị rời bàn cùng tick
        self.assertEqual(rows[0]["data"]["tip"], 0)  # kiên nhẫn 0 nên không đạt ngưỡng boa
        self.assertEqual(sess.sim.customers[0]["state"], "eating")


class Payment(unittest.TestCase):
    def test_paid_when_eating_finishes(self):
        scenario = {"customers": [eating(left=3)]}
        sess, rows = run(scenario, ticks=5)
        self.assertEqual([(r["tick"], r["data"]) for r in named(rows, "paid")], [
            (3, {"order_id": "K1", "table_id": "T1", "base_price": PRICE, "tip": TIP, "amount": PRICE + TIP,
                 "reason": "finished_eating"})])
        sim = sess.sim
        self.assertEqual((sim.money, sim.earned, sim.shift_earned), (PRICE + TIP,) * 3)
        self.assertEqual(sim.customers, [])
        self.assertIsNone(sim.snapshot()["tables"][0]["customer_id"])
        self.assertAlmostEqual(sim.reputation, Q["reputation_initial"] + Q["tip_reputation"])

    def test_no_reputation_bonus_without_a_tip(self):
        sess, _ = run({"customers": [eating(left=1, tip=0)]}, ticks=2)
        self.assertEqual(sess.sim.reputation, Q["reputation_initial"])
        self.assertEqual(sess.sim.money, PRICE)

    def test_reputation_is_capped_at_the_maximum(self):
        sess, _ = run({"reputation": Q["reputation_max"], "customers": [eating(left=1)]}, ticks=2)
        self.assertEqual(sess.sim.reputation, Q["reputation_max"])

    def test_customers_are_settled_in_table_order(self):
        t = tuning(extra_tables=(("T2", [13, 2]), ("T3", [14, 2])))
        scenario = {"customers": [eating("K3", "T3", left=1), eating("K1", "T1", left=1), eating("K2", "T2", left=1)]}
        _, rows = run(scenario, ticks=2, t=t)
        self.assertEqual([r["data"]["table_id"] for r in named(rows, "paid")], ["T1", "T2", "T3"])

    def test_waiting_customers_are_not_paid(self):
        sess, rows = run({"customers": [cust()]}, ticks=PATIENCE - 1)
        self.assertEqual(named(rows, "paid"), [])
        self.assertEqual(sess.sim.money, 0)


class Closing(unittest.TestCase):
    def test_eating_pays_and_waiting_leaves_before_quan_end(self):
        t = tuning(extra_tables=(("T2", [13, 2]),))
        scenario = {"time_left_ticks": 3, "customers": [cust("K2", "T2"), eating("K1", "T1", left=100)]}
        sess, rows = run(scenario, ticks=10, t=t)
        self.assertEqual([r["name"] for r in rows], ["paid", "customer_left", "quan_end"])
        self.assertEqual(rows[0]["data"]["reason"], "closing")
        self.assertEqual(rows[1]["data"]["reason"], "closing")
        end = rows[2]["data"]
        self.assertEqual((end["reason"], end["money"], end["earned"], end["shift_earned"]),
                         ("time", PRICE + TIP, PRICE + TIP, PRICE + TIP))
        self.assertAlmostEqual(end["reputation"], Q["reputation_initial"] + Q["tip_reputation"])  # không trừ uy tín
        self.assertTrue(sess.done)

    def test_dish_served_on_the_closing_step_pays_at_once(self):
        scenario = {"time_left_ticks": 1, "player": {"pos": NEAR_TABLE}, "hand": payload(),
                    "customers": [assigned()]}
        _, rows = run(scenario, taps(0), ticks=3)
        self.assertEqual([r["name"] for r in rows], ["served", "paid", "quan_end"])
        self.assertEqual(rows[1]["data"]["reason"], "closing")
        self.assertEqual(rows[1]["data"]["amount"], PRICE + TIP)

    def test_quan_end_is_the_last_event_and_ends_the_session(self):
        sess, rows = run({"time_left_ticks": 2}, ticks=10)
        self.assertEqual([r["name"] for r in rows], ["quan_end"])
        self.assertEqual(sess.tick, 2)
        self.assertTrue(sess.done)


class FullCycle(unittest.TestCase):
    def test_cook_pick_serve_eat_pay(self):
        frames = taps(*range(0, 246, 2)) + [{"tick": 250, "move": [0, -1]}, {"tick": 270, "move": [0, 0]}]
        frames += taps(*range(300, 1000, 2))
        sess, rows = run({"player": {"pos": [9, 2.5]}, "customers": [cust()]}, frames, ticks=1500,
                         stock={"bong_sung": 2})
        self.assertEqual([(r["tick"], r["name"]) for r in rows], [
            (1, "cook_started"), (1 + COOK, "dish_ready"), (1 + COOK, "dish_picked"),
            (301, "served"), (301 + EAT, "paid")])
        sim = sess.sim
        self.assertEqual((sim.money, sim.earned), (PRICE + TIP, PRICE + TIP))
        self.assertIsNone(sim.hand)
        self.assertEqual(sim.customers, [])
        self.assertAlmostEqual(sim.reputation, Q["reputation_initial"] + Q["tip_reputation"])


if __name__ == "__main__":
    unittest.main()
