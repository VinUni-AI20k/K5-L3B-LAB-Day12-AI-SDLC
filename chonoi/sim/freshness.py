"""Độ tươi & kho cá thể cho buổi Lặn (Phase 3 / TICKET-03 v1.2 — TV2, T310–T312).

Dùng chung hằng và hàm quy đổi của TV1 từ `chonoi.inventory` (`FRESH_SCALE = 240`,
`decay_units_per_tick`, `uses_individuals`) theo ADR-0001:
- Lưu độ tươi nội bộ bằng số nguyên 240 đơn vị / 1 điểm (`u ∈ [0, 24000]`).
- Giỏ hao `decay_units_per_tick(gather_decay_per_s, tick_hz)` (chuẩn: 0.5/s → −2/tick), kẹp đáy 0.
- Ươn khi `u < spoiled_below × 240` (chuẩn: `< 7200`); phát `spoiled` đúng một lần khi đi từ `>= 7200`
  xuống `< 7200`, sắp theo `id_key` nếu nhiều cá thể cùng vượt ngưỡng trong một tick.
- Kích hoạt theo `uses_individuals(contract_version)` (hoặc khi có `item_ids` / `hold` cá thể ở v1.2),
  giữ nguyên hành vi kho đếm cho `contract_version < 1.2` dù `game.contract.json` v1.1 đã có sẵn
  khóa `tuning.freshness`.
"""

from dataclasses import dataclass

from ..ids import id_key, sort_by_id
from ..inventory import FRESH_SCALE, decay_units_per_tick, uses_individuals

UNITS_PER_FRESH = FRESH_SCALE
MAX_FRESH = 100
MAX_UNITS = MAX_FRESH * UNITS_PER_FRESH


@dataclass(frozen=True)
class FreshnessConfig:
    initial: float
    initial_u: int
    gather_decay_u: int
    spoiled_below: float
    spoiled_below_u: int


def should_use_freshness(tuning: dict, raw_hold: list, contract_version=None, item_ids=None) -> bool:
    """Quyết định bật chế độ kho cá thể + độ tươi (v1.2+) hay giữ kho đếm (v1.0/v1.1)."""
    if not isinstance(tuning.get("freshness"), dict):
        return False
    if contract_version is not None:
        return uses_individuals(contract_version)
    if item_ids is not None:
        return True
    return any(isinstance(entry, dict) for entry in raw_hold)


def parse_freshness_config(tuning: dict):
    """Đọc `tuning.freshness` (dùng `decay_units_per_tick` của TV1); trả None nếu thiếu."""
    raw = tuning.get("freshness")
    if not isinstance(raw, dict):
        return None
    tick_hz = float(tuning.get("tick_hz", 60))
    initial = float(raw.get("initial", 100))
    spoiled_below = float(raw.get("spoiled_below", 30))
    spoiled_below_u = int(round(spoiled_below * UNITS_PER_FRESH))
    initial_u = fresh_to_units(initial, spoiled_below, spoiled_below_u)
    decay_per_s = float(raw.get("gather_decay_per_s", 0.5))
    gather_decay_u = max(0, decay_units_per_tick(decay_per_s, tick_hz))
    return FreshnessConfig(
        initial=initial,
        initial_u=initial_u,
        gather_decay_u=gather_decay_u,
        spoiled_below=spoiled_below,
        spoiled_below_u=spoiled_below_u,
    )


def fresh_to_units(fresh: float, spoiled_below: float = 30.0, spoiled_below_u: int = 7200) -> int:
    """Đổi độ tươi [0, 100] sang đơn vị nguyên [0, 24000], giữ nguyên nhánh tại ngưỡng ươn."""
    f = float(fresh)
    if f <= 0.0:
        return 0
    if f >= MAX_FRESH:
        return MAX_UNITS
    u = int(round(f * UNITS_PER_FRESH))
    if f < spoiled_below and u >= spoiled_below_u:
        u = spoiled_below_u - 1
    elif f >= spoiled_below and u < spoiled_below_u:
        u = spoiled_below_u
    return max(0, min(MAX_UNITS, u))


def units_to_fresh(u: int):
    """Đổi đơn vị nguyên sang điểm tươi đầy đủ độ chính xác (số nguyên nếu chia hết 240)."""
    if u <= 0:
        return 0
    if u % UNITS_PER_FRESH == 0:
        return u // UNITS_PER_FRESH
    return u / UNITS_PER_FRESH


def reserve_item_id(allocator, ident: str) -> None:
    """Giữ chỗ id đã tồn tại trên `IdAllocator` hoặc bất kỳ `ItemIds` nào có `.reserve(id)`."""
    if allocator is None or not ident:
        return
    reserve = getattr(allocator, "reserve", None)
    if callable(reserve):
        reserve(ident)


def next_item_id(allocator) -> str:
    """Cấp id cá thể `I<n>` qua `IdAllocator.new('I')`, hoặc `ItemIds.new()` / `.next()`."""
    new_fn = getattr(allocator, "new", None)
    if callable(new_fn):
        try:
            return new_fn("I")
        except TypeError:
            return new_fn()
    next_fn = getattr(allocator, "next", None)
    if callable(next_fn):
        return next_fn()
    raise TypeError("item_ids allocator phải hỗ trợ .new('I'), .new(), hoặc .next()")


def make_fresh_item(allocator, kind: str, cfg: FreshnessConfig) -> dict:
    """Tạo cá thể mới trong giỏ khi hái/bắt (fresh = initial, hao từ bước sau)."""
    return {"id": next_item_id(allocator), "kind": kind, "u": cfg.initial_u}


def build_hold_items(raw_hold: list, cfg: FreshnessConfig, allocator) -> list:
    """Khởi tạo giỏ cá thể từ scenario theo đúng thứ tự vào giỏ; reserve trước khi cấp id mới."""
    for entry in raw_hold:
        if isinstance(entry, dict):
            raw_id = entry.get("id")
            if isinstance(raw_id, str) and raw_id:
                reserve_item_id(allocator, raw_id)
    out = []
    for entry in raw_hold:
        if isinstance(entry, dict):
            raw_id = entry.get("id")
            ident = raw_id if (isinstance(raw_id, str) and raw_id) else next_item_id(allocator)
            if isinstance(entry.get("u"), int) and not isinstance(entry.get("u"), bool):
                u = max(0, min(MAX_UNITS, entry["u"]))
            else:
                u = fresh_to_units(entry.get("fresh", cfg.initial), cfg.spoiled_below, cfg.spoiled_below_u)
            out.append({"id": ident, "kind": entry["kind"], "u": u})
        else:
            out.append(make_fresh_item(allocator, str(entry), cfg))
    return out


def decay_hold(hold: list, cfg: FreshnessConfig, events: list) -> None:
    """Hao tươi toàn bộ cá thể đang có trong giỏ đầu bước; phát `spoiled` đúng 1 lần theo `id_key`."""
    if not hold or cfg.gather_decay_u <= 0:
        return
    newly_spoiled = []
    for item in hold:
        prev_u = item["u"]
        new_u = max(0, prev_u - cfg.gather_decay_u)
        item["u"] = new_u
        if prev_u >= cfg.spoiled_below_u and new_u < cfg.spoiled_below_u:
            newly_spoiled.append(item)
    for item in sorted(newly_spoiled, key=lambda it: id_key(it["id"])):
        events.append(("spoiled", {
            "item_id": item["id"],
            "kind": item["kind"],
            "location": "hold",
        }))


def serialize_hold_item(item: dict) -> dict:
    """Biểu diễn JSONL/file của một cá thể: `{id, kind, fresh}` (không lộ `u` nội bộ)."""
    return {"id": item["id"], "kind": item["kind"], "fresh": units_to_fresh(item["u"])}


def serialize_hold(hold: list) -> list:
    """Tuần tự hóa giỏ hoặc danh sách rơi giữ nguyên thứ tự hiện có (vào giỏ / LIFO)."""
    return [serialize_hold_item(item) for item in hold]


def serialize_inventory_items(hold: list) -> list:
    """Xuất mảng cá thể kho v1.2 sắp theo `id_key` với độ chính xác đầy đủ cho `fresh`."""
    return [serialize_hold_item(item) for item in sort_by_id(hold)]
