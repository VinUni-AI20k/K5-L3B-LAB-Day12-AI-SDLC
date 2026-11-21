"""Tiện ích riêng cho test hộp đen của QA (PRD-0). Chỉ đọc JSONL / file kho, không import chonoi.

`pending("lát 2")`: test của lát CHƯA merge -> mặc định SKIP để main luôn xanh.
Chạy thật mọi test pending: đặt biến môi trường QA_STRICT=1. Lát xong và test xanh thì QA bỏ decorator.
"""

import json
import os
import tempfile
import unittest

from helpers import ROOT, Workdir, frames, read_jsonl, run_headless, snapshots, write_json

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


FRESHNESS_V12 = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}


def use_v12_manifest():
    """Trỏ CHONOI_CONTRACT tới manifest v1.2 tạm khi `main` còn chạy v1.1 (Ticket-03: bật v1.2 khi cả hai đầu sẵn sàng).

    Trả hàm khôi phục (gọi trong tearDownModule). Manifest chính đã là v1.2 thì không làm gì. Cách của lát 0
    (tests/test_lat0_v12.py); khi `game.contract.json` lên v1.2 thì hàm này tự thành no-op.
    """
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    if manifest.get("tuning", {}).get("freshness") is not None:
        return lambda: None
    manifest["contract_version"] = "1.2"
    manifest["tuning"]["freshness"] = dict(FRESHNESS_V12)
    tmp = tempfile.TemporaryDirectory()
    old = os.environ.get("CHONOI_CONTRACT")
    os.environ["CHONOI_CONTRACT"] = write_json(os.path.join(tmp.name, "contract.json"), manifest)

    def restore():
        if old is None:
            os.environ.pop("CHONOI_CONTRACT", None)
        else:
            os.environ["CHONOI_CONTRACT"] = old
        tmp.cleanup()
    return restore


def manifest_is_v12() -> bool:
    """Manifest đang chạy (CHONOI_CONTRACT hoặc game.contract.json) có kho cá thể (khối freshness)?"""
    path = os.environ.get("CHONOI_CONTRACT") or os.path.join(ROOT, "game.contract.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("tuning", {}).get("freshness") is not None


def mk_hold(kinds: list, start: int = 1):
    """Fixture giỏ theo phiên bản đang chạy: v1.1 mảng kind; v1.2 mảng cá thể I<start>.. fresh 100."""
    if not manifest_is_v12():
        return list(kinds)
    return [{"id": f"I{start + n}", "kind": k, "fresh": 100} for n, k in enumerate(kinds)]


def mk_stock(counts: dict):
    """Fixture kho quán theo phiên bản: v1.1 map kind -> số; v1.2 mảng cá thể (id theo thứ tự kind), fresh 100."""
    if not manifest_is_v12():
        return dict(counts)
    items, n = [], 1
    for kind in sorted(counts):
        for _ in range(counts[kind]):
            items.append({"id": f"I{n}", "kind": kind, "fresh": 100})
            n += 1
    return items


def stock_counts(stock) -> dict:
    """Kho trong snapshot (map hoặc mảng cá thể) -> {kind: số lượng}, để assert độc lập phiên bản."""
    if isinstance(stock, dict):
        return dict(stock)
    out = {}
    for i in stock:
        out[i["kind"]] = out.get(i["kind"], 0) + 1
    return {k: out[k] for k in sorted(out)}
