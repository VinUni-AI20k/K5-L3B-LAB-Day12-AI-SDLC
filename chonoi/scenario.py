"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
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
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
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


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
    # --- phần nhóm thêm (C): kiểm cấu trúc theo PRD-0 mục D ---
    q, menu = tuning["quan"], tuning["menu"]
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput(f"reputation phải là số trong [{q['reputation_min']}, {q['reputation_max']}]")
    for tb in b.get("tables", []):
        if set(tb) - TABLE_KEYS:
            raise BadInput(f"tables.{tb['id']}: trường lạ {sorted(set(tb) - TABLE_KEYS)}")
        if "pos" in tb:
            _pos(f"tables.{tb['id']}.pos", tb["pos"], qb, axes=("x", "z"))
    for st in b.get("stoves", []):
        _validate_stove(st, menu, qb)
    if b.get("hand") is not None:
        _validate_dish("hand", b["hand"], menu)
    patience_full = int(round(q["patience_s"] * 60))
    eat_full = int(round(q["eat_s"] * 60))
    for c in b.get("customers", []):
        _validate_customer(c, menu, patience_full, eat_full)


TABLE_KEYS = {"id", "pos"}
STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
STOVE_STATES = ("idle", "cooking", "ready")
DISH_KEYS = {"order_id", "dish_id", "base_price"}
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
                 "order_status", "reserved", "base_price", "tip"}
CUSTOMER_STATES = ("waiting", "eating")
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")


def _pos_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
        raise BadInput(f"{name} phải là số nguyên dương")


def _validate_dish(name, d, menu):
    """Payload món {order_id, dish_id, base_price} (PRD-0 mục D)."""
    if not isinstance(d, dict) or set(d) != DISH_KEYS:
        raise BadInput(f"{name} phải là payload món {{order_id, dish_id, base_price}}")
    if not isinstance(d["order_id"], str) or not d["order_id"]:
        raise BadInput(f"{name}.order_id phải là id khách")
    if d["dish_id"] not in menu:
        raise BadInput(f"{name}.dish_id ngoài thực đơn: {d['dish_id']!r}")
    _pos_int(f"{name}.base_price", d["base_price"])


def _validate_stove(st, menu, qb):
    sid = st["id"]
    extra = set(st) - STOVE_KEYS
    if extra:
        raise BadInput(f"stoves.{sid}: trường lạ {sorted(extra)}")
    if "pos" in st:
        _pos(f"stoves.{sid}.pos", st["pos"], qb, axes=("x", "z"))
    state = st.get("state", "idle")
    if state not in STOVE_STATES:
        raise BadInput(f"stoves.{sid}.state phải là một trong {STOVE_STATES}")
    for key in ("cook_ticks_left", "ready_ticks"):
        if key in st:
            _nonneg_int(f"stoves.{sid}.{key}", st[key])
    dish = st.get("dish")
    if dish is not None:
        _validate_dish(f"stoves.{sid}.dish", dish, menu)
    if state == "idle" and (dish is not None or st.get("cook_ticks_left", 0) or st.get("ready_ticks", 0)):
        raise BadInput(f"stoves.{sid}: bếp idle không có món và bộ đếm phải bằng 0")
    if state == "cooking" and (dish is None or st.get("cook_ticks_left", 0) <= 0 or st.get("ready_ticks", 0)):
        raise BadInput(f"stoves.{sid}: bếp cooking cần món và cook_ticks_left > 0")
    if state == "ready" and (dish is None or st.get("cook_ticks_left", 0)):
        raise BadInput(f"stoves.{sid}: bếp ready cần món và cook_ticks_left = 0")


def _validate_customer(c, menu, patience_full, eat_full):
    cid = c["id"]
    extra = set(c) - CUSTOMER_KEYS
    if extra:
        raise BadInput(f"customers.{cid}: trường lạ {sorted(extra)}")
    if c.get("dish_id") not in menu:
        raise BadInput(f"customers.{cid}.dish_id phải là món trong thực đơn")
    state = c.get("state", "waiting")
    status = c.get("order_status", "reserved")
    if state not in CUSTOMER_STATES:
        raise BadInput(f"customers.{cid}.state phải là một trong {CUSTOMER_STATES}")
    if status not in ORDER_STATUSES:
        raise BadInput(f"customers.{cid}.order_status phải là một trong {ORDER_STATUSES}")
    for key in ("order_tick", "patience_ticks_left", "eat_ticks_left", "tip"):
        if key in c:
            _nonneg_int(f"customers.{cid}.{key}", c[key])
    if "base_price" in c:
        _pos_int(f"customers.{cid}.base_price", c["base_price"])
    if c.get("patience_ticks_left", 0) > patience_full:
        raise BadInput(f"customers.{cid}.patience_ticks_left vượt kiên nhẫn tối đa ({patience_full})")
    if c.get("eat_ticks_left", 0) > eat_full:
        raise BadInput(f"customers.{cid}.eat_ticks_left vượt thời gian ăn ({eat_full})")
    if "reserved" in c:
        res = c["reserved"]
        validate_items(res)  # kind hợp lệ, số nguyên >= 0
        res = {k: v for k, v in res.items() if v > 0}
        recipe = menu[c["dish_id"]]["recipe"]
        if status == "reserved" and res and res != recipe:
            raise BadInput(f"customers.{cid}.reserved khác công thức {c['dish_id']}")
        if status != "reserved" and res:
            raise BadInput(f"customers.{cid}: đơn {status} phải có reserved rỗng")
    eating = state == "eating"
    if eating != (status == "served"):
        raise BadInput(f"customers.{cid}: khách eating phải là đơn served và ngược lại")
    if eating:
        if c.get("eat_ticks_left", 0) <= 0 or "base_price" not in c or "tip" not in c:
            raise BadInput(f"customers.{cid}: khách eating cần eat_ticks_left > 0 và base_price, tip đã chốt")
    elif c.get("eat_ticks_left", 0):
        raise BadInput(f"customers.{cid}: khách chưa ăn thì eat_ticks_left = 0")


def validate_quan_links(scenario: dict, tuning: dict, stock: dict):
    """Kiểm liên kết đơn ↔ bếp/tay và giữ chỗ ↔ kho (PRD-0 mục D, mã 2).

    Gọi khi dựng QuanSim (lúc đó mới biết kho thật: --inventory hoặc scenario.stock).
    Trả về dict {customer_id: reserved} đã điền công thức cho đơn reserved thiếu `reserved`.
    """
    menu = tuning["menu"]
    customers = scenario.get("customers", [])
    by_id = {c["id"]: c for c in customers}
    holders = {}  # order_id -> nơi giữ món
    dishes = [(f"stoves.{st['id']}", st.get("dish")) for st in scenario.get("stoves", [])]
    dishes.append(("hand", scenario.get("hand")))
    for where, d in dishes:
        if d is None:
            continue
        c = by_id.get(d["order_id"])
        if c is None:
            raise BadInput(f"{where}: order_id {d['order_id']} không phải khách đang ngồi")
        if c.get("order_status", "reserved") != "assigned":
            raise BadInput(f"{where}: món chỉ thuộc đơn assigned ({d['order_id']})")
        if d["dish_id"] != c["dish_id"]:
            raise BadInput(f"{where}: món {d['dish_id']} không khớp đơn {d['order_id']} ({c['dish_id']})")
        if d["order_id"] in holders:
            raise BadInput(f"{where} và {holders[d['order_id']]} cùng giữ đơn {d['order_id']}")
        holders[d["order_id"]] = where
    for c in customers:
        if c.get("order_status", "reserved") == "assigned" and c["id"] not in holders:
            raise BadInput(f"customers.{c['id']}: đơn assigned phải có đúng một món ở bếp hoặc tay")
    # giữ chỗ: cấp công thức cho đơn reserved thiếu `reserved`, theo order_tick rồi id bàn
    filled = {}
    need = {}
    order = sorted(customers, key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))
    for c in order:
        if c.get("order_status", "reserved") != "reserved":
            filled[c["id"]] = {}
            continue
        res = c.get("reserved")
        res = dict(menu[c["dish_id"]]["recipe"]) if res is None or not any(res.values()) else \
            {k: v for k, v in res.items() if v > 0}
        filled[c["id"]] = res
        for k, v in res.items():
            need[k] = need.get(k, 0) + v
    for k, v in sorted(need.items()):
        if v > stock.get(k, 0):
            raise BadInput(f"giữ chỗ {k} = {v} vượt tồn kho {stock.get(k, 0)}")
    return filled
