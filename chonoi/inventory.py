"""File kho v1.0–v1.2 (Contract G & Phase 3 Mùa Nước Nổi).

v1.0/v1.1: {"items": {kind: số nguyên >= 0}}.
v1.2:      {"items": [{"id": str, "kind": str, "fresh": float|int}, ...]}.

Đọc: từ chối sai schema / id lạ hoặc trùng / fresh NaN, vô hạn hoặc ngoài [0, 100] (BadInput -> mã 2).
Ghi: qua file tạm cùng thư mục rồi thay thế nguyên tử, byte-ổn-định; v1.2 xuất sắp theo id_key.
"""

from fractions import Fraction
import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import id_key

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_P2 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")

FRESH_UNITS_PER_POINT = 240
DEFAULT_FRESHNESS = {
    "initial": 100,
    "gather_decay_per_s": 0.5,
    "quan_decay_per_s": 0.25,
    "spoiled_below": 30,
}


def is_v12(contract_version: str) -> bool:
    """Trả True nếu contract_version >= 1.2 (ví dụ '1.2')."""
    if not isinstance(contract_version, str):
        raise BadInput(f"contract_version không hợp lệ: {contract_version!r}")
    parts = contract_version.strip().split(".")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        raise BadInput(f"contract_version không hợp lệ: {contract_version!r}")
    return (int(parts[0]), int(parts[1])) >= (1, 2)


def _reject_json_constant(token: str):
    raise ValueError(f"hằng số JSON không hợp lệ: {token}")


def parse_fresh(value, name: str = "fresh") -> Fraction:
    """Chuyển fresh về Fraction chính xác trong [0, 100]; từ chối bool/NaN/Inf/ngoài miền."""
    if isinstance(value, Fraction):
        q = value
    elif isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BadInput(f"{name} phải là số hữu hạn trong [0, 100], đang là {value!r}")
    elif isinstance(value, int):
        q = Fraction(value, 1)
    else:
        if not math.isfinite(value):
            raise BadInput(f"{name} phải hữu hạn, đang là {value!r}")
        if not (0.0 <= value <= 100.0):
            raise BadInput(f"{name} ngoài miền [0, 100], đang là {value!r}")
        scaled = value * FRESH_UNITS_PER_POINT
        nearest = round(scaled)
        if abs(scaled - nearest) <= 1e-11:
            q = Fraction(nearest, FRESH_UNITS_PER_POINT)
        else:
            q = Fraction(str(value))
    if not (0 <= q <= 100):
        raise BadInput(f"{name} ngoài miền [0, 100], đang là {value!r}")
    return q


def fresh_to_json(q) -> int | float:
    """Chuyển giá trị độ tươi về int (nếu nguyên) hoặc float để tuần tự hóa JSON."""
    frac = q if isinstance(q, Fraction) else parse_fresh(q)
    return int(frac.numerator) if frac.denominator == 1 else float(frac)


def is_spoiled(fresh, spoiled_below=30) -> bool:
    """Kiểm tra cá thể đã ươn chưa (so trước làm tròn: fresh < spoiled_below)."""
    return parse_fresh(fresh) < Fraction(str(spoiled_below))


def decay_rate_per_tick(decay_per_s, tick_hz: int = 60) -> Fraction:
    """Lượng hao độ tươi mỗi tick dạng phân số chính xác."""
    return Fraction(str(decay_per_s)) / Fraction(tick_hz)


def validate_items(items, kinds=KINDS_P2):
    """Kiểm kho đếm v1.0/v1.1: {kind: số nguyên >= 0}."""
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


def validate_item_record(rec, *, kinds=KINDS_P2, seen_ids=None, name: str = "item") -> dict:
    """Kiểm một cá thể v1.2 {id, kind, fresh} và chuẩn hóa fresh."""
    if not isinstance(rec, dict) or set(rec.keys()) != {"id", "kind", "fresh"}:
        raise BadInput(f"{name} phải là object có đúng khóa id, kind, fresh")
    ident = rec["id"]
    if not isinstance(ident, str) or not ident:
        raise BadInput(f"{name}.id phải là chuỗi khác rỗng, đang là {ident!r}")
    if seen_ids is not None:
        if ident in seen_ids:
            raise BadInput(f"{name}: trùng id {ident!r}")
        seen_ids.add(ident)
    kind = rec["kind"]
    if kind not in kinds:
        raise BadInput(f"{name}.kind nguyên liệu lạ: {kind!r}")
    q = parse_fresh(rec["fresh"], name=f"{name}.fresh")
    return {"id": ident, "kind": kind, "fresh": fresh_to_json(q)}


def validate_item_list(items, *, kinds=KINDS_P2, seen_ids=None, name: str = "items") -> list[dict]:
    """Kiểm danh sách cá thể v1.2, bảo toàn thứ tự danh sách gốc."""
    if not isinstance(items, list):
        raise BadInput(f"{name} phải là mảng cá thể v1.2")
    tracker = set() if seen_ids is None else seen_ids
    return [
        validate_item_record(rec, kinds=kinds, seen_ids=tracker, name=f"{name}[{i}]")
        for i, rec in enumerate(items)
    ]


def make_item(ids, kind: str, fresh=100, *, kinds=KINDS_P2, prefix: str = "I") -> dict:
    """Cấp phát một cá thể nguyên liệu mới từ IdAllocator."""
    if kind not in kinds:
        raise BadInput(f"nguyên liệu lạ: {kind!r}")
    q = parse_fresh(fresh)
    return {"id": ids.new(prefix), "kind": kind, "fresh": fresh_to_json(q)}


def decay_items(items: list[dict], decay_per_s, *, tick_hz: int = 60, spoiled_below=30) -> list[dict]:
    """Giảm độ tươi từng cá thể tại chỗ; trả các cá thể vừa qua ngưỡng ươn (sắp theo id_key)."""
    step = decay_rate_per_tick(decay_per_s, tick_hz)
    threshold = Fraction(str(spoiled_below))
    newly_spoiled = []
    for item in items:
        before = parse_fresh(item["fresh"])
        after = max(Fraction(0), before - step)
        item["fresh"] = fresh_to_json(after)
        if before >= threshold and after < threshold:
            newly_spoiled.append(dict(item))
    newly_spoiled.sort(key=lambda x: id_key(x["id"]))
    return newly_spoiled


def export_items(items: list[dict], *, kinds=KINDS_P2) -> list[dict]:
    """Chuẩn hóa và xuất mảng cá thể sắp theo id_key (không làm thay đổi thứ tự danh sách vào)."""
    validated = validate_item_list(items, kinds=kinds)
    validated.sort(key=lambda x: id_key(x["id"]))
    return validated


def count_by_kind(items: list[dict]) -> dict[str, int]:
    """Đếm số lượng cá thể theo từng loại nguyên liệu."""
    counts = {}
    for item in items:
        k = item["kind"]
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def select_freshest(
    items: list[dict],
    kind: str,
    count: int,
    *,
    exclude_ids=None,
    spoiled_below=30,
) -> list[dict] | None:
    """Chọn `count` cá thể chưa ươn tươi nhất thuộc `kind` (hòa theo id_key); thiếu trả None."""
    if count == 0:
        return []
    excluded = set() if exclude_ids is None else set(exclude_ids)
    candidates = [
        item for item in items
        if item["kind"] == kind
        and item["id"] not in excluded
        and not is_spoiled(item["fresh"], spoiled_below)
    ]
    if len(candidates) < count:
        return None
    candidates.sort(key=lambda x: (-parse_fresh(x["fresh"]), id_key(x["id"])))
    return [dict(x) for x in candidates[:count]]


def price_for_items(listed_price: int, items: list[dict]) -> int:
    """Tính giá bán floor(giá niêm yết * trung bình fresh / 100)."""
    if not items:
        raise BadInput("cần ít nhất một cá thể để tính giá món")
    avg = sum(parse_fresh(x["fresh"]) for x in items) / Fraction(len(items))
    return math.floor(Fraction(listed_price) * avg / Fraction(100))


def tip_for_price(base_price: int, tip_rate=0.2) -> int:
    """Tính tiền boa floor(base_price * tip_rate) trên giá đã chốt."""
    return math.floor(Fraction(base_price) * Fraction(str(tip_rate)))


def sort_cook_items(items: list[dict]) -> list[dict]:
    """Sắp bản sao danh sách cá thể đưa vào cook_started.data.items theo (kind, id_key)."""
    return [dict(x) for x in sorted(items, key=lambda x: (x["kind"], id_key(x["id"])))]


def read_inventory(path: str, kinds=KINDS_P2, *, contract_version: str = "1.1"):
    """Đọc file kho theo contract_version: v1.0/v1.1 trả dict đếm, v1.2 trả list cá thể."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f, parse_constant=_reject_json_constant)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if is_v12(contract_version):
        return validate_item_list(data["items"], kinds=kinds)
    return validate_items(data["items"], kinds)


def read_inventory_v12(path: str, kinds=KINDS_P2) -> list[dict]:
    """Đọc file kho ép buộc schema v1.2."""
    return read_inventory(path, kinds=kinds, contract_version="1.2")


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items, *, kinds=KINDS_P2):
    """Ghi file kho nguyên tử (hỗ trợ cả dict v1.1 lẫn list cá thể v1.2)."""
    if isinstance(items, list):
        payload = export_items(items, kinds=kinds)
    elif isinstance(items, dict):
        payload = {k: items[k] for k in sorted(items) if items[k] > 0}
    else:
        raise BadInput("dữ liệu kho ghi ra phải là dict hoặc list")
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": payload}, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write_inventory_v12(path: str, items: list[dict], kinds=KINDS_P2):
    """Ghi file kho ép buộc schema v1.2 (list cá thể)."""
    if not isinstance(items, list):
        raise BadInput("kho v1.2 phải là mảng cá thể")
    write_inventory(path, items, kinds=kinds)
