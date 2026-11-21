"""File kho v1.0/v1.1 (kho đếm) & v1.2 (kho cá thể {id, kind, fresh}).

- v1.0/v1.1: {"items": {kind: số nguyên >= 0}}
- v1.2:      {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}
  (từ chối file kho đếm bằng mã 2 khi contract_version >= "1.2").
Ghi: qua file tạm cùng thư mục rồi thay thế nguyên tử, byte-ổn-định.
"""

import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_P2 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
ITEM_KEYS_V12 = {"id", "kind", "fresh"}


def is_v12_plus(contract_version: str) -> bool:
    try:
        parts = tuple(int(p) for p in str(contract_version).split("."))
        return parts >= (1, 2)
    except ValueError:
        return False


def validate_items(items, kinds=KINDS_P2):
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


def validate_item_instances(items, kinds=KINDS_P2) -> list:
    """Validate mảng cá thể v1.2: [{id, kind, fresh}]."""
    if not isinstance(items, list):
        raise BadInput("items ở Contract v1.2 phải là mảng cá thể [{id, kind, fresh}] (không nhận kho đếm)")
    seen = set()
    out = []
    for i, it in enumerate(items):
        if not isinstance(it, dict) or set(it.keys()) != ITEM_KEYS_V12:
            raise BadInput(f"items[{i}] phải có đúng các khóa {sorted(ITEM_KEYS_V12)}")
        iid = it["id"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"items[{i}].id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"items: id trùng {iid}")
        seen.add(iid)
        kind = it["kind"]
        if kind not in kinds:
            raise BadInput(f"items.{iid}: nguyên liệu lạ {kind!r}")
        fresh = it["fresh"]
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not math.isfinite(fresh) or not (0 <= fresh <= 100):
            raise BadInput(f"items.{iid}.fresh phải là số hữu hạn trong [0, 100]: {fresh!r}")
        out.append({"id": iid, "kind": kind, "fresh": fresh})
    return out


def read_inventory(path: str, kinds=KINDS_P2, contract_version: str = "1.1"):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if is_v12_plus(contract_version):
        return validate_item_instances(data["items"], kinds)
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang v1.0/v1.1 (mảng id kind theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def _atomic_write_json(path: str, payload: dict):
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


def write_inventory(path: str, items):
    """Ghi file kho nguyên tử: tự nhận diện dict (v1.0/v1.1) hoặc list cá thể (v1.2)."""
    if isinstance(items, list):
        write_inventory_v12(path, items)
        return
    clean = {k: items[k] for k in sorted(items) if items[k] > 0}
    _atomic_write_json(path, {"items": clean})


def write_inventory_v12(path: str, items: list):
    """Ghi file kho cá thể v1.2 sắp theo id, giữ đủ độ chính xác cho ngưỡng 30."""
    ordered = [
        {"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]}
        for it in sort_by_id(items)
    ]
    _atomic_write_json(path, {"items": ordered})
