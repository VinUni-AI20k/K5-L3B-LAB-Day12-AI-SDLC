"""Mô phỏng quán ăn buổi tối (Chế độ Quan) — adapter kho cá thể v1.2 (Turn 4)."""

from __future__ import annotations

import math
from collections import Counter
from decimal import Decimal

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import FRESH_SCALE, fresh_to_units, serialize_item, validate_items
from ..scenario import validate_quan_state
from .ramp import ramp_velocity


def _round3(v: float) -> float:
    return round(float(v), 3)


def _floor_mul(value: int, rate: float) -> int:
    return math.floor(Decimal(value) * Decimal(str(rate)))


def _ratio_ge(num: int, den: int, threshold: float) -> bool:
    if den <= 0:
        return False
    return Decimal(num) / Decimal(den) >= Decimal(str(threshold))


class QuanSim:
    """Mô phỏng điều hành quán ăn buổi tối với kho cá thể v1.2."""

    def __init__(
        self,
        tuning: dict,
        scenario: dict,
        rng,
        ids,
        inventory: list | None = None,
        *,
        initial_money: int = 0,
        initial_earned: int = 0,
        initial_reputation: float | None = None,
        allowed_dishes: list[str] | None = None,
    ):
        self.tuning = tuning
        self.t = tuning["quan"]
        self.menu = tuning["menu"]
        self.tick_hz = int(tuning["tick_hz"])
        self.rng = rng
        self.ids = ids
        self.allowed_dishes = sorted(allowed_dishes) if allowed_dishes is not None else sorted(self.menu)

        self.mode = "quan"
        self.phase = "quan"
        self.phase_tick = 0
        self.done = False
        self.reason = None

        fr = tuning["freshness"]
        self.spoil_th = float(fr["spoiled_below"])
        self.spoil_u = fresh_to_units(self.spoil_th, self.spoil_th)
        self.quan_decay_u = int(round(float(fr["quan_decay_per_s"]) * FRESH_SCALE / self.tick_hz))

        if not isinstance(scenario, dict):
            raise BadInput("quan phải là object")
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
        raw_stock = inventory if inventory is not None else scenario.get("stock", [])
        parsed_stock = validate_items(raw_stock, spoiled_below=self.spoil_th)
        self.stock = sort_by_id([
            {"id": it["id"], "kind": it["kind"], "fresh_u": it["fresh_u"]}
            for it in parsed_stock
        ])
        for it in self.stock:
            self.ids.reserve(it["id"])

        fixture_customers, auto_reserved = validate_quan_state(scenario, tuning, stock_map=raw_stock)

        self.duration_ticks = round(self.t["duration_s"] * self.tick_hz)
        self.time_left_ticks = int(scenario.get("time_left_ticks", self.duration_ticks))
        self.patience_max_ticks = round(self.t["patience_s"] * self.tick_hz)
        self.eat_ticks_full = round(self.t["eat_s"] * self.tick_hz)
        self.customer_interval_ticks = round(self.t["customer_interval_s"] * self.tick_hz)
        self.carry_limit = int(self.t["carry_limit"])
        self.burn_ticks = round(float(self.t["burn_s"]) * self.tick_hz) if self.t.get("burn_s") is not None else None
        self.random_customers = bool(scenario.get("random_customers", True))

        self.money = int(initial_money)
        self.earned = int(initial_earned)
        self.shift_earned = 0
        base_rep = self.t["reputation_initial"] if initial_reputation is None else initial_reputation
        self.reputation = float(scenario.get("reputation", base_rep))

        p = scenario.get("player", {})
        spos = p.get("pos", self.t["start_pos"])
        svel = p.get("vel", [0.0, 0.0])
        self.pos = [float(spos[0]), float(spos[1])]
        self.vel = [float(svel[0]), float(svel[1])]
        self._tgt = None
        self._ramp_left = 0

        hand = scenario.get("hand")
        self.hand = dict(hand) if hand is not None else None

        stove_map = {}
        for s in self.t["stoves"]:
            self.ids.reserve(s["id"])
            stove_map[s["id"]] = {
                "id": s["id"],
                "pos": [float(s["pos"][0]), float(s["pos"][1])],
                "state": "idle",
                "dish": None,
                "cook_ticks_left": 0,
                "ready_ticks": 0,
            }
        for s in scenario.get("stoves", []):
            st = stove_map[s["id"]]
            if "pos" in s:
                st["pos"] = [float(s["pos"][0]), float(s["pos"][1])]
            state = s.get("state", "idle")
            st["state"] = state
            st["dish"] = dict(s["dish"]) if s.get("dish") is not None else None
            st["cook_ticks_left"] = int(s.get("cook_ticks_left", 0))
            st["ready_ticks"] = int(s.get("ready_ticks", 0))
        self.stoves = sort_by_id(list(stove_map.values()))

        table_map = {}
        for tb in self.t["tables"]:
            self.ids.reserve(tb["id"])
            table_map[tb["id"]] = {
                "id": tb["id"],
                "pos": [float(tb["pos"][0]), float(tb["pos"][1])],
            }
        for tb in scenario.get("tables", []):
            if "pos" in tb:
                table_map[tb["id"]]["pos"] = [float(tb["pos"][0]), float(tb["pos"][1])]
        self.tables = sort_by_id(list(table_map.values()))

        customers = []
        for c in fixture_customers:
            cid = c["id"]
            self.ids.reserve(cid)
            ostatus = c.get("order_status", "reserved")
            if "reserved" in c:
                reserved = sorted(c["reserved"], key=id_key)
            elif ostatus == "reserved":
                reserved = sorted(auto_reserved[cid], key=id_key)
            else:
                reserved = []
            customers.append({
                "id": cid,
                "table_id": c["table_id"],
                "dish_id": c["dish_id"],
                "order_tick": int(c.get("order_tick", 0)),
                "state": c.get("state", "waiting"),
                "patience_ticks_left": int(c.get("patience_ticks_left", self.patience_max_ticks)),
                "eat_ticks_left": int(c.get("eat_ticks_left", 0)),
                "order_status": ostatus,
                "reserved": reserved,
                "base_price": int(c.get("base_price", 0)),
                "tip": int(c.get("tip", 0)),
            })
        self.customers = sort_by_id(customers)

    def snapshot(self) -> dict:
        occ = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {
                "pos": [_round3(self.pos[0]), _round3(self.pos[1])],
                "vel": [_round3(self.vel[0]), _round3(self.vel[1])],
            },
            "stock": sort_by_id([serialize_item(it) for it in self.stock]),
            "hand": dict(self.hand) if self.hand is not None else None,
            "stoves": [
                {
                    "id": s["id"],
                    "pos": [_round3(s["pos"][0]), _round3(s["pos"][1])],
                    "state": s["state"],
                    "dish": dict(s["dish"]) if s["dish"] is not None else None,
                    "cook_ticks_left": int(s["cook_ticks_left"]),
                    "ready_ticks": int(s["ready_ticks"]),
                }
                for s in sort_by_id(self.stoves)
            ],
            "tables": [
                {
                    "id": tb["id"],
                    "pos": [_round3(tb["pos"][0]), _round3(tb["pos"][1])],
                    "customer_id": occ.get(tb["id"]),
                }
                for tb in sort_by_id(self.tables)
            ],
            "customers": [
                {
                    "id": c["id"],
                    "table_id": c["table_id"],
                    "dish_id": c["dish_id"],
                    "order_tick": int(c["order_tick"]),
                    "state": c["state"],
                    "patience_ticks_left": int(c["patience_ticks_left"]),
                    "eat_ticks_left": int(c["eat_ticks_left"]),
                    "order_status": c["order_status"],
                    "reserved": sorted(c["reserved"], key=id_key),
                    "base_price": int(c["base_price"]),
                    "tip": int(c["tip"]),
                }
                for c in sort_by_id(self.customers)
            ],
        }

    def step(self, inp) -> list:
        if self.done:
            return []
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # 1. Đồng hồ & bộ đếm (tăng ready_ticks cho món đã ready từ đầu bước)
        already_ready = self._tick_stoves_and_customers()

        # 2. Hao tươi kho thô (-1 đv/tick), phát spoiled theo id rồi tái giữ chỗ 1 lần
        self._step_raw_stock_freshness(events)

        # 3. Xét món chín theo id bếp
        self._resolve_stoves_after_timers(already_ready, events)

        # 4. Di chuyển rồi xét tối đa một interact (theo đúng đối tượng gần nhất)
        self._move(inp)
        if inp.pressed("interact"):
            self._try_interact(events)

        # 5. Khách ăn xong trả tiền; hết kiên nhẫn hoặc đóng ca rời bàn
        self._settle_and_leave(events)
        if self.done:
            return events

        # 6. Khách mới (nếu còn giờ)
        self._maybe_spawn_customer(events)
        return events

    def _tick_stoves_and_customers(self) -> set[str]:
        already_ready = {st["id"] for st in self.stoves if st["state"] == "ready"}
        for st in sort_by_id(self.stoves):
            if st["id"] in already_ready:
                st["ready_ticks"] += 1
            elif st["state"] == "cooking":
                st["cook_ticks_left"] = max(0, int(st["cook_ticks_left"]) - 1)
        for c in sort_by_id(self.customers):
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, int(c["eat_ticks_left"]) - 1)
            else:
                c["patience_ticks_left"] = max(0, int(c["patience_ticks_left"]) - 1)
        return already_ready

    def _try_reserve_customer(self, c: dict) -> bool:
        """Thử giữ lại đúng một lần từ kho thô khả dụng chưa ươn (tươi nhất trước, hòa theo id)."""
        recipe = self.menu[c["dish_id"]]["recipe"]
        reserved_ids = {iid for other in self.customers for iid in other["reserved"]}
        avail_items = [
            it for it in self.stock
            if it["id"] not in reserved_ids and it["fresh_u"] >= self.spoil_u
        ]
        picked = []
        for k, amt in sorted(recipe.items()):
            cands = [it for it in avail_items if it["kind"] == k]
            cands.sort(key=lambda it: (-it["fresh_u"], id_key(it["id"])))
            if len(cands) < amt:
                c["reserved"] = []
                c["order_status"] = "unfulfillable"
                return False
            chosen = cands[:amt]
            chosen_ids = {it["id"] for it in chosen}
            avail_items = [it for it in avail_items if it["id"] not in chosen_ids]
            picked.extend(chosen_ids)
        c["reserved"] = sorted(picked, key=id_key)
        c["order_status"] = "reserved"
        return True

    def _step_raw_stock_freshness(self, events: list):
        newly_spoiled = set()
        for it in sort_by_id(self.stock):
            prev_u = it["fresh_u"]
            it["fresh_u"] = max(0, prev_u - self.quan_decay_u)
            if prev_u >= self.spoil_u and it["fresh_u"] < self.spoil_u:
                newly_spoiled.add(it["id"])
                events.append(("spoiled", {
                    "item_id": it["id"],
                    "kind": it["kind"],
                    "location": "stock",
                }))
        if not newly_spoiled:
            return
        affected = [
            c for c in self.customers
            if c["state"] == "waiting"
            and c["order_status"] == "reserved"
            and any(iid in newly_spoiled for iid in c["reserved"])
        ]
        affected.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        for c in affected:
            c["reserved"] = []
            self._try_reserve_customer(c)

    def _resolve_stoves_after_timers(self, already_ready: set[str], events: list):
        by_cust = {c["id"]: c for c in self.customers}
        for st in sort_by_id(self.stoves):
            if st["id"] not in already_ready and st["state"] == "cooking" and st["cook_ticks_left"] == 0:
                st["state"] = "ready"
                st["ready_ticks"] = 0
                d = st["dish"]
                events.append(("dish_ready", {
                    "stove_id": st["id"],
                    "order_id": d["order_id"],
                    "dish_id": d["dish_id"],
                }))
            elif (
                self.burn_ticks is not None
                and st["id"] in already_ready
                and st["state"] == "ready"
                and st["ready_ticks"] > self.burn_ticks
            ):
                d = st["dish"]
                st["state"] = "idle"
                st["dish"] = None
                st["cook_ticks_left"] = 0
                st["ready_ticks"] = 0
                c = by_cust.get(d["order_id"])
                status = "unfulfillable"
                if c is not None and c["state"] == "waiting":
                    self._try_reserve_customer(c)
                    status = c["order_status"]
                events.append(("dish_burnt", {
                    "stove_id": st["id"],
                    "order_id": d["order_id"],
                    "dish_id": d["dish_id"],
                    "order_status": status,
                }))

    def _move(self, inp):
        speed = float(self.t["walk_speed"])
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), self.t["ramp_max_ticks"])
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / self.tick_hz
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = float(lo), max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = float(hi), min(0.0, self.vel[i])

    def _try_interact(self, events: list):
        radius = float(self.t["interact_radius"])
        candidates = []
        for st in self.stoves:
            d = math.dist(self.pos, st["pos"])
            if d <= radius:
                candidates.append((d, 0, id_key(st["id"]), "stove", st))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= radius:
                candidates.append((d, 1, id_key(tb["id"]), "table", tb))
        if not candidates:
            return
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        _, _, _, kind, obj = candidates[0]
        if kind == "stove":
            self._interact_stove(obj, events)
        else:
            self._interact_table(obj, events)

    def _oldest_reserved_customer(self):
        waiting = [
            c for c in self.customers
            if c["state"] == "waiting" and c["order_status"] == "reserved"
        ]
        if not waiting:
            return None
        waiting.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        return waiting[0]

    def _interact_stove(self, st: dict, events: list) -> bool:
        if st["state"] == "ready":
            if self.hand is not None or self.carry_limit < 1:
                return False
            dish = st["dish"]
            self.hand = dict(dish)
            st["state"] = "idle"
            st["dish"] = None
            st["cook_ticks_left"] = 0
            st["ready_ticks"] = 0
            events.append(("dish_picked", {
                "stove_id": st["id"],
                "order_id": dish["order_id"],
                "dish_id": dish["dish_id"],
            }))
            return True

        if st["state"] == "idle":
            customer = self._oldest_reserved_customer()
            if customer is None:
                return False
            dish_id = customer["dish_id"]
            res_set = set(customer["reserved"])
            consumed = [it for it in self.stock if it["id"] in res_set]
            self.stock = [it for it in self.stock if it["id"] not in res_set]
            consumed.sort(key=lambda it: (it["kind"], id_key(it["id"])))
            items = [serialize_item(it) for it in consumed]

            base_price = (int(self.menu[dish_id]["price"]) * sum(it["fresh_u"] for it in consumed)) // (
                len(consumed) * 100 * FRESH_SCALE
            )
            payload = {
                "order_id": customer["id"],
                "dish_id": dish_id,
                "base_price": base_price,
            }
            customer["reserved"] = []
            customer["order_status"] = "assigned"
            customer["base_price"] = base_price
            st["state"] = "cooking"
            st["dish"] = payload
            st["cook_ticks_left"] = round(self.menu[dish_id]["cook_s"] * self.tick_hz)
            st["ready_ticks"] = 0
            events.append(("cook_started", {
                "stove_id": st["id"],
                "order_id": customer["id"],
                "dish_id": dish_id,
                "items": items,
                "base_price": base_price,
            }))
            return True
        return False

    def _interact_table(self, tb: dict, events: list) -> bool:
        if self.hand is None:
            return False
        order_id = self.hand["order_id"]
        dish_id = self.hand["dish_id"]
        base_price = int(self.hand["base_price"])
        for c in sort_by_id(self.customers):
            if (
                c["table_id"] == tb["id"]
                and c["id"] == order_id
                and c["state"] == "waiting"
                and c["order_status"] == "assigned"
                and c["dish_id"] == dish_id
            ):
                if _ratio_ge(c["patience_ticks_left"], self.patience_max_ticks, self.t["tip_min_patience_ratio"]):
                    tip = _floor_mul(base_price, self.t["tip_rate"])
                else:
                    tip = 0
                self.hand = None
                c["state"] = "eating"
                c["order_status"] = "served"
                c["eat_ticks_left"] = self.eat_ticks_full
                c["base_price"] = base_price
                c["tip"] = tip
                events.append(("served", {
                    "order_id": c["id"],
                    "table_id": tb["id"],
                    "dish_id": dish_id,
                    "patience_ticks_left": c["patience_ticks_left"],
                    "base_price": base_price,
                    "tip": tip,
                }))
                return True
        return False

    def _clear_order_dish(self, order_id: str):
        if self.hand is not None and self.hand.get("order_id") == order_id:
            self.hand = None
        for st in self.stoves:
            if st["dish"] is not None and st["dish"].get("order_id") == order_id:
                st["state"] = "idle"
                st["dish"] = None
                st["cook_ticks_left"] = 0
                st["ready_ticks"] = 0

    def _clamp_rep(self, val: float) -> float:
        lo = float(self.t["reputation_min"])
        hi = float(self.t["reputation_max"])
        return min(hi, max(lo, round(val, 6)))

    def _settle_and_leave(self, events: list):
        closing = self.time_left_ticks == 0
        tip_rep = float(self.t["tip_reputation"])
        left_delta = float(self.t["left_reputation_delta"])

        by_table = sort_by_id(self.customers, key=lambda c: c["table_id"])
        removed = set()

        for c in by_table:
            if c["state"] != "eating":
                continue
            if c["eat_ticks_left"] == 0 or closing:
                reason = "finished_eating" if c["eat_ticks_left"] == 0 else "closing"
                base_price = int(c["base_price"])
                tip = int(c["tip"])
                amount = base_price + tip
                self.money += amount
                self.earned += amount
                self.shift_earned += amount
                if tip > 0:
                    self.reputation = self._clamp_rep(self.reputation + tip_rep)
                events.append(("paid", {
                    "order_id": c["id"],
                    "table_id": c["table_id"],
                    "base_price": base_price,
                    "tip": tip,
                    "amount": amount,
                    "reason": reason,
                }))
                removed.add(c["id"])

        for c in by_table:
            if c["id"] in removed or c["state"] != "waiting":
                continue
            if closing:
                self._clear_order_dish(c["id"])
                events.append(("customer_left", {
                    "order_id": c["id"],
                    "table_id": c["table_id"],
                    "reason": "closing",
                    "reputation": self.reputation,
                }))
                removed.add(c["id"])
            elif c["patience_ticks_left"] == 0:
                self._clear_order_dish(c["id"])
                self.reputation = self._clamp_rep(self.reputation + left_delta)
                events.append(("customer_left", {
                    "order_id": c["id"],
                    "table_id": c["table_id"],
                    "reason": "patience",
                    "reputation": self.reputation,
                }))
                removed.add(c["id"])

        if removed:
            self.customers = [c for c in self.customers if c["id"] not in removed]

        if closing:
            events.append(("quan_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation,
            }))
            self.done = True
            self.reason = "time"

    def _maybe_spawn_customer(self, events: list):
        if not self.random_customers:
            return
        since_first = self.phase_tick - int(self.t["first_customer_tick"])
        if since_first < 0 or since_first % self.customer_interval_ticks != 0:
            return
        occupied = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
        if not free_tables:
            return
        tb = free_tables[0]

        reserved_ids = {iid for c in self.customers for iid in c["reserved"]}
        avail_items = [it for it in self.stock if it["id"] not in reserved_ids and it["fresh_u"] >= self.spoil_u]
        counts = Counter(it["kind"] for it in avail_items)

        dishes = [
            dish_id for dish_id in sorted(self.allowed_dishes)
            if dish_id in self.menu and all(counts[k] >= amt for k, amt in self.menu[dish_id]["recipe"].items())
        ]
        if not dishes:
            events.append(("no_dish", {}))
            return
        dish_id = self.rng.get("customer_order").choice(dishes)
        picked = []
        for k, amt in sorted(self.menu[dish_id]["recipe"].items()):
            cands = [it for it in avail_items if it["kind"] == k]
            cands.sort(key=lambda it: (-it["fresh_u"], id_key(it["id"])))
            picked.extend(it["id"] for it in cands[:amt])
        picked.sort(key=id_key)

        order_id = self.ids.new("C")
        self.customers.append({
            "id": order_id,
            "table_id": tb["id"],
            "dish_id": dish_id,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": self.patience_max_ticks,
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": picked,
            "base_price": 0,
            "tip": 0,
        })
        self.customers = sort_by_id(self.customers)
        events.append(("customer_arrived", {
            "order_id": order_id,
            "table_id": tb["id"],
            "dish_id": dish_id,
        }))
