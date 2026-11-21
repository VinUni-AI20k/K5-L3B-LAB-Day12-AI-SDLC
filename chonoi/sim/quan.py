"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
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
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = dict(scenario["hand"]) if scenario.get("hand") is not None else None
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.phase_tick = 0
        self.stoves = [dict(s, state=s.get("state", "idle"),
                            dish=dict(s["dish"]) if s.get("dish") is not None else None,
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [self._init_customer(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _init_customer(self, raw: dict) -> dict:
        c = dict(raw)
        c.setdefault("order_tick", 0)
        c.setdefault("state", "waiting")
        c.setdefault("order_status", "reserved")
        if c["state"] == "waiting":
            c.setdefault("patience_ticks_left", int(round(self.t["patience_s"] * 60)))
            c.setdefault("eat_ticks_left", 0)
        else:
            c.setdefault("patience_ticks_left", 0)
            c.setdefault("eat_ticks_left", int(round(self.t["eat_s"] * 60)))
        if "reserved" not in c:
            if c["order_status"] == "reserved":
                c["reserved"] = dict(self.menu[c["dish_id"]]["recipe"])
            else:
                c["reserved"] = {}
        else:
            c["reserved"] = dict(c["reserved"])
        c.setdefault("base_price", self.menu[c["dish_id"]]["price"] if c["state"] == "eating" else 0)
        c.setdefault("tip", 0)
        return c

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
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._tick_timers(events)
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        self._process_customers_and_closing(events)
        # TODO(nhóm, lát 3): khách mới theo lịch (first_customer_tick, customer_interval_s), no_dish khi self.time_left_ticks > 0.
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _tick_timers(self, events):
        """Giảm timer nấu/ăn/kiên nhẫn; tăng ready_ticks cho món đã ready từ đầu bước."""
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
                if s["cook_ticks_left"] == 0:
                    s["state"] = "ready"
                    s["ready_ticks"] = 0
                    dish = s["dish"]
                    events.append(("dish_ready", {
                        "stove_id": s["id"],
                        "order_id": dish["order_id"],
                        "dish_id": dish["dish_id"],
                    }))
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            elif c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)

    def _interact(self, events):
        """Tối đa một interact: chọn theo (khoảng cách, bếp trước bàn, id)."""
        r = self.t["interact_radius"]
        px, pz = self.pos
        candidates = []
        for s in self.stoves:
            d = math.hypot(px - s["pos"][0], pz - s["pos"][1])
            if d <= r:
                candidates.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.hypot(px - tb["pos"][0], pz - tb["pos"][1])
            if d <= r:
                candidates.append((d, 1, id_key(tb["id"]), "table", tb))
        if not candidates:
            return
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        _, _, _, kind, obj = candidates[0]
        if kind == "stove":
            self._interact_stove(obj, events)
        else:
            self._interact_table(obj, events)

    def _interact_stove(self, stove, events):
        if stove["state"] == "idle":
            reserved_orders = [
                c for c in self.customers
                if c["state"] == "waiting" and c["order_status"] == "reserved"
            ]
            if not reserved_orders:
                return
            reserved_orders.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
            c = reserved_orders[0]
            dish_id = c["dish_id"]
            base_price = self.menu[dish_id]["price"]
            items = []
            for k in sorted(c["reserved"]):
                amt = c["reserved"][k]
                self.stock[k] = max(0, self.stock.get(k, 0) - amt)
                items.extend([k] * amt)
            c["reserved"] = {}
            c["order_status"] = "assigned"
            stove["state"] = "cooking"
            stove["dish"] = {"order_id": c["id"], "dish_id": dish_id, "base_price": base_price}
            stove["cook_ticks_left"] = int(round(self.menu[dish_id]["cook_s"] * 60))
            stove["ready_ticks"] = 0
            events.append(("cook_started", {
                "stove_id": stove["id"],
                "order_id": c["id"],
                "dish_id": dish_id,
                "items": items,
                "base_price": base_price,
            }))
        elif stove["state"] == "ready":
            if self.hand is not None or self.t.get("carry_limit", 1) < 1:
                return
            dish = stove["dish"]
            self.hand = dict(dish)
            stove["state"] = "idle"
            stove["dish"] = None
            stove["cook_ticks_left"] = 0
            stove["ready_ticks"] = 0
            events.append(("dish_picked", {
                "stove_id": stove["id"],
                "order_id": dish["order_id"],
                "dish_id": dish["dish_id"],
            }))

    def _interact_table(self, table, events):
        if self.hand is None:
            return
        cust = next(
            (c for c in self.customers
             if c["table_id"] == table["id"] and c["state"] == "waiting" and c["id"] == self.hand["order_id"]),
            None,
        )
        if cust is None:
            return
        dish = self.hand
        self.hand = None
        patience_max = int(round(self.t["patience_s"] * 60))
        ratio = (cust["patience_ticks_left"] / patience_max) if patience_max > 0 else 0.0
        base_price = dish["base_price"]
        tip = math.floor(base_price * self.t["tip_rate"]) if ratio >= self.t["tip_min_patience_ratio"] else 0
        cust["state"] = "eating"
        cust["order_status"] = "served"
        cust["eat_ticks_left"] = int(round(self.t["eat_s"] * 60))
        cust["base_price"] = base_price
        cust["tip"] = tip
        events.append(("served", {
            "order_id": cust["id"],
            "table_id": table["id"],
            "dish_id": dish["dish_id"],
            "patience_ticks_left": cust["patience_ticks_left"],
            "base_price": base_price,
            "tip": tip,
        }))

    def _clamp_reputation(self, val: float) -> float:
        lo, hi = self.t["reputation_min"], self.t["reputation_max"]
        return min(hi, max(lo, round(val, 10)))

    def _pay_customer(self, c, reason: str, events):
        amount = c["base_price"] + c["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:
            self.reputation = self._clamp_reputation(self.reputation + self.t["tip_reputation"])
        events.append(("paid", {
            "order_id": c["id"],
            "table_id": c["table_id"],
            "base_price": c["base_price"],
            "tip": c["tip"],
            "amount": amount,
            "reason": reason,
        }))

    def _cleanup_customer_order(self, c):
        c["reserved"] = {}
        if self.hand is not None and self.hand["order_id"] == c["id"]:
            self.hand = None
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == c["id"]:
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0

    def _process_customers_and_closing(self, events):
        ordered = sorted(self.customers, key=lambda c: id_key(c["table_id"]))
        remaining = []
        closing = self.time_left_ticks <= 0
        for c in ordered:
            if not closing:
                if c["state"] == "eating" and c["eat_ticks_left"] == 0:
                    self._pay_customer(c, "finished_eating", events)
                elif c["state"] == "waiting" and c["patience_ticks_left"] == 0:
                    self.reputation = self._clamp_reputation(self.reputation + self.t["left_reputation_delta"])
                    events.append(("customer_left", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "patience",
                        "reputation": self.reputation,
                    }))
                    self._cleanup_customer_order(c)
                else:
                    remaining.append(c)
            else:
                if c["state"] == "eating":
                    self._pay_customer(c, "closing", events)
                else:
                    events.append(("customer_left", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "closing",
                        "reputation": self.reputation,
                    }))
                    self._cleanup_customer_order(c)
        self.customers = remaining

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
