"""File kho v1.2 (TICKET-03): {"items": [{"id", "kind", "fresh"}, ...]} — kho cá thể có độ tươi (ADR-0001).

Đọc: kho đếm v1.0/v1.1 ({"items": {kind: n}}), sai schema, kind lạ, id trùng, fresh ngoài [0,100] -> BadInput (mã 2).
Ghi: sắp theo id, fresh float đầy đủ (không làm tròn) để đọc lại giữ giá trị và nhánh ở ngưỡng 30;
qua file tạm cùng thư mục rồi thay thế nguyên tử; byte-ổn-định.
"""

import json
import os
import tempfile

from .errors import BadInput
from .items import list_json, parse_items

KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS_P1 = KINDS  # tên cũ


def read_inventory(path: str, kinds=KINDS) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if isinstance(data["items"], dict):
        raise BadInput("file kho đếm theo loại (v1.0/v1.1) không hợp lệ ở Contract v1.2: cần mảng cá thể")
    return parse_items(data["items"], kinds, "file kho items")


def write_inventory(path: str, items: list):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": list_json(items)}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
