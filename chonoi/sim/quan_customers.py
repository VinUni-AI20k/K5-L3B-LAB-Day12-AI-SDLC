"""Quán, lát 3 — khách: đến theo lịch, chọn món, giữ chỗ, kiên nhẫn, bỏ đi, no_dish.

Schema khách và thứ tự bước: docs/contracts/customer.md (PRD-0 mục D/E/F).
File này KHÔNG sửa quan.py; QuanSim chỉ cần gọi các hàm công khai dưới đây:

  build_fixture_customers(raw, tuning, stock, stoves, hand)  # __init__: khách dựng sẵn từ scenario
  tick_customers_timers(sim, events)    # đầu bước: giảm kiên nhẫn khách waiting (không giảm timer ăn)
  customers_leave(sim, events)          # sau khi trả tiền, trước quan_end: patience / closing + uy tín
  spawn_customers(sim, events)          # cuối bước, chỉ khi ca còn giờ
  tick_customers(sim, events, phase)    # tên cũ của khung, gọi hai hàm trên theo phase
  remove_customer(sim, customer)        # dùng khi khách rời bàn vì lý do khác (vd. ăn xong, trả tiền)

Quy ước sim (QuanSim) mà file này đọc/ghi:
  sim.customers, sim.tables, sim.stoves, sim.stock, sim.hand, sim.reputation, sim.time_left_ticks,
  sim.t (tuning["quan"]), sim.menu, sim.rng (Streams), sim.ids (IdAllocator),
  sim.phase_tick (nếu có), sim.random_customers (nếu có, mặc định True).
"""

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import validate_items

HZ = 60
CUSTOMER_PREFIX = "C"
RNG_STREAM = "customer_dish"

STATES = ("waiting", "eating")
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                 "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}


# --------------------------------------------------------------------------- tiện ích

def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if not _is_int(v) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")
    return v


def _order_id(payload):
    """order_id của món trên bếp/tay (payload {order_id, dish_id, base_price}); None nếu không có."""
    return payload.get("order_id") if isinstance(payload, dict) else None


def _recipe(menu, dish_id):
    return {k: n for k, n in menu[dish_id]["recipe"].items() if n > 0}


def _patience_full(t):
    return int(round(t["patience_s"] * HZ))


def _eat_full(t):
    return int(round(t["eat_s"] * HZ))


def _by_table(customers):
    return sorted(customers, key=lambda c: id_key(c["table_id"]))


def _phase_tick(sim):
    """phase_tick sau khi tăng. Ưu tiên sim.phase_tick; nếu thiếu thì suy từ thời lượng ca đầy.

    Cách suy chỉ đúng khi ca không bị rút ngắn bằng time_left_ticks (khi đó cần sim.phase_tick)."""
    pt = getattr(sim, "phase_tick", None)
    if pt is not None:
        return pt
    return int(round(sim.t["duration_s"] * HZ)) - sim.time_left_ticks


# --------------------------------------------------------------------------- khách dựng sẵn (scenario)

def build_fixture_customers(raw, tuning, stock=None, stoves=(), hand=None):
    """Chuẩn hóa `quan.customers[]` của scenario (PRD-0 mục D) và kiểm mâu thuẫn -> BadInput (mã 2).

    stock: tồn vật lý (gồm cả phần giữ chỗ) hoặc None nếu chưa biết (chưa kiểm vượt tồn).
    stoves: danh sách bếp đã gộp (dict có state/dish/cook_ticks_left); hand: payload món hoặc None.
    Trả danh sách khách đã đủ trường, sắp theo id.
    """
    t, menu = tuning["quan"], tuning["menu"]
    if not isinstance(raw, list):
        raise BadInput("customers phải là mảng")
    out = []
    for c in raw:
        if not isinstance(c, dict):
            raise BadInput("customers: mỗi phần tử phải là object")
        extra = set(c) - CUSTOMER_KEYS
        if extra:
            raise BadInput(f"trường lạ/chưa hỗ trợ trong customers.{c.get('id')}: {sorted(extra)}")
        cid = c.get("id")
        if not isinstance(cid, str) or not cid:
            raise BadInput("customers: mỗi phần tử cần id (chuỗi khác rỗng)")
        if not isinstance(c.get("table_id"), str):
            raise BadInput(f"customers.{cid}: table_id phải là chuỗi")
        dish_id = c.get("dish_id")
        if not isinstance(dish_id, str) or dish_id not in menu:
            raise BadInput(f"customers.{cid}: dish_id phải là món có trong menu")

        state = c.get("state", "waiting")
        status = c.get("order_status", "reserved")
        if state not in STATES:
            raise BadInput(f"customers.{cid}: state phải thuộc {STATES}")
        if status not in ORDER_STATUSES:
            raise BadInput(f"customers.{cid}: order_status phải thuộc {ORDER_STATUSES}")

        patience = _nonneg_int(f"customers.{cid}.patience_ticks_left",
                               c.get("patience_ticks_left", _patience_full(t)))
        if patience > _patience_full(t):
            raise BadInput(f"customers.{cid}.patience_ticks_left vượt kiên nhẫn đầy")
        eat = _nonneg_int(f"customers.{cid}.eat_ticks_left", c.get("eat_ticks_left", 0))
        if eat > _eat_full(t):
            raise BadInput(f"customers.{cid}.eat_ticks_left vượt thời gian ăn đầy")
        order_tick = _nonneg_int(f"customers.{cid}.order_tick", c.get("order_tick", 0))

        # eating <-> served; timer ăn dương và giá/boa đã chốt
        if (state == "eating") != (status == "served"):
            raise BadInput(f"customers.{cid}: khách eating phải là served và ngược lại")
        if state == "eating":
            if eat <= 0:
                raise BadInput(f"customers.{cid}: khách eating cần eat_ticks_left > 0")
            if "base_price" not in c or "tip" not in c:
                raise BadInput(f"customers.{cid}: khách eating phải khai base_price và tip")
        elif eat > 0:
            raise BadInput(f"customers.{cid}: eat_ticks_left > 0 chỉ khi eating")
        cust = {"id": cid, "table_id": c["table_id"], "dish_id": dish_id, "order_tick": order_tick,
                "state": state, "patience_ticks_left": patience, "eat_ticks_left": eat,
                "order_status": status}
        for key in ("base_price", "tip"):
            if key in c:
                cust[key] = _nonneg_int(f"customers.{cid}.{key}", c[key])

        # giữ chỗ: đơn reserved giữ đúng công thức (thiếu thì cấp); các đơn khác giữ rỗng
        recipe = _recipe(menu, dish_id)
        if "reserved" in c:
            reserved = validate_items(c["reserved"])
        else:
            reserved = dict(recipe) if status == "reserved" else {}
        if status == "reserved":
            if reserved != recipe:
                raise BadInput(f"customers.{cid}: reserved phải đúng công thức của {dish_id}")
        elif reserved:
            raise BadInput(f"customers.{cid}: đơn {status} phải có giữ chỗ rỗng")
        cust["reserved"] = reserved
        out.append(cust)

    out = sort_by_id(out)
    _check_stock(out, stock)
    _check_food_links(out, stoves, hand)
    return out


def _check_stock(customers, stock):
    if stock is None:
        return
    total = {}
    for c in customers:
        for k, n in c["reserved"].items():
            total[k] = total.get(k, 0) + n
    for k, n in total.items():
        if n > stock.get(k, 0):
            raise BadInput(f"giữ chỗ {k} ({n}) vượt tồn kho ({stock.get(k, 0)})")


def _check_food_links(customers, stoves, hand):
    """Đơn assigned có đúng một món ở bếp hoặc tay; đơn khác không có món; món phải khớp đơn."""
    by_id = {c["id"]: c for c in customers}
    found = {c["id"]: 0 for c in customers}

    def link(payload, where):
        oid = _order_id(payload)
        if oid is None:
            return
        c = by_id.get(oid)
        if c is None or c["order_status"] != "assigned":
            raise BadInput(f"{where}: món không khớp đơn nào đang assigned ({oid})")
        if payload.get("dish_id") not in (None, c["dish_id"]):
            raise BadInput(f"{where}: món không khớp dish_id của đơn {oid}")
        found[oid] += 1

    for s in stoves:
        if s.get("state", "idle") == "cooking" and not (_is_int(s.get("cook_ticks_left")) and s["cook_ticks_left"] > 0):
            raise BadInput(f"bếp {s.get('id')} cooking cần cook_ticks_left > 0")
        if s.get("state", "idle") != "idle":
            link(s.get("dish"), f"bếp {s.get('id')}")
    link(hand, "hand")
    for cid, n in found.items():
        want = 1 if by_id[cid]["order_status"] == "assigned" else 0
        if n != want:
            raise BadInput(f"customers.{cid}: đơn {by_id[cid]['order_status']} cần {want} món ở bếp/tay, có {n}")


# --------------------------------------------------------------------------- rời bàn

def remove_customer(sim, customer):
    """Khách rời bàn: bỏ khách (nhả phần giữ thô) và bỏ món của đơn đang nấu / ready / trên tay.

    Nguyên liệu đã dùng khi nấu không hoàn lại (kho do quan_service quản)."""
    sim.customers.remove(customer)
    oid = customer["id"]
    for s in sim.stoves:
        if _order_id(s.get("dish")) == oid:
            s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
    if _order_id(sim.hand) == oid:
        sim.hand = None


def _clamp_reputation(sim, value):
    return max(sim.t["reputation_min"], min(sim.t["reputation_max"], value))


# --------------------------------------------------------------------------- mỗi bước

def tick_customers_timers(sim, events=None):
    """Đầu bước: giảm kiên nhẫn của khách waiting. KHÔNG giảm eat_ticks_left (lát 4 tự giảm,
    giảm ở đây nữa thì khách ăn nhanh gấp đôi). Khách eating giữ nguyên kiên nhẫn."""
    for c in sim.customers:
        if c["state"] == "waiting" and c["patience_ticks_left"] > 0:
            c["patience_ticks_left"] -= 1


def customers_leave(sim, events):
    """Sau khi khách đang ăn đã trả tiền (lát 4), trước quan_end.

    Ca còn giờ: khách waiting có kiên nhẫn 0 rời (reason patience, trừ uy tín left_reputation_delta).
    Hết ca (time_left_ticks == 0): khách waiting rời với reason closing, không đổi uy tín.
    Khách eating KHÔNG xử lý ở đây. Phát customer_left theo thứ tự id bàn."""
    closing = sim.time_left_ticks <= 0
    for c in _by_table([c for c in sim.customers if c["state"] == "waiting"]):
        if closing:
            reason = "closing"
        elif c["patience_ticks_left"] == 0:
            reason = "patience"
        else:
            continue
        remove_customer(sim, c)
        if reason == "patience":
            sim.reputation = _clamp_reputation(sim, sim.reputation + sim.t["left_reputation_delta"])
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"],
                                         "reason": reason, "reputation": sim.reputation}))


def tick_customers(sim, events, phase="all"):
    """Tên cũ của khung (giữ để tương thích): phase "timers" / "leave" / "all" (timers rồi leave)."""
    if phase not in ("timers", "leave", "all"):
        raise ValueError(f"phase không hợp lệ: {phase!r}")
    if phase in ("timers", "all"):
        tick_customers_timers(sim, events)
    if phase in ("leave", "all"):
        customers_leave(sim, events)


def _available_stock(sim):
    avail = {k: n for k, n in sim.stock.items()}
    for c in sim.customers:
        for k, n in c["reserved"].items():
            avail[k] = avail.get(k, 0) - n
    return avail


def spawn_customers(sim, events):
    """Khách mới theo lịch (first_customer_tick, rồi mỗi customer_interval_s). Gọi CUỐI bước.

    Không còn giờ / random_customers=false / chưa tới lịch -> không làm gì. Không còn bàn trống -> bỏ lượt.
    Có bàn mà không món nào đủ nguyên liệu khả dụng -> no_dish. Ngược lại lấy bàn trống id nhỏ nhất,
    chọn đều theo seed trong các món đủ nguyên liệu, giữ đúng công thức."""
    if sim.time_left_ticks <= 0 or not getattr(sim, "random_customers", True):
        return
    t = sim.t
    pt = _phase_tick(sim)
    first = t["first_customer_tick"]
    interval = int(round(t["customer_interval_s"] * HZ))
    if pt < first or (pt - first) % interval != 0:
        return
    occupied = {c["table_id"] for c in sim.customers}
    free = [tb for tb in sim.tables if tb["id"] not in occupied]
    if not free:
        return
    table = min(free, key=lambda tb: id_key(tb["id"]))
    avail = _available_stock(sim)
    feasible = [d for d in sorted(sim.menu)
                if all(avail.get(k, 0) >= n for k, n in _recipe(sim.menu, d).items())]
    if not feasible:
        events.append(("no_dish", {}))
        return
    dish_id = sim.rng.get(RNG_STREAM).choice(feasible)
    cust = {"id": sim.ids.new(CUSTOMER_PREFIX), "table_id": table["id"], "dish_id": dish_id,
            "order_tick": pt, "state": "waiting", "patience_ticks_left": _patience_full(t),
            "eat_ticks_left": 0, "order_status": "reserved", "reserved": _recipe(sim.menu, dish_id)}
    sim.customers.append(cust)
    events.append(("customer_arrived", {"order_id": cust["id"], "table_id": table["id"], "dish_id": dish_id}))
