"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

from ..ids import sort_by_id
from .ramp import ramp_velocity


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.tick_hz = tuning["tick_hz"]
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
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * self.tick_hz)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = []
        for c in scenario.get("customers", []):
            customer = dict(c)
            # PRD-0 mục D: khách mặc định waiting, order_tick 0, order_status reserved, kiên nhẫn đầy.
            customer.setdefault("state", "waiting")
            customer.setdefault("order_tick", 0)
            customer.setdefault("order_status", "reserved")
            customer.setdefault("eat_ticks_left", 0)
            reserved = customer.get("reserved")
            if reserved is None:
                dish = self.menu.get(customer.get("dish_id"), {})
                reserved = dish.get("recipe", {}) if customer["order_status"] == "reserved" else {}
            customer["reserved"] = dict(reserved)
            if customer["state"] == "waiting":
                customer.setdefault("patience_ticks_left", int(round(t["patience_s"] * self.tick_hz)))
            self.customers.append(customer)
        for e in self.customers:
            ids.reserve(e["id"])
        self.random_customers = scenario.get("random_customers", True)
        self.sim_tick = 0
        self.phase_tick = 0
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
        self.sim_tick += 1
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._update_timers()
        self._move(inp)
        # TODO(nhóm): tối đa MỘT interact, chọn đối tượng theo (khoảng cách, bếp trước bàn, id).
        if self.time_left_ticks > 0:
            self._expire_customers(events)
            self._spawn_customer(events)
        if self.time_left_ticks <= 0:
            self._close_customers(events)  # PRD-0 mục F.4: dọn khách rồi mới phát quan_end
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    @staticmethod
    def _decrement(obj, key):
        if key in obj:
            obj[key] = max(0, obj[key] - 1)

    def _update_timers(self):
        for stove in self.stoves:
            if stove.get("state") == "cooking":
                self._decrement(stove, "cook_ticks_left")
                if stove.get("cook_ticks_left", 0) == 0:
                    stove["state"] = "ready"
            elif stove.get("state") == "ready":
                # PRD-0 mục F.1: chỉ tăng ready_ticks cho món đã ready ở đầu bước (món vừa chín bước này chưa tăng).
                stove["ready_ticks"] = stove.get("ready_ticks", 0) + 1
        for customer in self.customers:
            if customer.get("state") == "waiting":
                self._decrement(customer, "patience_ticks_left")
            elif customer.get("state") == "eating":
                self._decrement(customer, "eat_ticks_left")

    def _release_order(self, order_id):
        """Khách rời: nhả món của đơn đang nấu, ready hoặc trên tay (PRD-0 mục F.4); phần giữ nguyên liệu
        đi theo khách nên tự nhả khi khách bị xóa khỏi danh sách."""
        for stove in self.stoves:
            dish = stove.get("dish")
            if isinstance(dish, dict) and dish.get("order_id") == order_id:
                stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        hand = self.hand
        if isinstance(hand, dict) and hand.get("order_id") == order_id:
            self.hand = None

    def _expire_customers(self, events):
        for customer in sort_by_id(self.customers, key=lambda c: c["table_id"]):
            if customer.get("state") != "waiting" or customer.get("patience_ticks_left") != 0:
                continue
            self.reputation = min(
                self.t["reputation_max"],
                max(self.t["reputation_min"], self.reputation + self.t["left_reputation_delta"]),
            )
            self.customers.remove(customer)
            self._release_order(customer["id"])
            events.append(("customer_left", {
                "order_id": customer["id"], "table_id": customer["table_id"],
                "reason": "patience", "reputation": self.reputation,
            }))

    def _close_customers(self, events):
        """Hết ca: khách còn chờ rời với reason closing và KHÔNG trừ uy tín (khách còn ăn trả tiền ở lát 4)."""
        for customer in sort_by_id(self.customers, key=lambda c: c["table_id"]):
            if customer.get("state") != "waiting":
                continue
            self.customers.remove(customer)
            self._release_order(customer["id"])
            events.append(("customer_left", {
                "order_id": customer["id"], "table_id": customer["table_id"],
                "reason": "closing", "reputation": self.reputation,
            }))

    def _spawn_customer(self, events):
        interval = int(round(self.t["customer_interval_s"] * self.tick_hz))
        first = self.t["first_customer_tick"]
        if not self.random_customers or self.phase_tick < first or (self.phase_tick - first) % interval != 0:
            return
        occupied = {customer["table_id"] for customer in self.customers}
        free_tables = sort_by_id([table for table in self.tables if table["id"] not in occupied])
        if not free_tables:
            return

        available = dict(self.stock)
        for customer in self.customers:
            for ingredient, amount in customer.get("reserved", {}).items():
                available[ingredient] = available.get(ingredient, 0) - amount
        dishes = []
        for dish_id in sorted(self.menu):
            recipe = self.menu[dish_id]["recipe"]
            if all(available.get(ingredient, 0) >= amount for ingredient, amount in recipe.items()):
                dishes.append(dish_id)
        if not dishes:
            events.append(("no_dish", {}))
            return

        dish_id = self.rng.get("quan_customer_dish").choice(dishes)
        table = free_tables[0]
        customer_id = self.ids.new("C")
        recipe = dict(self.menu[dish_id]["recipe"])
        customer = {
            "id": customer_id,
            "table_id": table["id"],
            "state": "waiting",
            "order_status": "reserved",
            "order_tick": self.phase_tick,
            "dish_id": dish_id,
            "patience_ticks_left": int(round(self.t["patience_s"] * self.tick_hz)),
            "eat_ticks_left": 0,
            "reserved": recipe,
        }
        self.customers.append(customer)
        events.append(("customer_arrived", {
            "order_id": customer_id, "table_id": table["id"], "dish_id": dish_id,
        }))

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
