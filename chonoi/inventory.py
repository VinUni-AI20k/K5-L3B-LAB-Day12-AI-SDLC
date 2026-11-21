"""File kho.

v1.0/v1.1 (kho đếm): {"items": {kind: số nguyên >= 0}}  — giữ để đọc file cũ khi contract < 1.2.
v1.2 (TICKET-03 §1, kho cá thể): {"items": [{"id","kind","fresh"}, ...]} sắp theo id.

Độ tươi trong bộ nhớ dùng ĐƠN VỊ NGUYÊN: 240 đơn vị = 1 điểm tươi (gather −2 đv/tick,
quán −1 đv/tick ở 60 Hz). Cá thể trong bộ nhớ là dict {"id","kind","units"}; ra JSON qua item_out().
Nếu fresh đọc vào không biểu diễn chính xác bằng số nguyên đơn vị, units là Fraction (vẫn chính xác).

Đọc: sai schema / kind lạ / id trùng / fresh ngoài [0,100] / không hữu hạn → BadInput (mã 2).
Ghi: file tạm cùng thư mục rồi os.replace (nguyên tử).
"""

import json
import math
import os
import tempfile
from fractions import Fraction

from .errors import BadInput
from .ids import sort_by_id

FISH_KINDS = ("ca_loc", "ca_linh", "ca_keo")
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS_P1 = KINDS

UNITS_PER_FRESH = 240
ITEM_KEYS = {"id", "kind", "fresh"}


# ---------- độ tươi: đơn vị nguyên <-> fresh ----------

def _norm(u):
    u = Fraction(u)
    return int(u) if u.denominator == 1 else u


def fresh_to_units(fresh):
    """fresh (số JSON) -> đơn vị chính xác (int, hoặc Fraction nếu không chia hết).
    Float cách số nguyên đơn vị < 1e-6 đơn vị được bắt về số nguyên đó, để file do units_to_fresh ghi
    đọc lại ĐÚNG số đơn vị (vd 23998/240 = 99.99166…)."""
    u = Fraction(fresh) * UNITS_PER_FRESH
    n = round(u)
    if abs(u - n) < Fraction(1, 10**6):
        return int(n)
    return _norm(u)


def units_to_fresh(units):
    """Đơn vị -> số JSON: int nếu tròn điểm, ngược lại float gần nhất (đọc lại giữ nhánh ở ngưỡng)."""
    v = Fraction(units) / UNITS_PER_FRESH
    return int(v) if v.denominator == 1 else float(v)


def freshness_cfg(tuning):
    """tuning.freshness với mặc định v1.2 nếu thiếu."""
    f = tuning.get("freshness") or {}
    return {"initial": f.get("initial", 100), "gather_decay_per_s": f.get("gather_decay_per_s", 0.5),
            "quan_decay_per_s": f.get("quan_decay_per_s", 0.25), "spoiled_below": f.get("spoiled_below", 30)}


def decay_units_per_tick(tuning, where):
    """where = 'gather' | 'quan' → đơn vị trừ mỗi tick (0.5/s → 2, 0.25/s → 1 ở 60 Hz)."""
    f = freshness_cfg(tuning)
    rate = f["gather_decay_per_s"] if where == "gather" else f["quan_decay_per_s"]
    return _norm(Fraction(str(rate)) * UNITS_PER_FRESH / int(tuning.get("tick_hz", 60)))


def spoil_threshold_units(tuning):
    return fresh_to_units(Fraction(str(freshness_cfg(tuning)["spoiled_below"])))


def initial_units(tuning):
    return fresh_to_units(Fraction(str(freshness_cfg(tuning)["initial"])))


# ---------- cá thể ----------

def make_item(ident, kind, units):
    return {"id": ident, "kind": kind, "units": units}


def new_item(ids, kind, tuning):
    """Cá thể mới hái/bắt: id I<n> từ IdAllocator dùng chung, fresh = initial."""
    return make_item(ids.new("I"), kind, initial_units(tuning))


def item_out(it):
    return {"id": it["id"], "kind": it["kind"], "fresh": units_to_fresh(it["units"])}


def items_out(items, sort=True):
    """Danh sách cá thể -> mảng JSON {id,kind,fresh}; mặc định sắp theo id (file kho, snapshot)."""
    seq = sort_by_id(items) if sort else list(items)
    return [item_out(it) for it in seq]


def is_spoiled(it, threshold_units):
    return it["units"] < threshold_units


def decay(items, units, threshold_units):
    """Trừ `units` đơn vị (kẹp 0) cho mọi cá thể; trả các cá thể vừa đi từ ≥ ngưỡng xuống < ngưỡng,
    sắp theo id (để phát spoiled đúng một lần, theo id). So trước mọi làm tròn."""
    crossed = []
    for it in items:
        before = it["units"]
        after = before - units
        it["units"] = after if after > 0 else 0
        if before >= threshold_units and it["units"] < threshold_units:
            crossed.append(it)
    return sort_by_id(crossed)


def parse_items(raw, kinds=KINDS, where="items"):
    """Mảng JSON cá thể -> list dict {id,kind,units} (giữ thứ tự mảng). Sai → BadInput."""
    if not isinstance(raw, list):
        raise BadInput(f"{where} phải là mảng cá thể {{id,kind,fresh}}")
    out, seen = [], set()
    for e in raw:
        if not isinstance(e, dict) or set(e.keys()) != ITEM_KEYS:
            raise BadInput(f"{where}: mỗi cá thể phải có đúng khóa id, kind, fresh")
        ident, kind, fresh = e["id"], e["kind"], e["fresh"]
        if not isinstance(ident, str) or not ident:
            raise BadInput(f"{where}: id phải là chuỗi khác rỗng")
        if ident in seen:
            raise BadInput(f"{where}: id trùng {ident}")
        seen.add(ident)
        if kind not in kinds:
            raise BadInput(f"{where}: nguyên liệu lạ {kind!r}")
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not math.isfinite(fresh) \
                or not (0 <= fresh <= 100):
            raise BadInput(f"{where}: fresh của {ident} phải hữu hạn trong [0, 100]")
        out.append(make_item(ident, kind, fresh_to_units(fresh)))
    return out


# ---------- v1.0/v1.1: kho đếm (giữ cho file cũ) ----------

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


def hold_to_items(hold: list) -> dict:
    """Kho đếm từ danh sách kind (v1.1) hoặc cá thể (v1.2): object đếm sắp theo kind."""
    counts = {}
    for k in hold:
        k = k["kind"] if isinstance(k, dict) else k
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


# ---------- đọc / ghi file ----------

def _is_v12(version):
    try:
        return tuple(int(x) for x in str(version).split(".")[:2]) >= (1, 2)
    except ValueError:
        raise BadInput(f"contract_version lạ: {version!r}")


def read_inventory(path: str, version="1.2", kinds=KINDS):
    """v1.2 → list cá thể {id,kind,units} (thứ tự file); < 1.2 → dict đếm. Sai → BadInput (mã 2).
    v1.2 từ chối file kho đếm (items là object)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f, parse_constant=lambda c: float(c))
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if _is_v12(version):
        if isinstance(data["items"], dict):
            raise BadInput("contract v1.2: file kho đếm theo loại không còn hợp lệ (cần mảng cá thể)")
        return parse_items(data["items"], kinds, "file kho")
    return validate_items(data["items"], kinds)


def _atomic_dump(path, obj):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write_inventory_atomic(path: str, items):
    """v1.2: ghi {"items":[{id,kind,fresh}]} sắp theo id, nguyên tử. `items` là list cá thể bộ nhớ."""
    _atomic_dump(path, {"items": items_out(items)})


def write_inventory(path: str, items):
    """Tương thích: list cá thể → schema v1.2; dict đếm → schema v1.1."""
    if isinstance(items, list):
        return write_inventory_atomic(path, items)
    items = {k: items[k] for k in sorted(items) if items[k] > 0}
    _atomic_dump(path, {"items": items})
