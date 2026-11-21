"""Buổi tối — Mở Quán: khách/giữ chỗ P1-03 và bếp/phục vụ P1-04.

KitchenServingMixin quản lý validation, timers và cleanup dùng chung.
Khách mới sinh sau settlement, chỉ tham gia tương tác từ bước sau.
"""

from copy import deepcopy

from ..errors import BadInput
from ..ids import sort_by_id
from ..inventory import clone_items, items_to_counts, materialize_items
from .kitchen import KitchenServingMixin
from .ramp import ramp_velocity


class QuanSim(KitchenServingMixin):
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        # LiveGame restart must not reuse mutated customers, reservations or dishes.
        scenario = deepcopy(scenario)
        t = tuning["quan"]
        self.t = t
        self.tick_hz = tuning["tick_hz"]
        self.tick = 0
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        stock_source = inventory if inventory is not None else scenario.get("stock", {})
        self.stock_items = materialize_items(stock_source, ids, allow_legacy=inventory is None)
        self.stock = items_to_counts(self.stock_items)
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", self._ticks(t["duration_s"]))
        self.phase_tick = 0
        self.customer_interval_ticks = self._ticks(t["customer_interval_s"])
        self.patience_ticks = self._ticks(t["patience_s"])
        self.random_customers = scenario.get("random_customers", True)
        if not isinstance(self.random_customers, bool):
            raise BadInput("random_customers phải là boolean")
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [dict(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None
        self._validate_kitchen_state()

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "stock_items": self.inventory_items(),
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def inventory_items(self):
        """Danh sách cá thể còn trong kho vật lý sau các lần nấu."""
        remaining = self.stock.copy()
        kept = []
        for item in self.stock_items:
            kind = item["kind"]
            if remaining.get(kind, 0) > 0:
                kept.append(item)
                remaining[kind] -= 1
        return clone_items(kept)

    def step(self, inp):
        if self.done:
            return []
        events = []
        self.tick += 1
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._advance_kitchen_timers(events)
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        self._settle_customers(events)
        if not self.done:
            self._maybe_add_customer(events)
        return events

    def _available_stock(self):
        available = self.stock.copy()
        for customer in self.customers:
            for kind, count in customer["reserved"].items():
                available[kind] = available.get(kind, 0) - count
        return available

    def _maybe_add_customer(self, events):
        since_first = self.phase_tick - self.t["first_customer_tick"]
        if not self.random_customers or since_first < 0 or since_first % self.customer_interval_ticks:
            return
        occupied = {customer["table_id"] for customer in self.customers}
        table = next((table for table in self.tables if table["id"] not in occupied), None)
        if table is None:
            return
        table_id = table["id"]
        available = self._available_stock()
        dishes = [dish_id for dish_id in sorted(self.menu)
                  if all(available.get(kind, 0) >= count for kind, count in self.menu[dish_id]["recipe"].items())]
        if not dishes:
            events.append(("no_dish", {}))
            return
        dish_id = self.rng.get("customer_order").choice(dishes)
        reserved = dict(self.menu[dish_id]["recipe"])
        order_id = self.ids.new("C")
        self.customers.append({
            "id": order_id, "table_id": table_id, "dish_id": dish_id, "state": "waiting",
            "order_tick": self.phase_tick, "order_status": "reserved", "reserved": reserved,
            "patience_ticks_left": self.patience_ticks, "eat_ticks_left": 0, "base_price": 0, "tip": 0,
        })
        events.append(("customer_arrived", {"order_id": order_id, "table_id": table_id, "dish_id": dish_id}))

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
