"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json
import math

from .errors import BadInput
from .inventory import KINDS_P1, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
NODE_KEYS = {"id", "kind", "pos", "regrow_ticks"}
FISH_KEYS = {"id", "kind", "pos", "heading_deg"}
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
    """Kiểm v là số hữu hạn (loại bool, NaN, ±Infinity)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


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
    cd_max = int(round(g["catch_cooldown_s"] * 60))
    if "catch_cd_ticks" in p and p["catch_cd_ticks"] > cd_max:
        raise BadInput(f"player.catch_cd_ticks phải trong [0, {cd_max}]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    regrow_max = int(round(g["regrow_s"] * 60))
    for n in b.get("nodes", []):
        extra = set(n) - NODE_KEYS
        if extra:
            raise BadInput(f"nodes.{n['id']}: trường lạ/chưa hỗ trợ {sorted(extra)}")
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
            if n["regrow_ticks"] > regrow_max:
                raise BadInput(f"nodes.{n['id']}.regrow_ticks phải trong [0, {regrow_max}]")
    for f in b.get("fish", []):
        extra = set(f) - FISH_KEYS
        if extra:
            raise BadInput(f"fish.{f['id']}: trường lạ/chưa hỗ trợ {sorted(extra)}")
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")


QUAN_STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
QUAN_TABLE_KEYS = {"id", "pos"}
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                 "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
DISH_KEYS = {"order_id", "dish_id", "base_price"}
STOVE_STATES = ("idle", "cooking", "ready")
CUSTOMER_STATES = ("waiting", "eating")
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")


def _validate_quan(b, tuning):
    q, menu = tuning["quan"], tuning["menu"]
    qb = q["bounds"]
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput(f"reputation phải là số trong [{q['reputation_min']}, {q['reputation_max']}]")
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    customers = {c["id"]: c for c in b.get("customers", [])}
    _validate_tables(b.get("tables", []), q)
    for c in customers.values():
        _validate_customer(c, q, menu)
    # món đang ở bếp / trên tay: payload hợp lệ, nối đúng đơn assigned, mỗi đơn tối đa một món
    holders = {}  # order_id -> [(nơi giữ, payload món)]
    for s in b.get("stoves", []):
        dish = _validate_stove(s, q, menu)
        if dish is not None:
            holders.setdefault(dish["order_id"], []).append((f"stoves.{s['id']}", dish))
    if b.get("hand") is not None:
        _check_dish("hand", b["hand"], menu)
        holders.setdefault(b["hand"]["order_id"], []).append(("hand", b["hand"]))
    for oid, held in holders.items():
        where, dish = held[0]
        c = customers.get(oid)
        if c is None:
            raise BadInput(f"{where}: order_id {oid} không trỏ tới khách nào")
        if len(held) > 1:
            raise BadInput(f"đơn {oid} có nhiều hơn một món ({', '.join(w for w, _ in held)})")
        if c.get("order_status", "reserved") != "assigned":
            raise BadInput(f"{where}: đơn {oid} phải ở trạng thái assigned")
        if dish["dish_id"] != c["dish_id"]:
            raise BadInput(f"{where}: món {dish['dish_id']} không khớp đơn {oid} ({c['dish_id']})")
    for c in customers.values():
        if c.get("order_status", "reserved") == "assigned" and c["id"] not in holders:
            raise BadInput(f"customers.{c['id']}: đơn assigned phải có đúng một món ở bếp hoặc trên tay")


def _validate_tables(tables, q):
    known = {t["id"] for t in q["tables"]}
    for t in tables:
        if set(t) - QUAN_TABLE_KEYS:
            raise BadInput(f"tables.{t['id']}: trường lạ/chưa hỗ trợ {sorted(set(t) - QUAN_TABLE_KEYS)}")
        if t["id"] not in known:
            raise BadInput(f"tables.{t['id']}: id bàn không tồn tại")
        if "pos" in t:
            _pos(f"tables.{t['id']}.pos", t["pos"], q["bounds"], axes=("x", "z"))


def _validate_customer(c, q, menu):
    cid = c["id"]
    extra = set(c) - CUSTOMER_KEYS
    if extra:
        raise BadInput(f"customers.{cid}: trường lạ/chưa hỗ trợ {sorted(extra)}")
    if not isinstance(c.get("table_id"), str) or c["table_id"] not in {t["id"] for t in q["tables"]}:
        raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
    if c.get("dish_id") not in menu:
        raise BadInput(f"customers.{cid}: dish_id phải là một trong {sorted(menu)}")
    state = c.get("state", "waiting")
    status = c.get("order_status", "reserved")
    if state not in CUSTOMER_STATES:
        raise BadInput(f"customers.{cid}: state phải là một trong {CUSTOMER_STATES}")
    if status not in ORDER_STATUSES:
        raise BadInput(f"customers.{cid}: order_status phải là một trong {ORDER_STATUSES}")
    for key in ("order_tick", "patience_ticks_left", "eat_ticks_left", "base_price", "tip"):
        if key in c:
            _nonneg_int(f"customers.{cid}.{key}", c[key])
    if c.get("patience_ticks_left", 0) > int(round(q["patience_s"] * 60)):
        raise BadInput(f"customers.{cid}.patience_ticks_left vượt kiên nhẫn tối đa")
    if c.get("eat_ticks_left", 0) > int(round(q["eat_s"] * 60)):
        raise BadInput(f"customers.{cid}.eat_ticks_left vượt thời gian ăn")
    reserved = c.get("reserved")
    if reserved is not None:
        reserved = validate_items(reserved)
    if (state == "eating") != (status == "served"):
        raise BadInput(f"customers.{cid}: khách eating phải có order_status served (và ngược lại)")
    if state == "eating":
        if c.get("eat_ticks_left", 0) <= 0:
            raise BadInput(f"customers.{cid}: khách eating cần eat_ticks_left > 0")
        if "base_price" not in c or "tip" not in c:
            raise BadInput(f"customers.{cid}: khách eating phải khai base_price và tip đã chốt")
    if status == "reserved" and reserved is not None and reserved != menu[c["dish_id"]]["recipe"]:
        raise BadInput(f"customers.{cid}: reserved khác công thức {c['dish_id']}")
    if status != "reserved" and reserved:
        raise BadInput(f"customers.{cid}: đơn {status} phải có phần giữ rỗng")


def _validate_stove(s, q, menu):
    """Kiểm một bản cập nhật bếp; trả payload món đang giữ (hoặc None)."""
    sid = s["id"]
    extra = set(s) - QUAN_STOVE_KEYS
    if extra:
        raise BadInput(f"stoves.{sid}: trường lạ/chưa hỗ trợ {sorted(extra)}")
    if sid not in {x["id"] for x in q["stoves"]}:
        raise BadInput(f"stoves.{sid}: id bếp không tồn tại")
    if "pos" in s:
        _pos(f"stoves.{sid}.pos", s["pos"], q["bounds"], axes=("x", "z"))
    state = s.get("state", "idle")
    if state not in STOVE_STATES:
        raise BadInput(f"stoves.{sid}: state phải là một trong {STOVE_STATES}")
    for key in ("cook_ticks_left", "ready_ticks"):
        if key in s:
            _nonneg_int(f"stoves.{sid}.{key}", s[key])
    dish = s.get("dish")
    cook = s.get("cook_ticks_left", 0)
    if state == "idle":
        if dish is not None or cook or s.get("ready_ticks", 0):
            raise BadInput(f"stoves.{sid}: bếp idle không có món và bộ đếm phải bằng 0")
        return None
    if dish is None:
        raise BadInput(f"stoves.{sid}: bếp {state} phải có món")
    _check_dish(f"stoves.{sid}.dish", dish, menu)
    if state == "cooking":
        cook_max = int(round(menu[dish["dish_id"]]["cook_s"] * 60))
        if not (1 <= cook <= cook_max) or s.get("ready_ticks", 0):
            raise BadInput(f"stoves.{sid}: bếp cooking cần cook_ticks_left trong [1, {cook_max}], ready_ticks = 0")
    elif cook:
        raise BadInput(f"stoves.{sid}: bếp ready cần cook_ticks_left = 0")
    return dish


def _check_dish(name, dish, menu):
    if not isinstance(dish, dict) or set(dish) != DISH_KEYS:
        raise BadInput(f"{name}: payload món phải đúng các khóa {sorted(DISH_KEYS)}")
    if not isinstance(dish["order_id"], str) or dish["dish_id"] not in menu:
        raise BadInput(f"{name}: order_id phải là chuỗi, dish_id phải có trong menu")
    if isinstance(dish["base_price"], bool) or not isinstance(dish["base_price"], int) or dish["base_price"] <= 0:
        raise BadInput(f"{name}: base_price phải là số nguyên dương")


def check_reserved_within_stock(customers, stock):
    """Kiểm tổng phần giữ chỗ của khách không vượt tồn vật lý.

    Gọi sau khi đã điền `reserved` mặc định theo công thức (QuanSim), vì tồn có thể đến
    từ `--inventory` chứ không chỉ `scenario.quan.stock`.

    Args:
        customers: danh sách khách đã dựng, mỗi khách có `reserved` (kind -> số lượng).
        stock: tồn vật lý (kind -> số lượng), gồm cả phần đã giữ.

    Raises:
        BadInput: khi một nguyên liệu bị giữ nhiều hơn tồn (mã 2).
    """
    total = {}
    for c in customers:
        for kind, n in c.get("reserved", {}).items():
            total[kind] = total.get(kind, 0) + n
    for kind, n in sorted(total.items()):
        if n > stock.get(kind, 0):
            raise BadInput(f"giữ chỗ {kind} ×{n} vượt tồn ({stock.get(kind, 0)})")
