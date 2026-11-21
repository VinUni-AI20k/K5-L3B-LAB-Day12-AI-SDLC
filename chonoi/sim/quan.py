"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Lát 4 (Người 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                 ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
Lát 3 (Người 3): cung cấp quan_customers.py (load_customers, tick_customers,
                 oldest_reserved, leave_waiting, spawn_customer).
"""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

try:
    from .quan_customers import (load_customers, tick_customers,
                                  oldest_reserved, leave_waiting, spawn_customer)
except ImportError:
    # Fallback stubs khi lát 3 chưa gộp nhánh
    def load_customers(sim, scenario):
        return [dict(c, reserved=c.get("reserved", {})) for c in scenario.get("customers", [])]

    def tick_customers(sim):
        for c in sim.customers:
            if c.get("state") == "waiting":
                c["patience_ticks_left"] = max(0, c.get("patience_ticks_left", 0) - 1)
            elif c.get("state") == "eating":
                c["eat_ticks_left"] = max(0, c.get("eat_ticks_left", 0) - 1)

    def oldest_reserved(sim):
        candidates = [c for c in sim.customers if c.get("order_status") == "reserved" or c.get("reserved")]
        if not candidates:
            return None
        candidates.sort(key=lambda c: (c.get("order_tick", 0), id_key(c.get("table_id", ""))))
        return candidates[0]

    def leave_waiting(sim, customer, reason, events):
        if reason == "patience":
            delta = sim.t.get("left_reputation_delta", -0.5)
            sim.reputation = max(sim.t.get("reputation_min", 0.0), sim.reputation + delta)
        events.append(("customer_left", {
            "order_id": customer["id"],
            "table_id": customer["table_id"],
            "reason": reason,
            "reputation": sim.reputation
        }))
        customer["reserved"] = {}
        if customer in sim.customers:
            sim.customers.remove(customer)

    def spawn_customer(sim, phase_tick, events):
        pass

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
        self.phase_tick = 0
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.random_customers = scenario.get("random_customers", True)
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = load_customers(self, scenario)
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
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in sort_by_id(self.stoves)],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in sort_by_id(self.tables)],
            "customers": sort_by_id(self.customers),
        }

    def _clean_order_items(self, order_id):
        if self.hand and self.hand.get("order_id") == order_id:
            self.hand = None
        for s in self.stoves:
            if s.get("dish") and s["dish"].get("order_id") == order_id:
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # 1. Tăng đồng hồ, giảm timer ca, nấu, ăn và kiên nhẫn. Chỉ tăng ready_ticks cho món đã ready ở đầu bước.
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] = s.get("ready_ticks", 0) + 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s.get("cook_ticks_left", 0) - 1)

        tick_customers(self)

        # 2. Xét bếp theo id. Món nấu xong chuyển ready với ready_ticks = 0.
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                dish = s["dish"]
                events.append(("dish_ready", {
                    "stove_id": s["id"],
                    "order_id": dish["order_id"],
                    "dish_id": dish["dish_id"]
                }))

        # 3. Di chuyển rồi xét tối đa một interact
        self._move(inp)
        if inp.pressed("interact"):
            self._handle_interact(events)

        # 4. Theo id bàn, khách ăn xong trả tiền rồi rời bàn ngay
        sorted_tables = sort_by_id(self.tables)
        if self.time_left_ticks > 0:
            for tb in sorted_tables:
                c = next((cust for cust in list(self.customers) if cust["table_id"] == tb["id"]), None)
                if not c:
                    continue
                if c.get("state") == "eating" and c.get("eat_ticks_left", 0) == 0:
                    base_price = c.get("base_price", 0)
                    tip = c.get("tip", 0)
                    amount = base_price + tip
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    if tip > 0:
                        self.reputation = min(self.t["reputation_max"], self.reputation + self.t["tip_reputation"])
                    events.append(("paid", {
                        "order_id": c["id"],
                        "table_id": tb["id"],
                        "base_price": base_price,
                        "tip": tip,
                        "amount": amount,
                        "reason": "finished_eating"
                    }))
                    self.customers.remove(c)
                elif c.get("state") == "waiting" and c.get("patience_ticks_left", 0) == 0:
                    self._clean_order_items(c["id"])
                    leave_waiting(self, c, "patience", events)
        else:
            # Hết ca: khách còn ăn trả ngay, khách còn chờ rời với closing và không trừ uy tín
            for tb in sorted_tables:
                c = next((cust for cust in list(self.customers) if cust["table_id"] == tb["id"]), None)
                if not c:
                    continue
                if c.get("state") == "eating":
                    base_price = c.get("base_price", 0)
                    tip = c.get("tip", 0)
                    amount = base_price + tip
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    if tip > 0:
                        self.reputation = min(self.t["reputation_max"], self.reputation + self.t["tip_reputation"])
                    events.append(("paid", {
                        "order_id": c["id"],
                        "table_id": tb["id"],
                        "base_price": base_price,
                        "tip": tip,
                        "amount": amount,
                        "reason": "closing"
                    }))
                    self.customers.remove(c)
                elif c.get("state") == "waiting":
                    self._clean_order_items(c["id"])
                    leave_waiting(self, c, "closing", events)

            self.done = True
            self.reason = "time"
            events.append(("quan_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation
            }))

        # 5. Khách mới theo lịch nếu chưa đóng ca
        if not self.done:
            spawn_customer(self, self.phase_tick, events)

        return events

    def _handle_interact(self, events):
        r = self.t["interact_radius"]
        candidates = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r:
                candidates.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r:
                candidates.append((d, 1, id_key(tb["id"]), "table", tb))

        if not candidates:
            return

        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        best = candidates[0]
        kind, obj = best[3], best[4]

        if kind == "stove":
            s = obj
            if s["state"] == "idle":
                c = oldest_reserved(self)
                if c is not None:
                    dish_id = c["dish_id"]
                    recipe = self.menu[dish_id]["recipe"]
                    cook_s = self.menu[dish_id]["cook_s"]
                    price = self.menu[dish_id]["price"]

                    for k, amt in recipe.items():
                        self.stock[k] = self.stock.get(k, 0) - amt

                    c["reserved"] = {}
                    c["order_status"] = "assigned"

                    s["state"] = "cooking"
                    s["cook_ticks_left"] = int(round(cook_s * TICK))
                    s["ready_ticks"] = 0
                    s["dish"] = {
                        "order_id": c["id"],
                        "dish_id": dish_id,
                        "base_price": price
                    }

                    items = []
                    for k, cnt in recipe.items():
                        items.extend([k] * cnt)
                    items.sort()

                    events.append(("cook_started", {
                        "stove_id": s["id"],
                        "order_id": c["id"],
                        "dish_id": dish_id,
                        "items": items,
                        "base_price": price
                    }))
            elif s["state"] == "ready":
                if self.hand is None:
                    self.hand = s["dish"]
                    events.append(("dish_picked", {
                        "stove_id": s["id"],
                        "order_id": self.hand["order_id"],
                        "dish_id": self.hand["dish_id"]
                    }))
                    s["state"] = "idle"
                    s["dish"] = None
                    s["ready_ticks"] = 0

        elif kind == "table":
            tb = obj
            c = next((cust for cust in self.customers if cust["table_id"] == tb["id"]), None)
            if c is not None and self.hand is not None and self.hand.get("order_id") == c["id"]:
                order_id = c["id"]
                dish_id = c["dish_id"]
                base_price = self.hand["base_price"]
                patience_left = c.get("patience_ticks_left", 0)
                total_patience = int(round(self.t["patience_s"] * TICK))
                ratio = patience_left / total_patience if total_patience > 0 else 0.0

                if ratio >= self.t["tip_min_patience_ratio"]:
                    tip = math.floor(base_price * self.t["tip_rate"])
                else:
                    tip = 0

                c["state"] = "eating"
                c["order_status"] = "served"
                c["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
                c["base_price"] = base_price
                c["tip"] = tip
                self.hand = None

                events.append(("served", {
                    "order_id": order_id,
                    "table_id": tb["id"],
                    "dish_id": dish_id,
                    "patience_ticks_left": patience_left,
                    "base_price": base_price,
                    "tip": tip
                }))

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
