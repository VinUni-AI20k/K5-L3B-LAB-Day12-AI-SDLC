"""QA Phase 3 (TV5): checkpoint TICKET-03 "Mùa Nước Nổi" bằng CLI headless như máy chấm, ghi bằng chứng.

    python3 tools/qa_p3.py            # ghi docs/proof/phase-3/qa-report.md + file .json/.jsonl
    python3 tools/qa_p3.py --quick    # bỏ regression

Nếu game.contract.json chưa bật "1.2", script chạy các CP v1.2 trên BẢN SAO TẠM của chonoi/ + manifest
đã đổi contract_version → "1.2" (không sửa manifest thật) và ghi rõ chế độ trong báo cáo.

  CP1 (AC-P3-02) gather 1 bước, giỏ fresh 30 → spoiled tick 1 {item_id I1, kind, location hold}
  CP2 (AC-P3-01/05) smoke file: gather cập bến frame 0 → --inventory-out → quan --inventory --ticks 0;
      id/kind khớp chính xác, fresh khớp ±0.01 (dung sai ticket), file = gather_end.data.inventory
  CP3 (AC-P3-01) v1.2 từ chối kho đếm, id trùng, kind lạ, fresh ngoài miền/NaN → mã 2
  CP4 (AC-P3-03) phần giữ vừa ươn → spoiled rồi giữ lại cá thể khác; không đủ → unfulfillable
  CP5 (AC-P3-04) chốt giá floor(niêm yết × fresh TB / 100) sau đúng 60 bước hao ở quán (50.25 → 50 → 30k)
  CP6 (AC-P3-05) day 2 ngày: bàn giao cùng tick không hao thêm, pause/Shop không hao, id Ngày 2 cấp mới
  CP7 tất định day v1.2 (chạy 2 lần giống từng byte)
  CP8 regression: suite trên manifest thật + suite trên bản v1.2 (liệt kê test cần chủ lát đổi fixture)
"""

import argparse
import filecmp
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROOF = os.path.join(ROOT, "docs", "proof", "phase-3")
TOL = 0.01


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def rows(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def events(path, name=None):
    return [r for r in rows(path) if r["type"] == "event" and (name is None or r["name"] == name)]


def snaps(path):
    return [r for r in rows(path) if r["type"] == "snapshot"]


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def same_items(a, b):
    """id/kind chính xác, fresh trong ±0.01 (TICKET-03: dung sai quan sát độ tươi)."""
    ka = sorted(a, key=lambda i: i["id"])
    kb = sorted(b, key=lambda i: i["id"])
    return ([(i["id"], i["kind"]) for i in ka] == [(i["id"], i["kind"]) for i in kb]
            and all(abs(float(x["fresh"]) - float(y["fresh"])) <= TOL for x, y in zip(ka, kb)))


class Env:
    """Nơi chạy CLI: repo thật nếu manifest đã 1.2, không thì bản sao tạm có bật 1.2."""

    def __init__(self, tmp):
        man = load(os.path.join(ROOT, "game.contract.json"))
        self.repo_version = man.get("contract_version")
        if self.repo_version == "1.2":
            self.cwd, self.mode = ROOT, "repo (manifest 1.2)"
        else:
            self.cwd = os.path.join(tmp, "v12")
            os.makedirs(self.cwd)
            for d in ("chonoi", "tests", "tools", "docs"):
                shutil.copytree(os.path.join(ROOT, d), os.path.join(self.cwd, d),
                                ignore=shutil.ignore_patterns("__pycache__", "*.jpg", "*.jsonl"))
            for f in ("game.contract.json", "TEAM.md"):
                shutil.copy(os.path.join(ROOT, f), self.cwd)
            man["contract_version"] = "1.2"
            write_json(os.path.join(self.cwd, "game.contract.json"), man)
            self.mode = f"bản sao tạm bật 1.2 (manifest repo đang {self.repo_version})"

    def run(self, *args, cwd=None, env=None):
        t0 = time.perf_counter()
        p = subprocess.run([sys.executable, "-m", "chonoi.headless", *args], cwd=cwd or self.cwd,
                           capture_output=True, text=True, env=env)
        return p, time.perf_counter() - t0


class Report:
    def __init__(self):
        self.items = []

    def add(self, cp, ac, name, ok, detail):
        st = ok if isinstance(ok, str) else ("PASS" if ok else "FAIL")
        self.items.append((cp, ac, name, st, detail))
        print(f"[{st}] {cp} {name}: {detail}")


def P(name):
    return os.path.join(PROOF, name)


def cp1_spoil_threshold(rep, env):
    sc, out = P("cp1-spoil.scenario.json"), P("cp1-spoil.jsonl")
    write_json(sc, {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}], "random_fish": False, "monsters": []}})
    p, _ = env.run("--mode", "gather", "--seed", "1", "--scenario", sc, "--ticks", "1", "--out", out)
    if p.returncode:
        return rep.add("CP1", "AC-P3-02", "Ngưỡng ươn 30 ở gather", False, f"mã {p.returncode}: {p.stderr.strip()[:150]}")
    ev = events(out, "spoiled")
    want = [{"type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
             "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}]
    rep.add("CP1", "AC-P3-02", "Giỏ fresh 30 → spoiled đúng tick 1, một lần", ev == want, json.dumps(ev, ensure_ascii=False))


def cp2_file_handoff(rep, env):
    sc, ip = P("cp2-file.scenario.json"), P("cp2-file.inputs.json")
    inv, g_out, q_out = P("cp2-file.inventory.json"), P("cp2-file.gather.jsonl"), P("cp2-file.quan.jsonl")
    write_json(sc, {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, {"id": "I2", "kind": "ca_loc", "fresh": 57.5}],
                               "random_fish": False, "monsters": []}})
    write_json(ip, {"frames": [{"tick": 0, "interact": True}]})
    p, _ = env.run("--mode", "gather", "--seed", "1", "--scenario", sc, "--inputs", ip, "--ticks", "5",
                   "--out", g_out, "--inventory-out", inv)
    if p.returncode:
        return rep.add("CP2", "AC-P3-01/05", "Smoke bàn giao file", False, f"gather mã {p.returncode}: {p.stderr.strip()[:150]}")
    file_items = load(inv)["items"]
    end = events(g_out, "gather_end")[0]["data"]
    p, _ = env.run("--mode", "quan", "--seed", "1", "--inventory", inv, "--ticks", "0", "--out", q_out)
    if p.returncode:
        return rep.add("CP2", "AC-P3-01/05", "Smoke bàn giao file", False, f"quan mã {p.returncode}: {p.stderr.strip()[:150]}")
    stock0 = snaps(q_out)[0]["stock"]
    expect_fresh = [100 - 0.5 / 60, 57.5 - 0.5 / 60]  # hao đúng một bước gather trước khi cập bến
    # File giữ đủ độ chính xác (so tuyệt đối); JSONL (gather_end, snapshot) làm tròn — so theo dung sai ±0.01.
    ok = (end["reason"] == "docked" and same_items(end["inventory"]["items"], file_items) and same_items(file_items, stock0)
          and all(abs(i["fresh"] - f) < 1e-9 for i, f in zip(file_items, expect_fresh)))
    rep.add("CP2", "AC-P3-01/05", "gather --inventory-out → quan --inventory --ticks 0 (id/kind/fresh)", ok,
            f"file (đủ chính xác)={file_items} · gather_end={end['inventory']['items']} · stock quán @0={stock0}")


def cp3_reject(rep, env, tmp):
    cases = {
        "kho đếm v1.1": {"items": {"ca_loc": 1}},
        "id trùng": {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 90}, {"id": "I1", "kind": "ca_linh", "fresh": 90}]},
        "kind lạ": {"items": [{"id": "I1", "kind": "ca_ho", "fresh": 90}]},
        "fresh 100.1": {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100.1}]},
        "fresh âm": {"items": [{"id": "I1", "kind": "ca_loc", "fresh": -0.1}]},
        "thiếu fresh": {"items": [{"id": "I1", "kind": "ca_loc"}]},
    }
    got = {}
    for name, obj in cases.items():
        path = os.path.join(tmp, f"bad-{len(got)}.json")
        write_json(path, obj)
        p, _ = env.run("--mode", "quan", "--seed", "1", "--inventory", path, "--ticks", "0", "--out", os.path.join(tmp, "x.jsonl"))
        got[name] = p.returncode
    nan = os.path.join(tmp, "nan.json")
    with open(nan, "w") as f:
        f.write('{"items":[{"id":"I1","kind":"ca_loc","fresh":NaN}]}')
    got["fresh NaN"] = env.run("--mode", "quan", "--seed", "1", "--inventory", nan, "--ticks", "0", "--out", os.path.join(tmp, "x.jsonl"))[0].returncode
    rep.add("CP3", "AC-P3-01", "v1.2 trả mã 2 cho kho đếm / sai schema", all(v == 2 for v in got.values()),
            " · ".join(f"{k}→{v}" for k, v in got.items()))


def cp4_rereserve(rep, env):
    base = {"random_customers": False,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]}
    res = {}
    for tag, stock in (("thay", [{"id": "I1", "kind": "ca_loc", "fresh": 30.001}, {"id": "I2", "kind": "ca_loc", "fresh": 90}]),
                       ("thiếu", [{"id": "I1", "kind": "ca_loc", "fresh": 30.001}])):
        sc, out = P(f"cp4-{'swap' if tag == 'thay' else 'short'}.scenario.json"), P(f"cp4-{'swap' if tag == 'thay' else 'short'}.jsonl")
        write_json(sc, {"quan": dict(base, stock=stock)})
        p, _ = env.run("--mode", "quan", "--seed", "1", "--scenario", sc, "--ticks", "2", "--snapshot-every", "1", "--out", out)
        if p.returncode:
            return rep.add("CP4", "AC-P3-03", "Giữ lại khi ươn", False, f"mã {p.returncode}: {p.stderr.strip()[:150]}")
        s1 = next(s for s in snaps(out) if s["tick"] == 1)["customers"][0]
        res[tag] = (events(out, "spoiled"), s1["reserved"], s1["order_status"])
    ok = (res["thay"][0] and res["thay"][0][0]["tick"] == 1 and res["thay"][0][0]["data"]["location"] == "stock"
          and res["thay"][1:] == (["I2"], "reserved") and res["thiếu"][1:] == ([], "unfulfillable"))
    rep.add("CP4", "AC-P3-03", "Phần giữ vừa ươn → spoiled, giữ lại I2; không đủ → unfulfillable", ok,
            f"có I2: reserved={res['thay'][1]} {res['thay'][2]} · chỉ I1: reserved={res['thiếu'][1]} {res['thiếu'][2]}")


def cp5_price(rep, env):
    sc, ip, out = P("cp5-price.scenario.json"), P("cp5-price.inputs.json"), P("cp5-price.jsonl")
    write_json(sc, {"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 50.25}], "random_customers": False,
                             "player": {"pos": [2, 7]},
                             "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]}})
    write_json(ip, {"frames": [{"tick": 59, "interact": True}]})
    p, _ = env.run("--mode", "quan", "--seed", "1", "--scenario", sc, "--inputs", ip, "--ticks", "61", "--out", out)
    if p.returncode:
        return rep.add("CP5", "AC-P3-04", "Giá theo độ tươi", False, f"mã {p.returncode}: {p.stderr.strip()[:150]}")
    cs = events(out, "cook_started")
    d = cs[0]["data"] if cs else {}
    ok = bool(cs) and d["base_price"] == 30 and d["items"] == [{"id": "I1", "kind": "ca_loc", "fresh": 50}] and cs[0]["tick"] == 60
    rep.add("CP5", "AC-P3-04", "Hao 60 bước ở quán (50.25 → 50) rồi nấu: floor(60 × 50/100) = 30", ok, json.dumps(d, ensure_ascii=False))


def _day_frames(frames):
    merged = {}
    for fr in frames:
        merged.setdefault(fr["tick"], {}).update(fr)
    return {"frames": [merged[t] for t in sorted(merged)]}


def cp6_day(rep, env):
    sc, ip, out = P("cp6-day.scenario.json"), P("cp6-day.inputs.json"), P("cp6-day.jsonl")
    write_json(sc, {"gather": {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 80}],
                               "random_fish": False, "monsters": []},
                    "quan": {"time_left_ticks": 120, "random_customers": False}})
    frames = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}]

    def go():
        write_json(ip, _day_frames(frames))
        return env.run("--mode", "day", "--seed", "1", "--days", "2", "--scenario", sc, "--inputs", ip,
                       "--ticks", "2000", "--snapshot-every", "1", "--out", out)

    p, _ = go()
    if p.returncode:
        return rep.add("CP6", "AC-P3-05", "Day 2 ngày cá thể", False, f"mã {p.returncode}: {p.stderr.strip()[:150]}")
    q1 = next(e["tick"] for e in events(out, "phase_start") if e["phase"] == "quan" and e["day"] == 1)
    frames += [{"tick": q1 + 10, "pause": True}, {"tick": q1 + 11, "pause": False}, {"tick": q1 + 50, "pause": True}]
    p, _ = go()
    g2 = next(e["tick"] for e in events(out, "phase_start") if e["phase"] == "gather" and e["day"] == 2)
    frames += [{"tick": g2, "interact": True}, {"tick": g2 + 1, "interact": False}]
    p, _ = go()
    end1 = next(e for e in events(out, "gather_end") if e["day"] == 1)["data"]["inventory"]["items"]
    ss = snaps(out)
    q0 = next(s for s in ss if s["phase"] == "quan" and s["day"] == 1 and s["phase_tick"] == 0)
    paused = [s for s in ss if s["state"] == "paused"]
    shop = [s for s in ss if s["phase"] == "shop" and s["day"] == 1]
    g2s = next(s for s in ss if s["phase"] == "gather" and s["day"] == 2 and s["phase_tick"] == 0)
    hand_ok = same_items(end1, q0["stock"]) and q0["tick"] == next(e["tick"] for e in events(out, "gather_end") if e["day"] == 1)
    pause_ok = len(paused) >= 30 and all(s["stock"] == paused[0]["stock"] for s in paused)
    shop_ok = len(shop) > 100 and all(s["stock"] == shop[0]["stock"] for s in shop)
    ids1 = {i["id"] for i in end1}
    d2 = [(i["id"], i["kind"], i["fresh"]) for i in g2s["hold"]]
    id_ok = [x[0] for x in d2] == ["I3", "I4"] and not ids1 & {x[0] for x in d2} and [x[2] for x in d2] == [100, 80]
    ok = hand_ok and pause_ok and shop_ok and id_ok
    rep.add("CP6", "AC-P3-05", "Day: bàn giao cùng tick, pause/Shop không hao, id Ngày 2 cấp mới", ok,
            f"bàn giao={hand_ok} (tick {q0['tick']}) · pause {len(paused)} snapshot đứng={pause_ok} · Shop {len(shop)} snapshot đứng={shop_ok}"
            f" · hold D2={d2}")


def cp7_determinism(rep, env):
    a, b = P("det_day_v12_run1.jsonl"), P("det_day_v12_run2.jsonl")
    for o in (a, b):
        env.run("--mode", "day", "--seed", "7", "--days", "1", "--ticks", "3000", "--snapshot-every", "300", "--out", o)
    rep.add("CP7", "AC-P3-05", "Tất định day v1.2 (seed 7, 3.000 tick × 2)", filecmp.cmp(a, b, shallow=False), f"sha256 {sha(a)} / {sha(b)}")


def suite(cwd):
    env = dict(os.environ, PYTHONPATH="tests:.")
    p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=cwd,
                       capture_output=True, text=True, env=env)
    out = p.stderr + p.stdout
    bad = sorted({ln.split(" ", 1)[1].split(" ")[0] + " (" + ln.split("(")[1].split(".")[0] + ")"
                  for ln in out.splitlines() if ln.startswith(("FAIL:", "ERROR:"))})
    last = [ln for ln in p.stderr.strip().splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
    return p.returncode, " · ".join(last), bad, out


def cp8_regression(rep, env):
    rc, summary, bad, log = suite(ROOT)
    with open(P("test_suite.log"), "w", encoding="utf-8") as f:
        f.write(log)
    rep.add("CP8a", "AC-P3-06", f"Regression trên manifest repo ({env.repo_version})", rc == 0, summary)
    if env.cwd == ROOT:
        return
    rc2, summary2, bad2, log2 = suite(env.cwd)
    with open(P("test_suite_v12.log"), "w", encoding="utf-8") as f:
        f.write(log2)
    rep.add("CP8b", "AC-P3-06", "Toàn suite khi bật 1.2 (bản sao)", "PASS" if rc2 == 0 else "INFO",
            f"{summary2} · test còn dùng fixture kho đếm cần chủ lát đổi: {', '.join(bad2) if bad2 else 'không'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    os.makedirs(PROOF, exist_ok=True)
    git = lambda *c: subprocess.run(["git", *c], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    commit = git("rev-parse", "--short", "HEAD") + (" (+ thay đổi chưa commit)" if git("status", "--porcelain") else "")
    rep = Report()
    with tempfile.TemporaryDirectory() as tmp:
        env = Env(tmp)
        print("Chế độ:", env.mode)
        for cp in (cp1_spoil_threshold, cp2_file_handoff, lambda r, e: cp3_reject(r, e, tmp),
                   cp4_rereserve, cp5_price, cp6_day, cp7_determinism):
            try:
                cp(rep, env)
            except Exception as ex:  # ghi lỗi thật
                rep.add("CP?", "", getattr(cp, "__name__", "cp"), False, f"lỗi kiểm: {type(ex).__name__}: {ex}")
        if not a.quick:
            cp8_regression(rep, env)
        md = ["# QA Phase 3 · báo cáo tự động (`python3 tools/qa_p3.py`)", "",
              f"- Commit: `{commit}`", f"- Chế độ chạy CP1–CP7: **{env.mode}**",
              f"- Máy đo: {platform.platform()} · Python {platform.python_version()}",
              f"- Thời điểm: {time.strftime('%Y-%m-%d %H:%M:%S')}", "",
              "| CP | AC | Kiểm tra | Kết quả | Chi tiết |", "|---|---|---|---|---|"]
        md += [f"| {c} | {ac} | {n} | **{s}** | {d} |" for c, ac, n, s, d in rep.items]
    with open(P("qa-report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    return 1 if any(s == "FAIL" for *_, s, _ in rep.items) else 0


if __name__ == "__main__":
    sys.exit(main())
