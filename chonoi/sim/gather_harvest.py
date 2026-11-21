"""Gather lát 2 — hái nút + bắt cá.

`gather.py` đã gọi sẵn hai hàm dưới đây đúng chỗ trong một bước:
  - `try_gather`: khi bấm `interact` mà KHÔNG ở bến (bến đã xét trước).
  - `try_catch`:  khi bấm `catch`.

Dùng được trên `sim` (GatherSim):
  sim.t (tuning gather), sim.pos, sim.nodes, sim.fish, sim.hold, sim.catch_cd_ticks, sim._at_surface()
  sim._add_to_hold(kind, n, events, source) -> bool   # thiếu chỗ: tự phát hold_full {**source, required, free}
      source = {"action": "catch", "fish_id": id} hoặc {"action": "gather", "node_id": id}
Số liệu chỉ đọc từ sim.t (interact_radius, node_yield, regrow_s, catch_radius, catch_cooldown_s, fish_yield).
Sự kiện: events.append((tên, data)).
"""


def try_gather(sim, events):
    """TODO(lát 2): chỉ khi ở mặt nước: hái nút `ready` gần nhất trong interact_radius
    (bằng khoảng cách thì id nhỏ hơn) -> sự kiện `gather` / `hold_full`; đặt regrow_ticks cho nút."""


def try_catch(sim, events):
    """TODO(lát 2): chỉ khi catch_cd_ticks == 0 và dưới nước: bắt đàn cá trong catch_radius
    -> `fish_caught` / `hold_full`; đặt lại catch_cd_ticks."""
