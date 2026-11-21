"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

from ..ids import sort_by_id
from . import quan_customers, quan_service
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, day_plan=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        self.day_plan = day_plan if day_plan is not None else scenario.get("day_plan")
        self.random_customers = scenario.get("random_customers", True)
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.phase_tick = 0  # bắt đầu 0, tăng mỗi bước; lịch khách tính theo giá trị SAU tăng
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        # Khách dựng sẵn từ scenario: điền mặc định theo PRD-0 mục D.
        self.customers = [self._customer(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _customer(self, c):
        """Áp mặc định: waiting, order_tick 0, kiên nhẫn đầy, reserved theo công thức."""
        cu = {
            "id": c["id"],
            "table_id": c["table_id"],
            "dish_id": c["dish_id"],
            "order_tick": c.get("order_tick", 0),
            "state": c.get("state", "waiting"),
            "patience_ticks_left": c.get("patience_ticks_left", int(round(self.t["patience_s"] * TICK))),
            "eat_ticks_left": c.get("eat_ticks_left", 0),
            "order_status": c.get("order_status", "reserved"),
            "reserved": dict(c.get("reserved") or {}),
            "base_price": c.get("base_price"),
            "tip": c.get("tip"),
        }
        if cu["order_status"] == "reserved" and not cu["reserved"]:
            cu["reserved"] = dict(self.menu[cu["dish_id"]]["recipe"])
        return cu

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
        # 1. đồng hồ: timer nấu/ăn (lát 4) và kiên nhẫn khách (lát 3)
        events.extend(quan_service.advance_stoves_and_eating(self))
        quan_customers.tick_patience(self, events)
        # 2-3. đi lại
        self._move(inp)
        # 4. tối đa MỘT interact: bếp/bàn, chọn theo (khoảng cách, bếp trước bàn, id)
        events.extend(quan_service.handle_interact(self, inp))
        # 5. khách ăn xong trả tiền, 6. khách hết kiên nhẫn bỏ đi
        events.extend(quan_service.handle_finished_eating(self))
        quan_customers.leave_if_impatient(self, events)
        # 7. đóng ca hoặc 8. sinh khách theo lịch
        if self.time_left_ticks <= 0:
            events.extend(quan_service.handle_closing(self))
            self.done = True
            self.reason = "time"
            # `handle_closing` đã phát `quan_end`; chỉ phát bổ sung nếu nó không làm (vd. khung rỗng)
            if not any(name == "quan_end" for name, _ in events):
                events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                            "shift_earned": self.shift_earned, "reputation": self.reputation}))
        elif self.random_customers:
            quan_customers.spawn_due(self, events)
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
