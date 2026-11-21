"""Sinh bằng chứng Phase 1 vào docs/proof/phase-1/ (chạy ở commit sẽ gắn tag).

    python3 tools/proof_p1.py

Chạy: toàn bộ test, smoke 2 tiến trình dock → quán (PRD-0 mục G), một lượt chơi thật sáng → tối
với preset mặc định (inputs/play-default.json), và kiểm tất định (chạy lại cùng seed → giống từng byte).
Chỉ dùng thư viện chuẩn. JSONL lưu đuôi .jsonl.txt vì .gitignore bỏ qua *.jsonl.
"""

import datetime
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "proof", "phase-1")
PY = sys.executable
ENV = dict(os.environ, PYTHONUTF8="1",
           PYTHONPATH=os.pathsep.join(["tests", "."]),
           PATH=os.path.dirname(PY) + os.pathsep + os.environ.get("PATH", ""))


def sh(args, **kw):
    p = subprocess.run(args, cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8", **kw)
    return p.returncode, p.stdout, p.stderr


def headless(*args):
    code, _, err = sh([PY, "-m", "chonoi.headless", *args])
    if code != 0:
        sys.exit(f"headless lỗi (mã {code}): {' '.join(args)}\n{err}")


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


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    commit = sh(["git", "rev-parse", "--short", "HEAD"])[1].strip()
    # chỉ coi là "bẩn" nếu code game/test/contract khác commit (file proof và script này không tính)
    dirty = sh(["git", "status", "--porcelain", "--", "chonoi", "tests", "game.contract.json"])[1].strip()
    # so code game/test/contract với tag phase-1 (nếu có): giống thì bằng chứng áp dụng cho commit gắn tag
    tag_code, _, _ = sh(["git", "diff", "--quiet", "phase-1", "--", "chonoi", "tests", "game.contract.json"])
    tag_note = {0: " Code game, test và contract **giống hệt tag `phase-1`**.",
                1: " Code **khác** tag `phase-1`."}.get(tag_code, "")
    lines = []

    # 1. toàn bộ test
    code, out, err = sh([PY, "-m", "unittest", "discover", "-s", "tests", "-v"])
    write(p("tests-full.txt"), err + out)
    summary = [ln for ln in (err + out).splitlines() if ln.startswith("Ran ") or ln in ("OK",) or ln.startswith("FAILED")]
    lines.append(f"| Toàn bộ test (`unittest discover -s tests -v`) | [`tests-full.txt`](tests-full.txt) | {' · '.join(summary)} |")

    # 2. smoke 2 tiến trình dock → quán (PRD-0 mục G)
    sm = p("smoke")
    write(os.path.join(sm, "dock.json"), json.dumps({"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}}) + "\n")
    write(os.path.join(sm, "dock-inputs.json"), json.dumps({"frames": [{"tick": 0, "interact": True}]}) + "\n")
    headless("--mode", "gather", "--seed", "42", "--scenario", rel(os.path.join(sm, "dock.json")),
             "--inputs", rel(os.path.join(sm, "dock-inputs.json")), "--ticks", "1",
             "--out", rel(os.path.join(sm, "gather.jsonl.txt")), "--inventory-out", rel(os.path.join(sm, "catch.json")))
    headless("--mode", "quan", "--seed", "42", "--inventory", rel(os.path.join(sm, "catch.json")),
             "--ticks", "0", "--out", rel(os.path.join(sm, "quan.jsonl.txt")))
    kho = json.loads(read(os.path.join(sm, "catch.json")))
    stock0 = rows(os.path.join(sm, "quan.jsonl.txt"))[0]["stock"]
    ok = kho == {"items": {"bong_sung": 2, "ca_loc": 1}} and stock0 == kho["items"]
    lines.append(f"| Smoke dock → quán (PRD-0 G) | [`smoke/`](smoke/) | kho `{json.dumps(kho['items'])}`, "
                 f"quán tick 0 `stock` `{json.dumps(stock0)}` → {'ĐẠT' if ok else 'CHƯA ĐẠT'} |")

    # 3. lượt chơi thật sáng → tối với preset mặc định
    pl = p("play")
    os.makedirs(pl, exist_ok=True)
    inp = rel(p("inputs", "play-default.json"))
    g1, g2 = os.path.join(pl, "gather.jsonl.txt"), os.path.join(pl, "gather-rerun.jsonl.txt")
    k1, k2 = os.path.join(pl, "kho.json"), os.path.join(pl, "kho-rerun.json")
    headless("--mode", "gather", "--seed", "1", "--inputs", inp, "--ticks", "10800", "--out", rel(g1), "--inventory-out", rel(k1))
    headless("--mode", "gather", "--seed", "1", "--inputs", inp, "--ticks", "10800", "--out", rel(g2), "--inventory-out", rel(k2))
    q = os.path.join(pl, "quan.jsonl.txt")
    headless("--mode", "quan", "--seed", "1", "--inventory", rel(k1), "--ticks", "10800", "--snapshot-every", "600", "--out", rel(q))
    gr = rows(g1)
    evs = [f"t{r['tick']} {r['name']}" for r in gr if r["type"] == "event"]
    end_g, end_q = gr[-1], rows(q)[-1]
    same = sha(g1) == sha(g2) and sha(k1) == sha(k2)
    lines.append(f"| Chơi thật sáng (preset mặc định) | [`play/gather.jsonl.txt`](play/gather.jsonl.txt) | "
                 f"{', '.join(evs)}; end `{end_g['reason']}`; kho `{json.dumps(json.loads(read(k1))['items'])}` |")
    lines.append(f"| Quán đọc kho thật, trọn ca, không điều khiển (không ai nấu nên earned = 0, khách bỏ về) | [`play/quan.jsonl.txt`](play/quan.jsonl.txt) | "
                 f"end `{end_q['reason']}`, earned {end_q['earned']}, uy tín {end_q['reputation']}, điểm {end_q['score']} |")
    lines.append(f"| Tất định: chạy lại cùng seed | `play/*-rerun*` | sha256 JSONL {sha(g1)[:12]}… = {sha(g2)[:12]}…, "
                 f"kho {sha(k1)[:12]}… = {sha(k2)[:12]}… → {'GIỐNG TỪNG BYTE' if same else 'KHÁC'} |")

    # 4. ảnh HUD (chụp tay)
    for name, desc in (("hud-gather.png", "HUD sáng: thời gian, oxy, Máu, giỏ 12/12, `hold_full` ở N4"),
                       ("hud-quan.png", "HUD tối: thời gian, tiền, uy tín, điểm, kho, món khách gọi + thanh kiên nhẫn, "
                                        "bếp B1 đang nấu, log `customer_arrived`/`cook_started`")):
        have = os.path.exists(p(name))
        lines.append(f"| {desc} | {f'[`{name}`]({name})' if have else f'`{name}`'} | {'có' if have else 'CHƯA CHỤP'} |")

    notes = (
        "\n## Ghi chú trung thực về HUD (chơi thử)\n\n"
        "- HUD tối: nhãn món trên bếp B1 hiện `[object Object]`. `chonoi/web/index.html` in thẳng `stove.dish`, "
        "mà theo PRD-0 mục D đó là payload `{order_id, dish_id, base_price}`; cần in `dish.dish_id`.\n"
        "- HUD tối in `stock` (tồn vật lý, gồm phần khách giữ chỗ) chứ chưa phải \"kho khả dụng\" theo PRD-0 §2.\n"
        "- Cả hai lỗi chỉ ở hiển thị (file khung `chonoi/web/index.html`); luật, snapshot và JSONL vẫn đúng contract.\n"
    )
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    write(p("README.md"),
          "# Bằng chứng Phase 1\n\n"
          f"Sinh bằng `python3 tools/proof_p1.py` ở commit **`{commit}`**{' (code có thay đổi chưa commit!)' if dirty else ''}, lúc {now}.{tag_note}\n\n"
          "| Kiểm chứng | File | Kết quả |\n|---|---|---|\n" + "\n".join(lines) + "\n" + notes)
    print(read(p("README.md")))


if __name__ == "__main__":
    main()
