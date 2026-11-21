"""Quán lát 4 (@minhthu27) — bếp, bưng, phục vụ, tiền, boa, uy tín. Lát này giữ luôn `quan.py`.

Theo schema khách trong docs/contracts/customer.md (bản của @viethoang126, theo PRD-0 D/E/F):
`dish_id`, `order_tick`, `state` (waiting|eating), `patience_ticks_left`, `eat_ticks_left`,
`order_status` (reserved|assigned|unfulfillable|served), `reserved`, `base_price`, `tip`.

Thứ tự một bước (quan.py gọi):  1 `tick_service` (bếp nấu, khách ăn)  ->  2 `interact`  ->
3 `settle` (khách ăn xong trả tiền, rời bàn)  ->  hết ca: `settle(closing=True)`.
Phần kiên nhẫn / rời đi / khách mới là của lát 3 (KHÔNG giảm `eat_ticks_left` ở lát 3, đã làm ở đây).

`stock` là tồn vật lý gồm cả phần giữ chỗ: khi bếp nhận đơn, nguyên liệu bị trừ khỏi kho và `reserved` về {}.
Bếp nhớ đơn của mình bằng khóa nội bộ `order_id` (không xuất ra snapshot). Món trên tay `hand` là
`{order_id, dish_id, base_price}`.
"""

import math

from ..ids import id_key

TICK = 60


def _clamp_rep(sim, v):
    return max(sim.t["reputation_min"], min(sim.t["reputation_max"], v))


# --- bước 1: bếp nấu, khách ăn ----------------------------------------------------------
def tick_service(sim, events):
    drop_orphans(sim)
    for s in sim.stoves:  # theo id (sim.stoves đã sắp)
        if s["state"] == "cooking":
            s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
            if s["cook_ticks_left"] == 0:
                s["state"], s["ready_ticks"] = "ready", 0
                events.append(("dish_ready", {"stove_id": s["id"], "dish": s["dish"]}))
        elif s["state"] == "ready":
            s["ready_ticks"] += 1  # burn_s = null: không cháy
    for c in sim.customers:
        if c["state"] == "eating":
            c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)


def drop_orphans(sim):
    """Khách đã rời: bỏ món đang nấu / ready / trên tay của đơn đó (nguyên liệu đã dùng không hoàn lại)."""
    ids = {c["id"] for c in sim.customers}
    for s in sim.stoves:
        if s.get("order_id") and s["order_id"] not in ids:
            _reset_stove(s)
    if isinstance(sim.hand, dict) and sim.hand.get("order_id") not in ids:
        sim.hand = None


def _reset_stove(s):
    s["state"], s["dish"], s["cook_ticks_left"], s["ready_ticks"] = "idle", None, 0, 0
    s.pop("order_id", None)


# --- bước 3: trả tiền ---------------------------------------------------------------------
def settle(sim, events, closing=False):
    """Theo id bàn: khách ăn xong (eat_ticks_left == 0) trả tiền rồi rời bàn. Hết ca: mọi khách đang ăn trả ngay."""
    rank = {tb["id"]: i for i, tb in enumerate(sim.tables)}
    eating = [c for c in sim.customers if c["state"] == "eating" and (closing or c["eat_ticks_left"] <= 0)]
    eating.sort(key=lambda c: rank.get(c["table_id"], 0))
    for c in eating:
        total = c["base_price"] + c["tip"]
        if c["tip"] > 0:
            sim.reputation = _clamp_rep(sim, sim.reputation + sim.t["tip_reputation"])
        sim.money += total
        sim.earned += total
        sim.shift_earned += total
        events.append(("paid", {"customer_id": c["id"], "table_id": c["table_id"], "dish": c["dish_id"],
                                "price": c["base_price"], "tip": c["tip"], "total": total}))
    gone = {c["id"] for c in eating}
    if gone:
        sim.customers = [c for c in sim.customers if c["id"] not in gone]


# --- bước 2: interact ----------------------------------------------------------------------
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
            sim.hand = {"order_id": s.get("order_id"), "dish_id": s["dish"],
                        "base_price": sim.menu[s["dish"]]["price"]}
            events.append(("dish_picked", {"stove_id": s["id"], "dish": s["dish"]}))
            _reset_stove(s)
    elif s["state"] == "idle":
        _start_cooking(sim, s, events)


def _start_cooking(sim, s, events):
    """Nhận đơn `reserved` CŨ NHẤT (order_tick, id) mà kho đủ nguyên liệu."""
    for c in sorted(sim.customers, key=lambda c: (c["order_tick"], id_key(c["id"]))):
        if c["state"] != "waiting" or c["order_status"] != "reserved":
            continue
        recipe = sim.menu[c["dish_id"]]["recipe"]
        if any(sim.stock.get(k, 0) < n for k, n in recipe.items()):
            continue
        for k, n in recipe.items():
            sim.stock[k] -= n
        c["reserved"], c["order_status"] = {}, "assigned"
        s.update(state="cooking", dish=c["dish_id"], order_id=c["id"], ready_ticks=0,
                 cook_ticks_left=int(round(sim.menu[c["dish_id"]]["cook_s"] * TICK)))
        events.append(("cook_started", {"stove_id": s["id"], "dish": c["dish_id"], "customer_id": c["id"]}))
        return


def _use_table(sim, tb, events):
    """Bưng món: khách ngồi bàn này phải là chủ đơn của món trên tay."""
    h = sim.hand
    if not isinstance(h, dict):
        return
    for c in sim.customers:
        if c["table_id"] == tb["id"] and c["state"] == "waiting" and c["id"] == h.get("order_id"):
            tip = 0
            if c["patience_ticks_left"] >= sim.t["tip_min_patience_ratio"] * sim.t["patience_s"] * TICK:
                tip = int(math.floor(h["base_price"] * sim.t["tip_rate"]))
            c.update(state="eating", order_status="served", eat_ticks_left=int(round(sim.t["eat_s"] * TICK)),
                     base_price=h["base_price"], tip=tip)
            events.append(("served", {"customer_id": c["id"], "table_id": tb["id"], "dish": h["dish_id"]}))
            sim.hand = None
            return
