"""Kiểm tra số đàn cá ban đầu theo contract Phase 2."""

import copy
import json
import unittest

from chonoi.contract import DEFAULT_PATH, _validate_gather
from chonoi.errors import BadInput


class FishInitialContractTests(unittest.TestCase):
    def test_fish_initial_must_be_integer_eight(self):
        with open(DEFAULT_PATH, encoding="utf-8") as f:
            gather = json.load(f)["tuning"]["gather"]
        for value in (8, 7, 9, 8.0, True, None, []):
            with self.subTest(value=value):
                candidate = copy.deepcopy(gather)
                candidate["fish_initial"] = value
                if type(value) is int and value == 8:
                    _validate_gather(candidate)
                else:
                    with self.assertRaises(BadInput):
                        _validate_gather(candidate)


if __name__ == "__main__":
    unittest.main()
