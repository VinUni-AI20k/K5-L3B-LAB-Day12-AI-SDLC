"""TV3/TV1 helpers · kho cá thể {id,kind,fresh} và hao độ tươi (TICKET-03).

TV1 sở hữu adapter file; module này cung cấp thao tác dùng chung cho QuanSim/GatherSim
trong lúc chuyển schema. Ngưỡng spoiled so trước khi làm tròn hiển thị.
"""

import math

from .errors import BadInput
from .ids import id_key, sort_by_id
from .inventory import KINDS_P2, decay_items


def validate_unit(item, kinds=KINDS_P2):
    if not isinstance(item, dict):
        raise BadInput("cá thể kho phải là object")
    iid, kind, fresh = item.get("id"), item.get("kind"), item.get("fresh")
    if not isinstance(iid, str) or not iid:
        raise BadInput("cá thể cần id chuỗi khác rỗng")
    if kind not in kinds:
        raise BadInput(f"nguyên liệu lạ: {kind}")
    if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or math.isnan(fresh) or math.isinf(fresh):
        raise BadInput(f"fresh không hợp lệ: {fresh!r}")
    if not (0 <= float(fresh) <= 100):
        raise BadInput(f"fresh phải trong [0,100]: {fresh}")
    return {"id": iid, "kind": kind, "fresh": float(fresh)}


def validate_units(items, kinds=KINDS_P2):
    if not isinstance(items, list):
        raise BadInput("kho cá thể phải là mảng")
    out, seen = [], set()
    for raw in items:
        u = validate_unit(raw, kinds)
        if u["id"] in seen:
            raise BadInput(f"id cá thể trùng: {u['id']}")
        seen.add(u["id"])
        out.append(u)
    return out


def counts_to_units(counts: dict, ids, fresh=100.0) -> list:
    """Chuyển kho đếm (v1.0/v1.1) → cá thể tạm (fresh mặc định) để làm song song."""
    units = []
    for kind in sorted(counts):
        n = counts[kind]
        for _ in range(int(n)):
            units.append({"id": ids.new("I"), "kind": kind, "fresh": float(fresh)})
    return units


def is_spoiled(fresh, spoiled_below=30) -> bool:
    return float(fresh) < spoiled_below


def decay_units(units, decay_per_s, tick_hz, spoiled_below=30):
    """Hao tươi một bước; trả (units, list cá thể vừa qua ngưỡng spoilage)."""
    crossed = decay_items(units, decay_per_s, tick_hz=tick_hz, spoiled_below=spoiled_below)
    return units, crossed


def available_units(stock, reserved_ids, spoiled_below=30):
    """Cá thể chưa ươn và chưa bị giữ chỗ."""
    reserved = set(reserved_ids or [])
    return [
        u for u in stock
        if u["id"] not in reserved and not is_spoiled(u["fresh"], spoiled_below)
    ]


def pick_for_recipe(stock, recipe, reserved_ids=None, spoiled_below=30):
    """Chọn cá thể tươi nhất (hòa id) đủ công thức. Trả list id hoặc None nếu thiếu."""
    reserved = set(reserved_ids or [])
    pool = available_units(stock, reserved, spoiled_below)
    by_kind = {}
    for u in pool:
        by_kind.setdefault(u["kind"], []).append(u)
    for kind in by_kind:
        by_kind[kind].sort(key=lambda u: (-u["fresh"], id_key(u["id"])))
    chosen = []
    for kind, need in sorted(recipe.items()):
        cands = by_kind.get(kind, [])
        if len(cands) < need:
            return None
        chosen.extend(cands[:need])
    return [u["id"] for u in chosen]


def units_by_id(stock):
    return {u["id"]: u for u in stock}


def snapshot_units(stock):
    return sort_by_id([
        {"id": u["id"], "kind": u["kind"], "fresh": u["fresh"]} for u in stock
    ])
