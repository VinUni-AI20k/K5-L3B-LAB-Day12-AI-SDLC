"""Độ tươi cá thể (Ticket-03, Test Contract v1.2), dùng chung cho Gather, Quán, Day và file kho.

Cá thể nội bộ: {"id": "I<n>", "kind": <id nguyên liệu>, "fresh": Fraction}. Độ tươi là phân số CHÍNH XÁC (ADR 0001)
để phép trừ mỗi tick, so ngưỡng ươn và floor giá không lệch do số thực. Chỉ chuyển sang số JSON khi xuất, bằng
`view_items`, và giữ đúng phía ngưỡng ươn. Giao diện theo docs/contracts/phase-3.md.
"""

import math
from fractions import Fraction
from functools import lru_cache

from .errors import BadInput
from .ids import id_key

FRESH_MIN, FRESH_MAX = 0, 100  # miền hợp lệ của `fresh` trong schema kho v1.2 (schema, không phải tuning)
ITEM_KEYS = frozenset(("id", "kind", "fresh"))
ITEM_ID_PREFIX = "I"
_ZERO = Fraction(0)


def to_fraction(value, name="giá trị") -> Fraction:
    """Số JSON -> Fraction chính xác. float đi qua chuỗi thập phân ngắn nhất (repr) để 29.99 thành 2999/100."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise BadInput(f"{name} phải là số, đang là {value!r}")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise BadInput(f"{name} phải hữu hạn, đang là {value!r}")
        return Fraction(repr(value))
    return Fraction(value)


def parse_items(raw, kinds) -> list:
    """Kiểm mảng cá thể {id, kind, fresh}; trả danh sách bản ghi MỚI theo thứ tự vào, fresh là Fraction.

    id chuỗi khác rỗng, duy nhất; kind thuộc `kinds`; fresh hữu hạn trong [0, 100]. Nhận cả hàng đã ươn.
    """
    if not isinstance(raw, list):
        raise BadInput("items phải là mảng cá thể {id, kind, fresh}")
    out, seen = [], set()
    for i, item in enumerate(raw):
        if not isinstance(item, dict) or set(item) != ITEM_KEYS:
            raise BadInput(f"items[{i}] phải có đúng các khóa id, kind, fresh")
        iid, kind = item["id"], item["kind"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"items[{i}].id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"id cá thể trùng: {iid}")
        seen.add(iid)
        if not isinstance(kind, str) or kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind!r}")
        fresh = to_fraction(item["fresh"], f"items[{i}].fresh")
        if not FRESH_MIN <= fresh <= FRESH_MAX:
            raise BadInput(f"items[{i}].fresh phải trong [{FRESH_MIN}, {FRESH_MAX}], đang là {item['fresh']!r}")
        out.append({"id": iid, "kind": kind, "fresh": fresh})
    return out


def new_item(ids, kind, initial) -> dict:
    """Cá thể mới vừa bắt/hái: id kế tiếp của họ "I" từ allocator dùng chung, fresh = initial (tuning)."""
    return {"id": ids.new(ITEM_ID_PREFIX), "kind": kind, "fresh": to_fraction(initial, "freshness.initial")}


@lru_cache(maxsize=None)
def _rates(decay_per_s, tick_hz, spoiled_below):
    """(lượng hao mỗi tick, ngưỡng ươn) dạng Fraction; dựng một lần cho mỗi bộ số liệu."""
    return to_fraction(decay_per_s) / to_fraction(tick_hz), to_fraction(spoiled_below)


def age_items(items, decay_per_s, tick_hz, spoiled_below, location) -> list:
    """Hao tại chỗ mỗi cá thể decay_per_s / tick_hz, kẹp đáy 0.

    Trả các cặp ("spoiled", {item_id, kind, location}) xếp theo id cho cá thể đi từ >= ngưỡng xuống < ngưỡng ở lần
    hao này (đúng một lần mỗi cá thể vì độ tươi chỉ giảm).
    """
    if not items:
        return []
    step, threshold = _rates(decay_per_s, tick_hz, spoiled_below)
    crossed = []
    for item in items:  # đường nóng mỗi tick: kiểm dấu tử số thay vì so Fraction với step (nhanh hơn ~1/3)
        before = item["fresh"]
        after = before - step
        if after.numerator < 0:
            after = _ZERO
        item["fresh"] = after
        if after < threshold <= before:
            crossed.append(item)
    if len(crossed) > 1:
        crossed.sort(key=lambda it: id_key(it["id"]))
    return [("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": location}) for it in crossed]


def view_items(items, spoiled_below) -> list:
    """Bản sao để ghi JSON (file, event, snapshot), giữ thứ tự vào.

    fresh thành float đủ chữ số (repr đọc lại ra đúng float đó); nếu làm tròn float đưa giá trị sang phía kia của
    ngưỡng ươn thì lấy float gần nhất còn đúng phía.
    """
    threshold = to_fraction(spoiled_below)
    thr = float(threshold)
    below = math.nextafter(thr, -math.inf)
    out = []
    for item in items:
        fresh = item["fresh"]
        x = float(fresh)
        if fresh < threshold and x >= thr:
            x = below
        elif fresh >= threshold and x < thr:
            x = thr
        out.append({"id": item["id"], "kind": item["kind"], "fresh": x})
    return out
