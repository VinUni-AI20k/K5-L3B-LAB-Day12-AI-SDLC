"""Buổi tối — Mở Quán (PRD-0 mục F, Quán).

  Lát 3: khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
         bỏ đi (customer_left), no_dish, vòng đời khách.
  Lát 4: interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
         ăn xong trả tiền (paid), boa, uy tín, hết ca (closing, quan_end).
"""

import math
from fractions import Fraction

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


def _order_ref(obj):
    """Chuẩn hóa món trên bếp/tay về {"order_id","dish_id"} (hợp đồng mục 3) hoặc None.

    Scenario có thể ghi dish là chuỗi kèm order_id/customer_id, hoặc dish/dish_id là object.
    """
    if obj is None:
        return None
    if isinstance(obj, str):
        return {"order_id": None, "dish_id": obj}
    dish = obj.get("dish_id") or obj.get("dish")
    if isinstance(dish, dict):
        return _order_ref(dish)
    if dish is None:
        return None
    return {"order_id": obj.get("order_id") or obj.get("customer_id"), "dish_id": dish}


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.tick_hz = tuning.get("tick_hz", 60)
        self.phase_tick = 0
        self.rng = streams
        self.ids = ids
        self.random_customers = scenario.get("random_customers", True)
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = _order_ref(scenario.get("hand"))
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = []
        for s in self._merge(t["stoves"], scenario.get("stoves", [])):
            dish = _order_ref(s) if s.get("state", "idle") != "idle" else None
            state = s.get("state", "idle") if dish is not None else "idle"
            self.stoves.append({
                "id": s["id"], "pos": s["pos"], "state": state, "dish": dish,
                "cook_ticks_left": s.get("cook_ticks_left", 0), "ready_ticks": s.get("ready_ticks", 0),
            })
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = []
        self._init_customers(scenario.get("customers", []))
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
        """Một bước theo PRD-0 mục F "Quán" (1 đồng hồ → 2 bếp → 3 di chuyển + interact → 4 khách → 5 lịch)."""
        events = []
        # 1. Đồng hồ, timer ca, nấu, ăn, kiên nhẫn.
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.phase_tick += 1
        self._tick_timers()
        self._update_customer_patience()
        # 2. Bếp chín -> ready.
        events.extend(self._update_stoves())
        # 3. Di chuyển rồi tối đa MỘT interact.
        self._move(inp)
        if inp.pressed("interact"):
            events.extend(self._interact())
        # 4. Khách ăn xong trả tiền, hết kiên nhẫn rời, hoặc dọn cuối ca.
        closing = self.time_left_ticks <= 0
        events.extend(self._settle_customers(closing))
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        # 5. Khách mới theo lịch (first_customer_tick, customer_interval_s).
        if self._should_spawn_customer():
            table = self._find_available_table()
            if table is not None:
                events.extend(self._spawn_customer(table))
        return events

    # ---------- Lát 4: bước 1–2 (timer bếp/ăn, bếp chín) ----------

    def _tick_timers(self):
        """Bước 1: giảm cook/eat (không âm); ready_ticks chỉ tăng cho món đã ready từ đầu bước."""
        for s in self.stoves:
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
            elif s["state"] == "ready":
                s["ready_ticks"] += 1
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)

    def _update_stoves(self) -> list:
        """Bước 2: theo id bếp, món nấu xong chuyển ready với ready_ticks = 0 (burn_s: null)."""
        events = []
        for s in self.stoves:  # self.stoves đã sắp theo id
            if s["state"] == "cooking" and s["cook_ticks_left"] <= 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                c = self._customer(s["dish"]["order_id"])
                if c is not None:
                    c["order_status"] = "ready"
                events.append(("dish_ready", self._stove_data(s)))
        return events

    # ---------- Lát 4: bước 3 (interact) ----------

    def _interact(self) -> list:
        """Chọn đúng một đối tượng theo (khoảng cách, bếp trước bàn, id); không tương tác được thì bỏ lượt."""
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
            return []
        _, _, _, kind, obj = min(cands, key=lambda c: c[:3])
        if kind == "table":
            return self._serve(obj)
        if obj["state"] == "idle":
            return self._start_cooking(obj)
        if obj["state"] == "ready":
            return self._pick_dish(obj)
        return []  # bếp đang nấu: bỏ lượt

    def _start_cooking(self, stove) -> list:
        """Bếp idle lấy đơn reserved cũ nhất (order_tick, id bàn), tiêu nguyên liệu giữ, chốt giá."""
        orders = [c for c in self.customers if c["state"] == "waiting" and c["order_status"] == "reserved"]
        if not orders:
            return []
        c = min(orders, key=lambda o: (o["order_tick"], id_key(o["table_id"])))
        used = dict(c["reserved"] or self.menu[c["dish_id"]]["recipe"])
        for k, n in used.items():
            self.stock[k] = self.stock.get(k, 0) - n
        dish = self.menu[c["dish_id"]]
        c["reserved"] = {}
        c["order_status"] = "cooking"
        c["base_price"] = dish["price"]
        stove["state"] = "cooking"
        stove["dish"] = {"order_id": c["id"], "dish_id": c["dish_id"]}
        stove["cook_ticks_left"] = int(round(dish["cook_s"] * self.tick_hz))
        stove["ready_ticks"] = 0
        items = sorted(k for k, n in used.items() for _ in range(n))
        return [("cook_started", dict(self._stove_data(stove), items=items, base_price=c["base_price"]))]

    def _pick_dish(self, stove) -> list:
        """Bếp ready giao món cho tay trống (carry_limit 1) rồi về idle; tay đầy thì bỏ lượt."""
        if self.hand is not None or self.t["carry_limit"] < 1:
            return []
        data = self._stove_data(stove)
        self.hand = dict(stove["dish"])
        c = self._customer(self.hand["order_id"])
        if c is not None:
            c["order_status"] = "carried"
        stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        return [("dish_picked", data)]

    def _serve(self, table) -> list:
        """Bàn nhận đúng order_id trên tay: khách ăn với timer đầy, chốt boa theo kiên nhẫn sau bước 1."""
        c = next((x for x in self.customers if x["table_id"] == table["id"]), None)
        if c is None or self.hand is None or c["state"] != "waiting" or self.hand["order_id"] != c["id"]:
            return []
        price = c["base_price"] if c["base_price"] is not None else self.menu[c["dish_id"]]["price"]
        patience_max = int(round(self.t["patience_s"] * self.tick_hz))
        ratio = Fraction(c["patience_ticks_left"], patience_max)
        tip = 0
        if ratio >= Fraction(str(self.t["tip_min_patience_ratio"])):
            tip = math.floor(price * Fraction(str(self.t["tip_rate"])))
        self.hand = None
        c.update(state="eating", order_status="served", base_price=price, tip=tip,
                 eat_ticks_left=int(round(self.t["eat_s"] * self.tick_hz)))
        return [("served", {"order_id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                            "patience_ticks_left": c["patience_ticks_left"], "base_price": price, "tip": tip})]

    # ---------- Lát 4: bước 4 (trả tiền, rời quán, cuối ca) ----------

    def _settle_customers(self, closing) -> list:
        """Theo id bàn: ăn xong -> paid; còn giờ mà hết kiên nhẫn -> rời patience;
        hết ca: đang ăn -> paid closing, đang chờ -> rời closing (không trừ uy tín)."""
        events = []
        for c in sorted(self.customers, key=lambda x: id_key(x["table_id"])):
            if c["state"] == "eating":
                if c["eat_ticks_left"] <= 0:
                    events.extend(self._pay(c, "finished_eating"))
                elif closing:
                    events.extend(self._pay(c, "closing"))
            elif closing:
                events.extend(self._expire_customer(c, reason="closing"))
            elif c["patience_ticks_left"] <= 0:
                events.extend(self._expire_customer(c, reason="patience"))
        return events

    def _pay(self, c, reason) -> list:
        tip = c["tip"] or 0
        if c["base_price"] is None:
            c["base_price"] = self.menu[c["dish_id"]]["price"]
        amount = c["base_price"] + tip
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if tip > 0:
            self._add_reputation(self.t["tip_reputation"])
        self._remove_customer(c)
        return [("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": c["base_price"],
                          "tip": tip, "amount": amount, "reason": reason})]

    def _add_reputation(self, delta):
        rmin, rmax = self.t["reputation_min"], self.t["reputation_max"]
        self.reputation = max(rmin, min(rmax, round(self.reputation + delta, 6)))

    def _remove_customer(self, c):
        """Khách rời bàn: nhả giữ thô, bỏ món của đơn đang nấu/ready/trên tay (nguyên liệu đã dùng không hoàn)."""
        self._release_reserved(c)
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == c["id"]:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand is not None and self.hand["order_id"] == c["id"]:
            self.hand = None
        self.customers = [x for x in self.customers if x is not c]

    def _customer(self, cid):
        return next((c for c in self.customers if c["id"] == cid), None)

    @staticmethod
    def _stove_data(stove):
        return {"stove_id": stove["id"], "order_id": stove["dish"]["order_id"], "dish_id": stove["dish"]["dish_id"]}

    # ---------- Lát 3: kiên nhẫn, rời quán ----------

    def _update_customer_patience(self):
        """Bước 1: khách chờ giảm kiên nhẫn (không âm) từ bước sau khi đến; việc rời quán xét ở bước 4."""
        for c in self.customers:
            if c.get("state") == "waiting" and c.get("order_tick") != self.phase_tick:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)

    def _expire_customer(self, customer, reason="patience") -> list:
        if reason == "patience":
            self._add_reputation(self.t["left_reputation_delta"])
        self._remove_customer(customer)
        # PRD-0 mục E: order_id, table_id, reason, reputation. Giữ customer_id cho tương thích hợp đồng nhóm.
        return [("customer_left", {"order_id": customer["id"], "customer_id": customer["id"],
                                   "table_id": customer["table_id"], "reason": reason,
                                   "reputation": self.reputation})]

    def _release_reserved(self, customer):
        customer["reserved"] = {}

    def _should_spawn_customer(self) -> bool:
        if not self.random_customers:
            return False
        first_tick = self.t["first_customer_tick"]
        interval_ticks = int(round(self.t["customer_interval_s"] * self.tick_hz))
        if self.phase_tick < first_tick:
            return False
        return (self.phase_tick - first_tick) % interval_ticks == 0

    def _find_available_table(self):
        occupied = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in self.tables if tb["id"] not in occupied]
        if not free_tables:
            return None
        return sort_by_id(free_tables)[0]

    def _spawn_customer(self, table):
        events = []
        avail = self._available_stock()
        valid_dishes = []
        for did in sorted(self.menu.keys()):
            recipe = self.menu[did]["recipe"]
            if all(avail.get(k, 0) >= req for k, req in recipe.items()):
                valid_dishes.append(did)

        if not valid_dishes:
            events.append(("no_dish", {}))  # PRD-0 mục E: {} khi có bàn mà thiếu món
            return events

        rng = self.rng.get("customers")
        chosen_dish = rng.choice(valid_dishes)
        recipe = dict(self.menu[chosen_dish]["recipe"])

        customer_id = self.ids.new("C")
        pat_ticks = int(round(self.t["patience_s"] * self.tick_hz))
        new_customer = {
            "id": customer_id,
            "table_id": table["id"],
            "dish_id": chosen_dish,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": pat_ticks,
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": recipe,
            "base_price": None,
            "tip": 0,
        }
        self.customers.append(new_customer)
        events.append((
            "customer_arrived",
            {  # PRD-0 mục E: order_id, table_id, dish_id; giữ customer_id/reserved cho hợp đồng nhóm
                "order_id": customer_id,
                "customer_id": customer_id,
                "table_id": table["id"],
                "dish_id": chosen_dish,
                "reserved": recipe,
            }
        ))
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

    def _init_customers(self, scenario_customers):
        pat_ticks = int(round(self.t["patience_s"] * 60))
        for c in scenario_customers:
            cust = {
                "id": c["id"],
                "table_id": c["table_id"],
                "dish_id": c["dish_id"],
                "order_tick": c.get("order_tick", 0),
                "state": c.get("state", "waiting"),
                "patience_ticks_left": c.get("patience_ticks_left", pat_ticks),
                "eat_ticks_left": c.get("eat_ticks_left", 0),
                "order_status": c.get("order_status", "reserved" if c.get("state", "waiting") == "waiting" else "served"),
                "reserved": dict(c["reserved"]) if "reserved" in c else None,
                "base_price": c.get("base_price", None),
                "tip": c.get("tip", 0),
            }
            self.customers.append(cust)
            self.ids.reserve(cust["id"])
        self._infer_customer_reservations()

    def _available_stock(self) -> dict:
        """Kho khả dụng = stock - tổng nguyên liệu đang được giữ (reserved)."""
        reserved_totals = {}
        for c in self.customers:
            if c.get("order_status") == "reserved":
                res = c.get("reserved") or {}
                for k, v in res.items():
                    if v > 0:
                        reserved_totals[k] = reserved_totals.get(k, 0) + v
        return {k: max(0, self.stock.get(k, 0) - reserved_totals.get(k, 0)) for k in self.stock}

    def _infer_customer_reservations(self):
        """Khách fixture thiếu reserved được suy ra theo công thức món ăn (order_tick tăng dần, rồi id bàn)."""
        unreserved = [c for c in self.customers if not c.get("reserved") and c.get("order_status") == "reserved"]
        unreserved.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))
        for c in unreserved:
            recipe = self.menu[c["dish_id"]]["recipe"]
            avail = self._available_stock()
            for k, req in recipe.items():
                if avail.get(k, 0) < req:
                    from ..errors import BadInput
                    raise BadInput(f"không đủ kho để giữ nguyên liệu cho khách {c['id']} (món {c['dish_id']})")
            c["reserved"] = dict(recipe)

        for c in self.customers:
            if not c.get("reserved"):
                c["reserved"] = {}

        self._check_total_reservations()

    def _check_total_reservations(self):
        reserved_totals = {}
        for c in self.customers:
            if c.get("order_status") == "reserved":
                res = c.get("reserved") or {}
                for k, v in res.items():
                    if v > 0:
                        reserved_totals[k] = reserved_totals.get(k, 0) + v
        for k, v in reserved_totals.items():
            if v > self.stock.get(k, 0):
                from ..errors import BadInput
                raise BadInput(f"tổng nguyên liệu giữ vượt quá kho thực tế cho {k}: giữ {v}, kho có {self.stock.get(k, 0)}")
