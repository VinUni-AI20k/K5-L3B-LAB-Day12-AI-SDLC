"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
Lát 3 (quan.customers): trường lạ, bàn có thật / không trùng, món có trong menu, state/order_state hợp lệ,
kiên nhẫn trong [1, patience], giữ chỗ đúng công thức, khách eating đủ eat_ticks_left/price/tip,
khách giữ chỗ quá kho (khi kho ở scenario; kho từ --inventory thì QuanSim kiểm) -> mã 2.
TODO(nhóm): các mâu thuẫn khác của lát 4 (đơn assigned phải có đúng một món...) — PRD-0 mục D.
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
CUSTOMER_KEYS = {"id", "table_id", "state", "order_id", "dish_id", "order_state", "patience_ticks_left",
                 "reserved", "arrived_tick", "eat_ticks_left", "price", "tip"}
CUSTOMER_STATES = ("waiting", "eating")
ORDER_STATES_WAITING = ("reserved", "cooking", "ready", "carried")


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
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    _validate_customers(b, tuning)


def _validate_customers(b, tuning):
    q, menu = tuning["quan"], tuning["menu"]
    patience = int(round(q["patience_s"] * 60))
    eat = int(round(q["eat_s"] * 60))
    reserved_total, order_ids = {}, set()
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
        if "order_id" in c:
            if not isinstance(c["order_id"], str) or not c["order_id"]:
                raise BadInput(f"{cid}: order_id phải là chuỗi khác rỗng")
            if c["order_id"] in order_ids:
                raise BadInput(f"{cid}: order_id trùng {c['order_id']}")
            order_ids.add(c["order_id"])
        if "arrived_tick" in c:
            _nonneg_int(f"{cid}.arrived_tick", c["arrived_tick"])
        recipe = menu[c["dish_id"]]["recipe"]
        if state == "waiting":
            for k in ("eat_ticks_left", "price", "tip"):
                if k in c:
                    raise BadInput(f"{cid}: khách đang chờ không có {k}")
            order_state = c.get("order_state", "reserved")
            if order_state not in ORDER_STATES_WAITING:
                raise BadInput(f"{cid}: order_state phải là một trong {ORDER_STATES_WAITING}")
            if "patience_ticks_left" in c:
                pt = c["patience_ticks_left"]
                if isinstance(pt, bool) or not isinstance(pt, int) or not (1 <= pt <= patience):
                    raise BadInput(f"{cid}: patience_ticks_left phải là số nguyên trong [1, {patience}]")
            want = dict(recipe) if order_state == "reserved" else {}
            if "reserved" in c:
                validate_items(c["reserved"])
                if {k: v for k, v in c["reserved"].items() if v} != want:
                    raise BadInput(f"{cid}: reserved phải đúng công thức khi order_state=reserved, rỗng khi đã nấu")
            for k, n in want.items():
                reserved_total[k] = reserved_total.get(k, 0) + n
        else:
            if "order_state" in c and c["order_state"] != "served":
                raise BadInput(f"{cid}: khách đang ăn chỉ có order_state=served")
            if c.get("reserved"):
                raise BadInput(f"{cid}: khách đang ăn không giữ chỗ nguyên liệu")
            if "patience_ticks_left" in c:
                _nonneg_int(f"{cid}.patience_ticks_left", c["patience_ticks_left"])
                if c["patience_ticks_left"] > patience:
                    raise BadInput(f"{cid}: patience_ticks_left vượt kiên nhẫn tối đa")
            for k in ("eat_ticks_left", "price", "tip"):
                if k not in c:
                    raise BadInput(f"{cid}: khách đang ăn thiếu {k}")
                _nonneg_int(f"{cid}.{k}", c[k])
            if not (1 <= c["eat_ticks_left"] <= eat):
                raise BadInput(f"{cid}: eat_ticks_left phải trong [1, {eat}]")
    if "stock" in b:
        for k in sorted(reserved_total):
            if reserved_total[k] > b["stock"].get(k, 0):
                raise BadInput(f"khách giữ chỗ {reserved_total[k]} {k} nhưng stock chỉ có {b['stock'].get(k, 0)}")
