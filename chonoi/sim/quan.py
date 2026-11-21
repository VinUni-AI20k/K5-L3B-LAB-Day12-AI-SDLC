"""Buổi tối — Mở Quán (PRD-0 mục F)."""

import math
from fractions import Fraction

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items, item_out, items_out
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, day_plan=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        freshness = tuning["freshness"]
        self.spoiled_below = Fraction(str(freshness["spoiled_below"]))
        self.stock_decay = Fraction(str(freshness["quan_decay_per_s"])) / int(TICK)
        self.allowed_dishes = set(day_plan["dishes"]) if day_plan is not None else None
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # Kho cá thể v1.2: --inventory HOẶC scenario.stock.
        raw_stock = inventory if inventory is not None else scenario.get("stock", [])
        self.stock = [dict(it) for it in raw_stock] if isinstance(raw_stock, list) else dict(raw_stock)
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self.random_reservations = scenario.get("random_reservations", True)
        patience_ticks = int(round(t["patience_s"] * TICK))
        self.customers = []
        missing_reservations = set()
        for source in scenario.get("customers", []):
            customer = dict(source)
            customer.setdefault("state", "waiting")
            customer.setdefault("order_tick", 0)
            customer.setdefault("patience_ticks_left", patience_ticks)
            customer.setdefault("order_status", "reserved")
            if "reserved" not in customer:
                missing_reservations.add(customer["id"])
            customer.setdefault("reserved", {})
            self.customers.append(customer)
        if isinstance(self.stock, list):
            stock_by_id = {item["id"]: item for item in self.stock}
            seen_reserved_ids = set()
            for customer in self.customers:
                reserved = customer.get("reserved")
                if customer.get("order_status") != "reserved" or not isinstance(reserved, list):
                    continue
                if len(reserved) != len(set(reserved)) or seen_reserved_ids.intersection(reserved):
                    raise BadInput("customers.reserved không được dùng chung id cá thể")
                if any(iid not in stock_by_id for iid in reserved):
                    raise BadInput(f"customers.{customer['id']}.reserved phải trỏ tới id trong kho")
                items = [stock_by_id[iid] for iid in reserved]
                recipe_counts = {}
                for item in items:
                    if item["fresh"] < self.spoiled_below:
                        raise BadInput(f"customers.{customer['id']}.reserved không được giữ hàng đã ươn")
                    recipe_counts[item["kind"]] = recipe_counts.get(item["kind"], 0) + 1
                if recipe_counts != self.menu[customer["dish_id"]]["recipe"]:
                    raise BadInput(f"customers.{customer['id']}.reserved phải khớp đúng công thức")
                seen_reserved_ids.update(reserved)
        # Rebuild omitted fixture reservations in the contract's stable order.
        for customer in sorted(self.customers, key=lambda c: (
                c["order_tick"], id_key(c["table_id"]), id_key(c["id"]))):
            if customer["id"] in missing_reservations and customer["order_status"] == "reserved":
                recipe = self.menu.get(customer.get("dish_id"), {}).get("recipe", {})
                customer["reserved"] = dict(recipe)
        for e in self.customers:
            ids.reserve(e["id"])
        if isinstance(self.stock, list):
            for customer in sorted(self.customers, key=lambda c: (
                    c.get("order_tick", 0), id_key(c.get("table_id", "")), id_key(c["id"]))):
                if customer.get("order_status") == "reserved" and isinstance(customer.get("reserved"), dict):
                    selected = self._select_items(customer["reserved"])
                    if selected is None:
                        raise BadInput(f"customers.{customer['id']}.reserved vượt kho khả dụng")
                    customer["reserved"] = [it["id"] for it in selected]
        self.reservations = self._make_reservations(scenario)
        self._refresh_reservation_holds()
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
        table_reservations = {r["table_id"]: r["id"] for r in self.reservations
                              if r["state"] in ("holding", "waiting")}
        if isinstance(self.stock, list):
            stock_snap = items_out(self.stock)
        else:
            stock_snap = {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}
        return {
            "player": {"pos": self.pos},
            "stock": stock_snap,
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"]),
                        "reservation_id": table_reservations.get(tb["id"])} for tb in self.tables],
            "customers": [dict(c, reservation_id=c.get("reservation_id")) for c in sort_by_id(self.customers)],
            "reservations": [dict(r) for r in sorted(self.reservations, key=lambda r: id_key(r["id"]))],
        }

    def _make_reservations(self, scenario):
        fixtures = scenario.get("reservations")
        if fixtures is not None:
            result = [dict(r, state="scheduled") for r in fixtures]
        elif not self.random_reservations or not self.t["reservations"]["count"]:
            result = []
        else:
            cfg = self.t["reservations"]
            rng = self.rng.get("quan_reservation_arrival")
            dish_rng = self.rng.get("quan_reservation_dish")
            tables = sort_by_id(self.tables)
            dishes = sorted(self.allowed_dishes if self.allowed_dishes is not None else self.menu)
            result = []
            for index in range(cfg["count"]):
                table = tables[index]
                result.append({"id": self.ids.new("R"), "table_id": table["id"],
                               "dish_id": dish_rng.choice(dishes),
                               "arrival_tick": rng.randint(1800, 10799), "state": "scheduled"})
            result.sort(key=lambda r: (r["arrival_tick"], id_key(r["id"])))
        for reservation in result:
            self.ids.reserve(reservation["id"])
            reservation.setdefault("state", "scheduled")
            reservation["hold_tick"] = max(
                0, reservation["arrival_tick"] - int(round(self.t["reservations"]["table_hold_s"] * TICK)))
        return result

    def _refresh_reservation_holds(self):
        for reservation in self.reservations:
            if reservation["state"] == "scheduled" and self.phase_tick >= reservation["hold_tick"]:
                reservation["state"] = "holding"

    def _fail_reservation(self, reservation, reason, events, customer=None):
        if reservation["state"] in ("served", "failed"):
            return
        reservation["state"] = "failed"
        reservation["reason"] = reason
        if customer is not None:
            self._discard_customer_dish(customer)
            if customer in self.customers:
                self.customers.remove(customer)
        cfg = self.t["reservations"]
        self.reputation = min(self.t["reputation_max"], max(
            self.t["reputation_min"], self.reputation + cfg["failed_reputation_delta"]))
        events.append(("reservation_failed", {"reservation_id": reservation["id"],
                                               "order_id": customer["id"] if customer else None,
                                               "table_id": reservation["table_id"],
                                               "reason": reason, "reputation": self.reputation}))

    def _process_reservation_arrivals(self, events):
        self._refresh_reservation_holds()
        occupied = {customer["table_id"] for customer in self.customers}
        for reservation in sorted(self.reservations, key=lambda r: id_key(r["id"])):
            if reservation["state"] != "holding" or reservation["arrival_tick"] != self.phase_tick:
                continue
            if reservation["table_id"] in occupied:
                self._fail_reservation(reservation, "occupied", events)
                continue
            recipe = self.menu[reservation["dish_id"]]["recipe"]
            selected = self._select_items(recipe)
            if selected is None:
                self._fail_reservation(reservation, "stock", events)
                continue
            customer_id = self.ids.new("C")
            customer = {"id": customer_id, "reservation_id": reservation["id"],
                        "table_id": reservation["table_id"], "dish_id": reservation["dish_id"],
                        "order_tick": self.phase_tick, "state": "waiting",
                        "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
                        "eat_ticks_left": 0, "order_status": "reserved",
                        "reserved": [it["id"] for it in selected]}
            self.customers.append(customer)
            occupied.add(customer["table_id"])
            reservation["state"] = "waiting"
            reservation["order_id"] = customer_id
            events.append(("reservation_arrived", {"reservation_id": reservation["id"],
                                                    "order_id": customer_id,
                                                    "table_id": reservation["table_id"],
                                                    "dish_id": reservation["dish_id"]}))
            events.append(("customer_arrived", {"order_id": customer_id,
                                                 "table_id": reservation["table_id"],
                                                 "dish_id": reservation["dish_id"],
                                                 "reservation_id": reservation["id"]}))

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # Timers advance before movement and interaction. Remember which dishes
        # were already ready so newly cooked dishes start at ready_ticks == 0.
        ready_at_start = {s["id"] for s in self.stoves if s["state"] == "ready"}
        if isinstance(self.stock, list):
            for item in sorted(list(self.stock), key=lambda it: id_key(it["id"])):
                item["fresh"] = max(Fraction(0), item["fresh"] - self.stock_decay)
                if item["fresh"] < self.spoiled_below:
                    events.append(("spoiled", {"item_id": item["id"], "kind": item["kind"],
                                                "location": "stock"}))
                    self.stock.remove(item)
            remaining_ids = {item["id"] for item in self.stock}
            for customer in sorted(list(self.customers), key=lambda c: id_key(c["id"])):
                if (customer.get("order_status") == "reserved" and
                        isinstance(customer.get("reserved"), list) and
                        not set(customer["reserved"]) <= remaining_ids):
                    self._customer_left(customer, "stock", events)
        for stove in self.stoves:
            if stove["state"] == "cooking":
                stove["cook_ticks_left"] = max(0, stove["cook_ticks_left"] - 1)
                if stove["cook_ticks_left"] == 0:
                    stove["state"] = "ready"
                    stove["ready_ticks"] = 0
                    dish = stove["dish"]
                    events.append(("dish_ready", {"stove_id": stove["id"],
                                                   "order_id": dish["order_id"],
                                                   "dish_id": dish["dish_id"]}))
            elif stove["state"] == "ready" and stove["id"] in ready_at_start:
                stove["ready_ticks"] += 1
                burn_ticks = self.t.get("burn_s")
                if burn_ticks is not None and stove["ready_ticks"] >= int(round(burn_ticks * TICK)):
                    dish = stove.get("dish") or {}
                    customer = next((c for c in self.customers if c["id"] == dish.get("order_id")), None)
                    events.append(("dish_burnt", {"stove_id": stove["id"],
                                                   "order_id": dish.get("order_id"),
                                                   "dish_id": dish.get("dish_id"),
                                                   "order_status": "failed"}))
                    stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
                    if customer is not None:
                        if customer.get("reservation_id"):
                            reservation = next(r for r in self.reservations
                                               if r["id"] == customer["reservation_id"])
                            self._fail_reservation(reservation, "burnt", events, customer=customer)
                        else:
                            self._customer_left(customer, "burnt", events)
        # Existing eating customers count this tick. Newly served customers do
        # not begin eating until the next tick.
        for customer in sort_by_id(self.customers, key=lambda c: c["table_id"]):
            if customer.get("state") == "eating":
                customer["eat_ticks_left"] = max(0, customer["eat_ticks_left"] - 1)
        for customer in sort_by_id(self.customers):
            if customer.get("state") == "waiting":
                customer["patience_ticks_left"] = max(0, customer["patience_ticks_left"] - 1)
        self._move(inp)

        if inp.pressed("interact"):
            target = self._nearest_interaction()
            if target is not None:
                kind, entity = target
                if kind == "stove":
                    self._interact_stove(entity, events)
                else:
                    self._interact_table(entity, events)

        # Eating ends automatically, after the interaction, in table order.
        for customer in sort_by_id(list(self.customers), key=lambda c: c["table_id"]):
            if customer.get("state") == "eating" and customer["eat_ticks_left"] == 0:
                self._pay_and_leave(customer, "finished_eating", events)

        # Patience is resolved after interaction, so serving at exactly zero is
        # valid. Closing takes precedence over a patience timeout on that tick.
        if self.time_left_ticks > 0:
            for customer in sort_by_id(list(self.customers), key=lambda c: c["table_id"]):
                if customer.get("state") == "waiting" and customer["patience_ticks_left"] == 0:
                    self._customer_left(customer, "patience", events)

        if self.time_left_ticks <= 0:
            for customer in sort_by_id(list(self.customers), key=lambda c: c["table_id"]):
                if customer.get("state") == "eating":
                    self._pay_and_leave(customer, "closing", events)
                else:
                    self._customer_left(customer, "closing", events)
            for reservation in sorted(self.reservations, key=lambda r: id_key(r["id"])):
                if reservation["state"] in ("scheduled", "holding"):
                    self._fail_reservation(reservation, "closing", events)
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events

        self._process_reservation_arrivals(events)
        if self.random_customers:
            first = int(self.t["first_customer_tick"])
            interval = int(round(self.t["customer_interval_s"] * TICK))
            if self.phase_tick >= first and (self.phase_tick - first) % interval == 0:
                self._arrive_customer(events)
        return events

    def _nearest_interaction(self):
        candidates = []
        radius = self.t["interact_radius"]
        for stove in self.stoves:
            distance = math.dist(self.pos, stove["pos"])
            if distance <= radius:
                candidates.append((distance, 0, id_key(stove["id"]), "stove", stove))
        for table in self.tables:
            distance = math.dist(self.pos, table["pos"])
            if distance <= radius:
                candidates.append((distance, 1, id_key(table["id"]), "table", table))
        if not candidates:
            return None
        chosen = min(candidates, key=lambda item: item[:3])
        return chosen[3], chosen[4]

    def _interact_stove(self, stove, events):
        if stove["state"] == "idle":
            orders = [c for c in self.customers if c.get("order_status") == "reserved"]
            if not orders:
                return
            customer = min(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"]), id_key(c["id"])))
            recipe = dict(customer["reserved"]) if isinstance(customer["reserved"], dict) else None
            dish = self.menu[customer["dish_id"]]
            # Reserved stock is consumed only when cooking starts.
            if isinstance(self.stock, list):
                item_ids = set(customer["reserved"] if isinstance(customer["reserved"], list) else [])
                chosen = [it for it in self.stock if it["id"] in item_ids]
                recipe_counts = {}
                for item in chosen:
                    recipe_counts[item["kind"]] = recipe_counts.get(item["kind"], 0) + 1
                if len(chosen) != len(item_ids) or recipe_counts != dish["recipe"]:
                    customer["order_status"] = "unfulfillable"
                    customer["reserved"] = []
                    return
                recipe = dict(dish["recipe"])
                base_price = self._fresh_price(dish["price"], chosen)
                item_payloads = [item_out(it) for it in sorted(
                    chosen, key=lambda it: (it["kind"], id_key(it["id"])))]
                for item in chosen:
                    self.stock.remove(item)
            else:
                recipe = recipe or dict(dish["recipe"])
                for kind, amount in recipe.items():
                    self._consume(kind, amount)
                item_payloads = [kind for kind in sorted(recipe) for _ in range(recipe[kind])]
                base_price = dish["price"]
            customer["reserved"] = [] if isinstance(self.stock, list) else {}
            customer["order_status"] = "assigned"
            payload = {"order_id": customer["id"], "dish_id": customer["dish_id"],
                       "base_price": base_price}
            stove["state"] = "cooking"
            stove["dish"] = payload
            stove["cook_ticks_left"] = int(round(dish["cook_s"] * TICK))
            stove["ready_ticks"] = 0
            events.append(("cook_started", {"stove_id": stove["id"], "order_id": customer["id"],
                                             "dish_id": customer["dish_id"], "items": item_payloads,
                                             "base_price": base_price}))
        elif stove["state"] == "ready" and self.hand is None:
            payload = dict(stove["dish"])
            self.hand = payload
            stove["state"] = "idle"
            stove["dish"] = None
            stove["cook_ticks_left"] = 0
            stove["ready_ticks"] = 0
            events.append(("dish_picked", {"stove_id": stove["id"],
                                            "order_id": payload["order_id"],
                                            "dish_id": payload["dish_id"]}))

    def _interact_table(self, table, events):
        if self.hand is None:
            return
        customer = next((c for c in self.customers
                         if c["id"] == self.hand["order_id"] and c["table_id"] == table["id"]
                         and c.get("state") == "waiting"), None)
        if customer is None:
            return
        payload = self.hand
        self.hand = None
        reservation = next((r for r in self.reservations
                            if r["id"] == customer.get("reservation_id")), None)
        base_price = payload["base_price"]
        if reservation is not None:
            multiplier = Fraction(str(self.t["reservations"]["price_multiplier"]))
            base_price = math.floor(Fraction(base_price) * multiplier)
        max_patience = int(round(self.t["patience_s"] * TICK))
        ratio = customer["patience_ticks_left"] / max_patience
        customer["state"] = "eating"
        customer["order_status"] = "served"
        customer["reserved"] = [] if isinstance(self.stock, list) else {}
        customer["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
        customer["base_price"] = base_price
        tip = (math.floor(base_price * self.t["tip_rate"])
               if ratio >= self.t["tip_min_patience_ratio"] else 0)
        customer["tip"] = tip
        events.append(("served", {"order_id": customer["id"], "table_id": table["id"],
                                   "dish_id": customer["dish_id"],
                                   "patience_ticks_left": customer["patience_ticks_left"],
                                   "base_price": base_price, "tip": tip}))
        if reservation is not None:
            reservation["state"] = "served"
            events.append(("reservation_served", {"reservation_id": reservation["id"],
                                                   "order_id": customer["id"],
                                                   "table_id": table["id"]}))

    def _pay_and_leave(self, customer, reason, events):
        amount = customer["base_price"] + customer["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        events.append(("paid", {"order_id": customer["id"], "table_id": customer["table_id"],
                                 "base_price": customer["base_price"], "tip": customer["tip"],
                                 "amount": amount, "reason": reason}))
        if customer["tip"] > 0:
            self.reputation = min(self.t["reputation_max"], max(
                self.t["reputation_min"], self.reputation + self.t["tip_reputation"]))
        self.customers.remove(customer)

    def _discard_customer_dish(self, customer):
        order_id = customer["id"]
        for stove in self.stoves:
            dish = stove.get("dish")
            if dish is not None and dish.get("order_id") == order_id:
                stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand is not None and self.hand.get("order_id") == order_id:
            self.hand = None

    def _reserved_totals(self):
        totals = {}
        for customer in self.customers:
            if customer.get("order_status") == "reserved":
                reserved = customer.get("reserved", {})
                if isinstance(reserved, dict):
                    for kind, amount in reserved.items():
                        totals[kind] = totals.get(kind, 0) + amount
        return totals

    def _stock_counts(self):
        return hold_to_items(self.stock) if isinstance(self.stock, list) else self.stock

    def _consume(self, kind, amount):
        """Tiêu kho đếm của fixture Phase 1; kho cá thể dùng đường giữ chỗ theo ID."""
        if not isinstance(self.stock, list):
            self.stock[kind] -= amount
            return
        pick = sorted((it for it in self.stock if it["kind"] == kind),
                      key=lambda it: (-it["fresh"], id_key(it["id"])))[:amount]
        for it in pick:
            self.stock.remove(it)

    @staticmethod
    def _fresh_price(price, items):
        if not items:
            return price
        freshness = sum((it["fresh"] for it in items), Fraction(0)) / len(items)
        return math.floor(Fraction(price) * freshness / 100)

    def _select_items(self, recipe):
        """Pick the freshest distinct stock items required by a recipe; ties use stable ids."""
        if not isinstance(self.stock, list):
            return None
        reserved_ids = {iid for customer in self.customers
                        if customer.get("order_status") == "reserved"
                        for iid in customer.get("reserved", []) if isinstance(iid, str)}
        selected = []
        for kind, amount in sorted(recipe.items()):
            candidates = sorted((it for it in self.stock if it["kind"] == kind and it["id"] not in reserved_ids),
                                key=lambda it: (-it["fresh"], id_key(it["id"])))
            if len(candidates) < amount:
                return None
            selected.extend(candidates[:amount])
        return selected

    def _available_stock(self):
        if isinstance(self.stock, list):
            reserved_ids = {iid for customer in self.customers
                            if customer.get("order_status") == "reserved"
                            for iid in customer.get("reserved", []) if isinstance(iid, str)}
            counts = {}
            for item in self.stock:
                if item["id"] not in reserved_ids:
                    counts[item["kind"]] = counts.get(item["kind"], 0) + 1
            return counts
        reserved = self._reserved_totals()
        return {kind: amount - reserved.get(kind, 0) for kind, amount in self._stock_counts().items()}

    def _customer_left(self, customer, reason, events):
        if customer.get("reservation_id"):
            reservation = next(r for r in self.reservations if r["id"] == customer["reservation_id"])
            self._fail_reservation(reservation, reason, events, customer=customer)
            return
        if reason == "patience":
            q = self.t
            self.reputation = min(q["reputation_max"], max(
                q["reputation_min"], self.reputation + q["left_reputation_delta"]))
        self._discard_customer_dish(customer)
        self.customers.remove(customer)
        events.append(("customer_left", {"order_id": customer["id"],
                                          "table_id": customer["table_id"],
                                          "reason": reason,
                                          "reputation": self.reputation}))

    def _arrive_customer(self, events):
        occupied = {customer["table_id"] for customer in self.customers}
        held = {r["table_id"] for r in self.reservations if r["state"] == "holding"}
        free_tables = [table for table in self.tables
                       if table["id"] not in occupied and table["id"] not in held]
        if not free_tables:
            return
        table = sort_by_id(free_tables)[0]
        available = self._available_stock()
        dish_ids = sorted(
            dish_id for dish_id, dish in self.menu.items()
            if (self.allowed_dishes is None or dish_id in self.allowed_dishes)
            and all(available.get(kind, 0) >= amount for kind, amount in dish["recipe"].items())
        )
        if not dish_ids:
            events.append(("no_dish", {}))
            return
        dish_id = self.rng.get("quan_customer_orders").choice(dish_ids)
        selected = self._select_items(self.menu[dish_id]["recipe"])
        reserved = [it["id"] for it in selected] if selected is not None else dict(self.menu[dish_id]["recipe"])
        customer_id = self.ids.new("C")
        customer = {
            "id": customer_id,
            "table_id": table["id"],
            "dish_id": dish_id,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": reserved,
        }
        self.customers.append(customer)
        events.append(("customer_arrived", {"order_id": customer_id,
                                              "table_id": table["id"],
                                              "dish_id": dish_id}))

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
