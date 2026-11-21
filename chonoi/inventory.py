"""File kho (Contract G): chọn schema theo contract_version.

v1.0/v1.1 (kho đếm): {"items": {id: số nguyên >= 0}}.
v1.2 (kho cá thể, Ticket-03): {"items": [{"id", "kind", "fresh"}, ...]}; fresh đọc thành Fraction CHÍNH XÁC (không
qua float) trước khi kiểm, kho đếm / id trùng / loại lạ / fresh ngoài [0, 100] bị từ chối. Xem chonoi/freshness.py.

Đọc: từ chối sai schema (BadInput -> mã 2). Giao diện cũ giữ nguyên khi không truyền contract_version.
Ghi: qua file tạm cùng thư mục rồi thay thế nguyên tử, byte-ổn-định (v1.0 bỏ mục bằng 0; v1.2 sắp cá thể theo id).
"""

import json
import os
import tempfile
from fractions import Fraction

from .errors import BadInput
from .freshness import parse_items
from .ids import id_key

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_P2 = (*KINDS_P1, "ca_keo", "keo_neo")


def inventory_kinds(tuning):
    return KINDS_P2 if "shop" in tuning else KINDS_P1


def is_item_schema(contract_version) -> bool:
    """True khi contract_version >= 1.2: kho là mảng cá thể thay cho kho đếm."""
    return tuple(int(x) for x in str(contract_version).split(".")) >= (1, 2)


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


def read_inventory(path: str, kinds=KINDS_P1, *, contract_version="1.0"):
    """v1.0/v1.1 trả map đếm; v1.2 trả danh sách cá thể nội bộ (fresh là Fraction) theo thứ tự trong file."""
    items_schema = is_item_schema(contract_version)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f, parse_float=Fraction) if items_schema else json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if items_schema:
        if not isinstance(data["items"], list):
            raise BadInput("contract v1.2: items phải là mảng cá thể {id, kind, fresh}, kho đếm không còn hợp lệ")
        return parse_items(data["items"], kinds)
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items, *, contract_version="1.0"):
    """v1.0/v1.1: `items` là map đếm. v1.2: `items` là mảng cá thể ĐÃ chuyển sang số JSON (freshness.view_items)."""
    if is_item_schema(contract_version):
        payload = {"items": sorted(items, key=lambda it: id_key(it["id"]))}
    else:
        payload = {"items": {k: items[k] for k in sorted(items) if items[k] > 0}}
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
