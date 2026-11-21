"""Buổi tối — Mở Quán (`quan`). Góc nhìn từ trên xuống nhà bè, vị trí `[x, z]` (z hướng bắc).

Thứ tự một bước theo Test Contract v1.0 mục F ("Quán"):
  1. tăng đồng hồ (phase_tick), giảm timer ca, nấu, ăn, kiên nhẫn; ready_ticks chỉ tăng cho món ready ở đầu bước
  2. bếp theo id: nấu xong -> ready (dish_ready)
  3. di chuyển rồi tối đa MỘT interact, chọn theo (khoảng cách, bếp trước bàn, id)
  4. khách theo id bàn: ăn xong trả tiền (paid) rồi rời; hết kiên nhẫn rời (customer_left); hết ca thì dọn và quan_end
  5. còn giờ: lượt khách mới theo lịch (customer_arrived / no_dish)

v1.1: 2 bếp / 4 bàn / 6 món đọc từ contract. Quán độc lập dùng cả 6 món; trong `day`, `menu_filter`
(id món của kế hoạch Ngày) lọc thực đơn TRƯỚC khi lọc theo nguyên liệu khả dụng (tồn trừ phần giữ).
Tiền / earned / uy tín được mang sang từ Ngày trước qua tham số của hàm dựng.

v1.2 (TICKET-03 "Độ tươi"): kho quán là mảng cá thể {id,kind,fresh} (giữ cả hàng ươn, không áp sức chứa).
Bên trong lưu độ tươi bằng số nguyên `u` (240 đơn vị / điểm) để ngưỡng 30 và floor chính xác; quán trừ
1 đơn vị/tick (0.25/s), kể cả hàng đang giữ chỗ; món chín không hao. Bước 1b: hao tươi -> phát spoiled theo
id -> nhả + giữ lại MỘT lần các đơn có phần giữ vừa ươn (order_tick rồi id bàn), không đủ -> unfulfillable.
Giữ chỗ theo id: mỗi loại lấy cá thể chưa ươn, chưa giữ, tươi nhất, hòa theo id. Bắt đầu nấu tiêu đúng các
id đang giữ, chốt base_price = floor(giá niêm yết × trung bình fresh / 100).

Lát 3 (khách, giữ chỗ, kiên nhẫn) và lát 4 (bếp, bưng, phục vụ, tiền). Số liệu chỉ đọc từ tuning/menu,
ngẫu nhiên chỉ qua Streams("customers"), duyệt thực thể theo ids.sort_by_id.
"""

import math
from fractions import Fraction

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import (UNITS_PER_FRESH as UNITS, decay, decay_units_per_tick, item_out, parse_items,
                         spoil_threshold_units)
from .ramp import ramp_velocity

TICK = 60.0
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
                 "order_status", "reserved", "base_price", "tip"}
STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
PAYLOAD_KEYS = {"order_id", "dish_id", "base_price"}
ORDER_STATUS = ("reserved", "assigned", "unfulfillable", "served")


def load_items(raw, where="stock"):
    """Mảng cá thể: JSON {id,kind,fresh} hoặc bộ nhớ {id,kind,units} (bàn giao trong day) -> {id,kind,units}."""
    if isinstance(raw, list) and all(isinstance(x, dict) and "units" in x for x in raw):
        return sort_by_id([dict(x) for x in raw])
    return sort_by_id(parse_items(raw, where=where))


item_view = item_out


def _ticks(seconds):
    return int(round(seconds * TICK))


def _nonneg_int(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, menu_filter=None,
                 reputation=None, money=0, earned=0):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        # id món khách được gọi: cả thực đơn (quán độc lập) hoặc chỉ món trong kế hoạch Ngày
        self.dish_ids = sorted(self.menu) if menu_filter is None else sorted(d for d in menu_filter if d in self.menu)
        self.rng = streams
        self.ids = ids
        self.patience_full = _ticks(t["patience_s"])
        self.eat_full = _ticks(t["eat_s"])
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2); thiếu cả hai -> kho rỗng
        self.decay_units = decay_units_per_tick(tuning, "quan")
        self.spoil_units = spoil_threshold_units(tuning)
        self.stock = load_items(inventory if inventory is not None else scenario.get("stock", []))
        self.by_id = {it["id"]: it for it in self.stock}
        for it in self.stock:
            ids.reserve(it["id"])
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", _ticks(t["duration_s"]))
        self.phase_tick = 0
        self.reputation = reputation if reputation is not None else scenario.get("reputation", t["reputation_initial"])
        self.random_customers = scenario.get("random_customers", True)
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = self._load_customers(scenario.get("customers", []))
        for e in self.customers:
            ids.reserve(e["id"])
        self._validate_state()
        self.money = money
        self.earned = earned
        self.shift_earned = 0
        self.done = False
        self.reason = None

    # --- dựng fixture -------------------------------------------------------------
    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _load_customers(self, raw):
        table_ids = {tb["id"] for tb in self.tables}
        out = []
        for c in raw:
            extra = set(c) - CUSTOMER_KEYS
            if extra:
                raise BadInput(f"customers.{c.get('id')}: trường lạ/chưa hỗ trợ {sorted(extra)}")
            if c.get("table_id") not in table_ids:
                raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
            if c.get("dish_id") not in self.dish_ids:
                raise BadInput(f"customers.{c['id']}: dish_id ngoài phạm vi (thực đơn / kế hoạch Ngày)")
            cu = {
                "id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                "order_tick": c.get("order_tick", 0), "state": c.get("state", "waiting"),
                "patience_ticks_left": c.get("patience_ticks_left", self.patience_full),
                "eat_ticks_left": c.get("eat_ticks_left", 0),
                "order_status": c.get("order_status", "reserved"),
                "reserved": c.get("reserved"), "base_price": c.get("base_price"), "tip": c.get("tip"),
            }
            if cu["state"] not in ("waiting", "eating"):
                raise BadInput(f"customers.{c['id']}: state phải là waiting hoặc eating")
            if cu["order_status"] not in ORDER_STATUS:
                raise BadInput(f"customers.{c['id']}: order_status không hợp lệ")
            for k in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
                if not _nonneg_int(cu[k]):
                    raise BadInput(f"customers.{c['id']}.{k} phải là số nguyên không âm")
            if cu["patience_ticks_left"] > self.patience_full:
                raise BadInput(f"customers.{c['id']}: kiên nhẫn vượt tối đa")
            if cu["eat_ticks_left"] > self.eat_full:
                raise BadInput(f"customers.{c['id']}: thời gian ăn vượt tối đa")
            if cu["reserved"] is not None:
                r = cu["reserved"]
                if not isinstance(r, list) or any(not isinstance(x, str) for x in r):
                    raise BadInput(f"customers.{c['id']}.reserved phải là mảng id cá thể (v1.2)")
                cu["reserved"] = list(r)
            out.append(cu)
        if len({c["table_id"] for c in out}) != len(out):
            raise BadInput("hai khách cùng bàn")
        # phần giữ khai sẵn: trỏ tới cá thể chưa ươn trong kho, không dùng chung
        taken = set()
        for c in out:
            for i in c["reserved"] or []:
                it = self.by_id.get(i)
                if it is None:
                    raise BadInput(f"customers.{c['id']}.reserved: id {i} không có trong kho")
                if it["units"] < self.spoil_units:
                    raise BadInput(f"customers.{c['id']}.reserved: {i} đã ươn")
                if i in taken:
                    raise BadInput(f"customers.{c['id']}.reserved: {i} dùng chung với đơn khác")
                taken.add(i)
        # đơn reserved thiếu `reserved` -> cấp theo (order_tick, id bàn), tươi nhất rồi id nhỏ
        need = [c for c in out if c["order_status"] == "reserved" and c["reserved"] is None]
        for c in sorted(need, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            got = self._allocate(self.menu[c["dish_id"]]["recipe"], out)
            if got is not None:
                c["reserved"] = got
            else:
                c["order_status"], c["reserved"] = "unfulfillable", []
        for c in out:
            if c["reserved"] is None:
                c["reserved"] = []
            c["reserved"] = self._sort_ids(c["reserved"])
        return out

    def _validate_state(self):
        """Mâu thuẫn mức luật trong fixture -> mã 2 (Contract D)."""
        orders = {c["id"]: c for c in self.customers}
        holders = {}

        def payload(where, pl):
            if not isinstance(pl, dict) or set(pl) != PAYLOAD_KEYS:
                raise BadInput(f"{where}: payload món phải là {{order_id,dish_id,base_price}}")
            cu = orders.get(pl["order_id"])
            if cu is None or cu["dish_id"] != pl["dish_id"]:
                raise BadInput(f"{where}: món không khớp đơn nào")
            if cu["order_status"] != "assigned":
                raise BadInput(f"{where}: món chỉ thuộc đơn assigned")
            if pl["order_id"] in holders:
                raise BadInput(f"{where}: bếp và tay giữ cùng đơn {pl['order_id']}")
            holders[pl["order_id"]] = where

        for s in self.stoves:
            extra = set(s) - STOVE_KEYS
            if extra:
                raise BadInput(f"stoves.{s['id']}: trường lạ {sorted(extra)}")
            if s["state"] not in ("idle", "cooking", "ready"):
                raise BadInput(f"stoves.{s['id']}: state không hợp lệ")
            if not _nonneg_int(s["cook_ticks_left"]) or not _nonneg_int(s["ready_ticks"]):
                raise BadInput(f"stoves.{s['id']}: bộ đếm phải là số nguyên không âm")
            if s["state"] == "idle":
                if s["dish"] is not None or s["cook_ticks_left"] or s["ready_ticks"]:
                    raise BadInput(f"stoves.{s['id']}: bếp idle không có món/timer")
            else:
                payload(f"stoves.{s['id']}", s["dish"])
                if s["state"] == "cooking" and s["cook_ticks_left"] <= 0:
                    raise BadInput(f"stoves.{s['id']}: bếp cooking cần timer dương")
                if s["state"] == "cooking" and s["ready_ticks"]:
                    raise BadInput(f"stoves.{s['id']}: ready_ticks chỉ có khi ready")
                if s["state"] == "ready" and s["cook_ticks_left"]:
                    raise BadInput(f"stoves.{s['id']}: bếp ready không còn timer nấu")
        if self.hand is not None:
            payload("hand", self.hand)
        for c in self.customers:
            where = f"customers.{c['id']}"
            st = c["order_status"]
            if st == "reserved" and self._kinds(c["reserved"]) != dict(self.menu[c["dish_id"]]["recipe"]):
                raise BadInput(f"{where}: giữ khác công thức")
            if st != "reserved" and c["reserved"]:
                raise BadInput(f"{where}: chỉ đơn reserved mới giữ nguyên liệu")
            if st == "assigned" and c["id"] not in holders:
                raise BadInput(f"{where}: đơn assigned phải có đúng một món ở bếp hoặc tay")
            if (c["state"] == "eating") != (st == "served"):
                raise BadInput(f"{where}: khách eating phải là served và ngược lại")
            if c["state"] == "eating":
                if c["eat_ticks_left"] <= 0 or not _nonneg_int(c["base_price"]) or not _nonneg_int(c["tip"]):
                    raise BadInput(f"{where}: khách eating cần timer ăn dương và base_price, tip đã chốt")
            elif c["eat_ticks_left"]:
                raise BadInput(f"{where}: khách chờ không có timer ăn")

    # --- giao diện cho runner -----------------------------------------------------
    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": [item_view(it) for it in self.stock],
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": [dict(c, reserved=list(c["reserved"])) for c in sort_by_id(self.customers)],
        }

    # --- một bước -------------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ, timer ca, nấu, ăn, kiên nhẫn
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            else:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
        # 1b. hao tươi kho thô (kể cả hàng đang giữ), phát spoiled theo id, rồi xử lý giữ chỗ bị ươn
        self._decay(events)
        # 2. bếp theo id: chín -> ready
        for s in self.stoves:
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"], s["ready_ticks"] = "ready", 0
                events.append(("dish_ready", {"stove_id": s["id"], "order_id": s["dish"]["order_id"],
                                              "dish_id": s["dish"]["dish_id"]}))
        # 3. di chuyển, rồi tối đa một interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        # 4. khách theo id bàn
        closing = self.time_left_ticks <= 0
        for c in sorted(self.customers, key=lambda c: id_key(c["table_id"])):
            if c["state"] == "eating" and c["eat_ticks_left"] == 0:
                self._pay(c, "finished_eating", events)
            elif closing and c["state"] == "eating":
                self._pay(c, "closing", events)
            elif closing:
                self._leave(c, "closing", events)
            elif c["patience_ticks_left"] == 0:
                self._leave(c, "patience", events)
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        # 5. lượt khách mới
        self._maybe_arrive(events)
        return events

    # --- lát 4: bếp, bưng, phục vụ --------------------------------------------------
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
        _, _, _, kind, obj = min(cands, key=lambda c: c[:3])
        if kind == "stove":
            if obj["state"] == "idle":
                self._start_cooking(obj, events)
            elif obj["state"] == "ready" and self.hand is None:
                self.hand = obj["dish"]
                events.append(("dish_picked", {"stove_id": obj["id"], "order_id": obj["dish"]["order_id"],
                                               "dish_id": obj["dish"]["dish_id"]}))
                obj.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        else:
            cu = next((c for c in self.customers if c["table_id"] == obj["id"]), None)
            if (cu is not None and cu["state"] == "waiting" and self.hand is not None
                    and self.hand["order_id"] == cu["id"]):
                self._serve(cu, events)

    def _start_cooking(self, stove, events):
        orders = [c for c in self.customers if c["order_status"] == "reserved"]
        if not orders:
            return
        cu = min(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        dish = self.menu[cu["dish_id"]]
        used = [self.by_id[i] for i in cu["reserved"]]
        items = [item_view(it) for it in sorted(used, key=lambda it: (it["kind"], id_key(it["id"])))]
        gone = set(cu["reserved"])
        self.stock = [it for it in self.stock if it["id"] not in gone]
        for i in gone:
            del self.by_id[i]
        cu["reserved"] = []
        cu["order_status"] = "assigned"
        # giá chốt theo tươi: floor(giá × tổng u / (n × 240 × 100)), số nguyên/phân số chính xác
        total_u = sum(it["units"] for it in used)
        cu["base_price"] = math.floor(Fraction(str(dish["price"])) * total_u / (len(used) * UNITS * 100))
        stove.update(state="cooking", cook_ticks_left=_ticks(dish["cook_s"]), ready_ticks=0,
                     dish={"order_id": cu["id"], "dish_id": cu["dish_id"], "base_price": cu["base_price"]})
        events.append(("cook_started", {"stove_id": stove["id"], "order_id": cu["id"], "dish_id": cu["dish_id"],
                                        "items": items, "base_price": cu["base_price"]}))

    def _serve(self, cu, events):
        base = int(self.hand["base_price"])
        ratio = cu["patience_ticks_left"] / self.patience_full
        tip = math.floor(base * self.t["tip_rate"] + 1e-9) if ratio >= self.t["tip_min_patience_ratio"] else 0
        cu.update(state="eating", order_status="served", eat_ticks_left=self.eat_full, base_price=base, tip=tip)
        self.hand = None
        events.append(("served", {"order_id": cu["id"], "table_id": cu["table_id"], "dish_id": cu["dish_id"],
                                  "patience_ticks_left": cu["patience_ticks_left"], "base_price": base, "tip": tip}))

    def _pay(self, cu, reason, events):
        amount = cu["base_price"] + cu["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if cu["tip"] > 0:
            self._add_reputation(self.t["tip_reputation"])
        events.append(("paid", {"order_id": cu["id"], "table_id": cu["table_id"], "base_price": cu["base_price"],
                                "tip": cu["tip"], "amount": amount, "reason": reason}))
        self.customers.remove(cu)

    # --- lát 3: khách, giữ chỗ, kiên nhẫn -------------------------------------------
    def _leave(self, cu, reason, events):
        if reason == "patience":
            self._add_reputation(self.t["left_reputation_delta"])
        # nhả phần giữ thô (đơn reserved), bỏ món của đơn đang nấu / ready / trên tay
        cu["reserved"] = []
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == cu["id"]:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand is not None and self.hand["order_id"] == cu["id"]:
            self.hand = None
        events.append(("customer_left", {"order_id": cu["id"], "table_id": cu["table_id"], "reason": reason,
                                         "reputation": self.reputation}))
        self.customers.remove(cu)

    def _maybe_arrive(self, events):
        if not self.random_customers:
            return
        first = int(self.t["first_customer_tick"])
        every = _ticks(self.t["customer_interval_s"])
        pt = self.phase_tick
        if pt < first or (pt - first) % every != 0:
            return
        busy = {c["table_id"] for c in self.customers}
        free = [tb for tb in self.tables if tb["id"] not in busy]  # đã sắp theo id
        if not free:
            return
        dishes = [d for d in self.dish_ids if self._allocate(self.menu[d]["recipe"], self.customers) is not None]
        if not dishes:
            events.append(("no_dish", {}))
            return
        dish_id = dishes[self.rng.get("customers").randrange(len(dishes))]
        table = free[0]
        cid = self.ids.new("C")
        self.customers.append({
            "id": cid, "table_id": table["id"], "dish_id": dish_id, "order_tick": pt, "state": "waiting",
            "patience_ticks_left": self.patience_full, "eat_ticks_left": 0, "order_status": "reserved",
            "reserved": self._allocate(self.menu[dish_id]["recipe"], self.customers), "base_price": None, "tip": None,
        })
        events.append(("customer_arrived", {"order_id": cid, "table_id": table["id"], "dish_id": dish_id}))

    # --- tiện ích -------------------------------------------------------------------
    def _sort_ids(self, ids_):
        return sorted(ids_, key=lambda i: (self.by_id[i]["kind"], id_key(i)) if i in self.by_id else ("", id_key(i)))

    def _kinds(self, ids_):
        out = {}
        for i in ids_:
            k = self.by_id[i]["kind"]
            out[k] = out.get(k, 0) + 1
        return out

    def _allocate(self, recipe, customers):
        """Giữ theo id: mỗi loại lấy cá thể chưa ươn, chưa giữ, tươi nhất, hòa theo id. Không đủ -> None."""
        taken = {i for c in customers for i in (c.get("reserved") or [])}
        got = []
        for kind in sorted(recipe):
            cands = sorted((it for it in self.stock
                            if it["kind"] == kind and it["id"] not in taken and it["units"] >= self.spoil_units),
                           key=lambda it: (-it["units"], id_key(it["id"])))
            n = recipe[kind]
            if len(cands) < n:
                return None
            got.extend(it["id"] for it in cands[:n])
        return self._sort_ids(got)

    def _decay(self, events):
        spoiled = decay(self.stock, self.decay_units, self.spoil_units)  # đã sắp theo id
        if not spoiled:
            return
        for it in spoiled:
            events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "stock"}))
        bad = {it["id"] for it in spoiled}
        hit = [c for c in self.customers if c["order_status"] == "reserved" and bad & set(c["reserved"])]
        hit.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        for c in hit:  # nhả toàn bộ phần giữ của mọi đơn bị ảnh hưởng trước
            c["reserved"] = []
        for c in hit:  # rồi thử giữ lại đúng một lần theo order_tick, id bàn
            got = self._allocate(self.menu[c["dish_id"]]["recipe"], self.customers)
            if got is None:
                c["order_status"] = "unfulfillable"
            else:
                c["reserved"] = got

    def _add_reputation(self, delta):
        # làm tròn 9 chữ số để cộng dồn 0.2 không làm floor(uy tín) trong điểm lệch 1 bậc
        r = round(self.reputation + delta, 9)
        self.reputation = min(self.t["reputation_max"], max(self.t["reputation_min"], r))

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
