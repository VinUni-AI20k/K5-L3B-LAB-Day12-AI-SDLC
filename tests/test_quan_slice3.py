"""P1-06: quán lát 3 — khách đến theo lịch, chọn bàn, giữ chỗ, no_dish, kiên nhẫn, đóng ca (PRD-0 mục D, E, F).

Số liệu đọc từ game.contract.json. Chạy trong tiến trình qua Session. Mặc định contract P1 chỉ có bàn T1,
nên test cần nhiều bàn dùng bản sao tuning có thêm T2.
"""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session

T = load_contract()["tuning"]
Q = T["quan"]
# Contract v1.1 có 2 bếp và 4 bàn; test lát 3 kiểm từng luật trên bố cục P1 (bếp B1, bàn T1) để kết quả không đổi
# theo số bàn. Test theo bố cục 4 bàn nằm ở phần việc quán của Phase 2 (P2-05).
LAYOUT_P1 = copy.deepcopy(T)
LAYOUT_P1["quan"]["stoves"] = [s for s in Q["stoves"] if s["id"] == "B1"]
LAYOUT_P1["quan"]["tables"] = [tb for tb in Q["tables"] if tb["id"] == "T1"]
HZ = T["tick_hz"]
FIRST = Q["first_customer_tick"]
EVERY = round(Q["customer_interval_s"] * HZ)
PATIENCE = round(Q["patience_s"] * HZ)


def tuning_with_tables(*extra):
    t = copy.deepcopy(LAYOUT_P1)
    t["quan"]["tables"] = t["quan"]["tables"] + [{"id": i, "pos": pos} for i, pos in extra]
    return t


def run(scenario, stock=None, ticks=1, tuning=LAYOUT_P1):
    sess = Session("quan", tuning, scenario, 1, inventory=stock)
    player = InputPlayer([])
    rows = []
    while sess.tick < ticks and not sess.done:
        rows.extend(sess.step(player.advance(sess.tick)))
    return sess, rows


def named(rows, name):
    return [r for r in rows if r["name"] == name]


class Arrival(unittest.TestCase):
    def test_first_customer_at_first_tick_then_every_interval(self):
        t2 = tuning_with_tables(("T2", [5, 5]), ("T3", [6, 5]))
        sess, rows = run({}, {"bong_sung": 6}, ticks=FIRST + 2 * EVERY + 1, tuning=t2)
        self.assertEqual([r["tick"] for r in named(rows, "customer_arrived")], [FIRST, FIRST + EVERY, FIRST + 2 * EVERY])

    def test_nothing_before_first_customer_tick(self):
        _, rows = run({}, {"bong_sung": 2}, ticks=FIRST - 1)
        self.assertEqual(rows, [])

    def test_takes_lowest_free_table_and_payload(self):
        t3 = tuning_with_tables(("T3", [6, 5]), ("T2", [5, 5]))  # T2 và T3 cùng trống: phải chọn id nhỏ hơn
        scenario = {"customers": [{"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung"}]}
        sess, rows = run(scenario, {"bong_sung": 4}, ticks=FIRST, tuning=t3)
        arrived = named(rows, "customer_arrived")[0]["data"]
        self.assertEqual(arrived["table_id"], "T2")  # T1 đã có khách
        self.assertEqual(set(arrived), {"order_id", "table_id", "dish_id"})
        self.assertEqual(arrived["dish_id"], "goi_bong_sung")

    def test_no_free_table_skips_the_turn_without_event(self):
        scenario = {"customers": [{"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung"}]}
        _, rows = run(scenario, {"bong_sung": 4}, ticks=FIRST + 5)
        self.assertEqual([r for r in rows if r["name"] in ("customer_arrived", "no_dish")], [])

    def test_random_customers_false_disables_spawning(self):
        _, rows = run({"random_customers": False}, {"bong_sung": 2}, ticks=FIRST + 5)
        self.assertEqual(rows, [])

    def test_new_customer_defaults_and_full_patience_counting_down_from_next_step(self):
        sess, rows = run({}, {"bong_sung": 2}, ticks=FIRST)
        c = sess.sim.customers[0]
        self.assertEqual((c["state"], c["order_status"], c["order_tick"]), ("waiting", "reserved", FIRST))
        self.assertEqual(c["patience_ticks_left"], PATIENCE)  # chưa giảm ở bước vừa sinh
        self.assertEqual(c["reserved"], T["menu"]["goi_bong_sung"]["recipe"])
        sess, _ = run({}, {"bong_sung": 2}, ticks=FIRST + 1)
        self.assertEqual(sess.sim.customers[0]["patience_ticks_left"], PATIENCE - 1)

    def test_id_continues_the_family_of_loaded_customers(self):
        t2 = tuning_with_tables(("T2", [5, 5]))
        scenario = {"customers": [{"id": "C7", "table_id": "T1", "dish_id": "goi_bong_sung"}]}
        sess, rows = run(scenario, {"bong_sung": 4}, ticks=FIRST, tuning=t2)
        self.assertEqual(named(rows, "customer_arrived")[0]["data"]["order_id"], "C8")


class StockAndNoDish(unittest.TestCase):
    def test_no_dish_event_has_empty_data_when_nothing_is_cookable(self):
        _, rows = run({}, None, ticks=FIRST)
        self.assertEqual([(r["tick"], r["data"]) for r in named(rows, "no_dish")], [(FIRST, {})])
        self.assertEqual(named(rows, "customer_arrived"), [])

    def test_only_dishes_with_enough_unreserved_stock_are_chosen(self):
        for stock, expected in (({"bong_sung": 2}, "goi_bong_sung"), ({"ca_loc": 1}, "ca_loc_nuong_trui")):
            _, rows = run({}, stock, ticks=FIRST)
            self.assertEqual(named(rows, "customer_arrived")[0]["data"]["dish_id"], expected, stock)

    def test_reservations_of_seated_customers_are_subtracted(self):
        t2 = tuning_with_tables(("T2", [5, 5]))
        scenario = {"customers": [{"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung"}]}  # giữ 2 bong_sung
        _, rows = run(scenario, {"bong_sung": 2}, ticks=FIRST, tuning=t2)
        self.assertEqual([r["data"] for r in named(rows, "no_dish")], [{}])
        _, rows = run(scenario, {"bong_sung": 4}, ticks=FIRST, tuning=t2)
        self.assertEqual(len(named(rows, "customer_arrived")), 1)


class Patience(unittest.TestCase):
    def one_customer(self, **extra):
        return {"random_customers": False, "customers": [{"id": "K1", "table_id": "T1",
                                                          "dish_id": "goi_bong_sung", **extra}]}

    def test_scenario_customer_gets_prd_defaults_and_leaves_after_patience(self):
        sess, rows = run(self.one_customer(), {"bong_sung": 2}, ticks=PATIENCE + 1)
        left = named(rows, "customer_left")
        self.assertEqual([r["tick"] for r in left], [PATIENCE])
        self.assertEqual(left[0]["data"], {"order_id": "K1", "table_id": "T1", "reason": "patience",
                                           "reputation": Q["reputation_initial"] + Q["left_reputation_delta"]})
        self.assertEqual(sess.sim.customers, [])  # rời bàn, nhả phần giữ

    def test_fixture_defaults_are_filled_in(self):
        sess, _ = run(self.one_customer(), {"bong_sung": 2}, ticks=1)
        c = sess.sim.customers[0]
        self.assertEqual((c["state"], c["order_tick"], c["order_status"]), ("waiting", 0, "reserved"))
        self.assertEqual(c["reserved"], T["menu"]["goi_bong_sung"]["recipe"])

    def test_reputation_is_clamped_at_the_minimum(self):
        scenario = {**self.one_customer(patience_ticks_left=1), "reputation": 0}
        sess, rows = run(scenario, {"bong_sung": 2}, ticks=2)
        self.assertEqual(sess.sim.reputation, Q["reputation_min"])
        self.assertEqual(named(rows, "customer_left")[0]["data"]["reputation"], Q["reputation_min"])

    def test_leaving_frees_the_table_for_the_same_tick_arrival(self):
        # PRD-0 mục F: khách rời (bước 4) trước lượt sinh khách (bước 5) trong cùng tick
        scenario = {"customers": [{"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung",
                                   "patience_ticks_left": FIRST}]}
        _, rows = run(scenario, {"bong_sung": 4}, ticks=FIRST)
        self.assertEqual([r["name"] for r in rows], ["customer_left", "customer_arrived"])

    def test_leaving_drops_the_dish_of_that_order_from_stove_and_hand(self):
        payload = {"order_id": "K1", "dish_id": "goi_bong_sung", "base_price": 40}
        scenario = {**self.one_customer(order_status="assigned", reserved={}, patience_ticks_left=1),
                    "stoves": [{"id": "B1", "state": "cooking", "dish": payload, "cook_ticks_left": 500}]}
        sess, _ = run(scenario, {"bong_sung": 2}, ticks=2)
        stove = sess.sim.stoves[0]
        self.assertEqual((stove["state"], stove["dish"]), ("idle", None))
        scenario = {**self.one_customer(order_status="assigned", reserved={}, patience_ticks_left=1), "hand": payload}
        sess, _ = run(scenario, {"bong_sung": 2}, ticks=2)
        self.assertIsNone(sess.sim.hand)


class ClosingAndStoves(unittest.TestCase):
    def test_closing_makes_waiting_customers_leave_without_reputation_loss_before_quan_end(self):
        scenario = {"time_left_ticks": 5, "random_customers": False,
                    "customers": [{"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung"}]}
        sess, rows = run(scenario, {"bong_sung": 2}, ticks=10)
        self.assertEqual([r["name"] for r in rows], ["customer_left", "quan_end"])
        left = rows[0]["data"]
        self.assertEqual((left["reason"], left["reputation"]), ("closing", Q["reputation_initial"]))
        self.assertEqual(sess.sim.reputation, Q["reputation_initial"])
        self.assertEqual(sess.sim.customers, [])

    def test_no_new_customer_on_the_closing_tick(self):
        _, rows = run({"time_left_ticks": FIRST}, {"bong_sung": 2}, ticks=FIRST)
        self.assertEqual([r["name"] for r in rows], ["quan_end"])

    def test_ready_ticks_count_up_only_for_dishes_already_ready_at_step_start(self):
        payload = {"order_id": "K1", "dish_id": "goi_bong_sung", "base_price": 40}
        cust = [{"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned",
                 "reserved": {}}]
        ready = {"random_customers": False, "customers": cust,
                 "stoves": [{"id": "B1", "state": "ready", "dish": payload, "ready_ticks": 5}]}
        sess, _ = run(ready, None, ticks=10)
        self.assertEqual(sess.sim.stoves[0]["ready_ticks"], 15)
        cooking = {"random_customers": False, "customers": cust,
                   "stoves": [{"id": "B1", "state": "cooking", "dish": payload, "cook_ticks_left": 3}]}
        sess, _ = run(cooking, None, ticks=3)
        stove = sess.sim.stoves[0]
        self.assertEqual((stove["state"], stove["ready_ticks"]), ("ready", 0))  # vừa chín: chưa tăng
        sess, _ = run(cooking, None, ticks=5)
        self.assertEqual(sess.sim.stoves[0]["ready_ticks"], 2)


if __name__ == "__main__":
    unittest.main()
