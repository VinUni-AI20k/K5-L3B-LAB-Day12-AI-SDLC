"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .inventory import KINDS_P1, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
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
    for key in ("catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
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
    _validate_quan_rules(b, tuning)


ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")
DISH_PAYLOAD_KEYS = {"order_id", "dish_id", "base_price"}


def _dish_payload(name, v, menu):
    """Payload món (PRD-0 mục D): {order_id, dish_id, base_price}; hand và stoves[].dish là null hoặc payload."""
    if v is None:
        return None
    if not isinstance(v, dict) or set(v) != DISH_PAYLOAD_KEYS:
        raise BadInput(f"{name} phải là null hoặc {{order_id, dish_id, base_price}}")
    if not isinstance(v["order_id"], str) or not v["order_id"]:
        raise BadInput(f"{name}.order_id phải là chuỗi khác rỗng")
    if not isinstance(v["dish_id"], str) or v["dish_id"] not in menu:
        raise BadInput(f"{name}.dish_id phải là một món trong menu")
    _nonneg_int(f"{name}.base_price", v["base_price"])
    return v


def _validate_quan_rules(b, tuning):
    """Mâu thuẫn mức luật của quán (PRD-0 mục D): payload món, đơn assigned/unfulfillable/served,
    khách eating, giữ chỗ khác công thức hoặc quá tồn, bếp và tay giữ cùng đơn hoặc món không khớp đơn."""
    menu = tuning["menu"]
    q = tuning["quan"]
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput(f"reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")

    customers = {c["id"]: c for c in b.get("customers", [])}
    held = {}  # order_id -> nơi giữ món ("hand" hoặc "stoves.<id>")

    def hold_payload(where, payload):
        if payload is None:
            return
        oid = payload["order_id"]
        if oid not in customers:
            raise BadInput(f"{where}: order_id {oid!r} không phải khách nào trong scenario")
        dish = customers[oid].get("dish_id")
        if dish is not None and dish != payload["dish_id"]:
            raise BadInput(f"{where}: món {payload['dish_id']!r} không khớp đơn của khách {oid!r} ({dish!r})")
        if oid in held:
            raise BadInput(f"{where} và {held[oid]} cùng giữ đơn {oid!r}")
        held[oid] = where

    hold_payload("hand", _dish_payload("hand", b.get("hand"), menu))
    for s in b.get("stoves", []):
        where = f"stoves.{s['id']}"
        hold_payload(where, _dish_payload(f"{where}.dish", s.get("dish"), menu))
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in s:
                _nonneg_int(f"{where}.{key}", s[key])

    reserved_total = {}
    for cid, c in customers.items():
        status = c.get("order_status", "reserved")
        if status not in ORDER_STATUSES:
            raise BadInput(f"customers.{cid}.order_status phải thuộc {ORDER_STATUSES}")
        reserved = validate_items(c["reserved"]) if "reserved" in c else None
        dish = c.get("dish_id")
        if dish is not None and dish not in menu:
            raise BadInput(f"customers.{cid}.dish_id không có trong menu ({dish!r})")
        if status == "reserved" and reserved is not None and dish is not None and reserved != menu[dish]["recipe"]:
            raise BadInput(f"customers.{cid}: phần giữ chỗ khác công thức của {dish}")
        if status == "assigned":
            if cid not in held:
                raise BadInput(f"customers.{cid}: đơn assigned phải có đúng một món ở bếp hoặc tay")
            if reserved:
                raise BadInput(f"customers.{cid}: đơn assigned phải có phần giữ rỗng")
        if status == "unfulfillable":
            if reserved:
                raise BadInput(f"customers.{cid}: đơn unfulfillable phải có phần giữ rỗng")
            if cid in held:
                raise BadInput(f"customers.{cid}: đơn unfulfillable không có món")
        if c.get("state") == "eating":
            if status != "served":
                raise BadInput(f"customers.{cid}: khách eating phải có order_status served")
            eat = c.get("eat_ticks_left")
            if isinstance(eat, bool) or not isinstance(eat, int) or eat <= 0:
                raise BadInput(f"customers.{cid}: khách eating cần eat_ticks_left dương")
            for key in ("base_price", "tip"):
                _nonneg_int(f"customers.{cid}.{key}", c.get(key))
        for k, v in (reserved or {}).items():
            reserved_total[k] = reserved_total.get(k, 0) + v
    # Kho đến từ --inventory thì load_scenario không biết; headless gọi check_reserved_within_stock sau khi đọc kho.
    if "stock" in b:
        _check_within_stock(reserved_total, b["stock"])


def _check_within_stock(need, stock):
    for k in sorted(need):
        if need[k] > stock.get(k, 0):
            raise BadInput(f"khách giữ chỗ {k} = {need[k]} vượt kho ({stock.get(k, 0)})")


def check_reserved_within_stock(block, stock):
    """Phần giữ chỗ nguyên liệu của khách (ghi rõ trong `customers[].reserved`) không được vượt kho (PRD-0 mục D, mã 2).
    Dùng cho kho nạp từ --inventory; `block` là khối quan đã qua load_scenario nên `reserved` đã hợp lệ."""
    need = {}
    for c in block.get("customers", []):
        for k, v in (c.get("reserved") or {}).items():
            need[k] = need.get(k, 0) + v
    _check_within_stock(need, stock)
