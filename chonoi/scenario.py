"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json
import math
from fractions import Fraction

from .errors import BadInput
from .day import day_plans, gather_tuning
from .freshness import parse_items
from .inventory import inventory_kinds, validate_items

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


def _ordinary_numbers(value):
    if isinstance(value, Fraction):
        return float(value)
    if isinstance(value, list):
        return [_ordinary_numbers(item) for item in value]
    return value


def _keep_fresh_precision(obj):
    # object_hook đã xử lý từng dict con, giữ phân số riêng cho trường fresh.
    return {key: value if key == "fresh" else _ordinary_numbers(value) for key, value in obj.items()}


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            options = {"parse_float": Fraction, "object_hook": _keep_fresh_precision} if "freshness" in tuning else {}
            data = json.load(f, **options)
    except (OSError, OverflowError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    allowed = {"day", "gather", "quan"} if mode == "day" else {mode}
    if not isinstance(data, dict) or set(data) - allowed:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận {sorted(allowed)}")
    if mode != "day":
        return _phase_block(data.get(mode, {}), mode, tuning)
    initial = data.get("day", {})
    _validate_day(initial, tuning)
    if isinstance(data.get("quan"), dict) and ({"stock", "reputation"} & set(data["quan"])):
        raise BadInput("day không nhận quan.stock hoặc quan.reputation")
    day_tuning = gather_tuning(tuning, initial.get("upgrades", {}))
    return {"day": initial, "gather": _phase_block(data.get("gather", {}), "gather", day_tuning),
            "quan": _phase_block(data.get("quan", {}), "quan", tuning)}


def _validate_day(state, tuning):
    if not isinstance(state, dict) or set(state) - {"money", "earned", "reputation", "upgrades", "day_plan"}:
        raise BadInput("scenario.day sai schema")
    money, earned = state.get("money", 0), state.get("earned", 0)
    if ("money" in state) != ("earned" in state) or type(money) is not int or type(earned) is not int or not 0 <= money <= earned:
        raise BadInput("day cần khai cả money và earned; 0 <= money <= earned")
    q = tuning["quan"]
    if "reputation" in state and (not _num(state["reputation"])
            or not q["reputation_min"] <= state["reputation"] <= q["reputation_max"]):
        raise BadInput("day.reputation ngoài miền tuning")
    upgrades = state.get("upgrades", {})
    offers = tuning["shop"]["upgrades"]
    if not isinstance(upgrades, dict) or any(
            key not in offers or type(level) is not int or not 0 <= level <= len(offers[key])
            for key, level in upgrades.items()):
        raise BadInput("day.upgrades có cấp không được hỗ trợ")
    day_plans(tuning, state.get("day_plan", ()))


def _phase_block(block, mode, tuning):
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    if mode == "gather" and "shop" in tuning:
        allowed = allowed | {"monsters"}
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
    for arr in ("nodes", "fish", "monsters"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        kinds = inventory_kinds(tuning)
        if "freshness" in tuning:
            b["hold"] = parse_items(h, kinds)
        elif not isinstance(h, list) or any(k not in kinds for k in h):
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
    node_kinds = {n["kind"] for n in g["nodes"]} if "shop" in tuning else NODE_KINDS
    for n in b.get("nodes", []):
        if not isinstance(n.get("kind"), str) or n["kind"] not in node_kinds:
            raise BadInput(f"nodes.{n['id']}: kind không thuộc tuning")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    fish_kinds = g["fish_yield"] if "shop" in tuning else FISH_KINDS
    for f in b.get("fish", []):
        if not isinstance(f.get("kind"), str) or f["kind"] not in fish_kinds:
            raise BadInput(f"fish.{f['id']}: kind không thuộc tuning")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f and "shop" in tuning:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    for monster in b.get("monsters", []):
        _validate_monster(monster, g)


def _validate_monster(monster, gather):
    fields = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
    species = gather["monsters"]["species"]
    kind = monster.get("kind")
    if set(monster) - fields or not isinstance(kind, str) or kind not in species:
        raise BadInput("monsters chứa trường hoặc loài không hợp lệ")
    bounds = gather["bounds"]
    _pos("monsters.pos", monster.get("pos"), bounds)
    waypoints = monster.get("waypoints")
    if not isinstance(waypoints, list) or len(waypoints) != 2:
        raise BadInput("monsters.waypoints phải có hai vị trí")
    for point in waypoints:
        _pos("monsters.waypoints", point, bounds)
    state, remaining = monster.get("state", "patrol"), monster.get("state_ticks_left", 0)
    if state not in ("patrol", "chase", "recoil"):
        raise BadInput("monsters.state không hợp lệ")
    _nonneg_int("monsters.state_ticks_left", remaining)
    if (state == "recoil") != (remaining > 0):
        raise BadInput("monsters.state_ticks_left phải dương chỉ khi recoil")
    index = monster.get("target_idx", 1)
    if type(index) is not int or index not in (0, 1):
        raise BadInput("monsters.target_idx phải là 0 hoặc 1")
    direction = monster.get("recoil_dir")
    if state == "recoil":
        _pos("monsters.recoil_dir", direction, {"x": [-1, 1], "d": [-1, 1]})
        if not math.isclose(math.hypot(*direction), 1.0, rel_tol=0, abs_tol=0.001):
            raise BadInput("monsters.recoil_dir phải là vector đơn vị")
    elif direction is not None:
        raise BadInput("monsters.recoil_dir chỉ có giá trị khi recoil")


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        kinds = inventory_kinds(tuning)
        if "freshness" in tuning:
            b["stock"] = parse_items(b["stock"], kinds)
        else:
            validate_items(b["stock"], kinds)
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
