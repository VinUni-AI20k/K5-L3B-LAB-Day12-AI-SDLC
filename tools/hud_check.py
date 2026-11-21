"""Kiểm HUD (AC-P1-07) bằng snapshot thật và lưu bằng chứng vào docs/proof/<phase>/hud.md.

    python3 tools/hud_check.py --phase phase-1
    python3 tools/hud_check.py --phase phase-1 --cmd "python -m chonoi.headless"   # máy không có python3

Cần Node.js (chỉ cho công cụ này; game và test không cần). Các bước:
  1. Dựng 5 trạng thái bằng headless (snapshot do CHÍNH luật sim sinh ra): lặn 2 s; khách vừa đến
     (ván thật tới tick 130); bếp đang nấu; đang cầm món; khách đang ăn.
  2. Vẽ HUD của chonoi/web/index.html ở 4 bề rộng (1280/900/700/480) bằng tools/hud_harness.js.
  3. Kiểm: không lỗi vẽ; không chữ đè / tràn trong vùng HUD; đủ trường HUD tối thiểu của DoD PRD-0;
     kho khả dụng = tồn − phần giữ (tính độc lập từ snapshot); khách đang ăn hiện thời gian ăn.
Mã thoát: 0 đạt, 1 không đạt. Chỉ dùng thư viện chuẩn Python + Node.
"""

import argparse
import datetime
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIND = {"ca_loc": "cá lóc", "ca_linh": "cá linh", "bong_dien_dien": "điên điển", "bong_sung": "bông súng"}
D = {"order_id": "C1", "dish_id": "lau_ca_linh_dien_dien", "base_price": 120}
C = {"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien"}
ITEMS = lambda *pairs: [{"id": f"I{i + 1}", "kind": kind, "fresh": fresh} for i, (kind, fresh) in enumerate(pairs)]
STATES = [  # (tên, mode, scenario, inventory, inputs, tick lấy snapshot)
    ("gather_lan_2s", "gather", {"hold": ITEMS(("ca_linh", 100), ("bong_sung", 29.5)), "random_fish": False, "nodes": []}, None,
     {"frames": [{"tick": 0, "move": [1, 1]}]}, 120),
    ("quan_khach_vua_den", "quan", None, {"items": ITEMS(("ca_loc", 100), ("ca_loc", 97.5), ("bong_sung", 75), ("bong_sung", 75), ("ca_linh", 90), ("ca_linh", 90), ("bong_dien_dien", 100))},
     None, 130),
    ("quan_bep_dang_nau", "quan", {"random_customers": False, "stock": ITEMS(("ca_loc", 100), ("bong_sung", 96), ("bong_sung", 70), ("ca_linh", 84)),
     "stoves": [{"id": "B1", "state": "cooking", "dish": D, "cook_ticks_left": 400}],
     "customers": [dict(C, order_status="assigned", reserved=[], base_price=120, patience_ticks_left=2500)]},
     None, None, 0),
    ("quan_dang_cam_mon", "quan", {"random_customers": False, "stock": ITEMS(("ca_loc", 100)), "hand": D,
     "customers": [dict(C, order_status="assigned", reserved=[], base_price=120, patience_ticks_left=900)]},
     None, None, 0),
    ("quan_khach_dang_an", "quan", {"random_customers": False, "stock": ITEMS(("ca_loc", 29)), "reputation": 4.2,
     "customers": [dict(C, state="eating", order_status="served", reserved=[], base_price=120, tip=24,
                        eat_ticks_left=300)]}, None, None, 0),
]
REQUIRED = {  # DoD PRD-0: HUD tối thiểu
    "gather": [("thời gian", r"^Còn \d+:\d\d$"), ("oxy", r"^Oxy \d+s$"), ("Máu", r"^[♥♡]+$"),
               ("giỏ", r"^GIỎ \d+/\d+$")],
    "quan": [("thời gian", r"^Còn \d+:\d\d$"), ("kho khả dụng", r"^KHO KHẢ DỤNG$"), ("món gọi + kiên nhẫn", r"^T1: "),
             ("trạng thái bếp", r"^B1: "), ("món trên tay", r"^ĐANG CẦM: "), ("tiền", r"^Tiền -?\d+k$"),
             ("uy tín", r"^Uy tín \d+\.\d/5$")],
}
FRESH_REQUIRED = {
    "gather": ("độ tươi trong giỏ / dấu hàng ươn", r"\d{1,3}%|ƯƠN"),
    "quan": ("độ tươi trong kho / dấu hàng ươn", r"\d{1,3}%|ƯƠN"),
}


def available_text(snap):
    stock = snap.get("stock") or []
    if isinstance(stock, list):
        reserved = {item_id for c in snap.get("customers", []) for item_id in c.get("reserved", []) if isinstance(c.get("reserved"), list)}
        items = [i for i in stock if i.get("id") not in reserved]
        labels = [f"{KIND.get(i['kind'], i['kind'])} {round(float(i['fresh']))}%" + (" · ƯƠN" if float(i["fresh"]) < 30 else "") for i in items]
        return " · ".join(labels) or "Trống"
    avail = dict(stock)
    for c in snap.get("customers", []):
        if isinstance(c.get("reserved"), dict):
            for k, q in c["reserved"].items(): avail[k] = avail.get(k, 0) - q
    return " · ".join(f"{KIND[k]} ×{v}" for k, v in sorted(avail.items()) if v > 0) or "Trống"


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--phase", default="phase-1")
    ap.add_argument("--cmd", help="ghi đè headless_cmd (mặc định đọc game.contract.json)")
    a = ap.parse_args(argv)
    contract_path = os.path.join(ROOT, "game.contract.json")
    with open(contract_path, encoding="utf-8") as f:
        cmd_str = a.cmd or json.load(f)["headless_cmd"]
    out_dir = os.path.join(ROOT, "docs", "proof", a.phase)
    rel_out = os.path.relpath(out_dir, ROOT).replace(os.sep, "/")
    commit = _git("rev-parse", "--short", "HEAD")
    dirty = " (có thay đổi chưa commit)" if _git("status", "--porcelain", "--", ".", f":(exclude){rel_out}") else ""

    checks, snaps, pairs = [], {}, []
    with tempfile.TemporaryDirectory() as tmp:
        p = lambda n: os.path.join(tmp, n)
        for name, mode, sc, inv, inp, tick in STATES:
            args = ["--mode", mode, "--seed", "7", "--ticks", str(tick), "--snapshot-every", str(max(tick, 1)),
                    "--out", p(name + ".jsonl")]
            for flag, obj, fn in (("--scenario", {mode: sc} if sc else None, "sc"), ("--inventory", inv, "inv"),
                                  ("--inputs", inp, "in")):
                if obj is not None:
                    with open(p(f"{name}.{fn}.json"), "w", encoding="utf-8") as f:
                        json.dump(obj, f)
                    args += [flag, p(f"{name}.{fn}.json")]
            r = subprocess.run([*shlex.split(cmd_str), *args], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                checks.append((name, "headless dựng trạng thái", False, f"exit {r.returncode}: {r.stderr.strip()}"))
                continue
            with open(p(name + ".jsonl"), encoding="utf-8") as f:
                snap = next(json.loads(l) for l in f if '"type":"snapshot"' in l and f'"tick":{tick},' in l)
            snaps[name] = snap
            with open(p(name + ".snap.json"), "w", encoding="utf-8") as f:
                json.dump(snap, f, ensure_ascii=False)
            pairs.append(f"{name}={p(name + '.snap.json')}")
        html = open(os.path.join(ROOT, "chonoi", "web", "index.html"), encoding="utf-8").read()
        with open(p("client.js"), "w", encoding="utf-8") as f:
            f.write("\n".join(re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)))
        try:
            r = subprocess.run(["node", os.path.join(ROOT, "tools", "hud_harness.js"), p("client.js"), contract_path,
                                *pairs], capture_output=True, text=True, encoding="utf-8")
        except OSError:
            print("Cần Node.js để chạy tools/hud_harness.js", file=sys.stderr)
            return 1
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            return 1
        drawn = json.loads(r.stdout)

    hud_text = {}
    for name, snap in snaps.items():
        mode = snap["mode"]
        for W, res in drawn[name].items():
            tag = f"{name} @{W}px"
            if res["error"]:
                checks.append((tag, "vẽ không lỗi", False, res["error"]))
                continue
            hud = [t for t in res["texts"] if t["y1"] < 240]  # vùng HUD (v1.1: chữ 18 px, nhiều hàng)
            bad = []
            for i, t in enumerate(hud):
                if t["x1"] > int(W) + 1:
                    bad.append(f'tràn: "{t["s"]}"')
                for u in hud[i + 1:]:
                    if t["x0"] < u["x1"] and u["x0"] < t["x1"] and t["y0"] < u["y1"] and u["y0"] < t["y1"]:
                        bad.append(f'đè: "{t["s"]}" ↔ "{u["s"]}"')
            checks.append((tag, "không chữ đè / tràn", not bad, "; ".join(bad[:3])))
            if W == "1280":  # DoD v1.1: chữ không chân >= 18 px ở 1280x720 (mọi chữ trên màn hình)
                small = sorted({f'"{t["s"]}" {round(t["y1"] - t["y0"])}px' for t in res["texts"] if t["y1"] - t["y0"] < 18})
                checks.append((name, "mọi chữ >= 18 px ở 1280 px", not small, "; ".join(small[:4])))
            if W == "1280":
                strings = [t["s"] for t in hud]
                hud_text[name] = strings
                for label, pat in REQUIRED[mode]:
                    checks.append((name, f"có trường HUD: {label}", any(re.search(pat, s) for s in strings), ""))
                freshness_label, freshness_pat = FRESH_REQUIRED[mode]
                fresh_items = (snap.get("hold", []) if mode == "gather" else snap.get("stock", []))
                fresh_present = isinstance(fresh_items, list) and any("fresh" in i for i in fresh_items)
                shown_fresh = any(re.search(freshness_pat, s, re.I) for s in strings)
                checks.append((name, f"hiện {freshness_label}", fresh_present and shown_fresh, "snapshot không có cá thể hoặc HUD thiếu %/ƯƠN"))
                if mode == "quan":
                    want = available_text(snap)
                    i = strings.index("KHO KHẢ DỤNG") if "KHO KHẢ DỤNG" in strings else -1
                    got = strings[i + 1] if i >= 0 else None
                    checks.append((name, "kho khả dụng = tồn − giữ chỗ", got == want, f"HUD: {got!r}, cần: {want!r}"))
                    eating = [c for c in snap["customers"] if c["state"] == "eating"]
                    if eating:
                        ok = any("đang ăn" in s for s in strings)
                        checks.append((name, "khách đang ăn hiện thời gian ăn", ok, ""))

    passed = bool(checks) and all(ok for *_, ok, _ in checks)
    os.makedirs(out_dir, exist_ok=True)
    fails = [c for c in checks if not c[2]]
    md = [f"# Kiểm HUD (AC-P1-07) — {a.phase}", "",
          f"- Thời điểm: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
          f"- Commit: `{commit}`{dirty}",
          f"- Lệnh: `python3 tools/hud_check.py --phase {a.phase}`" + (f" (headless: `{cmd_str}`)" if a.cmd else ""),
          f"- Kết quả: **{'ĐẠT' if passed else 'CHƯA ĐẠT'}** — {len(checks) - len(fails)}/{len(checks)} mục kiểm", "",
          "Cách kiểm: snapshot do luật sim sinh ra (headless) → vẽ HUD của `chonoi/web/index.html` bằng canvas giả "
          "(`tools/hud_harness.js`) ở 4 bề rộng 1280/900/700/480 → kiểm lỗi vẽ, chữ đè/tràn, đủ trường HUD tối thiểu "
          "của DoD, kho khả dụng tính độc lập từ snapshot. Bề rộng chữ là ước lượng (ký tự × cỡ × 0.56).", "",
          "## Mục không đạt", ""]
    md += [f"- {n} — {what}: {d}" for n, what, _, d in fails] or ["(không có)"]
    md += ["", "## Chữ HUD hiển thị ở 1280px (theo trạng thái)", ""]
    for name, strings in hud_text.items():
        md.append(f"- **{name}**: " + " · ".join(f"`{s}`" for s in strings))
    md += ["", "## Toàn bộ mục kiểm", "", "| Trạng thái | Kiểm | Kết quả | Chi tiết |", "|---|---|---|---|"]
    md += [f"| {n} | {what} | {'đạt' if ok else 'CHƯA ĐẠT'} | {d} |" for n, what, ok, d in checks]
    with open(os.path.join(out_dir, "hud.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")
    for n, what, ok, d in fails:
        print(f"[FAIL] {n} — {what}: {d}")
    print(f"{'ĐẠT' if passed else 'CHƯA ĐẠT'} {len(checks) - len(fails)}/{len(checks)} — bằng chứng: {rel_out}/hud.md")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
