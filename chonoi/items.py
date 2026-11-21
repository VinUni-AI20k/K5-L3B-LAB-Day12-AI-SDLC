"""Kho cá thể dùng chung (Test Contract v1.2, Ticket-03 "Mùa Nước Nổi"). Lát 0 (s0ra1n0) sở hữu.

Cá thể là dict {id, kind, fresh}; `fresh` là ĐIỂM TƯƠI (0..100) dạng số. Mọi phép hao / so ngưỡng / floor đi qua
đơn vị nguyên `UNITS` (240 đơn vị = 1 điểm, clarify #16): gather 0.5/s = 2 đơn vị/tick, quán 0.25/s = 1 đơn vị/tick,
ngưỡng ươn 30 = 7200 đơn vị. Nhờ vậy so ngưỡng "trước làm tròn" và floor giá luôn chính xác, không trôi số thực.

Lát 2, 3, 4, 5 chỉ gọi các hàm ở đây, không tự nhân/chia đơn vị.
"""

import math

from .errors import BadInput
from .ids import id_key

UNITS = 240  # đơn vị mỗi điểm tươi
ITEM_KEYS = {"id", "kind", "fresh"}


def units(fresh) -> int:
    """Điểm tươi -> đơn vị nguyên (fixture như 97.5, 30.5, 29.996 biểu diễn đúng ở 1/240)."""
    return int(round(fresh * UNITS))


def from_units(u: int) -> float:
    return u / UNITS


def new_item(ids, kind, fresh) -> dict:
    """Cá thể mới: id `I…` cấp tiếp theo (không tái dùng). Lúc hái/bắt dùng fresh = freshness.initial."""
    return {"id": ids.new("I"), "kind": kind, "fresh": float(fresh)}


def is_spoiled(item, tuning) -> bool:
    """Ươn khi fresh < spoiled_below, so trước làm tròn (trên đơn vị nguyên)."""
    return units(item["fresh"]) < units(tuning["freshness"]["spoiled_below"])


def decay(items, per_tick, tuning) -> list:
    """Trừ `per_tick` ĐIỂM mỗi cá thể (kẹp 0), sửa tại chỗ. Trả các cá thể VỪA chuyển sang ươn, sắp theo id.

    `per_tick` là điểm/tick (ví dụ quan_decay_per_s / 60); quy về đơn vị nguyên để không trôi số.
    """
    step = units(per_tick)
    newly = []
    for item in items:
        was = is_spoiled(item, tuning)
        item["fresh"] = from_units(max(0, units(item["fresh"]) - step))
        if not was and is_spoiled(item, tuning):
            newly.append(item)
    return sorted(newly, key=lambda i: id_key(i["id"]))


def usable_by_kind(items, exclude_ids, tuning) -> dict:
    """Đếm theo loại các cá thể dùng được: bỏ hàng ươn và id trong `exclude_ids` (đang giữ chỗ)."""
    out = {}
    for item in items:
        if item["id"] not in exclude_ids and not is_spoiled(item, tuning):
            out[item["kind"]] = out.get(item["kind"], 0) + 1
    return {k: out[k] for k in sorted(out)}


def pick_freshest(items, kind, n, exclude_ids, tuning):
    """`n` id cá thể loại `kind` tươi nhất, chưa ươn, chưa bị loại trừ; hòa thì id nhỏ (id_key). Thiếu -> None."""
    cand = sorted((i for i in items if i["kind"] == kind and i["id"] not in exclude_ids and not is_spoiled(i, tuning)),
                  key=lambda i: (-units(i["fresh"]), id_key(i["id"])))
    if len(cand) < n:
        return None
    return [i["id"] for i in cand[:n]]


def price_by_fresh(list_price: int, used_items) -> int:
    """base_price = floor(giá niêm yết × trung bình fresh các cá thể dùng / 100), tính nguyên trên đơn vị."""
    total = sum(units(i["fresh"]) for i in used_items)
    return (list_price * total) // (len(used_items) * UNITS * 100)


def counts(items) -> dict:
    """Mảng cá thể -> {kind: số lượng}, sắp theo kind (dùng cho HUD / kế hoạch Ngày)."""
    out = {}
    for i in items:
        out[i["kind"]] = out.get(i["kind"], 0) + 1
    return {k: out[k] for k in sorted(out)}


def validate_items(arr, kinds, where="items") -> list:
    """Kiểm mảng cá thể theo Ticket-03: dict đúng 3 khóa, id chuỗi khác rỗng không trùng, kind hợp lệ,
    fresh hữu hạn trong [0, 100]. Kho đếm kiểu cũ (object) -> mã 2. Trả bản sao (fresh là float)."""
    if isinstance(arr, dict):
        raise BadInput(f"{where}: contract v1.2 cần MẢNG cá thể {{id, kind, fresh}}, không nhận kho đếm cũ")
    if not isinstance(arr, list):
        raise BadInput(f"{where} phải là mảng cá thể")
    seen, out = set(), []
    for it in arr:
        if not isinstance(it, dict) or set(it) != ITEM_KEYS:
            raise BadInput(f"{where}: mỗi cá thể có đúng khóa id, kind, fresh")
        if not isinstance(it["id"], str) or not it["id"] or it["id"] in seen:
            raise BadInput(f"{where}: id cá thể phải là chuỗi khác rỗng, không trùng ({it.get('id')!r})")
        seen.add(it["id"])
        if it["kind"] not in kinds:
            raise BadInput(f"{where}: nguyên liệu lạ {it['kind']!r}")
        f = it["fresh"]
        if isinstance(f, bool) or not isinstance(f, (int, float)) or not math.isfinite(f) or not 0 <= f <= 100:
            raise BadInput(f"{where}.{it['id']}: fresh phải hữu hạn trong [0, 100]")
        out.append({"id": it["id"], "kind": it["kind"], "fresh": float(f)})
    return out


def to_file(items) -> dict:
    """Object file kho v1.2: {"items": [...]} theo thứ tự id. Kho rỗng {"items": []}.

    `fresh` làm tròn 3 chữ số như JSONL (`chonoi/jsonl.py`) để file KHỚP `gather_end.data.inventory` (PRD-0 mục G).
    Vẫn "đủ chính xác khi đọc lại" (Ticket-03): lưới 1/240 ≈ 0.00417, sai số làm tròn ≤ 0.0005 = 0.12 đơn vị,
    nên `units(fresh)` khôi phục đúng số nguyên và nhánh ở ngưỡng 30."""
    return {"items": [{"id": i["id"], "kind": i["kind"], "fresh": round(i["fresh"], 3)}
                      for i in sorted(items, key=lambda i: id_key(i["id"]))]}


def from_file(obj, kinds) -> list:
    if not isinstance(obj, dict) or set(obj) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_items(obj["items"], kinds, "file kho")


def is_v12(tuning) -> bool:
    """Kho cá thể bật khi tuning có khối freshness (contract v1.2)."""
    return isinstance(tuning, dict) and tuning.get("freshness") is not None
