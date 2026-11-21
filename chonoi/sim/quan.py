"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

TV3 (PRD-0 mục E + F, lát 3): vòng đời khách — đến theo lịch, chọn món nấu được từ nguyên liệu
còn khả dụng, giữ chỗ nguyên liệu, kiên nhẫn, bỏ đi (customer_left), no_dish, đóng cửa (quan_end).
TV4 (lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                  ăn xong trả tiền (paid), boa, uy tín theo sự kiện phục vụ.
"""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.freshness = tuning.get("freshness")
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        stock = inventory if inventory is not None else scenario.get("stock", {})
        self.stock = [dict(item) for item in stock] if isinstance(stock, list) else dict(stock)
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.random_customers = scenario.get("random_customers", True)
        self.phase_tick = 0
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        # Khách dựng sẵn: điền mặc định theo PRD-0 mục D, rồi suy ra reserved còn thiếu.
        self.customers = []
        for e in scenario.get("customers", []):
            c = dict(e)
            c.setdefault("state", "waiting")
            c.setdefault("order_tick", 0)
            c.setdefault("order_status", "reserved")
            c.setdefault("patience_ticks_left", int(round(t["patience_s"] * TICK)))
            c.setdefault("eat_ticks_left", 0)
            c["reserved"] = dict(c.get("reserved") or {})
            c.setdefault("base_price", None)
            c.setdefault("tip", None)
            self.customers.append(c)
        # reserved mà thiếu giữ chỗ -> suy ra từ công thức, ưu tiên theo (order_tick, table_id).
        for c in sorted((c for c in self.customers
                         if c["order_status"] == "reserved" and not c["reserved"]),
                        key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            c["reserved"] = dict(self.menu[c["dish_id"]]["recipe"])
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
            "stock": (sort_by_id(self.stock) if isinstance(self.stock, list)
                      else {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}),
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    # Vòng tick chọn bếp/bàn và đơn hợp lệ trước khi gọi các hàm này.
    # Mỗi thao tác trả (tên sự kiện, dữ liệu) hoặc None nếu không thực hiện được.
    def start_cooking(self, stove, customer, *, base_price=None):
        """Nấu đơn reserved do vòng tick chọn theo order_tick rồi ID bàn.

        Bên gọi cập nhật trạng thái đơn và giải phóng phần giữ chỗ sau
        cook_started. Hàm này trừ kho thực đúng lúc món bắt đầu nấu.
        Với kho cá thể, bên gọi tính base_price theo các nguyên liệu đã giữ.
        """
        dish_id = customer["dish_id"]
        recipe = self.menu.get(dish_id)
        if stove["state"] != "idle" or recipe is None:
            return None
        ingredients = recipe["recipe"]
        dish = {"dish_id": dish_id, "order_id": customer["id"],
                "base_price": recipe["price"] if base_price is None else base_price}
        cook_ticks = max(1, round(recipe["cook_s"] * TICK))
        if isinstance(self.stock, list):
            if self.freshness is None or base_price is None:
                return None
            items = self._reserved_ingredients(customer, ingredients)
            if items is None:
                return None
            used_ids = {item["id"] for item in items}
            self.stock[:] = [item for item in self.stock if item["id"] not in used_ids]
            dish["base_price"] = base_price
            event_items = {"items": [dict(item) for item in items]}
        else:
            if any(self.stock.get(kind, 0) < quantity for kind, quantity in ingredients.items()):
                return None
            for kind, quantity in ingredients.items():
                self.stock[kind] -= quantity
            event_items = {}
        stove.update(state="cooking", dish=dish, cook_ticks_left=cook_ticks, ready_ticks=0)
        return "cook_started", {"stove_id": stove["id"], **dish, **event_items}

    def _reserved_ingredients(self, customer, recipe):
        reserved = customer.get("reserved")
        if not isinstance(reserved, list) or len(reserved) != len(set(reserved)):
            return None
        stock_by_id = {item["id"]: item for item in self.stock}
        items = []
        counts = {}
        threshold = self.freshness["spoiled_below"]
        for item_id in reserved:
            item = stock_by_id.get(item_id)
            if item is None or item["fresh"] < threshold:
                return None
            kind = item["kind"]
            counts[kind] = counts.get(kind, 0) + 1
            items.append(item)
        if counts != recipe:
            return None
        return sorted(sort_by_id(items), key=lambda item: item["kind"])

    def finish_cooking(self, stove):
        """Đổi trạng thái khi vòng tick đã đếm thời gian nấu về 0."""
        if stove["state"] != "cooking" or stove["cook_ticks_left"] != 0 or stove["dish"] is None:
            return None
        stove.update(state="ready", ready_ticks=0)
        return "dish_ready", {"stove_id": stove["id"], **stove["dish"]}

    def pick_dish(self, stove):
        """Bưng một món chín nếu tay đang trống."""
        if self.hand is not None or stove["state"] != "ready" or stove["dish"] is None:
            return None
        self.hand = stove["dish"]
        stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        return "dish_picked", {"stove_id": stove["id"], **self.hand}

    def serve_dish(self, table, customer):
        """Giao món cho đúng đơn. Bên gọi chuyển khách sang trạng thái ăn."""
        dish = self.hand
        if not isinstance(dish, dict) or customer["table_id"] != table["id"]:
            return None
        if dish.get("order_id") != customer["id"] or dish.get("dish_id") != customer["dish_id"]:
            return None
        self.hand = None
        return "served", {"table_id": table["id"], **dish}

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for c in self.customers:  # kiên nhẫn chỉ giảm khi còn đang chờ
            if c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
            elif c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
        for stove in self.stoves:
            if stove["state"] == "ready":
                stove["ready_ticks"] += 1
            elif stove["state"] == "cooking":
                stove["cook_ticks_left"] = max(0, stove["cook_ticks_left"] - 1)
                event = self.finish_cooking(stove)
                if event:
                    events.append(event)
        self._move(inp)
        if inp.pressed("interact"):
            event = self._interact()
            if event:
                events.append(event)
        self._pay_customers(events)
        self._customers_leave(events)
        self._spawn_customer(events)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _interact(self):
        targets = []
        for priority, entities in enumerate((self.stoves, self.tables)):
            for entity in entities:
                distance = math.dist(self.pos, entity["pos"])
                if distance <= self.t["interact_radius"]:
                    targets.append((distance, priority, entity))
        if not targets:
            return None
        _, priority, target = min(targets, key=lambda t: (t[0], t[1], id_key(t[2]["id"])))
        if priority == 0:
            if target["state"] == "ready":
                return self.pick_dish(target)
            if target["state"] != "idle":
                return None
            orders = (c for c in self.customers if c["order_status"] == "reserved")
            customer = min(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"])), default=None)
            if customer is None:
                return None
            event = self.start_cooking(target, customer)
            if event:
                customer.update(order_status="assigned", reserved=[] if isinstance(self.stock, list) else {})
            return event
        for customer in self.customers:
            if customer["table_id"] != target["id"] or customer["order_status"] != "assigned":
                continue
            event = self.serve_dish(target, customer)
            if event:
                price = event[1]["base_price"]
                threshold = self.t["patience_s"] * TICK * self.t["tip_min_patience_ratio"]
                tip = math.floor(price * self.t["tip_rate"]) if customer["patience_ticks_left"] >= threshold else 0
                customer.update(state="eating", order_status="served", base_price=price, tip=tip,
                                eat_ticks_left=round(self.t["eat_s"] * TICK))
            return event
        return None

    def _pay_customers(self, events):
        for customer in sorted(self.customers, key=lambda c: id_key(c["table_id"])):
            if customer["state"] != "eating" or (self.time_left_ticks > 0 and customer["eat_ticks_left"] > 0):
                continue
            price, tip = customer["base_price"], customer["tip"]
            amount = price + tip
            self.money += amount
            self.earned += amount
            self.shift_earned += amount
            if tip > 0:
                self.reputation = min(self.t["reputation_max"], self.reputation + self.t["tip_reputation"])
            events.append(("paid", {"order_id": customer["id"], "table_id": customer["table_id"],
                                    "dish_id": customer["dish_id"], "base_price": price, "tip": tip,
                                    "money": self.money, "reputation": self.reputation}))
            self.customers.remove(customer)

    def _available(self) -> dict:
        """Nguyên liệu khả dụng mỗi loại: kho trừ tổng khách đang giữ chỗ."""
        avail = dict(self.stock)
        for c in self.customers:
            for k, n in c.get("reserved", {}).items():
                avail[k] = avail.get(k, 0) - n
        return avail

    def _release_dishes(self, order_id):
        """Khách bỏ đi: hủy món của đơn đang ở bếp/tay để TV4 không xử lý đơn ma."""
        for s in self.stoves:
            if s.get("dish") and s["dish"].get("order_id") == order_id:
                s["state"], s["dish"], s["cook_ticks_left"], s["ready_ticks"] = "idle", None, 0, 0
        if self.hand and self.hand.get("order_id") == order_id:
            self.hand = None

    def _customers_leave(self, events):
        """Còn giờ: khách waiting hết kiên nhẫn rời bàn (trừ uy tín). Hết giờ: cả quán đóng cửa."""
        if self.time_left_ticks > 0:
            leaving = [c for c in self.customers if c["state"] == "waiting" and c["patience_ticks_left"] <= 0]
            reason, penalty = "patience", True
        else:
            leaving = [c for c in self.customers if c["state"] == "waiting"]
            reason, penalty = "closing", False
        leaving.sort(key=lambda c: id_key(c["table_id"]))
        for c in leaving:
            self.customers.remove(c)
            self._release_dishes(c["id"])
            if penalty:
                self.reputation = max(self.t["reputation_min"],
                                      min(self.t["reputation_max"],
                                          self.reputation + self.t["left_reputation_delta"]))
            events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"],
                                             "reason": reason, "reputation": self.reputation}))

    def _spawn_customer(self, events):
        """Khách mới theo lịch: bàn trống có id nhỏ nhất, chọn đều một món đủ nguyên liệu."""
        if self.time_left_ticks <= 0 or not self.random_customers:
            return
        first = self.t["first_customer_tick"]
        interval = int(round(self.t["customer_interval_s"] * TICK))
        due = self.phase_tick == first or (self.phase_tick > first and (self.phase_tick - first) % interval == 0)
        if not due:
            return
        occupied = {c["table_id"] for c in self.customers}
        free = sorted((tb["id"] for tb in self.tables if tb["id"] not in occupied), key=id_key)
        if not free:
            return
        avail = self._available()
        dishes = sorted(d for d, info in self.menu.items()
                        if all(avail.get(k, 0) >= n for k, n in info.get("recipe", {}).items()))
        if not dishes:
            events.append(("no_dish", {}))
            return
        dish_id = self.rng.get("customer_dish").choice(dishes)
        order_id = self.ids.new("C")
        self.customers.append({
            "id": order_id, "table_id": free[0], "dish_id": dish_id, "order_tick": self.phase_tick,
            "state": "waiting", "order_status": "reserved",
            "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
            "eat_ticks_left": 0, "reserved": dict(self.menu[dish_id]["recipe"]),
            "base_price": None, "tip": None,
        })
        events.append(("customer_arrived", {"order_id": order_id, "table_id": free[0], "dish_id": dish_id}))

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
