"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

import math

from ..ids import sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        # TODO(nhóm): khách dựng sẵn từ scenario (customers[]) và suy ra giữ chỗ (reserved).
        self.customers = [dict(c, reserved=c.get("reserved", {})) for c in scenario.get("customers", [])]
        for c in self.customers:
            c.setdefault("state", "waiting")
            p_ticks = int(round(t["patience_s"] * TICK))
            c.setdefault("patience_ticks", p_ticks)
            c.setdefault("patience_max_ticks", p_ticks)
            if c["state"] == "eating":
                c.setdefault("eat_ticks_left", int(round(t["eat_s"] * TICK)))
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        # 1. Bếp nấu (Lát 4)
        self._tick_stoves(events)
        # 2. Khách ăn xong & thanh toán (Lát 4)
        self._tick_customers_eating(events)
        # TODO(nhóm, lát 3): giảm kiên nhẫn; xử lý khách theo thứ tự PRD-0 mục F.
        self._move(inp)
        # 3. Tương tác Bếp & Bàn (Lát 4)
        self._interact(inp, events)
        # TODO(nhóm, lát 3): khách mới theo lịch (first_customer_tick, customer_interval_s), no_dish.
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _tick_stoves(self, events):
        """Lát 4: Bếp nấu, giảm cook_ticks_left, chuyển sang ready, bắn dish_ready."""
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking":
                s["cook_ticks_left"] -= 1
                if s["cook_ticks_left"] <= 0:
                    s["state"] = "ready"
                    s["cook_ticks_left"] = 0
                    s["ready_ticks"] = 0
                    events.append(("dish_ready", {"stove_id": s["id"], "dish": s["dish"]}))
            elif s["state"] == "ready":
                s["ready_ticks"] = s.get("ready_ticks", 0) + 1

    def _tick_customers_eating(self, events):
        """Lát 4: Khách ăn xong trả tiền, tính boa, cộng uy tín, bắn paid."""
        to_remove = []
        for c in sort_by_id(self.customers):
            if c.get("state") == "eating":
                c["eat_ticks_left"] = c.get("eat_ticks_left", 0) - 1
                if c["eat_ticks_left"] <= 0:
                    dish = c["order"]
                    price = self.menu[dish]["price"]
                    ratio = c.get("patience_ratio_served", 1.0)
                    tip = 0
                    if ratio >= self.t["tip_min_patience_ratio"]:
                        tip = int(round(price * self.t["tip_rate"]))
                        self.reputation = min(self.t["reputation_max"],
                                              round(self.reputation + self.t["tip_reputation"], 3))
                    self.money += price + tip
                    self.earned += price + tip
                    self.shift_earned += price + tip
                    events.append(("paid", {"customer_id": c["id"], "dish": dish,
                                            "money": price, "tip": tip, "reputation": self.reputation}))
                    to_remove.append(c)
        for c in to_remove:
            self.customers.remove(c)

    def _interact(self, inp, events):
        """Lát 4: Tương tác tại bếp (cook_started, dish_picked) hoặc bàn (served).
        Tối đa một tương tác, chọn đối tượng gần nhất trong interact_radius,
        nếu cùng khoảng cách: bếp trước bàn, rồi theo id.
        """
        if not inp.pressed("interact"):
            return

        radius = self.t["interact_radius"]
        candidates = []
        for s in self.stoves:
            d = math.hypot(self.pos[0] - s["pos"][0], self.pos[1] - s["pos"][1])
            if d <= radius:
                candidates.append((d, 0, s["id"], "stove", s))
        for tb in self.tables:
            d = math.hypot(self.pos[0] - tb["pos"][0], self.pos[1] - tb["pos"][1])
            if d <= radius:
                candidates.append((d, 1, tb["id"], "table", tb))

        if not candidates:
            return

        candidates.sort(key=lambda item: (round(item[0], 5), item[1], item[2]))
        _, _, _, kind, target = candidates[0]

        if kind == "stove":
            self._interact_stove(target, events)
        elif kind == "table":
            self._interact_table(target, events)

    def _choose_dish_to_cook(self):
        in_progress = [st["dish"] for st in self.stoves if st["dish"]]
        if self.hand:
            in_progress.append(self.hand)

        for c in sort_by_id(self.customers):
            if c.get("state") == "waiting":
                order = c.get("order")
                if order and order in self.menu:
                    if order in in_progress:
                        in_progress.remove(order)
                    else:
                        recipe = self.menu[order]["recipe"]
                        if all(self.stock.get(ing, 0) >= qty for ing, qty in recipe.items()):
                            return order

        for dish_id, info in self.menu.items():
            recipe = info["recipe"]
            if all(self.stock.get(ing, 0) >= qty for ing, qty in recipe.items()):
                return dish_id
        return None

    def _interact_stove(self, s, events):
        if s["state"] == "ready":
            if self.hand is None:
                dish = s["dish"]
                self.hand = dish
                s["state"] = "idle"
                s["dish"] = None
                s["ready_ticks"] = 0
                events.append(("dish_picked", {"stove_id": s["id"], "dish": dish}))
        elif s["state"] == "idle":
            if self.hand is None:
                dish = self._choose_dish_to_cook()
                if dish:
                    recipe = self.menu[dish]["recipe"]
                    for ing, qty in recipe.items():
                        self.stock[ing] = self.stock.get(ing, 0) - qty
                    s["state"] = "cooking"
                    s["dish"] = dish
                    s["cook_ticks_left"] = int(round(self.menu[dish]["cook_s"] * TICK))
                    s["ready_ticks"] = 0
                    events.append(("cook_started", {"stove_id": s["id"], "dish": dish}))

    def _interact_table(self, tb, events):
        if not self.hand:
            return
        c = next((cust for cust in self.customers if cust.get("table_id") == tb["id"]), None)
        if c and c.get("state") == "waiting":
            if self.hand == c.get("order"):
                dish = self.hand
                self.hand = None
                c["state"] = "eating"
                c["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
                p_left = c.get("patience_ticks", int(round(self.t["patience_s"] * TICK)))
                p_max = c.get("patience_max_ticks", int(round(self.t["patience_s"] * TICK)))
                c["patience_ratio_served"] = p_left / p_max if p_max > 0 else 1.0
                events.append(("served", {"customer_id": c["id"], "table_id": tb["id"], "dish": dish}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
