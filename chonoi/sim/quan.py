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
        self.phase_tick = scenario.get("phase_tick", 0)
        self.random_customers = scenario.get("random_customers", True)
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        
        parsed_customers = []
        for c in scenario.get("customers", []):
            cust = dict(c)
            cust.setdefault("state", "waiting")
            cust.setdefault("order_tick", 0)
            cust.setdefault("patience_ticks_left", int(round(t["patience_s"] * 60)))
            cust.setdefault("order_status", "reserved")
            if cust["order_status"] == "reserved" and "reserved" not in cust:
                dish_id = cust.get("dish_id")
                if dish_id and dish_id in self.menu:
                    cust["reserved"] = dict(self.menu[dish_id]["recipe"])
                else:
                    cust["reserved"] = {}
            else:
                cust.setdefault("reserved", {})
            parsed_customers.append(cust)
        self.customers = parsed_customers
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
        self.phase_tick += 1

        # 1. Bếp nấu và tuổi món ready
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking":
                s["cook_ticks_left"] -= 1
                if s["cook_ticks_left"] <= 0:
                    s["state"] = "ready"
                    s["ready_ticks"] = 0
                    events.append(("dish_ready", {
                        "stove_id": s["id"],
                        "order_id": s["dish"]["order_id"],
                        "dish_id": s["dish"]["dish_id"],
                    }))
            elif s["state"] == "ready":
                s["ready_ticks"] += 1

        # 2. Khách giảm kiên nhẫn / ăn
        for c in self.customers:
            if c.get("state") == "waiting":
                c["patience_ticks_left"] = max(0, c.get("patience_ticks_left", 0) - 1)
            elif c.get("state") == "eating":
                c["eat_ticks_left"] = max(0, c.get("eat_ticks_left", 0) - 1)

        # 3. Di chuyển
        self._move(inp)

        # 4. Tương tác (interact): tối đa 1 interact, chọn theo (khoảng cách, bếp trước bàn, id)
        if inp.pressed("interact"):
            candidates = []
            for s in self.stoves:
                d = math.dist(self.pos, s["pos"])
                if d <= self.t["interact_radius"]:
                    candidates.append((d, 0, s["id"], "stove", s))
            for tb in self.tables:
                d = math.dist(self.pos, tb["pos"])
                if d <= self.t["interact_radius"]:
                    candidates.append((d, 1, tb["id"], "table", tb))
            if candidates:
                candidates.sort(key=lambda item: (item[0], item[1], item[2]))
                _, _, _, kind, obj = candidates[0]
                if kind == "stove":
                    s = obj
                    if s["state"] == "idle":
                        # Lấy đơn reserved cũ nhất theo order_tick rồi id bàn
                        reserved_custs = [c for c in self.customers if c.get("order_status") == "reserved"]
                        if reserved_custs:
                            reserved_custs.sort(key=lambda c: (c.get("order_tick", 0), c["table_id"]))
                            cust = reserved_custs[0]
                            recipe = self.menu[cust["dish_id"]]["recipe"]
                            # Tiêu đúng nguyên liệu giữ
                            for k, amt in recipe.items():
                                self.stock[k] = self.stock.get(k, 0) - amt
                            cust["reserved"] = {}
                            cust["order_status"] = "assigned"
                            base_price = self.menu[cust["dish_id"]]["price"]
                            s["state"] = "cooking"
                            s["dish"] = {"order_id": cust["id"], "dish_id": cust["dish_id"], "base_price": base_price}
                            s["cook_ticks_left"] = int(round(self.menu[cust["dish_id"]]["cook_s"] * TICK))
                            items_list = []
                            for k, amt in sorted(recipe.items()):
                                items_list.extend([k] * amt)
                            events.append(("cook_started", {
                                "stove_id": s["id"],
                                "order_id": cust["id"],
                                "dish_id": cust["dish_id"],
                                "items": sorted(items_list),
                                "base_price": base_price,
                            }))
                    elif s["state"] == "ready":
                        if self.hand is None:
                            self.hand = s["dish"]
                            s["dish"] = None
                            s["state"] = "idle"
                            s["ready_ticks"] = 0
                            events.append(("dish_picked", {
                                "stove_id": s["id"],
                                "order_id": self.hand["order_id"],
                                "dish_id": self.hand["dish_id"],
                            }))
                elif kind == "table":
                    tb = obj
                    cust = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
                    if cust and cust.get("state") == "waiting" and self.hand and self.hand["order_id"] == cust["id"]:
                        cust["state"] = "eating"
                        cust["order_status"] = "served"
                        cust["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
                        dish = self.hand
                        self.hand = None
                        # Boa
                        pat_ratio = cust["patience_ticks_left"] / (self.t["patience_s"] * TICK)
                        if pat_ratio >= self.t["tip_min_patience_ratio"]:
                            tip = math.floor(dish["base_price"] * self.t["tip_rate"])
                        else:
                            tip = 0
                        cust["tip"] = tip
                        cust["base_price"] = dish["base_price"]
                        events.append(("served", {
                            "order_id": cust["id"],
                            "table_id": tb["id"],
                            "dish_id": cust["dish_id"],
                            "patience_ticks_left": cust["patience_ticks_left"],
                            "base_price": dish["base_price"],
                            "tip": tip,
                        }))

        # 5. Theo id bàn: Khách ăn xong trả tiền / Khách hết kiên nhẫn bỏ về
        for tb in sort_by_id(self.tables):
            cust = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
            if not cust:
                continue
            if cust.get("state") == "eating" and cust.get("eat_ticks_left", 0) <= 0:
                amount = cust["base_price"] + cust.get("tip", 0)
                self.money += amount
                self.earned += amount
                self.shift_earned += amount
                if cust.get("tip", 0) > 0:
                    self.reputation = min(self.t["reputation_max"], self.reputation + self.t["tip_reputation"])
                events.append(("paid", {
                    "order_id": cust["id"],
                    "table_id": cust["table_id"],
                    "base_price": cust["base_price"],
                    "tip": cust.get("tip", 0),
                    "amount": amount,
                    "reason": "finished_eating",
                }))
                self.customers.remove(cust)
            elif cust.get("state") == "waiting" and cust.get("patience_ticks_left", 0) <= 0 and self.time_left_ticks > 0:
                self.reputation = max(self.t["reputation_min"], self.reputation + self.t["left_reputation_delta"])
                events.append(("customer_left", {
                    "order_id": cust["id"],
                    "table_id": cust["table_id"],
                    "reason": "patience",
                    "reputation": self.reputation,
                }))
                # Nhả phần giữ, hủy món nếu đang nấu hoặc trên tay
                for s in self.stoves:
                    if s.get("dish") and s["dish"].get("order_id") == cust["id"]:
                        s["state"] = "idle"
                        s["dish"] = None
                        s["cook_ticks_left"] = 0
                        s["ready_ticks"] = 0
                if self.hand and self.hand.get("order_id") == cust["id"]:
                    self.hand = None
                self.customers.remove(cust)

        # 6. Hết ca
        if self.time_left_ticks <= 0:
            for tb in sort_by_id(self.tables):
                cust = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
                if not cust:
                    continue
                if cust.get("state") == "eating":
                    amount = cust["base_price"] + cust.get("tip", 0)
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    if cust.get("tip", 0) > 0:
                        self.reputation = min(self.t["reputation_max"], self.reputation + self.t["tip_reputation"])
                    events.append(("paid", {
                        "order_id": cust["id"],
                        "table_id": cust["table_id"],
                        "base_price": cust["base_price"],
                        "tip": cust.get("tip", 0),
                        "amount": amount,
                        "reason": "closing",
                    }))
                    self.customers.remove(cust)
                elif cust.get("state") == "waiting":
                    events.append(("customer_left", {
                        "order_id": cust["id"],
                        "table_id": cust["table_id"],
                        "reason": "closing",
                        "reputation": self.reputation,
                    }))
                    self.customers.remove(cust)
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation,
            }))
            return events

        # 7. Khách mới theo lịch
        if self.time_left_ticks > 0 and self.random_customers:
            first = self.t["first_customer_tick"]
            interval = int(round(self.t["customer_interval_s"] * TICK))
            if self.phase_tick >= first and (self.phase_tick - first) % interval == 0:
                occupied_tables = {c["table_id"] for c in self.customers}
                free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied_tables]
                if free_tables:
                    table = free_tables[0]
                    # Tính tồn khả dụng = tồn vật lý trừ phần giữ chỗ
                    reserved_counts = {}
                    for c in self.customers:
                        for k, amt in c.get("reserved", {}).items():
                            reserved_counts[k] = reserved_counts.get(k, 0) + amt
                    avail_stock = {k: self.stock.get(k, 0) - reserved_counts.get(k, 0) for k in self.stock}
                    # Món nấu được
                    cookable = []
                    for dish_id in sorted(self.menu.keys()):
                        recipe = self.menu[dish_id]["recipe"]
                        if all(avail_stock.get(k, 0) >= amt for k, amt in recipe.items()):
                            cookable.append(dish_id)
                    if not cookable:
                        events.append(("no_dish", {}))
                    else:
                        dish_id = self.rng.get("customer_dish").choice(cookable)
                        recipe = self.menu[dish_id]["recipe"]
                        cid = self.ids.new("C")
                        cust = {
                            "id": cid,
                            "table_id": table["id"],
                            "dish_id": dish_id,
                            "order_tick": self.phase_tick,
                            "state": "waiting",
                            "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
                            "eat_ticks_left": int(round(self.t["eat_s"] * TICK)),
                            "order_status": "reserved",
                            "reserved": dict(recipe),
                            "base_price": self.menu[dish_id]["price"],
                            "tip": 0,
                        }
                        self.customers.append(cust)
                        events.append(("customer_arrived", {
                            "order_id": cid,
                            "table_id": table["id"],
                            "dish_id": dish_id,
                        }))

        return events

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
