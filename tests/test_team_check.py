"""Test cho tools/check_team.py (kiểm danh sách thành viên)."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import check_team  # noqa: E402

GOOD = """# TEAM
| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| An | @an-nguyen | sim/gather | Integrator | quan |
| Bình | binh-tran | sim/quan | PO | gather |
| Chi | chi-le | client/ui | QA | quan |
| Dũng | dung-pham | qa | Scrum | ui |
"""


TEMPLATE_SAMPLE = """# TEAM
| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Nguyễn Văn A | handle-1 | sim/gather | Integrator | sim/quan |
| Trần Thị B | handle-2 | sim/quan | PO | sim/gather |
| Lê Văn C | … | client/ui | Scrum | sim/quan |
| Phạm Thị D | handle-4 | qa | QA lead | client/ui |
"""


class TeamCheck(unittest.TestCase):
    def test_good(self):
        m = check_team.parse_team(GOOD)
        self.assertEqual([x["handle"] for x in m], ["an-nguyen", "binh-tran", "chi-le", "dung-pham"])
        self.assertEqual(check_team.validate(m, 4, actor="an-nguyen", event="pull_request"), [])

    def test_template_is_rejected(self):
        # Kiểm tra mẫu chứa dấu placeholder '…' hoặc chưa điền handle hợp lệ bị từ chối
        m = check_team.parse_team(TEMPLATE_SAMPLE)
        errs = check_team.validate(m, 4)
        self.assertTrue(errs)
        self.assertTrue(any("chưa điền hoặc không hợp lệ" in e or "thiếu" in e for e in errs))

    def test_actual_team_file_is_valid(self):
        # Kiểm tra file TEAM.md thực tế của nhóm khớp team_size trong game.contract.json
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "TEAM.md"), encoding="utf-8") as f:
            m = check_team.parse_team(f.read())
        with open(os.path.join(root, "game.contract.json"), encoding="utf-8") as f:
            size = json.load(f).get("team_size", 5)
        self.assertEqual(check_team.validate(m, size), [])

    def test_wrong_size_duplicate_and_outsider(self):
        m = check_team.parse_team(GOOD)
        self.assertTrue(any("team_size" in e for e in check_team.validate(m, 5)))
        dup = check_team.parse_team(GOOD.replace("binh-tran", "an-nguyen"))
        self.assertTrue(any("trùng" in e for e in check_team.validate(dup, 4)))
        self.assertTrue(any("không có trong danh sách" in e for e in check_team.validate(m, 4, actor="ai-do", event="pull_request")))
        self.assertEqual(check_team.validate(m, 4, actor="ai-do", event="push"), [])
        self.assertEqual(check_team.validate(m, 4, actor="dependabot[bot]", event="pull_request"), [])

    def test_too_few_members(self):
        three = "\n".join(GOOD.splitlines()[:-1]) + "\n"
        self.assertTrue(any("4 đến 6" in e for e in check_team.validate(check_team.parse_team(three), 3)))


if __name__ == "__main__":
    unittest.main()
