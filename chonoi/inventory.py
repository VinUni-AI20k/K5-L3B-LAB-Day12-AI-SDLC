"""File kho. Schema chọn theo contract_version (ADR-0001, TICKET-03).

- Trước 1.2: {"items": {kind: số nguyên >= 0}}.
- Từ 1.2: {"items": [{id, kind, fresh}]}. Kho đếm → BadInput (mã 2).

Ghi qua file tạm cùng thư mục rồi os.replace. Độ tươi nội bộ dùng 240 đơn vị/điểm
(giỏ −2/tick, quán −1/tick) để ngưỡng 30 không lệch float.
"""

import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import sort_by_id

# v1.1 (TV1, T211): thêm cá kèo và kèo nèo.
KINDS_P1 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
FRESH_SCALE = 240  # đơn vị cho mỗi điểm tươi
_ITEM_KEYS = ("id", "kind", "fresh")


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


def version_tuple(version) -> tuple:
    try:
        return tuple(int(x) for x in str(version).split("."))
    except ValueError:
        return (1, 0)


def uses_individuals(version) -> bool:
    """Kho cá thể từ contract 1.2 trở đi (kể cả 1.3: gameplay vẫn theo v1.2)."""
    return version_tuple(version) >= (1, 2)


def fresh_to_units(fresh) -> int:
    return int(round(float(fresh) * FRESH_SCALE))


def units_to_fresh(units) -> float:
    return units / FRESH_SCALE


def decay_units_per_tick(decay_per_s, tick_hz=60) -> int:
    """Số đơn vị trừ mỗi tick. Phải chia hết (contract kiểm trước)."""
    units = float(decay_per_s) * FRESH_SCALE / float(tick_hz)
    rounded = round(units)
    if abs(units - rounded) > 1e-6:
        raise BadInput(f"hao tươi {decay_per_s}/s không ra số nguyên đơn vị/tick")
    return int(rounded)


def _finite_fresh(v):
    return not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v)


def validate_individuals(items, kinds=KINDS_P1) -> list:
    """Mảng cá thể. id duy nhất khác rỗng, kind thuộc danh mục, fresh hữu hạn trong [0, 100]."""
    if not isinstance(items, list):
        raise BadInput("contract từ v1.2 không nhận kho đếm; items phải là mảng cá thể")
    out = []
    seen = set()
    for i, item in enumerate(items):
        if not isinstance(item, dict) or set(item.keys()) != set(_ITEM_KEYS):
            raise BadInput(f"items[{i}] phải có đúng các khóa id, kind, fresh")
        ident = item.get("id")
        if not isinstance(ident, str) or not ident or ident in seen:
            raise BadInput(f"items[{i}].id phải là chuỗi khác rỗng và không trùng")
        seen.add(ident)
        if item.get("kind") not in kinds:
            raise BadInput(f"nguyên liệu lạ: {item.get('kind')!r}")
        fresh = item.get("fresh")
        if not _finite_fresh(fresh) or not (0 <= fresh <= 100):
            raise BadInput(f"items[{i}].fresh phải là số hữu hạn trong [0, 100], đang là {fresh!r}")
        out.append({"id": ident, "kind": item["kind"], "fresh": fresh})
    return sort_by_id(out)


def read_inventory(path: str, kinds=KINDS_P1, version="1.0"):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    items = data["items"]
    if uses_individuals(version):
        return validate_individuals(items, kinds)
    if isinstance(items, list):
        raise BadInput("contract trước v1.2 nhận kho đếm {kind: số}, không nhận mảng cá thể")
    return validate_items(items, kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items, version="1.0"):
    if uses_individuals(version):
        if not isinstance(items, list):
            raise BadInput("ghi kho v1.2 cần mảng cá thể")
        payload = validate_individuals(items)
    else:
        if not isinstance(items, dict):
            raise BadInput("ghi kho trước v1.2 cần object đếm")
        payload = {k: items[k] for k in sorted(items) if items[k] > 0}
    items = payload
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
