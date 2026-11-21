"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

TV3 (PRD-0 mục E + F, lát 3): vòng đời khách — đến theo lịch, chọn món nấu được từ nguyên liệu
còn khả dụng, giữ chỗ nguyên liệu, kiên nhẫn, bỏ đi (customer_left), no_dish, đóng cửa (quan_end).
TODO(TV4, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                  ăn xong trả tiền (paid), boa, uy tín theo sự kiện phục vụ.
"""

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
        self.random_customers = scenario.get("random_customers", True)
        self.phase_tick = 0
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        # Khách dựng sẵn: điền mặc định theo PRD-0 mục D, rồi suy ra reserved còn thiếu.
        self.customers = []
        for e in scenario.get("customers", []):
            c = dict(e)
            c.setdefault("state", "waiting")
            c.setdefault("order_tick", 0)
            c.setdefault("order_status", "reserved")
            c.setdefault("patience_ticks_left", int(round(t["patience_s"] * TICK)))
            c.setdefault("eat_ticks_left", 0)
            c["reserved"] = dict(c.get("reserved") or {})
            c.setdefault("base_price", None)
            c.setdefault("tip", None)
            self.customers.append(c)
        # reserved mà thiếu giữ chỗ -> suy ra từ công thức, ưu tiên theo (order_tick, table_id).
        for c in sorted((c for c in self.customers
                         if c["order_status"] == "reserved" and not c["reserved"]),
                        key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            c["reserved"] = dict(self.menu[c["dish_id"]]["recipe"])
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
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for c in self.customers:  # kiên nhẫn chỉ giảm khi còn đang chờ
            if c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
        # TODO(TV4): bếp nấu/chín (cook_ticks_left-- -> ready, ready_ticks++), khách ăn (eat_ticks_left--).
        self._move(inp)
        # TODO(TV4): tối đa MỘT interact, chọn đối tượng theo (khoảng cách, bếp trước bàn, id);
        #            bưng món, phục vụ (served), khách eating ăn xong trả tiền (paid, boa).
        self._customers_leave(events)
        self._spawn_customer(events)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _available(self) -> dict:
        """Nguyên liệu khả dụng mỗi loại: kho trừ tổng khách đang giữ chỗ."""
        avail = dict(self.stock)
        for c in self.customers:
            for k, n in c.get("reserved", {}).items():
                avail[k] = avail.get(k, 0) - n
        return avail

    def _release_dishes(self, order_id):
        """Khách bỏ đi: hủy món của đơn đang ở bếp/tay để TV4 không xử lý đơn ma."""
        for s in self.stoves:
            if s.get("dish") and s["dish"].get("order_id") == order_id:
                s["state"], s["dish"], s["cook_ticks_left"], s["ready_ticks"] = "idle", None, 0, 0
        if self.hand and self.hand.get("order_id") == order_id:
            self.hand = None

    def _customers_leave(self, events):
        """Còn giờ: khách waiting hết kiên nhẫn rời bàn (trừ uy tín). Hết giờ: cả quán đóng cửa."""
        if self.time_left_ticks > 0:
            leaving = [c for c in self.customers if c["state"] == "waiting" and c["patience_ticks_left"] <= 0]
            reason, penalty = "patience", True
        else:
            leaving = [c for c in self.customers if c["state"] == "waiting"]
            reason, penalty = "closing", False
        leaving.sort(key=lambda c: id_key(c["table_id"]))
        for c in leaving:
            self.customers.remove(c)
            self._release_dishes(c["id"])
            if penalty:
                self.reputation = max(self.t["reputation_min"],
                                      min(self.t["reputation_max"],
                                          self.reputation + self.t["left_reputation_delta"]))
            events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"],
                                             "reason": reason, "reputation": self.reputation}))

    def _spawn_customer(self, events):
        """Khách mới theo lịch: bàn trống có id nhỏ nhất, chọn đều một món đủ nguyên liệu."""
        if self.time_left_ticks <= 0 or not self.random_customers:
            return
        first = self.t["first_customer_tick"]
        interval = int(round(self.t["customer_interval_s"] * TICK))
        due = self.phase_tick == first or (self.phase_tick > first and (self.phase_tick - first) % interval == 0)
        if not due:
            return
        occupied = {c["table_id"] for c in self.customers}
        free = sorted((tb["id"] for tb in self.tables if tb["id"] not in occupied), key=id_key)
        if not free:
            return
        avail = self._available()
        dishes = sorted(d for d, info in self.menu.items()
                        if all(avail.get(k, 0) >= n for k, n in info.get("recipe", {}).items()))
        if not dishes:
            events.append(("no_dish", {}))
            return
        dish_id = self.rng.get("customer_dish").choice(dishes)
        order_id = self.ids.new("C")
        self.customers.append({
            "id": order_id, "table_id": free[0], "dish_id": dish_id, "order_tick": self.phase_tick,
            "state": "waiting", "order_status": "reserved",
            "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
            "eat_ticks_left": 0, "reserved": dict(self.menu[dish_id]["recipe"]),
            "base_price": None, "tip": None,
        })
        events.append(("customer_arrived", {"order_id": order_id, "table_id": free[0], "dish_id": dish_id}))

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
