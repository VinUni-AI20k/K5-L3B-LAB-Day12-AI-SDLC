"""File kho v1.2 (TICKET-03): {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}]}.

Đọc: từ chối kho đếm kiểu v1.0/v1.1 (object/dict) và mọi schema/id/kind/fresh sai (BadInput -> mã 2).
Ghi: sắp theo id_key(id), giữ độ chính xác để không đổi nhánh tại ngưỡng fresh = 30, qua file tạm nguyên tử.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from decimal import Decimal, ROUND_HALF_UP

from .errors import BadInput
from .ids import id_key, sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_V11 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")

FRESH_SCALE = 240
SPOILED_THRESHOLD = 30


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def fresh_to_units(fresh: float | int, spoiled_below: float = SPOILED_THRESHOLD) -> int:
    """Quy đổi fresh ∈ [0, 100] sang đơn vị nguyên (240 / điểm), bảo toàn nhánh tại ngưỡng ươn."""
    d = Decimal(str(fresh))
    sp_d = Decimal(str(spoiled_below))
    sp_u = int((sp_d * FRESH_SCALE).to_integral_value(rounding=ROUND_HALF_UP))
    max_u = 100 * FRESH_SCALE
    u = int((d * FRESH_SCALE).to_integral_value(rounding=ROUND_HALF_UP))
    u = max(0, min(max_u, u))
    if d < sp_d and u >= sp_u:
        u = max(0, sp_u - 1)
    elif d >= sp_d and u < sp_u:
        u = sp_u
    return u


def units_to_fresh(units: int) -> int | float:
    """Chuyển đơn vị nguyên về số JSON giữ tròn nếu nguyên điểm, đủ 6 chữ số nếu lẻ."""
    u = max(0, min(100 * FRESH_SCALE, int(units)))
    if u % FRESH_SCALE == 0:
        return u // FRESH_SCALE
    return round(u / FRESH_SCALE, 6)


def serialize_item(it: dict) -> dict:
    """Chuyển cá thể nội bộ (hoặc dict đã chuẩn) thành {"id", "kind", "fresh"}."""
    if "fresh_u" in it:
        fresh = units_to_fresh(it["fresh_u"])
    else:
        f = it["fresh"]
        fresh = int(f) if isinstance(f, float) and f.is_integer() else f
    return {"id": it["id"], "kind": it["kind"], "fresh": fresh}


def validate_items(items, kinds=KINDS_V11, spoiled_below: float = SPOILED_THRESHOLD) -> list[dict]:
    """Kiểm mảng cá thể v1.2; từ chối dict đếm kiểu cũ bằng BadInput (mã 2)."""
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể [{id, kind, fresh}] (không chấp nhận kho đếm v1.0/v1.1)")
    seen = set()
    out = []
    for i, it in enumerate(items):
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput(f"items[{i}] phải có đúng khóa id, kind, fresh")
        iid = it["id"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"items[{i}].id phải là chuỗi không rỗng")
        if iid in seen:
            raise BadInput(f"trùng id nguyên liệu: {iid!r}")
        seen.add(iid)
        kind = it["kind"]
        if not isinstance(kind, str) or kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind!r}")
        fresh = it["fresh"]
        if not _num(fresh) or not (0 <= fresh <= 100):
            raise BadInput(f"items[{iid}].fresh phải hữu hạn trong [0, 100], đang là {fresh!r}")
        u = fresh_to_units(fresh, spoiled_below)
        out.append({"id": iid, "kind": kind, "fresh": units_to_fresh(u), "fresh_u": u})
    return out


def read_inventory(path: str, kinds=KINDS_V11, spoiled_below: float = SPOILED_THRESHOLD) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    parsed = validate_items(data["items"], kinds=kinds, spoiled_below=spoiled_below)
    return sort_by_id([serialize_item(it) for it in parsed])


def hold_to_items(hold: list) -> list[dict]:
    """Khoang cá thể -> danh sách chuẩn hóa sắp theo id_key."""
    return sort_by_id([serialize_item(it) for it in hold])


def write_inventory(path: str, items: list[dict]):
    payload = sort_by_id([serialize_item(it) for it in items])
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": payload}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
