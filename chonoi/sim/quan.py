"""Buổi tối — di chuyển, bếp, phục vụ và quyết toán ca.

TV3 Phase 3: kho cá thể + hao tươi + giữ chỗ theo id + thử giữ lại khi ươn.
Vẫn hỗ trợ kho đếm (v1.1) để regression P1–P2 xanh trong lúc TV1 bật contract 1.2.
"""

import math
from decimal import Decimal

from ..errors import BadInput
from ..freshness import (
    available_units,
    counts_to_units,
    decay_units,
    is_spoiled,
    pick_for_recipe,
    snapshot_units,
    units_by_id,
    validate_units,
)
from ..ids import id_key, sort_by_id
from ..inventory import price_for_items
from ..inventory import validate_items
from .ramp import ramp_velocity


def _count(value):
    return type(value) is int and value >= 0


def _idle(stove):
    stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.hz = tuning["tick_hz"]
        self.patience = round(t["patience_s"] * self.hz)
        self.menu = tuning["menu"]
        self.freshness = tuning.get("freshness")
        self.rng = streams
        self.ids = ids
        fresh_cfg = tuning.get("freshness") or {
            "initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30,
        }
        self.fresh_initial = float(fresh_cfg.get("initial", 100))
        self.quan_decay_per_s = float(fresh_cfg.get("quan_decay_per_s", 0.25))
        self.spoiled_below = float(fresh_cfg.get("spoiled_below", 30))
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        raw = inventory if inventory is not None else scenario.get("stock", {})
        self.item_mode = isinstance(raw, list)
        if self.item_mode:
            self.stock = validate_units(raw)
            for u in self.stock:
                ids.reserve(u["id"])
        else:
            # v1.1 count map — giữ path cũ; đồng thời dựng stock_units nội bộ nếu cần dần.
            self.stock = dict(raw or {})
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * self.hz)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.random_customers = scenario.get("random_customers", True)
        self.customer_interval_ticks = round(t["customer_interval_s"] * self.hz)
        self.phase_tick = 0
        plan = scenario.get("day_plan")
        self.plan_dishes = dict(plan["dishes"]) if isinstance(plan, dict) and "dishes" in plan else None
        self.customers = []
        for fixture in scenario.get("customers", []):
            customer = self._load_customer(fixture)
            self.customers.append(customer)
            ids.reserve(customer["id"])
        self._check_dishes()
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    # --- TV3: kho khả dụng, kế hoạch ngày & lịch khách -----------------------
    def _all_reserved_ids(self):
        ids = []
        for c in self.customers:
            reserved = c.get("reserved") or []
            if isinstance(reserved, list):
                ids.extend(reserved)
        return ids

    def available_stock(self) -> dict:
        """Số lượng kind khả dụng (chưa ươn, chưa giữ) — dùng chọn món / no_dish."""
        if not self.item_mode:
            avail = dict(self.stock)
            for c in self.customers:
                reserved = c.get("reserved") or {}
                if isinstance(reserved, dict):
                    for kind, qty in reserved.items():
                        avail[kind] = avail.get(kind, 0) - qty
            return avail
        counts = {}
        for u in available_units(self.stock, self._all_reserved_ids(), self.spoiled_below):
            counts[u["kind"]] = counts.get(u["kind"], 0) + 1
        return counts

    def _menu_pool(self) -> list:
        if self.plan_dishes is None:
            return sorted(self.menu.keys())
        return sorted(d for d in self.plan_dishes if d in self.menu)

    def _free_tables(self):
        occupied = {c["table_id"] for c in self.customers}
        return [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]

    def _cookable_dishes(self) -> list:
        avail = self.available_stock()
        return [
            dish_id for dish_id in self._menu_pool()
            if all(avail.get(k, 0) >= qty for k, qty in self.menu[dish_id]["recipe"].items())
        ]

    def _is_spawn_tick(self) -> bool:
        first = self.t["first_customer_tick"]
        if self.phase_tick < first:
            return False
        return (self.phase_tick - first) % self.customer_interval_ticks == 0

    def _reserve_recipe(self, recipe, exclude_ids=None):
        if self.item_mode:
            return pick_for_recipe(self.stock, recipe, exclude_ids or self._all_reserved_ids(),
                                   self.spoiled_below)
        # count mode: trả map kind→qty (không phải list id)
        avail = self.available_stock()
        if any(avail.get(k, 0) < n for k, n in recipe.items()):
            return None
        return validate_items(recipe)

    def try_spawn_customer(self) -> list:
        events = []
        if not self.random_customers or self.time_left_ticks <= 0 or not self._is_spawn_tick():
            return events
        free = self._free_tables()
        if not free:
            return events
        cookable = self._cookable_dishes()
        if not cookable:
            events.append(("no_dish", {}))
            return events
        dish_id = self.rng.get("dish_pick").choice(cookable)
        table = free[0]
        cid = self.ids.new("C")
        recipe = self.menu[dish_id]["recipe"]
        reserved = self._reserve_recipe(recipe)
        if reserved is None:
            events.append(("no_dish", {}))
            return events
        customer = {
            "id": cid,
            "table_id": table["id"],
            "dish_id": dish_id,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "order_status": "reserved",
            "patience_ticks_left": self.patience,
            "eat_ticks_left": 0,
            "reserved": reserved if self.item_mode else validate_items(recipe),
        }
        self.customers.append(customer)
        events.append(("customer_arrived", {
            "order_id": cid, "table_id": table["id"], "dish_id": dish_id,
        }))
        return events

    def decay_and_rereserve(self) -> list:
        """Hao tươi kho thô → spoiled theo id → thử giữ lại đơn bị ảnh hưởng."""
        events = []
        if not self.item_mode:
            return events
        _, crossed = decay_units(self.stock, self.quan_decay_per_s, self.hz, self.spoiled_below)
        for u in crossed:
            events.append(("spoiled", {
                "item_id": u["id"], "kind": u["kind"], "location": "stock",
            }))
        spoiled_ids = {u["id"] for u in crossed}
        if not spoiled_ids:
            return events
        affected = [
            c for c in self.customers
            if c.get("order_status") == "reserved"
            and isinstance(c.get("reserved"), list)
            and any(iid in spoiled_ids for iid in c["reserved"])
        ]
        affected.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        for c in affected:
            c["reserved"] = []
            again = self._reserve_recipe(self.menu[c["dish_id"]]["recipe"])
            if again is None:
                c["order_status"] = "unfulfillable"
                c["reserved"] = []
            else:
                c["reserved"] = again
                c["order_status"] = "reserved"
        return events

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _load_customer(self, fixture):
        dish_id = fixture.get("dish_id")
        if not isinstance(dish_id, str) or dish_id not in self.menu:
            raise BadInput("đơn cần dish_id có trong menu")
        c = dict(state="waiting", order_tick=0, order_status="reserved",
                 patience_ticks_left=self.patience, eat_ticks_left=0)
        c.update(fixture)
        status = c["order_status"]
        if status not in ("reserved", "assigned", "unfulfillable", "served"):
            raise BadInput("order_status không hợp lệ")
        eating = status == "served"
        if c["state"] != ("eating" if eating else "waiting"):
            raise BadInput("trạng thái khách và đơn mâu thuẫn")
        for key in ("order_tick", "patience_ticks_left", "eat_ticks_left", "base_price", "tip"):
            if key in c and not _count(c[key]):
                raise BadInput(f"{key} phải là số nguyên không âm")
        if eating != (c["eat_ticks_left"] > 0) or eating and not {"base_price", "tip"} <= c.keys():
            raise BadInput("timer ăn hoặc tiền của đơn không hợp lệ")

        recipe = self.menu[dish_id]["recipe"]
        if self.item_mode:
            if status == "reserved":
                if "reserved" not in fixture or fixture["reserved"] is None:
                    picked = pick_for_recipe(self.stock, recipe, self._all_reserved_ids(), self.spoiled_below)
                    if picked is None:
                        raise BadInput("giữ nguyên liệu vượt kho / thiếu hàng tươi")
                    c["reserved"] = picked
                else:
                    if not isinstance(fixture["reserved"], list):
                        raise BadInput("reserved phải là mảng id cá thể")
                    by_id = units_by_id(self.stock)
                    used = set()
                    for iid in fixture["reserved"]:
                        if not isinstance(iid, str) or iid not in by_id:
                            raise BadInput(f"reserved trỏ id không có trong kho: {iid}")
                        if iid in used or is_spoiled(by_id[iid]["fresh"], self.spoiled_below):
                            raise BadInput("reserved trùng hoặc đã ươn")
                        used.add(iid)
                    # đủ công thức
                    kinds = {}
                    for iid in fixture["reserved"]:
                        kinds[by_id[iid]["kind"]] = kinds.get(by_id[iid]["kind"], 0) + 1
                    if kinds != validate_items(recipe):
                        raise BadInput("giữ nguyên liệu sai công thức")
                    c["reserved"] = list(fixture["reserved"])
            else:
                c["reserved"] = list(fixture.get("reserved") or [])
            return c

        expected = recipe if status == "reserved" else {}
        c["reserved"] = validate_items(c.get("reserved", expected))
        if c["reserved"] != expected or any(self.stock.get(k, 0) < n for k, n in expected.items()):
            raise BadInput("giữ nguyên liệu sai công thức hoặc vượt kho")
        return c

    def _check_dishes(self):
        dishes = []
        for stove in self.stoves:
            state = stove["state"]
            cook, ready = stove["cook_ticks_left"], stove["ready_ticks"]
            if (state not in ("idle", "cooking", "ready") or not _count(cook) or not _count(ready)
                    or (state == "cooking") != (cook > 0) or (ready and state != "ready")
                    or (state == "idle") != (stove["dish"] is None)):
                raise BadInput("trạng thái, món và timer bếp mâu thuẫn")
            if stove["dish"] is not None:
                dishes.append(stove["dish"])
        if self.hand is not None:
            dishes.append(self.hand)
        assigned = {c["id"]: c for c in self.customers if c["order_status"] == "assigned"}
        for dish in dishes:
            if (not isinstance(dish, dict) or set(dish) != {"order_id", "dish_id", "base_price"}
                    or not isinstance(dish["order_id"], str) or not _count(dish["base_price"])):
                raise BadInput("payload món không hợp lệ")
            c = assigned.pop(dish["order_id"], None)
            if (c is None or c["dish_id"] != dish["dish_id"]
                    or c.get("base_price", dish["base_price"]) != dish["base_price"]):
                raise BadInput("món trên bếp/tay không khớp đơn assigned duy nhất")
        if assigned:
            raise BadInput("đơn assigned thiếu món")

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        if self.item_mode:
            stock_snap = snapshot_units(self.stock)
        else:
            stock_snap = {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}
        customers = []
        for c in sort_by_id(self.customers):
            row = dict(c)
            if self.item_mode and isinstance(row.get("reserved"), list):
                row["reserved"] = list(row["reserved"])
            customers.append(row)
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": stock_snap,
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": customers,
        }

    def step(self, inp):
        """Thứ tự P3 quán: đồng hồ → hao tươi/spoiled/giữ lại → (cháy) → move → interact → leave → spawn."""
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for c in self.customers:
            timer = "eat_ticks_left" if c["state"] == "eating" else "patience_ticks_left"
            c[timer] = max(0, c[timer] - 1)
        for stove in self.stoves:
            if stove["state"] == "ready":
                stove["ready_ticks"] += 1
            elif stove["state"] == "cooking":
                stove["cook_ticks_left"] -= 1
                if stove["cook_ticks_left"] == 0:
                    stove.update(state="ready", ready_ticks=0)
                    events.append(("dish_ready", self._stove_event(stove)))

        events.extend(self.decay_and_rereserve())

        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        for c in sort_by_id(self.customers, key=lambda c: c["table_id"]):
            if c["state"] == "eating":
                if c["eat_ticks_left"] == 0:
                    self._pay(c, "finished_eating", events)
                elif self.time_left_ticks == 0:
                    self._pay(c, "closing", events)
            elif self.time_left_ticks == 0 or c["patience_ticks_left"] == 0:
                self._leave(c, events)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        events.extend(self.try_spawn_customer())
        return events

    @staticmethod
    def _stove_event(stove):
        dish = stove["dish"]
        return {"stove_id": stove["id"], "order_id": dish["order_id"], "dish_id": dish["dish_id"]}

    def _interact(self, events):
        targets = self.stoves + self.tables
        target = min(targets, key=lambda obj: math.dist(self.pos, obj["pos"]))
        if math.dist(self.pos, target["pos"]) > self.t["interact_radius"]:
            return
        if "state" in target:
            if target["state"] == "idle":
                self._start_cooking(target, events)
            elif target["state"] == "ready" and self.hand is None:
                events.append(("dish_picked", self._stove_event(target)))
                self.hand = target["dish"]
                _idle(target)
        elif self.hand is not None:
            for c in self.customers:
                if c["table_id"] == target["id"] and c["id"] == self.hand["order_id"]:
                    self._serve(c, events)
                    break

    def _start_cooking(self, stove, events):
        waiting = (c for c in self.customers if c["order_status"] == "reserved")
        c = min(waiting, key=lambda c: (c["order_tick"], id_key(c["table_id"])), default=None)
        if c is None:
            return
        menu = self.menu[c["dish_id"]]
        if isinstance(c["reserved"], list):
            items, base_price = self._consume_reserved_units(c["reserved"], menu["price"])
            reserved = []
        else:
            items = []
            for kind, amount in sorted(c["reserved"].items()):
                self.stock[kind] -= amount
                items.extend([kind] * amount)
            base_price = menu["price"]
            reserved = {}
        dish = {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": base_price}
        c.update(order_status="assigned", reserved=reserved, base_price=base_price)
        stove.update(state="cooking", dish=dish, cook_ticks_left=round(menu["cook_s"] * self.hz))
        events.append(("cook_started", dict(self._stove_event(stove), items=items, base_price=base_price)))

    def _consume_reserved_units(self, reserved, listed_price):
        by_id = {item["id"]: item for item in self.stock}
        used = sorted((by_id[iid] for iid in reserved), key=lambda item: (item["kind"], id_key(item["id"])))
        # Tính trên độ tươi nội bộ, tránh làm tròn trung bình sát biên floor.
        price = price_for_items(listed_price, used)
        consumed = set(reserved)
        self.stock[:] = [item for item in self.stock if item["id"] not in consumed]
        return [dict(item) for item in used], price

    def _serve(self, c, events):
        price = self.hand["base_price"]
        tip = 0
        if c["patience_ticks_left"] / self.patience >= self.t["tip_min_patience_ratio"]:
            tip = int(price * Decimal(str(self.t["tip_rate"])))
        c.update(state="eating", order_status="served", eat_ticks_left=round(self.t["eat_s"] * self.hz),
                 base_price=price, tip=tip)
        self.hand = None
        events.append(("served", {"order_id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                                  "patience_ticks_left": c["patience_ticks_left"], "base_price": price, "tip": tip}))

    def _change_reputation(self, delta):
        value = float(Decimal(str(self.reputation)) + Decimal(str(delta)))
        self.reputation = min(self.t["reputation_max"], max(self.t["reputation_min"], value))

    def _pay(self, c, reason, events):
        amount = c["base_price"] + c["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:
            self._change_reputation(self.t["tip_reputation"])
        events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": c["base_price"],
                                "tip": c["tip"], "amount": amount, "reason": reason}))
        self.customers.remove(c)

    def _leave(self, c, events):
        reason = "closing" if self.time_left_ticks == 0 else "patience"
        if reason == "patience":
            self._change_reputation(self.t["left_reputation_delta"])
        for stove in self.stoves:
            if stove["dish"] and stove["dish"]["order_id"] == c["id"]:
                _idle(stove)
        if self.hand and self.hand["order_id"] == c["id"]:
            self.hand = None
        if self.item_mode:
            c["reserved"] = []
        self.customers.remove(c)
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"],
                                         "reason": reason, "reputation": self.reputation}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / self.hz
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
