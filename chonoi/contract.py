"""Đọc game.contract.json và kiểm dải hợp lệ của tuning (Test Contract v1.1: PRD-0 mục A + Ticket-02 mục 1, 2, 4.1)."""

import json
import os

from .errors import BadInput
from .inventory import KINDS

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")

CONTRACT_VERSION = "1.1"
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
DISH_IDS = ("ca_loc_nuong_trui", "goi_bong_sung", "lau_ca_linh_dien_dien", "canh_chua_ca_loc", "ca_keo_nuong", "lau_mam")
STOVE_IDS = ("B1", "B2")
TABLE_IDS = ("T1", "T2", "T3", "T4")
SPECIES_KEYS = ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "depths", "hit_radius",
                "recoil_ticks", "recoil_dist")
UPGRADE_FIELDS = {"oxygen": "oxygen_max_s", "hp": "hp_max"}
# Mã mở rộng hợp lệ ở gốc manifest (Ticket-02 mục 3, 4.1)
EXTENSION_CODES = ("weapon", "net", "snake", "burn", "vendor", "ca_ho")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _between(name, v, lo, hi):
    if not _num(v) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải trong [{lo}, {hi}], đang là {v!r}")


def load_contract(path=DEFAULT_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được {path}: {e}")
    if c.get("contract_version") != CONTRACT_VERSION:
        raise BadInput(f"contract_version phải là {CONTRACT_VERSION!r}")
    ext = c.get("extensions", [])
    if not isinstance(ext, list) or any(e not in EXTENSION_CODES for e in ext) or len(set(ext)) != len(ext):
        raise BadInput(f"extensions phải là mảng mã không trùng trong {list(EXTENSION_CODES)}")
    validate_tuning(c.get("tuning"))
    return c


def extensions(contract) -> set:
    """Tập mã mở rộng đang bật (khai ở gốc manifest)."""
    return set(contract.get("extensions", []))


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


def _bounds(name, b, keys):
    if not isinstance(b, dict) or set(b) != set(keys):
        raise BadInput(f"tuning.{name}.bounds phải có đúng khóa {list(keys)}")
    for k in keys:
        v = b[k]
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and v[0] == 0 and v[1] > 0):
            raise BadInput(f"tuning.{name}.bounds.{k} phải là [0, số dương]")


def _validate_gather(g):
    """Dải hợp lệ P1 theo PRD mục 13.2."""
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
    if not isinstance(fy, dict) or set(fy) != set(FISH_KINDS):
        raise BadInput(f"tuning.gather.fish_yield phải có đúng {list(FISH_KINDS)}")
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
    _validate_fish_v11(g)
    _validate_monsters(g)


def _species_map(name, m, check):
    if not isinstance(m, dict) or set(m) != set(FISH_KINDS):
        raise BadInput(f"tuning.gather.{name} phải có đúng {list(FISH_KINDS)}")
    for k, v in m.items():
        check(f"gather.{name}.{k}", v)


def _range2(name, v, lo, hi):
    if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and lo <= v[0] <= v[1] <= hi):
        raise BadInput(f"tuning.{name} phải là [a, b] với {lo} <= a <= b <= {hi}")


def _validate_fish_v11(g):
    """Ticket-02 mục 1.1 và 4.1: đàn cá bơi và sinh."""
    b = g["bounds"]
    _int_between("gather.fish_initial", g.get("fish_initial"), 1, 30)
    _between("gather.fish_speed", g.get("fish_speed"), 0.1, 10)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_max", g.get("fish_max"), g["fish_initial"], 100)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 10)
    _range2("gather.fish_x", g.get("fish_x"), b["x"][0], b["x"][1])
    _species_map("fish_depths", g.get("fish_depths"),
                 lambda n, v: _range2(n, v, g["surface_depth"], b["d"][1]))
    xs = g.get("fish_spawn_x")
    if not (isinstance(xs, list) and xs and all(_num(x) and g["fish_x"][0] <= x <= g["fish_x"][1] for x in xs)):
        raise BadInput("tuning.gather.fish_spawn_x phải là danh sách x trong fish_x")

    def depth_list(name, v):
        kind = name.rsplit(".", 1)[1]
        lo, hi = g["fish_depths"][kind]
        if not (isinstance(v, list) and v and all(_num(d) and lo <= d <= hi for d in v)):
            raise BadInput(f"tuning.{name} phải là danh sách độ sâu trong dải bơi của loài")

    _species_map("fish_spawn_depths", g.get("fish_spawn_depths"), depth_list)
    _species_map("fish_weights", g.get("fish_weights"),
                 lambda n, v: _between(n, v, 0.000001, 1))


def _validate_monsters(g):
    """Ticket-02 mục 1.2 và 4.1: gather.monsters {species, spawns, invuln_ticks, loss_ratio}."""
    b = g["bounds"]
    m = g.get("monsters")
    if not isinstance(m, dict):
        raise BadInput("tuning.gather.monsters phải là object")
    species = m.get("species")
    if not isinstance(species, dict) or not species:
        raise BadInput("tuning.gather.monsters.species phải là object không rỗng")
    for kind, sp in species.items():
        n = f"gather.monsters.species.{kind}"
        if not isinstance(sp, dict) or set(sp) != set(SPECIES_KEYS):
            raise BadInput(f"tuning.{n} phải có đúng các khóa {list(SPECIES_KEYS)}")
        for key in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "hit_radius", "recoil_dist"):
            _between(f"{n}.{key}", sp[key], 0.01, 100)
        _int_between(f"{n}.recoil_ticks", sp["recoil_ticks"], 1, 100_000)
        _range2(f"{n}.depths", sp["depths"], b["d"][0], b["d"][1])
    spawns = m.get("spawns")
    if not isinstance(spawns, list):
        raise BadInput("tuning.gather.monsters.spawns phải là mảng")
    seen = set()
    for s in spawns:
        if not isinstance(s, dict) or not isinstance(s.get("id"), str) or s["id"] in seen:
            raise BadInput("tuning.gather.monsters.spawns: mỗi con cần id duy nhất")
        seen.add(s["id"])
        n = f"gather.monsters.spawns.{s['id']}"
        if s.get("kind") not in species:
            raise BadInput(f"tuning.{n}.kind phải thuộc species")
        _pos_in(f"{n}.pos", s.get("pos"), b, ("x", "d"))
        wps = s.get("waypoints")
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"tuning.{n}.waypoints phải có đúng 2 điểm")
        for i, wp in enumerate(wps):
            _pos_in(f"{n}.waypoints[{i}]", wp, b, ("x", "d"))
        _int_between(f"{n}.from_day", s.get("from_day"), 1, 5)
    _int_between("gather.monsters.invuln_ticks", m.get("invuln_ticks"), 0, 100_000)
    _between("gather.monsters.loss_ratio", m.get("loss_ratio"), 0, 1)


def _validate_day_plan(t):
    """Ticket-02 mục 2 và 4.1: day_plan là 5 object {day, dishes, ingredients}, ingredients = tổng công thức × suất."""
    plan, menu = t.get("day_plan"), t["menu"]
    if not isinstance(plan, list) or [p.get("day") if isinstance(p, dict) else None for p in plan] != [1, 2, 3, 4, 5]:
        raise BadInput("tuning.day_plan phải là 5 object có day 1..5 theo thứ tự")
    for p in plan:
        n = f"day_plan[{p['day']}]"
        if set(p) != {"day", "dishes", "ingredients"}:
            raise BadInput(f"tuning.{n} chỉ có day, dishes, ingredients")
        dishes = p["dishes"]
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"tuning.{n}.dishes phải là map id món -> số suất")
        for dish_id, count in dishes.items():
            if dish_id not in menu:
                raise BadInput(f"tuning.{n}.dishes: món lạ {dish_id}")
            _int_between(f"{n}.dishes.{dish_id}", count, 1, 100)
        if p["ingredients"] != plan_ingredients(menu, dishes):
            raise BadInput(f"tuning.{n}.ingredients phải bằng tổng công thức nhân số suất")


def plan_ingredients(menu, dishes) -> dict:
    """Tổng nguyên liệu cần cho kế hoạch: công thức × số suất."""
    total = {}
    for dish_id, count in dishes.items():
        for k, n in menu[dish_id]["recipe"].items():
            total[k] = total.get(k, 0) + n * count
    return total


def _validate_shop(t):
    """Ticket-02 mục 2 và 4.1: shop {max_ticks, upgrades.oxygen[], upgrades.hp[]}."""
    shop = t.get("shop")
    if not isinstance(shop, dict) or not isinstance(shop.get("upgrades"), dict):
        raise BadInput("tuning.shop phải có max_ticks và upgrades")
    _int_between("shop.max_ticks", shop.get("max_ticks"), 1, 100_000)
    ups = shop["upgrades"]
    for kind, field in UPGRADE_FIELDS.items():
        levels = ups.get(kind)
        if not isinstance(levels, list) or [lv.get("level") if isinstance(lv, dict) else None for lv in levels] \
                != list(range(1, len(levels) + 1)):
            raise BadInput(f"tuning.shop.upgrades.{kind} phải là mảng theo cấp 1, 2, ...")
        for lv in levels:
            if set(lv) != {"level", "price", field}:
                raise BadInput(f"tuning.shop.upgrades.{kind}: mỗi cấp có đúng level, price, {field}")
            _int_between(f"shop.upgrades.{kind}[{lv['level']}].price", lv["price"], 1, 1_000_000)
            if not _num(lv[field]) or lv[field] <= 0:
                raise BadInput(f"tuning.shop.upgrades.{kind}[{lv['level']}].{field} phải > 0")


def upgrade_value(tuning, kind, level, base):
    """Giá trị đang áp dụng của nâng cấp `kind` ở `level` (0 = chưa mua -> `base`)."""
    if not level:
        return base
    field = UPGRADE_FIELDS[kind]
    return tuning["shop"]["upgrades"][kind][level - 1][field]


def validate_tuning(t):
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    _validate_gather(g)
    # Quán: dải hợp lệ P1 (PRD mục 13.2)
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
    if q.get("burn_s") is not None:
        raise BadInput("burn_s phải là null ở Phase 1")
    qb = q["bounds"]
    for arr, need in (("stoves", STOVE_IDS), ("tables", TABLE_IDS)):
        items = q.get(arr)
        if not isinstance(items, list) or [e.get("id") if isinstance(e, dict) else None for e in items] != list(need):
            raise BadInput(f"tuning.quan.{arr} phải có đúng id {list(need)} theo thứ tự")
        for e in items:
            _pos_in(f"quan.{arr}.{e['id']}.pos", e.get("pos"), qb, ("x", "z"))
    for dish_id, d in menu.items():
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
    if set(menu) != set(DISH_IDS):
        raise BadInput(f"tuning.menu phải có đúng 6 món {list(DISH_IDS)}")
    for dish_id, d in menu.items():
        recipe = d.get("recipe")
        if not isinstance(recipe, dict) or not recipe or any(k not in KINDS for k in recipe) \
                or any(isinstance(n, bool) or not isinstance(n, int) or n < 1 for n in recipe.values()):
            raise BadInput(f"menu.{dish_id}.recipe phải là map nguyên liệu hợp lệ -> số nguyên dương")
    _validate_day_plan(t)
    _validate_shop(t)
