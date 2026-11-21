"""Chạy toàn bộ kiểm chứng Phase 1 và (tuỳ chọn) ghi bằng chứng vào docs/proof/phase-1/.

    python3 tools/run_checks.py            # chỉ in kết quả
    python3 tools/run_checks.py --proof    # ghi thêm docs/proof/phase-1/checks-<commit>.txt

Các bước: unittest · headless gather chạy 2 lần so từng byte · smoke hai tiến trình (gather -> kho -> quan)
· tools/check_team.py. Lệnh headless lấy từ game.contract.json, ghi đè được bằng CHONOI_HEADLESS_CMD.
Mã thoát 0 khi mọi bước đạt.
"""

import json
import os
import shlex
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROOF_DIR = os.path.join(ROOT, "docs", "proof", "phase-1")


def headless_cmd() -> list:
    override = os.environ.get("CHONOI_HEADLESS_CMD")
    if override:
        return shlex.split(override)
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return shlex.split(json.load(f)["headless_cmd"])


def sh(args: list, env: dict | None = None) -> tuple[int, str]:
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=env)
    return p.returncode, (p.stdout + p.stderr).strip()


def check_unittest() -> tuple[bool, str]:
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([os.path.join(ROOT, "tests"), ROOT]))
    code, out = sh([sys.executable, "-m", "unittest", "discover", "-s", "tests"], env=env)
    return code == 0, " ".join(out.splitlines()[-3:]) if out else ""


def check_determinism(tmp: str) -> tuple[bool, str]:
    outs = []
    for i in (1, 2):
        path = os.path.join(tmp, f"det{i}.jsonl")
        code, err = sh([*headless_cmd(), "--mode", "gather", "--seed", "1", "--ticks", "600", "--out", path])
        if code != 0:
            return False, f"lần {i} mã {code}: {err}"
        with open(path, "rb") as f:
            outs.append(f.read())
    same = outs[0] == outs[1]
    return same, f"gather seed 1, 600 tick: {len(outs[0])} byte, giống nhau={same}"


def check_two_process(tmp: str) -> tuple[bool, str]:
    """Smoke hộp đen ở cuối Test Contract (mục G)."""
    def p(name: str) -> str:
        return os.path.join(tmp, name)

    with open(p("dock.json"), "w", encoding="utf-8") as f:
        # v1.2 (Ticket-03): giỏ là mảng cá thể {id, kind, fresh}
        json.dump({"gather": {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100},
                                       {"id": "I2", "kind": "bong_sung", "fresh": 100},
                                       {"id": "I3", "kind": "bong_sung", "fresh": 100}]}}, f)
    with open(p("dock-inputs.json"), "w", encoding="utf-8") as f:
        json.dump({"frames": [{"tick": 0, "interact": True}]}, f)
    code, err = sh([*headless_cmd(), "--mode", "gather", "--seed", "42", "--scenario", p("dock.json"),
                    "--inputs", p("dock-inputs.json"), "--ticks", "1", "--out", p("gather.jsonl"),
                    "--inventory-out", p("catch.json")])
    if code != 0:
        return False, f"gather mã {code}: {err}"
    code, err = sh([*headless_cmd(), "--mode", "quan", "--seed", "42", "--inventory", p("catch.json"),
                    "--ticks", "0", "--out", p("quan.jsonl")])
    if code != 0:
        return False, f"quan mã {code}: {err}"
    with open(p("catch.json"), encoding="utf-8") as f:
        kho = json.load(f)
    with open(p("quan.jsonl"), encoding="utf-8") as f:
        stock = json.loads(f.readline())["stock"]
    # So CHÍNH XÁC id, kind, fresh giữa file kho (sau lần hao ở bước gather) và snapshot quán tick 0.
    ids = [i["id"] for i in kho["items"]]
    ok = ids == ["I1", "I2", "I3"] and stock == kho["items"]
    return ok, f"kho={json.dumps(kho)} · stock quán tick 0 khớp={stock == kho['items']}"


def check_team() -> tuple[bool, str]:
    code, out = sh([sys.executable, os.path.join("tools", "check_team.py")])
    return code == 0, " ".join(out.splitlines()[-2:]) if out else ""


def commit() -> str:
    code, out = sh(["git", "rev-parse", "--short", "HEAD"])
    return out if code == 0 else "unknown"


def main(argv: list) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        results = [("unittest", *check_unittest()),
                   ("tất định (2 lần, so byte)", *check_determinism(tmp)),
                   ("smoke hai tiến trình", *check_two_process(tmp)),
                   ("check_team", *check_team())]
    lines = [f"commit {commit()} · python {sys.version.split()[0]} · headless: {' '.join(headless_cmd())}"]
    lines += [f"[{'ĐẠT' if ok else 'CHƯA ĐẠT'}] {name}: {detail}" for name, ok, detail in results]
    report = "\n".join(lines)
    print(report)
    if "--proof" in argv:
        os.makedirs(PROOF_DIR, exist_ok=True)
        path = os.path.join(PROOF_DIR, f"checks-{commit()}.txt")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(report + "\n")
        print(f"đã ghi {os.path.relpath(path, ROOT)}")
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
