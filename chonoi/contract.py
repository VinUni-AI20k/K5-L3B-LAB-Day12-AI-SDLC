"""Đọc game.contract.json và kiểm tuning v1.2 (freshness, TICKET-03 §1) / v1.1 (PRD mục 13.2, Test Contract v1.0 + TICKET-02 v1.1)."""

import json
import os

from .errors import BadInput
from .inventory import FISH_KINDS, KINDS, NODE_KINDS

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")


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
    validate_tuning(c.get("tuning"))
    validate_root(c)
    return c


def _version(v):
    try:
        return tuple(int(x) for x in str(v).split(".")[:2])
    except ValueError:
        raise BadInput(f"contract_version lạ: {v!r}")


def validate_root(c):
    """v1.3 (TICKET-04): từ 1.3 phải khai báo bench_cmd và soak_cmd (chuỗi lệnh khác rỗng)."""
    if _version(c.get("contract_version")) >= (1, 3):
        for k in ("bench_cmd", "soak_cmd"):
            v = c.get(k)
            if not isinstance(v, str) or not v.strip():
                raise BadInput(f"contract v1.3 phải có {k} là chuỗi lệnh khác rỗng")


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
        raise BadInput(f"tuning.gather.fish_yield phải có đủ {list(FISH_KINDS)}")
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
    _validate_monsters(g, b)


def _range(name, v, lo, hi):
    """[a, b] với lo <= a <= b <= hi."""
    if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and lo <= v[0] <= v[1] <= hi):
        raise BadInput(f"tuning.{name} phải là [a, b] với {lo} <= a <= b <= {hi}")


def _species_map(name, m):
    if not isinstance(m, dict) or set(m) != set(FISH_KINDS):
        raise BadInput(f"tuning.gather.{name} phải có đúng các loài {list(FISH_KINDS)}")


def _validate_fish(g, b):
    """v1.1 §1.1: đàn cá bơi và sinh theo lịch."""
    _int_between("gather.fish_initial", g.get("fish_initial"), 0, 36)
    _int_between("gather.fish_max", g.get("fish_max"), 1, 36)
    if g["fish_initial"] > g["fish_max"]:
        raise BadInput("tuning.gather.fish_initial không được vượt fish_max")
    _between("gather.fish_speed", g.get("fish_speed"), 0, 10)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 100)
    _range("gather.fish_x", g.get("fish_x"), b["x"][0], b["x"][1])
    if g["fish_x"][0] >= g["fish_x"][1]:
        raise BadInput("tuning.gather.fish_x phải có độ rộng dương")
    for key in ("fish_depths", "fish_spawn_depths", "fish_weights"):
        _species_map(key, g.get(key))
    for k in FISH_KINDS:
        lo, hi = g["fish_depths"][k]
        _range(f"gather.fish_depths.{k}", g["fish_depths"][k], g["surface_depth"], b["d"][1])
        if lo == hi:
            raise BadInput(f"tuning.gather.fish_depths.{k} phải có độ rộng dương")
        ds = g["fish_spawn_depths"][k]
        if not isinstance(ds, list) or not ds or not all(_num(d) and lo <= d <= hi for d in ds):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải là danh sách độ sâu trong fish_depths")
        w = g["fish_weights"][k]
        if not _num(w) or w <= 0:
            raise BadInput(f"tuning.gather.fish_weights.{k} phải > 0")
    xs = g.get("fish_spawn_x")
    if (not isinstance(xs, list) or not xs or len(set(xs)) != len(xs)
            or not all(_num(x) and g["fish_x"][0] <= x <= g["fish_x"][1] for x in xs)):
        raise BadInput("tuning.gather.fish_spawn_x phải là danh sách x khác nhau trong fish_x")
    if g["fish_initial"] > len({(x, d) for x in xs for k in FISH_KINDS for d in g["fish_spawn_depths"][k]}):
        raise BadInput("tuning.gather.fish_initial vượt số điểm sinh hình học khác nhau")


MONSTER_SPECIES_KEYS = ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "depths",
                        "hit_radius", "recoil_ticks", "recoil_dist")


def _validate_monsters(g, b):
    """v1.1 §1.2 / §4.1: gather.monsters."""
    m = g.get("monsters")
    if not isinstance(m, dict) or not {"species", "spawns", "invuln_ticks", "loss_ratio"} <= set(m):
        raise BadInput("tuning.gather.monsters cần species, spawns, invuln_ticks, loss_ratio")
    _int_between("gather.monsters.invuln_ticks", m["invuln_ticks"], 0, 100_000)
    _between("gather.monsters.loss_ratio", m["loss_ratio"], 0, 1)
    sp = m["species"]
    if not isinstance(sp, dict) or not sp:
        raise BadInput("tuning.gather.monsters.species phải là object không rỗng")
    for kind, s in sp.items():
        if not isinstance(s, dict) or set(s) != set(MONSTER_SPECIES_KEYS):
            raise BadInput(f"tuning.gather.monsters.species.{kind} phải có đúng {list(MONSTER_SPECIES_KEYS)}")
        for key in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "hit_radius", "recoil_dist"):
            _between(f"gather.monsters.species.{kind}.{key}", s[key], 0, 100)
        _int_between(f"gather.monsters.species.{kind}.recoil_ticks", s["recoil_ticks"], 1, 100_000)
        _range(f"gather.monsters.species.{kind}.depths", s["depths"], b["d"][0], b["d"][1])
        if s["exit_radius"] < s["detect_radius"]:
            raise BadInput(f"tuning.gather.monsters.species.{kind}: exit_radius phải >= detect_radius")
    spawns = m["spawns"]
    if not isinstance(spawns, list):
        raise BadInput("tuning.gather.monsters.spawns phải là mảng")
    seen = set()
    for e in spawns:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or e["id"] in seen:
            raise BadInput("tuning.gather.monsters.spawns: mỗi con cần id duy nhất")
        seen.add(e["id"])
        if e.get("kind") not in sp:
            raise BadInput(f"tuning.gather.monsters.spawns.{e['id']}: kind phải thuộc species")
        lo, hi = sp[e["kind"]]["depths"]
        wps = e.get("waypoints")
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"tuning.gather.monsters.spawns.{e['id']}: cần đúng 2 waypoint")
        for i, pt in enumerate([e.get("pos")] + wps):
            _pos_in(f"gather.monsters.spawns.{e['id']}.{'pos' if i == 0 else 'waypoints'}", pt, b, ("x", "d"))
            if not (lo <= pt[1] <= hi):
                raise BadInput(f"tuning.gather.monsters.spawns.{e['id']}: vị trí ngoài dải độ sâu loài")
        if list(e["pos"]) != list(wps[0]):
            raise BadInput(f"tuning.gather.monsters.spawns.{e['id']}: waypoint đầu phải là vị trí xuất phát")
        _int_between(f"gather.monsters.spawns.{e['id']}.from_day", e.get("from_day"), 1, 5)


def _counts(name, m, allowed):
    if not isinstance(m, dict) or not m:
        raise BadInput(f"{name} phải là object không rỗng")
    for k, v in m.items():
        if k not in allowed:
            raise BadInput(f"{name}: khóa lạ {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
            raise BadInput(f"{name}.{k} phải là số nguyên dương")


def plan_ingredients(dishes: dict, menu: dict) -> dict:
    """Σ công thức × số suất, sắp theo id nguyên liệu (v1.1 §2, §4.1 day_plan)."""
    out = {}
    for dish_id, n in dishes.items():
        for k, q in menu[dish_id]["recipe"].items():
            out[k] = out.get(k, 0) + q * n
    return {k: out[k] for k in sorted(out)}


def _validate_menu(menu):
    for dish_id, d in menu.items():
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
        _counts(f"menu.{dish_id}.recipe", d.get("recipe"), KINDS)


def _validate_day_plan(plan, menu):
    if not isinstance(plan, list) or [p.get("day") if isinstance(p, dict) else None for p in plan] != [1, 2, 3, 4, 5]:
        raise BadInput("tuning.day_plan phải là mảng 5 object day 1..5 theo thứ tự")
    for p in plan:
        if set(p) != {"day", "dishes", "ingredients"}:
            raise BadInput(f"tuning.day_plan[{p['day']}] phải có đúng day, dishes, ingredients")
        _counts(f"day_plan[{p['day']}].dishes", p["dishes"], menu)
        _counts(f"day_plan[{p['day']}].ingredients", p["ingredients"], KINDS)
        if plan_ingredients(p["dishes"], menu) != {k: p["ingredients"][k] for k in sorted(p["ingredients"])}:
            raise BadInput(f"tuning.day_plan[{p['day']}].ingredients khác Σ công thức × số suất")


def _validate_shop(shop):
    if not isinstance(shop, dict) or not {"max_ticks", "upgrades"} <= set(shop):
        raise BadInput("tuning.shop cần max_ticks và upgrades")
    _int_between("shop.max_ticks", shop["max_ticks"], 1, 100_000)
    ups = shop["upgrades"]
    if not isinstance(ups, dict) or not {"oxygen", "hp"} <= set(ups):
        raise BadInput("tuning.shop.upgrades cần oxygen và hp")
    for uid, field in (("oxygen", "oxygen_max_s"), ("hp", "hp_max")):
        levels = ups[uid]
        if not isinstance(levels, list) or not levels:
            raise BadInput(f"tuning.shop.upgrades.{uid} phải là mảng cấp không rỗng")
        for i, lv in enumerate(levels, start=1):
            if not isinstance(lv, dict) or set(lv) != {"level", "price", field} or lv["level"] != i:
                raise BadInput(f"tuning.shop.upgrades.{uid}[{i}] phải là {{level:{i}, price, {field}}}")
            _int_between(f"shop.upgrades.{uid}[{i}].price", lv["price"], 1, 10_000_000)
        if uid == "oxygen":
            for lv in levels:
                _between(f"shop.upgrades.oxygen[{lv['level']}].oxygen_max_s", lv[field], 10, 120)
        else:
            for lv in levels:
                _int_between(f"shop.upgrades.hp[{lv['level']}].hp_max", lv[field], 1, 99)


FRESHNESS_KEYS = ("initial", "gather_decay_per_s", "quan_decay_per_s", "spoiled_below")


def _validate_freshness(f):
    """v1.2 §1: tuning.freshness {initial, gather_decay_per_s, quan_decay_per_s, spoiled_below}."""
    if not isinstance(f, dict) or set(f) != set(FRESHNESS_KEYS):
        raise BadInput(f"tuning.freshness phải có đúng {list(FRESHNESS_KEYS)}")
    _between("freshness.initial", f["initial"], 0, 100)
    _between("freshness.gather_decay_per_s", f["gather_decay_per_s"], 0, 100)
    _between("freshness.quan_decay_per_s", f["quan_decay_per_s"], 0, 100)
    _between("freshness.spoiled_below", f["spoiled_below"], 0, 100)


def validate_tuning(t):
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    _validate_freshness(t.get("freshness"))
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
    _validate_menu(menu)
    _validate_day_plan(t.get("day_plan"), menu)
    _validate_shop(t.get("shop"))
