"""Kiểm dải hợp lệ tuning trong chonoi/contract.py (HoangHongNgo, T7).

Contract chuẩn phải qua; mỗi ca sửa một khóa ra ngoài dải phải bị từ chối (BadInput -> headless mã 2).
"""

import copy
import json
import os
import unittest

from chonoi.contract import DEFAULT_PATH, load_contract, validate_tuning
from chonoi.errors import BadInput


def base_tuning():
    with open(DEFAULT_PATH, encoding="utf-8") as f:
        return json.load(f)["tuning"]


def mutate(fn):
    t = copy.deepcopy(base_tuning())
    fn(t)
    return t


class TestTuningRanges(unittest.TestCase):
    def test_default_contract_valid(self):
        load_contract()
        validate_tuning(base_tuning())

    def assertRejected(self, fn):
        with self.assertRaises(BadInput):
            validate_tuning(mutate(fn))

    def test_tick_hz_must_be_60(self):
        self.assertRejected(lambda t: t.update(tick_hz=30))

    def test_score_multiplier(self):
        self.assertRejected(lambda t: t["score"].update(reputation_multiplier=-1))
        self.assertRejected(lambda t: t.pop("score"))

    def test_gather_ranges(self):
        self.assertRejected(lambda t: t["gather"].update(duration_s=59))
        self.assertRejected(lambda t: t["gather"].update(hold_capacity=3))
        self.assertRejected(lambda t: t["gather"].update(oxygen_max_s=121))
        self.assertRejected(lambda t: t["gather"].update(ramp_max_ticks=7))

    def test_gather_range_edges_accepted(self):
        validate_tuning(mutate(lambda t: t["gather"].update(duration_s=60)))
        validate_tuning(mutate(lambda t: t["gather"].update(duration_s=600)))

    def test_quan_ranges(self):
        self.assertRejected(lambda t: t["quan"].update(patience_s=19))
        self.assertRejected(lambda t: t["quan"].update(tip_min_patience_ratio=0))
        self.assertRejected(lambda t: t["quan"].update(carry_limit=0))

    def test_stoves_tables(self):
        self.assertRejected(lambda t: t["quan"].update(stoves=[]))
        self.assertRejected(lambda t: t["quan"].update(tables=[{"id": "T1", "pos": [99, 2]}]))
        self.assertRejected(lambda t: t["quan"].update(tables=[{"id": "B1", "pos": [9, 2]}]))  # trùng id bếp
        self.assertRejected(lambda t: t["quan"].update(start_pos=[-1, 5]))

    def test_reputation(self):
        self.assertRejected(lambda t: t["quan"].update(reputation_initial=6))
        self.assertRejected(lambda t: t["quan"].update(reputation_min=5, reputation_max=5))

    def test_menu_recipe(self):
        self.assertRejected(lambda t: t.update(menu={}))
        self.assertRejected(lambda t: t["menu"]["goi_bong_sung"].update(recipe={"bong_sung": 0}))
        self.assertRejected(lambda t: t["menu"]["goi_bong_sung"].update(recipe={"ca_map": 1}))
        self.assertRejected(lambda t: t["menu"]["goi_bong_sung"].update(price=0))


class TestHeadlessExit2(unittest.TestCase):
    def test_bad_tuning_exit_2(self):
        """Contract sai dải -> headless trả mã 2 (chạy trên bản sao tạm của repo không cần thiết: gọi hàm)."""
        import io
        import tempfile
        from unittest import mock

        from chonoi import headless

        with open(DEFAULT_PATH, encoding="utf-8") as f:
            bad = json.load(f)
        bad["tuning"]["gather"]["hold_capacity"] = 99
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(bad, f)
            out = os.path.join(d, "o.jsonl")
            orig = load_contract
            with mock.patch.object(headless, "load_contract", lambda: orig(p)), \
                    mock.patch("sys.stderr", new_callable=io.StringIO):
                code = headless.main(["--mode", "gather", "--seed", "1", "--ticks", "10", "--out", out])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
