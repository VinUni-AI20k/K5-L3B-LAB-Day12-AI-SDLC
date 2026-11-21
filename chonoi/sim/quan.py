"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Luật theo PRD-0 mục F, Quán. Thứ tự một bước: timer, bếp chín, di chuyển, tối đa một interact,
khách (trả tiền, rời), sinh khách mới.
  Lát 3: khách đến theo lịch, giữ chỗ nguyên liệu, kiên nhẫn, customer_left, no_dish.
  Lát 4: interact bếp/bàn (cook_started, dish_ready, dish_picked, served), paid, boa, uy tín, hết ca (quan_end).
"""

import math
from fractions import Fraction

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.tick_hz = tuning["tick_hz"]
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
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * self.tick_hz)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = []
        for c in scenario.get("customers", []):
            customer = dict(c)
            # PRD-0 mục D: khách mặc định waiting, order_tick 0, order_status reserved, kiên nhẫn đầy.
            customer.setdefault("state", "waiting")
            customer.setdefault("order_tick", 0)
            customer.setdefault("order_status", "reserved")
            customer.setdefault("eat_ticks_left", 0)
            reserved = customer.get("reserved")
            if reserved is None:
                dish = self.menu.get(customer.get("dish_id"), {})
                reserved = dish.get("recipe", {}) if customer["order_status"] == "reserved" else {}
            customer["reserved"] = dict(reserved)
            if customer["state"] == "waiting":
                customer.setdefault("patience_ticks_left", int(round(t["patience_s"] * self.tick_hz)))
            self.customers.append(customer)
        for e in self.customers:
            ids.reserve(e["id"])
        self.random_customers = scenario.get("random_customers", True)
        self.sim_tick = 0
        self.phase_tick = 0
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None
        self.end_reason = None
        self.state = "playing"

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
        self.sim_tick += 1
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._update_timers()
        self._complete_stoves(events)
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        self._settle_customers(events)
        if self.time_left_ticks > 0:
            self._spawn_customer(events)
        return events

    @staticmethod
    def _decrement(obj, key):
        if key in obj:
            obj[key] = max(0, obj[key] - 1)

    def _update_timers(self):
        for stove in self.stoves:
            if stove.get("state") == "cooking":
                self._decrement(stove, "cook_ticks_left")
            elif stove.get("state") == "ready":
                # Only stoves already ready at the start of this step accumulate ready time.
                stove["ready_ticks"] = max(0, stove.get("ready_ticks", 0)) + 1
        for customer in self.customers:
            if customer.get("state") == "waiting":
                self._decrement(customer, "patience_ticks_left")
            elif customer.get("state") == "eating":
                self._decrement(customer, "eat_ticks_left")

    @staticmethod
    def _table_order(customer):
        return id_key(customer["table_id"])

    def _complete_stoves(self, events):
        for stove in sort_by_id(self.stoves):
            if stove.get("state") != "cooking" or stove.get("cook_ticks_left", 0) != 0:
                continue
            stove["state"] = "ready"
            stove["ready_ticks"] = 0
            dish = stove.get("dish")
            if not isinstance(dish, dict):
                dish = {}
            events.append(("dish_ready", {
                "stove_id": stove["id"], "order_id": dish.get("order_id"),
                "dish_id": dish.get("dish_id"),
            }))

    def _interact(self, events):
        radius = self.t["interact_radius"]
        candidates = []
        for stove in self.stoves:
            distance = math.dist(self.pos, stove["pos"])
            if distance <= radius:
                candidates.append((distance, 0, id_key(stove["id"]), "stove", stove))
        occupied = {customer["table_id"]: customer for customer in self.customers}
        for table in self.tables:
            distance = math.dist(self.pos, table["pos"])
            if distance <= radius:
                candidates.append((distance, 1, id_key(table["id"]), "table", (table, occupied.get(table["id"]))))
        if not candidates:
            return
        _, _, _, kind, target = min(candidates, key=lambda c: c[:3])
        if kind == "stove":
            self._interact_stove(target, events)
        elif target[1] is not None:
            self._interact_table(target[0], target[1], events)

    def _interact_stove(self, stove, events):
        state = stove.get("state")
        if state == "idle":
            orders = [c for c in self.customers
                      if c.get("state") == "waiting" and c.get("order_status") == "reserved"
                      and c.get("dish_id") in self.menu]  # đơn không rõ món thì không nấu được
            orders.sort(key=lambda c: (c.get("order_tick", 0), self._table_order(c)))
            if not orders:
                return
            customer = orders[0]
            reserved = customer.get("reserved", {})
            if any(self.stock.get(kind, 0) < quantity for kind, quantity in reserved.items()):
                return
            dish_id = customer["dish_id"]
            menu_item = self.menu[dish_id]
            for ingredient, quantity in reserved.items():
                self.stock[ingredient] -= quantity
            customer["reserved"] = {}
            customer["order_status"] = "assigned"
            base_price = menu_item["price"]
            stove.update({
                "state": "cooking",
                "dish": {"order_id": customer["id"], "dish_id": dish_id, "base_price": base_price},
                "cook_ticks_left": int(round(menu_item["cook_s"] * self.tick_hz)),
                "ready_ticks": 0,
            })
            items = [ingredient for ingredient in sorted(reserved)
                     for _ in range(reserved[ingredient])]
            events.append(("cook_started", {
                "stove_id": stove["id"], "order_id": customer["id"], "dish_id": dish_id,
                "items": items, "base_price": base_price,
            }))
        elif state == "ready" and self.hand is None and self.t["carry_limit"] > 0:
            dish = stove.get("dish")
            if not isinstance(dish, dict):
                return
            self.hand = dish
            stove.update({"state": "idle", "dish": None, "cook_ticks_left": 0, "ready_ticks": 0})
            events.append(("dish_picked", {
                "stove_id": stove["id"], "order_id": dish["order_id"], "dish_id": dish["dish_id"],
            }))

    def _interact_table(self, table, customer, events):
        if customer.get("state") != "waiting" or not isinstance(self.hand, dict):
            return
        if self.hand.get("order_id") != customer["id"]:
            return
        dish = self.hand
        self.hand = None
        patience_left = customer.get("patience_ticks_left", 0)
        full_patience = int(round(self.t["patience_s"] * self.tick_hz))
        base_price = dish["base_price"]
        # Tính chính xác (không dùng số thực nhị phân) để floor và so ngưỡng không lệch 1 đơn vị.
        enough_patience = Fraction(patience_left, full_patience) >= Fraction(str(self.t["tip_min_patience_ratio"]))
        tip = math.floor(base_price * Fraction(str(self.t["tip_rate"]))) if enough_patience else 0
        customer.update({
            "state": "eating", "order_status": "served",
            "eat_ticks_left": int(round(self.t["eat_s"] * self.tick_hz)),
            "dish_id": dish["dish_id"], "base_price": base_price, "tip": tip,
        })
        events.append(("served", {
            "order_id": customer["id"], "table_id": table["id"], "dish_id": dish["dish_id"],
            "patience_ticks_left": patience_left, "base_price": base_price, "tip": tip,
        }))

    def _release_order(self, order_id):
        for stove in self.stoves:
            dish = stove.get("dish")
            if isinstance(dish, dict) and dish.get("order_id") == order_id:
                stove.update({"state": "idle", "dish": None, "cook_ticks_left": 0, "ready_ticks": 0})
        if isinstance(self.hand, dict) and self.hand.get("order_id") == order_id:
            self.hand = None

    def _apply_tip_reputation(self, tip):
        if tip > 0:
            self.reputation = min(self.t["reputation_max"], max(
                self.t["reputation_min"], self.reputation + self.t["tip_reputation"]))

    def _pay_customer(self, customer, reason, events):
        base_price = customer.get("base_price", 0)
        tip = customer.get("tip", 0)
        amount = base_price + tip
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        self._apply_tip_reputation(tip)
        events.append(("paid", {
            "order_id": customer["id"], "table_id": customer["table_id"],
            "base_price": base_price, "tip": tip, "amount": amount, "reason": reason,
        }))
        self.customers.remove(customer)

    def _leave_customer(self, customer, reason, events, penalize=False):
        self._release_order(customer["id"])
        if penalize:
            self.reputation = min(self.t["reputation_max"], max(
                self.t["reputation_min"], self.reputation + self.t["left_reputation_delta"]))
        self.customers.remove(customer)
        events.append(("customer_left", {
            "order_id": customer["id"], "table_id": customer["table_id"],
            "reason": reason, "reputation": self.reputation,
        }))

    def _settle_customers(self, events):
        ordered = sort_by_id(self.customers, key=lambda c: c["table_id"])
        if self.time_left_ticks == 0:
            for customer in ordered:
                if customer not in self.customers:
                    continue
                if customer.get("state") == "eating":
                    self._pay_customer(customer, "closing", events)
                else:
                    self._leave_customer(customer, "closing", events)
            self.done = True
            self.reason = self.end_reason = "time"
            self.state = "finished"
            events.append(("quan_end", {
                "reason": "time", "money": self.money, "earned": self.earned,
                "shift_earned": self.shift_earned, "reputation": self.reputation,
            }))
            return

        for customer in ordered:
            if customer.get("state") == "eating" and customer.get("eat_ticks_left") == 0:
                self._pay_customer(customer, "finished_eating", events)
            elif customer.get("state") == "waiting" and customer.get("patience_ticks_left") == 0:
                self._leave_customer(customer, "patience", events, penalize=True)

    def _spawn_customer(self, events):
        interval = int(round(self.t["customer_interval_s"] * self.tick_hz))
        first = self.t["first_customer_tick"]
        if not self.random_customers or self.phase_tick < first or (self.phase_tick - first) % interval != 0:
            return
        occupied = {customer["table_id"] for customer in self.customers}
        free_tables = sort_by_id([table for table in self.tables if table["id"] not in occupied])
        if not free_tables:
            return

        available = dict(self.stock)
        for customer in self.customers:
            for ingredient, amount in customer.get("reserved", {}).items():
                available[ingredient] = available.get(ingredient, 0) - amount
        dishes = []
        for dish_id in sorted(self.menu):
            recipe = self.menu[dish_id]["recipe"]
            if all(available.get(ingredient, 0) >= amount for ingredient, amount in recipe.items()):
                dishes.append(dish_id)
        if not dishes:
            events.append(("no_dish", {}))
            return

        dish_id = self.rng.get("quan_customer_dish").choice(dishes)
        table = free_tables[0]
        customer_id = self.ids.new("C")
        recipe = dict(self.menu[dish_id]["recipe"])
        customer = {
            "id": customer_id,
            "table_id": table["id"],
            "state": "waiting",
            "order_status": "reserved",
            "order_tick": self.phase_tick,
            "dish_id": dish_id,
            "patience_ticks_left": int(round(self.t["patience_s"] * self.tick_hz)),
            "eat_ticks_left": 0,
            "reserved": recipe,
        }
        self.customers.append(customer)
        events.append(("customer_arrived", {
            "order_id": customer_id, "table_id": table["id"], "dish_id": dish_id,
        }))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / self.tick_hz
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
