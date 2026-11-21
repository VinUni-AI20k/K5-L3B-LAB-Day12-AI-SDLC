"""Smoke hộp đen hai tiến trình gather -> kho -> quan (PRD-0 mục G). Chỉ dùng thư viện chuẩn.

Chạy từ gốc repo: python3 .agents/skills/smoke-hai-tien-trinh/smoke.py [--proof <thư mục>]
"""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
EXPECTED = {"bong_sung": 2, "ca_loc": 1}
BAD_INVENTORIES = {  # v1.2 (TICKET-03): kho cá thể; kho đếm cũ cũng phải mã 2
    "kho_dem_v11": {"items": {"ca_loc": 1}},
    "kind_la": {"items": [{"id": "I1", "kind": "ca_tra", "fresh": 50}]},
    "id_trung": {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 50}, {"id": "I1", "kind": "ca_loc", "fresh": 40}]},
    "fresh_ngoai_mien": {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100.5}]},
    "khoa_goc_la": {"items": [], "money": 0},
}
DOCK_HOLD = [{"id": "I1", "kind": "ca_linh", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 100},
             {"id": "I3", "kind": "ca_loc", "fresh": 100}]


def headless_cmd():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        cmd = shlex.split(json.load(f)["headless_cmd"])
    if cmd and cmd[0] in ("python3", "python"):
        cmd[0] = sys.executable  # Windows thường không có `python3`
    return cmd


def run(*args):
    p = subprocess.run([*headless_cmd(), *args], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stderr.strip()


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proof", help="thư mục lưu bằng chứng (smoke.txt + jsonl + kho)")
    opt = ap.parse_args()

    results = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    w = tempfile.mkdtemp(prefix="smoke-p1-")
    p = lambda name: os.path.join(w, name)  # noqa: E731
    try:
        # 0. ngưỡng ươn (fixture TICKET-03): fresh 30, một bước không input -> spoiled ở tick 1
        write_json(p("spoil.json"), {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
                                                "random_fish": False, "monsters": []}})
        code, err = run("--mode", "gather", "--seed", "1", "--scenario", p("spoil.json"), "--ticks", "1",
                        "--out", p("spoil.jsonl"))
        ev = [r for r in read_jsonl(p("spoil.jsonl")) if r.get("type") == "event"] if code == 0 else []
        want = [{"type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
                 "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}]
        check("fresh 30 -> spoiled đúng tick 1", ev == want, f"mã={code} ev={ev} {err}")

        write_json(p("dock.json"), {"gather": {"hold": DOCK_HOLD, "random_fish": False, "monsters": []}})
        write_json(p("dock-inputs.json"), {"frames": [{"tick": 0, "interact": True}]})

        # 1-2. gather cập bến, ghi kho
        code, err = run("--mode", "gather", "--seed", "42", "--scenario", p("dock.json"),
                        "--inputs", p("dock-inputs.json"), "--ticks", "600",
                        "--out", p("gather.jsonl"), "--inventory-out", p("kho.json"))
        check("gather chạy, mã 0", code == 0, err)
        rows = read_jsonl(p("gather.jsonl")) if code == 0 else []
        end = rows[-1] if rows else {}
        check("gather kết thúc docked", end.get("reason") == "docked", f"reason={end.get('reason')}")
        kho = None
        if os.path.exists(p("kho.json")):
            with open(p("kho.json"), encoding="utf-8") as f:
                kho = json.load(f)
        items = (kho or {}).get("items")
        after_one = 100 - 0.5 / 60  # hao giỏ ở bước gather duy nhất
        ok = (isinstance(items, list) and [(i["id"], i["kind"]) for i in items] ==
              [("I1", "ca_linh"), ("I2", "bong_sung"), ("I3", "ca_loc")]
              and all(abs(i["fresh"] - after_one) < 1e-9 for i in items))
        check("kho.json mảng cá thể sắp id, fresh sau 1 bước hao", ok, f"kho={kho}")
        ge = [r for r in rows if r.get("type") == "event" and r.get("name") == "gather_end"]
        gi = ge[0]["data"]["inventory"]["items"] if len(ge) == 1 else []
        check("kho.json khớp gather_end.inventory (id/kind, fresh ±0.01)",
              ok and [(i["id"], i["kind"]) for i in gi] == [(i["id"], i["kind"]) for i in items]
              and all(abs(a["fresh"] - b["fresh"]) <= 0.01 for a, b in zip(gi, items)), f"{len(ge)} gather_end")

        # 3. quan đọc kho
        code, err = run("--mode", "quan", "--seed", "42", "--inventory", p("kho.json"),
                        "--ticks", "0", "--out", p("quan.jsonl"))
        snap = read_jsonl(p("quan.jsonl"))[0] if code == 0 else {}
        st = snap.get("stock") or []
        check("quan snapshot tick 0: đúng id, kind, độ tươi như file",
              snap.get("tick") == 0 and items is not None and [(i["id"], i["kind"]) for i in st] ==
              [(i["id"], i["kind"]) for i in items] and all(abs(a["fresh"] - b["fresh"]) <= 0.01 for a, b in zip(st, items)),
              f"mã={code} stock={st} {err}")

        # 4. chạm --ticks trước khi xong -> không ghi kho
        code, err = run("--mode", "gather", "--seed", "42", "--ticks", "5",
                        "--out", p("cut.jsonl"), "--inventory-out", p("cut-kho.json"))
        check("tick_limit không tạo file kho", code == 0 and not os.path.exists(p("cut-kho.json")), err)

        # 5. kho sai -> mã 2
        for name, inv in BAD_INVENTORIES.items():
            write_json(p(f"bad-{name}.json"), inv)
            code, _ = run("--mode", "quan", "--seed", "1", "--inventory", p(f"bad-{name}.json"),
                          "--ticks", "0", "--out", p(f"bad-{name}.jsonl"))
            check(f"kho sai ({name}) -> mã 2", code == 2, f"mã={code}")

        lines = [f"{'ĐẠT ' if ok else 'TRƯỢT'} | {name}" + (f" | {d}" if d and not ok else "")
                 for name, ok, d in results]
        passed = sum(ok for _, ok, _ in results)
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            declared = json.load(f)["headless_cmd"]
        lines.append(f"\n{passed}/{len(results)} mục đạt · headless_cmd: {declared}")
        report = "\n".join(lines)
        print(report)

        if opt.proof:
            out = os.path.join(ROOT, opt.proof)
            os.makedirs(out, exist_ok=True)
            with open(os.path.join(out, "smoke.txt"), "w", encoding="utf-8", newline="\n") as f:
                f.write(report + "\n")
            for name in ("dock.json", "dock-inputs.json", "gather.jsonl", "kho.json", "quan.jsonl"):
                if os.path.exists(p(name)):
                    shutil.copy(p(name), os.path.join(out, "smoke-" + name))
            print(f"Đã lưu bằng chứng vào {opt.proof}")
        return 0 if passed == len(results) else 1
    finally:
        shutil.rmtree(w, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
