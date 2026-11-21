"""Lát 3 — Khách đến, chọn món, giữ chỗ nguyên liệu, kiên nhẫn, bỏ đi.

Chủ: Đặng Đức Minh (DMinh1102).
Commit khung dựng sẵn các hàm API truy vấn/tiêu thụ cơ bản để Lát 4 kiểm thử độc lập;
phần lịch khách, chọn món, kiên nhẫn, bỏ đi, validate fixture do Lát 3 triển khai.
"""

from ..ids import sort_by_id


def validate_scenario(block: dict, tuning: dict) -> None:
    # TODO(DMinh1102): kiểm tra mâu thuẫn mức luật về khách/giữ chỗ (reserved vượt kho...) -> raise BadInput.
    pass


def on_load(sim) -> None:
    # TODO(DMinh1102): chuẩn hóa khách từ fixture (giữ chỗ, patience_ticks mặc định, _cooking).
    for c in sim.customers:
        c.setdefault("state", "waiting")
        c.setdefault("reserved", {})
        c.setdefault("_cooking", False)


def available_stock(sim) -> dict:
    avail = dict(sim.stock)
    for c in sim.customers:
        for k, v in c.get("reserved", {}).items():
            avail[k] = avail.get(k, 0) - v
    return {k: v for k, v in sorted(avail.items()) if v > 0}


def pending_order(sim):
    waiting = [c for c in sim.customers if c.get("state") == "waiting" and not c.get("_cooking")]
    if not waiting:
        return None
    return sort_by_id(waiting)[0]


def consume_reserved(sim, customer: dict) -> None:
    for k, qty in customer.get("reserved", {}).items():
        left = sim.stock.get(k, 0) - qty
        if left > 0:
            sim.stock[k] = left
        else:
            sim.stock.pop(k, None)
    customer["reserved"] = {}
    customer["_cooking"] = True


def customer_at_table(sim, table_id: str):
    for c in sim.customers:
        if c.get("table_id") == table_id:
            return c
    return None


def remove(sim, customer: dict) -> None:
    if customer in sim.customers:
        sim.customers.remove(customer)


def tick_patience(sim, events: list) -> None:
    # TODO(DMinh1102): giảm patience_ticks của khách waiting.
    pass


def process_departures(sim, events: list) -> list:
    # TODO(DMinh1102): khách waiting có patience_ticks == 0 -> trả reserved, customer_left, add_reputation(-0.5), remove.
    return []


def spawn_if_due(sim, events: list) -> None:
    # TODO(DMinh1102): lịch theo sim.step_no (first_customer_tick, customer_interval_s), chọn món qua Streams('customer_order'), no_dish.
    pass


def close_shift(sim, events: list) -> None:
    # TODO(DMinh1102): đóng ca — khách waiting rời đi không phạt uy tín.
    pass
