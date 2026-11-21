"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
Lát 3 (quan.customers, PRD-0 mục D): trường lạ, bàn có thật / không trùng, món có trong menu,
state/order_status hợp lệ, kiên nhẫn trong [0, patience] khi chờ, giữ chỗ đúng công thức / không quá tồn,
đơn assigned có đúng một món (bếp/tay), unfulfillable không có món và không giữ chỗ,
khách eating đủ eat_ticks_left/base_price/tip; payload món trỏ tới khách có thật và khớp đơn,
bếp cooking có timer dương, bếp idle không có món -> mã 2.
(Kho từ --inventory thì QuanSim kiểm giữ chỗ quá kho, vẫn trước khi ghi output.)
"""

import json

from .errors import BadInput
from .inventory import KINDS_P1, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
                 "order_status", "reserved", "base_price", "tip"}
CUSTOMER_STATES = ("waiting", "eating")
ORDER_STATUS_WAITING = ("reserved", "assigned", "unfulfillable")


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
        if "age_ticks" in f:  # v1.1 mục 4.3
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])


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
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    _validate_customers(b, tuning)
    _validate_dish_links(b, tuning)


def _dishes_for(order_id, b):
    """Số món của đơn đang nằm trên bếp hoặc trên tay (payload {"order_id", ...})."""
    n = sum(1 for st in b.get("stoves", []) if isinstance(st.get("dish"), dict)
            and st["dish"].get("order_id") == order_id)
    hand = b.get("hand")
    return n + (1 if isinstance(hand, dict) and hand.get("order_id") == order_id else 0)


def _validate_customers(b, tuning):
    q, menu = tuning["quan"], tuning["menu"]
    patience = int(round(q["patience_s"] * 60))
    eat = int(round(q["eat_s"] * 60))
    dur = int(round(q["duration_s"] * 60))
    reserved_total = {}
    for c in b.get("customers", []):
        cid = f"customers.{c['id']}"
        extra = set(c) - CUSTOMER_KEYS
        if extra:
            raise BadInput(f"{cid}: trường lạ/chưa hỗ trợ {sorted(extra)}")
        if c.get("dish_id") not in menu:
            raise BadInput(f"{cid}: dish_id phải là món trong menu {sorted(menu)}")
        state = c.get("state", "waiting")
        if state not in CUSTOMER_STATES:
            raise BadInput(f"{cid}: state phải là một trong {CUSTOMER_STATES}")
        if "order_tick" in c:
            _nonneg_int(f"{cid}.order_tick", c["order_tick"])
            if c["order_tick"] > dur:
                raise BadInput(f"{cid}: order_tick vượt độ dài ca")
        for k in ("eat_ticks_left", "base_price", "tip"):
            if k in c:
                _nonneg_int(f"{cid}.{k}", c[k])
        if "reserved" in c:
            validate_items(c["reserved"])
        reserved = {k: v for k, v in c.get("reserved", {}).items() if v}
        recipe = menu[c["dish_id"]]["recipe"]
        if state == "waiting":
            status = c.get("order_status", "reserved")
            if status not in ORDER_STATUS_WAITING:
                raise BadInput(f"{cid}: khách đang chờ có order_status trong {ORDER_STATUS_WAITING}")
            if "patience_ticks_left" in c:
                pt = c["patience_ticks_left"]
                if isinstance(pt, bool) or not isinstance(pt, int) or not (0 <= pt <= patience):
                    raise BadInput(f"{cid}: patience_ticks_left phải là số nguyên trong [0, {patience}]")
            for k in ("eat_ticks_left", "base_price", "tip"):
                if c.get(k, 0) != 0:
                    raise BadInput(f"{cid}: khách đang chờ có {k} = 0")
            if status == "reserved":
                if "reserved" in c and reserved != dict(recipe):
                    raise BadInput(f"{cid}: reserved phải đúng công thức {dict(recipe)}")
                if _dishes_for(c["id"], b):
                    raise BadInput(f"{cid}: đơn reserved chưa nấu nên không có món ở bếp/tay")
                for k, n in recipe.items():
                    reserved_total[k] = reserved_total.get(k, 0) + n
            else:
                if reserved:
                    raise BadInput(f"{cid}: đơn {status} không giữ chỗ nguyên liệu")
                want = 1 if status == "assigned" else 0
                if _dishes_for(c["id"], b) != want:
                    raise BadInput(f"{cid}: đơn {status} phải có đúng {want} món ở bếp/tay")
        else:
            if c.get("order_status", "served") != "served":
                raise BadInput(f"{cid}: khách đang ăn có order_status = served")
            if reserved:
                raise BadInput(f"{cid}: khách đang ăn không giữ chỗ nguyên liệu")
            if "patience_ticks_left" in c:
                _nonneg_int(f"{cid}.patience_ticks_left", c["patience_ticks_left"])
                if c["patience_ticks_left"] > patience:
                    raise BadInput(f"{cid}: patience_ticks_left vượt kiên nhẫn tối đa")
            for k in ("eat_ticks_left", "base_price", "tip"):
                if k not in c:
                    raise BadInput(f"{cid}: khách đang ăn thiếu {k}")
            if not (1 <= c["eat_ticks_left"] <= eat):
                raise BadInput(f"{cid}: eat_ticks_left phải trong [1, {eat}]")
            if c["base_price"] != menu[c["dish_id"]]["price"]:
                raise BadInput(f"{cid}: base_price phải bằng giá món {menu[c['dish_id']]['price']}")
            if _dishes_for(c["id"], b):
                raise BadInput(f"{cid}: khách đang ăn thì món không còn ở bếp/tay")
    if "stock" in b:
        for k in sorted(reserved_total):
            if reserved_total[k] > b["stock"].get(k, 0):
                raise BadInput(f"khách giữ chỗ {reserved_total[k]} {k} nhưng stock chỉ có {b['stock'].get(k, 0)}")


PAYLOAD_KEYS = {"order_id", "dish_id", "base_price"}
STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
STOVE_STATES = ("idle", "cooking", "ready")


def _validate_payload(name, p, customers, menu):
    """Payload món {order_id, dish_id, base_price}: order_id = id khách có thật, món khớp đơn, giá đã chốt."""
    if not isinstance(p, dict) or set(p) != PAYLOAD_KEYS:
        raise BadInput(f"{name}: payload món phải có đúng {sorted(PAYLOAD_KEYS)}")
    c = customers.get(p["order_id"])
    if c is None:
        raise BadInput(f"{name}: order_id {p['order_id']!r} không trỏ tới khách nào (liên kết thiếu)")
    if p["dish_id"] != c.get("dish_id"):
        raise BadInput(f"{name}: món {p['dish_id']!r} không khớp đơn {p['order_id']}")
    if isinstance(p["base_price"], bool) or p["base_price"] != menu[c["dish_id"]]["price"]:
        raise BadInput(f"{name}: base_price phải bằng giá món {menu[c['dish_id']]['price']}")


def _validate_dish_links(b, tuning):
    """PRD-0 mục D: món trên bếp/tay phải khớp đơn; bếp cooking có timer dương; bếp idle không có món."""
    menu = tuning["menu"]
    customers = {c["id"]: c for c in b.get("customers", [])}
    if b.get("hand") is not None:
        _validate_payload("hand", b["hand"], customers, menu)
    qb = tuning["quan"]["bounds"]
    for st in b.get("stoves", []):
        sid = f"stoves.{st['id']}"
        extra = set(st) - STOVE_KEYS
        if extra:
            raise BadInput(f"{sid}: trường lạ/chưa hỗ trợ {sorted(extra)}")
        if "pos" in st:
            _pos(f"{sid}.pos", st["pos"], qb, axes=("x", "z"))
        state = st.get("state", "idle")
        if state not in STOVE_STATES:
            raise BadInput(f"{sid}: state phải là một trong {STOVE_STATES}")
        for k in ("cook_ticks_left", "ready_ticks"):
            if k in st:
                _nonneg_int(f"{sid}.{k}", st[k])
        dish = st.get("dish")
        if state == "idle":
            if dish is not None or st.get("cook_ticks_left", 0) or st.get("ready_ticks", 0):
                raise BadInput(f"{sid}: bếp idle không có món và bộ đếm bằng 0")
            continue
        _validate_payload(f"{sid}.dish", dish, customers, menu)
        if state == "cooking" and st.get("cook_ticks_left", 0) <= 0:
            raise BadInput(f"{sid}: bếp cooking phải có cook_ticks_left dương")
        if state == "ready" and st.get("cook_ticks_left", 0) != 0:
            raise BadInput(f"{sid}: bếp ready có cook_ticks_left = 0")
