"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

v1.1 (TV6, T242): khối `day` (mode day), `gather.monsters[]`, `gather.fish[].age_ticks`; cấm `quan.stock`,
`quan.reputation` khi chạy day; `0 ≤ money ≤ earned`; `day.day_plan` tính lại ingredients và so.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json
import math

from .errors import BadInput
from .inventory import KINDS_P1, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}  # monsters: v1.1
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung")
FISH_KINDS = ("ca_linh", "ca_loc")
QUAN_PLAYER_KEYS = {"pos", "vel"}
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}  # v1.1
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
MONSTER_STATES = ("patrol", "chase", "recoil")
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
    """gather/quan: trả dict của khối đó. day (v1.1): trả {"day":…, "gather":…, "quan":…} (khối vắng = {})."""
    if path is None:
        return {"day": {}, "gather": {}, "quan": {}} if mode == "day" else {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if mode == "day":
        return _load_day(data, tuning)
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    return _validate_block(mode, data.get(mode, {}), tuning)


def _validate_block(mode, block, tuning):
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


def _load_day(data, tuning):
    """Scenario `day` (đề §4.3): khối day dựng trạng thái xuyên Ngày; gather/quan là mẫu khởi tạo mỗi Ngày."""
    if not isinstance(data, dict) or not set(data) <= {"day", "gather", "quan"}:
        raise BadInput("scenario day chỉ được có khối 'day', 'gather', 'quan'")
    q = data.get("quan", {})
    if isinstance(q, dict):
        bad = sorted(set(q) & {"stock", "reputation"})
        if bad:
            raise BadInput(f"chạy day cấm quan.{', quan.'.join(bad)} (dùng gather.hold / day.reputation)")
    out = {"day": _validate_day(data.get("day", {}), tuning),
           "gather": _validate_block("gather", data.get("gather", {}), tuning),
           "quan": _validate_block("quan", q, tuning)}
    return out


def _validate_day(b, tuning):
    if not isinstance(b, dict):
        raise BadInput("khối day phải là object")
    extra = set(b) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    for k in ("money", "earned"):
        if k in b:
            _nonneg_int(f"day.{k}", b[k])
    money, earned = b.get("money", 0), b.get("earned", 0)
    if money > earned:
        raise BadInput("day: cần 0 ≤ money ≤ earned (khai cả hai khi có tiền đầu kỳ)")
    if "reputation" in b:
        q = tuning["quan"]
        lo, hi = q.get("reputation_min", 0), q.get("reputation_max", 5)
        if not (_num(b["reputation"]) and lo <= b["reputation"] <= hi):
            raise BadInput(f"day.reputation phải trong [{lo}, {hi}]")
    shop = tuning.get("shop")
    if "upgrades" in b:
        u = b["upgrades"]
        if not isinstance(u, dict):
            raise BadInput("day.upgrades phải là object {id: cấp}")
        if not isinstance(shop, dict) or not isinstance(shop.get("upgrades"), dict):
            raise BadInput("contract chưa có khóa tuning.shop (chờ TV1)")
        for uid, lv in u.items():
            if uid not in shop["upgrades"]:
                raise BadInput(f"day.upgrades: nâng cấp lạ {uid}")
            _nonneg_int(f"day.upgrades.{uid}", lv)
            if lv > len(shop["upgrades"][uid]):
                raise BadInput(f"day.upgrades.{uid} vượt cấp tối đa")
    if "day_plan" in b:
        from .sim.day import plan_ingredients
        plans = b["day_plan"]
        if not isinstance(plans, list):
            raise BadInput("day.day_plan phải là mảng {day, dishes[, ingredients]}")
        seen = set()
        for i, p in enumerate(plans):
            if not isinstance(p, dict) or set(p) - {"day", "dishes", "ingredients"}:
                raise BadInput(f"day.day_plan[{i}] chỉ có day, dishes, ingredients")
            d = p.get("day")
            if isinstance(d, bool) or not isinstance(d, int) or not (1 <= d <= 5) or d in seen:
                raise BadInput(f"day.day_plan[{i}].day phải là số nguyên 1–5, không trùng")
            seen.add(d)
            dishes = p.get("dishes")
            if not isinstance(dishes, dict) or not dishes or any(
                    isinstance(n, bool) or not isinstance(n, int) or n <= 0 for n in dishes.values()):
                raise BadInput(f"day.day_plan[{i}].dishes phải là map món → số nguyên dương")
            ing = plan_ingredients(tuning["menu"], dishes)
            if "ingredients" in p and p["ingredients"] != ing:
                raise BadInput(f"day.day_plan[{i}].ingredients khác Σ công thức × suất ({ing})")
    return b


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
    for m in b.get("monsters", []):
        _validate_monster(m, g)
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


def _validate_monster(m, g):
    """gather.monsters[] (đề §4.3): thay bố trí mặc định; loài phải có trong tuning.gather.monsters.species."""
    mid = m["id"]
    extra = set(m) - MONSTER_KEYS
    if extra:
        raise BadInput(f"monsters.{mid}: trường lạ {sorted(extra)}")
    species = (g.get("monsters") or {}).get("species")
    if not isinstance(species, dict):
        raise BadInput("contract chưa có khóa tuning.gather.monsters (chờ TV1)")
    if m.get("kind") not in species:
        raise BadInput(f"monsters.{mid}: kind phải là một trong {sorted(species)}")
    _pos(f"monsters.{mid}.pos", m.get("pos"), g["bounds"])
    wps = m.get("waypoints")
    if not (isinstance(wps, list) and len(wps) == 2):
        raise BadInput(f"monsters.{mid}.waypoints phải có đúng 2 điểm")
    for j, wp in enumerate(wps):
        _pos(f"monsters.{mid}.waypoints[{j}]", wp, g["bounds"])
    if m.get("target_idx", 1) not in (0, 1) or isinstance(m.get("target_idx"), bool):
        raise BadInput(f"monsters.{mid}.target_idx phải là 0 hoặc 1")
    state = m.get("state", "patrol")
    if state not in MONSTER_STATES:
        raise BadInput(f"monsters.{mid}.state phải là một trong {MONSTER_STATES}")
    if "state_ticks_left" in m:
        _nonneg_int(f"monsters.{mid}.state_ticks_left", m["state_ticks_left"])
    rd = m.get("recoil_dir")
    if state == "recoil":
        if m.get("state_ticks_left", 0) <= 0:
            raise BadInput(f"monsters.{mid}: recoil cần state_ticks_left > 0")
        if not (isinstance(rd, list) and len(rd) == 2 and all(_num(c) for c in rd)
                and abs(math.hypot(rd[0], rd[1]) - 1) <= 1e-6):
            raise BadInput(f"monsters.{mid}.recoil_dir phải là vector đơn vị khi recoil")
    elif rd is not None:
        raise BadInput(f"monsters.{mid}.recoil_dir chỉ khác null khi recoil")


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
