"""Lát 1 — Lặn sống sót (bơi, chuyển vùng mặt nước/dưới nước, oxy, ngạt, ngất).

Chủ: Trần Duy Thành (thanh289). Stub dựng sẵn từ commit khung T000.
"""


def zone_change(sim, was_surface: bool, events: list) -> None:
    # TODO(thanh289): so vùng đầu/cuối bước -> phát 'dive' / 'surface' (data: {"pos": list(sim.pos)}).
    pass


def update_oxygen(sim, events: list) -> bool:
    # TODO(thanh289): cập nhật oxy, oxygen_empty, đếm ngạt, choke, Máu.
    # Máu == 0 -> hold.clear(sim), phát 'faint', trả True.
    return False
