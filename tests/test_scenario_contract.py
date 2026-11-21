"""P1-08: kiểm mâu thuẫn scenario mức luật (quán) và các khóa còn lại của game.contract.json."""

import copy
import os
import unittest

from helpers import Workdir, run_headless, write_json

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput
from chonoi.scenario import check_reserved_within_stock, load_scenario

TUNING = load_contract()["tuning"]


def scenario_err(block):
    """Nạp scenario quan qua load_scenario; trả BadInput nếu bị từ chối, None nếu hợp lệ."""
    with Workdir() as w:
        path = write_json(w.path("s.json"), {"quan": block})
        try:
            load_scenario(path, "quan", TUNING)
        except BadInput as e:
            return e
    return None


def tuning_err(mutate):
    t = copy.deepcopy(TUNING)
    mutate(t)
    try:
        validate_tuning(t)
    except BadInput as e:
        return e
    return None


class QuanScenarioRules(unittest.TestCase):
    def test_valid_reservation_within_stock(self):
        block = {"stock": {"ca_loc": 2, "bong_sung": 2},
                 "customers": [{"id": "K1", "table_id": "T1", "reserved": {"ca_loc": 1}}]}
        self.assertIsNone(scenario_err(block))

    def test_reservation_over_stock_rejected(self):
        block = {"stock": {"ca_loc": 1}, "customers": [{"id": "K1", "table_id": "T1", "reserved": {"ca_loc": 2}}]}
        self.assertIn("vượt kho", str(scenario_err(block)))

    def test_reservations_of_two_customers_add_up(self):
        block = {"stock": {"ca_loc": 1}, "tables": [{"id": "T2", "pos": [5, 5]}],
                 "customers": [{"id": "K1", "table_id": "T1", "reserved": {"ca_loc": 1}},
                               {"id": "K2", "table_id": "T2", "reserved": {"ca_loc": 1}}]}
        self.assertIn("vượt kho", str(scenario_err(block)))

    def test_reserved_unknown_ingredient_rejected(self):
        block = {"stock": {"ca_loc": 1}, "customers": [{"id": "K1", "table_id": "T1", "reserved": {"ca_la": 1}}]}
        self.assertIsNotNone(scenario_err(block))

    def test_reputation_out_of_range(self):
        self.assertIsNone(scenario_err({"reputation": 5}))
        self.assertIsNotNone(scenario_err({"reputation": 5.5}))
        self.assertIsNotNone(scenario_err({"reputation": -1}))

    # --- PRD-0 mục D: payload món, đơn assigned/unfulfillable, khách eating, giữ chỗ khác công thức ---
    @staticmethod
    def payload(order_id="K1", dish_id="goi_bong_sung", price=40):
        return {"order_id": order_id, "dish_id": dish_id, "base_price": price}

    @staticmethod
    def customer(status="assigned", **extra):
        return {"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": status, **extra}

    def test_valid_assigned_order_on_stove_or_in_hand(self):
        pl = self.payload()
        stove = {"id": "B1", "state": "cooking", "dish": pl, "cook_ticks_left": 30}
        self.assertIsNone(scenario_err({"stoves": [stove], "customers": [self.customer(reserved={})]}))
        self.assertIsNone(scenario_err({"hand": pl, "customers": [self.customer(reserved={})]}))
        self.assertIsNone(scenario_err({"hand": None, "stoves": [{"id": "B1", "dish": None}]}))

    def test_dish_payload_must_have_exact_shape(self):
        for bad in ("goi_bong_sung", ["goi_bong_sung"], {"order_id": "K1"}, {**self.payload(), "extra": 1},
                    self.payload(dish_id="pho_bo"), self.payload(order_id=""), self.payload(price=-1),
                    self.payload(price=True)):
            err = scenario_err({"hand": bad, "customers": [self.customer(reserved={})]})
            self.assertIsInstance(err, BadInput, bad)  # BadInput (mã 2), không văng TypeError

    def test_payload_must_match_a_customer_and_their_dish(self):
        self.assertIn("không phải khách", str(scenario_err({"hand": self.payload("K9"),
                                                             "customers": [self.customer(reserved={})]})))
        self.assertIn("không khớp đơn", str(scenario_err({"hand": self.payload(dish_id="ca_loc_nuong_trui"),
                                                           "customers": [self.customer(reserved={})]})))

    def test_stove_and_hand_cannot_hold_the_same_order(self):
        pl = self.payload()
        err = scenario_err({"hand": pl, "stoves": [{"id": "B1", "dish": pl}], "customers": [self.customer(reserved={})]})
        self.assertIn("cùng giữ đơn", str(err))

    def test_assigned_needs_exactly_one_dish_and_empty_reservation(self):
        self.assertIn("đúng một món", str(scenario_err({"customers": [self.customer(reserved={})]})))
        pl = self.payload()
        err = scenario_err({"hand": pl, "stock": {"bong_sung": 2},
                            "customers": [self.customer(reserved={"bong_sung": 2})]})
        self.assertIn("phần giữ rỗng", str(err))

    def test_unfulfillable_has_no_dish_and_no_reservation(self):
        self.assertIsNone(scenario_err({"customers": [self.customer("unfulfillable", reserved={})]}))
        self.assertIsNotNone(scenario_err({"stock": {"bong_sung": 2},
                                           "customers": [self.customer("unfulfillable", reserved={"bong_sung": 2})]}))
        self.assertIsNotNone(scenario_err({"hand": self.payload(),
                                           "customers": [self.customer("unfulfillable", reserved={})]}))

    def test_reserved_must_equal_recipe(self):
        ok = self.customer("reserved", reserved={"bong_sung": 2})
        self.assertIsNone(scenario_err({"stock": {"bong_sung": 2}, "customers": [ok]}))
        bad = self.customer("reserved", reserved={"bong_sung": 1})
        self.assertIn("khác công thức", str(scenario_err({"stock": {"bong_sung": 2}, "customers": [bad]})))

    def test_order_status_must_be_known(self):
        self.assertIsNotNone(scenario_err({"customers": [self.customer("cooking", reserved={})]}))

    def test_eating_customer_must_be_served_with_timer_price_and_tip(self):
        eating = self.customer("served", state="eating", eat_ticks_left=100, base_price=40, tip=8)
        self.assertIsNone(scenario_err({"customers": [eating]}))
        for bad in (dict(eating, order_status="reserved"), dict(eating, eat_ticks_left=0),
                    {k: v for k, v in eating.items() if k != "tip"},
                    {k: v for k, v in eating.items() if k != "base_price"}):
            self.assertIsNotNone(scenario_err({"customers": [bad]}), bad)

    def test_stove_counters_must_not_be_negative(self):
        self.assertIsNotNone(scenario_err({"stoves": [{"id": "B1", "cook_ticks_left": -1}]}))


class ContractKeys(unittest.TestCase):
    def test_repo_contract_is_valid(self):
        validate_tuning(copy.deepcopy(TUNING))

    def test_start_pos_outside_bounds(self):
        self.assertIsNotNone(tuning_err(lambda t: t["quan"].update(start_pos=[99, 5])))

    def test_stove_and_table_layout(self):
        self.assertIsNotNone(tuning_err(lambda t: t["quan"].update(stoves=[])))
        self.assertIsNotNone(tuning_err(lambda t: t["quan"].update(tables=[{"id": "T1", "pos": [99, 2]}])))
        self.assertIsNotNone(tuning_err(
            lambda t: t["quan"].update(stoves=[{"id": "B1", "pos": [1, 1]}, {"id": "B1", "pos": [2, 2]}])))

    def test_carry_limit_and_reputation_order(self):
        self.assertIsNotNone(tuning_err(lambda t: t["quan"].update(carry_limit=0)))
        self.assertIsNotNone(tuning_err(lambda t: t["quan"].update(reputation_initial=9)))
        self.assertIsNotNone(tuning_err(lambda t: t["quan"].update(reputation_min=4, reputation_initial=3)))

    def test_menu_recipe(self):
        self.assertIsNotNone(tuning_err(lambda t: t["menu"]["goi_bong_sung"].update(recipe={})))
        self.assertIsNotNone(tuning_err(lambda t: t["menu"]["goi_bong_sung"].update(recipe={"ca_la": 1})))
        self.assertIsNotNone(tuning_err(lambda t: t["menu"]["goi_bong_sung"].update(recipe={"bong_sung": 0})))

    def test_score_multiplier(self):
        self.assertIsNotNone(tuning_err(lambda t: t["score"].update(reputation_multiplier=-1)))


class HeadlessExitCode(unittest.TestCase):
    def test_contradictory_scenario_exits_2(self):
        with Workdir() as w:
            sc = write_json(w.path("s.json"), {"quan": {"stock": {"ca_loc": 1},
                            "customers": [{"id": "K1", "table_id": "T1", "reserved": {"ca_loc": 5}}]}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "10",
                                     "--out", w.path("o.jsonl"), "--scenario", sc)
        self.assertEqual(code, 2, err)


class ReservedVsInventory(unittest.TestCase):
    """P1-08b: giữ chỗ nguyên liệu không được vượt kho nạp từ --inventory (PRD-0 mục D, mã 2)."""

    @staticmethod
    def customers(*reserved):
        return [{"id": f"K{i}", "table_id": f"T{i}", "dish_id": "goi_bong_sung", "reserved": r}
                for i, r in enumerate(reserved, 1)]

    def run_quan(self, w, customers, inventory):
        sc = write_json(w.path("s.json"), {"quan": {"customers": customers}})
        inv = write_json(w.path("inv.json"), {"items": inventory})
        out = w.path("o.jsonl")
        code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--out", out,
                                 "--scenario", sc, "--inventory", inv)
        return code, err, os.path.exists(out)

    def test_reservation_within_inventory_is_accepted(self):
        with Workdir() as w:
            code, err, wrote = self.run_quan(w, self.customers({"bong_sung": 2}), {"bong_sung": 2})
        self.assertEqual(code, 0, err)
        self.assertTrue(wrote)

    def test_reservation_over_inventory_exits_2_before_writing_output(self):
        with Workdir() as w:
            code, err, wrote = self.run_quan(w, self.customers({"bong_sung": 2}), {"bong_sung": 1})
        self.assertEqual(code, 2, err)
        self.assertIn("bong_sung = 2", err)  # tên nguyên liệu và số lượng (ASCII, không phụ thuộc mã hóa console)
        self.assertFalse(wrote)

    def test_ingredient_missing_from_inventory_counts_as_zero(self):
        with Workdir() as w:
            code, _, _ = self.run_quan(w, self.customers({"ca_loc": 1}), {"bong_sung": 5})
        self.assertEqual(code, 2)

    def test_check_function_adds_up_customers_and_accepts_exact_stock(self):
        two = {"customers": [{"reserved": {"ca_loc": 1}}, {"reserved": {"ca_loc": 1}}, {"id": "K3"}]}
        check_reserved_within_stock(two, {"ca_loc": 2})  # vừa đủ: không lỗi
        with self.assertRaises(BadInput):
            check_reserved_within_stock(two, {"ca_loc": 1})
        check_reserved_within_stock({}, {})  # không khách: không lỗi


if __name__ == "__main__":
    unittest.main()
