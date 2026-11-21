"""Quán lát 4 — bếp, bưng, phục vụ, tiền, uy tín. Lát này giữ luôn `quan.py`.

`quan.py` đã gọi sẵn:
  - `tick_service`: mỗi bước, trước khi đi lại.
  - `interact`:     khi bấm `interact`.

Dùng được trên `sim` (QuanSim):
  sim.t, sim.menu, sim.stock, sim.hand, sim.stoves, sim.tables, sim.customers, sim.pos,
  sim.money, sim.earned, sim.shift_earned, sim.reputation
Schema khách: docs/contracts/customer.md. Sự kiện: events.append((tên, data)).
"""


def tick_service(sim, events):
    """TODO(lát 4): bếp đang nấu đếm ngược -> `dish_ready`; khách đang ăn đếm ngược
    -> `paid` (giá + boa theo tip_rate / tip_min_patience_ratio), cộng tiền, cập nhật uy tín."""


def interact(sim, events):
    """TODO(lát 4): tối đa MỘT interact, chọn đối tượng trong interact_radius theo
    (khoảng cách, bếp trước bàn, id): bếp -> `cook_started` / `dish_picked`; bàn -> `served`."""
