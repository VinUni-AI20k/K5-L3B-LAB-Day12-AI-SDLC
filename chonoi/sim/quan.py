"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Thứ tự một bước theo PRD-0 mục F (Quán), xem step():
  1. đồng hồ, kiên nhẫn (lát 3), nấu / ăn / ready_ticks + món chín (lát 4)
  2. di chuyển rồi tối đa MỘT interact (lát 4)
  3. theo id bàn: ăn xong trả tiền (lát 4), hết kiên nhẫn rời bàn (lát 3); hết ca thì đóng ca
  4. còn giờ thì xét lượt khách mới (lát 3)

Lát 3 (đã làm): khách theo lịch, chọn món đủ nguyên liệu khả dụng, giữ chỗ, kiên nhẫn,
  customer_left (patience/closing), no_dish, dựng khách từ scenario và suy ra giữ chỗ.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid) trong _pay, boa, uy tín.
"""

import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

sort_key_table = id_key  # sắp bàn theo id (T2 trước T10)

TICK = 60.0
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
                 "order_status", "reserved", "base_price", "tip"}
CUSTOMER_STATES = ("waiting", "eating")
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, allowed_dishes=None, carry=None):
        t = tuning["quan"]
        self.t = t
        self.tuning = tuning  # Phase 3: dùng chung cấu hình freshness qua chonoi.items
        self.freshness = tuning.get("freshness")  # None ở v1.1, không đổi luật Phase 2
        self.menu = tuning["menu"]
        # món khách được gọi: cả menu (quán độc lập) hoặc món trong kế hoạch Ngày (mode day, Phase 2)
        self.allowed_dishes = sorted(allowed_dishes if allowed_dishes is not None else self.menu)
        self.patience_full = int(round(t["patience_s"] * TICK))
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        source_stock = inventory if inventory is not None else scenario.get(
            "stock", [] if self.freshness is not None else {})
        if self.freshness is not None:
            # Contract v1.2: kho là mảng cá thể, không được ép dict (mất id/độ tươi).
            # Validator ở lát 0 từ chối schema đếm cũ trước khi tạo sim.
            self.stock = sort_by_id([dict(item) for item in source_stock])
            for item in self.stock:
                ids.reserve(item["id"])
        else:
            self.stock = dict(source_stock)
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = self._init_customers(scenario.get("customers", []))
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        if carry is not None:  # mode day: tiền, earned, uy tín giữ qua Ngày (Ticket-02 mục 2)
            self.money, self.earned, self.reputation = carry["money"], carry["earned"], carry["reputation"]
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
            "stock": ([dict(item) for item in sort_by_id(self.stock)] if self.freshness is not None
                      else {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}),
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        # 1. đồng hồ + timer. Lịch khách dùng phase_tick SAU khi tăng.
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._tick_patience()                 # lát 3
        if self.freshness is not None:
            self._tick_freshness(events)      # lát 4, v1.2: cả hàng giữ chỗ vẫn hao
            # Lát 3 sở hữu _retry_spoiled: phải merge trước khi chạy v1.2 tích hợp.
            retry = getattr(self, "_retry_spoiled", None)
            if retry is None and self.customers:
                raise BadInput("v1.2 cần Lát 3 triển khai _retry_spoiled trước khi chạy Quán")
            if retry is not None:
                retry(events)
        self._tick_stoves_and_eating(events)  # lát 4: nấu, ăn, ready_ticks, món chín -> dish_ready
        # 2. di chuyển rồi tối đa MỘT interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)            # lát 4
        # 3. theo id bàn: trả tiền / rời bàn; hết ca thì đóng ca và dừng
        self._settle_customers(events)        # lát 3 (gọi _pay của lát 4)
        if self.time_left_ticks <= 0:
            self._close_shift(events)
            return events
        # 4. lượt khách mới
        self._spawn_customers(events)         # lát 3
        return events

    # --- lát 3 (sở hữu: người làm quán lát 3) ------------------------------------
    def _init_customers(self, src):
        """Dựng khách từ scenario (PRD-0 mục D). Mặc định: waiting, order_tick 0, kiên nhẫn đầy, order_status
        reserved. Đơn reserved thiếu `reserved` được cấp theo công thức, xét theo (order_tick, id bàn).
        Mâu thuẫn (món lạ, giữ khác công thức, giữ quá tồn...) -> BadInput (mã 2)."""
        table_ids = {tb["id"] for tb in self.tables}
        out = []
        for c in src:
            extra = set(c) - CUSTOMER_KEYS
            if extra:
                raise BadInput(f"customers.{c['id']}: trường lạ/chưa hỗ trợ {sorted(extra)}")
            if c.get("dish_id") not in self.menu:
                raise BadInput(f"customers.{c['id']}: dish_id phải là món trong menu")
            if c["table_id"] not in table_ids:
                raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
            cu = {"id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                  "order_tick": c.get("order_tick", 0), "state": c.get("state", "waiting"),
                  "patience_ticks_left": c.get("patience_ticks_left", self.patience_full),
                  "eat_ticks_left": c.get("eat_ticks_left", 0), "order_status": c.get("order_status", "reserved"),
                  "reserved": c.get("reserved"), "base_price": c.get("base_price"), "tip": c.get("tip")}
            for key in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
                v = cu[key]
                if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                    raise BadInput(f"customers.{c['id']}.{key} phải là số nguyên không âm")
            if cu["patience_ticks_left"] > self.patience_full:
                raise BadInput(f"customers.{c['id']}.patience_ticks_left vượt kiên nhẫn tối đa")
            if cu["state"] not in CUSTOMER_STATES or cu["order_status"] not in ORDER_STATUSES:
                raise BadInput(f"customers.{c['id']}: state/order_status không hợp lệ")
            if cu["reserved"] is not None and (not isinstance(cu["reserved"], dict) or any(
                    isinstance(n, bool) or not isinstance(n, int) or n < 0 for n in cu["reserved"].values())):
                raise BadInput(f"customers.{c['id']}.reserved phải là map kind -> số nguyên không âm")
            recipe = self.menu[cu["dish_id"]]["recipe"]
            if cu["order_status"] == "reserved":
                if cu["reserved"] is not None and cu["reserved"] != recipe:
                    raise BadInput(f"customers.{c['id']}: phần giữ khác công thức món")
            elif cu["reserved"]:
                raise BadInput(f"customers.{c['id']}: đơn {cu['order_status']} phải có phần giữ rỗng")
            out.append(cu)
        # cấp phần giữ còn thiếu theo (order_tick, id bàn), rồi kiểm tổng giữ không vượt tồn
        for cu in sorted(out, key=lambda x: (x["order_tick"], *sort_key_table(x["table_id"]))):
            if cu["reserved"] is None:
                cu["reserved"] = dict(self.menu[cu["dish_id"]]["recipe"]) if cu["order_status"] == "reserved" else {}
        self.customers = out
        if any(n < 0 for n in self._available().values()):
            raise BadInput("customers: tổng nguyên liệu giữ chỗ vượt tồn kho")
        return out

    def _tick_patience(self):
        """Bước 1: khách đang chờ (chưa được giao món) mất 1 tick kiên nhẫn, kẹp 0."""
        for c in self.customers:
            if c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)

    def _settle_customers(self, events):
        """Bước 3, theo id bàn: ăn xong -> trả tiền (lát 4, _pay); nếu ca còn giờ, đang chờ mà kiên nhẫn 0
        -> rời bàn (patience) và uy tín += left_reputation_delta. Hết ca thì _close_shift lo phần còn lại."""
        for c in self._by_table():
            if c["state"] == "eating" and c["eat_ticks_left"] == 0:
                self._pay(c, "finished_eating", events)
            elif c["state"] == "waiting" and c["patience_ticks_left"] == 0 and self.time_left_ticks > 0:
                self._change_reputation(self.t["left_reputation_delta"])
                self._leave(c, "patience", events)

    def _close_shift(self, events):
        """Hết ca, theo id bàn: khách còn ăn trả ngay (lát 4, _pay), khách còn chờ rời với closing,
        không trừ uy tín. Dọn xong phát quan_end."""
        for c in self._by_table():
            if c["state"] == "eating":
                self._pay(c, "closing", events)
            else:
                self._leave(c, "closing", events)
        self.done = True
        self.reason = "time"
        events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                    "shift_earned": self.shift_earned, "reputation": self.reputation}))

    def _spawn_customers(self, events):
        """Bước 4 (ca còn giờ): lượt khách ở first_customer_tick rồi mỗi customer_interval_s × 60 tick.
        Không còn bàn -> bỏ lượt. Có bàn -> bàn trống id nhỏ nhất; chọn đều theo seed trong các món đủ
        nguyên liệu khả dụng (tồn trừ giữ chỗ); không có món -> no_dish. Khách mới giữ đúng công thức ngay."""
        if not self.random_customers or not self._customer_turn():
            return
        seated = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in self.tables if tb["id"] not in seated]  # self.tables đã sắp theo id
        if not free_tables:
            return
        avail = self._available()
        dishes = [d for d in self.allowed_dishes
                  if all(avail.get(k, 0) >= n for k, n in self.menu[d]["recipe"].items())]
        if not dishes:
            events.append(("no_dish", {}))
            return
        dish = dishes[self.rng.get("customer_dish").randrange(len(dishes))]
        table = free_tables[0]
        c = {"id": self.ids.new("C"), "table_id": table["id"], "dish_id": dish, "order_tick": self.phase_tick,
             "state": "waiting", "patience_ticks_left": self.patience_full, "eat_ticks_left": 0,
             "order_status": "reserved", "reserved": {}, "base_price": None, "tip": None}
        self._reserve(c, dish)
        self.customers.append(c)
        events.append(("customer_arrived", {"order_id": c["id"], "table_id": table["id"], "dish_id": dish}))

    def _customer_turn(self) -> bool:
        first = self.t["first_customer_tick"]
        interval = int(round(self.t["customer_interval_s"] * TICK))
        return self.phase_tick >= first and (self.phase_tick - first) % interval == 0

    def _by_table(self):
        return sorted(self.customers, key=lambda c: sort_key_table(c["table_id"]))

    def _leave(self, c, reason, events):
        """Khách rời bàn: nhả phần giữ thô, bỏ món của đơn đang nấu / ready / trên tay
        (nguyên liệu đã dùng không hoàn lại), phát customer_left."""
        self._release(c)
        for s in self.stoves:
            if isinstance(s.get("dish"), dict) and s["dish"].get("order_id") == c["id"]:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if isinstance(self.hand, dict) and self.hand.get("order_id") == c["id"]:
            self.hand = None
        self.customers.remove(c)
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
                                         "reputation": self.reputation}))

    # --- lát 4 (sở hữu: người làm quán lát 4) ------------------------------------
    def _tick_freshness(self, events):
        """P3-11: kho quán hao trước giữ lại/nấu; hàng đã giữ chỗ vẫn nằm trong stock.

        Chỉ dùng hàm decay dùng chung của lát 0 (chonoi.items); không tự làm tròn
        độ tươi và không phát spoiled lần thứ hai cho hàng đã ươn.
        """
        if self.freshness is None:
            return
        from ..items import decay

        per_tick = self.freshness["quan_decay_per_s"] / TICK
        newly_spoiled = decay(self.stock, per_tick, self.tuning)
        for item in sort_by_id(newly_spoiled):
            events.append(("spoiled", {"item_id": item["id"], "kind": item["kind"],
                                       "location": "stock"}))

    def _reserve_after_burn(self, customer):
        """P3-15: món cháy đã mất nguyên liệu; thử giữ lại TOÀN BỘ công thức đúng một lần.

        Hai bếp cùng cháy được xử lý theo id bếp; đơn đầu giữ trước, đơn sau
        không được dùng trùng id. Chỉ áp dụng kho cá thể v1.2.
        """
        from ..items import pick_freshest

        occupied = {ident for other in self.customers for ident in other.get("reserved", [])}
        chosen = []
        recipe = self.menu[customer["dish_id"]]["recipe"]
        for kind, count in sorted(recipe.items()):
            matches = pick_freshest(self.stock, kind, count, occupied | set(chosen), self.tuning)
            if matches is None:
                customer["reserved"] = []
                customer["order_status"] = "unfulfillable"
                return
            chosen.extend(matches)
        customer["reserved"] = sorted(chosen, key=id_key)
        customer["order_status"] = "reserved"

    def _tick_stoves_and_eating(self, events):
        """Bước 1: giảm timer, ready ở đầu bước mới tăng tuổi; xử lý theo id bếp."""
        burn_s = self.t.get("burn_s")
        burn_ticks = int(round(burn_s * TICK)) if burn_s is not None else None
        for stove in sort_by_id(self.stoves):
            if stove["state"] == "cooking":
                stove["cook_ticks_left"] = max(0, stove["cook_ticks_left"] - 1)
                if stove["cook_ticks_left"] == 0:
                    stove["state"] = "ready"
                    stove["ready_ticks"] = 0
                    dish = stove["dish"]
                    events.append(("dish_ready", {"stove_id": stove["id"],
                                                  "order_id": dish["order_id"], "dish_id": dish["dish_id"]}))
            elif stove["state"] == "ready":
                stove["ready_ticks"] += 1
                if burn_ticks is not None and stove["ready_ticks"] > burn_ticks:
                    dish = stove["dish"]
                    stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
                    customer = next((c for c in self.customers if c["id"] == dish["order_id"]), None)
                    status = "unfulfillable"
                    if customer is not None:
                        if self.freshness is not None:
                            self._reserve_after_burn(customer)
                        else:
                            recipe = self.menu[customer["dish_id"]]["recipe"]
                            available = self._available()
                            if all(available.get(k, 0) >= n for k, n in recipe.items()):
                                self._reserve(customer, customer["dish_id"])
                                customer["order_status"] = "reserved"
                            else:
                                customer["reserved"] = {}
                                customer["order_status"] = "unfulfillable"
                        customer["base_price"] = None
                        customer["tip"] = None
                        status = customer["order_status"]
                    events.append(("dish_burnt", {"stove_id": stove["id"],
                                                   "order_id": dish["order_id"],
                                                   "dish_id": dish["dish_id"],
                                                   "order_status": status}))
        for customer in self.customers:
            if customer["state"] == "eating":
                customer["eat_ticks_left"] = max(0, customer["eat_ticks_left"] - 1)

    def _pay(self, c, reason, events):
        """Bước 3: trả tiền món + boa, cập nhật uy tín rồi dọn bàn."""
        base_price, tip = c["base_price"], c["tip"]
        amount = base_price + tip
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if tip > 0:
            self._change_reputation(self.t["tip_reputation"])
        events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"],
                                "base_price": base_price, "tip": tip, "amount": amount,
                                "reason": reason}))
        self.customers.remove(c)

    def _interact(self, events):
        """Bước 2: chọn MỘT đối tượng gần nhất, bếp trước bàn rồi id khi hòa."""
        radius_sq = self.t["interact_radius"] ** 2
        nearby = []
        for stove in self.stoves:
            dist_sq = sum((a - b) ** 2 for a, b in zip(self.pos, stove["pos"]))
            if dist_sq <= radius_sq + 1e-12:
                nearby.append((dist_sq, 0, id_key(stove["id"]), stove))
        for table in self.tables:
            dist_sq = sum((a - b) ** 2 for a, b in zip(self.pos, table["pos"]))
            if dist_sq <= radius_sq + 1e-12:
                nearby.append((dist_sq, 1, id_key(table["id"]), table))
        if not nearby:
            return
        _, kind, _, target = min(nearby, key=lambda candidate: candidate[:3])
        if kind == 0:
            stove = target
            if stove["state"] == "idle":
                pending = [c for c in self.customers if c["state"] == "waiting"
                           and c["order_status"] == "reserved"]
                if not pending:
                    return
                c = min(pending, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
                if self.freshness is not None:
                    from ..items import is_spoiled

                    # Lát 3 giữ id, lát 4 chỉ tiêu đúng id đó. Không chọn lại
                    # nguyên liệu vào phút cuối hay nhận hàng đã ươn.
                    reserved_ids = c["reserved"]
                    indexed = {item["id"]: item for item in self.stock}
                    selected = [indexed[ident] for ident in reserved_ids if ident in indexed]
                    recipe = self.menu[c["dish_id"]]["recipe"]
                    amounts = {}
                    for item in selected:
                        amounts[item["kind"]] = amounts.get(item["kind"], 0) + 1
                    if (len(selected) != len(reserved_ids) or len(set(reserved_ids)) != len(reserved_ids)
                            or amounts != recipe or any(is_spoiled(item, self.tuning) for item in selected)):
                        return  # lát 3 _retry_spoiled xử lý phần giữ không còn dùng được
                    items = [dict(item) for item in sort_by_id(selected)]
                    used = set(reserved_ids)
                    self.stock = [item for item in self.stock if item["id"] not in used]
                    c["reserved"] = []
                    c["base_price"] = math.floor(
                        self.menu[c["dish_id"]]["price"] *
                        (sum(item["fresh"] for item in selected) / len(selected)) / 100)
                else:
                    items = sorted(k for k, count in c["reserved"].items() for _ in range(count))
                    for ingredient, amount in c["reserved"].items():
                        self.stock[ingredient] -= amount
                    self._release(c)
                    c["base_price"] = self.menu[c["dish_id"]]["price"]
                c["order_status"] = "assigned"
                stove.update(state="cooking", dish={"order_id": c["id"],
                            "dish_id": c["dish_id"], "base_price": c["base_price"]},
                            cook_ticks_left=int(round(self.menu[c["dish_id"]]["cook_s"] * TICK)),
                            ready_ticks=0)
                events.append(("cook_started", {"stove_id": stove["id"], "order_id": c["id"],
                                                "dish_id": c["dish_id"], "items": items,
                                                "base_price": c["base_price"]}))
            elif stove["state"] == "ready" and self.hand is None:
                self.hand = dict(stove["dish"])
                stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
                events.append(("dish_picked", {"stove_id": stove["id"],
                                               "order_id": self.hand["order_id"],
                                               "dish_id": self.hand["dish_id"]}))
        else:
            table = target
            c = next((c for c in self.customers if c["table_id"] == table["id"]), None)
            if (not isinstance(self.hand, dict) or c is None or c["state"] != "waiting"
                    or c["order_status"] != "assigned" or self.hand["order_id"] != c["id"]
                    or self.hand["dish_id"] != c["dish_id"]):
                return
            c["state"] = "eating"
            c["order_status"] = "served"
            c["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
            c["base_price"] = self.hand["base_price"]
            threshold = self.t["tip_min_patience_ratio"] * self.patience_full
            c["tip"] = (math.floor(c["base_price"] * self.t["tip_rate"])
                        if c["patience_ticks_left"] >= threshold else 0)
            self.hand = None
            events.append(("served", {"order_id": c["id"], "table_id": c["table_id"],
                                      "dish_id": c["dish_id"],
                                      "patience_ticks_left": c["patience_ticks_left"],
                                      "base_price": c["base_price"], "tip": c["tip"]}))

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
