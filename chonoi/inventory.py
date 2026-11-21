"""File kho (Contract G). Bên đọc/ghi chọn schema theo `contract_version` (Ticket-03 mục 1):

- v1.0, v1.1 (kho đếm):   {"items": {kind: số nguyên >= 0}}
- v1.2 (kho cá thể):      {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}
  id chuỗi khác rỗng, duy nhất; kind thuộc danh mục; fresh hữu hạn trong [0, 100]. Kho rỗng {"items": []}.
  Chạy v1.2 mà gặp kho đếm hoặc sai schema -> mã 2.

Đọc: từ chối sai schema / kind lạ / số âm (BadInput -> mã 2).
Ghi: qua file tạm cùng thư mục rồi thay thế nguyên tử, byte-ổn-định. v1.1 bỏ mục bằng 0; v1.2 sắp theo id và ghi
fresh đủ chính xác (không làm tròn) để đọc lại vẫn đúng giá trị và nhánh ở ngưỡng 30.
"""

import json
import math
import os
import tempfile

from .errors import BadInput

# v1.1: 6 nguyên liệu (thêm cá kèo, kèo nèo). KINDS_P1 giữ làm tên cũ để code Phase 1 vẫn chạy.
KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS_P1 = KINDS
ITEM_KEYS = {"id", "kind", "fresh"}


def is_v12(version) -> bool:
    return version in ("1.2", "1.3")  # 1.3 giữ kho cá thể như 1.2 (Ticket-04)


def validate_items(items, kinds=KINDS):
    """Kho đếm (v1.1): object kind -> số nguyên >= 0. Trả dict đã bỏ mục bằng 0."""
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


def validate_instances(items, where="items", kinds=KINDS, seen=None):
    """Kho cá thể (v1.2): mảng {id, kind, fresh}. Trả nguyên mảng (dạng public). `seen` để kiểm id trùng giữa
    nhiều nơi chứa (ví dụ hold và stock trong scenario)."""
    if not isinstance(items, list):
        raise BadInput(f"{where} phải là mảng cá thể {{id, kind, fresh}} (v1.2)")
    seen = set() if seen is None else seen
    for i, it in enumerate(items):
        if not isinstance(it, dict) or set(it) != ITEM_KEYS:
            raise BadInput(f"{where}[{i}] phải có đúng các khóa id, kind, fresh")
        if not isinstance(it["id"], str) or not it["id"]:
            raise BadInput(f"{where}[{i}].id phải là chuỗi khác rỗng")
        if it["id"] in seen:
            raise BadInput(f"{where}: id cá thể trùng {it['id']}")
        seen.add(it["id"])
        if it["kind"] not in kinds:
            raise BadInput(f"{where}[{i}]: nguyên liệu lạ {it['kind']!r}")
        f = it["fresh"]
        if isinstance(f, bool) or not isinstance(f, (int, float)) or not math.isfinite(f) or not (0 <= f <= 100):
            raise BadInput(f"{where}[{i}].fresh phải là số hữu hạn trong [0, 100]")
    return items


def read_inventory(path: str, version=None, kinds=KINDS):
    """v1.1 trả dict đếm; v1.2 trả danh sách cá thể trong code ({id, kind, u}, xem chonoi.fresh).
    version None: lấy contract_version của game.contract.json."""
    if version is None:
        from .contract import load_contract
        version = load_contract()["contract_version"]
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if is_v12(version):
        from .fresh import from_public
        return [from_public(it) for it in validate_instances(data["items"], "items", kinds)]
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang -> object đếm, sắp theo id nguyên liệu. Nhận phần tử là chuỗi kind (v1.1) hoặc cá thể (dict có kind)."""
    counts = {}
    for k in hold:
        k = k["kind"] if isinstance(k, dict) else k
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def encode(items, version="1.1"):
    """Giá trị `items` theo schema của version. Nhận dict đếm, mảng cá thể trong code hoặc mảng public."""
    if is_v12(version):
        if isinstance(items, dict):
            raise BadInput("v1.2 cần kho cá thể, không ghi được kho đếm")
        from .fresh import public
        from .ids import sort_by_id
        out = [public(it) if "u" in it else dict(it) for it in items]
        return sort_by_id(out)
    if isinstance(items, list):
        items = hold_to_items(items)
    return {k: items[k] for k in sorted(items) if items[k] > 0}


def write_inventory(path: str, items, version="1.1"):
    data = encode(items, version)
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            # json.dump ghi float bằng repr (đủ chữ số để đọc lại ra đúng giá trị), không làm tròn như JSONL
            json.dump({"items": data}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
