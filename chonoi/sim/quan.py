"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Phân chia lát:
  - Lát 3 (`quan_customers.py`): khách đến theo lịch, chọn món nấu được, giữ chỗ
    nguyên liệu, kiên nhẫn, bỏ đi (customer_left), no_dish. Schema khách: docs/contracts/customer.md.
  - Lát 4 (`quan_service.py` + file này): interact bếp/bàn (cook_started, dish_ready,
    dish_picked, served), ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
  Chỉ người làm lát 4 sửa file này (thứ tự gọi trong step); lát 3 KHÔNG cần sửa file này.
"""

from ..ids import id_key, sort_by_id
from . import quan_customers as customers
from . import quan_service as service
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
        self.customers = self._load_customers(scenario.get("customers", []), t)
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _load_customers(self, raw, t):
        """Khách dựng sẵn từ scenario: điền mặc định (customer.md) và cấp `reserved` theo công thức;
        khách có order_tick nhỏ hơn lấy kho trước (rồi theo id bàn)."""
        full = int(round(t["patience_s"] * 60))
        out = [dict(c, state=c.get("state", "waiting"), order_tick=c.get("order_tick", 0),
                    order_status=c.get("order_status", "reserved"),
                    patience_ticks_left=c.get("patience_ticks_left", full),
                    eat_ticks_left=c.get("eat_ticks_left", 0)) for c in raw]
        free = dict(self.stock)
        todo = sorted((c for c in out if "reserved" not in c and c["order_status"] == "reserved"),
                      key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        for c in todo:
            recipe = self.menu[c["dish_id"]]["recipe"]
            if all(free.get(k, 0) >= n for k, n in recipe.items()):
                for k, n in recipe.items():
                    free[k] -= n
                c["reserved"] = dict(recipe)
        for c in out:
            c.setdefault("reserved", {})
        return out

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
        # Thứ tự theo docs/contracts/customer.md mục 5 (PRD-0 F). Hàm lát 3 gọi nếu có.
        timers = getattr(customers, "tick_customers_timers", None) or getattr(customers, "tick_customers", None)
        leave = getattr(customers, "customers_leave", None)
        closing = self.time_left_ticks <= 0
        service.tick_service(self, events)              # 1. bếp nấu -> dish_ready, khách ăn đếm ngược
        if timers:
            timers(self, events)                        # 1. kiên nhẫn (lát 3)
        self._move(inp)                                 # 2. đi lại
        if inp.pressed("interact"):
            service.interact(self, events)              # 2. tối đa MỘT interact
        service.settle(self, events, closing=closing)   # 3. ăn xong -> paid, rời bàn (hết ca: trả hết)
        if leave:
            leave(self, events)                         # 4/5. bỏ đi vì kiên nhẫn / closing (lát 3)
        service.drop_orphans(self)
        if not closing:
            customers.spawn_customers(self, events)     # 6. khách mới (lát 3)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
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
