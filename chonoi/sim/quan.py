"""Buổi tối — Mở Quán.

PRD-0 mục F, Quán:
  Lát 3 (Đón khách & Giữ chỗ):
    - Khách đến theo lịch (first_customer_tick, customer_interval_s).
    - Khách chọn bàn trống (id nhỏ nhất), chọn đều 1 trong các món nấu được từ kho khả dụng (tồn vật lý - reserved).
    - Giữ chỗ nguyên liệu (reserved). Không có món đủ -> phát no_dish.
    - Giảm kiên nhẫn (patience_s). Hết kiên nhẫn -> customer_left (reason: "patience"), trừ uy tín (left_reputation_delta), giải phóng reserved.
  Lát 4 (Bếp, Bưng món, Tính tiền, Uy tín):
    - Di chuyển rồi xét tối đa 1 interact theo (khoảng cách, bếp trước bàn, id). Nếu không tương tác được, bỏ lượt.
    - Bếp idle: nhận đơn reserved cũ nhất (order_tick rồi id bàn), tiêu nguyên liệu giữ, phát cook_started.
    - Bếp nấu xong (cook_ticks_left == 0) -> dish_ready, ready_ticks = 0.
    - Bếp ready: nhấc lên tay trống (dish_picked), bếp về idle.
    - Bàn: giao đúng món khách gọi -> served, khách ăn trong eat_s. Nếu kiên nhẫn còn lại >= 50% chốt boa (floor(base_price * tip_rate)), ngược lại boa 0.
    - Ăn xong -> trả tiền món + boa (paid, reason: "finished_eating"), có boa cộng uy tín (tip_reputation).
    - Hết ca (time_left_ticks <= 0) -> khách đang ăn trả ngay (reason: "closing"), khách chờ rời (reason: "closing", không trừ uy tín), phát quan_end.
"""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, mode=None):
        self.mode = mode or scenario.get("mode", "quan")
        self.phase = "quan"
        self.tuning = tuning
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        self.phase_tick = scenario.get("phase_tick", 0)
        self.day = scenario.get("day", 1)
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        raw_stock = inventory if inventory is not None else scenario.get("stock", {})
        if isinstance(raw_stock, list):
            self.stock = [dict(it) for it in raw_stock]
        else:
            self.stock = dict(raw_stock)
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0),
                            order_id=s.get("order_id"), base_price=s.get("base_price", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.random_customers = scenario.get("random_customers", True)

        # Kế hoạch ngày (day_plan) cho mode day
        day_plans = scenario.get("day_plan") or tuning.get("day_plan", [])
        self.day_plan = next((dp for dp in day_plans if dp.get("day") == self.day), None)
        if self.day_plan:
            self.planned_dishes = dict(self.day_plan.get("dishes", {}))
        else:
            self.planned_dishes = None

        for s in self.stoves:
            ids.reserve(s["id"])
        for tb in self.tables:
            ids.reserve(tb["id"])

        self.customers = []
        patience_max = int(round(t["patience_s"] * 60))
        for c in scenario.get("customers", []):
            ids.reserve(c["id"])
            dish_id = c.get("dish_id") or c.get("dish")
            recipe = self.menu[dish_id]["recipe"] if (dish_id and dish_id in self.menu) else {}
            base_price = c.get("base_price", self.menu[dish_id]["price"] if (dish_id and dish_id in self.menu) else 0)
            order_status = c.get("order_status", "served" if c.get("state") == "eating" else "reserved")
            reserved = dict(c.get("reserved", recipe if order_status == "reserved" else {}))
            tip = c.get("tip")
            if tip is None:
                ratio = c.get("patience_ticks_left", patience_max) / patience_max
                if c.get("state") == "eating" and ratio >= t["tip_min_patience_ratio"]:
                    tip = math.floor(base_price * t["tip_rate"])
                else:
                    tip = 0
            cust = {
                "id": c["id"],
                "table_id": c["table_id"],
                "dish_id": dish_id,
                "order_tick": c.get("order_tick", 0),
                "state": c.get("state", "waiting"),
                "patience_ticks_left": c.get("patience_ticks_left", patience_max),
                "eat_ticks_left": c.get("eat_ticks_left", 0),
                "order_status": order_status,
                "reserved": reserved,
                "base_price": base_price,
                "tip": tip,
            }
            self.customers.append(cust)

        # Khớp bếp với khách assigned nếu chưa có order_id
        for c in self.customers:
            if c["order_status"] == "assigned":
                if not (self.hand and self.hand.get("order_id") == c["id"]):
                    for s in self.stoves:
                        if s["state"] in ("cooking", "ready") and s["dish"] == c["dish_id"] and not s.get("order_id"):
                            s["order_id"] = c["id"]
                            s["base_price"] = c["base_price"]
                            break

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
        if isinstance(self.stock, list):
            stock_snap = [dict(it) for it in sort_by_id(self.stock)]
        else:
            stock_snap = {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}
        return {
            "player": {"pos": self.pos},
            "stock": stock_snap,
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in sort_by_id(self.stoves)],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])}
                       for tb in sort_by_id(self.tables)],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1

        # 1. Tăng đồng hồ, giảm timer ca, nấu, ăn và kiên nhẫn
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for s in sort_by_id(self.stoves):
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] -= 1

        for c in self.customers:
            if c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
            elif c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)

        # 2. Bếp nấu xong chuyển sang ready
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking" and s["cook_ticks_left"] <= 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                events.append(("dish_ready", {
                    "stove_id": s["id"],
                    "order_id": s.get("order_id"),
                    "dish_id": s["dish"],
                }))

        # 3. Di chuyển và tương tác interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)

        # 4. Xử lý khách hàng (ăn xong, hết kiên nhẫn, hết ca)
        self._update_customers(events)

        # 5. Khách mới theo lịch
        if self.time_left_ticks > 0 and self.random_customers:
            self._spawn_customer(events)

        return events

    def _interact(self, events):
        r = self.t["interact_radius"]
        candidates = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r:
                candidates.append((d, 0, id_key(s["id"]), s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r:
                candidates.append((d, 1, id_key(tb["id"]), tb))

        if not candidates:
            return

        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        _, kind, _, target = candidates[0]

        if kind == 0:
            s = target
            if s["state"] == "idle":
                reserved_orders = [c for c in self.customers if c["state"] == "waiting" and c["order_status"] == "reserved"]
                if reserved_orders:
                    reserved_orders.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
                    c = reserved_orders[0]
                    recipe = self.menu[c["dish_id"]]["recipe"]
                    for k, qty in recipe.items():
                        self.stock[k] = self.stock.get(k, 0) - qty
                    c["reserved"] = {}
                    c["order_status"] = "assigned"

                    cook_ticks = int(round(self.menu[c["dish_id"]]["cook_s"] * 60))
                    s["state"] = "cooking"
                    s["dish"] = c["dish_id"]
                    s["cook_ticks_left"] = cook_ticks
                    s["ready_ticks"] = 0
                    s["order_id"] = c["id"]
                    s["base_price"] = c["base_price"]

                    items_list = []
                    for k, qty in sorted(recipe.items()):
                        items_list.extend([k] * qty)
                    items_list.sort()

                    events.append(("cook_started", {
                        "stove_id": s["id"],
                        "order_id": c["id"],
                        "dish_id": c["dish_id"],
                        "items": items_list,
                        "base_price": c["base_price"],
                    }))
            elif s["state"] == "ready":
                if self.hand is None:
                    self.hand = {
                        "order_id": s["order_id"],
                        "dish_id": s["dish"],
                        "base_price": s["base_price"],
                    }
                    events.append(("dish_picked", {
                        "stove_id": s["id"],
                        "order_id": s["order_id"],
                        "dish_id": s["dish"],
                    }))
                    s["state"] = "idle"
                    s["dish"] = None
                    s["cook_ticks_left"] = 0
                    s["ready_ticks"] = 0
                    s["order_id"] = None
                    s["base_price"] = 0
        else:
            tb = target
            cust = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
            if cust and cust["state"] == "waiting" and self.hand is not None and self.hand.get("order_id") == cust["id"]:
                patience_max = int(round(self.t["patience_s"] * 60))
                ratio = cust["patience_ticks_left"] / patience_max
                if ratio >= self.t["tip_min_patience_ratio"]:
                    tip = math.floor(cust["base_price"] * self.t["tip_rate"])
                else:
                    tip = 0
                cust["state"] = "eating"
                cust["order_status"] = "served"
                cust["eat_ticks_left"] = int(round(self.t["eat_s"] * 60))
                cust["tip"] = tip
                events.append(("served", {
                    "order_id": cust["id"],
                    "table_id": cust["table_id"],
                    "dish_id": cust["dish_id"],
                    "patience_ticks_left": cust["patience_ticks_left"],
                    "base_price": cust["base_price"],
                    "tip": tip,
                }))
                self.hand = None

    def _update_customers(self, events):
        by_table = sorted(self.customers, key=lambda c: id_key(c["table_id"]))

        if self.time_left_ticks > 0:
            to_remove = set()
            for c in by_table:
                if c["state"] == "eating" and c["eat_ticks_left"] <= 0:
                    amount = c["base_price"] + c["tip"]
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    if c["tip"] > 0:
                        self.reputation = min(self.t["reputation_max"], self.reputation + self.t["tip_reputation"])
                    events.append(("paid", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "base_price": c["base_price"],
                        "tip": c["tip"],
                        "amount": amount,
                        "reason": "finished_eating",
                    }))
                    to_remove.add(c["id"])

            for c in by_table:
                if c["id"] not in to_remove and c["state"] == "waiting" and c["patience_ticks_left"] <= 0:
                    self.reputation = max(self.t["reputation_min"], self.reputation + self.t["left_reputation_delta"])
                    events.append(("customer_left", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "patience",
                        "reputation": self.reputation,
                    }))
                    self._cleanup_customer(c)
                    to_remove.add(c["id"])

            if to_remove:
                self.customers = [c for c in self.customers if c["id"] not in to_remove]
        else:
            for c in by_table:
                if c["state"] == "eating":
                    amount = c["base_price"] + c["tip"]
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    if c["tip"] > 0:
                        self.reputation = min(self.t["reputation_max"], self.reputation + self.t["tip_reputation"])
                    events.append(("paid", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "base_price": c["base_price"],
                        "tip": c["tip"],
                        "amount": amount,
                        "reason": "closing",
                    }))

            for c in by_table:
                if c["state"] == "waiting":
                    self._cleanup_customer(c)
                    events.append(("customer_left", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "closing",
                        "reputation": self.reputation,
                    }))

            self.customers = []
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation,
            }))

    def _cleanup_customer(self, c):
        c["reserved"] = {}
        for s in self.stoves:
            if s.get("order_id") == c["id"]:
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0
                s["order_id"] = None
                s["base_price"] = 0
        if self.hand and self.hand.get("order_id") == c["id"]:
            self.hand = None

    def _spawn_customer(self, events):
        first_tick = self.t["first_customer_tick"]
        interval = int(round(self.t["customer_interval_s"] * 60))
        if self.phase_tick < first_tick or (self.phase_tick - first_tick) % interval != 0:
            return

        occupied = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
        if not free_tables:
            return

        table = free_tables[0]

        reserved_totals = {}
        for c in self.customers:
            if c.get("order_status") == "reserved":
                for k, qty in c.get("reserved", {}).items():
                    reserved_totals[k] = reserved_totals.get(k, 0) + qty

        avail = {k: max(0, self.stock.get(k, 0) - reserved_totals.get(k, 0)) for k in self.stock}

        def can_cook(dish_key):
            recipe = self.menu[dish_key]["recipe"]
            return all(avail.get(k, 0) >= qty for k, qty in recipe.items())

        # Mode day: bám sát theo Kế hoạch ngày (D1–D5) và tồn khả dụng
        if self.mode == "day" and self.day_plan:
            candidates = [d for d in sorted(self.planned_dishes.keys())
                          if self.planned_dishes.get(d, 0) > 0 and can_cook(d)]
            if not candidates:
                candidates = [d for d in sorted(self.day_plan.get("dishes", {}).keys())
                              if can_cook(d)]
        else:
            candidates = [d for d in sorted(self.menu.keys()) if can_cook(d)]

        if not candidates:
            events.append(("no_dish", {}))
            return

        dish_id = self.rng.get("customer").choice(candidates)
        if self.mode == "day" and self.planned_dishes and self.planned_dishes.get(dish_id, 0) > 0:
            self.planned_dishes[dish_id] -= 1
        recipe = self.menu[dish_id]["recipe"]
        c_id = self.ids.new("C")
        new_customer = {
            "id": c_id,
            "table_id": table["id"],
            "dish_id": dish_id,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": int(round(self.t["patience_s"] * 60)),
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": dict(recipe),
            "base_price": self.menu[dish_id]["price"],
            "tip": 0,
        }
        self.customers.append(new_customer)
        events.append(("customer_arrived", {
            "order_id": c_id,
            "table_id": table["id"],
            "dish_id": dish_id,
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
