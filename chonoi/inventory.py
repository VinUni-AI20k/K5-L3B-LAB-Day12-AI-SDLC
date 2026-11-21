"""File kho v1.0 (Contract G): {"items": {id: số nguyên >= 0}}.

Đọc: từ chối sai schema / id lạ / số âm (BadInput -> mã 2).
Ghi: bỏ mục bằng 0, qua file tạm cùng thư mục rồi thay thế, byte-ổn-định.
"""

import json
import os
import tempfile

from .errors import BadInput

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_ALL = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")


def validate_items(items, kinds=KINDS_ALL):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def validate_inventory_v12(items, kinds=KINDS_ALL):
    if not isinstance(items, list):
        raise BadInput("items trong contract v1.2 phải là mảng cá thể")
    seen_ids = set()
    out = []
    for item in items:
        if not isinstance(item, dict):
            raise BadInput("mỗi cá thể trong kho phải là object")
        if set(item.keys()) != {"id", "kind", "fresh"}:
            raise BadInput("cá thể kho phải có đúng các khóa 'id', 'kind', 'fresh'")
        iid = item.get("id")
        if not isinstance(iid, str) or not iid:
            raise BadInput("id cá thể phải là chuỗi khác rỗng")
        if iid in seen_ids:
            raise BadInput(f"id trùng trong kho: {iid}")
        seen_ids.add(iid)
        kind = item.get("kind")
        if kind not in kinds:
            raise BadInput(f"nguyên liệu lạ trong kho: {kind}")
        fresh = item.get("fresh")
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not (0 <= fresh <= 100):
            raise BadInput(f"fresh ngoài miền [0, 100]: {fresh!r}")
        out.append({"id": iid, "kind": kind, "fresh": float(fresh)})
    return out


def read_inventory(path: str, kinds=KINDS_ALL, version="1.2") -> list | dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")

    if version == "1.2":
        if isinstance(data["items"], dict):
            raise BadInput("Contract v1.2 không nhận file kho đếm (phải là mảng cá thể)")
        return validate_inventory_v12(data["items"], kinds)
    else:
        if isinstance(data["items"], list):
            return validate_inventory_v12(data["items"], kinds)
        return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang -> object đếm (cho tương thích v1.0)."""
    counts = {}
    for k in hold:
        kind = k["kind"] if isinstance(k, dict) else k
        counts[kind] = counts.get(kind, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items):
    if isinstance(items, list):
        from .ids import sort_by_id
        sorted_items = sort_by_id(items)
        out_obj = {"items": [{"id": it["id"], "kind": it["kind"],
                              "fresh": round(it["fresh"], 3) if isinstance(it["fresh"], float) else it["fresh"]}
                             for it in sorted_items]}
    else:
        out_items = {k: items[k] for k in sorted(items) if items[k] > 0}
        out_obj = {"items": out_items}

    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out_obj, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
