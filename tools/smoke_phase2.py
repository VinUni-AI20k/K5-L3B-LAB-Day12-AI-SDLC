"""Smoke tích hợp Phase 2 (P2-09, phút 20) chạy bằng lệnh headless thật (hộp đen), thoát 1 nếu có mục đỏ.

    python3 tools/smoke_phase2.py

Kiểm luồng gather --inventory-out -> quan --inventory theo luật v1.1 (quán 2 bếp, 4 bàn, 6 món): cá thể sinh động
(fish_spawned), kho bàn giao, khách chỉ gọi món có trong menu v1.1, tất định từng byte qua hai
lần chạy. (`pause` và chế độ day: kiểm ở P2-10.) Chỉ dùng thư viện chuẩn.
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
