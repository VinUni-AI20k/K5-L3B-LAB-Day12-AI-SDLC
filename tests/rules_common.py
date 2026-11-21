"""Tiện ích dùng chung cho test luật của nhóm (test_rules_*.py).

Tách khỏi tests/helpers.py (khung của giảng viên, hạn chế sửa). Mọi test luật đều là hộp đen:
chỉ chạy `headless_cmd` rồi đọc JSONL / file kho, nên dùng được với mọi ngôn ngữ.
"""

import json

from helpers import read_jsonl, run_headless, snapshots, write_json


def contract_tuning(mode):
    """Số liệu của một mode, đọc từ game.contract.json (không hard-code số trong test)."""
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"][mode]


def run_mode(w, mode, block, inp=None, ticks=10, every=1, inv_out=None, seed=1):
    """Chạy headless với scenario `{mode: block}` và inputs tùy chọn; trả danh sách dòng JSONL.

    `every=1` cho snapshot mỗi tick để đọc trạng thái tại tick bất kỳ.
    """
    args = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--snapshot-every", str(every),
            "--scenario", write_json(w.path("sc.json"), {mode: block}), "--out", w.path("o.jsonl")]
    if inp is not None:
        args += ["--inputs", write_json(w.path("in.json"), inp)]
    if inv_out:
        args += ["--inventory-out", inv_out]
    code, err = run_headless(*args)
    assert code == 0, f"headless thoát mã {code}: {err}"
    return read_jsonl(w.path("o.jsonl"))


def at(rows, tick):
    """Snapshot tại đúng `tick` (cần chạy với every sao cho tick đó có snapshot)."""
    return {s["tick"]: s for s in snapshots(rows)}[tick]
