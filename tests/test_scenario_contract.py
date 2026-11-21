"""P1-08: kiểm mâu thuẫn scenario mức luật (quán) và các khóa còn lại của game.contract.json."""

import copy
import unittest

from helpers import Workdir, run_headless, write_json

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput
from chonoi.scenario import load_scenario

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

    def test_stove_dish_must_be_in_menu(self):
        self.assertIsNone(scenario_err({"stoves": [{"id": "B1", "dish": "goi_bong_sung", "cook_ticks_left": 30}]}))
        self.assertIsNotNone(scenario_err({"stoves": [{"id": "B1", "dish": "pho_bo"}]}))
        # sai kiểu phải bị từ chối bằng BadInput (mã 2), không được văng TypeError
        self.assertIsNotNone(scenario_err({"stoves": [{"id": "B1", "dish": ["goi_bong_sung"]}]}))
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


if __name__ == "__main__":
    unittest.main()
