"""Sinh bằng chứng Phase 2 vào docs/proof/phase-2/ (chạy ở commit sẽ gắn tag).

    python3 tools/proof_p2.py

Chạy: toàn bộ test; một ca sáng v1.1 trọn 180 s (cá sinh theo seed, cá bơi, sinh theo lịch); Cá Sấu chạm
và ngất (fixture); mode day 3 Ngày (gather → quan → shop); mã thoát 2 của `--days`; và kiểm tất định
(chạy lại cùng seed → giống từng byte). Chỉ dùng thư viện chuẩn. JSONL lưu đuôi .jsonl.txt vì
.gitignore bỏ qua *.jsonl.
"""

import datetime
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "proof", "phase-2")
PY = sys.executable
ENV = dict(os.environ, PYTHONUTF8="1",
           PYTHONPATH=os.pathsep.join(["tests", "."]),
           PATH=os.path.dirname(PY) + os.pathsep + os.environ.get("PATH", ""))
CONTRACT = json.load(open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8"))
G = CONTRACT["tuning"]["gather"]


def sh(args):
    p = subprocess.run(args, cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def headless(*args, expect=0):
    code, _, err = sh([PY, "-m", "chonoi.headless", *args])
    if code != expect:
        sys.exit(f"headless mã {code} (mong {expect}): {' '.join(args)}\n{err}")
    return err.strip()


def p(*parts):
    return os.path.join(OUT, *parts)


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def rows(path):
    return [json.loads(line) for line in read(path).splitlines() if line.strip()]


def evs(rs, *names):
    return [r for r in rs if r["type"] == "event" and (not names or r["name"] in names)]


def snaps(rs):
    return [r for r in rs if r["type"] == "snapshot"]


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def same_twice(args, out1, out2, extra=None):
    """Chạy headless 2 lần cùng tham số; trả True nếu JSONL (và file phụ) giống từng byte."""
    headless(*args, "--out", rel(out1), *(["--inventory-out", rel(extra[0])] if extra else []))
    headless(*args, "--out", rel(out2), *(["--inventory-out", rel(extra[1])] if extra else []))
    return sha(out1) == sha(out2) and (not extra or sha(extra[0]) == sha(extra[1]))


def in_band(f):
    lo, hi = G["fish_depths"][f["kind"]]
    return G["fish_x"][0] <= f["pos"][0] <= G["fish_x"][1] and lo <= f["pos"][1] <= hi


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    commit = sh(["git", "rev-parse", "--short", "HEAD"])[1].strip()
    dirty = sh(["git", "status", "--porcelain", "--", "chonoi", "tests", "game.contract.json"])[1].strip()
    tag_code, _, _ = sh(["git", "diff", "--quiet", "phase-2", "--", "chonoi", "tests", "game.contract.json"])
    tag_note = {0: " Code game, test và contract **giống hệt tag `phase-2`**.",
                1: " Code **khác** tag `phase-2`."}.get(tag_code, " (Chưa có tag `phase-2` lúc sinh.)")
    lines = []
    ok = lambda b: "ĐẠT" if b else "CHƯA ĐẠT"

    # 1. toàn bộ test
    code, out, err = sh([PY, "-m", "unittest", "discover", "-s", "tests", "-v"])
    write(p("tests-full.txt"), err + out)
    summary = [ln for ln in (err + out).splitlines() if ln.startswith("Ran ") or ln == "OK" or ln.startswith("FAILED")]
    lines.append(f"| Toàn bộ test (`unittest discover -s tests -v`) | [`tests-full.txt`](tests-full.txt) | {' · '.join(summary)} |")

    # 2. ca sáng v1.1, seed 1, không điều khiển: cá sinh theo seed, bơi, sinh theo lịch
    fd = p("fish")
    ticks = str(int(round(G["duration_s"] * 60)))
    g1, g2 = os.path.join(fd, "gather.jsonl.txt"), os.path.join(fd, "gather-rerun.jsonl.txt")
    os.makedirs(fd, exist_ok=True)
    same_g = same_twice(["--mode", "gather", "--seed", "1", "--ticks", ticks, "--snapshot-every", "60"], g1, g2)
    gr = rows(g1)
    first = snaps(gr)[0]["fish"]
    spawned = evs(gr, "fish_spawned")
    allsn = snaps(gr)
    band_ok = all(in_band(f) for s in allsn for f in s["fish"])
    pts = [tuple(f["pos"]) for f in first]
    init_ok = len(first) == G["fish_initial"] and len(set(pts)) == len(pts)
    lines.append(f"| Đầu ca seed 1: {G['fish_initial']} đàn ở điểm sinh khác nhau | [`fish/gather.jsonl.txt`](fish/gather.jsonl.txt) | "
                 + ", ".join(f"{f['id']} {f['kind']} {f['pos']}" for f in first) + f" → {ok(init_ok)} |")
    lines.append(f"| Sinh theo lịch mỗi {G['fish_spawn_ticks']} tick, trần {G['fish_max']} | `fish/gather.jsonl.txt` | "
                 + ", ".join(f"t{e['tick']} {e['data']['id']} {e['data']['kind']}" for e in spawned)
                 + f"; cuối ca {len(allsn[-1]['fish'])} đàn → {ok(len(allsn[-1]['fish']) == G['fish_max'])} |")
    lines.append(f"| Cá bơi trong x ∈ {G['fish_x']} và dải độ sâu loài ({len(allsn)} snapshot) | `fish/gather.jsonl.txt` | "
                 f"{ok(band_ok)}; tuổi F1 cuối ca `age_ticks` = {next(f['age_ticks'] for f in allsn[-1]['fish'] if f['id'] == 'F1') if any(f['id'] == 'F1' for f in allsn[-1]['fish']) else '—'} |")
    lines.append(f"| Tất định ca sáng (chạy lại seed 1) | `fish/gather-rerun.jsonl.txt` | sha256 {sha(g1)[:12]}… = {sha(g2)[:12]}… → "
                 f"{'GIỐNG TỪNG BYTE' if same_g else 'KHÁC'} |")

    # 3. Cá Sấu: chạm (mất hàng LIFO, bất tử) và ngất
    md = p("monsters")
    hold = ["ca_loc", "bong_sung", "ca_linh", "bong_sung"]
    croc = {"id": "M1", "kind": "ca_sau", "pos": [62, 24], "waypoints": [[60, 24], [64, 24]]}
    for name, player in (("hit", {"pos": [62, 24]}), ("faint", {"pos": [62, 24], "hp": 1})):
        write(os.path.join(md, f"{name}.json"), json.dumps({"gather": {"player": player, "random_fish": False,
                                                                     "hold": hold, "monsters": [croc]}}) + "\n")
        headless("--mode", "gather", "--seed", "1", "--ticks", "300", "--scenario", rel(os.path.join(md, f"{name}.json")),
                 "--out", rel(os.path.join(md, f"{name}.jsonl.txt")),
                 "--inventory-out", rel(os.path.join(md, f"{name}-kho.json")))
    hr = rows(os.path.join(md, "hit.jsonl.txt"))
    hits = evs(hr, "monster_hit")
    gaps = [b["tick"] - a["tick"] for a, b in zip(hits, hits[1:])]
    inv = G["monsters"]["invuln_ticks"]
    h0 = hits[0]["data"] if hits else {}
    hit_ok = bool(hits) and h0.get("lost") == ["bong_sung", "ca_linh"] and all(g >= inv for g in gaps)
    lines.append(f"| Cá Sấu chạm: mất floor(n × {G['monsters']['loss_ratio']}) hàng LIFO, bất tử {inv} tick | "
                 f"[`monsters/hit.jsonl.txt`](monsters/hit.jsonl.txt) | "
                 + ", ".join(f"t{e['tick']} hp {e['data']['hp']} mất {e['data']['lost']}" for e in hits)
                 + f"; khoảng cách giữa các lần chạm {gaps} → {ok(hit_ok)} |")
    fr = rows(os.path.join(md, "faint.jsonl.txt"))
    seq = [(e["tick"], e["name"]) for e in evs(fr)]
    fkho = json.loads(read(os.path.join(md, "faint-kho.json")))
    faint = evs(fr, "faint")
    faint_ok = [n for _, n in seq] == ["monster_hit", "faint", "gather_end"] and faint and \
        faint[0]["data"]["cause"] == "monster" and fkho == {"items": {}}
    lines.append(f"| Ngất do Cá Sấu (hp 1) | [`monsters/faint.jsonl.txt`](monsters/faint.jsonl.txt) | "
                 f"{seq}; faint `{json.dumps(faint[0]['data'] if faint else {}, ensure_ascii=False)}`; kho `{json.dumps(fkho)}` → {ok(faint_ok)} |")

    # 4. mode day 3 Ngày, không điều khiển
    dd = p("day")
    os.makedirs(dd, exist_ok=True)
    days = 3
    per_day = int(round(G["duration_s"] * 60)) + int(round(CONTRACT["tuning"]["quan"]["duration_s"] * 60)) \
        + CONTRACT["tuning"]["shop"]["max_ticks"]
    d1, d2 = os.path.join(dd, "day.jsonl.txt"), os.path.join(dd, "day-rerun.jsonl.txt")
    same_d = same_twice(["--mode", "day", "--days", str(days), "--seed", "1", "--ticks", str(per_day * days + 10),
                         "--snapshot-every", "600"], d1, d2)
    dr = rows(d1)
    flow = [f"t{e['tick']} N{e['day']} {e['name']}{'(' + e['phase'] + ')' if e['name'] == 'phase_start' else ''}"
            for e in evs(dr, "day_start", "phase_start", "gather_end", "quan_end", "shop_end")]
    end = dr[-1]
    lines.append(f"| Mode day {days} Ngày (gather → quan → shop) | [`day/day.jsonl.txt`](day/day.jsonl.txt) | "
                 f"{', '.join(flow)}; end `{end.get('reason')}`, days_completed {end.get('days_completed')} → "
                 f"{ok(end.get('reason') == 'days_complete' and end.get('days_completed') == days)} |")
    mons = {}
    for s in snaps(dr):
        if s.get("phase") == "gather" and "monsters" in s:
            mons.setdefault(s["day"], [m["id"] for m in s["monsters"]])
    want = {d: [m["id"] for m in G["monsters"]["spawns"] if m["from_day"] <= d] for d in range(1, days + 1)}
    lines.append(f"| Cá Sấu theo Ngày trong mode day (`from_day`) | `day/day.jsonl.txt` | thấy {mons}, contract mong {want} → "
                 f"{ok(mons == want)}{'' if mons == want else ' (chờ `day.py` truyền `GatherSim(..., day=self.day)`)'} |")
    lines.append(f"| Tất định mode day (chạy lại seed 1) | `day/day-rerun.jsonl.txt` | sha256 {sha(d1)[:12]}… = {sha(d2)[:12]}… → "
                 f"{'GIỐNG TỪNG BYTE' if same_d else 'KHÁC'} |")

    # 5. mã thoát 2 của --days (thoát trước khi ghi đầu ra)
    bad = os.path.join(dd, "bad.jsonl.txt")
    cases = [("--mode", "day", "--days", "0"), ("--mode", "day", "--days", "6"), ("--mode", "gather", "--days", "2")]
    res = []
    for c in cases:
        msg = headless(*c, "--seed", "1", "--ticks", "0", "--out", rel(bad), expect=2)
        res.append(f"`{' '.join(c)}` → 2 ({msg.splitlines()[-1] if msg else ''})")
    lines.append(f"| `--days` sai → mã 2, không ghi đầu ra | — | {'; '.join(res)}; file đầu ra "
                 f"{'KHÔNG tạo' if not os.path.exists(bad) else 'BỊ TẠO'} |")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    write(p("README.md"),
          "# Bằng chứng Phase 2\n\n"
          f"Sinh bằng `python3 tools/proof_p2.py` ở commit **`{commit}`**{' (code có thay đổi chưa commit!)' if dirty else ''}, lúc {now}.{tag_note}\n\n"
          "| Kiểm chứng | File | Kết quả |\n|---|---|---|\n" + "\n".join(lines) + "\n")
    print(read(p("README.md")))


if __name__ == "__main__":
    main()
