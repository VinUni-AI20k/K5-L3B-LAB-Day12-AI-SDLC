"""File kho (Contract G). Bên đọc chọn schema theo contract_version (Ticket-03):
  v1.0/v1.1: kho ĐẾM {"items": {kind: số nguyên >= 0}};
  v1.2:      kho CÁ THỂ {"items": [{id, kind, fresh}, ...]}, kho rỗng {"items": []}; kho đếm cũ -> mã 2.

Đọc: từ chối sai schema / kind lạ / số âm / id trùng / fresh ngoài [0, 100] (BadInput -> mã 2).
Ghi: qua file tạm cùng thư mục rồi thay thế nguyên tử, byte-ổn-định.
"""

import json
import os
import tempfile

from .errors import BadInput

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
# v1.1 (Ticket-02): thêm cá kèo và kèo nèo. Schema file kho giữ nguyên như v1.0.
KINDS = KINDS_P1 + ("ca_keo", "keo_neo")


def validate_items(items, kinds=KINDS):
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


def read_inventory(path: str, kinds=KINDS, v12=False):
    """v12=False -> {kind: n}; v12=True -> mảng cá thể (chonoi.items)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if v12:
        from .items import from_file
        return from_file(data, kinds)
    if isinstance(data["items"], list):
        raise BadInput("contract trước v1.2 chỉ nhận kho đếm {kind: số}")
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items):
    """`items`: dict đếm (v1.1) hoặc mảng cá thể (v1.2)."""
    if isinstance(items, list):
        from .items import to_file
        items = to_file(items)["items"]
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
