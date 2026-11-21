"""Quản lý giỏ nguyên liệu buổi sáng (thứ tự nhặt LIFO, sức chứa hold_capacity).

Chủ: Trần Duy Thành (Lát 1). Chỉ module này được ghi sim.hold.
"""


def free_slots(sim) -> int:
    return sim.t["hold_capacity"] - len(sim.hold)


def push_all(sim, kinds: list) -> bool:
    if len(kinds) > free_slots(sim):
        return False
    sim.hold.extend(kinds)
    return True


def clear(sim) -> None:
    sim.hold.clear()
