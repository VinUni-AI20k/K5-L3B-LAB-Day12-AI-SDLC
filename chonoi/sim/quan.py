"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

from ..errors import BadInput
from ..ids import sort_by_id
from ..inventory import validate_items
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
        tick_hz = tuning["tick_hz"]
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.phase_tick = 0
        self.customer_interval_ticks = int(round(t["customer_interval_s"] * tick_hz))
        self.patience_ticks = int(round(t["patience_s"] * tick_hz))
        self.random_customers = scenario.get("random_customers", True)
        if not isinstance(self.random_customers, bool):
            raise BadInput("random_customers phải là boolean")
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [self._load_customer(c) for c in scenario.get("customers", [])]
        if any(count < 0 for count in self._available_stock().values()):
            raise BadInput("khách giữ chỗ nguyên liệu vượt quá kho")
        self._check_assigned_orders()
        for customer in self.customers:
            ids.reserve(customer["id"])
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
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _load_customer(self, customer):
        order = {
            "state": "waiting", "order_tick": 0, "patience_ticks_left": self.patience_ticks,
            "eat_ticks_left": 0, "order_status": "reserved", "base_price": 0, "tip": 0,
        }
        allowed = order.keys() | {"id", "table_id", "dish_id", "reserved"}
        if customer.keys() - allowed:
            raise BadInput("khách có trường chưa hỗ trợ")
        order.update(customer)
        dish_id = order.get("dish_id")
        if not isinstance(dish_id, str) or dish_id not in self.menu:
            raise BadInput(f"customers.{order['id']}: dish_id phải là món trong menu")
        for key in ("order_tick", "patience_ticks_left", "eat_ticks_left", "base_price", "tip"):
            if type(order[key]) is not int or order[key] < 0:
                raise BadInput(f"customers.{order['id']}.{key} phải là số nguyên không âm")
        status = order["order_status"]
        if order["state"] == "eating":
            if (status != "served" or order["eat_ticks_left"] <= 0
                    or order["base_price"] <= 0 or "tip" not in customer):
                raise BadInput("khách eating phải có đơn served, thời gian ăn, giá và boa đã chốt")
        elif (order["state"] != "waiting" or status not in ("reserved", "assigned", "unfulfillable")
              or order["eat_ticks_left"] != 0):
            raise BadInput("trạng thái khách, đơn hoặc thời gian ăn mâu thuẫn")
        expected = self.menu[dish_id]["recipe"] if status == "reserved" else {}
        reserved = validate_items(order.get("reserved", expected))
        if reserved != expected:
            raise BadInput("phần giữ chỗ không khớp trạng thái đơn và công thức")
        return dict(order, reserved=dict(reserved))

    def _check_assigned_orders(self):
        assigned = {c["id"]: c for c in self.customers if c["order_status"] == "assigned"}
        dishes = [stove["dish"] for stove in self.stoves if stove["dish"] is not None]
        if self.hand is not None:
            dishes.append(self.hand)
        for dish in dishes:
            if not isinstance(dish, dict) or dish.keys() != {"order_id", "dish_id", "base_price"}:
                raise BadInput("payload món phải có order_id, dish_id và base_price")
            order_id = dish["order_id"]
            order = assigned.pop(order_id, None) if isinstance(order_id, str) else None
            if (order is None or dish["dish_id"] != order["dish_id"]
                    or type(dish["base_price"]) is not int or dish["base_price"] <= 0):
                raise BadInput("món ở bếp hoặc tay phải khớp một đơn assigned duy nhất")
        if assigned:
            raise BadInput("mỗi đơn assigned cần đúng một món ở bếp hoặc tay")
        for stove in self.stoves:
            cook_left, ready_ticks = stove["cook_ticks_left"], stove["ready_ticks"]
            if any(type(ticks) is not int or ticks < 0 for ticks in (cook_left, ready_ticks)):
                raise BadInput("timer bếp phải là số nguyên không âm")
            state = stove["state"]
            valid = (
                (state == "idle" and stove["dish"] is None and cook_left == ready_ticks == 0)
                or (state == "cooking" and stove["dish"] is not None and cook_left > 0 and ready_ticks == 0)
                or (state == "ready" and stove["dish"] is not None and cook_left == 0)
            )
            if not valid:
                raise BadInput("trạng thái bếp không khớp món hoặc timer")

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos, "vel": self.vel},
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
        self._decrease_patience()
        # TODO(nhóm, lát 4): giảm bộ đếm nấu / ăn và chuyển trạng thái bếp.
        self._move(inp)
        # TODO(nhóm, lát 4): interact, sau đó xử lý paid cùng lượt duyệt khách theo id bàn.
        self._remove_waiting_customers(events)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        else:
            self._maybe_add_customer(events)
        return events

    def _available_stock(self):
        available = self.stock.copy()
        for customer in self.customers:
            for kind, count in customer["reserved"].items():
                available[kind] = available.get(kind, 0) - count
        return available

    def _decrease_patience(self):
        for customer in self.customers:
            if customer["state"] == "waiting":
                customer["patience_ticks_left"] = max(0, customer["patience_ticks_left"] - 1)

    def _remove_waiting_customers(self, events):
        closing = self.time_left_ticks == 0
        for customer in sort_by_id(self.customers, key=lambda c: c["table_id"]):
            if customer["state"] == "waiting" and (closing or customer["patience_ticks_left"] == 0):
                self._customer_left(customer, "closing" if closing else "patience", events)

    def _customer_left(self, customer, reason, events):
        order_id = customer["id"]
        if self.hand is not None and self.hand["order_id"] == order_id:
            self.hand = None
        for stove in self.stoves:
            if stove["dish"] is not None and stove["dish"]["order_id"] == order_id:
                stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        self.customers.remove(customer)
        if reason == "patience":
            self.reputation = max(self.t["reputation_min"], min(
                self.t["reputation_max"], self.reputation + self.t["left_reputation_delta"]
            ))
        events.append(("customer_left", {
            "order_id": order_id, "table_id": customer["table_id"],
            "reason": reason, "reputation": self.reputation,
        }))

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
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
