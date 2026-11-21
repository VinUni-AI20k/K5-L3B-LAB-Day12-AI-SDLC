#!/usr/bin/env python3
"""Script tự động kiểm thử đa Phase (Phase 1–4):
- Chạy unit tests hồi quy (toàn bộ tests của phase hiện tại và các phase trước).
- Chạy headless mô phỏng đơn lẻ hoặc tích hợp chuỗi 2 tiến trình (gather -> kho.json -> quan).
- Phân tích snapshots, events, schema kho.
- Sinh báo cáo nghiệm thu vào docs/proof/phase-<N>/verification_summary.md.
- Tự động ghi nhật ký vào docs/ai-usage-log.md khi có cờ --log-ai.

Tương thích hoàn hảo cả Windows (python) và Linux/macOS (python3).
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
TOOLS_DIR = os.path.join(ROOT, "tools")


def _env():
    env = os.environ.copy()
    tests_dir = os.path.join(ROOT, "tests")
    env["PYTHONPATH"] = f"{tests_dir}{os.pathsep}{ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"
    env["PATH"] = f"{TOOLS_DIR}{os.pathsep}{env.get('PATH', '')}"
    return env


def run_unit_tests(pattern="test_smoke_*.py"):
    print(f"[1/3] Chạy Unit Tests hồi quy (pattern={pattern})...")
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"]
    t0 = time.time()
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=_env())
    duration = round(time.time() - t0, 2)
    passed = res.returncode == 0
    print(f"      → {'✅ PASS' if passed else '❌ FAIL'} ({duration}s)")
    return {"passed": passed, "returncode": res.returncode,
            "stdout": res.stdout, "stderr": res.stderr, "duration_s": duration}


def run_headless(mode="gather", seed=1, ticks=600, out_path=None, scenario=None, inventory=None, inventory_out=None):
    if out_path is None:
        out_path = os.path.join(ROOT, "docs", "proof", f"headless_{mode}_seed{seed}.jsonl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = [sys.executable, "-m", "chonoi.headless",
           "--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--out", out_path]
    if scenario:
        cmd += ["--scenario", scenario]
    if inventory:
        cmd += ["--inventory", inventory]
    if inventory_out:
        cmd += ["--inventory-out", inventory_out]

    t0 = time.time()
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=_env())
    duration = round(time.time() - t0, 2)
    stats = {"snapshots": 0, "events": 0, "event_types": {}}
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if row.get("type") == "snapshot":
                    stats["snapshots"] += 1
                elif row.get("type") == "event":
                    stats["events"] += 1
                    n = row.get("name", "?")
                    stats["event_types"][n] = stats["event_types"].get(n, 0) + 1
    passed = res.returncode == 0
    out_rel = os.path.relpath(out_path, ROOT).replace("\\", "/")
    print(f"      → mode={mode}: {'✅ PASS' if passed else '❌ FAIL'} (exit {res.returncode}, {duration}s) "
          f"| snapshots={stats['snapshots']} events={stats['events']}")
    return {"passed": passed, "returncode": res.returncode, "stderr": res.stderr,
            "out_file": out_rel, "out_path": out_path, "duration_s": duration, "stats": stats}


def generate_report(phase, test_res, sim_results, proof_dir):
    print(f"[3/3] Sinh báo cáo verification_summary.md cho Phase {phase}...")
    os.makedirs(proof_dir, exist_ok=True)
    summary = os.path.join(proof_dir, "verification_summary.md")
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    abs_summary = os.path.abspath(summary).replace("\\", "/")

    sim_md = ""
    table_rows = ""
    for sim in sim_results:
        abs_proof = os.path.abspath(sim["out_path"]).replace("\\", "/")
        sim_md += f"""### Chế độ: `{sim["out_file"]}`
- **Proof:** [`{sim["out_file"]}`](file:///{abs_proof})
- **Trạng thái:** {"✅ PASS" if sim["passed"] else "❌ FAIL"} (exit `{sim["returncode"]}`, `{sim["duration_s"]}s`)
- **Snapshots:** `{sim["stats"]["snapshots"]}` | **Events:** `{sim["stats"]["events"]}`
- **Thống kê sự kiện:**
```json
{json.dumps(sim["stats"]["event_types"], indent=2, ensure_ascii=False)}
```
"""
        table_rows += f"| Mô phỏng `{sim['out_file']}` | Headless ({sim['stats']['snapshots']} snapshots) | [{sim['out_file']}](file:///{abs_proof}) | {'Đạt' if sim['passed'] else 'Chưa đạt'} |\n"

    md = f"""# Báo cáo Kiểm Chứng Tự Động — Phase {phase}
Thời gian thực hiện: `{ts}`

## 1. Kết quả Unit Tests (Hồi quy)
- **Trạng thái:** {"✅ ĐẠT (PASS)" if test_res["passed"] else "❌ CHƯA ĐẠT (FAIL)"} — `{test_res["duration_s"]}s`
```text
{(test_res["stderr"] or "Toàn bộ tests chạy thành công.")[-2000:]}
```

## 2. Kết quả Mô phỏng Headless
{sim_md}

## 3. Gợi ý điền ma trận kiểm chứng (docs/verification/phase-{phase}.md)
| AC / Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Unit tests hồi quy | unittest discover | [verification_summary.md](file:///{abs_summary}) | {"Đạt" if test_res["passed"] else "Chưa đạt"} |
{table_rows}"""

    with open(summary, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"      → Đã lưu: {summary}")
    return summary


def log_ai(phase, author, task, model="Antigravity / Agentic AI", tokens="~5k", note=""):
    log_file = os.path.join(ROOT, "docs", "ai-usage-log.md")
    if not os.path.exists(log_file):
        return
    row = f"| {phase} | {author} | {model} | {task} | {tokens} | {note or 'OK'} |\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(row)
    print(f"      → Đã tự động ghi nhật ký AI vào {log_file}")


def main():
    p = argparse.ArgumentParser(description="Chạy test, headless, sinh báo cáo verification cho Phase 1–4")
    p.add_argument("--phase", type=int, default=1, help="Số thứ tự Phase (1, 2, 3, 4)")
    p.add_argument("--mode", default="gather", choices=["gather", "quan"], help="Chế độ chạy đơn lẻ")
    p.add_argument("--seed", type=int, default=1, help="Seed ngẫu nhiên")
    p.add_argument("--ticks", type=int, default=600, help="Số ticks mô phỏng")
    p.add_argument("--two-process", action="store_true", help="Chạy chuỗi tích hợp 2 tiến trình: gather -> kho.json -> quan")
    p.add_argument("--scenario", default=None, help="File scenario (nếu có)")
    p.add_argument("--inventory", default=None, help="File inventory nạp vào quan (nếu có)")
    p.add_argument("--pattern", default="test_smoke_*.py", help="Pattern unittest")
    p.add_argument("--log-ai", action="store_true", help="Tự động thêm dòng vào docs/ai-usage-log.md")
    p.add_argument("--author", default="B", help="Tên / handle người thực hiện")
    p.add_argument("--task-name", default=None, help="Tên task cần log")
    p.add_argument("--model", default="Antigravity / Agentic AI", help="Tên model AI")
    p.add_argument("--note", default="Chạy test tự động", help="Ghi chú kết quả")
    args = p.parse_args()

    proof_dir = os.path.join(ROOT, "docs", "proof", f"phase-{args.phase}")
    os.makedirs(proof_dir, exist_ok=True)

    test_res = run_unit_tests(pattern=args.pattern)

    sim_results = []
    if args.two_process:
        print(f"[2/3] Chạy chuỗi tích hợp 2 tiến trình: gather -> kho.json -> quan (Phase {args.phase})...")
        kho_path = os.path.join(proof_dir, f"kho_seed{args.seed}.json")
        gather_path = os.path.join(proof_dir, f"gather_seed{args.seed}_ticks{args.ticks}.jsonl")
        quan_path = os.path.join(proof_dir, f"quan_seed{args.seed}_ticks{args.ticks}.jsonl")

        r_gather = run_headless(mode="gather", seed=args.seed, ticks=args.ticks,
                                out_path=gather_path, scenario=args.scenario, inventory_out=kho_path)
        sim_results.append(r_gather)

        if os.path.exists(kho_path):
            r_quan = run_headless(mode="quan", seed=args.seed, ticks=args.ticks,
                                  out_path=quan_path, inventory=kho_path)
            sim_results.append(r_quan)
        else:
            print(f"      ℹ️ Lưu ý: File kho '{os.path.basename(kho_path)}' chưa được tạo vì gather chưa cập bến (dock) hoặc chưa hết giờ (180s). Bỏ qua bước chạy quán.")
    else:
        print(f"[2/3] Chạy Headless mode={args.mode}, seed={args.seed}, ticks={args.ticks} (Phase {args.phase})...")
        out_path = os.path.join(proof_dir, f"{args.mode}_seed{args.seed}_ticks{args.ticks}.jsonl")
        r_single = run_headless(mode=args.mode, seed=args.seed, ticks=args.ticks,
                                out_path=out_path, scenario=args.scenario, inventory=args.inventory)
        sim_results = [r_single]

    generate_report(args.phase, test_res, sim_results, proof_dir)

    if args.log_ai:
        task = args.task_name or f"Kiểm thử & sinh báo cáo Phase {args.phase}"
        log_ai(args.phase, author=args.author, task=task, model=args.model, note=args.note)

    all_passed = test_res["passed"] and all(s["passed"] for s in sim_results)
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
