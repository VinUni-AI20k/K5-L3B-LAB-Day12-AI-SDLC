"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Phần việc của nhóm:
  - TODO(TV3, lát 3): Khách đến theo lịch (first_customer_tick, customer_interval_s),
                      chọn món theo seed trong 3 món đủ nguyên liệu khả dụng,
                      tạo đơn reserved, no_dish khi thiếu món.
  - ĐÃ HOÀN THÀNH (TV4 - AnhQuanHANU, lát 4): Bếp nấu, lấy món lên tay, bưng phục vụ tại bàn,
                      chốt boa, ăn xong thanh toán, cộng uy tín, dọn dẹp khi khách rời và kết ca.
"""

import math

from ..ids import id_key, sort_by_id
from ..errors import BadInput
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

        # Kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))

        # Hand: payload món {order_id, dish_id, base_price} hoặc None
        raw_hand = scenario.get("hand")
        if isinstance(raw_hand, dict):
            self.hand = dict(raw_hand)
        elif isinstance(raw_hand, str):
            self.hand = {
                "order_id": "C1",
                "dish_id": raw_hand,
                "base_price": self.menu.get(raw_hand, {}).get("price", 0)
            }
        else:
            self.hand = None

        self.burn_s = self.t.get("burn_s")
        self.burn_ticks = int(round(self.burn_s * TICK)) if self.burn_s is not None else None

        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))

        # Bếp (stoves)
        self.stoves = [
            dict(
                s,
                state=s.get("state", "idle"),
                dish=s.get("dish"),
                order_id=s.get("order_id"),
                base_price=s.get("base_price"),
                cook_ticks_left=s.get("cook_ticks_left", 0),
                ready_ticks=s.get("ready_ticks", 0)
            )
            for s in self._merge(t["stoves"], scenario.get("stoves", []))
        ]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        for stove in self.stoves:
            payload = stove["dish"]
            if isinstance(payload, dict):
                if set(payload) != {"dish_id", "order_id", "base_price"}:
                    raise BadInput("payload món ở bếp thiếu hoặc thừa trường")
                stove.update(dish=payload["dish_id"], order_id=payload["order_id"], base_price=payload["base_price"])

        # Khách (customers)
        patience_max = int(round(t["patience_s"] * TICK))
        self.customers = []
        for c in scenario.get("customers", []):
            dish_id = c.get("dish_id")
            base_price = c.get("base_price")
            if base_price is None and dish_id and dish_id in self.menu:
                base_price = self.menu[dish_id]["price"]

            cust = {
                "id": c["id"],
                "table_id": c["table_id"],
                "dish_id": dish_id,
                "order_tick": c.get("order_tick", 0),
                "state": c.get("state", "waiting"),
                "patience_ticks_left": c.get("patience_ticks_left", patience_max),
                "eat_ticks_left": c.get("eat_ticks_left", 0),
                "order_status": c.get("order_status", "reserved"),
                "reserved": dict(c.get("reserved", {})),
                "base_price": base_price if base_price is not None else 0,
                "tip": c.get("tip", 0),
            }
            # Thiếu reserved ở đơn reserved thì cấp theo công thức món
            if cust["order_status"] == "reserved" and not cust["reserved"] and dish_id and dish_id in self.menu:
                cust["reserved"] = dict(self.menu[dish_id]["recipe"])
            self.customers.append(cust)
            ids.reserve(c["id"])

        # Đồng bộ order_id/base_price cho bếp đang cooking/ready từ scenario
        for s in self.stoves:
            if s["dish"] and not s.get("order_id"):
                for c in self.customers:
                    if c.get("dish_id") == s["dish"] and c.get("order_status") in ("assigned", "served"):
                        s["order_id"] = c["id"]
                        s["base_price"] = c.get("base_price", self.menu[s["dish"]]["price"])
                        break

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
            "stoves": [
                {k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                for s in sort_by_id(self.stoves)
            ],
            "tables": [
                {"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])}
                for tb in sort_by_id(self.tables)
            ],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []

        # 1. Tăng đồng hồ, giảm timer ca, nấu, ăn và kiên nhẫn. Chỉ tăng ready_ticks cho món đã ready ở đầu bước.
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        ready_at_start = {s["id"] for s in self.stoves if s["state"] == "ready"}
        for s in self.stoves:
            if s["id"] in ready_at_start:
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] -= 1

        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            elif c["state"] == "waiting":
                # Giảm thời gian kiên nhẫn
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)

        # 2. Xét bếp theo id. Món nấu xong chuyển ready với ready_ticks = 0.
        #    Nếu bật mở rộng cháy món (burn_s): kiểm tra món cháy khi ready_ticks > burn_ticks.
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking" and s["cook_ticks_left"] <= 0:
                s["state"] = "ready"
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0
                events.append((
                    "dish_ready",
                    {"stove_id": s["id"], "order_id": s["order_id"], "dish_id": s["dish"]}
                ))
            elif s["state"] == "ready" and self.burn_ticks is not None and s["ready_ticks"] > self.burn_ticks:
                self._handle_dish_burnt(s, events)

        # 3. Di chuyển người chơi
        self._move(inp)

        # 4. Xét tối đa MỘT interact (chọn theo khoảng cách, bếp trước bàn, id)
        if inp.pressed("interact"):
            self._handle_interact(events)

        # 5. Theo id bàn, khách ăn xong trả tiền rồi rời bàn ngay.
        #    Xử lý kiên nhẫn = 0 khi còn giờ hoặc thanh toán dứt điểm khi hết ca.
        self._process_customers_and_closing(events)

        # 6. TODO(TV3, Lát 3): Xét lượt khách mới theo lịch (first_customer_tick, customer_interval_s)
        #    - Kiểm tra bàn trống, chọn bàn id nhỏ nhất
        #    - Chọn đều theo seed trong các món đủ nguyên liệu (tồn vật lý trừ phần giữ)
        #    - Nếu không có món đủ phát no_dish
        #    - Khách mới giữ đúng công thức ngay, order_tick = phase_tick hiện tại.

        return events

    # --- Các hàm xử lý tương tác của TV4 (Bếp, Phục vụ, Thanh toán) ---

    def _handle_interact(self, events):
        """Xét tối đa MỘT interact, ưu tiên (khoảng cách, bếp trước bàn, id). Bỏ lượt nếu không tương tác được."""
        radius = float(self.t["interact_radius"])
        candidates = []

        # Ứng viên Bếp (ưu tiên loại 0)
        for s in sort_by_id(self.stoves):
            d = math.dist(self.pos, s["pos"])
            if d <= radius:
                candidates.append((d, 0, id_key(s["id"]), "stove", s))

        # Ứng viên Bàn (ưu tiên loại 1)
        for tb in sort_by_id(self.tables):
            d = math.dist(self.pos, tb["pos"])
            if d <= radius:
                candidates.append((d, 1, id_key(tb["id"]), "table", tb))

        if not candidates:
            return

        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        best = candidates[0]
        target_type, target = best[3], best[4]

        if target_type == "stove":
            self._interact_stove(target, events)
        elif target_type == "table":
            self._interact_table(target, events)

    def _interact_stove(self, stove, events):
        """Tương tác với bếp: Bắt đầu nấu nếu idle, lấy món lên tay nếu ready."""
        # Bếp idle: lấy đơn reserved cũ nhất theo order_tick rồi id bàn
        if stove["state"] == "idle":
            reserved_candidates = [
                c for c in self.customers
                if c.get("order_status") == "reserved" and c.get("state") == "waiting"
            ]
            if not reserved_candidates:
                return

            # Sắp theo order_tick cũ nhất, rồi id bàn
            reserved_candidates.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))
            target_cust = reserved_candidates[0]
            dish_id = target_cust["dish_id"]
            if not dish_id or dish_id not in self.menu:
                return

            recipe = self.menu[dish_id]["recipe"]

            # Tiêu đúng nguyên liệu giữ trong kho
            for kind, qty in recipe.items():
                self.stock[kind] = self.stock.get(kind, 0) - qty
                if self.stock[kind] <= 0:
                    del self.stock[kind]

            target_cust["reserved"] = {}
            target_cust["order_status"] = "assigned"
            base_price = target_cust.get("base_price", self.menu[dish_id]["price"])

            stove["state"] = "cooking"
            stove["dish"] = dish_id
            stove["order_id"] = target_cust["id"]
            stove["base_price"] = base_price
            stove["cook_ticks_left"] = int(round(self.menu[dish_id]["cook_s"] * TICK))
            stove["ready_ticks"] = 0

            # Danh sách items tiêu thụ theo thứ tự alphabet của kind
            items = []
            for kind in sorted(recipe.keys()):
                items.extend([kind] * recipe[kind])

            events.append((
                "cook_started",
                {
                    "stove_id": stove["id"],
                    "order_id": target_cust["id"],
                    "dish_id": dish_id,
                    "items": items,
                    "base_price": base_price
                }
            ))

        # Bếp ready: giao món cho tay trống và về idle
        elif stove["state"] == "ready":
            if self.hand is None:
                self.hand = {
                    "order_id": stove["order_id"],
                    "dish_id": stove["dish"],
                    "base_price": stove["base_price"]
                }
                events.append((
                    "dish_picked",
                    {
                        "stove_id": stove["id"],
                        "order_id": stove["order_id"],
                        "dish_id": stove["dish"]
                    }
                ))
                stove["state"] = "idle"
                stove["dish"] = None
                stove["order_id"] = None
                stove["base_price"] = None
                stove["cook_ticks_left"] = 0
                stove["ready_ticks"] = 0

    def _handle_dish_burnt(self, stove, events):
        """Mở rộng Cháy món (burn): khi ready_ticks > burn_ticks, bỏ món, bếp rảnh ngay, thử giữ lại nguyên liệu."""
        dish_id = stove["dish"]
        order_id = stove["order_id"]
        new_status = "unfulfillable"

        # Tìm khách tương ứng với đơn bị cháy
        cust = next((c for c in self.customers if c["id"] == order_id), None)
        if cust and dish_id and dish_id in self.menu:
            recipe = self.menu[dish_id]["recipe"]
            # Tính tồn kho khả dụng (tồn kho vật lý trừ phần giữ của các khách khác)
            available_stock = dict(self.stock)
            for other in self.customers:
                if other["id"] != cust["id"] and other.get("reserved"):
                    for rk, rq in other["reserved"].items():
                        available_stock[rk] = available_stock.get(rk, 0) - rq

            can_reserve = all(available_stock.get(k, 0) >= qty for k, qty in recipe.items())
            if can_reserve:
                cust["order_status"] = "reserved"
                cust["reserved"] = dict(recipe)
                new_status = "reserved"
            else:
                cust["order_status"] = "unfulfillable"
                cust["reserved"] = {}
                new_status = "unfulfillable"

        # Bếp rảnh ngay, nguyên liệu đã nấu bị mất
        stove["state"] = "idle"
        stove["dish"] = None
        stove["order_id"] = None
        stove["base_price"] = None
        stove["cook_ticks_left"] = 0
        stove["ready_ticks"] = 0

        events.append((
            "dish_burnt",
            {
                "stove_id": stove["id"],
                "order_id": order_id,
                "dish_id": dish_id,
                "order_status": new_status
            }
        ))

    def _interact_table(self, table, events):
        """Tương tác với bàn: Giao món đúng order_id, chốt boa và khách bắt đầu ăn."""
        if not self.hand:
            return

        cust = next((c for c in self.customers if c["table_id"] == table["id"]), None)
        if not cust:
            return

        # Bàn nhận đúng order_id thì khách ăn với timer đầy
        if self.hand.get("order_id") == cust["id"]:
            cust["state"] = "eating"
            cust["order_status"] = "served"
            cust["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))

            # Chốt boa bằng floor(tiền món × tip_rate) nếu tỷ lệ kiên nhẫn còn lại đạt tip_min_patience_ratio
            total_patience = int(round(self.t["patience_s"] * TICK))
            patience_ratio = (cust["patience_ticks_left"] / total_patience) if total_patience > 0 else 0.0

            if patience_ratio >= self.t["tip_min_patience_ratio"]:
                tip = math.floor(cust["base_price"] * self.t["tip_rate"])
            else:
                tip = 0
            cust["tip"] = tip

            events.append((
                "served",
                {
                    "order_id": cust["id"],
                    "table_id": table["id"],
                    "dish_id": cust["dish_id"],
                    "patience_ticks_left": cust["patience_ticks_left"],
                    "base_price": cust["base_price"],
                    "tip": tip
                }
            ))

            # Tay đã trao món xong
            self.hand = None

    def _process_customers_and_closing(self, events):
        """Xử lý thanh toán khi ăn xong, khách hết kiên nhẫn bỏ về, hoặc hết ca."""
        # 1. Khi ca mở quán còn thời gian
        if self.time_left_ticks > 0:
            remaining_customers = []
            for c in sorted(self.customers, key=lambda x: id_key(x["table_id"])):
                # Khách ăn xong -> trả tiền
                if c["state"] == "eating" and c["eat_ticks_left"] <= 0:
                    base_price = c["base_price"]
                    tip = c.get("tip", 0)
                    amount = base_price + tip

                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount

                    if tip > 0:
                        self.reputation = min(
                            float(self.t["reputation_max"]),
                            round(self.reputation + float(self.t["tip_reputation"]), 3)
                        )

                    events.append((
                        "paid",
                        {
                            "order_id": c["id"],
                            "table_id": c["table_id"],
                            "base_price": base_price,
                            "tip": tip,
                            "amount": amount,
                            "reason": "finished_eating"
                        }
                    ))
                # Khách waiting có kiên nhẫn về 0 -> bỏ quán
                elif c["state"] == "waiting" and c["patience_ticks_left"] <= 0:
                    self.reputation = max(
                        float(self.t["reputation_min"]),
                        round(self.reputation + float(self.t["left_reputation_delta"]), 3)
                    )
                    events.append((
                        "customer_left",
                        {
                            "order_id": c["id"],
                            "table_id": c["table_id"],
                            "reason": "patience",
                            "reputation": self.reputation
                        }
                    ))
                    self._cleanup_customer_order(c["id"])
                else:
                    remaining_customers.append(c)

            self.customers = remaining_customers

        # 2. Khi hết ca (time_left_ticks <= 0)
        else:
            for c in sorted(self.customers, key=lambda x: id_key(x["table_id"])):
                # Khách còn ăn trả ngay (kể cả vừa được giao món)
                if c["state"] == "eating":
                    base_price = c["base_price"]
                    tip = c.get("tip", 0)
                    amount = base_price + tip

                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount

                    if tip > 0:
                        self.reputation = min(
                            float(self.t["reputation_max"]),
                            round(self.reputation + float(self.t["tip_reputation"]), 3)
                        )

                    events.append((
                        "paid",
                        {
                            "order_id": c["id"],
                            "table_id": c["table_id"],
                            "base_price": base_price,
                            "tip": tip,
                            "amount": amount,
                            "reason": "closing"
                        }
                    ))
                # Khách còn chờ rời với closing và không trừ uy tín
                elif c["state"] == "waiting":
                    events.append((
                        "customer_left",
                        {
                            "order_id": c["id"],
                            "table_id": c["table_id"],
                            "reason": "closing",
                            "reputation": self.reputation
                        }
                    ))
                    self._cleanup_customer_order(c["id"])

            self.customers = []

            # Dọn món đang nấu dở ở bếp hoặc trên tay
            self.hand = None
            for s in self.stoves:
                s["state"] = "idle"
                s["dish"] = None
                s["order_id"] = None
                s["base_price"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0

            self.done = True
            self.reason = "time"
            events.append((
                "quan_end",
                {
                    "reason": "time",
                    "money": self.money,
                    "earned": self.earned,
                    "shift_earned": self.shift_earned,
                    "reputation": self.reputation
                }
            ))

    def _cleanup_customer_order(self, order_id):
        """Khi khách rời: bỏ món của đơn đang nấu, ready hoặc trên tay. Nguyên liệu đã dùng không hoàn lại."""
        if self.hand and self.hand.get("order_id") == order_id:
            self.hand = None

        for s in self.stoves:
            if s.get("order_id") == order_id:
                s["state"] = "idle"
                s["dish"] = None
                s["order_id"] = None
                s["base_price"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0

    def _move(self, inp):
        """Di chuyển người chơi trong quán ăn."""
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
