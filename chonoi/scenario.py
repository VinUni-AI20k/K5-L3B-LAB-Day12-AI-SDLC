"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

Kiểm cú pháp, id, bộ đếm, sức chứa và tính nhất quán giữa kho, đơn và món.
"""

import json

from .errors import BadInput
from .ids import id_key
from .inventory import KINDS_P1, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung")
FISH_KINDS = ("ca_linh", "ca_loc")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    if mode == "gather":
        dur = int(round(tuning[mode]["duration_s"] * 60))
        if "time_left_ticks" in block:
            t = block["time_left_ticks"]
            if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
                raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
        _validate_gather(block, tuning)
    else:
        validate_quan_state(block, tuning)
    return block


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(k not in KINDS_P1 for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")


def _pos_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
        raise BadInput(f"{name} phải là số nguyên dương")


def _validate_dish_payload(name, dish, menu):
    if not isinstance(dish, dict):
        raise BadInput(f"{name}: payload món phải là object")
    req = {"order_id", "dish_id", "base_price"}
    if set(dish) != req:
        raise BadInput(f"{name}: payload món phải có đúng {sorted(req)}")
    if not isinstance(dish["order_id"], str) or not dish["order_id"]:
        raise BadInput(f"{name}.order_id phải là chuỗi không rỗng")
    if not isinstance(dish["dish_id"], str) or dish["dish_id"] not in menu:
        raise BadInput(f"{name}.dish_id ngoài menu: {dish['dish_id']!r}")
    _pos_int(f"{name}.base_price", dish["base_price"])


def _register_dish(name, dish, menu, slots):
    _validate_dish_payload(name, dish, menu)
    order_id = dish["order_id"]
    if order_id in slots:
        raise BadInput(f"trùng order_id {order_id!r} trên nhiều bếp/tay")
    slots[order_id] = dish


def _validate_reserved_map(name, r, kinds):
    if not isinstance(r, dict):
        raise BadInput(f"{name}.reserved phải là object")
    out = {}
    for k, v in r.items():
        if not isinstance(k, str) or k not in kinds:
            raise BadInput(f"{name}.reserved: nguyên liệu ngoài phạm vi {k!r}")
        _pos_int(f"{name}.reserved[{k}]", v)
        out[k] = v
    return out


def validate_quan_state(b, tuning, stock_map=None):
    """Trả danh sách khách đã chuẩn hóa và phần giữ chỗ suy ra từ công thức."""
    qt = tuning["quan"]
    menu = tuning["menu"]
    kinds = set(KINDS_P1)
    tick_hz = tuning["tick_hz"]
    dur_ticks = round(qt["duration_s"] * tick_hz)
    qb = qt["bounds"]

    if not isinstance(b, dict):
        raise BadInput("quan phải là object")
    extra = set(b) - QUAN_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong quan: {sorted(extra)}")
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("quan.random_customers phải là bool")
    if "time_left_ticks" in b:
        _pos_int("quan.time_left_ticks", b["time_left_ticks"])
        if b["time_left_ticks"] > dur_ticks:
            raise BadInput("quan.time_left_ticks vượt thời lượng pha")
    if "reputation" in b:
        rep = b["reputation"]
        if not _num(rep) or not (qt["reputation_min"] <= rep <= qt["reputation_max"]):
            raise BadInput("quan.reputation ngoài miền tuning")

    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])

    if stock_map is None and "stock" in b:
        stock_map = validate_items(b["stock"])

    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")

    known_stoves = {s["id"] for s in qt["stoves"]}
    slot_orders = {}
    for st in b.get("stoves", []):
        sid = st["id"]
        if sid not in known_stoves:
            raise BadInput(f"stoves.{sid}: id bếp không tồn tại trong tuning")
        allowed_st = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
        if set(st) - allowed_st:
            raise BadInput(f"stoves.{sid}: trường lạ {sorted(set(st) - allowed_st)}")
        if "pos" in st:
            _pos(f"stoves.{sid}.pos", st["pos"], qb, axes=("x", "z"))
        state = st.get("state", "idle")
        if state not in ("idle", "cooking", "ready"):
            raise BadInput(f"stoves.{sid}.state không hợp lệ: {state!r}")
        dish = st.get("dish")
        cook_left = st.get("cook_ticks_left", 0)
        ready_t = st.get("ready_ticks", 0)
        _nonneg_int(f"stoves.{sid}.cook_ticks_left", cook_left)
        _nonneg_int(f"stoves.{sid}.ready_ticks", ready_t)
        if state == "idle":
            if dish is not None or cook_left != 0 or ready_t != 0:
                raise BadInput(f"stoves.{sid}: bếp idle không được giữ món hoặc timer dương")
        else:
            if state == "cooking" and (cook_left == 0 or ready_t != 0):
                raise BadInput(f"stoves.{sid}: bếp cooking phải có cook_ticks_left > 0 và ready_ticks == 0")
            if state == "ready" and cook_left != 0:
                raise BadInput(f"stoves.{sid}: bếp ready phải có cook_ticks_left == 0")
            _register_dish(f"stoves.{sid}.dish", dish, menu, slot_orders)

    if b.get("hand") is not None:
        _register_dish("quan.hand", b["hand"], menu, slot_orders)

    known_tables = {t["id"] for t in qt["tables"]}
    for tb in b.get("tables", []):
        tid = tb["id"]
        if tid not in known_tables:
            raise BadInput(f"tables.{tid}: id bàn không tồn tại trong tuning")
        if set(tb) - {"id", "pos"}:
            raise BadInput(f"tables.{tid}: trường lạ {sorted(set(tb) - {'id', 'pos'})}")
        if "pos" in tb:
            _pos(f"tables.{tid}.pos", tb["pos"], qb, axes=("x", "z"))

    allowed_c = {
        "id", "table_id", "dish_id", "order_tick", "state",
        "patience_ticks_left", "eat_ticks_left", "order_status",
        "reserved", "base_price", "tip",
    }
    seen_tables = set()
    assigned_seen = set()
    used_reserved = {}
    need_auto_reserve = []
    customers = []
    for raw_customer in b.get("customers", []):
        c = dict(raw_customer)
        cid = c["id"]
        for old, current in (("dish", "dish_id"), ("patience_ticks", "patience_ticks_left")):
            if old in c:
                value = c.pop(old)
                if current in c and (type(value) is not type(c[current]) or value != c[current]):
                    raise BadInput(f"customers.{cid}: {old} mâu thuẫn với {current}")
                c.setdefault(current, value)
        if set(c) - allowed_c:
            raise BadInput(f"customers.{cid}: trường lạ {sorted(set(c) - allowed_c)}")
        customers.append(c)
        tid = c.get("table_id")
        if not isinstance(tid, str) or tid not in known_tables:
            raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
        if tid in seen_tables:
            raise BadInput("hai khách cùng bàn")
        seen_tables.add(tid)

        did = c.get("dish_id")
        if not isinstance(did, str) or did not in menu:
            raise BadInput(f"customers.{cid}: dish_id không hợp lệ: {did!r}")
        otick = c.get("order_tick", 0)
        _nonneg_int(f"customers.{cid}.order_tick", otick)
        cstate = c.get("state", "waiting")
        if cstate not in ("waiting", "eating"):
            raise BadInput(f"customers.{cid}.state không hợp lệ: {cstate!r}")
        pat = c.get("patience_ticks_left", round(qt["patience_s"] * tick_hz))
        eat = c.get("eat_ticks_left", 0)
        _nonneg_int(f"customers.{cid}.patience_ticks_left", pat)
        _nonneg_int(f"customers.{cid}.eat_ticks_left", eat)
        ostatus = c.get("order_status", "reserved")
        if ostatus not in ("reserved", "assigned", "unfulfillable", "served"):
            raise BadInput(f"customers.{cid}.order_status không hợp lệ: {ostatus!r}")

        if cstate == "eating":
            if ostatus != "served" or eat <= 0:
                raise BadInput(f"customers.{cid}: khách eating phải served và có eat_ticks_left > 0")
            if cid in slot_orders:
                raise BadInput(f"customers.{cid}: khách eating không được còn món ở bếp/tay")
            if "reserved" in c and c["reserved"] != {}:
                raise BadInput(f"customers.{cid}: khách eating phải có reserved rỗng")
            if "base_price" not in c or "tip" not in c:
                raise BadInput(f"customers.{cid}: khách eating phải chốt base_price và tip")
            _pos_int(f"customers.{cid}.base_price", c["base_price"])
            _nonneg_int(f"customers.{cid}.tip", c["tip"])
        else:
            if eat != 0:
                raise BadInput(f"customers.{cid}: khách waiting phải có eat_ticks_left == 0")
            if ostatus == "served":
                raise BadInput(f"customers.{cid}: khách waiting không thể served")
            if "base_price" in c:
                _nonneg_int(f"customers.{cid}.base_price", c["base_price"])
            if "tip" in c:
                _nonneg_int(f"customers.{cid}.tip", c["tip"])
            if ostatus == "assigned":
                dish = slot_orders.get(cid)
                if dish is None or dish["dish_id"] != did:
                    raise BadInput(f"customers.{cid}: đơn assigned phải khớp đúng một món ở bếp hoặc tay")
                if c.get("base_price", dish["base_price"]) != dish["base_price"]:
                    raise BadInput(f"customers.{cid}: base_price không khớp món đã nấu")
                c["base_price"] = dish["base_price"]
                if "reserved" in c and c["reserved"] != {}:
                    raise BadInput(f"customers.{cid}: đơn assigned phải có reserved rỗng")
                assigned_seen.add(cid)
            elif ostatus == "unfulfillable":
                if cid in slot_orders:
                    raise BadInput(f"customers.{cid}: đơn unfulfillable không được có món ở bếp/tay")
                if "reserved" in c and c["reserved"] != {}:
                    raise BadInput(f"customers.{cid}: đơn unfulfillable phải có reserved rỗng")
            else:  # reserved
                if cid in slot_orders:
                    raise BadInput(f"customers.{cid}: đơn reserved không được có món ở bếp/tay")
                recipe = menu[did]["recipe"]
                if "reserved" in c:
                    res = _validate_reserved_map(f"customers.{cid}", c["reserved"], kinds)
                    if res != recipe:
                        raise BadInput(f"customers.{cid}: reserved khác công thức món {did}")
                    for k, amt in res.items():
                        used_reserved[k] = used_reserved.get(k, 0) + amt
                else:
                    need_auto_reserve.append((otick, id_key(tid), cid, dict(recipe)))

    orphan = set(slot_orders) - assigned_seen
    if orphan:
        raise BadInput(f"món trên bếp/tay không gắn với khách assigned: {sorted(orphan)}")

    resolved = {}
    if stock_map is not None:
        avail = dict(stock_map)
        for k, amt in used_reserved.items():
            if avail.get(k, 0) < amt:
                raise BadInput(f"tổng giữ chỗ {k} vượt tồn kho")
            avail[k] -= amt
        need_auto_reserve.sort(key=lambda item: (item[0], item[1]))
        for _, _, cid, recipe in need_auto_reserve:
            for k, amt in recipe.items():
                if avail.get(k, 0) < amt:
                    raise BadInput(f"customers.{cid}: thiếu tồn kho {k} để giữ chỗ theo công thức")
                avail[k] = avail.get(k, 0) - amt
            resolved[cid] = recipe
    return customers, resolved
