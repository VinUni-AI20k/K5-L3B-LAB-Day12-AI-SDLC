"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json
import math

from .errors import BadInput
from .inventory import KINDS_P1, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "monsters", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
DAY_KEYS = {"day", "max_days", "money", "earned", "reputation", "upgrades", "stock", "gather", "quan", "shop", "time_left_ticks", "intro_ticks", "daily_menu"}


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
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan", "day"}:
        raise BadInput("scenario chỉ được có khối 'gather', 'quan' hoặc 'day'")
    if mode != "day" and set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    if mode == "day":
        for key in ("day", "gather", "quan"):
            if key in data and not isinstance(data[key], dict):
                raise BadInput(f"scenario.{key} phải là object")
        settings = data.get("day", {})
        # Chấp nhận fixture cũ đặt gather/quan trong day để không làm mất dữ liệu test cũ.
        gather = data.get("gather", settings.get("gather", {}))
        quan = data.get("quan", settings.get("quan", {}))
        if not isinstance(gather, dict) or set(gather) - GATHER_KEYS:
            raise BadInput("scenario.gather không hợp lệ")
        if not isinstance(quan, dict) or set(quan) - QUAN_KEYS or "stock" in quan or "reputation" in quan:
            raise BadInput("scenario.quan không hợp lệ cho day")
        for key, fixture in (("gather", gather), ("quan", quan)):
            if "time_left_ticks" in fixture:
                ticks = fixture["time_left_ticks"]
                limit = int(round(tuning[key]["duration_s"] * 60))
                if isinstance(ticks, bool) or not isinstance(ticks, int) or not 1 <= ticks <= limit:
                    raise BadInput(f"scenario.{key}.time_left_ticks không hợp lệ")
        _validate_gather(gather, tuning)
        _validate_quan(quan, tuning)
        return {"day": settings, "gather": gather, "quan": quan}
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS if mode == "quan" else DAY_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    if mode in tuning and "duration_s" in tuning[mode]:
        dur = int(round(tuning[mode]["duration_s"] * 60))
        if "time_left_ticks" in block:
            t = block["time_left_ticks"]
            if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
                raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    elif mode == "quan":
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
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    for m in b.get("monsters", []):
        allowed = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
        if set(m) - allowed or m.get("kind") not in g["monsters"]["species"]:
            raise BadInput(f"monsters.{m['id']}: trường hoặc loài không hợp lệ")
        spec = g["monsters"]["species"][m["kind"]]
        _pos(f"monsters.{m['id']}.pos", m.get("pos"), bounds)
        waypoints = m.get("waypoints")
        if not isinstance(waypoints, list) or len(waypoints) != 2:
            raise BadInput(f"monsters.{m['id']}: cần hai waypoint")
        for point in waypoints:
            _pos(f"monsters.{m['id']}.waypoints", point, bounds)
        if any(not spec["depths"][0] <= point[1] <= spec["depths"][1]
               for point in [m["pos"], *waypoints]):
            raise BadInput(f"monsters.{m['id']}: ngoài vùng độ sâu")
        target = m.get("target_idx", 1)
        if isinstance(target, bool) or not isinstance(target, int) or target not in (0, 1):
            raise BadInput(f"monsters.{m['id']}: target_idx phải là 0 hoặc 1")
        state = m.get("state", "patrol")
        if state not in ("patrol", "chase", "recoil"):
            raise BadInput(f"monsters.{m['id']}: state không hợp lệ")
        ticks = m.get("state_ticks_left", 0)
        _nonneg_int(f"monsters.{m['id']}.state_ticks_left", ticks)
        direction = m.get("recoil_dir")
        if state == "recoil":
            if (ticks == 0 or not isinstance(direction, list) or len(direction) != 2
                    or not all(_num(v) and math.isfinite(v) for v in direction)
                    or not math.isclose(math.hypot(*direction), 1.0, abs_tol=1e-6)):
                raise BadInput(f"monsters.{m['id']}: recoil cần timer và hướng đơn vị")
        elif ticks != 0 or direction is not None:
            raise BadInput(f"monsters.{m['id']}: timer/hướng chỉ dùng khi recoil")


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
