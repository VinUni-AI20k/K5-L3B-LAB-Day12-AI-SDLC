"""File kho.

v1.0/v1.1 (kho đếm): {"items": {kind: số nguyên >= 0}}.
v1.2 (kho cá thể): {"items": [{"id","kind","fresh"}]} — sai schema / kind lạ / id trùng / fresh ngoài
[0,100] / file kho đếm → BadInput (mã 2). Ghi qua file tạm cùng thư mục rồi thay thế, sắp theo id.

Độ tươi trong sim giữ dạng Fraction để so ngưỡng 30 và floor giá chính xác; ra JSON là float.
"""

import json
import math
import os
import tempfile
from fractions import Fraction

from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_ALL = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")


def validate_items(items, kinds=KINDS_ALL):
    """Kho đếm v1.0/v1.1."""
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


def parse_fresh(v):
    """Số JSON -> Fraction đúng giá trị thập phân đã viết (30.1 là 301/10, không phải float gần đúng)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise BadInput(f"fresh phải là số hữu hạn: {v!r}")
    f = Fraction(repr(v)) if isinstance(v, float) else Fraction(v)
    if not (0 <= f <= 100):
        raise BadInput(f"fresh phải trong [0, 100]: {v!r}")
    return f


def validate_item_list(items, kinds=KINDS_ALL, seen=None):
    """Kho cá thể v1.2 -> danh sách {id, kind, fresh: Fraction}, giữ thứ tự mảng.
    `seen` (set) dùng chung để bắt id trùng giữa nhiều nơi chứa."""
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể {id, kind, fresh} (contract v1.2)")
    seen = set() if seen is None else seen
    out = []
    for it in items:
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput(f"cá thể phải có đúng khóa id, kind, fresh: {it!r}")
        iid = it["id"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"id cá thể phải là chuỗi khác rỗng: {iid!r}")
        if iid in seen:
            raise BadInput(f"id cá thể trùng: {iid}")
        seen.add(iid)
        if it["kind"] not in kinds:
            raise BadInput(f"nguyên liệu lạ: {it['kind']}")
        out.append({"id": iid, "kind": it["kind"], "fresh": parse_fresh(it["fresh"])})
    return out


def item_out(it) -> dict:
    """Cá thể nội bộ -> JSON (float đủ chính xác: repr của float đọc lại ra đúng float đó)."""
    return {"id": it["id"], "kind": it["kind"], "fresh": float(it["fresh"])}


def items_out(items) -> list:
    """Danh sách công khai sắp theo id (file kho, gather_end.inventory, snapshot kho)."""
    return [item_out(it) for it in sort_by_id(items)]


def read_inventory(path: str, kinds=KINDS_ALL) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_item_list(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Danh sách cá thể -> object đếm theo kind (cầu nối cho quán còn dùng kho đếm)."""
    counts = {}
    for it in hold:
        k = it["kind"] if isinstance(it, dict) else it
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items: list):
    """Ghi kho cá thể v1.2 nguyên tử: file tạm cùng thư mục rồi os.replace."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": items_out(items)}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
