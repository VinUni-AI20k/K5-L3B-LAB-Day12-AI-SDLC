"""Công cụ tools/check_no_hardcode.py (skill check-no-hardcode, HX-03): không báo oan trên repo sạch, bắt được số cứng."""

import os
import sys
import unittest

from helpers import ROOT, Workdir

sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_no_hardcode as tool  # noqa: E402


def scan(source, contract_numbers=frozenset({30, 0.5})):
    with Workdir() as w:
        path = w.path("rule.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(source)
        import pathlib
        return tool.scan_file(pathlib.Path(path), set(contract_numbers))


class NoHardcode(unittest.TestCase):
    def test_clean_repo_exits_0(self):
        self.assertEqual(tool.main(), 0)

    def test_flags_a_tuning_looking_number(self):
        found = scan("x = 42.5\n")
        self.assertEqual([(line, value) for line, value, _ in found], [(1, 42.5)])

    def test_accepts_contract_values_structural_constants_and_angle_wrap(self):
        self.assertEqual(scan("a = 30\nb = 0.5\nc = 0\nd = 1\ne = -1\nheading = angle % 360\n"), [])

    def test_allow_marker_and_annotations_are_ignored(self):
        self.assertEqual(scan("x = 42.5  # allow-hardcode\n"), [])
        self.assertEqual(scan("def f(a: 'int' = 1) -> float:\n    return a\n"), [])

    def test_negative_literal_is_reported_once_with_its_sign(self):
        found = scan("x = -7\n")
        self.assertEqual([(line, value) for line, value, _ in found], [(1, -7)])


if __name__ == "__main__":
    unittest.main()
