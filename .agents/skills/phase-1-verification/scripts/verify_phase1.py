"""Kiểm chứng Phase 1: unittest + headless gather/quán + tất định + mã 2, ghi bằng chứng.

Chạy từ gốc repo (Windows dùng `python`, macOS/Linux dùng `python3`):
    python .agents/skills/phase-1-verification/scripts/verify_phase1.py
    python .agents/skills/phase-1-verification/scripts/verify_phase1.py --no-proof
    python .agents/skills/phase-1-verification/scripts/verify_phase1.py --only-tests -k harvest

Mã thoát: 0 mọi bước đạt; 1 có bước chưa đạt.
Bằng chứng mặc định ghi vào docs/proof/phase-1/verify-run.txt.

Vì sao có "shim python3": game.contract.json khai `headless_cmd: python3 -m chonoi.headless`
và test hộp đen gọi đúng lệnh đó. Trên Windows `python3` thường chỉ là lối tắt mở
Microsoft Store (mã 9009) nên 21 test hộp đen fail dù luật đúng. Script tạo một venv nhỏ
ngoài repo, chép python.exe thành python3.exe rồi đặt lên đầu PATH. Không sửa contract.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
PROOF = os.path.join(ROOT, "docs", "proof", "phase-1", "verify-run.txt")
SAMPLE_INV = "docs/contracts/inventory.sample.json"


def _python3_works(env=None):
    try:
        p = subprocess.run(["python3", "-c", "import sys; print(sys.version_info[0])"],
                           capture_output=True, text=True, env=env, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return p.returncode == 0 and p.stdout.strip() == "3"


def ensure_python3(log):
    """Bảo đảm `python3` chạy được cho tiến trình con; trả mô tả cách đã làm."""
    if _python3_works():
        return "python3 có sẵn trên PATH"
    if os.name != "nt":
        log("CẢNH BÁO: không có python3 trên PATH; test hộp đen sẽ fail.")
        return "KHÔNG có python3"
    shim = os.path.join(os.path.realpath(tempfile.gettempdir()), "chonoi-py3shim")
    scripts = os.path.join(shim, "Scripts")
    exe3 = os.path.join(scripts, "python3.exe")
    if not os.path.exists(exe3):
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", shim], check=True)
        shutil.copyfile(os.path.join(scripts, "python.exe"), exe3)
    # Đặt PATH ngay trong tiến trình này: trên Windows CreateProcess tìm lệnh theo PATH của
    # tiến trình gọi, nên mọi cấp con (unittest -> run_headless) đều thấy python3 thật.
    os.environ["PATH"] = scripts + os.pathsep + os.environ.get("PATH", "")
    if not _python3_works():
        log("CẢNH BÁO: tạo shim python3 xong vẫn không chạy được.")
        return "shim python3 KHÔNG chạy"
    # Không in đường dẫn tuyệt đối: file bằng chứng được commit, tránh lộ thư mục máy cá nhân.
    return "python3 trên Windows là lối tắt Store; dùng shim venv (python3.exe) trong thư mục tạm"


def run(cmd, env=None):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    return p.returncode, p.stdout, p.stderr


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def count_events(path):
    counts = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                t = json.loads(line).get("type", "?")
                counts[t] = counts.get(t, 0) + 1
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-proof", action="store_true", help="không ghi docs/proof/phase-1/verify-run.txt")
    ap.add_argument("--only-tests", action="store_true", help="chỉ chạy unittest (dùng khi đang sửa luật)")
    ap.add_argument("-k", dest="pattern", help="lọc test theo tên, chuyển cho unittest -k")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--ticks", type=int, default=600)
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # console Windows mặc định cp1252, không in được tiếng Việt
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    lines, results = [], []

    def log(s=""):
        print(s)
        lines.append(s)

    def check(name, ok, detail=""):
        results.append((name, ok))
        log(f"[{'ĐẠT' if ok else 'CHƯA ĐẠT'}] {name}" + (f" — {detail}" if detail else ""))

    rc, head, _ = run(["git", "rev-parse", "--short", "HEAD"])
    rc2, branch, _ = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    rc3, dirty, _ = run(["git", "status", "--porcelain"])
    log("Kiểm chứng Phase 1 (verify_phase1.py)")
    log(f"Thời điểm (UTC): {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M}")
    log(f"Commit: {head.strip() if rc == 0 else '?'} trên nhánh {branch.strip() if rc2 == 0 else '?'}"
        + (" (có thay đổi chưa commit)" if rc3 == 0 and dirty.strip() else ""))
    log(f"Python: {sys.version.split()[0]} ({sys.platform})")
    log(f"python3: {ensure_python3(log)}")
    log()

    # 1. Toàn bộ unittest
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(["tests", "."]))
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    if a.pattern:
        cmd += ["-k", a.pattern]
    log("$ PYTHONPATH=tests:. python3 -m unittest discover -s tests -v" + (f" -k {a.pattern}" if a.pattern else ""))
    code, out, err = run(cmd, env=env)
    text = out + err
    m = re.search(r"Ran (\d+) tests?", text)
    ran = int(m.group(1)) if m else 0
    bad = re.findall(r"^(FAIL|ERROR): (\S+) \(([^)]+)\)", text, re.M)
    for kind, _, where in bad:
        log(f"    {kind}: {where}")
    summary = text.strip().splitlines()[-1] if text.strip() else "(không có output)"
    check("unittest", code == 0 and ran > 0, f"chạy {ran} test, {summary}")
    if "9009" in text or "Python was not found" in text:
        log("    Gợi ý: lỗi 9009 / 'Python was not found' = python3 là lối tắt Store, không phải luật sai.")

    if not a.only_tests:
        tmp = tempfile.mkdtemp(prefix="verify-p1-")
        hl = ["python3", "-m", "chonoi.headless"]
        base = ["--seed", str(a.seed), "--ticks", str(a.ticks)]

        # 2. Headless gather / quán, chạy 2 lần để so tất định từng byte
        for mode in ("gather", "quan"):
            outs = []
            for i in (1, 2):
                o = os.path.join(tmp, f"{mode}-{i}.jsonl")
                extra = ["--inventory-out", os.path.join(tmp, f"inv-{i}.json")] if mode == "gather" else []
                log(f"$ python3 -m chonoi.headless --mode {mode} {' '.join(base)} --out {mode}.jsonl"
                    + (" --inventory-out inv.json" if extra else "") + (f"   (lần {i})" if i == 2 else ""))
                code, _, err = run(hl + ["--mode", mode] + base + ["--out", o] + extra)
                if code != 0:
                    log(f"    stderr: {err.strip()[:300]}")
                outs.append((code, o))
            c1, o1 = outs[0]
            check(f"headless {mode} chạy được", c1 == 0, f"mã thoát {c1}"
                  + (f", sự kiện {count_events(o1)}" if c1 == 0 else ""))
            if c1 == 0 and outs[1][0] == 0:
                h1, h2 = sha256(o1), sha256(outs[1][1])
                check(f"headless {mode} tất định (cùng seed -> cùng byte)", h1 == h2, f"sha256 {h1[:16]}…")
        inv = os.path.join(tmp, "inv-1.json")
        log(f"    Ghi chú: gather {a.ticks} tick " + ("ĐÃ ghi kho" if os.path.exists(inv)
            else "chưa ghi kho (khớp test_inv_01_not_written_when_tick_limit_first: hết số tick trước khi cập bến thì không ghi)"))

        # 3. Quán đọc kho mẫu theo schema contract
        o = os.path.join(tmp, "quan-inv.jsonl")
        log(f"$ python3 -m chonoi.headless --mode quan {' '.join(base)} --inventory {SAMPLE_INV} --out quan-inv.jsonl")
        code, _, err = run(hl + ["--mode", "quan"] + base + ["--inventory", SAMPLE_INV, "--out", o])
        check("quán nạp kho mẫu", code == 0, f"mã thoát {code}" + (f", {err.strip()[:200]}" if code else ""))

        # 4. Đầu vào sai -> mã 2, không ghi đầu ra
        for label, args in (("--ticks -1", ["--mode", "quan", "--seed", "1", "--ticks", "-1"]),
                            ("--mode river", ["--mode", "river", "--seed", "1", "--ticks", "0"]),
                            ("--inventory với gather", ["--mode", "gather", "--seed", "1", "--ticks", "0",
                                                        "--inventory", SAMPLE_INV])):
            o = os.path.join(tmp, "bad.jsonl")
            log(f"$ python3 -m chonoi.headless {' '.join(args)} --out bad.jsonl")
            code, _, _ = run(hl + args + ["--out", o])
            check(f"đầu vào sai ({label}) -> mã 2, không ghi file", code == 2 and not os.path.exists(o),
                  f"mã thoát {code}")
        shutil.rmtree(tmp, ignore_errors=True)

    log()
    passed = sum(ok for _, ok in results)
    log(f"Tổng: {passed}/{len(results)} bước đạt.")
    if not a.no_proof and not a.only_tests:
        os.makedirs(os.path.dirname(PROOF), exist_ok=True)
        with open(PROOF, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        print(f"Đã ghi bằng chứng: {os.path.relpath(PROOF, ROOT)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
