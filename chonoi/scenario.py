"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
quan (Commit 1 — TV3): kiểm mâu thuẫn mức luật theo PRD-0 mục D: khách reserved vượt kho,
đơn assigned phải có đúng một món ở bếp/tay, khách eating thiếu giá/tip... -> BadInput (mã 2).
"""

import json

from .errors import BadInput
from .inventory import KINDS_P1, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung")
FISH_KINDS = ("ca_linh", "ca_loc")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
QUAN_STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
QUAN_STOVE_STATES = ("idle", "cooking", "ready")
QUAN_CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                      "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
QUAN_CUSTOMER_STATES = ("waiting", "eating")
QUAN_ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")
DISH_KEYS = {"order_id", "dish_id", "base_price"}


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


def _check_dish(label, dish, menu, customer_ids):
    """Món đang nấu ở bếp hoặc giữ trên tay: payload {order_id, dish_id, base_price} khớp một đơn."""
    if not isinstance(dish, dict) or set(dish) != DISH_KEYS:
        raise BadInput(f"{label} phải là payload {{order_id, dish_id, base_price}}")
    if dish["dish_id"] not in menu:
        raise BadInput(f"{label}: dish_id phải là món trong menu")
    if dish["order_id"] not in customer_ids:
        raise BadInput(f"{label}: order_id phải khớp một khách tồn tại")
    if not _num(dish["base_price"]) or dish["base_price"] < 0:
        raise BadInput(f"{label}: base_price phải là số không âm")


def _validate_quan(b, tuning):
    q, menu = tuning["quan"], tuning["menu"]
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b and not (_num(b["reputation"])
                                  and q["reputation_min"] <= b["reputation"] <= q["reputation_max"]):
        raise BadInput(f"reputation phải là số trong [{q['reputation_min']}, {q['reputation_max']}]")
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = q["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")

    customers = b.get("customers", [])
    customer_ids = {c["id"] for c in customers}

    # Món đang nấu/giữ: tay + mỗi bếp tối đa một món; mỗi đơn chỉ được giữ ở đúng một chỗ.
    holders = []
    hand = b.get("hand")
    if hand is not None:
        _check_dish("hand", hand, menu, customer_ids)
        holders.append(("hand", hand["order_id"]))
    for s in b.get("stoves", []):
        extra = set(s) - QUAN_STOVE_KEYS
        if extra:
            raise BadInput(f"stoves.{s['id']}: trường lạ {sorted(extra)}")
        state = s.get("state", "idle")
        if state not in QUAN_STOVE_STATES:
            raise BadInput(f"stoves.{s['id']}: state phải là một trong {QUAN_STOVE_STATES}")
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in s:
                _nonneg_int(f"stoves.{s['id']}.{key}", s[key])
        if state == "cooking":
            if s.get("cook_ticks_left", 0) <= 0:
                raise BadInput(f"stoves.{s['id']}: bếp đang cooking cần cook_ticks_left > 0")
            if s.get("dish") is None:
                raise BadInput(f"stoves.{s['id']}: bếp đang cooking thiếu dish")
        if s.get("dish") is not None:
            _check_dish(f"stoves.{s['id']}.dish", s["dish"], menu, customer_ids)
            holders.append((f"stoves.{s['id']}", s["dish"]["order_id"]))
    held_by = {}
    for where, oid in holders:
        if oid in held_by:
            raise BadInput(f"đơn {oid} bị giữ ở cả {held_by[oid]} và {where}")
        held_by[oid] = where

    known_tables = {t["id"] for t in q["tables"]} | {t.get("id") for t in b.get("tables", [])}
    table_ids = []
    reserved_total = {}
    for c in customers:
        cid = c["id"]
        table_ids.append(c.get("table_id"))
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known_tables:
            raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
        extra = set(c) - QUAN_CUSTOMER_KEYS
        if extra:
            raise BadInput(f"customers.{cid}: trường lạ {sorted(extra)}")
        if c.get("dish_id") not in menu:
            raise BadInput(f"customers.{cid}: dish_id phải là món trong menu")
        for key in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
            if key in c:
                _nonneg_int(f"customers.{cid}.{key}", c[key])
        for key in ("base_price", "tip"):
            if key in c and not (_num(c[key]) and c[key] >= 0):
                raise BadInput(f"customers.{cid}: {key} phải là số không âm")
        state = c.get("state", "waiting")
        if state not in QUAN_CUSTOMER_STATES:
            raise BadInput(f"customers.{cid}: state phải là một trong {QUAN_CUSTOMER_STATES}")
        status = c.get("order_status", "reserved")
        if status not in QUAN_ORDER_STATUSES:
            raise BadInput(f"customers.{cid}: order_status phải là một trong {QUAN_ORDER_STATUSES}")
        reserved = None
        if c.get("reserved") is not None:
            if not isinstance(c["reserved"], dict):
                raise BadInput(f"customers.{cid}: reserved phải là object nguyên liệu")
            try:
                reserved = validate_items(c["reserved"])
            except BadInput as e:
                raise BadInput(f"customers.{cid}: reserved không hợp lệ: {e}")
        holds = [where for where, oid in holders if oid == cid]
        recipe = menu[c["dish_id"]].get("recipe", {})
        if status == "reserved":
            if reserved is None:
                # Thiếu giữ chỗ -> suy ra từ công thức (ưu tiên order_tick rồi table_id ảnh hưởng
                # lúc chạy; ở đây tổng reserved vẫn phải <= kho nên thứ tự không đổi kết luận).
                reserved = dict(recipe)
                c["reserved"] = dict(recipe)
            elif reserved != recipe:
                raise BadInput(f"customers.{cid}: reserved phải khớp đúng công thức của {c['dish_id']}")
        elif status == "assigned":
            if len(holds) != 1:
                raise BadInput(f"customers.{cid}: đơn assigned phải có đúng một món ở bếp hoặc trên tay")
            if reserved:
                raise BadInput(f"customers.{cid}: đơn assigned phải có reserved rỗng")
        elif status == "unfulfillable":
            if state != "waiting":
                raise BadInput(f"customers.{cid}: khách unfulfillable phải vẫn đang chờ (state=waiting)")
            if reserved:
                raise BadInput(f"customers.{cid}: khách unfulfillable phải có reserved rỗng")
            if holds:
                raise BadInput(f"customers.{cid}: đơn unfulfillable không được có món ở bếp/tay")
        if state == "eating":
            if status != "served":
                raise BadInput(f"customers.{cid}: khách đang ăn phải có order_status=served")
            if c.get("eat_ticks_left", 0) <= 0:
                raise BadInput(f"customers.{cid}: khách đang ăn cần eat_ticks_left > 0")
            if "base_price" not in c or "tip" not in c:
                raise BadInput(f"customers.{cid}: khách đang ăn cần khai base_price và tip đã chốt")
        for kind, n in (reserved or {}).items():
            reserved_total[kind] = reserved_total.get(kind, 0) + n
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
    if "stock" in b:
        for kind in sorted(reserved_total):
            if reserved_total[kind] > b["stock"].get(kind, 0):
                raise BadInput(f"tổng reserved của khách vượt kho: cần {reserved_total[kind]} '{kind}', "
                               f"kho chỉ còn {b['stock'].get(kind, 0)}")
