"""Tiện ích riêng cho test hộp đen của QA (PRD-0). Chỉ đọc JSONL / file kho, không import chonoi.

`pending("lát 2")`: test của lát CHƯA merge -> mặc định SKIP để main luôn xanh.
Chạy thật mọi test pending: đặt biến môi trường QA_STRICT=1. Lát xong và test xanh thì QA bỏ decorator.
"""

import json
import os
import unittest

from helpers import Workdir, frames, read_jsonl, run_headless, snapshots, write_json

STRICT = os.environ.get("QA_STRICT") == "1"


def pending(slice_name: str):
    """Đánh dấu test đang chờ một lát; QA_STRICT=1 thì vẫn chạy."""
    return unittest.skipUnless(STRICT, f"chờ {slice_name} (QA_STRICT=1 để chạy)")


def run_case(test: unittest.TestCase, mode: str, *, scenario: dict | None = None, inputs: list | None = None,
             ticks: int, seed: int = 1, every: int = 1, inventory: dict | None = None,
             inventory_out: bool = False) -> tuple[list, dict | None]:
    """Chạy headless một lần; trả (các dòng JSONL, kho ghi ra hoặc None). Mã thoát khác 0 -> test hỏng."""
    with Workdir() as w:
        args = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks),
                "--snapshot-every", str(every), "--out", w.path("o.jsonl")]
        if scenario is not None:
            args += ["--scenario", write_json(w.path("sc.json"), {mode: scenario})]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        if inventory is not None:
            args += ["--inventory", write_json(w.path("inv.json"), {"items": inventory})]
        if inventory_out:
            args += ["--inventory-out", w.path("kho.json")]
        code, err = run_headless(*args)
        test.assertEqual(code, 0, err)
        rows = read_jsonl(w.path("o.jsonl"))
        kho = None
        if inventory_out and os.path.exists(w.path("kho.json")):
            with open(w.path("kho.json"), encoding="utf-8") as f:
                kho = json.load(f)
        return rows, kho


def snap_at(rows: list, tick: int) -> dict:
    """Snapshot đúng tick (chạy với every=1 để có mọi tick)."""
    for s in snapshots(rows):
        if s["tick"] == tick:
            return s
    raise AssertionError(f"không có snapshot ở tick {tick}")


def press(tick: int, button: str) -> list:
    """Cạnh lên ở `tick`, nhả ở tick sau."""
    return [{"tick": tick, button: True}, {"tick": tick + 1, button: False}]
