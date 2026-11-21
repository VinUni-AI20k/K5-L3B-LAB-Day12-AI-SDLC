"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Phân chia lát:
  - Lát 3 (`quan_customers.py`): khách đến theo lịch, chọn món nấu được, giữ chỗ
    nguyên liệu, kiên nhẫn, bỏ đi (customer_left), no_dish. Schema khách: docs/contracts/customer.md.
  - Lát 4 (`quan_service.py` + file này): interact bếp/bàn (cook_started, dish_ready,
    dish_picked, served), ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
  Chỉ người làm lát 4 sửa file này (thứ tự gọi trong step); lát 3 KHÔNG cần sửa file này.
"""

from ..ids import sort_by_id
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
        # khách dựng sẵn từ scenario; trường vắng lấy mặc định theo docs/contracts/customer.md
        full = int(round(t["patience_s"] * 60))
        self.customers = [dict(c, reserved=c.get("reserved", {}), state=c.get("state", "waiting"),
                               patience_ticks=c.get("patience_ticks", full), eat_ticks=c.get("eat_ticks", 0))
                          for c in scenario.get("customers", [])]
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
        # Thứ tự tạm theo khung; lát 4 chỉnh lại đúng PRD-0 mục F khi đề mở.
        service.tick_service(self, events)      # lát 4: bếp nấu -> dish_ready, khách ăn xong -> paid
        customers.tick_customers(self, events)  # lát 3: giảm kiên nhẫn, customer_left
        self._move(inp)
        if inp.pressed("interact"):
            service.interact(self, events)      # lát 4: tối đa MỘT interact (khoảng cách, bếp trước bàn, id)
        customers.spawn_customers(self, events)  # lát 3: khách mới theo lịch, chọn món, giữ chỗ, no_dish
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
