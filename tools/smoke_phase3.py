"""Smoke Phase 3 (P3-07, P3-08) bằng lệnh headless thật (hộp đen) với game.contract.json 1.2, thoát 1 nếu có mục đỏ.

    python3 tools/smoke_phase3.py

Kiểm bàn giao kho cá thể: `gather --inventory-out` (độ tươi 100 và 30) rồi `quan --inventory --ticks 0` ở hai tiến trình,
so id, kind, fresh trong snapshot tick 0 của quán với file kho; file kho đếm của v1.1 và scenario sai schema bị từ chối
(mã 2); ca gather và ca quán đủ giờ, chế độ day 2 Ngày chạy hết, tất định từng byte. Chỉ dùng thư viện chuẩn.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smoke_phase1 import RESULTS, ROOT, check, rows, run, sha, write  # noqa: E402

SHIFT = "10800"


def item(n, kind, fresh):
    return {"id": f"I{n}", "kind": kind, "fresh": fresh}


def names(rs, name):
    return [r for r in rs if r.get("type") == "event" and r["name"] == name]


def main():
    t = tempfile.mkdtemp(prefix="smoke-p3-")
    p = lambda name: os.path.join(t, name)  # noqa: E731
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        contract = json.load(f)
    check("game.contract.json là 1.2 và có khối freshness 4 khóa",
          contract["contract_version"] == "1.2" and set(contract["tuning"]["freshness"]) ==
          {"initial", "gather_decay_per_s", "quan_decay_per_s", "spoiled_below"})
    r = lambda args: run(args, v12=True)  # noqa: E731

    # 1. Bàn giao kho cá thể, hai tiến trình: fresh 100 và fresh 30
    hold = [item(1, "ca_loc", 100), item(2, "bong_sung", 30), item(3, "bong_sung", 100)]
    dock = write(p("dock.json"), {"gather": {"hold": hold}})
    frames = write(p("frames.json"), {"frames": [{"tick": 0, "interact": True}]})
    hashes = []
    for k in (1, 2):
        c1, e1 = r(["--mode", "gather", "--seed", "42", "--scenario", dock, "--inputs", frames, "--ticks", "1",
                    "--out", p(f"g{k}.jsonl"), "--inventory-out", p(f"kho{k}.json")])
        c2, e2 = r(["--mode", "quan", "--seed", "42", "--inventory", p(f"kho{k}.json"), "--ticks", "0",
                    "--out", p(f"q{k}.jsonl")])
        ok = c1 == 0 and c2 == 0
        hashes.append((sha(p(f"kho{k}.json")), sha(p(f"q{k}.jsonl"))) if ok else None)
        if k == 1:
            kho = json.load(open(p("kho1.json"), encoding="utf-8"))["items"] if ok else []
            stock = rows(p("q1.jsonl"))[0].get("stock") if ok else None
            check("bàn giao: snapshot tick 0 của quán = file kho (id, kind, fresh)", ok and stock == kho and len(kho) == 3,
                  f"mã {c1}/{c2}, kho {kho}")
            check("bàn giao: id và loại giữ nguyên, độ tươi 100 và 30 chỉ hao đúng 1 tick của gather",
                  ok and [(i["id"], i["kind"]) for i in kho] == [("I1", "ca_loc"), ("I2", "bong_sung"), ("I3", "bong_sung")]
                  and kho[0]["fresh"] == kho[2]["fresh"] < 100 and kho[1]["fresh"] < 30, str(kho))
            ev = names(rows(p("g1.jsonl")), "gather_end")
            check("gather_end.inventory là kho cá thể đúng file", ok and ev and ev[-1]["data"]["inventory"] == {"items": kho})
            sp = names(rows(p("g1.jsonl")), "spoiled")
            check("cá thể fresh 30 ươn ở tick đầu (xuống dưới ngưỡng), cá thể fresh 100 thì chưa",
                  ok and [e["data"]["id"] for e in sp] == ["I2"], str([e["data"] for e in sp]))
    check("bàn giao: file kho và JSONL quán giống từng byte qua 2 lần", hashes[0] is not None and hashes[0] == hashes[1])

    # 2. Quán đọc đúng fresh 100 và fresh 30 từ file kho dựng sẵn
    stock_in = [item(1, "ca_loc", 100), item(2, "ca_linh", 30)]
    c, _ = r(["--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", write(p("in.json"), {"items": stock_in}),
              "--out", p("qin.jsonl")])
    check("quan --inventory --ticks 0: fresh 100 và fresh 30 đọc đúng", c == 0 and rows(p("qin.jsonl"))[0]["stock"] == stock_in)

    # 3. Sai schema theo phiên bản
    for name, args in (("file kho đếm (v1.1) bị từ chối", ["--inventory", write(p("cnt.json"), {"items": {"ca_loc": 1}})]),
                       ("file kho cá thể trùng id bị từ chối", ["--inventory", write(p("dup.json"), {"items": [item(1, "ca_loc", 5), item(1, "ca_loc", 6)]})]),
                       ("file kho cá thể fresh vượt 100 bị từ chối", ["--inventory", write(p("hi.json"), {"items": [item(1, "ca_loc", 101)]})])):
        out = p("bad.jsonl")
        if os.path.exists(out):
            os.remove(out)
        c, _ = r(["--mode", "quan", "--seed", "1", "--ticks", "0", "--out", out, *args])
        check(f"quan v1.2: {name} -> mã 2, không ghi output", c == 2 and not os.path.exists(out), f"mã {c}")
    c, _ = r(["--mode", "gather", "--seed", "1", "--ticks", "0", "--out", p("kind.jsonl"),
              "--scenario", write(p("kind.json"), {"gather": {"hold": ["ca_loc"]}})])
    check("gather v1.2: hold dạng danh sách loại (v1.1) bị từ chối -> mã 2", c == 2, f"mã {c}")

    # 4. Ca đủ giờ và chế độ day
    c1, _ = r(["--mode", "gather", "--seed", "7", "--ticks", SHIFT, "--out", p("gf.jsonl"), "--inventory-out", p("kf.json")])
    c2, _ = r(["--mode", "quan", "--seed", "7", "--ticks", SHIFT, "--out", p("qf.jsonl"), "--inventory", p("kf.json")])
    check("ca gather đủ giờ rồi ca quán đủ giờ (v1.2): mã 0", c1 == 0 and c2 == 0)
    digests = []
    for k in (1, 2):
        c, _ = r(["--mode", "day", "--days", "2", "--seed", "3", "--ticks", "200000", "--snapshot-every", "600",
                  "--out", p(f"day{k}.jsonl")])
        digests.append((c, sha(p(f"day{k}.jsonl")) if c == 0 else None))
    end = rows(p("day1.jsonl"))[-1] if digests[0][0] == 0 else {}
    check("day --days 2 (v1.2): days_complete, tất định từng byte",
          digests[0][0] == digests[1][0] == 0 and digests[0][1] == digests[1][1] and end.get("reason") == "days_complete"
          and end.get("days_completed") == 2, str(end))

    failed = [x for x in RESULTS if not x[1]]
    width = max(len(x[0]) for x in RESULTS)
    for name, ok, detail in RESULTS:
        print(f"{'OK  ' if ok else 'FAIL'} {name:<{width}}  {detail}")
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} mục đạt")
    return 1 if failed else 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
