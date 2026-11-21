"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): đếm kiên nhẫn, bỏ đi (customer_left).
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

from collections import Counter

from ..ids import sort_by_id
from .ramp import ramp_velocity


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        self.tick_hz = tuning["tick_hz"]
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self.customer_interval_ticks = round(t["customer_interval_s"] * self.tick_hz)
        self.patience_max_ticks = round(t["patience_s"] * self.tick_hz)
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", round(t["duration_s"] * self.tick_hz))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [self._load_customer(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _load_customer(self, customer):
        if "reserved" not in customer and customer.get("state", "waiting") == "waiting":
            recipe = self.menu.get(customer.get("dish"), {}).get("recipe", {})
        else:
            recipe = customer.get("reserved", {})
        return dict(customer, reserved=dict(recipe))

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
        occupied = self._occupied_tables()
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
        # TODO(nhóm): giảm kiên nhẫn / nấu / ăn; bếp chín -> ready; xử lý khách theo thứ tự PRD-0 mục F.
        self._move(inp)
        # TODO(nhóm): tối đa MỘT interact, chọn đối tượng theo (khoảng cách, bếp trước bàn, id).
        table = self._arrival_table()
        if table is not None:
            self._seat_customer(table, events)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _occupied_tables(self):
        return {c["table_id"]: c["id"] for c in self.customers}

    def _arrival_table(self):
        since_first = self.phase_tick - self.t["first_customer_tick"]
        if not self.random_customers or since_first < 0 or since_first % self.customer_interval_ticks:
            return None
        occupied = self._occupied_tables()
        return next((table for table in self.tables if table["id"] not in occupied), None)

    def _seat_customer(self, table, events):
        available = Counter(self.stock)
        for customer in self.customers:
            available.subtract(customer["reserved"])
        dishes = [dish for dish, entry in sorted(self.menu.items())
                  if all(available[kind] >= amount for kind, amount in entry["recipe"].items())]
        customer_id = self.ids.new("C")
        if not dishes:
            events.append(("no_dish", {"customer_id": customer_id}))
            return
        dish = self.rng.get("customer_order").choice(dishes)
        table_id = table["id"]
        self.customers.append({"id": customer_id, "table_id": table_id, "dish": dish, "state": "waiting",
                               "patience_ticks": self.patience_max_ticks, "eat_ticks_left": 0,
                               "reserved": dict(self.menu[dish]["recipe"])})
        events.append(("customer_arrived", {"customer_id": customer_id, "table_id": table_id, "dish": dish}))

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
