"""Kiểm phần Nhật Minh với dependency v1.1 trong thư mục tạm; không merge Git.

    python3 tools/check_nhat_minh.py

Ref mặc định là snapshot đã có contract v1.1 và Cá Sấu. Nếu object chưa có,
Integrator cung cấp ref tương đương qua --prefactor-ref. Script không fetch.
P3 dùng component probe; không tuyên bố migration kho/day/shop đã hoàn tất.
"""

import argparse
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY = "6187354e76eb31adec90ecd8dfea1d305d6d6427"
OVERLAY = ("chonoi/sim/fish.py", "chonoi/sim/current.py", "chonoi/sim/freshness.py",
           "chonoi/sim/monsters.py", "chonoi/sim/gather.py", "chonoi/sim/gather_actions.py",
           "tests/test_fish_rules.py", "tests/test_gather_extensions.py", "tests/gather_component_probe.py",
           "tests/test_gather_actions.py", "tests/test_gather_rules.py", "tests/test_net_day_rules.py")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefactor-ref", default=DEPENDENCY)
    parser.add_argument("--with-integration-patches", action="store_true",
                        help="apply proposed metadata/day/shop patches only in the temporary checkout")
    parser.add_argument("--out", type=Path, default=ROOT / "docs/proof/phase-2/all-assigned-v11.txt")
    args = parser.parse_args()
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--verify", args.prefactor_ref + "^{commit}"],
                                         cwd=ROOT, text=True, stderr=subprocess.PIPE).strip()
        archive = subprocess.check_output(["git", "archive", commit], cwd=ROOT, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        print("Dependency ref is unavailable locally; supply --prefactor-ref pointing to the v1.1 dependency.",
              file=sys.stderr)
        return error.returncode
    with tempfile.TemporaryDirectory(prefix="chonoi-nhat-minh-") as tmp:
        checkout = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(checkout, filter="data")
        for filename in OVERLAY:
            shutil.copy2(ROOT / filename, checkout / filename)
        if args.with_integration_patches:
            for filename in ("integrator-extension-hooks.patch", "integrator-net-data.patch"):
                patch = ROOT / "docs/proof/phase-2" / filename
                applied = subprocess.run(["git", "apply", str(patch)], cwd=checkout,
                                         capture_output=True, encoding="utf-8")
                if applied.returncode:
                    print(applied.stderr.encode("ascii", errors="backslashreplace").decode("ascii"))
                    return applied.returncode
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(("tests", ".")), PYTHONIOENCODING="utf-8")
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                                cwd=checkout, env=env, capture_output=True, encoding="utf-8")
    log = f"Dependency: {commit}\nLocal gather implementation/tests overlaid in a temporary checkout.\n"
    log += "Includes CLI fish tests and normalized gather component probes for net/freshness/current.\n"
    log += "Does not claim v1.2 inventory migration or complete day/shop integration.\n"
    command = "python3 tools/check_nhat_minh.py"
    if args.with_integration_patches:
        command += " --with-integration-patches"
        log += "Proposed Integrator patches applied ONLY in the temporary checkout for day/net CLI checks.\n"
    log += "Command: " + command + "\n"
    log += f"Exit code: {result.returncode}\n\n" + result.stdout + result.stderr
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(log, encoding="utf-8")
    output = (result.stdout + result.stderr).splitlines()
    if result.returncode:
        start = next((i for i, line in enumerate(output) if line.startswith("====")), 0)
        summary = "\n".join(output[start:])
    else:
        summary = "\n".join(output[-5:])
    print(summary.encode("ascii", errors="backslashreplace").decode("ascii"))
    print("UTF-8 log: " + str(args.out))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
