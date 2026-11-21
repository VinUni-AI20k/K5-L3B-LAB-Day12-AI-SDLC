"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  Lát 4 (TV3): bếp đã có — chọn đối tượng interact, nấu (cook_started), chín (dish_ready), bưng (dish_picked).
  TODO(nhóm, lát 4): phục vụ tại bàn (served), ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

import math

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
        # 1. đồng hồ + timer bếp (nấu, tuổi món ready) rồi 2. bếp chín -> ready (theo id)
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._tick_stoves(events)
        # TODO(nhóm, lát 3): giảm kiên nhẫn / ăn của khách.
        # 3. di chuyển rồi tối đa MỘT interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        # TODO(nhóm, lát 3/4): ăn xong trả tiền, khách hết kiên nhẫn rời, dọn quán khi hết ca.
        # TODO(nhóm, lát 3): khách mới theo lịch (first_customer_tick, customer_interval_s), no_dish.
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    # --- bếp (lát 4) -------------------------------------------------------------
    def _tick_stoves(self, events):
        """Bước 1–2: món ready ở ĐẦU bước tăng tuổi; món đang nấu giảm timer, về 0 thì ready (theo id)."""
        for s in self.stoves:  # self.stoves đã sắp theo id
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
                if s["cook_ticks_left"] == 0:
                    s["state"] = "ready"
                    s["ready_ticks"] = 0
                    d = s["dish"]
                    events.append(("dish_ready", {"stove_id": s["id"], "order_id": d["order_id"],
                                                  "dish_id": d["dish_id"]}))

    def _interact(self, events):
        """Chọn đúng MỘT đối tượng trong bán kính theo (khoảng cách, bếp trước bàn, id).
        Đối tượng được chọn không tương tác được thì bỏ lượt (không thử đối tượng khác)."""
        r = self.t["interact_radius"]
        cands = []
        for order, kind, coll in ((0, "stove", self.stoves), (1, "table", self.tables)):
            for obj in coll:
                d = math.dist(self.pos, obj["pos"])
                if d <= r:
                    cands.append((d, order, id_key(obj["id"]), kind, obj))
        if not cands:
            return
        _, _, _, kind, obj = min(cands, key=lambda c: c[:3])
        if kind == "stove":
            self._interact_stove(obj, events)
        else:
            self._interact_table(obj, events)

    def _interact_stove(self, s, events):
        if s["state"] == "idle":
            c = self._oldest_reserved_order()
            if c is None:
                return
            dish_id = c["dish_id"]
            dish = self.menu[dish_id]
            items = []
            for kind in sorted(c["reserved"]):
                n = c["reserved"][kind]
                self.stock[kind] = self.stock.get(kind, 0) - n
                items.extend([kind] * n)
            base_price = dish["price"]
            c["order_status"] = "assigned"
            c["reserved"] = {}
            c["base_price"] = base_price
            s["state"] = "cooking"
            s["dish"] = {"order_id": c["id"], "dish_id": dish_id, "base_price": base_price}
            s["cook_ticks_left"] = int(round(dish["cook_s"] * TICK))
            s["ready_ticks"] = 0
            events.append(("cook_started", {"stove_id": s["id"], "order_id": c["id"], "dish_id": dish_id,
                                            "items": items, "base_price": base_price}))
        elif s["state"] == "ready" and self.hand is None:  # carry_limit = 1
            d = s["dish"]
            self.hand = d
            s["state"], s["dish"], s["cook_ticks_left"], s["ready_ticks"] = "idle", None, 0, 0
            events.append(("dish_picked", {"stove_id": s["id"], "order_id": d["order_id"], "dish_id": d["dish_id"]}))
        # cooking, hoặc ready mà tay đã cầm món: bỏ lượt

    def _interact_table(self, tb, events):
        pass  # TODO(nhóm, lát 4): phục vụ đúng order_id trên tay -> served, chốt boa, khách ăn.

    def _oldest_reserved_order(self):
        """Đơn reserved cũ nhất theo (order_tick, id bàn)."""
        orders = [c for c in self.customers if c.get("order_status", "reserved") == "reserved"]
        if not orders:
            return None
        return min(orders, key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))

    def drop_order_dish(self, order_id):
        """Khách rời: bỏ món của đơn đang nấu, ready hoặc trên tay (nguyên liệu đã dùng không hoàn).
        Dùng cho phần khách rời của lát 3."""
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == order_id:
                s["state"], s["dish"], s["cook_ticks_left"], s["ready_ticks"] = "idle", None, 0, 0
        if self.hand is not None and self.hand["order_id"] == order_id:
            self.hand = None

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
