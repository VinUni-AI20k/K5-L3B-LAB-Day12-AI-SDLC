"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm): nối các thao tác bếp/bàn vào vòng tick; xử lý trả tiền và boa.
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
        self.freshness = tuning.get("freshness")
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        stock = inventory if inventory is not None else scenario.get("stock", {})
        self.stock = [dict(item) for item in stock] if isinstance(stock, list) else dict(stock)
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
            "stock": (sort_by_id(self.stock) if isinstance(self.stock, list)
                      else {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}),
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    # Vòng tick chọn bếp/bàn và đơn hợp lệ trước khi gọi các hàm này.
    # Mỗi thao tác trả (tên sự kiện, dữ liệu) hoặc None nếu không thực hiện được.
    def start_cooking(self, stove, customer, *, base_price=None):
        """Nấu đơn reserved do vòng tick chọn theo order_tick rồi ID bàn.

        Bên gọi cập nhật trạng thái đơn và giải phóng phần giữ chỗ sau
        cook_started. Hàm này trừ kho thực đúng lúc món bắt đầu nấu.
        Với kho cá thể, bên gọi tính base_price theo các nguyên liệu đã giữ.
        """
        dish_id = customer["dish_id"]
        recipe = self.menu.get(dish_id)
        if stove["state"] != "idle" or recipe is None:
            return None
        ingredients = recipe["recipe"]
        dish = {"dish_id": dish_id, "customer_id": customer["id"]}
        if customer.get("order_id") is not None:
            dish["order_id"] = customer["order_id"]
        cook_ticks = max(1, round(recipe["cook_s"] * TICK))
        if isinstance(self.stock, list):
            if self.freshness is None or base_price is None:
                return None
            items = self._reserved_ingredients(customer, ingredients)
            if items is None:
                return None
            used_ids = {item["id"] for item in items}
            self.stock[:] = [item for item in self.stock if item["id"] not in used_ids]
            dish["base_price"] = base_price
            event_items = {"items": [dict(item) for item in items]}
        else:
            if any(self.stock.get(kind, 0) < quantity for kind, quantity in ingredients.items()):
                return None
            for kind, quantity in ingredients.items():
                self.stock[kind] -= quantity
            event_items = {}
        stove.update(state="cooking", dish=dish, cook_ticks_left=cook_ticks, ready_ticks=0)
        return "cook_started", {"stove_id": stove["id"], **dish, **event_items}

    def _reserved_ingredients(self, customer, recipe):
        reserved = customer.get("reserved")
        if not isinstance(reserved, list) or len(reserved) != len(set(reserved)):
            return None
        stock_by_id = {item["id"]: item for item in self.stock}
        items = []
        counts = {}
        threshold = self.freshness["spoiled_below"]
        for item_id in reserved:
            item = stock_by_id.get(item_id)
            if item is None or item["fresh"] < threshold:
                return None
            kind = item["kind"]
            counts[kind] = counts.get(kind, 0) + 1
            items.append(item)
        if counts != recipe:
            return None
        return sorted(sort_by_id(items), key=lambda item: item["kind"])

    def finish_cooking(self, stove):
        """Đổi trạng thái khi vòng tick đã đếm thời gian nấu về 0."""
        if stove["state"] != "cooking" or stove["cook_ticks_left"] != 0 or stove["dish"] is None:
            return None
        stove.update(state="ready", ready_ticks=0)
        return "dish_ready", {"stove_id": stove["id"], **stove["dish"]}

    def pick_dish(self, stove):
        """Bưng một món chín nếu tay đang trống."""
        if self.hand is not None or stove["state"] != "ready" or stove["dish"] is None:
            return None
        self.hand = stove["dish"]
        stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        return "dish_picked", {"stove_id": stove["id"], **self.hand}

    def serve_dish(self, table, customer):
        """Giao món cho đúng đơn. Bên gọi chuyển khách sang trạng thái ăn."""
        dish = self.hand
        if not isinstance(dish, dict) or customer["table_id"] != table["id"]:
            return None
        if dish.get("customer_id") != customer["id"] or dish.get("dish_id") != customer["dish_id"]:
            return None
        if dish.get("order_id") != customer.get("order_id"):
            return None
        self.hand = None
        return "served", {"table_id": table["id"], **dish}

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        # TODO(nhóm): giảm kiên nhẫn / nấu / ăn; bếp chín -> ready; xử lý khách theo thứ tự PRD-0 mục F.
        self._move(inp)
        # TODO(nhóm): tối đa MỘT interact, chọn đối tượng theo (khoảng cách, bếp trước bàn, id).
        # TODO(nhóm): khách mới theo lịch (first_customer_tick, customer_interval_s), no_dish.
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
