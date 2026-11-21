"""Buổi tối — Mở Quán (PRD-0 mục F, Quán). Lát 3 (khách, giữ chỗ, kiên nhẫn) + lát 4 (bếp, bưng, phục vụ, tiền).

Thứ tự xử lý một bước (mục F, Quán):
  1. tăng đồng hồ; giảm timer ca / nấu / ăn / kiên nhẫn; ready_ticks +1 cho món đã ready từ đầu bước
  2. bếp theo id: nấu xong -> ready (ready_ticks = 0), phát dish_ready
  3. di chuyển; tối đa MỘT interact (khoảng cách, bếp trước bàn, id)
  4. theo id bàn: khách ăn xong trả tiền; khách hết kiên nhẫn rời (nếu còn giờ); hết ca thì dọn hết -> quan_end
  5. còn giờ: khách mới theo lịch (first_customer_tick, customer_interval_s), hoặc no_dish

Số liệu chỉ đọc từ tuning (game.contract.json); ngẫu nhiên chỉ qua Streams.
"""

import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..scenario import check_reserved_within_stock
from .ramp import ramp_velocity

TICK = 60.0
EPS = 1e-9  # so bán kính "tính cả đúng mép"


def _ticks(seconds):
    return int(round(seconds * 60))


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        self.patience_total = _ticks(t["patience_s"])
        self.eat_total = _ticks(t["eat_s"])
        self.interval_ticks = _ticks(t["customer_interval_s"])
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2). Gồm cả phần đã giữ chỗ.
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", _ticks(t["duration_s"]))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.random_customers = scenario.get("random_customers", True)
        self.phase_tick = 0
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = self._build_customers(scenario.get("customers", []))
        check_reserved_within_stock(self.customers, self.stock)  # mã 2 nếu giữ quá tồn
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    # ---------- dựng trạng thái đầu ----------

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _build_customers(self, fixtures):
        """Khách dựng sẵn từ scenario; điền mặc định theo mục D. Đơn reserved thiếu `reserved` thì
        cấp theo công thức, xét theo (order_tick, id bàn)."""
        out = []
        for c in fixtures:
            self.ids.reserve(c["id"])
            e = dict(c)
            e.setdefault("state", "waiting")
            e.setdefault("order_tick", 0)
            e.setdefault("order_status", "reserved")
            e.setdefault("patience_ticks_left", self.patience_total)
            e.setdefault("eat_ticks_left", 0)
            e.setdefault("base_price", 0)
            e.setdefault("tip", 0)
            out.append(e)
        for e in sorted(out, key=lambda e: (e["order_tick"], id_key(e["table_id"]))):
            if e["order_status"] == "reserved" and "reserved" not in e:
                e["reserved"] = dict(self.menu[e["dish_id"]]["recipe"])
            e.setdefault("reserved", {})
        return out

    # ---------- snapshot ----------

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

    # ---------- một bước ----------

    def step(self, inp):
        events = []
        # 1. đồng hồ và các timer
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.phase_tick += 1
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
        for c in self.customers:
            if c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
            elif c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
        # 2. bếp theo id: nấu xong -> ready
        for s in self.stoves:
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                d = s["dish"]
                events.append(("dish_ready", {"stove_id": s["id"], "order_id": d["order_id"], "dish_id": d["dish_id"]}))
        # 3. di chuyển rồi tối đa một interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        # 4. theo id bàn: trả tiền / bỏ đi
        closing = self.time_left_ticks <= 0
        for c in sorted(self.customers, key=lambda c: id_key(c["table_id"])):
            if c["state"] == "eating":
                if c["eat_ticks_left"] == 0:
                    self._pay(c, "finished_eating", events)
                elif closing:
                    self._pay(c, "closing", events)
            elif c["state"] == "waiting":
                if closing:
                    self._leave(c, "closing", events)
                elif c["patience_ticks_left"] == 0:
                    self.reputation = self._clamp_rep(self.reputation + self.t["left_reputation_delta"])
                    self._leave(c, "patience", events)
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        # 5. khách mới theo lịch
        first = self.t["first_customer_tick"]
        if (self.random_customers and self.phase_tick >= first and self.interval_ticks > 0
                and (self.phase_tick - first) % self.interval_ticks == 0):
            self._spawn_customer(events)
        return events

    # ---------- tương tác ----------

    def _interact(self, events):
        r = self.t["interact_radius"]
        best = None
        for kind, objs in ((0, self.stoves), (1, self.tables)):  # bếp trước bàn
            for o in objs:
                d = math.hypot(o["pos"][0] - self.pos[0], o["pos"][1] - self.pos[1])
                if d <= r + EPS:
                    key = (d, kind, id_key(o["id"]))
                    if best is None or key < best[0]:
                        best = (key, kind, o)
        if best is None:
            return
        _, kind, obj = best
        if kind == 0:
            self._interact_stove(obj, events)
        else:
            self._interact_table(obj, events)

    def _interact_stove(self, s, events):
        if s["state"] == "idle":
            waiting = [c for c in self.customers if c["order_status"] == "reserved"]
            if not waiting:
                return
            c = min(waiting, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
            recipe = self.menu[c["dish_id"]]["recipe"]
            for kind, n in c["reserved"].items():
                self.stock[kind] = self.stock.get(kind, 0) - n
            items = [k for k in sorted(recipe) for _ in range(recipe[k])]
            price = self.menu[c["dish_id"]]["price"]
            c["reserved"] = {}
            c["order_status"] = "assigned"
            c["base_price"] = price
            s["state"] = "cooking"
            s["cook_ticks_left"] = _ticks(self.menu[c["dish_id"]]["cook_s"])
            s["ready_ticks"] = 0
            s["dish"] = {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": price}
            events.append(("cook_started", {"stove_id": s["id"], "order_id": c["id"], "dish_id": c["dish_id"],
                                            "items": items, "base_price": price}))
        elif s["state"] == "ready" and self.hand is None:
            d = s["dish"]
            self.hand = dict(d)
            s["state"] = "idle"
            s["dish"] = None
            s["cook_ticks_left"] = 0
            s["ready_ticks"] = 0
            events.append(("dish_picked", {"stove_id": s["id"], "order_id": d["order_id"], "dish_id": d["dish_id"]}))

    def _interact_table(self, tb, events):
        if self.hand is None:
            return
        c = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
        if c is None or c["state"] != "waiting" or c["id"] != self.hand["order_id"]:
            return
        base = self.hand["base_price"]
        ratio_ok = c["patience_ticks_left"] / self.patience_total >= self.t["tip_min_patience_ratio"]
        tip = math.floor(base * self.t["tip_rate"]) if ratio_ok else 0
        c["state"] = "eating"
        c["order_status"] = "served"
        c["eat_ticks_left"] = self.eat_total
        c["base_price"] = base
        c["tip"] = tip
        self.hand = None
        events.append(("served", {"order_id": c["id"], "table_id": tb["id"], "dish_id": c["dish_id"],
                                  "patience_ticks_left": c["patience_ticks_left"], "base_price": base, "tip": tip}))

    # ---------- vòng đời khách ----------

    def _pay(self, c, reason, events):
        amount = c["base_price"] + c["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:
            self.reputation = self._clamp_rep(self.reputation + self.t["tip_reputation"])
        events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": c["base_price"],
                                "tip": c["tip"], "amount": amount, "reason": reason}))
        self.customers.remove(c)

    def _leave(self, c, reason, events):
        """Khách rời không ăn: nhả phần giữ chỗ, bỏ món của đơn (đang nấu / ready / trên tay)."""
        for s in self.stoves:
            if s["dish"] and s["dish"]["order_id"] == c["id"]:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand and self.hand["order_id"] == c["id"]:
            self.hand = None
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
                                         "reputation": self.reputation}))
        self.customers.remove(c)

    def _clamp_rep(self, v):
        return min(self.t["reputation_max"], max(self.t["reputation_min"], v))

    def _available(self):
        """Tồn khả dụng = kho trừ phần đã giữ chỗ."""
        avail = dict(self.stock)
        for c in self.customers:
            for k, n in c["reserved"].items():
                avail[k] = avail.get(k, 0) - n
        return avail

    def _spawn_customer(self, events):
        taken = {c["table_id"] for c in self.customers}
        free = [tb for tb in self.tables if tb["id"] not in taken]
        if not free:
            return  # không còn bàn: bỏ lượt (không phát no_dish)
        table = free[0]  # self.tables đã sắp theo id
        avail = self._available()
        cands = [d for d in sorted(self.menu)
                 if all(avail.get(k, 0) >= n for k, n in self.menu[d]["recipe"].items())]
        if not cands:
            events.append(("no_dish", {}))
            return
        dish = self.rng.get("quan_dish").choice(cands)
        cid = self.ids.new("C")
        self.customers.append({
            "id": cid, "table_id": table["id"], "dish_id": dish, "order_tick": self.phase_tick,
            "state": "waiting", "patience_ticks_left": self.patience_total, "eat_ticks_left": 0,
            "order_status": "reserved", "reserved": dict(self.menu[dish]["recipe"]),
            "base_price": 0, "tip": 0,
        })
        events.append(("customer_arrived", {"order_id": cid, "table_id": table["id"], "dish_id": dish}))

    # ---------- di chuyển ----------

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
