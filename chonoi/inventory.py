"""Contract v1.2 inventory adapters: external fresh, internal integer fresh_u."""
import json
import math
import os
import tempfile

from .errors import BadInput
from .fresh import item_out, to_units
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS = KINDS_P1 + ("ca_keo", "keo_neo")


def validate_items(items, kinds=KINDS):
    """Validate external items, preserving basket insertion order and external schema."""
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể v1.2")
    seen, out = set(), []
    for it in items:
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput("cá thể cần đúng id, kind, fresh")
        ident, kind, fresh = it["id"], it["kind"], it["fresh"]
        if not isinstance(ident, str) or not ident or ident in seen:
            raise BadInput("id cá thể phải là chuỗi khác rỗng, không trùng")
        if not isinstance(kind, str) or kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind!r}")
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not 0 <= fresh <= 100 or not math.isfinite(fresh):
            raise BadInput("fresh phải hữu hạn trong [0,100]")
        seen.add(ident)
        out.append({"id": ident, "kind": kind, "fresh": float(fresh)})
    return out


def read_inventory(path: str, tuning=None) -> list:
    # tuning optional for the existing CLI callers; v1.2 is the only accepted schema.
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return sort_by_id([{"id": it["id"], "kind": it["kind"], "fresh_u": to_units(it["fresh"])}
                       for it in validate_items(data["items"])])


def hold_to_items(hold: list) -> list:
    """Internal basket to independent internal inventory, sorted by id."""
    return [dict(it) for it in sort_by_id(hold)]


def write_inventory(path: str, items: list):
    payload = [item_out(it) for it in sort_by_id(items)]
    validate_items(payload)
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
