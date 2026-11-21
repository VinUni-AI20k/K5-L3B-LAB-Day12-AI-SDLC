"""Độ tươi và cá thể nguyên liệu (Test Contract v1.2, Ticket-03 mục 1). KHUNG — Integrator giữ, cả nhóm dùng.

Tính bằng số nguyên để so ngưỡng 30 và phép floor chính xác: 240 đơn vị cho mỗi điểm tươi (UNITS).
- Giỏ hao 0.5/s = 1/120 điểm mỗi tick = 2 đơn vị/tick; kho quán hao 0.25/s = 1 đơn vị/tick.
- Ươn khi fresh < 30, tức u < 7200.

Cá thể TRONG CODE: {"id": "I1", "kind": "ca_linh", "u": 24000}.
Cá thể RA NGOÀI (snapshot, event, file kho): {"id": "I1", "kind": "ca_linh", "fresh": 100.0} qua `public()`.

v1.2 bật khi manifest có khối `freshness` (contract.py bắt buộc khối này ở 1.2 và cấm ở 1.1): dùng `enabled(tuning)`.
"""

import math

UNITS = 240


def enabled(tuning) -> bool:
    """True khi chạy Test Contract v1.2 (kho cá thể, có độ tươi)."""
    return "freshness" in tuning


def cfg(tuning) -> dict:
    """Hằng số độ tươi tính bằng đơn vị nguyên."""
    f = tuning["freshness"]
    return {
        "initial_u": to_units(f["initial"]),
        "gather_decay_u": to_units(f["gather_decay_per_s"]) // 60,
        "quan_decay_u": to_units(f["quan_decay_per_s"]) // 60,
        "spoiled_u": to_units(f["spoiled_below"]),
    }


def to_units(fresh) -> int:
    """Điểm tươi -> đơn vị. Làm tròn xuống (kèm dung sai nhỏ) để không bao giờ đổi phía ngưỡng nguyên."""
    return int(math.floor(fresh * UNITS + 1e-9))


def fresh_of(item) -> float:
    return item["u"] / UNITS


def new_item(ids, kind, tuning) -> dict:
    """Cá thể mới (vừa bắt/hái hoặc hàng mua): id I<n> nối tiếp, fresh = freshness.initial."""
    return {"id": ids.new("I"), "kind": kind, "u": cfg(tuning)["initial_u"]}


def from_public(obj) -> dict:
    """{id, kind, fresh} (fixture, file kho) -> cá thể trong code."""
    return {"id": obj["id"], "kind": obj["kind"], "u": to_units(obj["fresh"])}


def public(item) -> dict:
    return {"id": item["id"], "kind": item["kind"], "fresh": fresh_of(item)}


def public_list(items) -> list:
    return [public(it) for it in items]


def out(items) -> list:
    """Xuất danh sách hàng: cá thể -> public, chuỗi kind (v1.1) giữ nguyên. Dùng cho lost, hold, stock..."""
    return [public(it) if isinstance(it, dict) else it for it in items]


def is_spoiled(item, tuning) -> bool:
    return item["u"] < cfg(tuning)["spoiled_u"]


def decay(items, units_per_tick, tuning) -> list:
    """Trừ `units_per_tick` cho mọi cá thể (kẹp đáy 0). Trả các cá thể VỪA ươn (đi từ >= ngưỡng xuống < ngưỡng),
    sắp theo id, để phát `spoiled` đúng một lần theo id."""
    from .ids import sort_by_id
    limit = cfg(tuning)["spoiled_u"]
    newly = []
    for it in items:
        before = it["u"]
        it["u"] = max(0, before - units_per_tick)
        if before >= limit > it["u"]:
            newly.append(it)
    return sort_by_id(newly)
