"""File kho theo Test Contract, thay thế nguyên tử khi ghi thành công."""

import json
import os
import tempfile

from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_V11 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung", "ca_keo", "keo_neo")


def validate_items(items, kinds=KINDS_V11):
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


def validate_fresh_items(items, kinds=KINDS_V11, *, name="inventory.items"):
    """Kiểm kho cá thể, giữ ID, độ tươi và cả nguyên liệu đã ươn."""
    if not isinstance(items, list):
        raise BadInput(f"{name} phải là mảng cá thể")

    seen = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {"id", "kind", "fresh"}:
            raise BadInput(f"{name}: mỗi cá thể cần đúng id, kind và fresh")
        ident = item["id"]
        if not isinstance(ident, str) or not ident:
            raise BadInput(f"{name}: id phải là chuỗi khác rỗng")
        if ident in seen:
            raise BadInput(f"{name}: id trùng {ident}")
        seen.add(ident)
        if not isinstance(item["kind"], str) or item["kind"] not in kinds:
            raise BadInput(f"{name}.{ident}: nguyên liệu lạ {item['kind']!r}")
        fresh = item["fresh"]
        # So miền cũng loại NaN và vô cực mà không làm tròn.
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not 0 <= fresh <= 100:
            raise BadInput(f"{name}.{ident}.fresh phải trong [0, 100]")
    return items


def read_inventory(path: str, kinds=KINDS_V11, *, contract_version="1.1") -> list | dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if contract_version in ("1.2", "1.3"):
        return validate_fresh_items(data["items"], kinds)
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items: list | dict):
    if isinstance(items, list):
        items = sort_by_id(validate_fresh_items(items))
    else:
        items = {kind: items[kind] for kind in sorted(items) if items[kind] > 0}
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
