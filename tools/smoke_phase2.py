"""Smoke tích hợp Phase 2 (P2-09, phút 20) chạy bằng lệnh headless thật (hộp đen), thoát 1 nếu có mục đỏ.

    python3 tools/smoke_phase2.py

Kiểm luồng gather --inventory-out -> quan --inventory theo luật v1.1 (quán 2 bếp, 4 bàn, 6 món): cá thể sinh động
(fish_spawned), kho bàn giao, khách chỉ gọi món có trong menu v1.1, tất định từng byte qua hai
lần chạy. pause ở gather và quan, `--mode day --days 2` chạy hết (thứ tự pha, days_complete), đầu vào day sai. Chỉ dùng thư viện chuẩn.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smoke_phase1 import check, RESULTS, ROOT, rows, run, sha, write  # noqa: E402

SHIFT = "10800"
DOCK_HOLD = ["ca_loc", "bong_sung", "bong_sung", "ca_linh", "ca_linh", "ca_keo", "keo_neo", "bong_dien_dien"]


def names(rs, name):
    return [r for r in rs if r["type"] == "event" and r["name"] == name]


def main():
    t = tempfile.mkdtemp(prefix="smoke-p2-")
    p = lambda name: os.path.join(t, name)  # noqa: E731

    # 1. Bàn giao với kho dựng sẵn (v1.1): kho file = hold, quán dựng đúng 2 bếp, 4 bàn
    dock = write(p("dock.json"), {"gather": {"hold": DOCK_HOLD}})
    frames = write(p("frames.json"), {"frames": [{"tick": 0, "interact": True}]})
    code, err = run(["--mode", "gather", "--seed", "42", "--scenario", dock, "--inputs", frames, "--ticks", "1",
                     "--out", p("g.jsonl"), "--inventory-out", p("kho.json")])
    kho = json.load(open(p("kho.json"), encoding="utf-8")) if code == 0 else {}
    want = {}
    for k in DOCK_HOLD:
        want[k] = want.get(k, 0) + 1
    check("gather -> kho: file kho = hold dựng sẵn", code == 0 and kho == {"items": want}, f"mã {code}, kho {kho}")

    code, err = run(["--mode", "quan", "--seed", "42", "--inventory", p("kho.json"), "--ticks", SHIFT, "--out", p("q.jsonl")])
    q = rows(p("q.jsonl")) if code == 0 else [{}]
    s0 = q[0]
    check("quan v1.1: tick 0 có 2 bếp, 4 bàn, stock = kho",
          code == 0 and len(s0.get("stoves", [])) == 2 and len(s0.get("tables", [])) == 4 and s0.get("stock") == want,
          f"mã {code}, {len(s0.get('stoves', []))} bếp, {len(s0.get('tables', []))} bàn")
    menu = json.load(open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8"))["tuning"]["menu"]
    arrived = [r["data"].get("dish_id") for r in names(q, "customer_arrived")]
    check("quan: có khách đến, mọi món gọi nằm trong menu 6 món", len(menu) == 6 and bool(arrived) and set(arrived) <= set(menu),
          f"{len(arrived)} khách, {len(menu)} món menu")
    check("quan: ca đủ 10800 tick kết thúc quan_end", q[-1].get("type") == "end" and q[-1].get("reason") == "time"
          and names(q, "quan_end") != [], str(q[-1]))

    # 2. Ca gather thật rồi đưa kho sang quán, hai lần giống từng byte
    digests = []
    for k in (1, 2):
        c1, _ = run(["--mode", "gather", "--seed", "7", "--ticks", SHIFT, "--out", p(f"gf{k}.jsonl"),
                     "--inventory-out", p(f"kf{k}.json")])
        c2, _ = run(["--mode", "quan", "--seed", "7", "--ticks", SHIFT, "--inventory", p(f"kf{k}.json"),
                     "--out", p(f"qf{k}.jsonl")])
        digests.append((c1, c2, sha(p(f"gf{k}.jsonl")), sha(p(f"kf{k}.json")), sha(p(f"qf{k}.jsonl"))) if c1 == c2 == 0 else None)
    check("ca gather đủ -> quán đủ: mã 0 và giống từng byte qua 2 lần", digests[0] is not None and digests[0] == digests[1],
          "" if digests[0] else "mã thoát khác 0")
    gf = rows(p("gf1.jsonl"))
    check("gather: có fish_spawned (cá thể sinh động, P2-03)", len(names(gf, "fish_spawned")) > 0,
          f"{len(names(gf, 'fish_spawned'))} sự kiện")

    # 3. pause (v1.1) ở gather và quan: cạnh pause đầu -> paused (tick 2), sim đứng yên; cạnh kế (tick 6) -> resumed
    pause = write(p("pause.json"), {"frames": [{"tick": 2, "pause": True}, {"tick": 3, "pause": False},
                                               {"tick": 6, "pause": True}]})
    for mode, extra in (("gather", []), ("quan", ["--inventory", p("kho.json")])):
        code, _ = run(["--mode", mode, "--seed", "1", "--ticks", "10", "--inputs", pause, "--snapshot-every", "1",
                       "--out", p(f"pause-{mode}.jsonl"), *extra])
        r = rows(p(f"pause-{mode}.jsonl")) if code == 0 else []
        ev = [x["name"] for x in r if x["type"] == "event" and x["name"] in ("paused", "resumed")]
        snaps = {x["tick"]: x for x in r if x["type"] == "snapshot"}
        frozen = bool(snaps) and snaps[3]["state"] == "paused" and snaps[3]["sim_tick"] == snaps[2]["sim_tick"]
        check(f"{mode}: pause -> paused, đứng yên, resumed", code == 0 and ev == ["paused", "resumed"] and frozen,
              f"mã {code}, sự kiện {ev}")

    # 4. --mode day --days 2 chạy hết: thứ tự pha, ngày, days_complete, tất định
    runs = []
    for k in (1, 2):
        code, err = run(["--mode", "day", "--days", "2", "--seed", "3", "--ticks", "200000", "--snapshot-every", "600",
                         "--out", p(f"day{k}.jsonl")])
        runs.append((code, sha(p(f"day{k}.jsonl")) if code == 0 else None))
    d = rows(p("day1.jsonl")) if runs[0][0] == 0 else [{}]
    seq = [(r["day"], r["name"], r["phase"]) for r in d if r.get("type") == "event"
           and r["name"] in ("day_start", "day_plan", "phase_start", "gather_end", "quan_end", "shop_end")]
    want = []
    for day in (1, 2):
        want += [(day, "day_start", "gather"), (day, "day_plan", "gather"), (day, "phase_start", "gather"),
                 (day, "gather_end", "gather"), (day, "phase_start", "quan"), (day, "quan_end", "quan"),
                 (day, "phase_start", "shop"), (day, "shop_end", "shop")]
    check("day: thứ tự sự kiện qua 2 Ngày đúng mục 4.5", runs[0][0] == 0 and seq == want, f"mã {runs[0][0]}, {len(seq)} sự kiện")
    end = d[-1]
    check("day: kết thúc days_complete, days_completed = 2",
          end.get("type") == "end" and end.get("reason") == "days_complete" and end.get("days_completed") == 2, str(end))
    check("day: tất định từng byte qua 2 lần", runs[0][0] == runs[1][0] == 0 and runs[0][1] == runs[1][1])
    snap = next((r for r in d if r.get("type") == "snapshot" and r.get("phase") == "shop"), {})
    check("day: snapshot có day, day_plan, upgrades, active_upgrades",
          all(k in snap for k in ("day", "day_plan", "upgrades", "active_upgrades")), f"khóa {sorted(snap)[:6]}")

    # 5. đầu vào sai của chế độ day -> mã 2, không ghi tệp
    bad = {"--days 0": ["--days", "0"], "--days 6": ["--days", "6"], "--inventory với day": ["--inventory", p("kho.json")]}
    for name, extra in bad.items():
        out = p("bad.jsonl")
        if os.path.exists(out):
            os.remove(out)
        code, _ = run(["--mode", "day", "--seed", "1", "--ticks", "1", "--out", out, *extra])
        check(f"day: {name} -> mã 2", code == 2 and not os.path.exists(out), f"mã {code}")

    failed = [r for r in RESULTS if not r[1]]
    width = max(len(r[0]) for r in RESULTS)
    for name, ok, detail in RESULTS:
        print(f"{'OK  ' if ok else 'FAIL'} {name:<{width}}  {detail}")
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} mục đạt")
    return 1 if failed else 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
