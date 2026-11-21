"""Đọc game.contract.json và kiểm dải hợp lệ của tuning (Test Contract v1.1).

v1.0: PRD-0 mục A (docs/prd/phase-1.md). v1.1: Ticket-02 mục 1, 2, 4.1 (docs/prd/phase-2.md).
Lát 0 (Phase 2) đổi: fish_initial là SỐ đàn (không còn danh sách), thêm fish_* (cá bơi/sinh), 3 loài cá,
3 loại cây (thêm keo_neo), gather.monsters (Cá Sấu), 2 bếp/4 bàn, 6 món, day_plan, shop.
"""

import json
import math
import os

from .errors import BadInput
from .inventory import KINDS

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")

NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
MONSTER_KEYS = ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "depths", "hit_radius",
                "recoil_ticks", "recoil_dist")
UPGRADE_FIELDS = {"oxygen": "oxygen_max_s", "hp": "hp_max"}


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _between(name, v, lo, hi):
    if not _num(v) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải trong [{lo}, {hi}], đang là {v!r}")


def load_contract(path=None) -> dict:
    """Đọc manifest. `CHONOI_CONTRACT` (biến môi trường, chỉ dùng khi phát triển) trỏ tới manifest khác,
    ví dụ bản v1.2 trong lúc chuyển đổi; bộ chấm và CI không đặt biến này."""
    path = path or os.environ.get("CHONOI_CONTRACT") or DEFAULT_PATH
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được {path}: {e}")
    version = c.get("contract_version")
    if version not in SUPPORTED_VERSIONS:
        raise BadInput(f"contract_version phải thuộc {list(SUPPORTED_VERSIONS)}, đang là {version!r}")
    t = c.get("tuning")
    if isinstance(t, dict) and (version == "1.2") != ("freshness" in t):
        raise BadInput("contract_version 1.2 cần tuning.freshness; bản trước 1.2 không có khóa này")
    validate_tuning(t, extensions=validate_extensions(c.get("extensions", [])))
    return c


SUPPORTED_VERSIONS = ("1.0", "1.1", "1.2")


def _validate_freshness(f):
    """Ticket-03: freshness {initial, gather_decay_per_s, quan_decay_per_s, spoiled_below} = 100, 0.5, 0.25, 30."""
    if not isinstance(f, dict) or set(f) != {"initial", "gather_decay_per_s", "quan_decay_per_s", "spoiled_below"}:
        raise BadInput("tuning.freshness phải có đúng initial, gather_decay_per_s, quan_decay_per_s, spoiled_below")
    _between("freshness.initial", f["initial"], 0, 100)
    _between("freshness.spoiled_below", f["spoiled_below"], 0, f["initial"])
    for key in ("gather_decay_per_s", "quan_decay_per_s"):
        _between(f"freshness.{key}", f[key], 0, 100)
        # Hao mỗi tick phải là số nguyên đơn vị 1/240 điểm (chonoi/items.py) để so ngưỡng chính xác.
        per_tick_units = f[key] / 60 * 240
        if abs(per_tick_units - round(per_tick_units)) > 1e-9:
            raise BadInput(f"tuning.freshness.{key}: hao mỗi tick phải là bội của 1/240 điểm")


# Mã mở rộng Ticket-02 mục 3 / 4.1. Khai ở gốc manifest: "extensions": [...].
EXTENSION_CODES = ("weapon", "net", "snake", "burn", "vendor", "ca_ho")


def validate_extensions(ext) -> tuple:
    if not isinstance(ext, list) or any(e not in EXTENSION_CODES for e in ext) or len(set(ext)) != len(ext):
        raise BadInput(f"extensions phải là danh sách mã không trùng trong {list(EXTENSION_CODES)}")
    return tuple(ext)


def _int_between(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải là số nguyên trong [{lo}, {hi}], đang là {v!r}")


def _pos_in(name, pos, bounds, keys):
    if (not isinstance(pos, list) or len(pos) != 2 or not all(_num(c) for c in pos)):
        raise BadInput(f"tuning.{name} phải là [số, số]")
    for c, k in zip(pos, keys):
        lo, hi = bounds[k]
        if not (lo <= c <= hi):
            raise BadInput(f"tuning.{name} nằm ngoài vùng {k} ∈ [{lo}, {hi}]")


def _range(name, r, lo, hi):
    """[a, b] với lo <= a <= b <= hi."""
    if not (isinstance(r, list) and len(r) == 2 and all(_num(c) for c in r) and lo <= r[0] <= r[1] <= hi):
        raise BadInput(f"tuning.{name} phải là [a, b] trong [{lo}, {hi}]")


def _bounds(name, b, keys):
    if not isinstance(b, dict) or set(b) != set(keys):
        raise BadInput(f"tuning.{name}.bounds phải có đúng khóa {list(keys)}")
    for k in keys:
        v = b[k]
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and v[0] == 0 and v[1] > 0):
            raise BadInput(f"tuning.{name}.bounds.{k} phải là [0, số dương]")


def _species_map(name, m):
    if not isinstance(m, dict) or set(m) != set(FISH_KINDS):
        raise BadInput(f"tuning.{name} phải có đúng 3 loài {list(FISH_KINDS)}")


def _validate_gather(g):
    """Dải hợp lệ v1.0 (PRD-0 mục A) + khóa v1.1 (Ticket-02 mục 1.1, 1.2, 4.1)."""
    _between("gather.duration_s", g.get("duration_s"), 60, 600)
    _bounds("gather", g.get("bounds"), ("x", "d"))
    b = g["bounds"]
    _between("gather.dock_radius", g.get("dock_radius"), 0.5, 5)
    _between("gather.interact_radius", g.get("interact_radius"), 0.5, 5)
    _between("gather.catch_radius", g.get("catch_radius"), 0.5, 5)
    _between("gather.swim_speed", g.get("swim_speed"), 1, 10)
    _between("gather.catch_cooldown_s", g.get("catch_cooldown_s"), 0, 10)
    _between("gather.oxygen_max_s", g.get("oxygen_max_s"), 10, 120)
    _int_between("gather.ramp_max_ticks", g.get("ramp_max_ticks"), 0, 6)
    _int_between("gather.hold_capacity", g.get("hold_capacity"), 4, 30)
    _int_between("gather.hp_max", g.get("hp_max"), 1, 99)
    _int_between("gather.oxygen_refill_per_tick", g.get("oxygen_refill_per_tick"), 1, 10_000)
    _int_between("gather.choke_interval_ticks", g.get("choke_interval_ticks"), 1, 10_000)
    _int_between("gather.node_yield", g.get("node_yield"), 1, 12)
    _between("gather.regrow_s", g.get("regrow_s"), 0.1, 600)
    _between("gather.surface_depth", g.get("surface_depth"), 0, 5)
    _pos_in("gather.dock_pos", g.get("dock_pos"), b, ("x", "d"))
    _pos_in("gather.start_pos", g.get("start_pos"), b, ("x", "d"))
    if not _num(g.get("start_heading_deg")):
        raise BadInput("tuning.gather.start_heading_deg phải là số")
    fy = g.get("fish_yield")
    _species_map("gather.fish_yield", fy)
    for k, v in fy.items():
        _int_between(f"gather.fish_yield.{k}", v, 1, g["hold_capacity"])
    nodes = g.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise BadInput("tuning.gather.nodes phải là mảng không rỗng")
    seen, kinds = set(), set()
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or n["id"] in seen:
            raise BadInput("tuning.gather.nodes: mỗi nút cần id duy nhất")
        seen.add(n["id"])
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải thuộc {list(NODE_KINDS)}")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if kinds != set(NODE_KINDS):
        raise BadInput(f"tuning.gather.nodes phải có ít nhất một nút mỗi loại {list(NODE_KINDS)}")
    _validate_fish(g, b)
    _validate_monsters(g.get("monsters"), b)


def _validate_fish(g, b):
    """Cá bơi / sinh (Ticket-02 mục 1.1). fish_initial là số đàn đầu ca."""
    _int_between("gather.fish_max", g.get("fish_max"), 1, 100)
    _int_between("gather.fish_initial", g.get("fish_initial"), 0, g["fish_max"])
    _between("gather.fish_speed", g.get("fish_speed"), 0, 10)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 100)
    _range("gather.fish_x", g.get("fish_x"), *b["x"])
    depths = g.get("fish_depths")
    _species_map("gather.fish_depths", depths)
    for k, r in depths.items():
        _range(f"gather.fish_depths.{k}", r, g["surface_depth"], b["d"][1])
        if r[0] <= g["surface_depth"]:
            raise BadInput(f"tuning.gather.fish_depths.{k}: cá phải ở dưới nước")
    sx = g.get("fish_spawn_x")
    if not (isinstance(sx, list) and sx and all(_num(x) and g["fish_x"][0] <= x <= g["fish_x"][1] for x in sx)
            and len(set(sx)) == len(sx)):
        raise BadInput("tuning.gather.fish_spawn_x phải là danh sách x khác nhau trong fish_x")
    sd = g.get("fish_spawn_depths")
    _species_map("gather.fish_spawn_depths", sd)
    points = set()
    for k, ds in sd.items():
        lo, hi = depths[k]
        if not (isinstance(ds, list) and ds and all(_num(d) and lo <= d <= hi for d in ds)):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải là danh sách d trong fish_depths.{k}")
        points |= {(x, d) for x in sx for d in ds}
    if len(points) < g["fish_initial"]:
        raise BadInput("tuning.gather: không đủ điểm sinh khác nhau cho fish_initial")
    w = g.get("fish_weights")
    _species_map("gather.fish_weights", w)
    if not all(_num(v) and v >= 0 for v in w.values()) or sum(w.values()) <= 0:
        raise BadInput("tuning.gather.fish_weights phải không âm, tổng dương")


def _validate_monsters(m, b):
    """Cá Sấu (Ticket-02 mục 1.2, 4.1): species, spawns, invuln_ticks, loss_ratio."""
    if not isinstance(m, dict) or not {"species", "spawns", "invuln_ticks", "loss_ratio"} <= set(m):
        raise BadInput("tuning.gather.monsters cần species, spawns, invuln_ticks, loss_ratio")
    _int_between("gather.monsters.invuln_ticks", m["invuln_ticks"], 0, 100_000)
    _between("gather.monsters.loss_ratio", m["loss_ratio"], 0, 1)
    sp = m["species"]
    if not isinstance(sp, dict) or not sp:
        raise BadInput("tuning.gather.monsters.species phải là object không rỗng")
    for kind, s in sp.items():
        name = f"gather.monsters.species.{kind}"
        if not isinstance(s, dict) or set(s) != set(MONSTER_KEYS):
            raise BadInput(f"tuning.{name} phải có đúng khóa {list(MONSTER_KEYS)}")
        for key in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "hit_radius", "recoil_dist"):
            _between(f"{name}.{key}", s[key], 0, 100)
        if s["exit_radius"] < s["detect_radius"]:
            raise BadInput(f"tuning.{name}: exit_radius phải >= detect_radius")
        _int_between(f"{name}.recoil_ticks", s["recoil_ticks"], 1, 100_000)
        _range(f"{name}.depths", s["depths"], *b["d"])
    spawns = m["spawns"]
    if not isinstance(spawns, list):
        raise BadInput("tuning.gather.monsters.spawns phải là mảng")
    seen = set()
    for e in spawns:
        if not isinstance(e, dict) or set(e) != {"id", "kind", "pos", "waypoints", "from_day"}:
            raise BadInput("tuning.gather.monsters.spawns: mỗi con có id, kind, pos, waypoints, from_day")
        if not isinstance(e["id"], str) or not e["id"] or e["id"] in seen:
            raise BadInput("tuning.gather.monsters.spawns: id phải duy nhất")
        seen.add(e["id"])
        if e["kind"] not in sp:
            raise BadInput(f"tuning.gather.monsters.spawns.{e['id']}: kind không có trong species")
        _int_between(f"gather.monsters.spawns.{e['id']}.from_day", e["from_day"], 1, 5)
        lo, hi = sp[e["kind"]]["depths"]
        wps = e["waypoints"]
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"tuning.gather.monsters.spawns.{e['id']}: cần đúng 2 waypoint")
        for i, p in enumerate([e["pos"], *wps]):
            _pos_in(f"gather.monsters.spawns.{e['id']}.pos[{i}]", p, b, ("x", "d"))
            if not lo <= p[1] <= hi:
                raise BadInput(f"tuning.gather.monsters.spawns.{e['id']}: nằm ngoài dải độ sâu của loài")
        if e["pos"] != wps[0]:
            raise BadInput(f"tuning.gather.monsters.spawns.{e['id']}: waypoint đầu là vị trí xuất phát")


def _validate_menu(menu):
    if not isinstance(menu, dict) or not menu:
        raise BadInput("tuning.menu phải là object không rỗng")
    for dish_id, d in menu.items():
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
        r = d.get("recipe")
        if (not isinstance(r, dict) or not r or set(r) - set(KINDS)
                or any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in r.values())):
            raise BadInput(f"menu.{dish_id}.recipe phải là map nguyên liệu → số nguyên dương")


def plan_ingredients(dishes, menu) -> dict:
    """Tổng công thức × số suất (Ticket-02 mục 4.1), sắp theo id nguyên liệu."""
    total = {}
    for dish_id, n in dishes.items():
        for k, c in menu[dish_id]["recipe"].items():
            total[k] = total.get(k, 0) + c * n
    return {k: total[k] for k in sorted(total)}


def validate_dishes(name, dishes, menu):
    if (not isinstance(dishes, dict) or not dishes or set(dishes) - set(menu)
            or any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in dishes.values())):
        raise BadInput(f"{name}.dishes phải là map id món → số nguyên dương")


def _validate_day_plan(plan, menu):
    if not isinstance(plan, list) or len(plan) != 5:
        raise BadInput("tuning.day_plan phải là mảng 5 Ngày")
    for i, e in enumerate(plan, 1):
        if not isinstance(e, dict) or set(e) != {"day", "dishes", "ingredients"} or e["day"] != i:
            raise BadInput(f"tuning.day_plan[{i - 1}] phải là {{day: {i}, dishes, ingredients}}")
        validate_dishes(f"tuning.day_plan[{i - 1}]", e["dishes"], menu)
        if e["ingredients"] != plan_ingredients(e["dishes"], menu):
            raise BadInput(f"tuning.day_plan[{i - 1}].ingredients khác tổng công thức × số suất")


def _validate_shop(shop, g):
    if not isinstance(shop, dict) or set(shop) != {"max_ticks", "upgrades"}:
        raise BadInput("tuning.shop phải là {max_ticks, upgrades}")
    _int_between("shop.max_ticks", shop["max_ticks"], 1, 100_000)
    ups = shop["upgrades"]
    if not isinstance(ups, dict) or not set(UPGRADE_FIELDS) <= set(ups):
        raise BadInput("tuning.shop.upgrades cần oxygen và hp")
    for up, field in UPGRADE_FIELDS.items():
        levels = ups[up]
        if not isinstance(levels, list) or not levels:
            raise BadInput(f"tuning.shop.upgrades.{up} phải là mảng theo cấp")
        for i, lv in enumerate(levels, 1):
            name = f"shop.upgrades.{up}[{i - 1}]"
            if not isinstance(lv, dict) or set(lv) != {"level", "price", field} or lv["level"] != i:
                raise BadInput(f"tuning.{name} phải là {{level: {i}, price, {field}}}")
            _int_between(f"{name}.price", lv["price"], 1, 10 ** 9)
        if up == "oxygen":
            for lv in levels:
                _between(f"shop.upgrades.oxygen.{lv['level']}.oxygen_max_s", lv["oxygen_max_s"], 10, 120)
        else:
            for lv in levels:
                _int_between(f"shop.upgrades.hp.{lv['level']}.hp_max", lv["hp_max"], 1, 99)


def validate_tuning(t, extensions=()):
    """`extensions`: mã mở rộng đang bật (gốc manifest). Hiện chỉ ảnh hưởng `quan.burn_s`."""
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    _validate_gather(g)
    # Quán: dải hợp lệ (PRD-0 mục A), 2 bếp / 4 bàn ở v1.1 lấy theo dữ liệu
    _between("quan.duration_s", q.get("duration_s"), 60, 600)
    _bounds("quan", q.get("bounds"), ("x", "z"))
    _between("quan.patience_s", q.get("patience_s"), 20, 180)
    _between("quan.walk_speed", q.get("walk_speed"), 1, 10)
    _between("quan.interact_radius", q.get("interact_radius"), 0.5, 5)
    _int_between("quan.ramp_max_ticks", q.get("ramp_max_ticks", 6), 0, 6)
    _between("quan.eat_s", q.get("eat_s"), 0.1, 600)
    _between("quan.customer_interval_s", q.get("customer_interval_s"), 0.1, 600)
    _int_between("quan.first_customer_tick", q.get("first_customer_tick"), 1, int(q["duration_s"] * 60) - 1)
    if not (_num(q.get("tip_rate")) and q["tip_rate"] > 0 and _num(q.get("left_reputation_delta"))
            and q["left_reputation_delta"] < 0):
        raise BadInput("tip_rate phải > 0 và left_reputation_delta phải < 0")
    ratio = q.get("tip_min_patience_ratio")
    if not (_num(ratio) and 0 < ratio <= 1):
        raise BadInput("quan.tip_min_patience_ratio phải thuộc (0, 1]")
    if not (_num(q.get("tip_reputation")) and q["tip_reputation"] > 0):
        raise BadInput("quan.tip_reputation phải > 0")
    # Ticket-02 mục 3/4.1: lõi `burn_s: null`; bật mở rộng burn thì `quan.burn_s` hữu hạn (> 0), chuẩn là 20 s.
    if "burn" in extensions:
        if not (_num(q.get("burn_s")) and q["burn_s"] > 0):
            raise BadInput("extensions có burn thì quan.burn_s phải là số hữu hạn > 0")
    elif q.get("burn_s") is not None:
        raise BadInput("burn_s phải là null khi chưa bật mở rộng burn (extensions)")
    for name in ("stoves", "tables"):
        arr = q.get(name)
        if not isinstance(arr, list) or not arr or len({e.get("id") for e in arr}) != len(arr):
            raise BadInput(f"tuning.quan.{name} phải là mảng không rỗng, id duy nhất")
        for e in arr:
            _pos_in(f"quan.{name}.{e['id']}.pos", e.get("pos"), q["bounds"], ("x", "z"))
    _validate_menu(menu)
    # v1.1: kế hoạch Ngày và Shop (Ticket-02 mục 2). Thiếu khối = contract v1.0 cũ (chỉ gather/quan).
    if "day_plan" in t:
        _validate_day_plan(t["day_plan"], menu)
    if "shop" in t:
        _validate_shop(t["shop"], g)
    if "freshness" in t:  # v1.2 (Ticket-03): kho cá thể
        _validate_freshness(t["freshness"])


def _pos_int_map(name, m, allowed=None):
    if not isinstance(m, dict) or not m:
        raise BadInput(f"{name} phải là map khác rỗng id -> số nguyên dương")
    for k, v in m.items():
        if allowed is not None and k not in allowed:
            raise BadInput(f"{name}: id lạ {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
            raise BadInput(f"{name}.{k} phải là số nguyên dương")


def validate_day_plan(plan, menu, expect_days=None):
    """Mảng {day, dishes, ingredients?}; ingredients (nếu khai) phải khớp tổng công thức × số suất."""
    if not isinstance(plan, list) or not plan:
        raise BadInput("day_plan phải là mảng khác rỗng")
    days = []
    for entry in plan:
        if not isinstance(entry, dict) or not set(entry) <= {"day", "dishes", "ingredients"}:
            raise BadInput("day_plan: mỗi mục chỉ có day, dishes, ingredients")
        day = entry.get("day")
        _int_between("day_plan.day", day, 1, 5)
        _pos_int_map(f"day_plan[{day}].dishes", entry.get("dishes"), menu)
        if "ingredients" in entry:
            _pos_int_map(f"day_plan[{day}].ingredients", entry["ingredients"])
            if entry["ingredients"] != plan_ingredients(entry["dishes"], menu):
                raise BadInput(f"day_plan[{day}].ingredients khác tổng công thức × số suất")
        days.append(day)
    if len(set(days)) != len(days):
        raise BadInput("day_plan: trùng số Ngày")
    if expect_days is not None and sorted(days) != list(range(1, expect_days + 1)):
        raise BadInput(f"tuning.day_plan phải có đủ Ngày 1..{expect_days}")
