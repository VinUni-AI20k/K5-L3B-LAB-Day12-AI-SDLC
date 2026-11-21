"""Quán lát 4 (@minhthu27) — bếp, bưng, phục vụ, tiền, boa, uy tín. Lát này giữ luôn `quan.py`.

`quan.py` gọi: `tick_service` (mỗi bước, trước khi đi lại) và `interact` (khi bấm `interact`).
Số liệu chỉ đọc từ `sim.t` / `sim.menu`. Schema khách: docs/contracts/customer.md
(state `waiting` -> `eating`; khách rời đi do lát 3 xử lý trong `tick_customers`).

Bếp nhớ khách mình nấu cho bằng khóa nội bộ `customer_id` (không xuất ra snapshot).
Ghi chú ghép với lát 3: `reserved` là phần nguyên liệu GIỮ CHỖ trong `sim.stock`; khi bếp nhận đơn,
nguyên liệu được trừ khỏi kho và `reserved` về `{}`.
"""

import math

from ..ids import id_key

TICK = 60


def _clamp_rep(sim, v):
    return max(sim.t["reputation_min"], min(sim.t["reputation_max"], v))


# --- mỗi bước: bếp, ăn, trả tiền -----------------------------------------------------
def tick_service(sim, events):
    ids = {c["id"] for c in sim.customers}
    for s in sim.stoves:
        if s.get("customer_id") and s["customer_id"] not in ids:  # khách đã bỏ đi: bỏ món
            _reset_stove(s)
        if s["state"] == "cooking":
            s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
            if s["cook_ticks_left"] == 0:
                s["state"], s["ready_ticks"] = "ready", 0
                events.append(("dish_ready", {"stove_id": s["id"], "dish": s["dish"]}))
        elif s["state"] == "ready":
            s["ready_ticks"] += 1  # burn_s = null: không cháy
    paid = []
    for c in sorted(sim.customers, key=lambda c: id_key(c["id"])):
        if c["state"] == "eating":
            c["eat_ticks"] = max(0, c.get("eat_ticks", 0) - 1)
            if c["eat_ticks"] == 0:
                _pay(sim, c, events)
                paid.append(c["id"])
    if paid:
        sim.customers = [c for c in sim.customers if c["id"] not in paid]


def _pay(sim, c, events):
    price = sim.menu[c["dish"]]["price"]
    tip = 0
    if c["patience_ticks"] >= sim.t["tip_min_patience_ratio"] * sim.t["patience_s"] * TICK:
        tip = int(math.floor(price * sim.t["tip_rate"]))
        if tip > 0:
            sim.reputation = _clamp_rep(sim, sim.reputation + sim.t["tip_reputation"])
    total = price + tip
    sim.money += total
    sim.earned += total
    sim.shift_earned += total
    events.append(("paid", {"customer_id": c["id"], "table_id": c["table_id"], "dish": c["dish"],
                            "price": price, "tip": tip, "total": total}))


def _reset_stove(s):
    s["state"], s["dish"], s["cook_ticks_left"], s["ready_ticks"] = "idle", None, 0, 0
    s.pop("customer_id", None)


# --- interact -------------------------------------------------------------------------
def interact(sim, events):
    """Tối đa MỘT interact/bước: đối tượng trong interact_radius theo (khoảng cách, bếp trước bàn, id)."""
    r = sim.t["interact_radius"]
    cands = [(math.dist(sim.pos, o["pos"]), kind, id_key(o["id"]), o)
             for kind, objs in ((0, sim.stoves), (1, sim.tables)) for o in objs]
    cands = sorted((c for c in cands if c[0] <= r), key=lambda c: c[:3])
    if not cands:
        return
    kind, obj = cands[0][1], cands[0][3]
    (_use_stove if kind == 0 else _use_table)(sim, obj, events)


def _use_stove(sim, s, events):
    if s["state"] == "ready":
        if sim.hand is None:  # carry_limit = 1
            sim.hand = s["dish"]
            events.append(("dish_picked", {"stove_id": s["id"], "dish": s["dish"]}))
            _reset_stove(s)
    elif s["state"] == "idle":
        _start_cooking(sim, s, events)


def _start_cooking(sim, s, events):
    """Nhận đơn của khách `waiting` (id nhỏ nhất, chưa có bếp nào nấu) mà kho đủ nguyên liệu."""
    taken = {st.get("customer_id") for st in sim.stoves}
    for c in sorted(sim.customers, key=lambda c: id_key(c["id"])):
        if c["state"] != "waiting" or c["id"] in taken:
            continue
        recipe = sim.menu[c["dish"]]["recipe"]
        if any(sim.stock.get(k, 0) < n for k, n in recipe.items()):
            continue
        for k, n in recipe.items():
            sim.stock[k] -= n
        c["reserved"] = {}
        s.update(state="cooking", dish=c["dish"], customer_id=c["id"], ready_ticks=0,
                 cook_ticks_left=int(round(sim.menu[c["dish"]]["cook_s"] * TICK)))
        events.append(("cook_started", {"stove_id": s["id"], "dish": c["dish"], "customer_id": c["id"]}))
        return


def _use_table(sim, tb, events):
    if sim.hand is None:
        return
    for c in sim.customers:
        if c["table_id"] == tb["id"] and c["state"] == "waiting" and c["dish"] == sim.hand:
            c["state"], c["eat_ticks"] = "eating", int(round(sim.t["eat_s"] * TICK))
            events.append(("served", {"customer_id": c["id"], "table_id": tb["id"], "dish": sim.hand}))
            sim.hand = None
            return
