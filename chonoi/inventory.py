"""File kho (Contract G):
- v1.0/v1.1: {"items": {kind: count}}
- v1.2: {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}

Đọc: từ chối sai schema / kind lạ / id trùng / fresh ngoài [0, 100] (BadInput -> mã 2).
Contract v1.2 từ chối kho đếm theo loại với mã thoát 2.
Ghi: qua file tạm cùng thư mục rồi thay thế nguyên tử, sắp xếp theo id.
"""

import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung", "ca_keo", "keo_neo")


def get_contract_version() -> str:
    try:
        from .contract import load_contract
        return str(load_contract().get("contract_version", "1.2"))
    except Exception:
        return "1.2"


def validate_items_v12(items, kinds=KINDS_P1):
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể trong Contract v1.2")
    seen_ids = set()
    out = []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            raise BadInput(f"item {i} không phải object")
        if set(it.keys()) != {"id", "kind", "fresh"}:
            raise BadInput(f"item {i} phải có đúng các khóa 'id', 'kind', 'fresh'")
        item_id = it["id"]
        if not isinstance(item_id, str) or not item_id:
            raise BadInput(f"item {i}: id phải là chuỗi khác rỗng")
        if item_id in seen_ids:
            raise BadInput(f"id trùng: {item_id}")
        seen_ids.add(item_id)
        kind = it["kind"]
        if kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind}")
        fresh = it["fresh"]
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not math.isfinite(fresh) or not (0 <= fresh <= 100):
            raise BadInput(f"fresh ngoài miền [0, 100]: {fresh}")
        out.append({"id": item_id, "kind": kind, "fresh": float(fresh)})
    return out


def validate_items_v10(items, kinds=KINDS_P1):
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


def validate_items(items, kinds=KINDS_P1):
    if isinstance(items, list):
        return validate_items_v12(items, kinds)
    elif isinstance(items, dict):
        return validate_items_v10(items, kinds)
    raise BadInput("items phải là mảng cá thể hoặc object đếm")


def read_inventory(path: str, kinds=KINDS_P1, contract_version=None):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")

    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")

    raw_items = data["items"]
    # Nếu contract_version được chỉ định >= 1.2 thì bắt buộc dùng mảng cá thể
    if contract_version is not None and contract_version >= "1.2":
        if isinstance(raw_items, dict):
            raise BadInput("Contract v1.2 không hỗ trợ kho đếm theo loại; phải dùng mảng cá thể {id, kind, fresh}")
        return validate_items_v12(raw_items, kinds)
    elif contract_version is not None and contract_version < "1.2":
        if isinstance(raw_items, list):
            return validate_items_v12(raw_items, kinds)
        return validate_items_v10(raw_items, kinds)
    else:
        # Tự động nhận diện khi gọi hàm trực tiếp không truyền contract_version
        if isinstance(raw_items, list):
            return validate_items_v12(raw_items, kinds)
        elif isinstance(raw_items, dict):
            return validate_items_v10(raw_items, kinds)
        raise BadInput("items phải là mảng cá thể hoặc object đếm")


def hold_to_items(hold: list):
    """Khoang -> mảng cá thể hoặc object đếm."""
    if not hold:
        return {}
    if isinstance(hold[0], dict):
        return list(hold)
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    c_ver = get_contract_version()
    try:
        if not items:
            data = {"items": [] if c_ver >= "1.2" else {}}
        elif isinstance(items, list):
            clean_items = []
            for it in items:
                f_val = float(it["fresh"])
                clean_items.append({
                    "id": str(it["id"]),
                    "kind": str(it["kind"]),
                    "fresh": f_val
                })
            data = {"items": sort_by_id(clean_items)}
        elif isinstance(items, dict):
            data = {"items": {k: items[k] for k in sorted(items) if items[k] > 0}}
        else:
            raise BadInput("items phải là mảng hoặc object")

        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
