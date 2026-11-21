"""Đọc game.contract.json và kiểm dải hợp lệ của tuning P1 (PRD mục 13.2, Test Contract)."""

import json
import os

from .errors import BadInput
from .freshness import PHASES, decay_units_per_tick
from .inventory import KINDS

SUPPORTED_VERSIONS = ("1.0", "1.1", "1.2")
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")

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
    if c.get("contract_version") not in SUPPORTED_VERSIONS:
        raise BadInput(f"contract_version phải thuộc {SUPPORTED_VERSIONS}, đang là {c.get('contract_version')!r}")
    validate_tuning(c.get("tuning"), c["contract_version"])
    return c


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
    if not isinstance(fy, dict) or not {"ca_linh", "ca_loc"} <= set(fy) or not set(fy) <= set(FISH_KINDS):
        raise BadInput(f"tuning.gather.fish_yield phải có ca_linh, ca_loc và chỉ gồm các loài {FISH_KINDS}")
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
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải thuộc {NODE_KINDS}")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if not {"bong_dien_dien", "bong_sung"} <= kinds:
        raise BadInput("tuning.gather.nodes phải có ít nhất một nút mỗi loại (bong_dien_dien, bong_sung)")
    fish = g.get("fish_initial")
    if isinstance(fish, int) and not isinstance(fish, bool):
        _validate_fish_dynamics(g, fy, b)  # v1.1: fish_initial là số đàn đầu ca
        _validate_monsters(g, b)
        return
    if not isinstance(fish, list) or len(fish) != 6:
        raise BadInput("tuning.gather.fish_initial phải là số (v1.1) hoặc danh sách đúng 6 đàn (v1.0)")
    seen = set()
    for f in fish:
        if not isinstance(f, dict) or not isinstance(f.get("id"), str) or f["id"] in seen:
            raise BadInput("tuning.gather.fish_initial: mỗi đàn cần id duy nhất")
        seen.add(f["id"])
        if f.get("kind") not in fy:
            raise BadInput(f"tuning.gather.fish_initial.{f['id']}: kind phải thuộc fish_yield")
        _pos_in(f"gather.fish_initial.{f['id']}.pos", f.get("pos"), b, ("x", "d"))
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"tuning.gather.fish_initial.{f['id']}: đàn cá phải ở dưới nước")


def _range_in(name, v, lo, hi):
    """v là [a, b] với lo <= a < b <= hi."""
    if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and lo <= v[0] < v[1] <= hi):
        raise BadInput(f"tuning.{name} phải là [a, b] với {lo} <= a < b <= {hi}, đang là {v!r}")


def _per_species(name, v, species):
    if not isinstance(v, dict) or set(v) != set(species):
        raise BadInput(f"tuning.{name} phải có đúng các loài {sorted(species)}")


def _validate_fish_dynamics(g, fy, b):
    """v1.1 mục 1.1 và 4.1: số đàn đầu ca, bơi, sinh thêm. fish_initial là số."""
    species = set(fy)
    _int_between("gather.fish_max", g.get("fish_max"), 1, 1000)
    _int_between("gather.fish_initial", g.get("fish_initial"), 1, g["fish_max"])
    _between("gather.fish_speed", g.get("fish_speed"), 0, 20)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 1000)
    _range_in("gather.fish_x", g.get("fish_x"), b["x"][0], b["x"][1])
    _per_species("gather.fish_depths", g.get("fish_depths"), species)
    _per_species("gather.fish_spawn_depths", g.get("fish_spawn_depths"), species)
    _per_species("gather.fish_weights", g.get("fish_weights"), species)
    for k in species:
        _range_in(f"gather.fish_depths.{k}", g["fish_depths"][k], max(b["d"][0], g["surface_depth"]), b["d"][1])
        lo, hi = g["fish_depths"][k]
        ds = g["fish_spawn_depths"][k]
        if not (isinstance(ds, list) and ds and all(_num(d) and lo <= d <= hi for d in ds)):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải là danh sách số trong fish_depths {g['fish_depths'][k]}")
        w = g["fish_weights"][k]
        if not (_num(w) and w > 0):
            raise BadInput(f"tuning.gather.fish_weights.{k} phải > 0")
    xs = g.get("fish_spawn_x")
    fx = g["fish_x"]
    if not (isinstance(xs, list) and xs and all(_num(x) and fx[0] <= x <= fx[1] for x in xs)
            and len(set(xs)) == len(xs)):
        raise BadInput("tuning.gather.fish_spawn_x phải là danh sách x không trùng, nằm trong fish_x")
    spots = len(xs) * sum(len(set(g["fish_spawn_depths"][k])) for k in species)
    if g["fish_initial"] > spots:
        raise BadInput(f"tuning.gather.fish_initial ({g['fish_initial']}) vượt số điểm sinh ({spots})")


def _validate_monsters(g, b):
    """v1.1 mục 1.2: gather.monsters (tùy chọn; không có thì không có thủy quái)."""
    m = g.get("monsters")
    if m is None:
        return
    if not isinstance(m, dict):
        raise BadInput("tuning.gather.monsters phải là object")
    species = m.get("species")
    if not isinstance(species, dict) or not species:
        raise BadInput("tuning.gather.monsters.species phải là object không rỗng")
    for kind, sp in species.items():
        if not isinstance(sp, dict):
            raise BadInput(f"tuning.gather.monsters.species.{kind} phải là object")
        for key, lo, hi in (("patrol_speed", 0, 20), ("chase_speed", 0, 20), ("detect_radius", 0, 1000),
                            ("exit_radius", 0, 1000), ("hit_radius", 0, 1000), ("recoil_dist", 0, 1000)):
            _between(f"gather.monsters.species.{kind}.{key}", sp.get(key), lo, hi)
        _int_between(f"gather.monsters.species.{kind}.recoil_ticks", sp.get("recoil_ticks"), 1, 100_000)
        _range_in(f"gather.monsters.species.{kind}.depths", sp.get("depths"), b["d"][0], b["d"][1])
        if sp["exit_radius"] < sp["detect_radius"]:
            raise BadInput(f"tuning.gather.monsters.species.{kind}: exit_radius phải >= detect_radius")
    _int_between("gather.monsters.invuln_ticks", m.get("invuln_ticks"), 0, 100_000)
    r = m.get("loss_ratio")
    if not (_num(r) and 0 < r <= 1):
        raise BadInput("tuning.gather.monsters.loss_ratio phải thuộc (0, 1]")
    spawns, seen = m.get("spawns"), set()
    if not isinstance(spawns, list):
        raise BadInput("tuning.gather.monsters.spawns phải là mảng")
    for sp in spawns:
        if not isinstance(sp, dict) or not isinstance(sp.get("id"), str) or sp["id"] in seen:
            raise BadInput("tuning.gather.monsters.spawns: mỗi quái cần id duy nhất")
        seen.add(sp["id"])
        if sp.get("kind") not in species:
            raise BadInput(f"tuning.gather.monsters.spawns.{sp['id']}: kind phải thuộc species")
        _pos_in(f"gather.monsters.spawns.{sp['id']}.pos", sp.get("pos"), b, ("x", "d"))
        wps = sp.get("waypoints")
        if not (isinstance(wps, list) and wps and wps[0] == sp["pos"]):
            raise BadInput(f"tuning.gather.monsters.spawns.{sp['id']}: waypoints không rỗng và điểm đầu là pos")
        for k, wp in enumerate(wps):
            _pos_in(f"gather.monsters.spawns.{sp['id']}.waypoints.{k}", wp, b, ("x", "d"))
        _int_between(f"gather.monsters.spawns.{sp['id']}.from_day", sp.get("from_day"), 1, 5)


def _validate_day_plan(t, menu):
    """v1.1 mục 2 và 4.1: day_plan là 5 object {day, dishes, ingredients}; ingredients = tổng công thức × suất."""
    plan = t.get("day_plan")
    if plan is None:
        return
    if not (isinstance(plan, list) and len(plan) == 5):
        raise BadInput("tuning.day_plan phải là mảng đúng 5 ngày")
    for i, d in enumerate(plan, 1):
        if not isinstance(d, dict) or d.get("day") != i or isinstance(d.get("day"), bool):
            raise BadInput(f"tuning.day_plan[{i - 1}].day phải bằng {i}")
        dishes, ing = d.get("dishes"), {}
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"tuning.day_plan[{i - 1}].dishes phải là object không rỗng")
        for dish, n in dishes.items():
            if dish not in menu or isinstance(n, bool) or not isinstance(n, int) or n <= 0:
                raise BadInput(f"tuning.day_plan[{i - 1}].dishes.{dish}: món phải có trong menu, suất là số nguyên > 0")
            for kind, q in menu[dish]["recipe"].items():
                ing[kind] = ing.get(kind, 0) + q * n
        if d.get("ingredients") != ing:
            raise BadInput(f"tuning.day_plan[{i - 1}].ingredients phải bằng tổng công thức × suất: {ing}")


def _validate_shop(t, g):
    """v1.1 mục 2 và 4.1: shop {max_ticks, upgrades{oxygen[], hp[]}}."""
    shop = t.get("shop")
    if shop is None:
        return
    if not isinstance(shop, dict):
        raise BadInput("tuning.shop phải là object")
    _int_between("shop.max_ticks", shop.get("max_ticks"), 1, 1_000_000)
    ups = shop.get("upgrades")
    if not isinstance(ups, dict) or set(ups) != {"oxygen", "hp"}:
        raise BadInput("tuning.shop.upgrades phải có đúng oxygen và hp")
    for name, key, base in (("oxygen", "oxygen_max_s", g["oxygen_max_s"]), ("hp", "hp_max", g["hp_max"])):
        levels, prev = ups[name], base
        if not isinstance(levels, list) or not levels:
            raise BadInput(f"tuning.shop.upgrades.{name} phải là mảng không rỗng")
        for k, lv in enumerate(levels, 1):
            if not isinstance(lv, dict) or lv.get("level") != k:
                raise BadInput(f"tuning.shop.upgrades.{name}: cấp phải đánh số 1, 2, ... theo thứ tự")
            _int_between(f"shop.upgrades.{name}.{k}.price", lv.get("price"), 1, 10_000_000)
            if not (_num(lv.get(key)) and lv[key] > prev):
                raise BadInput(f"tuning.shop.upgrades.{name}.{k}.{key} phải lớn hơn cấp trước ({prev})")
            prev = lv[key]


def _validate_freshness(t, required):
    """v1.2 (Ticket-03): độ tươi bằng số nguyên đơn vị; hao mỗi tick phải ra số nguyên."""
    f = t.get("freshness")
    if f is None:
        if required:
            raise BadInput("contract 1.2 phải có tuning.freshness")
        return
    if not isinstance(f, dict) or set(f) != {"fresh_max", "spoil_below", "units_per_point", "decay_per_s"}:
        raise BadInput("tuning.freshness phải có đúng fresh_max, spoil_below, units_per_point, decay_per_s")
    _int_between("freshness.fresh_max", f["fresh_max"], 1, 1000)
    _int_between("freshness.spoil_below", f["spoil_below"], 1, f["fresh_max"])
    _int_between("freshness.units_per_point", f["units_per_point"], 1, 100_000)
    d = f["decay_per_s"]
    if not isinstance(d, dict) or set(d) != set(PHASES):
        raise BadInput("tuning.freshness.decay_per_s phải có đúng gather và quan")
    for phase in PHASES:
        _between(f"freshness.decay_per_s.{phase}", d[phase], 0, 100)
        decay_units_per_tick(f, t["tick_hz"], phase)  # phải ra số nguyên đơn vị mỗi tick


def validate_tuning(t, version=None):
    """`version` "1.2" bắt buộc có khối freshness; các bản khác cho phép có sẵn để A và B đọc số trước khi bật v1.2."""
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
    _validate_quan_layout(q)
    for dish_id, d in menu.items():
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
        recipe = d.get("recipe")
        if not isinstance(recipe, dict) or not recipe:
            raise BadInput(f"menu.{dish_id}: recipe phải là object không rỗng")
        for k, n in recipe.items():
            if k not in KINDS or isinstance(n, bool) or not isinstance(n, int) or n <= 0:
                raise BadInput(f"menu.{dish_id}.recipe: {k!r} phải là nguyên liệu hợp lệ với số nguyên > 0")
    _validate_day_plan(t, menu)
    _validate_shop(t, g)
    _validate_freshness(t, required=version == "1.2")
    m = (t.get("score") or {}).get("reputation_multiplier")
    if not _num(m) or m < 0:
        raise BadInput("tuning.score.reputation_multiplier phải là số không âm")


def _validate_quan_layout(q):
    """Bếp, bàn, vị trí đầu, uy tín, giới hạn mang (P1-08)."""
    b = q["bounds"]
    _pos_in("quan.start_pos", q.get("start_pos"), b, ("x", "z"))
    _int_between("quan.carry_limit", q.get("carry_limit"), 1, 10_000)
    for arr in ("stoves", "tables"):
        items = q.get(arr)
        if not isinstance(items, list) or not items:
            raise BadInput(f"tuning.quan.{arr} phải là mảng không rỗng")
        seen = set()
        for e in items:
            if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"] or e["id"] in seen:
                raise BadInput(f"tuning.quan.{arr}: mỗi phần tử cần id duy nhất")
            seen.add(e["id"])
            _pos_in(f"quan.{arr}.{e['id']}.pos", e.get("pos"), b, ("x", "z"))
    lo, init, hi = q.get("reputation_min"), q.get("reputation_initial"), q.get("reputation_max")
    if not (_num(lo) and _num(init) and _num(hi) and lo <= init <= hi):
        raise BadInput("tuning.quan: cần reputation_min <= reputation_initial <= reputation_max (đều là số)")
