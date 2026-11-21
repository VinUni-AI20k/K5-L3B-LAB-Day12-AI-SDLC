"""Helper độ tươi dùng chung cho Phase 3 (Contract v1.2 — M1, M2, M3, M4, M6).

Dùng biểu diễn nguyên `FRESH_SCALE = 240` đơn vị mỗi điểm tươi (theo gợi ý Ticket03):
- `fresh = 100` -> `24000` đơn vị
- `gather` (-0.5/s ở 60 Hz) -> trừ đúng `2` đơn vị/tick
- `quan`   (-0.25/s ở 60 Hz) -> trừ đúng `1` đơn vị/tick
- Ngưỡng ươn `< 30` -> so `units < 30 * 240 = 7200` (chính xác tuyệt đối, không sai số float).
"""

import math

FRESH_SCALE = 240


def to_units(fresh: float) -> int:
    """Chuyển độ tươi [0, 100] sang đơn vị nguyên (làm tròn gần nhất)."""
    return max(0, int(round(float(fresh) * FRESH_SCALE)))


def from_units(units: int) -> float:
    """Chuyển đơn vị nguyên về độ tươi float (giữ đủ độ chính xác ở ngưỡng 30)."""
    val = max(0, int(units)) / FRESH_SCALE
    return round(val, 6)


def decay_units_per_tick(decay_per_s: float, tick_hz: int = 60) -> int:
    """Số đơn vị nguyên hao mỗi tick (0.5/s -> 2, 0.25/s -> 1 ở 60 Hz)."""
    return int(round((float(decay_per_s) / float(tick_hz)) * FRESH_SCALE))


def is_spoiled_units(units: int, spoiled_below: float = 30.0) -> bool:
    """Kiểm tra đã ươn (`fresh < spoiled_below`) trước làm tròn."""
    return int(units) < int(round(float(spoiled_below) * FRESH_SCALE))


def is_spoiled(fresh: float, spoiled_below: float = 30.0) -> bool:
    """Kiểm tra trực tiếp giá trị `fresh` float."""
    return float(fresh) < float(spoiled_below)


def calc_fresh_base_price(list_price: int, item_units: list) -> int:
    """Tính `floor(giá niêm yết * avg_fresh / 100)` chính xác bằng số nguyên."""
    if not item_units:
        return int(list_price)
    total_units = sum(int(u) for u in item_units)
    return (int(list_price) * total_units) // (100 * FRESH_SCALE * len(item_units))


def calc_fresh_base_price_float(list_price: int, fresh_values: list) -> int:
    """Biến thể nhận danh sách `fresh` float, chuyển qua đơn vị nguyên để tránh sai số."""
    if not fresh_values:
        return int(list_price)
    return calc_fresh_base_price(list_price, [to_units(v) for v in fresh_values])


def calc_tip(base_price: int, tip_rate: float) -> int:
    """Tính boa `floor(base_price * tip_rate)` trên giá đã chốt."""
    return math.floor(int(base_price) * float(tip_rate))
