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


def contract_version():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["contract_version"]


def contract_all():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)


# Test Phase 2 chỉ chạy khi game.contract.json đã chuyển sang v1.1 (Integrator đổi khi tích hợp xong),
# để nhánh chính không đỏ trong lúc các lát Phase 2 đang làm. Khi đổi sang 1.1, các test này tự bật.
import unittest  # noqa: E402

requires_v11 = unittest.skipUnless(contract_version() == "1.1", "chờ contract_version 1.1 (Phase 2)")


def run_day(w, scenario=None, inp=None, days=1, ticks=10, every=1, seed=1):
    """Chạy `--mode day` với scenario nhiều khối ({day, gather, quan}); trả danh sách dòng JSONL."""
    scenario = {} if scenario is None else dict(scenario)
    if "quan" in scenario and "random_reservations" not in scenario["quan"] and "reservations" not in scenario["quan"]:
        scenario["quan"] = dict(scenario["quan"], random_reservations=False)
    args = ["--mode", "day", "--days", str(days), "--seed", str(seed), "--ticks", str(ticks),
            "--snapshot-every", str(every), "--out", w.path("o.jsonl")]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), scenario)]
    if inp is not None:
        args += ["--inputs", write_json(w.path("in.json"), inp)]
    code, err = run_headless(*args)
    assert code == 0, f"headless thoát mã {code}: {err}"
    return read_jsonl(w.path("o.jsonl"))


def run_mode(w, mode, block, inp=None, ticks=10, every=1, inv_out=None, seed=1):
    """Chạy headless với scenario `{mode: block}` và inputs tùy chọn; trả danh sách dòng JSONL.

    `every=1` cho snapshot mỗi tick để đọc trạng thái tại tick bất kỳ.
    """
    block = dict(block)
    if mode == "quan" and "random_reservations" not in block and "reservations" not in block:
        block["random_reservations"] = False
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
