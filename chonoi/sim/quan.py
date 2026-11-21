"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Luật theo PRD-0 mục F, Quán. Thứ tự một bước: timer, bếp chín, di chuyển, tối đa một interact,
khách (trả tiền, rời), sinh khách mới.
  Lát 3: khách đến theo lịch, giữ chỗ nguyên liệu, kiên nhẫn, customer_left, no_dish.
  Lát 4: interact bếp/bàn (cook_started, dish_ready, dish_picked, served), paid, boa, uy tín, hết ca (quan_end).
"""

import math
from fractions import Fraction

from ..freshness import Freshness
from ..ids import id_key, sort_by_id
from ..inventory import counts_to_individuals, inventory_schema
from .ramp import ramp_velocity


class ItemizedStock(list):
    """List of physical items with a count view for the day/shop integration."""

    def items(self):
        counts = {}
        for item in self:
            counts[item["kind"]] = counts.get(item["kind"], 0) + 1
        return counts.items()


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, *, allowed_dishes=None,
                 money=0, earned=0, shift_earned=0, reputation=None, contract_version=None):
        t = tuning["quan"]
        self.t = t
        self.tick_hz = tuning["tick_hz"]
        self.menu = tuning["menu"]
        self.freshness = Freshness(tuning) if "freshness" in tuning else None
        self.allowed_dishes = None if allowed_dishes is None else frozenset(allowed_dishes)
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        source_stock = inventory if inventory is not None else scenario.get("stock", {})
        self.itemized_stock = self.freshness is not None and (
            isinstance(source_stock, list) or inventory_schema(contract_version or "1.1") == "individuals")
        if self.itemized_stock:
            if isinstance(source_stock, dict):
                source_stock = counts_to_individuals(source_stock, fresh=tuning["freshness"]["initial"])
            self.stock = ItemizedStock(sort_by_id([{"id": item["id"], "kind": item["kind"],
                                                     "fresh": self.freshness.to_units(item["fresh"])}
                                                    for item in source_stock]))
        else:
            self.stock = dict(source_stock)
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * self.tick_hz)))
        self.reputation = (reputation if reputation is not None else
                           scenario.get("reputation", t["reputation_initial"]))
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
            if self.itemized_stock:
                customer["reserved"] = self._legacy_reservation_to_ids(reserved)
            else:
                customer["reserved"] = dict(reserved)
            if customer["state"] == "waiting":
                customer.setdefault("patience_ticks_left", int(round(t["patience_s"] * self.tick_hz)))
            self.customers.append(customer)
        for e in self.customers:
            ids.reserve(e["id"])
        self.random_customers = scenario.get("random_customers", True)
        self.sim_tick = 0
        self.phase_tick = 0
        self.money = money
        self.earned = earned
        self.shift_earned = shift_earned
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
        if self.itemized_stock:
            stock = [{"id": item["id"], "kind": item["kind"],
                      "fresh": self.freshness.to_points(item["fresh"])}
                     for item in sort_by_id(self.stock)]
            customers = []
            for customer in sort_by_id(self.customers):
                row = dict(customer)
                row["reserved"] = sorted(customer.get("reserved", []), key=id_key)
                customers.append(row)
        else:
            stock = {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}
            customers = sort_by_id(self.customers)
        return {
            "player": {"pos": self.pos},
            "stock": stock,
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": customers,
        }

    def step(self, inp):
        events = []
        self.sim_tick += 1
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._update_timers()
        if self.itemized_stock:
            self._decay_stock(events)
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

    def _legacy_reservation_to_ids(self, reserved):
        if isinstance(reserved, list):
            return list(reserved)
        already = {item_id for customer in self.customers for item_id in customer.get("reserved", [])}
        result = []
        for kind in sorted(reserved):
            matching = [item for item in self._available_items(already) if item["kind"] == kind]
            matching.sort(key=lambda item: (-item["fresh"], id_key(item["id"])))
            quantity = reserved[kind]
            result.extend(item["id"] for item in matching[:quantity])
            already.update(item["id"] for item in matching[:quantity])
        return result

    def _reserved_ids(self):
        return {item_id for customer in self.customers for item_id in customer.get("reserved", [])}

    def _available_items(self, exclude=()):
        excluded = set(exclude)
        return [item for item in self.stock if item["id"] not in excluded
                and not self.freshness.is_spoiled(item["fresh"])]

    def _reserve_recipe(self, recipe, exclude=()):
        available = self._available_items(exclude)
        chosen = []
        for kind in sorted(recipe):
            candidates = [item for item in available if item["kind"] == kind]
            candidates.sort(key=lambda item: (-item["fresh"], id_key(item["id"])))
            quantity = recipe[kind]
            if len(candidates) < quantity:
                return None
            selected = candidates[:quantity]
            chosen.extend(selected)
            available = [item for item in available if item["id"] not in {x["id"] for x in selected}]
        return [item["id"] for item in chosen]

    def _decay_stock(self, events):
        decay = self.freshness.decay("quan")
        newly_spoiled = []
        for item in sort_by_id(self.stock):
            before = item["fresh"]
            item["fresh"] = max(0, before - decay)
            if before >= self.freshness.spoil_units and self.freshness.is_spoiled(item["fresh"]):
                newly_spoiled.append(item)
        for item in newly_spoiled:
            events.append(("spoiled", {"item_id": item["id"], "kind": item["kind"], "location": "stock"}))

        spoiled_ids = {item["id"] for item in newly_spoiled}
        affected = [customer for customer in self.customers
                    if customer.get("order_status") == "reserved"
                    and spoiled_ids.intersection(customer.get("reserved", []))]
        affected.sort(key=lambda c: (c.get("order_tick", 0), self._table_order(c)))
        for customer in affected:
            recipe = self.menu.get(customer.get("dish_id"), {}).get("recipe", {})
            customer["reserved"] = []
            replacement = self._reserve_recipe(recipe, self._reserved_ids())
            if replacement is None:
                customer["order_status"] = "unfulfillable"
            else:
                customer["reserved"] = replacement

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
            dish_id = customer["dish_id"]
            menu_item = self.menu[dish_id]
            if self.itemized_stock:
                reserved_ids = set(reserved)
                items = sorted((item for item in self.stock if item["id"] in reserved_ids),
                               key=lambda item: (item["kind"], id_key(item["id"])))
                if len(items) != len(reserved_ids) or any(self.freshness.is_spoiled(i["fresh"]) for i in items):
                    return
                base_price = self.freshness.dish_price(menu_item["price"], [item["fresh"] for item in items])
                event_items = [{"id": item["id"], "kind": item["kind"],
                                "fresh": self.freshness.to_points(item["fresh"])} for item in items]
                self.stock = ItemizedStock(item for item in self.stock if item["id"] not in reserved_ids)
                customer["reserved"] = []
            else:
                if any(self.stock.get(kind, 0) < quantity for kind, quantity in reserved.items()):
                    return
                for ingredient, quantity in reserved.items():
                    self.stock[ingredient] -= quantity
                event_items = [ingredient for ingredient in sorted(reserved)
                               for _ in range(reserved[ingredient])]
                base_price = menu_item["price"]
                customer["reserved"] = {}
            customer["order_status"] = "assigned"
            stove.update({
                "state": "cooking",
                "dish": {"order_id": customer["id"], "dish_id": dish_id, "base_price": base_price},
                "cook_ticks_left": int(round(menu_item["cook_s"] * self.tick_hz)),
                "ready_ticks": 0,
            })
            events.append(("cook_started", {
                "stove_id": stove["id"], "order_id": customer["id"], "dish_id": dish_id,
                "items": event_items, "base_price": base_price,
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

        if self.itemized_stock:
            reserved_ids = self._reserved_ids()
            available = {}
            for item in self._available_items(reserved_ids):
                available[item["kind"]] = available.get(item["kind"], 0) + 1
        else:
            available = dict(self.stock)
            for customer in self.customers:
                for ingredient, amount in customer.get("reserved", {}).items():
                    available[ingredient] = available.get(ingredient, 0) - amount
        dishes = []
        for dish_id in sorted(self.menu):
            if self.allowed_dishes is not None and dish_id not in self.allowed_dishes:
                continue
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
        if self.itemized_stock:
            reserved = self._reserve_recipe(recipe, self._reserved_ids())
            if reserved is None:
                events.append(("no_dish", {}))
                return
            recipe = reserved
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
