"""Độ tươi (v1.2, Ticket-03): đơn vị số nguyên, đọc từ `tuning.freshness`. Dùng chung cho gather, quán, HUD.

Trong sim `fresh` là SỐ NGUYÊN ĐƠN VỊ (`units`): `units_per_point` đơn vị = 1 điểm tươi. Trong file kho và snapshot
`fresh` là ĐIỂM (làm tròn 3 chữ số). Hao mỗi tick là số nguyên đơn vị nên ngưỡng ươn và giá `floor` đúng từng tick,
không có sai số số thực.
"""

from .errors import BadInput

PHASES = ("gather", "quan")
POINT_DIGITS = 3  # làm tròn điểm tươi khi ghi ra (đủ để đổi ngược về đúng số nguyên đơn vị)


class Freshness:
    def __init__(self, tuning):
        f = tuning.get("freshness")
        if not isinstance(f, dict):
            raise BadInput("tuning.freshness chỉ có từ contract 1.2")
        self.units_per_point = f["units_per_point"]
        self.max_units = f["fresh_max"] * self.units_per_point
        self.spoil_units = f["spoil_below"] * self.units_per_point
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


def decay_units_per_tick(freshness, tick_hz, phase) -> int:
    """Hao mỗi tick, đơn vị nguyên; BadInput nếu tốc độ ×units_per_point không chia hết cho tick_hz."""
    per_tick = freshness["decay_per_s"][phase] * freshness["units_per_point"] / tick_hz
    if abs(per_tick - round(per_tick)) > 1e-9:
        raise BadInput(f"tuning.freshness: hao {phase} phải ra số nguyên đơn vị mỗi tick, đang là {per_tick}")
    return round(per_tick)
