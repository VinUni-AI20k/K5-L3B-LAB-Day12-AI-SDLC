"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

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
        self.customers = []
        for c in scenario.get("customers", []):
            customer = dict(c)
            customer.setdefault("state", "waiting")
            customer.setdefault("order_tick", 0)
            customer.setdefault("patience_ticks_left", int(round(t["patience_s"] * TICK)))
            customer.setdefault("eat_ticks_left", 0)
            customer.setdefault("order_status", "reserved")
            customer["reserved"] = dict(c.get("reserved", self.menu[c["dish_id"]]["recipe"]
                                              if customer["order_status"] == "reserved" else {}))
            customer.setdefault("base_price", None)
            customer.setdefault("tip", None)
            self.customers.append(customer)
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)

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
        for customer in self.customers:
            key = "eat_ticks_left" if customer["state"] == "eating" else "patience_ticks_left"
            customer[key] = max(0, customer[key] - 1)
        self._move(inp)
        # TODO(nhóm): tối đa MỘT interact, chọn đối tượng theo (khoảng cách, bếp trước bàn, id).
        # Bếp/bàn xử lý trước khi khách hết kiên nhẫn để phục vụ đúng tick 0 vẫn hợp lệ.
        if self.time_left_ticks <= 0:
            self._depart_waiting(events, closing=True)
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        else:
            self._depart_waiting(events)
            self._arrive(events)
        return events

    def available_stock(self):
        """Kho vật lý trừ nguyên liệu đã giữ cho những đơn chưa nấu."""
        available = dict(self.stock)
        for customer in self.customers:
            for kind, count in customer["reserved"].items():
                available[kind] = available.get(kind, 0) - count
        return available

    def _release_order(self, customer):
        """Nhả giữ chỗ và bỏ món đang gắn với đơn khi khách rời."""
        customer["reserved"] = {}
        for stove in self.stoves:
            if stove.get("dish") and stove["dish"].get("order_id") == customer["id"]:
                stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand and self.hand.get("order_id") == customer["id"]:
            self.hand = None

    def _depart_waiting(self, events, closing=False):
        for customer in sort_by_id(list(self.customers)):
            if customer["state"] != "waiting" or (not closing and customer["patience_ticks_left"] > 0):
                continue
            self._release_order(customer)
            self.customers.remove(customer)
            if not closing:
                self.reputation = max(self.t["reputation_min"], min(self.t["reputation_max"],
                    self.reputation + self.t["left_reputation_delta"]))
            events.append(("customer_left", {"order_id": customer["id"], "table_id": customer["table_id"],
                                             "reason": "closing" if closing else "patience",
                                             "reputation": self.reputation}))

    def _arrive(self, events):
        first = self.t["first_customer_tick"]
        interval = int(round(self.t["customer_interval_s"] * TICK))
        if not self.random_customers or self.phase_tick < first or (self.phase_tick - first) % interval:
            return
        occupied = {c["table_id"] for c in self.customers}
        table = next((tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied), None)
        if table is None:
            return
        available = self.available_stock()
        choices = [dish for dish in sorted(self.menu) if all(available.get(k, 0) >= n
                   for k, n in self.menu[dish]["recipe"].items())]
        if not choices:
            events.append(("no_dish", {}))
            return
        dish_id = self.rng.get("customer_order").choice(choices)
        order_id = self.ids.new("C")
        self.customers.append({"id": order_id, "table_id": table["id"], "dish_id": dish_id,
                               "order_tick": self.phase_tick, "state": "waiting",
                               "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
                               "eat_ticks_left": 0, "order_status": "reserved",
                               "reserved": dict(self.menu[dish_id]["recipe"]), "base_price": None, "tip": None})
        events.append(("customer_arrived", {"order_id": order_id, "table_id": table["id"],
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
