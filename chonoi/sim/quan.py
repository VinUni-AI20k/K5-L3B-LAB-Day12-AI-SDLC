"""Buổi tối — Mở Quán (`quan`), theo PRD-0 mục D, E, F (Phase 1).

Mặt bằng nhìn từ trên xuống: vị trí `[x, z]`. Một bước (tick) xử lý đúng thứ tự PRD-0 mục F "Quán":
  1. Đồng hồ: giảm giờ ca, kiên nhẫn khách đang chờ, thời gian nấu, thời gian ăn;
     tăng `ready_ticks` cho món đã ready từ đầu bước.
  2. Xét bếp theo id: nấu xong -> ready (`dish_ready`, ready_ticks = 0). `burn_s: null` -> không cháy.
  3. Di chuyển rồi tối đa MỘT interact, chọn đối tượng theo (khoảng cách, bếp trước bàn, id).
     Đối tượng được chọn mà không tương tác được thì bỏ lượt (không thử đối tượng khác).
  4. Xét khách theo id bàn: ăn xong trả tiền; còn giờ mà khách chờ hết kiên nhẫn thì bỏ đi;
     hết ca thì khách đang ăn trả ngay, khách đang chờ rời với `closing`, rồi phát `quan_end`.
  5. Còn giờ: khách mới theo lịch `first_customer_tick` + k * `customer_interval_s`.

Mô hình đơn (order_id = id khách):
  reserved      -> nguyên liệu đang giữ trong kho (stock vẫn tính cả phần giữ), chưa nấu
  assigned      -> đã chốt giá, món ở bếp (cooking/ready) hoặc trên tay, phần giữ rỗng
  served        -> khách đang ăn (state = eating), đã chốt base_price và tip
  unfulfillable -> còn chờ, giữ chỗ rỗng, không có món (chỉ đến từ scenario)
Payload món (trên bếp hoặc trên tay): {order_id, dish_id, base_price}.
"""

import math
from fractions import Fraction

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import validate_items
from .ramp import ramp_velocity

TICK = 60.0
CUSTOMER_PREFIX = "C"  # [giả định] tiền tố id khách (= order_id); xem docs/clarify.md
CUSTOMER_STATES = ("waiting", "eating")
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")
STOVE_STATES = ("idle", "cooking", "ready")


def _ticks(seconds):
    return int(round(seconds * TICK))


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        self.patience_max = _ticks(t["patience_s"])
        self.eat_max = _ticks(t["eat_s"])
        self.interval = _ticks(t["customer_interval_s"])
        self.first_tick = int(t["first_customer_tick"])
        self.tip_rate = Fraction(str(t["tip_rate"]))
        self.tip_min_ratio = Fraction(str(t["tip_min_patience_ratio"]))

        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2); thiếu cả hai -> kho rỗng
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.time_left_ticks = scenario.get("time_left_ticks", _ticks(t["duration_s"]))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.random_customers = scenario.get("random_customers", True)
        self.phase_tick = 0
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

        self.tables = [dict(tb, pos=[float(c) for c in tb["pos"]])
                       for tb in self._merge(t["tables"], scenario.get("tables", []))]
        self.stoves = []
        for s in self._merge(t["stoves"], scenario.get("stoves", [])):
            self.stoves.append({
                "id": s["id"], "pos": [float(c) for c in s["pos"]],
                "state": s.get("state", "idle"),
                # giữ nguyên giá trị sai kiểu để _check_dish báo mã 2 thay vì crash
                "dish": dict(s["dish"]) if isinstance(s.get("dish"), dict) else s.get("dish"),
                "cook_ticks_left": s.get("cook_ticks_left", 0),
                "ready_ticks": s.get("ready_ticks", 0),
            })
        self.hand = dict(scenario["hand"]) if scenario.get("hand") is not None else None
        self.customers = [self._customer_from_scenario(c) for c in scenario.get("customers", [])]
        for c in self.customers:
            ids.reserve(c["id"])
        self._derive_and_check()

    # ------------------------------------------------------------------ dựng & kiểm scenario
    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _customer_from_scenario(self, c):
        state = c.get("state", "waiting")
        status = c.get("order_status", "served" if state == "eating" else "reserved")
        return {
            "id": c["id"],
            "table_id": c["table_id"],
            "dish_id": c.get("dish_id"),
            "order_tick": c.get("order_tick", 0),
            "state": state,
            "patience_ticks_left": c.get("patience_ticks_left", self.patience_max),
            "eat_ticks_left": c.get("eat_ticks_left", self.eat_max if state == "eating" else 0),
            "order_status": status,
            "reserved": c.get("reserved"),  # None = thiếu, suy ra theo công thức bên dưới
            "base_price": c.get("base_price"),
            "tip": c.get("tip"),
        }

    def _derive_and_check(self):
        """Mâu thuẫn mức luật -> BadInput (mã 2), kiểm trước khi ghi đầu ra."""
        lo, hi = self.t["reputation_min"], self.t["reputation_max"]
        if not _is_num(self.reputation) or not (lo <= self.reputation <= hi):
            raise BadInput(f"reputation phải là số trong [{lo}, {hi}]")
        if not isinstance(self.random_customers, bool):
            raise BadInput("random_customers phải là boolean")

        by_id = {c["id"]: c for c in self.customers}
        for c in self.customers:
            cid = f"customers.{c['id']}"
            if c["dish_id"] not in self.menu:
                raise BadInput(f"{cid}: dish_id phải là món trong menu")
            if c["state"] not in CUSTOMER_STATES:
                raise BadInput(f"{cid}: state phải là một trong {CUSTOMER_STATES}")
            if c["order_status"] not in ORDER_STATUSES:
                raise BadInput(f"{cid}: order_status phải là một trong {ORDER_STATUSES}")
            for key in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
                if not _is_int(c[key]) or c[key] < 0:
                    raise BadInput(f"{cid}.{key} phải là số nguyên không âm")
            if c["patience_ticks_left"] > self.patience_max:
                raise BadInput(f"{cid}.patience_ticks_left vượt kiên nhẫn tối đa")
            if c["eat_ticks_left"] > self.eat_max:
                raise BadInput(f"{cid}.eat_ticks_left vượt thời gian ăn")
            for key in ("base_price", "tip"):
                if c[key] is not None and (not _is_int(c[key]) or c[key] < 0):
                    raise BadInput(f"{cid}.{key} phải là số nguyên không âm")
            if c["reserved"] is not None:
                c["reserved"] = validate_items(c["reserved"])
            eating = c["state"] == "eating"
            if eating != (c["order_status"] == "served"):
                raise BadInput(f"{cid}: khách eating phải có order_status served (và ngược lại)")
            if eating:
                if c["eat_ticks_left"] <= 0 or c["base_price"] is None or c["tip"] is None:
                    raise BadInput(f"{cid}: khách eating cần eat_ticks_left > 0, base_price và tip")
            elif c["tip"] not in (None, 0):
                # khách chưa phục vụ: tip chưa chốt, chấp nhận null hoặc 0 (clarify #12)
                raise BadInput(f"{cid}: khách chưa được phục vụ chỉ có tip null hoặc 0")
            if c["order_status"] != "reserved":
                if c["reserved"]:
                    raise BadInput(f"{cid}: đơn {c['order_status']} phải có phần giữ rỗng")
                c["reserved"] = {}

        # Món trên bếp / trên tay phải khớp đúng một đơn assigned.
        holders = {}
        for s in self.stoves:
            sid = f"stoves.{s['id']}"
            if s["state"] not in STOVE_STATES:
                raise BadInput(f"{sid}: state phải là một trong {STOVE_STATES}")
            for key in ("cook_ticks_left", "ready_ticks"):
                if not _is_int(s[key]) or s[key] < 0:
                    raise BadInput(f"{sid}.{key} phải là số nguyên không âm")
            if s["state"] == "idle":
                if s["dish"] is not None:
                    raise BadInput(f"{sid}: bếp idle không có món")
                continue
            if s["state"] == "cooking" and s["cook_ticks_left"] <= 0:
                raise BadInput(f"{sid}: bếp cooking cần cook_ticks_left > 0")
            self._check_dish(sid, s["dish"], by_id, holders)
        if self.hand is not None:
            self._check_dish("hand", self.hand, by_id, holders)
        for c in self.customers:
            if c["order_status"] == "assigned":
                if c["id"] not in holders:
                    raise BadInput(f"customers.{c['id']}: đơn assigned phải có đúng một món ở bếp hoặc tay")
                if c["base_price"] is None:
                    c["base_price"] = holders[c["id"]]["base_price"]
                elif c["base_price"] != holders[c["id"]]["base_price"]:
                    raise BadInput(f"customers.{c['id']}: base_price không khớp món")

        # Phần giữ chỗ: khai thì phải đúng công thức; thiếu thì cấp theo (order_tick, id bàn).
        for c in self._by_order(c for c in self.customers if c["order_status"] == "reserved"):
            recipe = self.menu[c["dish_id"]]["recipe"]
            if c["reserved"] is None:
                c["reserved"] = dict(recipe)
            elif c["reserved"] != recipe:
                raise BadInput(f"customers.{c['id']}: phần giữ khác công thức món")
        held = self._reserved_total()
        for k, n in held.items():
            if n > self.stock.get(k, 0):
                raise BadInput(f"phần giữ chỗ vượt tồn kho: {k}")

    def _check_dish(self, where, dish, by_id, holders):
        if not isinstance(dish, dict) or set(dish) != {"order_id", "dish_id", "base_price"}:
            raise BadInput(f"{where}: món phải là {{order_id, dish_id, base_price}}")
        if not isinstance(dish["order_id"], str) or not isinstance(dish["dish_id"], str):
            raise BadInput(f"{where}: order_id và dish_id phải là chuỗi")
        if not _is_int(dish["base_price"]) or dish["base_price"] < 0:
            raise BadInput(f"{where}: base_price phải là số nguyên không âm")
        c = by_id.get(dish["order_id"])
        if c is None or c["order_status"] != "assigned" or c["dish_id"] != dish["dish_id"]:
            raise BadInput(f"{where}: món không khớp đơn assigned nào")
        if dish["order_id"] in holders:
            raise BadInput(f"{where}: bếp và tay giữ cùng một đơn")
        holders[dish["order_id"]] = dish

    def _by_order(self, customers):
        return sorted(customers, key=lambda c: (c["order_tick"], id_key(c["table_id"])))

    def _reserved_total(self):
        out = {}
        for c in self.customers:
            for k, n in (c["reserved"] or {}).items():
                out[k] = out.get(k, 0) + n
        return out

    # ------------------------------------------------------------------ snapshot
    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": list(self.pos), "vel": list(self.vel)},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": dict(self.hand) if self.hand else None,
            "stoves": [{"id": s["id"], "pos": s["pos"], "state": s["state"],
                        "dish": dict(s["dish"]) if s["dish"] else None,
                        "cook_ticks_left": s["cook_ticks_left"], "ready_ticks": s["ready_ticks"]}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])}
                       for tb in self.tables],
            "customers": [{
                "id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                "order_tick": c["order_tick"], "state": c["state"],
                "patience_ticks_left": c["patience_ticks_left"], "eat_ticks_left": c["eat_ticks_left"],
                "order_status": c["order_status"],
                "reserved": {k: c["reserved"][k] for k in sorted(c["reserved"])},
                "base_price": c["base_price"], "tip": c["tip"],
            } for c in sort_by_id(self.customers)],
        }

    # ------------------------------------------------------------------ một bước
    def step(self, inp):
        events = []
        self.phase_tick += 1
        self._tick_timers()                      # 1
        self._update_stoves(events)              # 2
        self._move(inp)                          # 3
        if inp.pressed("interact"):
            self._interact(events)
        self._resolve_customers(events)          # 4
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        self._spawn_customer(events)             # 5
        return events

    # 1. đồng hồ
    def _tick_timers(self):
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for c in self.customers:
            if c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
            else:
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
        for s in self.stoves:
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
            elif s["state"] == "ready":
                s["ready_ticks"] += 1

    # 2. bếp chín
    def _update_stoves(self, events):
        for s in self.stoves:
            if s["state"] == "cooking" and s["cook_ticks_left"] <= 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                events.append(("dish_ready", self._dish_data(s)))

    # 3. di chuyển + interact
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

    def _interact(self, events):
        r = self.t["interact_radius"]
        cands = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r:
                cands.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r:
                cands.append((d, 1, id_key(tb["id"]), "table", tb))
        if not cands:
            return
        _, _, _, kind, obj = min(cands, key=lambda x: x[:3])
        if kind == "stove":
            self._interact_stove(obj, events)
        else:
            self._interact_table(obj, events)

    def _interact_stove(self, s, events):
        if s["state"] == "idle":
            orders = self._by_order(c for c in self.customers
                                    if c["order_status"] == "reserved" and c["state"] == "waiting")
            if not orders:
                return
            c = orders[0]
            dish = self.menu[c["dish_id"]]
            items = []
            for k in sorted(c["reserved"]):
                n = c["reserved"][k]
                self.stock[k] = self.stock.get(k, 0) - n
                items.extend([k] * n)
            c["reserved"] = {}
            c["order_status"] = "assigned"
            c["base_price"] = dish["price"]
            s["state"] = "cooking"
            s["dish"] = {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": dish["price"]}
            s["cook_ticks_left"] = _ticks(dish["cook_s"])
            s["ready_ticks"] = 0
            data = self._dish_data(s)
            data.update(items=items, base_price=dish["price"])
            events.append(("cook_started", data))
        elif s["state"] == "ready" and self.hand is None:  # carry_limit = 1 ở v1.0
            data = self._dish_data(s)
            self.hand = s["dish"]
            self._clear_stove(s)
            events.append(("dish_picked", data))

    def _interact_table(self, tb, events):
        c = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
        if c is None or self.hand is None or c["state"] != "waiting" or self.hand["order_id"] != c["id"]:
            return
        price = self.hand["base_price"]
        ratio_ok = Fraction(c["patience_ticks_left"], self.patience_max) >= self.tip_min_ratio
        tip = math.floor(price * self.tip_rate) if ratio_ok else 0
        c.update(state="eating", order_status="served", eat_ticks_left=self.eat_max,
                 base_price=price, tip=tip)
        self.hand = None
        events.append(("served", {"order_id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                                  "patience_ticks_left": c["patience_ticks_left"],
                                  "base_price": price, "tip": tip}))

    # 4. khách trả tiền / bỏ đi / hết ca
    def _resolve_customers(self, events):
        closing = self.time_left_ticks <= 0
        for c in sorted(self.customers, key=lambda c: id_key(c["table_id"])):
            if c["state"] == "eating":
                if c["eat_ticks_left"] <= 0 or closing:
                    self._pay(c, "closing" if c["eat_ticks_left"] > 0 else "finished_eating", events)
            elif closing:
                self._leave(c, "closing", events)
            elif c["patience_ticks_left"] <= 0:
                self._leave(c, "patience", events)

    def _pay(self, c, reason, events):
        amount = c["base_price"] + c["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:
            self._add_reputation(self.t["tip_reputation"])
        self.customers.remove(c)
        events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": c["base_price"],
                                "tip": c["tip"], "amount": amount, "reason": reason}))

    def _leave(self, c, reason, events):
        # nhả phần giữ thô (stock vẫn còn nguyên), bỏ món của đơn đang nấu / ready / trên tay
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == c["id"]:
                self._clear_stove(s)
        if self.hand is not None and self.hand["order_id"] == c["id"]:
            self.hand = None
        if reason == "patience":
            self._add_reputation(self.t["left_reputation_delta"])
        self.customers.remove(c)
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
                                         "reputation": self.reputation}))

    def _add_reputation(self, delta):
        lo, hi = self.t["reputation_min"], self.t["reputation_max"]
        # làm tròn để cộng dồn số thực không làm floor(reputation) lệch (ví dụ 4.999999 -> 4)
        self.reputation = min(hi, max(lo, round(self.reputation + delta, 9)))

    # 5. khách mới
    def _spawn_customer(self, events):
        if not self.random_customers or self.phase_tick < self.first_tick:
            return
        if self.interval <= 0 or (self.phase_tick - self.first_tick) % self.interval != 0:
            return
        occupied = {c["table_id"] for c in self.customers}
        free = [tb for tb in self.tables if tb["id"] not in occupied]  # đã sắp theo id
        if not free:
            return
        held = self._reserved_total()
        avail = {k: self.stock.get(k, 0) - held.get(k, 0) for k in self.stock}
        options = [d for d in sorted(self.menu)
                   if all(avail.get(k, 0) >= n for k, n in self.menu[d]["recipe"].items())]
        if not options:
            events.append(("no_dish", {}))
            return
        dish_id = options[self.rng.get("quan_customer_dish").randrange(len(options))]
        table = free[0]
        cid = self.ids.new(CUSTOMER_PREFIX)
        self.customers.append({
            "id": cid, "table_id": table["id"], "dish_id": dish_id, "order_tick": self.phase_tick,
            "state": "waiting", "patience_ticks_left": self.patience_max, "eat_ticks_left": 0,
            "order_status": "reserved", "reserved": dict(self.menu[dish_id]["recipe"]),
            "base_price": None, "tip": None,
        })
        events.append(("customer_arrived", {"order_id": cid, "table_id": table["id"], "dish_id": dish_id}))

    # tiện ích
    @staticmethod
    def _dish_data(s):
        return {"stove_id": s["id"], "order_id": s["dish"]["order_id"], "dish_id": s["dish"]["dish_id"]}

    @staticmethod
    def _clear_stove(s):
        s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
