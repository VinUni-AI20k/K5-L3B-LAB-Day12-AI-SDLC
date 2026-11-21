"""Độ tươi (v1.2, Ticket-03): đơn vị số nguyên, đọc từ `tuning.freshness`. Dùng chung cho gather, quán, HUD.

Khối `tuning.freshness` đúng 4 khóa theo Ticket-03: `initial` (độ tươi cá thể mới), `gather_decay_per_s`,
`quan_decay_per_s` (điểm hao mỗi giây) và `spoiled_below` (ươn khi `fresh < spoiled_below`).

Trong sim `fresh` là SỐ NGUYÊN ĐƠN VỊ (`units`): `UNITS_PER_POINT` đơn vị = 1 điểm tươi (gợi ý của đề, chi tiết cài đặt
nên không nằm trong contract). Trong file kho và snapshot `fresh` là ĐIỂM (làm tròn 3 chữ số). Hao mỗi tick là số
nguyên đơn vị nên ngưỡng ươn và giá `floor` đúng từng tick, không có sai số số thực.
"""

from .errors import BadInput

PHASES = ("gather", "quan")
UNITS_PER_POINT = 240  # đơn vị nguyên mỗi điểm tươi; 0.5/s và 0.25/s ở 60 tick/s ra đúng 2 và 1 đơn vị mỗi tick
FRESH_SCALE = 100  # công thức giá của đề chia trung bình `fresh` cho 100
KEYS = {"initial", "gather_decay_per_s", "quan_decay_per_s", "spoiled_below"}
POINT_DIGITS = 3  # làm tròn điểm tươi khi ghi ra (đủ để đổi ngược về đúng số nguyên đơn vị)


class Freshness:
    def __init__(self, tuning):
        f = tuning.get("freshness")
        if not isinstance(f, dict):
            raise BadInput("tuning.freshness chỉ có từ contract 1.2")
        self.units_per_point = UNITS_PER_POINT
        self.max_units = f["initial"] * self.units_per_point
        self.spoil_units = f["spoiled_below"] * self.units_per_point
        self._decay = {p: decay_units_per_tick(f, tuning["tick_hz"], p) for p in PHASES}

    def decay(self, phase) -> int:
        """Số đơn vị hao mỗi tick ở pha `gather` hoặc `quan`."""
        return self._decay[phase]

    def is_spoiled(self, units) -> bool:
        """Ươn khi fresh < ngưỡng (xuống từ >= ngưỡng thì phát `spoiled`)."""
        return units < self.spoil_units

    def to_units(self, points) -> int:
        return round(points * self.units_per_point)

    def to_points(self, units):
        return round(units / self.units_per_point, POINT_DIGITS)

    def dish_price(self, list_price, units) -> int:
        return dish_price(list_price, units, self.units_per_point)


def decay_units_per_tick(freshness, tick_hz, phase) -> int:
    """Hao mỗi tick, đơn vị nguyên; BadInput nếu tốc độ ×UNITS_PER_POINT không chia hết cho tick_hz."""
    per_tick = freshness[f"{phase}_decay_per_s"] * UNITS_PER_POINT / tick_hz
    if abs(per_tick - round(per_tick)) > 1e-9:
        raise BadInput(f"tuning.freshness: hao {phase} phải ra số nguyên đơn vị mỗi tick, đang là {per_tick}")
    return round(per_tick)


def dish_price(list_price, units, units_per_point=UNITS_PER_POINT) -> int:
    """Giá món theo đề: floor(giá niêm yết × trung bình fresh / 100), không hệ số phụ.

    `units` là danh sách độ tươi (số nguyên đơn vị) của các nguyên liệu dùng cho món. Tính bằng số nguyên nên `floor`
    đúng từng tick, không sai số số thực.
    """
    if not units:
        raise ValueError("cần ít nhất một nguyên liệu để tính giá theo độ tươi")
    return list_price * sum(units) // (len(units) * units_per_point * FRESH_SCALE)
