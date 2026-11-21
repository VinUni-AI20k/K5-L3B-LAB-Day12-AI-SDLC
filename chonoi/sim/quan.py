"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  Lát 4 (TV4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
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

    def __init__(self, tuning, scenario, streams, ids, inventory=None, *, day_dishes=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.orderable_dishes = sorted(self.menu if day_dishes is None else day_dishes)
        unknown = set(self.orderable_dishes) - self.menu.keys()
        if unknown:
            raise BadInput(f"món ngoài menu trong day_plan: {sorted(unknown)}")
        self.rng = streams
        self.ids = ids
        self.tick = 0
        self._tuning = tuning
        self.leftover_lifetime_ticks = None  # None = tắt (headless); bật qua enable_live_leftovers()
        self.stored_dishes = []
        tick_hz = tuning["tick_hz"]
        self.patience_ticks = round(t["patience_s"] * tick_hz)
        self.customer_interval_ticks = round(t["customer_interval_s"] * tick_hz)
        self.random_customers = scenario.get("random_customers", True)
        if not isinstance(self.random_customers, bool):
            raise BadInput("random_customers phải là boolean")
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
        self.customers = self._load_customers(scenario.get("customers", []))
        if any(amount < 0 for amount in self.available_stock().values()):
            raise BadInput("nguyên liệu giữ chỗ vượt quá kho")
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

    def _load_customers(self, fixtures):
        customers = []
        for fixture in sort_by_id(fixtures):
            customer = dict(fixture)
            customer.setdefault("state", "waiting")
            customer.setdefault("patience_ticks_left", self.patience_ticks)
            patience = customer["patience_ticks_left"]
            if type(patience) is not int or patience < 0:
                raise BadInput("patience_ticks_left phải là số nguyên không âm")
            dish_id = customer.get("dish_id")
            recipe = {}
            if dish_id is not None:
                if not isinstance(dish_id, str) or dish_id not in self.menu:
                    raise BadInput(f"mã món không hợp lệ: {dish_id!r}")
                if customer["state"] == "waiting":
                    recipe = self.menu[dish_id]["recipe"]
            customer["reserved"] = validate_items(customer.get("reserved", recipe))
            if dish_id is not None and customer["reserved"] != recipe:
                raise BadInput(f"giữ chỗ không khớp đơn của khách {customer['id']}")
            self.ids.reserve(customer["id"])
            order_id = customer.get("order_id")
            if order_id is not None:
                if not isinstance(order_id, str) or not order_id:
                    raise BadInput("order_id phải là chuỗi khác rỗng")
                self.ids.reserve(order_id)
            customers.append(customer)
        return customers

    def available_stock(self):
        available = dict(self.stock)
        for customer in self.customers:
            for kind, amount in customer["reserved"].items():
                available[kind] = available.get(kind, 0) - amount
        return available

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        snapshot = {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }
        if self.leftover_lifetime_ticks is not None:
            snapshot["stored_dishes"] = list(self.stored_dishes)
        return snapshot

    def step(self, inp):
        """Thứ tự 8 bước theo docs/plan/phase-1-tv3-tv4.md (chờ đối chiếu mục F, clarify Q6)."""
        events = []
        # 1. đồng hồ
        self.tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        # 2. TV3: giảm kiên nhẫn, khách hết kiên nhẫn -> customer_left, nhả reserved
        self._update_customer_patience(events)
        if self.leftover_lifetime_ticks is not None:
            self._expire_leftovers(events)
        # 3. TV4: bếp đếm nấu, chín -> ready
        self._tick_stoves(events)
        # 4. TV4: khách ăn xong -> trả tiền
        self._tick_eating(events)
        # 5. di chuyển
        self._move(inp)
        # 6. TV4: tối đa MỘT interact (cạnh lên)
        if inp.pressed("interact"):
            self._interact(events)
        # 7. TV3: khách mới theo lịch, chọn món, no_dish
        self._spawn_customer(events)
        # 8. TV4: hết ca
        if self.time_left_ticks <= 0:
            self._end_shift(events)
        return events


    # --- Lát 4 (TV4): bếp, bưng, phục vụ, ăn, trả tiền, kết ca -----------------
    # Quy ước dữ liệu dùng chung với TV3: xem docs/plan/phase-1-tv3-tv4.md.
    # Những chỗ ghi "mục F" / "Qn" đang chờ PO đối chiếu (docs/clarify.md).

    def _ticks(self, seconds) -> int:
        return int(round(seconds * TICK))

    def _customer_at(self, table_id):
        for c in self.customers:
            if c.get("table_id") == table_id:
                return c
        return None

    def _tick_stoves(self, events):
        """Bếp cooking đếm ngược; về 0 -> ready (dish_ready). Bếp ready đếm ready_ticks."""
        for s in self.stoves:
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
                if s["cook_ticks_left"] == 0:
                    s["state"] = "ready"
                    s["ready_ticks"] = 0
                    # TODO(TV4, mục F mục E): đúng tên trường data của dish_ready.
                    events.append(("dish_ready", {"stove_id": s["id"], "dish_id": s["dish"],
                                                  "order_id": s.get("order_id")}))
            elif s["state"] == "ready":
                s["ready_ticks"] += 1
                # burn_s = null ở Phase 1 -> món không cháy. TODO(phase sau): cháy khi burn_s có giá trị.

    def _tick_eating(self, events):
        """Khách eating đếm thời gian ăn; ăn xong -> _pay."""
        for c in sort_by_id(list(self.customers)):
            if c.get("state") != "eating":
                continue
            # TODO(TV4, mục F): tên trường thời gian ăn còn lại (tạm: eat_ticks_left).
            c["eat_ticks_left"] = max(0, c.get("eat_ticks_left", self._ticks(self.t["eat_s"])) - 1)
            if c["eat_ticks_left"] == 0:
                self._pay(c, events)

    def _interact(self, events):
        """Chọn MỘT đối tượng trong interact_radius theo (khoảng cách, bếp trước bàn, id)."""
        r = self.t["interact_radius"]
        cands = []
        for kind_rank, objs in ((0, self.stoves), (1, self.tables)):
            for o in objs:
                d = ((o["pos"][0] - self.pos[0]) ** 2 + (o["pos"][1] - self.pos[1]) ** 2) ** 0.5
                if d <= r:  # TODO(TV4, mục F): bán kính tính cả mép (<=) như gather?
                    cands.append((d, kind_rank, o["id"], o))
        if not cands:
            return
        # TODO(TV4, mục F): chọn đối tượng gần nhất kể cả khi không làm được gì,
        #   hay chỉ xét đối tượng đang tương tác được (bếp idle có đơn, bếp ready khi tay trống, bàn đúng đơn)?
        _, kind_rank, _, target = min(cands, key=lambda c: c[:3])
        if kind_rank == 0:
            self._stove_interact(target, events)
        else:
            self._table_interact(target, events)

    def _next_order(self):
        """Đơn `waiting` cũ nhất (TV3 đang giữ nguyên liệu): order_tick nhỏ nhất, hòa thì order_id (clarify Q3)."""
        taken = {s.get("order_id") for s in self.stoves if s.get("order_id")}
        waiting = [c for c in self.customers
                   if c.get("state") == "waiting" and c.get("order_id") not in taken]
        if not waiting:
            return None
        return min(sort_by_id(waiting, key=lambda c: c.get("order_id") or ""),
                   key=lambda c: c.get("order_tick", 0))

    def _stove_interact(self, s, events):
        if self.leftover_lifetime_ticks is not None and self._interact_with_leftovers(events):
            return
        if s["state"] == "idle":
            c = self._next_order()
            if c is None:
                return
            # tiêu đúng phần đã giữ, xóa reserved trong cùng bước (thống nhất với TV3)
            for k, n in c.get("reserved", {}).items():
                self.stock[k] = self.stock.get(k, 0) - n
            c["reserved"] = {}
            # waiting -> assigned: khớp _load_customers của TV3 (chỉ đơn waiting mới giữ nguyên liệu).
            # TODO(TV4, Q1): xác nhận tên trạng thái với mục F.
            c["state"] = "assigned"
            dish = c["dish_id"]
            s.update(state="cooking", dish=dish, order_id=c.get("order_id"),
                     cook_ticks_left=self._ticks(self.menu[dish]["cook_s"]), ready_ticks=0)
            # TODO(TV4, mục E): đúng tên trường data của cook_started.
            events.append(("cook_started", {"stove_id": s["id"], "dish_id": dish,
                                            "order_id": c.get("order_id")}))
        elif s["state"] == "ready" and self.hand is None:
            # carry_limit = 1: tay trống mới bưng được.
            # TODO(TV4, mục F): định dạng `hand` trong snapshot (chuỗi mã món hay object có order_id).
            self.hand = {"dish_id": s["dish"], "order_id": s.get("order_id")}
            if self.leftover_lifetime_ticks is not None:
                self.hand["expires_at_tick"] = self.tick + self.leftover_lifetime_ticks
            events.append(("dish_picked", {"stove_id": s["id"], "dish_id": s["dish"],
                                           "order_id": s.get("order_id")}))
            s.update(state="idle", dish=None, order_id=None, cook_ticks_left=0, ready_ticks=0)

    def enable_live_leftovers(self):
        """Sáng tạo của nhóm (ADR-0001), chỉ chonoi.live gọi: bật bảo quản món thừa.

        Đổi thời gian game sang tick theo tuning.live: một ca `quan.duration_s` giây thật
        ứng với `quan_shift_game_hours` giờ game. Với 180 s / 3 giờ: 1 phút game = 1 s,
        nên 30 phút game = 30 s = 1800 tick.
        """
        live = self._tuning["live"]
        seconds_per_game_minute = self.t["duration_s"] / (live["quan_shift_game_hours"] * 60)
        self.leftover_lifetime_ticks = int(round(
            live["leftover_lifetime_game_minutes"] * seconds_per_game_minute * self._tuning["tick_hz"]))

    def _has_live_order(self, dish):
        order_id = dish.get("order_id")
        return order_id is not None and any(
            c.get("order_id") == order_id and c["state"] == "assigned" for c in self.customers
        )

    def _expire_leftovers(self, events):
        for dish in self.stored_dishes[:]:
            if self.tick >= dish["expires_at_tick"] and not self._has_live_order(dish):
                self.stored_dishes.remove(dish)
                events.append(("dish_discarded", {"dish_id": dish["dish_id"]}))
        if isinstance(self.hand, dict) and "expires_at_tick" in self.hand:
            if self.tick >= self.hand["expires_at_tick"] and not self._has_live_order(self.hand):
                events.append(("dish_discarded", {"dish_id": self.hand["dish_id"]}))
                self.hand = None

    def _interact_with_leftovers(self, events):
        if self.hand is None:
            for dish in self.stored_dishes:
                if self._has_live_order(dish):
                    self.hand = dish
                    self.stored_dishes.remove(dish)
                    events.append(("dish_picked", {"dish_id": dish["dish_id"],
                                                   "order_id": dish["order_id"]}))
                    return True
        elif isinstance(self.hand, dict) and "expires_at_tick" in self.hand and not self._has_live_order(self.hand):
            dish = self.hand
            self.hand = None
            dish["order_id"] = None
            waiting = self._next_order()
            if waiting is not None and waiting.get("dish_id") == dish["dish_id"]:
                waiting["reserved"].clear()
                waiting["state"] = "assigned"
                dish["order_id"] = waiting["order_id"]
            self.stored_dishes.append(dish)
            events.append(("dish_stored", {"dish_id": dish["dish_id"]}))
            return True
        return False

    def _table_interact(self, tb, events):
        c = self._customer_at(tb["id"])
        if c is None or self.hand is None or c.get("state") == "eating":
            return
        if self.hand.get("order_id") != c.get("order_id"):
            return  # TODO(TV4, mục F): bưng sai đơn -> bỏ qua hay phát sự kiện riêng?
        dish = c["dish_id"]
        price = self.menu[dish]["price"]
        # Gợi ý từ scenario.py: khách eating mang sẵn giá/tip -> tính boa lúc phục vụ (clarify Q4).
        c["price"] = price
        c["tip"] = self._tip(price, c)
        c["state"] = "eating"
        c["eat_ticks_left"] = self._ticks(self.t["eat_s"])
        self.hand = None
        events.append(("served", {"customer_id": c["id"], "table_id": tb["id"], "dish_id": dish,
                                  "order_id": c.get("order_id")}))

    def _tip(self, price, c) -> int:
        """Boa = floor(price * tip_rate) nếu kiên nhẫn còn >= tip_min_patience_ratio (clarify Q4)."""
        full = self._ticks(self.t["patience_s"])
        ratio = c.get("patience_ticks_left", 0) / full if full else 0
        # TODO(TV4, Q4): ngưỡng là >= hay >; floor áp vào giá trị nào.
        if ratio >= self.t["tip_min_patience_ratio"]:
            return int(price * self.t["tip_rate"] // 1)
        return 0

    def _pay(self, c, events):
        total = c.get("price", 0) + c.get("tip", 0)
        self.money += total
        self.earned += total
        self.shift_earned += total
        if c.get("tip", 0) > 0:
            # TODO(TV4, mục F): uy tín +tip_reputation chỉ khi có boa? kẹp [reputation_min, reputation_max].
            self.reputation = min(self.t["reputation_max"],
                                  max(self.t["reputation_min"], self.reputation + self.t["tip_reputation"]))
        events.append(("paid", {"customer_id": c["id"], "price": c.get("price", 0), "tip": c.get("tip", 0)}))
        self.customers.remove(c)  # TV4 xóa khách khi đã trả tiền (thống nhất với TV3)

    def _end_shift(self, events):
        # TODO(TV4, Q5): khách đang chờ / đang ăn khi hết ca: có customer_left hoặc paid trước quan_end?
        self.done = True
        self.reason = "time"
        events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                    "shift_earned": self.shift_earned, "reputation": self.reputation}))

    def _update_customer_patience(self, events):
        for customer in sort_by_id(self.customers):
            if customer["state"] not in ("waiting", "assigned"):
                continue
            customer["patience_ticks_left"] = max(0, customer["patience_ticks_left"] - 1)
            if customer["patience_ticks_left"]:
                continue
            customer["reserved"].clear()
            self.customers.remove(customer)
            self.reputation = max(self.t["reputation_min"],
                                  self.reputation + self.t["left_reputation_delta"])
            events.append(("customer_left", {"customer_id": customer["id"],
                                             "order_id": customer.get("order_id"),
                                             "table_id": customer["table_id"]}))

    def _spawn_customer(self, events):
        elapsed = self.tick - self.t["first_customer_tick"]
        if not self.random_customers or elapsed < 0 or elapsed % self.customer_interval_ticks:
            return
        occupied = {customer["table_id"] for customer in self.customers}
        table = next((table for table in self.tables if table["id"] not in occupied), None)
        if table is None:
            return
        available = self.available_stock()
        reusable = {dish["dish_id"]: dish for dish in reversed(self.stored_dishes)
                    if not self._has_live_order(dish)}
        dishes = [dish_id for dish_id in self.orderable_dishes
                  if dish_id in reusable
                  or all(available.get(kind, 0) >= amount
                         for kind, amount in self.menu[dish_id]["recipe"].items())]
        if not dishes:
            events.append(("no_dish", {"table_id": table["id"]}))
            return
        dish_id = self.rng.get("customer_menu").choice(dishes)
        customer = {
            "id": self.ids.new("C"),
            "table_id": table["id"],
            "dish_id": dish_id,
            "order_id": self.ids.new("O"),
            "order_tick": self.tick,
            "state": "waiting",
            "patience_ticks_left": self.patience_ticks,
            "reserved": dict(self.menu[dish_id]["recipe"]),
        }
        if dish_id in reusable:
            reusable[dish_id]["order_id"] = customer["order_id"]
            customer["state"] = "assigned"
            customer["reserved"] = {}
        self.customers.append(customer)
        events.append(("customer_arrived", {"customer_id": customer["id"],
                                            "table_id": customer["table_id"],
                                            "order_id": customer["order_id"],
                                            "dish_id": dish_id}))

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
