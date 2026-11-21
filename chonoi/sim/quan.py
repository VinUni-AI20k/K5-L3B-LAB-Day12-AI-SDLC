"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

TV3 (lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
            bỏ đi (customer_left), no_dish, vòng đời khách waiting.
TV4 (lát 4): interact tại bếp/bàn, nấu/bưng/phục vụ, ăn xong trả tiền, boa, uy tín.
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
        self.patience_max = int(round(t["patience_s"] * TICK))
        self.customer_interval_ticks = int(round(t["customer_interval_s"] * TICK))
        self.random_customers = scenario.get("random_customers", True)
        self.phase_tick = 0
        self.customers = [
            self.normalize_customer(dict(c)) for c in scenario.get("customers", [])
        ]
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

    # --- TV3: kho khả dụng & chuẩn hóa khách ---------------------------------
    def available_stock(self) -> dict:
        """Tồn vật lý trừ tổng reserved của mọi đơn còn ngồi."""
        avail = dict(self.stock)
        for c in self.customers:
            for kind, qty in (c.get("reserved") or {}).items():
                avail[kind] = avail.get(kind, 0) - qty
        return avail

    def normalize_customer(self, c: dict) -> dict:
        """Default waiting/reserved; thiếu reserved thì lấy recipe theo dish_id."""
        out = dict(c)
        out.setdefault("state", "waiting")
        out.setdefault("order_status", "reserved")
        out.setdefault("order_tick", 0)
        out.setdefault("patience_ticks_left", self.patience_max)
        out.setdefault("eat_ticks_left", 0)
        out.setdefault("base_price", None)
        out.setdefault("tip", None)
        if "reserved" not in c or c["reserved"] is None:
            recipe = self.menu[out["dish_id"]]["recipe"]
            out["reserved"] = {k: recipe[k] for k in sorted(recipe)}
        else:
            out["reserved"] = dict(c["reserved"])
        return out

    def release_and_cleanup(self, order_id: str, reason: str) -> None:
        """Nhả reserved; bỏ món cùng order_id trên bếp/tay. Không hoàn stock đã nấu."""
        for c in list(self.customers):
            if c["id"] != order_id:
                continue
            c["reserved"] = {}
            self.customers.remove(c)
            break
        for s in self.stoves:
            dish = s.get("dish")
            if dish and dish.get("order_id") == order_id:
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0
        if self.hand and self.hand.get("order_id") == order_id:
            self.hand = None

    def tick_patience(self) -> None:
        """Chỉ khách waiting: giảm 1. Khách vừa spawn (cuối bước) không bị trừ cùng tick."""
        for c in self.customers:
            if c.get("state") == "waiting" and c.get("order_status") == "reserved":
                if c["patience_ticks_left"] > 0:
                    c["patience_ticks_left"] -= 1

    def handle_patience_leave(self) -> list:
        """waiting + patience 0 → customer_left + left_reputation_delta."""
        events = []
        delta = self.t["left_reputation_delta"]
        lo, hi = self.t["reputation_min"], self.t["reputation_max"]
        for c in sort_by_id(list(self.customers)):
            if c.get("state") != "waiting":
                continue
            if c["patience_ticks_left"] > 0:
                continue
            self.reputation = max(lo, min(hi, self.reputation + delta))
            events.append(("customer_left", {
                "order_id": c["id"],
                "table_id": c["table_id"],
                "reason": "patience",
                "reputation": self.reputation,
            }))
            self.release_and_cleanup(c["id"], "patience")
        return events

    def handle_closing_leaves(self) -> list:
        """Hết ca: khách waiting rời closing, không trừ uy tín."""
        events = []
        for c in sort_by_id(list(self.customers)):
            if c.get("state") != "waiting":
                continue
            events.append(("customer_left", {
                "order_id": c["id"],
                "table_id": c["table_id"],
                "reason": "closing",
                "reputation": self.reputation,
            }))
            self.release_and_cleanup(c["id"], "closing")
        return events

    def _free_tables(self):
        occupied = {c["table_id"] for c in self.customers}
        return [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]

    def _cookable_dishes(self) -> list:
        avail = self.available_stock()
        dishes = []
        for dish_id in sorted(self.menu.keys()):
            recipe = self.menu[dish_id]["recipe"]
            if all(avail.get(k, 0) >= qty for k, qty in recipe.items()):
                dishes.append(dish_id)
        return dishes

    def _is_spawn_tick(self) -> bool:
        first = self.t["first_customer_tick"]
        interval = self.customer_interval_ticks
        if self.phase_tick < first:
            return False
        return (self.phase_tick - first) % interval == 0

    def try_spawn_customer(self, phase_tick: int) -> list:
        """Lịch first_customer_tick rồi mỗi interval; bàn trống id nhỏ nhất; else no_dish."""
        events = []
        if not self.random_customers:
            return events
        if self.time_left_ticks <= 0:
            return events
        if not self._is_spawn_tick():
            return events
        free = self._free_tables()
        if not free:
            return events  # bàn bận: bỏ lượt, không event
        cookable = self._cookable_dishes()
        if not cookable:
            events.append(("no_dish", {}))
            return events
        dish_id = self.rng.get("dish_pick").choice(cookable)
        table = free[0]
        cid = self.ids.new("C")
        recipe = self.menu[dish_id]["recipe"]
        customer = self.normalize_customer({
            "id": cid,
            "table_id": table["id"],
            "dish_id": dish_id,
            "order_tick": phase_tick,
            "state": "waiting",
            "order_status": "reserved",
            "patience_ticks_left": self.patience_max,
            "reserved": {k: recipe[k] for k in sorted(recipe)},
        })
        self.customers.append(customer)
        events.append(("customer_arrived", {
            "order_id": cid,
            "table_id": table["id"],
            "dish_id": dish_id,
        }))
        return events

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id([{
                "id": c["id"],
                "table_id": c["table_id"],
                "dish_id": c["dish_id"],
                "order_tick": c["order_tick"],
                "state": c["state"],
                "patience_ticks_left": c["patience_ticks_left"],
                "eat_ticks_left": c.get("eat_ticks_left", 0),
                "order_status": c["order_status"],
                "reserved": {k: c["reserved"][k] for k in sorted(c.get("reserved") or {}) if c["reserved"][k] > 0},
                "base_price": c.get("base_price"),
                "tip": c.get("tip"),
            } for c in self.customers]),
        }

    def step(self, inp):
        """Thứ tự mục F: timer → move → interact(TV4) → patience leave → closing/pay(TV4) → spawn."""
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # TV3: giảm kiên nhẫn khách waiting đã có (không gồm khách spawn cuối bước này)
        self.tick_patience()
        # TODO(nhóm, TV4): giảm timer nấu / ăn; bếp chín -> ready.

        self._move(inp)

        # TODO(nhóm, TV4): tối đa MỘT interact, chọn theo (khoảng cách, bếp trước bàn, id).

        # TV3: khách waiting hết kiên nhẫn
        events.extend(self.handle_patience_leave())

        # TV4 sẽ xử lý eating done / thanh toán trước đóng ca; TV3 dọn waiting khi hết giờ.
        if self.time_left_ticks <= 0:
            events.extend(self.handle_closing_leaves())
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events

        # TV3: sinh khách mới theo lịch (phase_tick sau tăng)
        events.extend(self.try_spawn_customer(self.phase_tick))
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
