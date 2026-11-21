"""Khách, giữ chỗ, kiên nhẫn — lát 3 (PRD §F, mục Quán).

Không sửa `quan.py` ngoài ba dòng gọi vào; bếp/bưng/phục vụ/tiền nằm ở `quan_service.py`.
Giữ chỗ KHÔNG trừ `stock`: `stock` đã bao gồm phần đang giữ (PRD §D). Chỉ khi bắt đầu nấu
mới tiêu nguyên liệu (việc của lát 4).
"""

import math

from ..ids import id_key
from .quan_service import cancel_customer_order

TICK = 60


def _clamp(rep, t):
    return max(t["reputation_min"], min(t["reputation_max"], rep))


def _reserved_totals(sim):
    out = {}
    for c in sim.customers:
        for k, n in c["reserved"].items():
            out[k] = out.get(k, 0) + n
    return out


def affordable_dishes(sim):
    """Món mà kho khả dụng (tồn trừ phần đang giữ) đủ nguyên liệu, sắp theo id.
    Trong `day`: lọc menu theo `day_plan.dishes` trước, rồi mới lọc nguyên liệu khả dụng.
    Quán độc lập dùng cả 6 món."""
    held = _reserved_totals(sim)
    out = []
    if getattr(sim, "day_plan", None) and isinstance(sim.day_plan, dict) and "dishes" in sim.day_plan:
        candidate_dishes = sorted(sim.day_plan["dishes"])
    else:
        candidate_dishes = sorted(sim.menu)
    for dish_id in candidate_dishes:
        if dish_id not in sim.menu:
            continue
        recipe = sim.menu[dish_id]["recipe"]
        if all(sim.stock.get(k, 0) - held.get(k, 0) >= n for k, n in recipe.items()):
            out.append(dish_id)
    return out


def free_table(sim):
    taken = {c["table_id"] for c in sim.customers}
    free = [tb for tb in sim.tables if tb["id"] not in taken]
    return min(free, key=lambda tb: id_key(tb["id"])) if free else None


def tick_patience(sim, events):
    for c in sim.customers:
        if c["state"] == "waiting" and c["patience_ticks_left"] > 0:
            c["patience_ticks_left"] -= 1


def _leave(sim, c, reason, events):
    sim.customers.remove(c)
    cancel_customer_order(sim, c["id"])
    if reason == "patience":
        sim.reputation = _clamp(sim.reputation + sim.t["left_reputation_delta"], sim.t)
    events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"],
                                     "reason": reason, "reputation": sim.reputation}))


def leave_if_impatient(sim, events):
    if sim.time_left_ticks <= 0:
        return
    for c in list(sim.customers):
        if c["state"] == "waiting" and c["patience_ticks_left"] == 0:
            _leave(sim, c, "patience", events)


def close_shift(sim, events):
    """Hết ca: khách còn chờ rời với lý do closing, không trừ uy tín."""
    for c in list(sim.customers):
        if c["state"] == "waiting":
            _leave(sim, c, "closing", events)


def spawn_due(sim, events):
    """Lượt khách theo phase_tick: first_customer_tick, rồi mỗi customer_interval_s × 60."""
    first = sim.t["first_customer_tick"]
    interval = int(round(sim.t["customer_interval_s"] * TICK))
    pt = sim.phase_tick
    if pt < first or (pt - first) % interval:
        return
    table = free_table(sim)
    if table is None:
        return
    dishes = affordable_dishes(sim)
    if not dishes:
        events.append(("no_dish", {}))
        return
    dish_id = sim.rng.get("customer_dish").choice(dishes)
    cid = sim.ids.new("C")
    sim.customers.append({
        "id": cid,
        "table_id": table["id"],
        "dish_id": dish_id,
        "order_tick": pt,
        "state": "waiting",
        "patience_ticks_left": int(round(sim.t["patience_s"] * TICK)),
        "eat_ticks_left": 0,
        "order_status": "reserved",
        "reserved": dict(sim.menu[dish_id]["recipe"]),
        "base_price": None,
        "tip": None,
    })
    events.append(("customer_arrived", {"order_id": cid, "table_id": table["id"], "dish_id": dish_id}))


def distance(sim, c):
    """Khoảng cách người chơi tới bàn của khách (dùng cho lát 4 khi phục vụ)."""
    table = next((tb for tb in sim.tables if tb["id"] == c["table_id"]), None)
    return math.dist(sim.pos, table["pos"]) if table else float("inf")
