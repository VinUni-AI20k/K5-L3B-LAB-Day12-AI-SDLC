"""Kho cá thể (Contract v1.2): {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}.

[THAY THẾ v1.2] Kho đếm theo loại (v1.0/v1.1) -> kho cá thể. File kho đếm hoặc sai schema -> mã 2.
Độ tươi lưu nội bộ bằng ĐƠN VỊ NGUYÊN: 240 đơn vị / 1 điểm tươi (gather -2/tick, quán -1/tick),
để so ngưỡng 30 và phép floor chính xác. Ra ngoài (file, JSONL) đổi về điểm: units / 240.

Cá thể nội bộ: {"id", "kind", "units"}. Cá thể ra ngoài: {"id", "kind", "fresh"}.
Ghi file: sắp theo id, qua file tạm cùng thư mục rồi thay thế nguyên tử; float ghi đủ chữ số để đọc lại y nguyên.
"""

import json
import math
import os
import tempfile
from fractions import Fraction

from .errors import BadInput
from .ids import id_key

FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS_P1 = KINDS  # tên cũ

UNITS = 240  # đơn vị nội bộ cho 1 điểm tươi
TICK = 60


def to_units(fresh) -> float:
    u = fresh * UNITS
    r = round(u)
    return r if abs(u - r) < 1e-6 else u


def units_per_tick(decay_per_s) -> float:
    return to_units(decay_per_s / TICK)


def fresh_of(it):
    return it["units"] / UNITS


def item_out(it) -> dict:
    return {"id": it["id"], "kind": it["kind"], "fresh": fresh_of(it)}


def by_id(items):
    return sorted(items, key=lambda it: id_key(it["id"]))


def new_item(ids, kind, fresh):
    return {"id": ids.new("I"), "kind": kind, "units": to_units(fresh)}


def is_spoiled(it, spoil_below) -> bool:
    return it["units"] < to_units(spoil_below)


def avg_fresh(items) -> Fraction:
    """Trung bình fresh (điểm) dạng phân số chính xác."""
    return sum(Fraction(it["units"]) for it in items) / (len(items) * UNITS)


def priced(price, items) -> int:
    """floor(giá niêm yết × trung bình fresh / 100)."""
    return math.floor(Fraction(price) * avg_fresh(items) / 100)


def decay(items, per_tick, spoil_below, location, events):
    """Hao tươi một bước, kẹp đáy 0. Phát spoiled (theo id) khi đi từ ≥ ngưỡng xuống < ngưỡng.
    Trả danh sách id vừa ươn."""
    limit = to_units(spoil_below)
    out = []
    for it in by_id(items):
        before = it["units"]
        it["units"] = max(0, before - per_tick)
        if before >= limit > it["units"]:
            out.append(it["id"])
            events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": location}))
    return out


def validate_item_list(arr, name="items", kinds=KINDS):
    """Mảng cá thể {id, kind, fresh} -> danh sách cá thể nội bộ (giữ thứ tự). Sai -> BadInput."""
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng cá thể {{id, kind, fresh}} (kho đếm không còn hợp lệ ở v1.2)")
    out, seen = [], set()
    for i, it in enumerate(arr):
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput(f"{name}[{i}] phải có đúng id, kind, fresh")
        iid, kind, fresh = it["id"], it["kind"], it["fresh"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"{name}[{i}].id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"{name}: id trùng {iid}")
        seen.add(iid)
        if kind not in kinds:
            raise BadInput(f"{name}[{i}]: nguyên liệu lạ {kind!r}")
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not math.isfinite(fresh) \
                or not 0 <= fresh <= 100:
            raise BadInput(f"{name}[{i}].fresh phải hữu hạn trong [0, 100]")
        out.append({"id": iid, "kind": kind, "units": to_units(fresh)})
    return out


def read_inventory(path: str, kinds=KINDS) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_item_list(data["items"], "items", kinds)


def write_inventory(path: str, items: list):
    """items: cá thể ra ngoài {id, kind, fresh}; ghi theo id."""
    items = sorted(items, key=lambda it: id_key(it["id"]))
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
