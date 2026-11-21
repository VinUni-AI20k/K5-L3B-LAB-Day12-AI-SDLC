"""Smoke test Phase 1 chạy bằng lệnh headless thật (hộp đen), in bảng kết quả và thoát 1 nếu có mục đỏ.

    python3 tools/smoke_phase1.py

Kiểm: --ticks 0; ca đầy đủ 10.800 tick của cả hai chế độ; cùng seed thì JSONL và file kho giống từng byte
(nhiều seed, hai giá trị --snapshot-every, hai thư mục đầu ra khác nhau); lượt bàn giao gather -> quan theo PRD-0 mục G;
file kho không được ghi khi chạm --ticks; mã thoát 2 cho đầu vào sai. Chỉ dùng thư viện chuẩn.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_determinism import DEFAULT_FRAMES, ROOT, headless_cmd  # noqa: E402

RESULTS = []


def run(args, cwd=ROOT):
    p = subprocess.run([*headless_cmd(), *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stderr


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rows(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))


def write(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path


def main():
    t = tempfile.mkdtemp(prefix="smoke-p1-")
    p = lambda name: os.path.join(t, name)  # noqa: E731
    inputs = write(p("inputs.json"), DEFAULT_FRAMES)

    for mode in ("gather", "quan"):
        code, err = run(["--mode", mode, "--seed", "1", "--ticks", "0", "--out", p(f"{mode}0.jsonl")])
        r = rows(p(f"{mode}0.jsonl")) if code == 0 else []
        check(f"{mode}: --ticks 0", code == 0 and [x["type"] for x in r] == ["snapshot", "end"]
              and r[-1]["reason"] == "tick_limit", f"mã {code}, {len(r)} dòng")

        start = time.time()
        code, err = run(["--mode", mode, "--seed", "1", "--ticks", "10800", "--out", p(f"{mode}full.jsonl")])
        took = time.time() - start
        r = rows(p(f"{mode}full.jsonl")) if code == 0 else []
        last_event = [x["name"] for x in r if x["type"] == "event"][-1:] or [None]
        want = "gather_end" if mode == "gather" else "quan_end"
        check(f"{mode}: ca đầy đủ 10800 tick", code == 0 and r and r[-1]["type"] == "end" and r[-1]["reason"] == "time"
              and last_event == [want], f"mã {code}, {took:.1f}s, sự kiện cuối {last_event[0]}, end.reason {r[-1]['reason'] if r else None}")

        for seed in (1, 42, 2026):
            for every in (1, 10):
                hashes = []
                for k in (1, 2):
                    os.makedirs(p(f"out{k}"), exist_ok=True)
                    out = os.path.join(p(f"out{k}"), f"{mode}-{seed}-{every}.jsonl")
                    code, err = run(["--mode", mode, "--seed", str(seed), "--ticks", "3000", "--out", out,
                                     "--inputs", inputs, "--snapshot-every", str(every)])
                    hashes.append(sha(out) if code == 0 else f"mã {code}: {err.strip()[:80]}")
                check(f"{mode}: tất định seed {seed}, snapshot-every {every}, hai thư mục đầu ra",
                      hashes[0] == hashes[1] and not hashes[0].startswith("mã"), hashes[0][:12])

    # Đường có ngẫu nhiên thật: quán có kho đủ nên khách chọn món theo seed (Streams).
    kho_all = write(p("kho-all.json"), {"items": {"ca_loc": 5, "ca_linh": 6, "bong_dien_dien": 3, "bong_sung": 10}})
    per_seed = {}
    for seed in range(1, 9):
        pair = []
        for k in (1, 2):
            out = p(f"rnd-{seed}-{k}.jsonl")
            code, err = run(["--mode", "quan", "--seed", str(seed), "--ticks", "4000", "--out", out,
                             "--inventory", kho_all, "--snapshot-every", "10"])
            pair.append(sha(out) if code == 0 else f"mã {code}")
        per_seed[seed] = pair
    check("quan có kho và khách ngẫu nhiên: mỗi seed chạy 2 lần giống từng byte (8 seed)",
          all(a == b and not a.startswith("mã") for a, b in per_seed.values()))
    check("quan: seed khác nhau cho kết quả khác nhau (ngẫu nhiên thật đi qua Streams)",
          len({a for a, _ in per_seed.values()}) >= 2, f"{len({a for a, _ in per_seed.values()})} kết quả khác nhau trong 8 seed")

    # PRD-0 mục G: bàn giao gather -> quan
    dock = write(p("dock.json"), {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}})
    dock_in = write(p("dock-inputs.json"), {"frames": [{"tick": 0, "interact": True}]})
    kho_hash = []
    for k in (1, 2):
        kho = p(f"kho{k}.json")
        code, err = run(["--mode", "gather", "--seed", "42", "--scenario", dock, "--inputs", dock_in, "--ticks", "1",
                         "--out", p(f"dock{k}.jsonl"), "--inventory-out", kho])
        code2, err2 = run(["--mode", "quan", "--seed", "42", "--inventory", kho, "--ticks", "0", "--out", p(f"quan{k}.jsonl")])
        ok = code == 0 and code2 == 0
        kho_hash.append((sha(kho), sha(p(f"quan{k}.jsonl"))) if ok else None)
        if k == 1 and ok:
            snap0 = rows(p("quan1.jsonl"))[0]
            with open(kho, encoding="utf-8") as f:
                content = json.load(f)
            check("bàn giao gather -> quan (PRD-0 mục G)", content == {"items": {"bong_sung": 2, "ca_loc": 1}}
                  and snap0["stock"] == {"bong_sung": 2, "ca_loc": 1}, f"kho {content}, stock tick 0 {snap0['stock']}")
    check("bàn giao: file kho và JSONL quán giống từng byte qua 2 lần", kho_hash[0] is not None and kho_hash[0] == kho_hash[1])

    code, err = run(["--mode", "gather", "--seed", "1", "--ticks", "5", "--out", p("short.jsonl"),
                     "--inventory-out", p("khoshort.json")])
    check("chạm --ticks trước khi kết thúc: không tạo file kho", code == 0 and not os.path.exists(p("khoshort.json")))

    bad = {
        "thiếu --seed": ["--mode", "quan", "--ticks", "1", "--out", p("b1.jsonl")],
        "--ticks âm": ["--mode", "quan", "--seed", "1", "--ticks", "-1", "--out", p("b2.jsonl")],
        "--mode day (v1.0)": ["--mode", "day", "--seed", "1", "--ticks", "1", "--out", p("b3.jsonl")],
        "--inventory với gather": ["--mode", "gather", "--seed", "1", "--ticks", "1", "--out", p("b4.jsonl"),
                                   "--inventory", p("kho1.json")],
        "scenario sai khối": ["--mode", "quan", "--seed", "1", "--ticks", "1", "--out", p("b5.jsonl"),
                              "--scenario", write(p("sc-sai.json"), {"gather": {}})],
        "scenario không tồn tại": ["--mode", "quan", "--seed", "1", "--ticks", "1", "--out", p("b6.jsonl"),
                                   "--scenario", p("khong-co.json")],
    }
    for name, args in bad.items():
        code, _ = run(args)
        check(f"đầu vào sai ({name}) thoát mã 2", code == 2, f"mã {code}")

    width = max(len(n) for n, _, _ in RESULTS)
    for name, ok, detail in RESULTS:
        print(f"{'OK ' if ok else 'LỖI'}  {name.ljust(width)}  {detail}")
    failed = [n for n, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} mục đạt" + (f"; LỖI: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
