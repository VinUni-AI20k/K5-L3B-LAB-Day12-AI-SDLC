"""Hook chặn sửa file khóa và công cụ check_determinism của nhóm (HX-02, HX-04)."""

import importlib.util
import json
import os
import subprocess
import sys
import unittest

from helpers import ROOT, Workdir

HOOK = os.path.join(ROOT, ".agents", "hooks", "protect_locked_files.py")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_determinism  # noqa: E402

_spec = importlib.util.spec_from_file_location("protect_locked_files", HOOK)
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)


def payload(tool, path):
    return {"tool_name": tool, "tool_input": {"file_path": path}}


class ProtectLockedFiles(unittest.TestCase):
    def ask(self, tool, rel_or_abs):
        r = hook.decide(payload(tool, rel_or_abs), ROOT)
        return r and r["hookSpecificOutput"]["permissionDecision"]

    def test_locked_files_ask(self):
        for rel in ("game.contract.json", "docs/contracts/README.md", "docs/contracts/inventory.sample.json",
                    "chonoi/inventory.py"):
            self.assertEqual(self.ask("Edit", os.path.join(ROOT, *rel.split("/"))), "ask", rel)

    def test_write_and_relative_path(self):
        self.assertEqual(self.ask("Write", "game.contract.json"), "ask")
        self.assertEqual(self.ask("MultiEdit", "docs/contracts/README.md"), "ask")

    def test_windows_style_path(self):
        self.assertEqual(self.ask("Edit", ROOT + "\\docs\\contracts\\README.md"), "ask" if os.sep == "\\" else None)

    def test_other_files_pass(self):
        for rel in ("chonoi/sim/gather.py", "docs/clarify.md", "TEAM.md", "docs/contracts_notes.md",
                    "tests/test_smoke_p1.py"):
            self.assertIsNone(self.ask("Edit", os.path.join(ROOT, *rel.split("/"))), rel)

    def test_read_tools_and_outside_repo_pass(self):
        self.assertIsNone(self.ask("Read", os.path.join(ROOT, "game.contract.json")))
        self.assertIsNone(self.ask("Edit", os.path.join(os.path.dirname(ROOT), "game.contract.json")))

    def test_script_reads_stdin_and_prints_json(self):
        p = subprocess.run([sys.executable, HOOK], input=json.dumps(payload("Edit", "game.contract.json")),
                           capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": ROOT})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"], "ask")
        p = subprocess.run([sys.executable, HOOK], input=json.dumps(payload("Edit", "TEAM.md")),
                           capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": ROOT})
        self.assertEqual((p.returncode, p.stdout), (0, ""))

    def test_garbage_input_does_not_block(self):
        p = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True)
        self.assertEqual((p.returncode, p.stdout), (0, ""))

    def test_settings_json_wires_the_hook(self):
        with open(os.path.join(ROOT, ".claude", "settings.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        entry = cfg["hooks"]["PreToolUse"][0]
        self.assertIn("Edit", entry["matcher"])
        self.assertIn("protect_locked_files.py", entry["hooks"][0]["command"])


class CheckDeterminism(unittest.TestCase):
    def test_current_repo_is_deterministic(self):
        self.assertEqual(check_determinism.main(["--ticks", "300"]), 0)

    def test_first_diff(self):
        with Workdir() as w:
            a, b, c = w.path("a"), w.path("b"), w.path("c")
            for path, text in ((a, b"x\ny\nz\n"), (b, b"x\ny\nz\n"), (c, b"x\nQ\nz\n")):
                with open(path, "wb") as f:
                    f.write(text)
            self.assertIsNone(check_determinism.first_diff(a, b))
            self.assertEqual(check_determinism.first_diff(a, c), 2)


if __name__ == "__main__":
    unittest.main()
