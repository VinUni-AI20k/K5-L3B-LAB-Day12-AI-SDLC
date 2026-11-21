"""Cá thể nguyên liệu có độ tươi (Contract v1.2, TICKET-03; ADR-0001). Dùng chung cho giỏ, kho quán, file kho, day.

Một cá thể là dict {"id": "I7", "kind": "ca_linh", "fresh": Fraction}. Độ tươi lưu bằng `Fraction` để so ngưỡng 30
và floor giá chính xác với mọi fixture (float JSON đổi sang phân số đúng giá trị); xuất ra JSON là float.
"""

import math
from fractions import Fraction

from .errors import BadInput
from .ids import id_key, sort_by_id

TICK = 60


def frac(v) -> Fraction:
    return v if isinstance(v, Fraction) else Fraction(v)


def per_tick(per_second) -> Fraction:
    """Hao mỗi tick từ số liệu /s trong contract (0.5/s -> 1/120; 0.25/s -> 1/240), chính xác theo thập phân."""
    return Fraction(str(per_second)) / TICK


def new_item(ids, kind, fresh) -> dict:
    return {"id": ids.new("I"), "kind": kind, "fresh": frac(fresh)}


def to_json(item) -> dict:
    return {"id": item["id"], "kind": item["kind"], "fresh": float(item["fresh"])}


def list_json(items) -> list:
    """Mảng cá thể ra JSON, sắp theo id (file kho, stock, gather_end.inventory)."""
    return [to_json(it) for it in sort_by_id(items)]


def order_json(items) -> list:
    """Giữ nguyên thứ tự (giỏ theo thứ tự vào, lost theo thứ tự bỏ LIFO)."""
    return [to_json(it) for it in items]


def is_spoiled(item, below) -> bool:
    return item["fresh"] < frac(below)


def decay(items, step: Fraction, below, location, events):
    """Hao tươi mọi cá thể (kẹp đáy 0); phát `spoiled` đúng một lần khi đi từ >= ngưỡng xuống < ngưỡng, theo id.
    Trả danh sách id vừa ươn."""
    below = frac(below)
    crossed = []
    for it in items:
        before = it["fresh"]
        it["fresh"] = max(Fraction(0), before - step)
        if before >= below > it["fresh"]:
            crossed.append(it)
    for it in sort_by_id(crossed):
        events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": location}))
    return [it["id"] for it in crossed]


def freshest(items, kind, n, exclude=(), below=30):
    """n cá thể chưa ươn của `kind`, tươi nhất rồi id nhỏ; None nếu không đủ."""
    cands = [it for it in items if it["kind"] == kind and it["id"] not in exclude and not is_spoiled(it, below)]
    cands.sort(key=lambda it: (-it["fresh"], id_key(it["id"])))
    return cands[:n] if len(cands) >= n else None


def priced(list_price, used) -> int:
    """base_price = floor(giá niêm yết × trung bình fresh của các cá thể dùng / 100)."""
    total = sum((it["fresh"] for it in used), Fraction(0))
    return math.floor(Fraction(list_price) * total / (len(used) * 100)) if used else int(list_price)


def parse_items(arr, kinds, where="items", ids=None) -> list:
    """Kiểm + dựng mảng cá thể từ JSON. Sai schema / kind lạ / id trùng / fresh ngoài [0,100] -> BadInput (mã 2)."""
    if not isinstance(arr, list):
        raise BadInput(f"{where} phải là mảng cá thể {{id, kind, fresh}} (Contract v1.2)")
    out, seen = [], set() if ids is None else ids
    for i, e in enumerate(arr):
        if not isinstance(e, dict) or set(e) != {"id", "kind", "fresh"}:
            raise BadInput(f"{where}[{i}] phải có đúng id, kind, fresh")
        if not isinstance(e["id"], str) or not e["id"]:
            raise BadInput(f"{where}[{i}].id phải là chuỗi khác rỗng")
        if e["id"] in seen:
            raise BadInput(f"{where}: id cá thể trùng {e['id']}")
        seen.add(e["id"])
        if e["kind"] not in kinds:
            raise BadInput(f"{where}[{i}]: nguyên liệu lạ {e['kind']!r}")
        f = e["fresh"]
        if isinstance(f, bool) or not isinstance(f, (int, float)) or not math.isfinite(f) or not 0 <= f <= 100:
            raise BadInput(f"{where}[{i}].fresh phải là số hữu hạn trong [0, 100]")
        out.append({"id": e["id"], "kind": e["kind"], "fresh": frac(f)})
    return out
