"""File kho v1.2 (TICKET-03): {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}]}.

Đọc: từ chối kho đếm hoặc sai schema / kind lạ / id trùng / fresh ngoài [0, 100] (BadInput -> mã 2).
Ghi: sắp theo id, qua file tạm cùng thư mục rồi thay thế nguyên tử, đủ độ chính xác ở ngưỡng 30.
"""

from fractions import Fraction
import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import sort_by_id

KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS_P1 = KINDS
UNITS_PER_FRESH = 240


def to_fraction(val) -> Fraction:
    if isinstance(val, Fraction):
        return val
    if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
        raise BadInput(f"độ tươi không hợp lệ: {val!r}")
    if isinstance(val, int):
        return Fraction(val, 1)
    u = round(val * UNITS_PER_FRESH)
    if abs(val * UNITS_PER_FRESH - u) <= 0.15:
        return Fraction(int(u), UNITS_PER_FRESH)
    return Fraction(str(val))


def fresh_to_num(val):
    frac = to_fraction(val) if not isinstance(val, Fraction) else val
    if frac.denominator == 1:
        return int(frac.numerator)
    r = round(float(frac), 3)
    return int(r) if r == int(r) else r


def format_item(item: dict) -> dict:
    return {
        "id": item["id"],
        "kind": item["kind"],
        "fresh": fresh_to_num(item["fresh"]),
    }


def validate_items(items, kinds=KINDS) -> list:
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể {id, kind, fresh}")
    out = []
    seen = set()
    for it in items:
        if not isinstance(it, dict) or set(it.keys()) != {"id", "kind", "fresh"}:
            raise BadInput("mỗi cá thể phải là object có đúng khóa id, kind, fresh")
        iid = it["id"]
        if not isinstance(iid, str) or not iid:
            raise BadInput("id cá thể phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"id cá thể trùng: {iid}")
        seen.add(iid)
        kind = it["kind"]
        if kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind}")
        fr = it["fresh"]
        if isinstance(fr, bool) or not isinstance(fr, (int, float)) or not math.isfinite(fr) or not (0 <= fr <= 100):
            raise BadInput(f"fresh ngoài miền [0, 100] cho {iid}: {fr!r}")
        out.append({"id": iid, "kind": kind, "fresh": fresh_to_num(to_fraction(fr))})
    return out


def read_inventory(path: str, kinds=KINDS_P1) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> list:
    """Giỏ (mảng cá thể theo thứ tự nhặt) -> mảng cá thể sắp theo id."""
    return [format_item(it) for it in sort_by_id(hold)]


def write_inventory(path: str, items: list):
    out = [format_item(it) for it in sort_by_id(items)]
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": out}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
