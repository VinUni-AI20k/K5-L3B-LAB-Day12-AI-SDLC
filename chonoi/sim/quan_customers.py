"""Quán lát 3 — vòng đời khách.

`quan.py` đã gọi sẵn hai hàm dưới đây mỗi bước. Schema một khách: docs/contracts/customer.md
(lát 3 chốt; lát 4 dùng).

Dùng được trên `sim` (QuanSim):
  sim.t (tuning quan), sim.menu, sim.stock, sim.customers, sim.tables, sim.ids (IdAllocator),
  sim.rng (Streams — mọi ngẫu nhiên đi qua đây), sim.time_left_ticks, sim.reputation
Số liệu chỉ đọc từ sim.t / sim.menu (first_customer_tick, customer_interval_s, patience_s,
left_reputation_delta...). Sự kiện: events.append((tên, data)).
"""


def tick_customers(sim, events):
    """TODO(lát 3): giảm kiên nhẫn khách đang chờ; hết kiên nhẫn -> `customer_left`,
    trả nguyên liệu đã giữ chỗ về kho, trừ uy tín (left_reputation_delta)."""


def spawn_customers(sim, events):
    """TODO(lát 3): khách mới theo lịch (first_customer_tick, customer_interval_s) nếu còn bàn trống;
    chọn món nấu được từ kho (trừ phần đã giữ chỗ), giữ chỗ nguyên liệu (reserved); không món nào -> `no_dish`."""
