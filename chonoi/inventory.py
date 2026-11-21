"""File kho (Contract G):
- v1.0 / v1.1: {"items": {kind: số lượng >= 0}}
- v1.2 (TICKET-03): {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100.0}, ...]}

Đọc: Bên đọc chọn schema theo contract_version. Contract v1.2 trả mã 2 cho file kho đếm hoặc sai schema,
     kind lạ, id trùng, fresh ngoài miền [0, 100].
Ghi: qua file tạm cùng thư mục rồi thay thế nguyên tử.
"""

import json
import os
import tempfile

from .errors import BadInput
from .ids import id_key

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_P2 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung", "ca_keo", "keo_neo")
KINDS = KINDS_P2


def validate_item_list(items, kinds=KINDS) -> list:
    """Kiểm tra và trả về mảng cá thể v1.2: [{id, kind, fresh}]."""
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể")
    seen_ids = set()
    out = []
    for it in items:
        if not isinstance(it, dict) or set(it.keys()) != {"id", "kind", "fresh"}:
            raise BadInput(f"cá thể kho phải có đúng khóa id, kind, fresh: {it!r}")
        item_id = it["id"]
        if not isinstance(item_id, str) or not item_id:
            raise BadInput(f"id cá thể không hợp lệ: {item_id!r}")
        if item_id in seen_ids:
            raise BadInput(f"trùng id cá thể trong kho: {item_id}")
        seen_ids.add(item_id)
        kind = it["kind"]
        if kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind}")
        fresh = it["fresh"]
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not (0 <= fresh <= 100):
            raise BadInput(f"độ tươi không hợp lệ cho {item_id}: {fresh!r}")
        out.append({"id": item_id, "kind": kind, "fresh": float(fresh)})
    return out


def validate_items(items, kinds=KINDS) -> dict:
    """Kiểm tra và trả về kho đếm v1.0/v1.1: {kind: số lượng}."""
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


def read_inventory(path: str, kinds=KINDS, contract_version=None):
    """Đọc file kho.

    Nếu contract_version >= '1.2': chỉ chấp nhận kho cá thể (mảng {id, kind, fresh}).
    File kho đếm (dict) sẽ trả BadInput (mã thoát 2).
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")

    raw_items = data["items"]
    # Kiểm tra contract_version nếu chưa truyền
    if contract_version is None:
        try:
            from .contract import load_contract
            contract_version = load_contract().get("contract_version", "1.0")
        except Exception:
            contract_version = "1.0"

    is_v12 = str(contract_version) >= "1.2"
    if isinstance(raw_items, list):
        return validate_item_list(raw_items, kinds)
    elif isinstance(raw_items, dict):
        if is_v12:
            raise BadInput("Contract v1.2 trả mã 2 cho file kho đếm (yêu cầu kho cá thể [THAY THẾ])")
        return validate_items(raw_items, kinds)
    else:
        raise BadInput("items trong file kho phải là mảng cá thể hoặc object đếm")


def hold_to_items(hold: list) -> list | dict:
    """Khoang -> mảng cá thể (nếu phần tử là cá thể) hoặc object đếm."""
    if not hold:
        return {}
    if isinstance(hold[0], dict):
        return sorted(hold, key=lambda x: id_key(x["id"]))
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            if isinstance(items, list):
                # Sắp xếp theo id cá thể, làm tròn 3 chữ số khớp JsonlWriter
                sorted_items = [
                    {"id": it["id"], "kind": it["kind"], "fresh": round(float(it["fresh"]), 3)}
                    for it in sorted(items, key=lambda x: id_key(x["id"]))
                ]
                json.dump({"items": sorted_items}, f, ensure_ascii=False, separators=(",", ":"))
            else:
                filtered = {k: items[k] for k in sorted(items) if items[k] > 0}
                json.dump({"items": filtered}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
