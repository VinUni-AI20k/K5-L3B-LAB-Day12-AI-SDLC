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


def version_tuple():
    return tuple(int(x) for x in contract_version().split("."))


# Test Phase 2 chạy từ contract 1.1 trở lên; test Phase 3 chỉ chạy khi contract 1.2 (kho cá thể + độ tươi).
# Nhờ vậy nhánh chính không đỏ trong lúc các lát đang làm, và regression P1-P2 vẫn còn hiệu lực sau khi bật 1.2.
import unittest  # noqa: E402

FRESH = version_tuple() >= (1, 2)
requires_v11 = unittest.skipUnless(version_tuple() >= (1, 1), "chờ contract_version >= 1.1 (Phase 2)")
requires_v12 = unittest.skipUnless(FRESH, "chờ contract_version 1.2 (Phase 3)")


# ---- Fixture kho theo schema của contract hiện hành -------------------------------------------------
# <= 1.1: giỏ là mảng kind, kho là {kind: số lượng}, giữ chỗ là {kind: số lượng}.
# 1.2: giỏ và kho là mảng cá thể {id, kind, fresh}, giữ chỗ là mảng id (Phase3.md mục 1).
def item(i, kind, fresh=100):
    return {"id": f"I{i}", "kind": kind, "fresh": fresh}


def H(*kinds, fresh=100):
    """Fixture giỏ `gather.hold` theo thứ tự nhặt (mới nhất cuối)."""
    return [item(i, k, fresh) for i, k in enumerate(kinds, 1)] if FRESH else list(kinds)


class Kitchen:
    """Dựng `quan.stock` và `customers[].reserved` nhất quán: Kitchen({'ca_loc': 2}).stock / .reserve({'ca_loc': 1})."""

    def __init__(self, counts, fresh=100):
        self._free = {}
        self._items = []
        for kind, n in counts.items():
            for _ in range(n):
                it = item(len(self._items) + 1, kind, fresh)
                self._items.append(it)
                self._free.setdefault(kind, []).append(it["id"])
        self._counts = dict(counts)
        self.stock = self._items if FRESH else dict(counts)

    def reserve(self, counts):
        if not FRESH:
            return dict(counts)
        ids = []
        for kind, n in counts.items():
            for _ in range(n):
                ids.append(self._free[kind].pop(0))
        return ids


def kinds(xs):
    """Chuẩn hóa mảng giỏ / lost / items thành mảng kind (giữ thứ tự)."""
    return [x["kind"] if isinstance(x, dict) else x for x in xs]


def counts(x):
    """Chuẩn hóa kho (dict đếm, mảng cá thể hoặc object file kho {items: ...}) thành {kind: số lượng}."""
    if isinstance(x, dict) and "items" in x:
        x = x["items"]
    if isinstance(x, dict):
        return {k: v for k, v in x.items() if v}
    out = {}
    for it in x:
        out[it["kind"]] = out.get(it["kind"], 0) + 1
    return out


def res_counts(snapshot, customer):
    """Giữ chỗ của một khách thành {kind: số lượng}; v1.2 tra id trong kho của snapshot."""
    r = customer.get("reserved") or {}
    if isinstance(r, dict):
        return dict(r)
    by_id = {it["id"]: it["kind"] for it in snapshot.get("stock", [])}
    out = {}
    for iid in r:
        out[by_id[iid]] = out.get(by_id[iid], 0) + 1
    return out


def settled_price(price, decay_ticks):
    """Giá chốt khi nấu (Phase3.md mục 1): floor(giá × trung bình fresh / 100). Từ 1.2 kho quán hao 1 đơn vị/tick
    (240 đơn vị = 1 điểm), nên nấu sau `decay_ticks` bước thì mọi cá thể mới có fresh = (24000 - n)/240."""
    return price * (24000 - decay_ticks) // 24000 if FRESH else price


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
