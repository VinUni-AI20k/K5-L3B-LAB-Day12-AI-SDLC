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
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [dict(c, reserved=c.get("reserved", {})) for c in scenario.get("customers", [])]
        self._elapsed_ticks = 0
        self._next_customer_tick = int(t["first_customer_tick"]) if scenario.get("random_customers", True) else None
        self._reserve_fixture_customers()
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
            # tồn VẬT LÝ (hợp đồng mục 2.2); kho khả dụng = stock − Σ reserved, UI tự tính
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
        self._elapsed_ticks += 1

        # Kiên nhẫn bắt đầu giảm ở tick sau khi khách đến/được dựng fixture.
        for c in sort_by_id(self.customers):
            if c.get("state", "waiting") == "waiting" and c.get("arrived_tick", 0) != self._elapsed_ticks:
                c["patience_ticks_left"] = max(0, int(c.get("patience_ticks_left",
                                                              int(round(self.t["patience_s"] * TICK))) - 1))
        events.extend(self._remove_impatient_customers())
        self._cancel_orphan_orders()
        # Lát 4: bếp nấu -> chín, khách ăn xong -> trả tiền (bộ đếm giảm từ bước SAU khi đặt).
        events.extend(self._tick_stoves())
        events.extend(self._tick_eating())

        self._move(inp)
        if inp.pressed("interact"):
            events.extend(self._interact())
        if not self.done and self._next_customer_tick is not None and self._elapsed_ticks >= self._next_customer_tick:
            events.extend(self._seat_scheduled_customer())
            interval_ticks = int(round(self.t["customer_interval_s"] * TICK))
            self._next_customer_tick += max(1, interval_ticks)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.extend(self._close_customers())
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _reserve_fixture_customers(self):
        for c in self.customers:
            dish_id = c.get("dish_id")
            if dish_id is not None and dish_id not in self.menu:
                from ..errors import BadInput
                raise BadInput(f"customers.{c['id']}: dish_id không có trong menu")

            order_status = c.get("order_status", "reserved")
            if order_status not in ("reserved", "assigned", "unfulfillable", "served"):
                from ..errors import BadInput
                raise BadInput(f"customers.{c['id']}: order_status không hợp lệ")
            reserved = c.get("reserved")
            if reserved is None:
                reserved = {}
            if not isinstance(reserved, dict):
                from ..errors import BadInput
                raise BadInput(f"customers.{c['id']}: reserved phải là object")
            if dish_id is not None and order_status == "reserved" and not reserved:
                reserved = dict(self.menu[dish_id]["recipe"])
            if order_status != "reserved":
                reserved = {}

            for kind, qty in reserved.items():
                if kind not in self.stock or qty > self.stock.get(kind, 0):
                    from ..errors import BadInput
                    raise BadInput(f"customers.{c['id']}: reserved vượt kho khả dụng")

            c["reserved"] = reserved
            c["dish_id"] = dish_id
            c["order_tick"] = int(c.get("order_tick", 0))
            c["order_status"] = order_status
            c["state"] = c.get("state", "waiting")
            c["patience_ticks_left"] = int(c.get("patience_ticks_left",
                                                  int(round(self.t["patience_s"] * TICK))))
            c["eat_ticks_left"] = int(c.get("eat_ticks_left", 0))
            c["base_price"] = int(c.get("base_price", self.menu[dish_id]["price"] if dish_id else 0))
            c["tip"] = int(c.get("tip", 0))
            c["arrived_tick"] = 0

        totals = {}
        for c in self.customers:
            if c["order_status"] == "reserved":
                for kind, qty in c["reserved"].items():
                    totals[kind] = totals.get(kind, 0) + qty
        for kind, qty in totals.items():
            if qty > self.stock.get(kind, 0):
                from ..errors import BadInput
                raise BadInput(f"tổng reserved vượt kho khả dụng: {kind}")

    def _available_stock(self):
        reserved_totals = {}
        for c in self.customers:
            if c.get("order_status") == "reserved":
                for kind, qty in c.get("reserved", {}).items():
                    reserved_totals[kind] = reserved_totals.get(kind, 0) + qty
        return {
            kind: max(0, qty - reserved_totals.get(kind, 0))
            for kind, qty in self.stock.items()
        }

    def _available_dishes(self):
        available = []
        available_stock = self._available_stock()
        for dish_id in sorted(self.menu):
            recipe = self.menu[dish_id]["recipe"]
            if all(available_stock.get(kind, 0) >= qty for kind, qty in recipe.items()):
                available.append(dish_id)
        return available

    def _seat_scheduled_customer(self):
        empty_tables = [
            tb for tb in sort_by_id(self.tables)
            if not any(c.get("table_id") == tb["id"] for c in self.customers)
        ]
        if not empty_tables:
            return []

        available = self._available_dishes()
        if not available:
            return [("no_dish", {"table_id": empty_tables[0]["id"]})]

        dish_id = self.rng.get("customers").choice(available)
        recipe = dict(self.menu[dish_id]["recipe"])
        table = empty_tables[0]
        customer_id = self.ids.new("C")
        customer = {
            "id": customer_id,
            "table_id": table["id"],
            "dish_id": dish_id,
            "reserved": recipe,
            "order_tick": self._elapsed_ticks,
            "order_status": "reserved",
            "state": "waiting",
            "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
            "eat_ticks_left": 0,
            "base_price": int(self.menu[dish_id]["price"]),
            "tip": 0,
            "arrived_tick": self._elapsed_ticks,
        }
        self.customers.append(customer)
        return [("customer_arrived", {
            "customer_id": customer_id,
            "table_id": table["id"],
            "dish_id": dish_id,
        })]

    def _release_reserved(self, customer):
        customer["reserved"] = {}

    def _remove_impatient_customers(self):
        events = []
        remaining = []
        for c in sort_by_id(self.customers):
            if c.get("state", "waiting") == "waiting" and c.get("patience_ticks_left", 0) <= 0:
                self._release_reserved(c)
                self.reputation = max(float(self.t["reputation_min"]),
                                      self.reputation + float(self.t["left_reputation_delta"]))
                events.append(("customer_left", {
                    "customer_id": c["id"],
                    "table_id": c["table_id"],
                    "reason": "patience",
                    "reputation": self.reputation,
                }))
            else:
                remaining.append(c)
        self.customers = remaining
        return events

    def _close_customers(self):
        events = []
        for c in sort_by_id(self.customers):
            self._release_reserved(c)
            events.append(("customer_left", {
                "customer_id": c["id"],
                "table_id": c["table_id"],
                "reason": "closing",
                "reputation": self.reputation,
            }))
        self.customers = []
        return events

    # --- Lát 4: bếp, bưng, phục vụ, tiền, uy tín ------------------------------
    def _ticks(self, seconds):
        return int(round(seconds * TICK))

    def _customer(self, customer_id):
        for c in self.customers:
            if c["id"] == customer_id:
                return c
        return None

    def _rep(self, delta):
        lo, hi = float(self.t["reputation_min"]), float(self.t["reputation_max"])
        self.reputation = min(hi, max(lo, self.reputation + delta))

    def _cancel_orphan_orders(self):
        """Khách đã bỏ đi -> hủy món đang nấu/chín/trên tay; không hoàn nguyên liệu (clarify #4)."""
        for s in self.stoves:
            if s["dish"] is not None and self._customer(s["dish"]["order_id"]) is None:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand is not None and self._customer(self.hand["order_id"]) is None:
            self.hand = None

    def _tick_stoves(self):
        events = []
        for s in sort_by_id(self.stoves):
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
                if s["cook_ticks_left"] == 0:
                    s["state"], s["ready_ticks"] = "ready", 0
                    events.append(("dish_ready", {"stove_id": s["id"], "customer_id": s["dish"]["order_id"],
                                                  "dish_id": s["dish"]["dish_id"]}))
        return events

    def _tick_eating(self):
        events = []
        for c in sort_by_id(list(self.customers)):
            if c.get("state") == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
                if c["eat_ticks_left"] == 0:
                    events.append(self._pay(c))
        return events

    def _interact(self):
        """Tối đa MỘT interact: đối tượng gần nhất trong interact_radius, hòa -> bếp trước bàn -> id."""
        r = self.t["interact_radius"]
        cands = [(math.dist(self.pos, o["pos"]), kind, id_key(o["id"]), o)
                 for kind, coll in ((0, self.stoves), (1, self.tables)) for o in coll]
        cands = [c for c in cands if c[0] <= r]
        if not cands:
            return []
        _, kind, _, target = min(cands, key=lambda c: c[:3])
        if kind == 0:
            if target["state"] == "idle":
                return self._cook(target)
            if target["state"] == "ready":
                return self._pick(target)
            return []
        return self._serve(target)

    def _cook(self, stove):
        orders = [c for c in self.customers if c.get("order_status") == "reserved" and c.get("dish_id")]
        if not orders:
            return []
        c = min(orders, key=lambda x: (x["order_tick"], id_key(x["id"])))
        dish_id = c["dish_id"]
        for kind, qty in self.menu[dish_id]["recipe"].items():
            self.stock[kind] = self.stock.get(kind, 0) - qty
        c["reserved"], c["order_status"] = {}, "assigned"
        stove.update(state="cooking", dish={"dish_id": dish_id, "order_id": c["id"]},
                     cook_ticks_left=max(1, self._ticks(self.menu[dish_id]["cook_s"])), ready_ticks=0)
        return [("cook_started", {"stove_id": stove["id"], "customer_id": c["id"], "dish_id": dish_id})]

    def _pick(self, stove):
        if self.hand is not None:  # carry_limit = 1
            return []
        dish = stove["dish"]
        c = self._customer(dish["order_id"])
        self.hand = {"order_id": dish["order_id"], "dish_id": dish["dish_id"],
                     "base_price": int(c["base_price"] if c else self.menu[dish["dish_id"]]["price"])}
        stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        return [("dish_picked", {"stove_id": stove["id"], "customer_id": dish["order_id"],
                                 "dish_id": dish["dish_id"]})]

    def _serve(self, table):
        if self.hand is None:
            return []
        c = next((x for x in self.customers if x.get("table_id") == table["id"]), None)
        if c is None or c.get("state") != "waiting" or c["id"] != self.hand["order_id"]:
            return []
        price = int(self.hand["base_price"])
        full = self._ticks(self.t["patience_s"])
        ratio = c["patience_ticks_left"] / full if full > 0 else 0
        tip = math.floor(price * self.t["tip_rate"]) if ratio >= self.t["tip_min_patience_ratio"] else 0
        c.update(state="eating", order_status="served", base_price=price, tip=tip,
                 eat_ticks_left=max(1, self._ticks(self.t["eat_s"])))
        self.hand = None
        return [("served", {"customer_id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"], "tip": tip})]

    def _pay(self, c):
        amount = int(c["base_price"]) + int(c["tip"])
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:  # [GĐ] có boa -> +tip_reputation (clarify #7)
            self._rep(float(self.t["tip_reputation"]))
        self.customers = [x for x in self.customers if x["id"] != c["id"]]
        return ("paid", {"customer_id": c["id"], "table_id": c["table_id"], "amount": amount, "tip": c["tip"],
                         "money": self.money, "reputation": self.reputation})

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
