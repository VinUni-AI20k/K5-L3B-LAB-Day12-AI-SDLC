"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Luật chơi Lát 3 và 4 (PRD-0 mục D–F, TEAM.md):
  - Khách đến theo lịch (first_customer_tick, customer_interval_s), chọn món đủ nguyên liệu,
    giữ chỗ nguyên liệu (reserved), kiên nhẫn, bỏ đi (customer_left), thiếu món (no_dish).
  - Tương tác E: ưu tiên đối tượng theo (khoảng cách, bếp trước bàn, id).
    Bếp idle nhận đơn reserved cũ nhất (cook_started). Nấu xong chín (dish_ready).
    Bưng khi tay trống (dish_picked). Giao đúng bàn/khách (served).
  - Khách ăn xong trả tiền (paid), tính boa và uy tín.
  - Hết ca (time_left_ticks <= 0): thu tiền khách đang ăn, dọn khách chờ với lý do closing,
    phát quan_end.
"""

import math

from ..ids import id_key, sort_by_id
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
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0

        # Kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))

        # Tay người chơi: {order_id, dish_id, base_price} hoặc None
        raw_hand = scenario.get("hand")
        if isinstance(raw_hand, str):
            self.hand = {
                "order_id": None,
                "dish_id": raw_hand,
                "base_price": self.menu.get(raw_hand, {}).get("price", 0),
            }
        elif isinstance(raw_hand, dict):
            self.hand = dict(raw_hand)
        else:
            self.hand = None

        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.total_duration_ticks = int(round(t["duration_s"] * TICK))
        self.phase_tick = self.total_duration_ticks - self.time_left_ticks
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))

        # Bếp
        self.stoves = []
        for s in self._merge(t["stoves"], scenario.get("stoves", [])):
            st = dict(s)
            st.setdefault("state", "idle")
            st.setdefault("cook_ticks_left", 0)
            st.setdefault("ready_ticks", 0)
            d = st.get("dish")
            if isinstance(d, str):
                st["dish"] = {
                    "order_id": None,
                    "dish_id": d,
                    "base_price": self.menu.get(d, {}).get("price", 0),
                }
            elif isinstance(d, dict):
                st["dish"] = dict(d)
            else:
                st["dish"] = None
            self.stoves.append(st)
        self.stoves = sort_by_id(self.stoves)

        # Bàn
        self.tables = self._merge(t["tables"], scenario.get("tables", []))

        # Khách dựng sẵn từ scenario
        self.customers = []
        for c in scenario.get("customers", []):
            ids.reserve(c["id"])
            cust = dict(c)
            cust.setdefault("state", "waiting")
            cust.setdefault("order_tick", 0)
            d_id = cust.get("dish_id")
            cust.setdefault("base_price", self.menu.get(d_id, {}).get("price", 0) if d_id else 0)
            cust.setdefault("tip", 0)
            cust.setdefault("patience_ticks_left", int(round(t["patience_s"] * TICK)))
            cust.setdefault("eat_ticks_left", int(round(t["eat_s"] * TICK)))
            if "reserved" not in cust:
                if cust["state"] == "waiting" and cust.get("order_status") != "assigned":
                    cust["reserved"] = dict(self.menu[d_id]["recipe"]) if d_id in self.menu else {}
                else:
                    cust["reserved"] = {}
            cust.setdefault(
                "order_status",
                "reserved"
                if cust.get("reserved")
                else ("served" if cust["state"] == "eating" else "assigned"),
            )
            self.customers.append(cust)

        self.random_customers = scenario.get("random_customers", True)

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
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [
                {
                    "id": s["id"],
                    "pos": s["pos"],
                    "state": s["state"],
                    "dish": s["dish"],
                    "cook_ticks_left": s["cook_ticks_left"],
                    "ready_ticks": s["ready_ticks"],
                }
                for s in sort_by_id(self.stoves)
            ],
            "tables": [
                {"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])}
                for tb in sort_by_id(self.tables)
            ],
            "customers": [
                {
                    "id": c["id"],
                    "table_id": c["table_id"],
                    "dish_id": c["dish_id"],
                    "order_tick": c.get("order_tick", 0),
                    "state": c["state"],
                    "patience_ticks_left": c["patience_ticks_left"],
                    "eat_ticks_left": c["eat_ticks_left"],
                    "order_status": c["order_status"],
                    "reserved": {k: c["reserved"][k] for k in sorted(c["reserved"]) if c["reserved"][k] > 0}
                    if c.get("reserved")
                    else {},
                    "base_price": c["base_price"],
                    "tip": c["tip"],
                }
                for c in sort_by_id(self.customers)
            ],
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.phase_tick += 1

        # 1. Timer & Bếp chín
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking":
                s["cook_ticks_left"] -= 1
                if s["cook_ticks_left"] <= 0:
                    s["state"] = "ready"
                    s["cook_ticks_left"] = 0
                    s["ready_ticks"] = 0
                    events.append(
                        (
                            "dish_ready",
                            {
                                "stove_id": s["id"],
                                "order_id": s["dish"]["order_id"],
                                "dish_id": s["dish"]["dish_id"],
                            },
                        )
                    )
            elif s["state"] == "ready":
                s["ready_ticks"] += 1

        for c in self.customers:
            if c["state"] == "waiting":
                c["patience_ticks_left"] -= 1
            elif c["state"] == "eating":
                c["eat_ticks_left"] -= 1

        # 2. Di chuyển & E
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)

        # 3. Thanh toán, khách rời hoặc đóng ca
        # Xét khách ăn xong (finished_eating)
        still_here = []
        for c in sort_by_id(self.customers):
            if c["state"] == "eating" and c["eat_ticks_left"] <= 0:
                base_price = c["base_price"]
                tip = c["tip"]
                amount = base_price + tip
                self.money += amount
                self.earned += amount
                self.shift_earned += amount
                if tip > 0:
                    self.reputation = round(
                        min(float(self.t["reputation_max"]), self.reputation + float(self.t["tip_reputation"])),
                        3,
                    )
                events.append(
                    (
                        "paid",
                        {
                            "order_id": c["id"],
                            "table_id": c["table_id"],
                            "base_price": base_price,
                            "tip": tip,
                            "amount": amount,
                            "reason": "finished_eating",
                        },
                    )
                )
            else:
                still_here.append(c)
        self.customers = still_here

        # Xét khách chờ hết kiên nhẫn (patience)
        still_here = []
        for c in sort_by_id(self.customers):
            if c["state"] == "waiting" and c["patience_ticks_left"] <= 0:
                self.reputation = round(
                    max(float(self.t["reputation_min"]), self.reputation + float(self.t["left_reputation_delta"])),
                    3,
                )
                c["reserved"] = {}
                events.append(
                    (
                        "customer_left",
                        {
                            "order_id": c["id"],
                            "table_id": c["table_id"],
                            "reason": "patience",
                            "reputation": self.reputation,
                        },
                    )
                )
            else:
                still_here.append(c)
        self.customers = still_here

        # Nếu hết giờ: đóng ca
        if self.time_left_ticks <= 0:
            for c in sort_by_id(self.customers):
                if c["state"] == "eating":
                    base_price = c["base_price"]
                    tip = c["tip"]
                    amount = base_price + tip
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    if tip > 0:
                        self.reputation = round(
                            min(float(self.t["reputation_max"]), self.reputation + float(self.t["tip_reputation"])),
                            3,
                        )
                    events.append(
                        (
                            "paid",
                            {
                                "order_id": c["id"],
                                "table_id": c["table_id"],
                                "base_price": base_price,
                                "tip": tip,
                                "amount": amount,
                                "reason": "closing",
                            },
                        )
                    )
                elif c["state"] == "waiting":
                    c["reserved"] = {}
                    events.append(
                        (
                            "customer_left",
                            {
                                "order_id": c["id"],
                                "table_id": c["table_id"],
                                "reason": "closing",
                                "reputation": self.reputation,
                            },
                        )
                    )
            self.customers = []
            self.done = True
            self.reason = "time"
            events.append(
                (
                    "quan_end",
                    {
                        "reason": "time",
                        "money": self.money,
                        "earned": self.earned,
                        "shift_earned": self.shift_earned,
                        "reputation": self.reputation,
                    },
                )
            )
            return events

        # 4. Khách mới theo lịch nếu còn giờ
        if self.random_customers:
            self._check_new_customer(events)

        return events

    def _interact(self, events):
        radius = self.t["interact_radius"]
        candidates = []

        # Xét bếp
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= radius:
                has_reserved = any(c["order_status"] == "reserved" for c in self.customers)
                if s["state"] == "idle" and has_reserved:
                    candidates.append((d, 0, id_key(s["id"]), "stove", s))
                elif s["state"] == "ready" and self.hand is None:
                    candidates.append((d, 0, id_key(s["id"]), "stove", s))

        # Xét bàn
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= radius and self.hand is not None:
                cust = next(
                    (c for c in self.customers if c["table_id"] == tb["id"] and c["state"] == "waiting"),
                    None,
                )
                if cust and cust["id"] == self.hand["order_id"]:
                    candidates.append((d, 1, id_key(tb["id"]), "table", tb, cust))

        if not candidates:
            return

        candidates.sort(key=lambda x: (x[0], x[1], x[2]))
        chosen = candidates[0]

        if chosen[3] == "stove":
            s = chosen[4]
            if s["state"] == "idle":
                # Nhận đơn reserved cũ nhất
                res_custs = [c for c in self.customers if c["order_status"] == "reserved"]
                res_custs.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["id"])))
                target_cust = res_custs[0]

                d_id = target_cust["dish_id"]
                base_price = self.menu[d_id]["price"]
                s["state"] = "cooking"
                s["dish"] = {
                    "order_id": target_cust["id"],
                    "dish_id": d_id,
                    "base_price": base_price,
                }
                s["cook_ticks_left"] = int(round(self.menu[d_id]["cook_s"] * TICK))
                s["ready_ticks"] = 0

                # Trừ tồn vật lý và nhả reserved của khách
                for k, amt in target_cust["reserved"].items():
                    self.stock[k] = self.stock.get(k, 0) - amt

                items = []
                for k, count in target_cust["reserved"].items():
                    items.extend([k] * count)
                items.sort()

                target_cust["reserved"] = {}
                target_cust["order_status"] = "assigned"

                events.append(
                    (
                        "cook_started",
                        {
                            "stove_id": s["id"],
                            "order_id": target_cust["id"],
                            "dish_id": d_id,
                            "items": items,
                            "base_price": base_price,
                        },
                    )
                )
            elif s["state"] == "ready":
                # Bưng món khi tay trống
                self.hand = dict(s["dish"])
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0
                events.append(
                    (
                        "dish_picked",
                        {
                            "stove_id": s["id"],
                            "order_id": self.hand["order_id"],
                            "dish_id": self.hand["dish_id"],
                        },
                    )
                )

        elif chosen[3] == "table":
            tb, cust = chosen[4], chosen[5]
            patience_left = cust["patience_ticks_left"]
            max_pat = int(round(self.t["patience_s"] * TICK))
            ratio = patience_left / max_pat
            base_price = self.hand["base_price"]
            if ratio >= self.t["tip_min_patience_ratio"]:
                tip = int(round(base_price * self.t["tip_rate"]))
            else:
                tip = 0
            cust["tip"] = tip
            cust["base_price"] = base_price
            cust["state"] = "eating"
            cust["order_status"] = "served"
            cust["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))

            events.append(
                (
                    "served",
                    {
                        "order_id": cust["id"],
                        "table_id": tb["id"],
                        "dish_id": cust["dish_id"],
                        "patience_ticks_left": patience_left,
                        "base_price": base_price,
                        "tip": tip,
                    },
                )
            )
            self.hand = None

    def _check_new_customer(self, events):
        first_tick = self.t["first_customer_tick"]
        interval = int(round(self.t["customer_interval_s"] * TICK))

        if self.phase_tick >= first_tick and (self.phase_tick - first_tick) % interval == 0:
            occupied = {c["table_id"] for c in self.customers}
            empty_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
            if not empty_tables:
                # Bàn bận bỏ lượt
                return

            # Tính kho khả dụng
            avail = dict(self.stock)
            for c in self.customers:
                for k, amt in c.get("reserved", {}).items():
                    avail[k] = avail.get(k, 0) - amt

            eligible = []
            for d_id in sorted(self.menu):
                recipe = self.menu[d_id]["recipe"]
                if all(avail.get(k, 0) >= req for k, req in recipe.items()):
                    eligible.append(d_id)

            if not eligible:
                events.append(("no_dish", {}))
                return

            chosen_dish = self.rng.get("customer").choice(sorted(eligible))
            cid = self.ids.new("C")
            empty_table = empty_tables[0]
            recipe = dict(self.menu[chosen_dish]["recipe"])

            new_c = {
                "id": cid,
                "table_id": empty_table["id"],
                "dish_id": chosen_dish,
                "order_tick": self.phase_tick,
                "state": "waiting",
                "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
                "eat_ticks_left": int(round(self.t["eat_s"] * TICK)),
                "order_status": "reserved",
                "reserved": recipe,
                "base_price": self.menu[chosen_dish]["price"],
                "tip": 0,
            }
            self.customers.append(new_c)
            events.append(
                (
                    "customer_arrived",
                    {
                        "order_id": cid,
                        "table_id": empty_table["id"],
                        "dish_id": chosen_dish,
                    },
                )
            )

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
