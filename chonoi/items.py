"""Cá thể nguyên liệu và độ tươi (Test Contract v1.2, TICKET-03 mục 1). Dùng chung cho gather, quán, day.

Biểu diễn trong sim: dict {"id": "I7", "kind": "ca_linh", "fresh_units": 24000}.
1 điểm tươi = UNITS (240) đơn vị → gather −2/tick (0.5/s), quán −1/tick (0.25/s), ươn khi < 30 × 240.
So ngưỡng và floor giá bằng đơn vị (số nguyên với mọi fixture biểu diễn chính xác) → không sai số ở 30.
Chỉ đổi ra `fresh` (điểm) khi xuất snapshot / event / file: dùng `public()` / `public_list()`.

Thứ tự trong danh sách = thứ tự vào giỏ (LIFO khi mất hàng: duyệt ngược).
"""

import math

from .errors import BadInput
from .ids import id_key

UNITS = 240  # đơn vị mỗi điểm tươi
KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")


def is_v12(tuning) -> bool:
    """Bật luật cá thể khi manifest có khối `freshness` (chỉ có từ contract v1.2)."""
    return isinstance(tuning, dict) and "freshness" in tuning


class Freshness:
    """Hằng số độ tươi đọc từ tuning.freshness, quy đổi sang đơn vị/tick."""

    def __init__(self, tuning):
        f = tuning["freshness"]
        hz = tuning.get("tick_hz", 60)
        self.initial = to_units(f["initial"])
        self.gather_per_tick = to_units(f["gather_decay_per_s"]) / hz  # 0.5/s -> 2 đơn vị/tick
        self.quan_per_tick = to_units(f["quan_decay_per_s"]) / hz      # 0.25/s -> 1 đơn vị/tick
        self.spoiled_below = to_units(f["spoiled_below"])               # 30 -> 7200


def to_units(fresh) -> float:
    u = fresh * UNITS
    r = round(u)
    return r if abs(u - r) < 1e-6 else u


def to_fresh(units):
    f = units / UNITS
    return int(f) if f == int(f) else f


class ItemIds:
    """Cấp I1, I2, … theo thứ tự vào giỏ; tăng xuyên pha và Ngày (giữ MỘT đối tượng cho cả lượt `day`)."""

    def __init__(self):
        self._next = 1

    def reserve(self, item_id: str):
        k = id_key(item_id)
        if k[0] == "I" and k[1] >= 0:
            self._next = max(self._next, k[1] + 1)

    def new(self) -> str:
        n = self._next
        self._next += 1
        return f"I{n}"


def new_item(ids: ItemIds, kind: str, fr: Freshness) -> dict:
    return {"id": ids.new(), "kind": kind, "fresh_units": fr.initial}


def from_public(obj) -> dict:
    return {"id": obj["id"], "kind": obj["kind"], "fresh_units": to_units(obj["fresh"])}


def public(item) -> dict:
    return {"id": item["id"], "kind": item["kind"], "fresh": to_fresh(item["fresh_units"])}


def public_list(items, by_id=False) -> list:
    src = sorted(items, key=lambda it: id_key(it["id"])) if by_id else items
    return [public(it) for it in src]


def is_spoiled(item, fr: Freshness) -> bool:
    return item["fresh_units"] < fr.spoiled_below


def decay(items, per_tick, fr: Freshness) -> list:
    """Hao `per_tick` đơn vị mỗi cá thể (kẹp 0). Trả các cá thể VỪA ươn (≥ ngưỡng → < ngưỡng), sắp theo id."""
    newly = []
    for it in items:
        before = it["fresh_units"]
        it["fresh_units"] = max(0, before - per_tick)
        if before >= fr.spoiled_below > it["fresh_units"]:
            newly.append(it)
    return sorted(newly, key=lambda it: id_key(it["id"]))


def pick_freshest(items, kind, n, fr: Freshness, exclude=()) -> list:
    """n cá thể `kind` chưa ươn, tươi nhất, hòa theo id; thiếu thì trả []."""
    cand = [it for it in items if it["kind"] == kind and it["id"] not in exclude and not is_spoiled(it, fr)]
    cand.sort(key=lambda it: (-it["fresh_units"], id_key(it["id"])))
    return cand[:n] if len(cand) >= n else []


def price_by_fresh(list_price: int, used) -> int:
    """floor(giá niêm yết × trung bình fresh / 100), tính bằng đơn vị: floor(giá × Σu / (n × 100 × UNITS))."""
    used = list(used)
    if not used:
        return list_price
    total = sum(it["fresh_units"] for it in used)
    if all(float(it["fresh_units"]).is_integer() for it in used):
        return (list_price * int(total)) // (len(used) * 100 * UNITS)
    return math.floor(list_price * total / (len(used) * 100 * UNITS))


def lifo(items) -> list:
    """Thứ tự bỏ khi mất hàng: vào sau mất trước."""
    return list(reversed(items))


def validate_public_items(arr, name="items", kinds=KINDS) -> list:
    """Kiểm mảng cá thể {id, kind, fresh}; trả danh sách nội bộ theo đúng thứ tự mảng."""
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng cá thể {{id, kind, fresh}}")
    seen, out = set(), []
    for i, it in enumerate(arr):
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput(f"{name}[{i}] phải có đúng khóa id, kind, fresh")
        if not isinstance(it["id"], str) or not it["id"]:
            raise BadInput(f"{name}[{i}].id phải là chuỗi khác rỗng")
        if it["id"] in seen:
            raise BadInput(f"{name}: id trùng {it['id']}")
        seen.add(it["id"])
        if it["kind"] not in kinds:
            raise BadInput(f"{name}[{i}].kind lạ: {it['kind']!r}")
        f = it["fresh"]
        if isinstance(f, bool) or not isinstance(f, (int, float)) or not math.isfinite(f) or not (0 <= f <= 100):
            raise BadInput(f"{name}[{i}].fresh phải hữu hạn trong [0, 100]")
        out.append(from_public(it))
    return out
