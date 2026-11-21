"""QA Phase 2 (TV5): chạy các checkpoint bàn giao bằng CLI headless như máy chấm, ghi bằng chứng.

    python3 tools/qa_p2.py            # ghi vào docs/proof/phase-2/ (qa-report.md + file .jsonl/.json)
    python3 tools/qa_p2.py --quick    # bỏ regression

Checkpoint (TICKET-02 mục 5 + phân công TV5):
  CP1 smoke liên tiến trình gather --inventory-out → quan --inventory, đủ 6 loại, so stock tick 0 (integration.*)
  CP2 day --days 1 trọn Ngày không pause: ≤ 22.200 tick, ≤ 20 s, thứ tự day_start → day_plan → phase_start
  CP3 day --days 2 fixture money=earned=200: mua oxygen + shop_done cùng frame → money 0, earned 200,
      oxy tối đa Ngày 2 = 2700, days_completed = 2, reason days_complete
  CP4 pause headless: đứng sim_tick/time_left, chỉ tăng tick ngoài, phát paused/resumed
  CP5 ngất vẫn mở quán với kho rỗng
  CP6 tất định: day chạy lại cùng seed/input giống từng byte
  CP7 regression toàn suite (gồm test Phase 1 còn hiệu lực)
"""

import argparse
import filecmp
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROOF = os.path.join(ROOT, "docs", "proof", "phase-2")
HEADLESS = [sys.executable, "-m", "chonoi.headless"]
DAY_TICK_LIMIT = 22200


def run(args, **kw):
    t0 = time.perf_counter()
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, **kw)
    return p, time.perf_counter() - t0


def rows(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def events(path, name=None):
    return [r for r in rows(path) if r["type"] == "event" and (name is None or r["name"] == name)]


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


class Report:
    def __init__(self):
        self.items = []

    def add(self, cp, name, ok, detail):
        status = ok if isinstance(ok, str) else ("PASS" if ok else "FAIL")
        self.items.append((cp, name, status, detail))
        print(f"[{status}] {cp} {name}: {detail}")

    def markdown(self, commit):
        out = ["# QA Phase 2 · báo cáo tự động (`python3 tools/qa_p2.py`)", "",
               f"- Commit: `{commit}`",
               f"- Máy đo: {platform.platform()} · Python {platform.python_version()} · {platform.machine()}",
               f"- Thời điểm chạy: {time.strftime('%Y-%m-%d %H:%M:%S')}", "",
               "| CP | Kiểm tra | Kết quả | Chi tiết |", "|---|---|---|---|"]
        out += [f"| {c} | {n} | **{s}** | {d} |" for c, n, s, d in self.items]
        return "\n".join(out) + "\n"


def cp1_integration(rep, tmp):
    hold = ["ca_loc", "bong_sung", "bong_sung", "ca_keo", "ca_keo", "keo_neo", "ca_linh", "bong_dien_dien"]
    sc, ip = os.path.join(PROOF, "integration.scenario.json"), os.path.join(PROOF, "integration.inputs.json")
    write_json(sc, {"gather": {"hold": hold, "random_fish": False}})
    write_json(ip, {"frames": [{"tick": 0, "interact": True}]})
    inv = os.path.join(PROOF, "integration.inventory.json")
    g_out, q_out = os.path.join(PROOF, "integration.gather.jsonl"), os.path.join(PROOF, "integration.quan.jsonl")
    p, _ = run(HEADLESS + ["--mode", "gather", "--seed", "1", "--scenario", sc, "--inputs", ip,
                           "--ticks", "10", "--out", g_out, "--inventory-out", inv])
    if p.returncode:
        return rep.add("CP1", "Smoke gather → quan (6 loại)", False, f"gather mã {p.returncode}: {p.stderr.strip()[:150]}")
    end = events(g_out, "gather_end")[0]["data"]
    p, _ = run(HEADLESS + ["--mode", "quan", "--seed", "1", "--inventory", inv, "--ticks", "1", "--out", q_out])
    if p.returncode:
        return rep.add("CP1", "Smoke gather → quan (6 loại)", False, f"quan mã {p.returncode}: {p.stderr.strip()[:150]}")
    stock0 = [r for r in rows(q_out) if r["type"] == "snapshot"][0]["stock"]
    with open(inv, encoding="utf-8") as f:
        file_items = json.load(f)["items"]
    ok = end["reason"] == "docked" and end["inventory"]["items"] == file_items == stock0 and len(stock0) == 6
    rep.add("CP1", "Smoke gather `--inventory-out` → quan `--inventory` (6 loại)", ok,
            f"gather_end={end['inventory']['items']} · file={file_items} · stock@0={stock0}")


def cp2_day1(rep, tmp):
    out = os.path.join(PROOF, "day1.jsonl")
    p, dt = run(HEADLESS + ["--mode", "day", "--seed", "42", "--days", "1", "--ticks", str(DAY_TICK_LIMIT),
                            "--snapshot-every", "600", "--out", out])
    if p.returncode:
        return rep.add("CP2", "Headless day --days 1", False, f"mã {p.returncode}: {p.stderr.strip()[:150]}")
    end = rows(out)[-1]
    head = [e["name"] for e in events(out)[:3]]
    plan = events(out, "day_plan")[0]["data"]
    ok = (dt <= 20 and end["days_completed"] == 1 and end["reason"] == "days_complete" and end["ticks"] <= DAY_TICK_LIMIT
          and head == ["day_start", "day_plan", "phase_start"]
          and plan == {"dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3}, "ingredients": {"bong_sung": 6, "ca_loc": 3}})
    rep.add("CP2", "Headless day --days 1 trọn Ngày, không pause (≤ 22.200 tick, ≤ 20 s)", ok,
            f"{dt:.2f} s · {end['ticks']} tick · reason={end['reason']} · days_completed={end['days_completed']} · mở đầu {head}")


def _day2(tmp, frames, name="day2"):
    sc = os.path.join(PROOF, f"{name}.scenario.json")
    ip = os.path.join(PROOF, f"{name}.inputs.json")
    out = os.path.join(PROOF, f"{name}.jsonl")
    write_json(sc, {"day": {"money": 200, "earned": 200},
                    "gather": {"hold": ["ca_loc"], "random_fish": False}, "quan": {"time_left_ticks": 60}})
    merged = {}
    for fr in frames:  # gộp các frame cùng tick (CLI cấm tick trùng)
        merged.setdefault(fr["tick"], {}).update(fr)
    write_json(ip, {"frames": [merged[t] for t in sorted(merged)]})
    p, _ = run(HEADLESS + ["--mode", "day", "--seed", "1", "--days", "2", "--scenario", sc, "--inputs", ip,
                           "--ticks", "3000", "--snapshot-every", "1", "--out", out])
    return p, out


def _phase_tick(out, phase, day):
    return next(e["tick"] for e in events(out, "phase_start") if e["phase"] == phase and e["day"] == day)


def cp3_day2(rep, tmp):
    frames = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}]
    p, out = _day2(tmp, frames)
    if p.returncode:
        return rep.add("CP3", "day --days 2 mua oxygen", False, f"mã {p.returncode}: {p.stderr.strip()[:150]}")
    s1 = _phase_tick(out, "shop", 1)  # Shop chạy gameplay từ bước đọc input tick s1
    frames += [{"tick": s1, "buy": "oxygen", "shop_done": True}, {"tick": s1 + 1, "shop_done": False}]
    p, out = _day2(tmp, frames)
    g2 = _phase_tick(out, "gather", 2)
    frames += [{"tick": g2, "interact": True}, {"tick": g2 + 1, "interact": False}]
    p, out = _day2(tmp, frames)
    s2 = _phase_tick(out, "shop", 2)
    frames += [{"tick": s2, "shop_done": True}]
    p, out = _day2(tmp, frames)
    if p.returncode:
        return rep.add("CP3", "day --days 2 mua oxygen", False, f"mã {p.returncode}: {p.stderr.strip()[:150]}")
    bought = events(out, "bought")
    ends = [e["data"] for e in events(out, "shop_end")]
    snaps = [r for r in rows(out) if r["type"] == "snapshot"]
    d2 = next(s for s in snaps if s.get("day") == 2 and s["phase"] == "gather")
    end = rows(out)[-1]
    ok = (bought and bought[0]["data"] == {"upgrade": "oxygen", "level": 1, "price": 200, "money": 0}
          and ends == [{"reason": "done"}, {"reason": "done"}]
          and d2["active_upgrades"] == {"oxygen": 1} and d2["player"]["oxygen_max_ticks"] == 2700
          and end["days_completed"] == 2 and end["reason"] == "days_complete" and end["earned"] == 200)
    rep.add("CP3", "day --days 2: money=earned=200, mua oxygen + shop_done cùng frame", ok,
            f"bought={bought[0]['data'] if bought else None} · shop_end={ends} · D2 oxy_max={d2['player']['oxygen_max_ticks']} "
            f"active={d2['active_upgrades']} · end money={end['money']} earned={end['earned']} days_completed={end['days_completed']}")


def cp4_pause(rep, tmp):
    ip = os.path.join(PROOF, "pause.inputs.json")
    out = os.path.join(PROOF, "pause.jsonl")
    write_json(ip, {"frames": [{"tick": 10, "pause": True}, {"tick": 11, "pause": False}, {"tick": 110, "pause": True}]})
    p, _ = run(HEADLESS + ["--mode", "day", "--seed", "1", "--inputs", ip, "--ticks", "200",
                           "--snapshot-every", "1", "--out", out])
    if p.returncode:
        return rep.add("CP4", "Pause headless", False, f"mã {p.returncode}: {p.stderr.strip()[:150]}")
    snaps = {r["tick"]: r for r in rows(out) if r["type"] == "snapshot"}
    names = [(e["tick"], e["name"]) for e in events(out) if e["name"] in ("paused", "resumed")]
    a, b, c = snaps[11], snaps[110], snaps[111]
    ok = (names == [(11, "paused"), (111, "resumed")] and a["state"] == b["state"] == "paused"
          and a["sim_tick"] == b["sim_tick"] and a["time_left_ticks"] == b["time_left_ticks"]
          and c["state"] == "playing" and c["sim_tick"] == b["sim_tick"] + 1)
    rep.add("CP4", "Pause headless (đứng sim_tick + đồng hồ, chỉ tăng tick ngoài)", ok,
            f"event={names} · sim_tick@11={a['sim_tick']} @110={b['sim_tick']} @111={c['sim_tick']} · "
            f"time_left@11={a['time_left_ticks']} @110={b['time_left_ticks']}")


def cp5_faint(rep, tmp):
    sc = os.path.join(PROOF, "faint.scenario.json")
    out = os.path.join(PROOF, "faint.jsonl")
    write_json(sc, {"gather": {"hold": ["ca_loc", "bong_sung"], "player": {"pos": [20, 5], "hp": 1, "oxygen_ticks": 0}}})
    p, _ = run(HEADLESS + ["--mode", "day", "--seed", "1", "--scenario", sc, "--ticks", "120",
                           "--snapshot-every", "1", "--out", out])
    if p.returncode:
        return rep.add("CP5", "Ngất vẫn mở quán", False, f"mã {p.returncode}: {p.stderr.strip()[:150]}")
    ev = [(e["tick"], e["phase"], e["name"]) for e in events(out) if e["name"] in ("faint", "gather_end", "phase_start")][1:]
    end = events(out, "gather_end")[0]["data"]
    q0 = next(r for r in rows(out) if r["type"] == "snapshot" and r["phase"] == "quan")
    ok = (end["reason"] == "fainted" and end["inventory"]["items"] == {} and q0["stock"] == {}
          and q0["phase_tick"] == 0 and [n for _, _, n in ev] == ["faint", "gather_end", "phase_start"])
    rep.add("CP5", "Ngất → gather_end(fainted) → phase_start(quan) cùng tick, kho rỗng", ok,
            f"{ev} · stock quán@0={q0['stock']}")


def cp6_determinism(rep, tmp):
    a, b = os.path.join(PROOF, "det_day_run1.jsonl"), os.path.join(PROOF, "det_day_run2.jsonl")
    for out in (a, b):
        run(HEADLESS + ["--mode", "day", "--seed", "7", "--days", "1", "--ticks", "3000", "--snapshot-every", "300", "--out", out])
    rep.add("CP6", "Tất định day seed 7 (3.000 tick × 2 lần)", filecmp.cmp(a, b, shallow=False),
            f"sha256 {sha(a)} / {sha(b)}")


def cp7_regression(rep):
    env = dict(os.environ, PYTHONPATH="tests:.")
    p, dt = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], env=env)
    with open(os.path.join(PROOF, "test_suite.log"), "w", encoding="utf-8") as f:
        f.write(p.stderr + p.stdout)
    last = [ln for ln in p.stderr.strip().splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
    rep.add("CP7", "Regression toàn suite (P1 còn hiệu lực + P2)", p.returncode == 0, f"{' · '.join(last)} ({dt:.1f} s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    os.makedirs(PROOF, exist_ok=True)
    git = lambda *c: subprocess.run(["git", *c], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    commit = git("rev-parse", "--short", "HEAD") + (" (+ thay đổi chưa commit)" if git("status", "--porcelain") else "")
    rep = Report()
    with tempfile.TemporaryDirectory() as tmp:
        for cp in (cp1_integration, cp2_day1, cp3_day2, cp4_pause, cp5_faint, cp6_determinism):
            try:
                cp(rep, tmp)
            except Exception as e:  # ghi lỗi thật, không giấu
                rep.add(cp.__name__[:3].upper(), cp.__name__, False, f"lỗi kiểm: {type(e).__name__}: {e}")
        if not a.quick:
            cp7_regression(rep)
    with open(os.path.join(PROOF, "qa-report.md"), "w", encoding="utf-8") as f:
        f.write(rep.markdown(commit))
    return 1 if any(s == "FAIL" for _, _, s, _ in rep.items) else 0


if __name__ == "__main__":
    sys.exit(main())
