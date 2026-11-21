"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json
import math

from .errors import BadInput
from .inventory import KINDS
from .items import parse_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "monsters", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                 "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
PAYLOAD_KEYS = {"order_id", "dish_id", "base_price"}
MONSTER_INSTANCE_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state",
                         "state_ticks_left", "recoil_dir"}


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
    """gather/quan: trả khối của mode. day (v1.1 mục 4.3): trả {"gather", "quan", "day"} (khối vắng = {})."""
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan", "day"}:
        raise BadInput("scenario chỉ được có khối 'gather', 'quan' hoặc (với --mode day) 'day'")
    if mode == "day":
        out = {}
        for m in ("gather", "quan"):
            if m in data:
                out[m] = _load_block(data[m], m, tuning, in_day=True)
        out["day"] = _validate_day(data.get("day", {}), tuning)
        return out
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    return _load_block(data.get(mode, {}), mode, tuning)


def _load_block(block, mode, tuning, in_day=False):
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    if in_day and mode == "quan":
        bad = {"stock", "reputation"} & set(block)
        if bad:
            raise BadInput(f"--mode day cấm quan.{'/'.join(sorted(bad))} (dùng gather.hold / day.reputation)")
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


DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def _validate_day(d, tuning):
    """Khối day {money, earned, reputation, upgrades, day_plan} — v1.1 mục 4.3."""
    from .contract import plan_ingredients
    if not isinstance(d, dict):
        raise BadInput("khối day phải là object")
    extra = set(d) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    for k in ("money", "earned"):
        if k in d:
            _nonneg_int(f"day.{k}", d[k])
    money, earned = d.get("money", 0), d.get("earned", 0)
    if money > 0 and "earned" not in d:
        raise BadInput("day: có tiền đầu kỳ thì phải khai cả money và earned")
    if not money <= earned:
        raise BadInput("day: cần 0 <= money <= earned")
    if "reputation" in d:
        q = tuning["quan"]
        if not _num(d["reputation"]) or not (q["reputation_min"] <= d["reputation"] <= q["reputation_max"]):
            raise BadInput("day.reputation phải trong [reputation_min, reputation_max]")
    ups = d.get("upgrades", {})
    if not isinstance(ups, dict):
        raise BadInput("day.upgrades phải là object id -> cấp")
    for k, lvl in ups.items():
        levels = tuning["shop"]["upgrades"].get(k)
        if levels is None:
            raise BadInput(f"day.upgrades.{k}: nâng cấp không có trong shop.upgrades")
        if isinstance(lvl, bool) or not isinstance(lvl, int) or not (0 <= lvl <= len(levels)):
            raise BadInput(f"day.upgrades.{k} phải là cấp nguyên trong [0, {len(levels)}]")
    plan = d.get("day_plan", [])
    if not isinstance(plan, list):
        raise BadInput("day.day_plan phải là mảng")
    seen = set()
    for p in plan:
        if not isinstance(p, dict) or set(p) - {"day", "dishes", "ingredients"} or "dishes" not in p:
            raise BadInput("day.day_plan: mỗi mục là {day, dishes[, ingredients]}")
        if isinstance(p.get("day"), bool) or p.get("day") not in (1, 2, 3, 4, 5) or p["day"] in seen:
            raise BadInput("day.day_plan.day phải là 1..5, không trùng")
        seen.add(p["day"])
        dishes = p["dishes"]
        if (not isinstance(dishes, dict) or not dishes or any(x not in tuning["menu"] for x in dishes)
                or not all(isinstance(n, int) and not isinstance(n, bool) and n > 0 for n in dishes.values())):
            raise BadInput(f"day.day_plan.{p['day']}.dishes phải là map id món -> số nguyên dương")
        if "ingredients" in p and p["ingredients"] != plan_ingredients(dishes, tuning["menu"]):
            raise BadInput(f"day.day_plan.{p['day']}.ingredients khác tổng công thức × số suất")
    return d


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
        parse_items(h, KINDS, "gather.hold")  # v1.2: mảng cá thể {id, kind, fresh} theo thứ tự vào giỏ
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
        if "age_ticks" in f:  # v1.1: số bước cá đã tham gia bơi
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    for m in b.get("monsters", []):
        extra = set(m) - MONSTER_INSTANCE_KEYS
        if extra:
            raise BadInput(f"monsters.{m['id']}: trường lạ {sorted(extra)}")
        species = tuning["gather"]["monsters"]["species"]
        kind = m.get("kind")
        if not isinstance(kind, str) or kind not in species:
            raise BadInput(f"monsters.{m['id']}: kind phải thuộc {sorted(species)}")
        depths = species[kind]["depths"]
        _pos(f"monsters.{m['id']}.pos", m.get("pos"), bounds)
        if not depths[0] <= m["pos"][1] <= depths[1]:
            raise BadInput(f"monsters.{m['id']}.pos nằm ngoài dải độ sâu {depths}")
        waypoints = m.get("waypoints")
        if not isinstance(waypoints, list) or len(waypoints) != 2:
            raise BadInput(f"monsters.{m['id']}.waypoints phải có đúng 2 điểm")
        for index, point in enumerate(waypoints):
            _pos(f"monsters.{m['id']}.waypoints[{index}]", point, bounds)
            if not depths[0] <= point[1] <= depths[1]:
                raise BadInput(f"monsters.{m['id']}.waypoints[{index}] nằm ngoài dải độ sâu {depths}")
        target_idx = m.get("target_idx", 1)
        if isinstance(target_idx, bool) or not isinstance(target_idx, int) or target_idx not in (0, 1):
            raise BadInput(f"monsters.{m['id']}.target_idx phải là 0 hoặc 1")
        state = m.get("state", "patrol")
        if state not in ("patrol", "chase", "recoil"):
            raise BadInput(f"monsters.{m['id']}.state không hợp lệ")
        ticks = m.get("state_ticks_left", 0)
        _nonneg_int(f"monsters.{m['id']}.state_ticks_left", ticks)
        if state == "recoil":
            if ticks <= 0:
                raise BadInput(f"monsters.{m['id']}: recoil cần state_ticks_left dương")
            direction = m.get("recoil_dir")
            if not (isinstance(direction, list) and len(direction) == 2 and all(_num(v) for v in direction)
                    and math.isclose(math.hypot(*direction), 1.0, rel_tol=1e-6, abs_tol=1e-6)):
                raise BadInput(f"monsters.{m['id']}.recoil_dir phải là vector đơn vị khi recoil")
        elif ticks != 0 or m.get("recoil_dir") is not None:
            raise BadInput(f"monsters.{m['id']}: timer/recoil_dir chỉ dùng khi recoil")


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    below = tuning["freshness"]["spoiled_below"]
    if "stock" in b:
        stock = {it["id"]: it for it in parse_items(b["stock"], KINDS, "quan.stock")}  # v1.2: mảng cá thể
    else:
        stock = None
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
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
    menu = tuning["menu"]
    customers = b.get("customers", [])
    stoves = {s["id"]: dict(s) for s in tuning["quan"]["stoves"]}
    for update in b.get("stoves", []):
        if update["id"] not in stoves:
            raise BadInput(f"id bếp không tồn tại: {update['id']}")
        stoves[update["id"]].update(update)
    default_table_ids = {t["id"] for t in tuning["quan"]["tables"]}
    if any(tb["id"] not in default_table_ids for tb in b.get("tables", [])):
        raise BadInput("id bàn không tồn tại")
    known = default_table_ids
    payloads = []
    if "hand" in b and b["hand"] is not None:
        _validate_payload("hand", b["hand"], customers, menu)
        payloads.append(b["hand"])
    for stove in stoves.values():
        state = stove.get("state", "idle")
        if state not in ("idle", "cooking", "ready"):
            raise BadInput(f"stoves.{stove['id']}.state không hợp lệ")
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in stove:
                _nonneg_int(f"stoves.{stove['id']}.{key}", stove[key])
        if state == "cooking":
            timer = stove.get("cook_ticks_left", 0)
            if isinstance(timer, bool) or not isinstance(timer, int) or timer <= 0:
                raise BadInput(f"stoves.{stove['id']}: cooking cần cook_ticks_left dương")
            if stove.get("dish") is None:
                raise BadInput(f"stoves.{stove['id']}: cooking cần dish")
        elif state == "ready" and stove.get("dish") is None:
            raise BadInput(f"stoves.{stove['id']}: ready cần dish")
        elif state == "idle" and stove.get("dish") is not None:
            raise BadInput(f"stoves.{stove['id']}: idle không được có dish")
        if stove.get("dish") is not None:
            _validate_payload(f"stoves.{stove['id']}.dish", stove["dish"], customers, menu)
            payloads.append(stove["dish"])
    reserved_totals = {}
    for c in b.get("customers", []):
        extra = set(c) - CUSTOMER_KEYS
        if extra:
            raise BadInput(f"customers.{c['id']}: trường lạ {sorted(extra)}")
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
        dish_id = c.get("dish_id")
        if not isinstance(dish_id, str) or dish_id not in menu:
            raise BadInput(f"customers.{c['id']}: dish_id phải là món trong menu")
        _nonneg_int(f"customers.{c['id']}.order_tick", c.get("order_tick", 0))
        for key in ("patience_ticks_left", "eat_ticks_left"):
            if key in c:
                _nonneg_int(f"customers.{c['id']}.{key}", c[key])
        state = c.get("state", "waiting")
        status = c.get("order_status", "reserved")
        if state not in ("waiting", "eating") or status not in ("reserved", "assigned", "unfulfillable", "served"):
            raise BadInput(f"customers.{c['id']}: state/order_status không hợp lệ")
        # v1.2: reserved là mảng id cá thể (vắng ở đơn reserved -> quan.py cấp theo order_tick rồi id bàn)
        reserved = c.get("reserved")
        if reserved is not None:
            if not isinstance(reserved, list) or not all(isinstance(x, str) and x for x in reserved)                     or len(set(reserved)) != len(reserved):
                raise BadInput(f"customers.{c['id']}.reserved phải là mảng id cá thể không trùng")
            if status != "reserved" and reserved:
                raise BadInput(f"customers.{c['id']}: đơn không reserved phải có reserved rỗng")
            if status == "reserved":
                if stock is None or any(x not in stock for x in reserved):
                    raise BadInput(f"customers.{c['id']}: reserved trỏ tới cá thể không có trong kho")
                if any(stock[x]["fresh"] < below for x in reserved):
                    raise BadInput(f"customers.{c['id']}: reserved trỏ tới cá thể đã ươn")
                kinds = {}
                for x in reserved:
                    kinds[stock[x]["kind"]] = kinds.get(stock[x]["kind"], 0) + 1
                if kinds != menu[dish_id]["recipe"]:
                    raise BadInput(f"customers.{c['id']}: reserved phải đúng công thức")
                for x in reserved:
                    if x in reserved_totals:
                        raise BadInput(f"customers.{c['id']}: cá thể {x} đã giữ cho đơn khác")
                    reserved_totals[x] = c["id"]
        if status == "unfulfillable" and state != "waiting":
            raise BadInput(f"customers.{c['id']}: unfulfillable phải đang waiting")
        if status == "served":
            if state != "eating":
                raise BadInput(f"customers.{c['id']}: served phải đang eating")
            for key in ("eat_ticks_left", "base_price", "tip"):
                if key not in c:
                    raise BadInput(f"customers.{c['id']}: eating cần {key}")
            _positive_int(f"customers.{c['id']}.base_price", c["base_price"])
            _nonneg_int(f"customers.{c['id']}.tip", c["tip"])
            if c["eat_ticks_left"] <= 0:
                raise BadInput(f"customers.{c['id']}: eating cần eat_ticks_left dương")
        elif state != "waiting":
            raise BadInput(f"customers.{c['id']}: eating cần order_status served")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
    orders = [p["order_id"] for p in payloads]
    if len(orders) != len(set(orders)):
        raise BadInput("bếp và tay giữ cùng đơn")
    for c in customers:
        status = c.get("order_status", "reserved")
        payload_count = orders.count(c["id"])
        if status == "assigned" and payload_count != 1:
            raise BadInput(f"customers.{c['id']}: assigned phải có đúng một món ở bếp hoặc tay")
        if status != "assigned" and payload_count:
            raise BadInput(f"customers.{c['id']}: trạng thái đơn không được có món ở bếp hoặc tay")


def _positive_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BadInput(f"{name} phải là số nguyên dương")


def _validate_payload(name, payload, customers, menu):
    if not isinstance(payload, dict) or set(payload) != PAYLOAD_KEYS:
        raise BadInput(f"{name} phải có order_id, dish_id, base_price")
    customer = next((c for c in customers if c.get("id") == payload["order_id"]), None)
    if customer is None or customer.get("dish_id") != payload["dish_id"]:
        raise BadInput(f"{name}: order_id/dish_id không khớp khách")
    if not isinstance(payload["dish_id"], str) or payload["dish_id"] not in menu:
        raise BadInput(f"{name}: dish_id không tồn tại")
    _positive_int(f"{name}.base_price", payload["base_price"])
    if payload["base_price"] != menu[payload["dish_id"]]["price"]:
        raise BadInput(f"{name}.base_price không khớp giá món")
