"""Lát 2 — Hái rau mặt nước và bắt cá dưới nước.

Chủ: Đoàn Anh Hùng (doananhhung). Stub dựng sẵn từ commit khung T000.
"""


def try_gather(sim, events: list) -> None:
    # TODO(doananhhung): chỉ khi sim._at_surface(), pick.nearest trên nút ready -> hold.push_all -> gather / hold_full.
    pass


def try_catch(sim, events: list) -> None:
    # TODO(doananhhung): chỉ khi dưới nước và catch_cd_ticks == 0 -> pick.nearest trên sim.fish -> fish_caught / hold_full.
    pass
