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
        # TODO(nhóm): khách dựng sẵn từ scenario (customers[]) và suy ra giữ chỗ (reserved).
        self.customers = [dict(c, reserved=c.get("reserved", {})) for c in scenario.get("customers", [])]
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
        # Thứ tự gọi do Integrator giữ; đối chiếu PRD-0 mục F rồi mới đổi (báo cả nhóm).
        self._tick_customers(events)      # lát 3: kiên nhẫn, customer_left
        self._tick_stoves_and_eating(events)  # lát 4: nấu -> dish_ready, ăn xong -> paid
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)        # lát 4: tối đa MỘT interact
        self._spawn_customers(events)     # lát 3: khách mới theo lịch, no_dish
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    # --- lát 3 (sở hữu: người làm quán lát 3) ------------------------------------
    def _tick_customers(self, events):
        """TODO(nhóm, lát 3): giảm kiên nhẫn khách đang chờ (sort_by_id); hết kiên nhẫn -> customer_left,
        trả nguyên liệu giữ chỗ về kho (self._release), self._change_reputation(left_reputation_delta)."""

    def _spawn_customers(self, events):
        """TODO(nhóm, lát 3): khách đầu ở first_customer_tick, sau đó mỗi customer_interval_s; id qua self.ids;
        chọn món nấu được từ kho CHƯA giữ chỗ (self._available()); không có món -> no_dish;
        có -> ngồi bàn trống, giữ chỗ nguyên liệu (self._reserve). Ngẫu nhiên chỉ qua self.rng."""

    # --- lát 4 (sở hữu: người làm quán lát 4) ------------------------------------
    def _tick_stoves_and_eating(self, events):
        """TODO(nhóm, lát 4): bếp cooking giảm cook_ticks_left, về 0 -> ready + dish_ready;
        khách eating giảm thời gian ăn, xong -> paid (price + boa), money/earned/shift_earned,
        self._change_reputation(tip_reputation) nếu có boa; bàn trống."""

    def _interact(self, events):
        """TODO(nhóm, lát 4): chọn đối tượng trong interact_radius theo (khoảng cách, bếp trước bàn, id):
        bếp idle + có đơn giữ chỗ -> cook_started (trừ kho theo giữ chỗ); bếp ready + tay trống -> dish_picked;
        bàn có khách đúng món + tay cầm món -> served. Chỉ MỘT hành động mỗi tick."""

    # --- dùng chung (lát 3 + lát 4) ----------------------------------------------
    def _change_reputation(self, delta):
        """Mọi thay đổi uy tín đi qua đây: kẹp [reputation_min, reputation_max]."""
        lo, hi = self.t["reputation_min"], self.t["reputation_max"]
        self.reputation = min(hi, max(lo, self.reputation + delta))

    def _available(self) -> dict:
        """Kho còn dùng được = stock - tổng reserved của mọi khách."""
        free = dict(self.stock)
        for c in self.customers:
            for k, n in c.get("reserved", {}).items():
                free[k] = free.get(k, 0) - n
        return free

    def _reserve(self, customer, dish):
        """Giữ chỗ nguyên liệu của món `dish` cho khách (chưa trừ stock; trừ khi cook_started)."""
        customer["reserved"] = dict(self.menu[dish]["recipe"])

    def _release(self, customer):
        """Bỏ giữ chỗ (khách bỏ đi trước khi nấu)."""
        customer["reserved"] = {}

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
