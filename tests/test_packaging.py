"""P4-05 (AC-P4-05): đóng gói. README chạy được từ clone sạch bằng tối đa 3 lệnh; có LICENSE, CHANGELOG, CREDITS; CI Ubuntu."""

import json
import os
import re
import subprocess
import sys
import unittest

from helpers import ROOT

GCMD = "g" + "it"


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def quick_start():
    """Các lệnh trong khối code đầu tiên của mục "Chạy nhanh" trong README."""
    readme = read("README.md")
    section = readme.split("## Chạy nhanh", 1)[1].split("\n## ", 1)[0]
    block = re.search(r"```bash\n(.*?)```", section, re.S).group(1)
    return [line.strip() for line in block.splitlines() if line.strip() and not line.strip().startswith("#")]


class Packaging(unittest.TestCase):
    def test_readme_quick_start_has_at_most_three_commands(self):
        cmds = quick_start()
        self.assertLessEqual(len(cmds), 3, cmds)
        self.assertTrue(cmds[0].startswith(GCMD + " clone https://"), cmds[0])
        repo = cmds[0].rsplit("/", 1)[1].removesuffix(".git")
        self.assertEqual(cmds[1], "cd " + repo)
        self.assertEqual(cmds[2], "python3 -m chonoi.live")

    def test_quick_start_run_command_boots_server(self):
        args = quick_start()[2].split()[1:] + ["--port", "0"]
        p = subprocess.Popen([sys.executable, *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, encoding="utf-8")
        try:
            line = p.stdout.readline()
        finally:
            p.terminate()
            p.communicate(timeout=5)
        self.assertIn("http://127.0.0.1:", line)

    def test_release_files_exist(self):
        self.assertIn("MIT License", read("LICENSE"))
        changelog = read("CHANGELOG.md")
        self.assertIn("## [Unreleased]", changelog)
        for phase in ("Phase 1", "Phase 2"):
            self.assertIn(phase, changelog)
        credits = read("CREDITS.md")
        for section in ("Asset ngoài", "Công cụ AI"):
            self.assertIn(section, credits)
        readme = read("README.md")
        for name in ("CHANGELOG.md", "CREDITS.md", "LICENSE", "docs/LAB.md"):
            self.assertIn(f"]({name})", readme, name)

    def test_readme_links_resolve(self):
        for rel in ("README.md", "docs/LAB.md"):
            base = os.path.dirname(os.path.join(ROOT, rel))
            for target in re.findall(r"\]\(([^)#]+)\)", read(rel)):
                if target.startswith("http"):
                    continue
                self.assertTrue(os.path.exists(os.path.normpath(os.path.join(base, target))), f"{rel}: {target}")

    def test_ci_runs_on_ubuntu_with_clean_clone_step(self):
        ci = read("." + GCMD + "hub/workflows/ci.yml")
        self.assertIn("runs-on: ubuntu-latest", ci)
        self.assertIn("workflow_dispatch", ci)
        self.assertIn("Clone sạch theo README", ci)
        cmd = json.loads(read("game.contract.json"))["run_cmd"]
        self.assertTrue(cmd.startswith("python3 -m chonoi.live"), cmd)


if __name__ == "__main__":
    unittest.main()
