"""File kho (Contract G). v1.0/v1.1: kho đếm {"items": {kind: số nguyên >= 0}}.
v1.2 (TICKET-03): kho cá thể {"items": [{"id", "kind", "fresh"}]}, sắp theo id; bên đọc chọn schema theo
contract_version (v12=True khi manifest có khối freshness) — v1.2 gặp kho đếm → mã 2.

Đọc: từ chối sai schema / id lạ / số âm (BadInput -> mã 2).
Ghi: bỏ mục bằng 0, qua file tạm cùng thư mục rồi thay thế, byte-ổn-định.
"""

import json
import os
import tempfile

from .errors import BadInput

# v1.1: thêm ca_keo, keo_neo (TICKET-02 mục 1.3). Giữ tên KINDS_P1 làm bí danh cho code cũ.
KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS_P1 = KINDS


def validate_items(items, kinds=KINDS_P1):
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


def read_inventory(path: str, kinds=KINDS_P1, v12=False):
    """v1.1 -> dict đếm; v1.2 -> danh sách cá thể nội bộ (xem chonoi.items)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if v12:
        from .items import validate_public_items
        if not isinstance(data["items"], list):
            raise BadInput("contract v1.2: file kho phải là mảng cá thể (kho đếm theo loại không còn hợp lệ)")
        return validate_public_items(data["items"], "items", kinds)
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items):
    """dict đếm (v1.1) hoặc danh sách cá thể nội bộ (v1.2, ghi sắp theo id, fresh đủ chính xác)."""
    if isinstance(items, list):
        from .items import public_list
        items = public_list(items, by_id=True)
    else:
        items = {k: items[k] for k in sorted(items) if items[k] > 0}
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
