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


CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                 "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
CUSTOMER_STATES = {"waiting", "eating"}
ORDER_STATUSES = {"reserved", "cooking", "ready", "carried", "served"}
STOVE_STATES = {"idle", "cooking", "ready"}
STOVE_KEYS = {"id", "pos", "state", "dish", "dish_id", "cook_ticks_left", "ready_ticks", "order_id", "customer_id"}
TABLE_KEYS = {"id", "pos", "customer_id"}
HAND_KEYS = {"dish", "dish_id", "order_id", "customer_id"}


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")

    q_tuning = tuning["quan"]
    menu = tuning["menu"]
    qb = q_tuning["bounds"]

    if "reputation" in b:
        rep = b["reputation"]
        if not _num(rep) or not (q_tuning["reputation_min"] <= rep <= q_tuning["reputation_max"]):
            raise BadInput(f"reputation phải là số trong [{q_tuning['reputation_min']}, {q_tuning['reputation_max']}]")

    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")

    known_tables = {t["id"]: t for t in q_tuning["tables"]}
    for t in b.get("tables", []):
        if not isinstance(t, dict):
            raise BadInput("tables phải là mảng object")
        extra = set(t) - TABLE_KEYS
        if extra:
            raise BadInput(f"tables.{t.get('id', '?')}: trường lạ: {sorted(extra)}")
        if t["id"] not in known_tables:
            raise BadInput(f"id bàn không tồn tại: {t['id']}")
        if "pos" in t:
            _pos(f"tables.{t['id']}.pos", t["pos"], qb, axes=("x", "z"))
        known_tables[t["id"]] = t

    known_stoves = {s["id"]: s for s in q_tuning["stoves"]}
    stove_orders = {}
    for s in b.get("stoves", []):
        if not isinstance(s, dict):
            raise BadInput("stoves phải là mảng object")
        extra = set(s) - STOVE_KEYS
        if extra:
            raise BadInput(f"stoves.{s.get('id', '?')}: trường lạ: {sorted(extra)}")
        if s["id"] not in known_stoves:
            raise BadInput(f"id bếp không tồn tại: {s['id']}")
        if "pos" in s:
            _pos(f"stoves.{s['id']}.pos", s["pos"], qb, axes=("x", "z"))
        state = s.get("state", "idle")
        if state not in STOVE_STATES:
            raise BadInput(f"stoves.{s['id']}: state không hợp lệ: {state}")
        dish = s.get("dish") or s.get("dish_id")
        if dish is not None and dish not in menu:
            raise BadInput(f"stoves.{s['id']}: dish không có trong menu: {dish}")
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in s:
                _nonneg_int(f"stoves.{s['id']}.{key}", s[key])
        oid = s.get("order_id") or s.get("customer_id")
        if oid is not None:
            if not isinstance(oid, str) or not oid:
                raise BadInput(f"stoves.{s['id']}: order_id phải là chuỗi khác rỗng")
            if oid in stove_orders:
                raise BadInput(f"hai bếp cùng giữ một đơn: {oid}")
            stove_orders[oid] = s["id"]
        known_stoves[s["id"]] = s

    hand = b.get("hand")
    hand_oid = None
    if hand is not None:
        if isinstance(hand, dict):
            extra = set(hand) - HAND_KEYS
            if extra:
                raise BadInput(f"hand có trường lạ: {sorted(extra)}")
            dish = hand.get("dish") or hand.get("dish_id")
            if dish is not None and dish not in menu:
                raise BadInput(f"hand: món không có trong menu: {dish}")
            hand_oid = hand.get("order_id") or hand.get("customer_id")
            if hand_oid is not None and (not isinstance(hand_oid, str) or not hand_oid):
                raise BadInput("hand: order_id phải là chuỗi khác rỗng")
        elif isinstance(hand, str):
            pass
        else:
            raise BadInput("hand phải là dict hoặc chuỗi")

    if hand_oid is not None and hand_oid in stove_orders:
        raise BadInput(f"bếp và tay cùng giữ một đơn: {hand_oid}")

    customers = b.get("customers", [])
    cust_ids = set()
    table_ids = []
    total_reserved = {}

    for c in customers:
        if not isinstance(c, dict):
            raise BadInput("customers phải là mảng object")
        cid = c.get("id")
        if not isinstance(cid, str) or not cid:
            raise BadInput("customers: mỗi phần tử cần id (chuỗi khác rỗng)")
        cust_ids.add(cid)
        extra = set(c) - CUSTOMER_KEYS
        if extra:
            raise BadInput(f"customers.{cid}: trường lạ: {sorted(extra)}")

        tid = c.get("table_id")
        if not isinstance(tid, str) or tid not in known_tables:
            raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
        table_ids.append(tid)

        did = c.get("dish_id")
        if not isinstance(did, str) or did not in menu:
            raise BadInput(f"customers.{cid}: dish_id phải là món trong menu")

        state = c.get("state", "waiting")
        if state not in CUSTOMER_STATES:
            raise BadInput(f"customers.{cid}: state không hợp lệ: {state}")

        status = c.get("order_status", "reserved" if state == "waiting" else "served")
        if status not in ORDER_STATUSES:
            raise BadInput(f"customers.{cid}: order_status không hợp lệ: {status}")

        if state == "eating" and status != "served":
            raise BadInput(f"customers.{cid}: khách đang ăn phải có order_status là 'served'")

        for timer in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
            if timer in c:
                _nonneg_int(f"customers.{cid}.{timer}", c[timer])

        if "tip" in c:
            tip = c["tip"]
            if isinstance(tip, bool) or not isinstance(tip, (int, float)) or tip < 0:
                raise BadInput(f"customers.{cid}.tip phải là số không âm")

        if "base_price" in c and c["base_price"] is not None:
            bp = c["base_price"]
            if isinstance(bp, bool) or not isinstance(bp, int) or bp <= 0:
                raise BadInput(f"customers.{cid}.base_price phải là số nguyên dương")

        recipe = menu[did]["recipe"]

        if "reserved" in c:
            res = c["reserved"]
            if not isinstance(res, dict):
                raise BadInput(f"customers.{cid}.reserved phải là object")
            for rk, rv in res.items():
                if rk not in KINDS_P1:
                    raise BadInput(f"customers.{cid}.reserved: nguyên liệu lạ {rk}")
                if isinstance(rv, bool) or not isinstance(rv, int) or rv < 0:
                    raise BadInput(f"customers.{cid}.reserved: số lượng cho {rk} phải là số nguyên không âm")

            cleaned_res = {k: v for k, v in res.items() if v > 0}
            if status != "reserved":
                if cleaned_res:
                    raise BadInput(f"customers.{cid}: trạng thái đơn hàng {status} mâu thuẫn với nguyên liệu giữ")
            else:
                if cleaned_res != recipe:
                    raise BadInput(f"customers.{cid}: nguyên liệu giữ không phù hợp công thức món {did}")
        else:
            if status != "reserved":
                cleaned_res = {}
            else:
                cleaned_res = recipe

        if status == "reserved":
            for rk, rv in cleaned_res.items():
                total_reserved[rk] = total_reserved.get(rk, 0) + rv

    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")

    for oid in stove_orders:
        if oid not in cust_ids:
            raise BadInput(f"bếp tham chiếu order/customer không tồn tại: {oid}")
    if hand_oid is not None and hand_oid not in cust_ids:
        raise BadInput(f"tay tham chiếu order/customer không tồn tại: {hand_oid}")

    if "stock" in b:
        stock = b["stock"]
        for rk, rv in total_reserved.items():
            if rv > stock.get(rk, 0):
                raise BadInput(f"tổng nguyên liệu giữ vượt quá kho thực tế cho {rk}: giữ {rv}, kho có {stock.get(rk, 0)}")
