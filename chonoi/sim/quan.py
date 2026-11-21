"""Buổi tối — Mở Quán (`quan`).

Luật chơi Phase 1 theo PRD-0 mục F:
- Khách đến theo lịch (first_customer_tick, customer_interval_s), chọn món nấu được, giữ chỗ nguyên liệu.
- Bếp & bưng món: `chonoi/sim/kitchen.py` (`step_stoves`, `interact_stove`).
- Phục vụ, thanh toán & đóng ca: `chonoi/sim/service.py` (`interact_table`, `step_service_and_closing`).
"""


import math
from fractions import Fraction

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from .kitchen import _re_reserve_v12, interact_stove, step_stoves

from .ramp import ramp_velocity
from .service import handle_table_interact, update_service

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, dish_pool=None):
        """Khởi tạo mô phỏng Quán (`quan`).

        dish_pool: iterable các dish_id trong kế hoạch ngày (mode day); None nếu dùng toàn bộ menu (mode quan độc lập).
        """
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.freshness = tuning.get("freshness") or {}
        hz = Fraction(str(tuning.get("tick_hz", 60.0)))
        if self.freshness:
            self.spoiled_below = Fraction(str(self.freshness.get("spoiled_below", 30)))
            self.decay_per_tick = Fraction(str(self.freshness.get("quan_decay_per_s", 0.25))) / hz
        else:
            self.spoiled_below = Fraction(30)
            self.decay_per_tick = Fraction("0.25") / hz

        if dish_pool is None:
            self.dish_pool = None
        else:
            self.dish_pool = sorted(set(dish_pool))
            if not self.dish_pool:
                raise BadInput("dish_pool không được rỗng")
            for dish_id in self.dish_pool:
                if dish_id not in self.menu:
                    raise BadInput(f"dish_pool chứa món không có trong menu: {dish_id}")
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        raw_stock = inventory if inventory is not None else scenario.get("stock", {})
        if isinstance(raw_stock, list):
            seen_stock_ids = set()
            self.stock = []
            for it in raw_stock:
                if not isinstance(it, dict) or "id" not in it or "kind" not in it or "fresh" not in it:
                    raise BadInput("mỗi phần tử trong stock cá thể phải có id, kind, fresh")
                if it["id"] in seen_stock_ids:
                    raise BadInput(f"id cá thể trùng trong kho: {it['id']}")
                seen_stock_ids.add(it["id"])
                fresh_val = it["fresh"]
                if isinstance(fresh_val, bool) or not isinstance(fresh_val, (int, float, Fraction)):
                    raise BadInput(f"fresh không hợp lệ cho {it['id']}: {fresh_val!r}")
                self.stock.append({
                    "id": it["id"],
                    "kind": it["kind"],
                    "fresh": Fraction(str(fresh_val)) if not isinstance(fresh_val, Fraction) else fresh_val,
                })
            self.stock = sort_by_id(self.stock)
        else:
            self.stock = dict(raw_stock)

        self.hand = dict(scenario["hand"]) if scenario.get("hand") is not None else None
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))
        self.stoves = [
            dict(
                s,
                pos=[float(c) for c in s["pos"]],
                state=s.get("state", "idle"),
                dish=dict(s["dish"]) if s.get("dish") is not None else None,
                cook_ticks_left=s.get("cook_ticks_left", 0),
                ready_ticks=s.get("ready_ticks", 0),
            )
            for s in self._merge(t["stoves"], scenario.get("stoves", []))
        ]
        self.tables = [
            dict(tb, pos=[float(c) for c in tb["pos"]])
            for tb in self._merge(t["tables"], scenario.get("tables", []))
        ]
        pat_max = int(round(t["patience_s"] * TICK))
        self.customers = []
        for c in scenario.get("customers", []):
            cust = {
                "id": c["id"],
                "table_id": c["table_id"],
                "dish_id": c["dish_id"],
                "order_tick": c.get("order_tick", 0),
                "state": c.get("state", "waiting"),
                "patience_ticks_left": c.get("patience_ticks_left", pat_max),
                "eat_ticks_left": c.get("eat_ticks_left", 0),
                "order_status": c.get("order_status", "reserved"),
                "base_price": c.get("base_price", 0),
                "tip": c.get("tip", 0),
            }
            if "reserved" in c:
                if isinstance(c["reserved"], list):
                    cust["reserved"] = list(c["reserved"])
                elif isinstance(c["reserved"], dict):
                    cust["reserved"] = dict(c["reserved"])
                elif c["reserved"] is None:
                    cust["reserved"] = None
                else:
                    raise BadInput(f"reserved của khách {c['id']} không hợp lệ")
            else:
                cust["reserved"] = None
            self.customers.append(cust)
            ids.reserve(c["id"])

        if isinstance(self.stock, list):
            # v1.2: Validation và cấp reserved theo id cá thể
            stock_by_id = {it["id"]: it for it in self.stock}
            seen_reserved_ids = set()

            for c in self.customers:
                status = c.get("order_status")
                res = c.get("reserved")
                if status in ("unfulfillable", "assigned"):
                    if res not in (None, []):
                        raise BadInput(f"đơn {status} {c['id']} phải có reserved rỗng")
                    c["reserved"] = []
                elif res is not None:
                    if not isinstance(res, list):
                        raise BadInput(f"reserved của khách {c['id']} phải là mảng id cá thể")
                    counts = {}
                    for iid in res:
                        if iid not in stock_by_id:
                            raise BadInput(f"id {iid} trong reserved của {c['id']} không có trong kho")
                        it = stock_by_id[iid]
                        if it["fresh"] < self.spoiled_below:
                            raise BadInput(f"cá thể {iid} trong reserved của {c['id']} đã bị ươn")
                        if iid in seen_reserved_ids:
                            raise BadInput(f"hai đơn dùng chung cá thể {iid}")
                        seen_reserved_ids.add(iid)
                        counts[it["kind"]] = counts.get(it["kind"], 0) + 1

                    recipe = self.menu[c["dish_id"]]["recipe"]
                    if counts != recipe:
                        raise BadInput(f"nguyên liệu trong reserved không khớp công thức món {c['dish_id']}")

            # Tự cấp reserved cho đơn reserved chưa có reserved
            missing_res = [c for c in self.customers if c["order_status"] == "reserved" and c["reserved"] is None]
            missing_res.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
            for c in missing_res:
                _re_reserve_v12(self, c, self.menu[c["dish_id"]]["recipe"], self.spoiled_below)

            for c in self.customers:
                if c["reserved"] is None:
                    c["reserved"] = []
        else:
            # v1.1: Validation và cấp reserved theo dict đếm (logic cũ)
            missing_res = [c for c in self.customers if c["order_status"] == "reserved" and c["reserved"] is None]
            missing_res.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
            for c in missing_res:
                c["reserved"] = dict(self.menu[c["dish_id"]]["recipe"])
            for c in self.customers:
                if c["reserved"] is None:
                    c["reserved"] = {}

            total_res = {}
            for c in self.customers:
                for k, q in c["reserved"].items():
                    total_res[k] = total_res.get(k, 0) + q
            for k, q in total_res.items():
                if q > self.stock.get(k, 0):
                    raise BadInput(f"giữ chỗ vượt quá tồn kho cho {k}: {q} > {self.stock.get(k, 0)}")

        # Kiểm tra mâu thuẫn kịch bản: đơn assigned phải có bếp nấu, khách eating phải có base_price
        cooking_orders = {s["dish"]["order_id"] for s in self.stoves if s.get("dish")}
        for c in self.customers:
            if c.get("order_status") == "assigned" and c["id"] not in cooking_orders:
                raise BadInput(f"đơn assigned {c['id']} phải có bếp đang nấu")
            if c.get("state") == "eating" and (not c.get("base_price") or c["base_price"] <= 0):
                raise BadInput(f"khách eating {c['id']} thiếu base_price")

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

    def _clamp_rep(self, val: float) -> float:
        return min(float(self.t["reputation_max"]), max(float(self.t["reputation_min"]), val))

    def _release_customer_order(self, order_id: str):
        if self.hand is not None and self.hand["order_id"] == order_id:
            self.hand = None
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == order_id:
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        if isinstance(self.stock, list):
            stock_snap = [
                {
                    "id": it["id"],
                    "kind": it["kind"],
                    "fresh": round(float(it["fresh"]), 3),
                }
                for it in sort_by_id(self.stock)
            ]
        else:
            stock_snap = {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}

        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": stock_snap,
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in sort_by_id(self.stoves)],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])}
                       for tb in sort_by_id(self.tables)],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []

        # 1. Tăng đồng hồ và giảm timer ca
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        shift_closing = self.time_left_ticks <= 0

        for c in self.customers:
            if c["state"] in ("waiting", "waiting_dish"):
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
            elif c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)

        # 2. HAO TƯƠI kho thô và phát spoiled (v1.2)
        if isinstance(self.stock, list):
            spoiled_events = []
            just_spoiled_ids = set()
            for it in self.stock:
                old_fresh = it["fresh"]
                new_fresh = max(Fraction(0), old_fresh - self.decay_per_tick)
                it["fresh"] = new_fresh
                if old_fresh >= self.spoiled_below and new_fresh < self.spoiled_below:
                    just_spoiled_ids.add(it["id"])
                    spoiled_events.append((it["id"], it["kind"]))

            spoiled_events.sort(key=lambda x: id_key(x[0]))
            for iid, kind in spoiled_events:
                events.append(("spoiled", {
                    "item_id": iid,
                    "kind": kind,
                    "location": "stock",
                }))

            # Xử lý các đơn có phần giữ vừa ươn:
            # Nhả toàn bộ phần giữ của đơn và giữ lại đúng 1 lần bằng _re_reserve_v12.
            # Nhiều đơn bị ảnh hưởng thì xử lý theo (order_tick, id bàn).
            if just_spoiled_ids:
                affected = [
                    c for c in self.customers
                    if c.get("order_status") == "reserved" and any(iid in just_spoiled_ids for iid in c.get("reserved", []))
                ]
                affected.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
                for c in affected:
                    c["reserved"] = []
                    recipe = self.menu[c["dish_id"]]["recipe"]
                    _re_reserve_v12(self, c, recipe, self.spoiled_below)

        # 3. Bếp: đếm nấu / ready_ticks và chuyển cooking -> ready (Người A)
        step_stoves(self, events)

        # 4. Di chuyển rồi xét tối đa một interact (Người A: bếp | Người B: bàn)
        self._move(inp)
        if inp.pressed("interact"):
            self._handle_interact(events)

        # 5. Tiến trình ăn, kiên nhẫn, thanh toán (Người B) & đóng ca
        events.extend(update_service(self))
        if shift_closing:
            for c in list(self.customers):
                dish_name = c.get("dish_id") or c.get("dish")
                if c.get("state") == "eating":
                    base_price = c.get("base_price") or int(self.menu.get(dish_name, {}).get("price", 0))
                    tip = c.get("tip", 0)
                    total = base_price + tip
                    self.money += total
                    self.earned += total
                    self.shift_earned += total
                    events.append(("paid", {
                        "order_id": c.get("id"),
                        "customer_id": c.get("id"),
                        "dish_id": dish_name,
                        "dish": dish_name,
                        "amount": total,
                        "tip": tip,
                        "reputation": round(float(self.reputation), 3),
                        "reason": "shift_closing",
                    }))
                elif c.get("state") in ("waiting", "waiting_dish"):
                    events.append(("customer_left", {
                        "order_id": c.get("id"),
                        "customer_id": c.get("id"),
                        "table_id": c.get("table_id"),
                        "reason": "closing",
                        "reputation": round(float(self.reputation), 3),
                    }))

            self.hand = None
            self.customers = []
            for s in self.stoves:
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0

            self.done = True
            self.reason = "time"
            events.append(("quan_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": round(float(self.reputation), 3),
            }))
            return events

        # 6. Khách mới theo lịch
        if self.random_customers:
            first = int(self.t["first_customer_tick"])
            interval = int(round(self.t["customer_interval_s"] * TICK))
            if self.phase_tick >= first and (self.phase_tick - first) % interval == 0:
                occupied = {c["table_id"] for c in self.customers}
                free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
                if free_tables:
                    if isinstance(self.stock, list):
                        taken = {iid for c in self.customers for iid in c.get("reserved", [])}
                        available_items = [
                            it for it in self.stock
                            if it["id"] not in taken and it["fresh"] >= self.spoiled_below
                        ]
                        avail_counts = {}
                        for it in available_items:
                            k = it["kind"]
                            avail_counts[k] = avail_counts.get(k, 0) + 1

                        candidates = self.dish_pool if self.dish_pool is not None else sorted(self.menu.keys())
                        affordable = [
                            dish_id for dish_id in candidates
                            if all(avail_counts.get(k, 0) >= q for k, q in self.menu[dish_id]["recipe"].items())
                        ]
                        if not affordable:
                            events.append(("no_dish", {}))
                        else:
                            tb = free_tables[0]
                            dish_id = self.rng.get("customer_dish").choice(affordable)
                            cid = self.ids.new("C")
                            recipe = self.menu[dish_id]["recipe"]

                            picked_ids = []
                            for kind in sorted(recipe.keys()):
                                need = recipe[kind]
                                cands = [
                                    it for it in available_items
                                    if it["kind"] == kind and it["id"] not in picked_ids
                                ]
                                cands.sort(key=lambda it: (-it["fresh"], id_key(it["id"])))
                                for it in cands[:need]:
                                    picked_ids.append(it["id"])

                            self.customers.append({
                                "id": cid,
                                "table_id": tb["id"],
                                "dish_id": dish_id,
                                "order_tick": self.phase_tick,
                                "state": "waiting",
                                "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
                                "eat_ticks_left": 0,
                                "order_status": "reserved",
                                "reserved": picked_ids,
                                "base_price": 0,
                                "tip": 0,
                            })
                            events.append(("customer_arrived", {
                                "order_id": cid,
                                "table_id": tb["id"],
                                "dish_id": dish_id,
                            }))
                    else:
                        avail = dict(self.stock)
                        for c in self.customers:
                            for k, q in c.get("reserved", {}).items():
                                avail[k] = avail.get(k, 0) - q
                        candidates = self.dish_pool if self.dish_pool is not None else sorted(self.menu.keys())
                        affordable = [
                            dish_id for dish_id in candidates
                            if all(avail.get(k, 0) >= q for k, q in self.menu[dish_id]["recipe"].items())
                        ]
                        if not affordable:
                            events.append(("no_dish", {}))
                        else:
                            tb = free_tables[0]
                            dish_id = self.rng.get("customer_dish").choice(affordable)
                            cid = self.ids.new("C")
                            recipe = dict(self.menu[dish_id]["recipe"])
                            self.customers.append({
                                "id": cid,
                                "table_id": tb["id"],
                                "dish_id": dish_id,
                                "order_tick": self.phase_tick,
                                "state": "waiting",
                                "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
                                "eat_ticks_left": 0,
                                "order_status": "reserved",
                                "reserved": recipe,
                                "base_price": 0,
                                "tip": 0,
                            })
                            events.append(("customer_arrived", {
                                "order_id": cid,
                                "table_id": tb["id"],
                                "dish_id": dish_id,
                            }))

        return events

    def _handle_interact(self, events):
        ir = float(self.t["interact_radius"])
        cands = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= ir:
                cands.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= ir:
                cands.append((d, 1, id_key(tb["id"]), "table", tb))
        if not cands:
            return
        cands.sort(key=lambda x: (x[0], x[1], x[2]))
        _, _, _, kind, obj = cands[0]

        if kind == "stove":
            interact_stove(self, obj, events)
        elif kind == "table":
            events.extend(handle_table_interact(self, obj))

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
