"""Đọc game.contract.json và kiểm dải hợp lệ của tuning (Test Contract v1.1, TICKET-02 mục 1, 4.1)."""

import json
import os

from .errors import BadInput
from .inventory import KINDS

NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
SPECIES_KEYS = {"patrol_speed", "chase_speed", "detect_radius", "exit_radius", "depths", "hit_radius",
                "recoil_ticks", "recoil_dist"}

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
    extensions = c.get("extensions", [])
    if (not isinstance(extensions, list)
            or any(not isinstance(extension, str) for extension in extensions)
            or len(set(extensions)) != len(extensions)):
        raise BadInput("extensions phải là mảng mã mở rộng dạng chuỗi, không trùng")
    validate_tuning(c.get("tuning"))
    version = c.get("contract_version")
    if version not in ("1.1", "1.2", "1.3"):
        raise BadInput(f"contract_version phải là 1.1, 1.2 hoặc 1.3, đang là {version!r}")
    if (version in ("1.2", "1.3")) != ("freshness" in c["tuning"]):
        raise BadInput("contract v1.2+ cần khối tuning.freshness (và chỉ v1.2+ có khối này)")
    if version == "1.3":  # TICKET-04: gameplay theo v1.2, thêm lệnh bench / soak ở gốc manifest
        for key in ("bench_cmd", "soak_cmd"):
            if not isinstance(c.get(key), str) or not c[key].strip():
                raise BadInput(f"contract v1.3 cần {key} (chuỗi lệnh) ở gốc manifest")
    burn_enabled = "burn" in extensions
    burn_configured = c["tuning"]["quan"].get("burn_s") is not None
    if burn_enabled != burn_configured:
        raise BadInput('extensions có "burn" khi và chỉ khi tuning.quan.burn_s được đặt')
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
    _validate_fish(g, b)
    _validate_monsters(g, b)


def _range_in(name, r, lo, hi):
    if not (isinstance(r, list) and len(r) == 2 and all(_num(c) for c in r) and lo <= r[0] <= r[1] <= hi):
        raise BadInput(f"tuning.{name} phải là [a, b] với {lo} ≤ a ≤ b ≤ {hi}")


def _species_map(name, m):
    if not isinstance(m, dict) or set(m) != set(FISH_KINDS):
        raise BadInput(f"tuning.{name} phải là map đủ {list(FISH_KINDS)}")
    return m


def _validate_fish(g, b):
    """v1.1 (TICKET-02 mục 1.1, 4.1): cá bơi / sinh theo seed."""
    _int_between("gather.fish_initial", g.get("fish_initial"), 1, 100)
    _int_between("gather.fish_max", g.get("fish_max"), g["fish_initial"], 100)
    _between("gather.fish_speed", g.get("fish_speed"), 0, 10)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 100)
    _range_in("gather.fish_x", g.get("fish_x"), *b["x"])
    lo_x, hi_x = g["fish_x"]
    xs = g.get("fish_spawn_x")
    if not isinstance(xs, list) or not xs or not all(_num(x) and lo_x <= x <= hi_x for x in xs):
        raise BadInput("tuning.gather.fish_spawn_x phải là danh sách x nằm trong fish_x")
    depths = _species_map("gather.fish_depths", g.get("fish_depths"))
    for k, r in depths.items():
        _range_in(f"gather.fish_depths.{k}", r, g["surface_depth"], b["d"][1])
    spawn_depths = _species_map("gather.fish_spawn_depths", g.get("fish_spawn_depths"))
    for k, ds in spawn_depths.items():
        lo, hi = depths[k]
        if not isinstance(ds, list) or not ds or not all(_num(d) and lo <= d <= hi for d in ds):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải là danh sách độ sâu trong fish_depths.{k}")
    weights = _species_map("gather.fish_weights", g.get("fish_weights"))
    for k, w in weights.items():
        _between(f"gather.fish_weights.{k}", w, 0, 1)
    if sum(weights.values()) <= 0:
        raise BadInput("tuning.gather.fish_weights phải có tổng dương")


def _validate_monsters(g, b):
    """v1.1 (TICKET-02 mục 1.2, 4.1): Cá Sấu (và Rắn nếu bật mở rộng snake)."""
    m = g.get("monsters")
    if not isinstance(m, dict):
        raise BadInput("tuning.gather.monsters phải là object")
    _int_between("gather.monsters.invuln_ticks", m.get("invuln_ticks"), 0, 100_000)
    _between("gather.monsters.loss_ratio", m.get("loss_ratio"), 0, 1)
    species = m.get("species")
    if not isinstance(species, dict) or "ca_sau" not in species:
        raise BadInput("tuning.gather.monsters.species phải có ca_sau")
    for k, sp in species.items():
        if not isinstance(sp, dict) or set(sp) != SPECIES_KEYS:
            raise BadInput(f"tuning.gather.monsters.species.{k} phải có đúng {sorted(SPECIES_KEYS)}")
        for key in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "hit_radius", "recoil_dist"):
            _between(f"gather.monsters.species.{k}.{key}", sp[key], 0, 100)
        _int_between(f"gather.monsters.species.{k}.recoil_ticks", sp["recoil_ticks"], 1, 100_000)
        _range_in(f"gather.monsters.species.{k}.depths", sp["depths"], 0, b["d"][1])
    spawns = m.get("spawns")
    if not isinstance(spawns, list):
        raise BadInput("tuning.gather.monsters.spawns phải là mảng")
    seen = set()
    for sp in spawns:
        if not isinstance(sp, dict) or not isinstance(sp.get("id"), str) or sp["id"] in seen:
            raise BadInput("tuning.gather.monsters.spawns: mỗi con cần id duy nhất")
        seen.add(sp["id"])
        name = f"gather.monsters.spawns.{sp['id']}"
        if sp.get("kind") not in species:
            raise BadInput(f"tuning.{name}: kind phải thuộc species")
        _pos_in(f"{name}.pos", sp.get("pos"), b, ("x", "d"))
        wps = sp.get("waypoints")
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"tuning.{name}.waypoints phải có đúng 2 điểm")
        for i, wp in enumerate(wps):
            _pos_in(f"{name}.waypoints[{i}]", wp, b, ("x", "d"))
        _int_between(f"{name}.from_day", sp.get("from_day"), 1, 5)


def recipe_sum(dishes, menu) -> dict:
    """Tổng nguyên liệu = công thức × số suất, sắp theo kind."""
    total = {}
    for dish_id, n in dishes.items():
        for k, c in menu[dish_id]["recipe"].items():
            total[k] = total.get(k, 0) + c * n
    return {k: total[k] for k in sorted(total)}


def validate_day_plan(plan, menu):
    """v1.1 mục 4.1: 5 object {day, dishes, ingredients}; ingredients = tổng công thức × số suất."""
    days = [p.get("day") if isinstance(p, dict) else None for p in plan] if isinstance(plan, list) else None
    if days != [1, 2, 3, 4, 5]:
        raise BadInput("tuning.day_plan phải là 5 object có day = 1..5 theo thứ tự")
    for p in plan:
        d, dishes = p["day"], p.get("dishes")
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"tuning.day_plan[{d}].dishes phải là map không rỗng")
        for dish_id, n in dishes.items():
            if dish_id not in menu:
                raise BadInput(f"tuning.day_plan[{d}].dishes.{dish_id}: món không có trong menu")
            _int_between(f"day_plan[{d}].dishes.{dish_id}", n, 1, 1000)
        if p.get("ingredients") != recipe_sum(dishes, menu):
            raise BadInput(f"tuning.day_plan[{d}].ingredients phải bằng tổng công thức × số suất")


def _validate_freshness(f):
    """v1.2 (TICKET-03): {initial, gather_decay_per_s, quan_decay_per_s, spoiled_below}."""
    if not isinstance(f, dict) or set(f) != {"initial", "gather_decay_per_s", "quan_decay_per_s", "spoiled_below"}:
        raise BadInput("tuning.freshness phải có đúng initial, gather_decay_per_s, quan_decay_per_s, spoiled_below")
    _between("freshness.initial", f["initial"], 0, 100)
    _between("freshness.gather_decay_per_s", f["gather_decay_per_s"], 0, 100)
    _between("freshness.quan_decay_per_s", f["quan_decay_per_s"], 0, 100)
    _between("freshness.spoiled_below", f["spoiled_below"], 0, 100)


def _validate_shop(shop):
    """v1.1 mục 4.1: {max_ticks, upgrades}; mỗi nâng cấp là mảng theo cấp 1, 2, ..."""
    if not isinstance(shop, dict):
        raise BadInput("tuning.shop phải là object")
    _int_between("shop.max_ticks", shop.get("max_ticks"), 1, 100_000)
    ups = shop.get("upgrades")
    if not isinstance(ups, dict) or not {"oxygen", "hp"} <= set(ups):
        raise BadInput("tuning.shop.upgrades phải có oxygen và hp")
    value_key = {"oxygen": "oxygen_max_s", "hp": "hp_max"}
    for name, levels in ups.items():
        lvls = [lv.get("level") if isinstance(lv, dict) else None for lv in levels] if isinstance(levels, list) else None
        if not lvls or lvls != list(range(1, len(lvls) + 1)):
            raise BadInput(f"tuning.shop.upgrades.{name} phải là mảng theo cấp 1, 2, ...")
        for lv in levels:
            _int_between(f"shop.upgrades.{name}[{lv['level']}].price", lv.get("price"), 1, 10**9)
            if name in value_key and not _num(lv.get(value_key[name])):
                raise BadInput(f"tuning.shop.upgrades.{name}[{lv['level']}] cần {value_key[name]}")


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
    if q.get("burn_s") is not None and not (_num(q["burn_s"]) and q["burn_s"] > 0):
        raise BadInput("quan.burn_s phải là null (lõi) hoặc số dương (mở rộng burn)")
    stove_ids = [e.get("id") for e in q.get("stoves", []) if isinstance(e, dict)]
    table_ids = [e.get("id") for e in q.get("tables", []) if isinstance(e, dict)]
    if stove_ids != ["B1", "B2"] or table_ids != ["T1", "T2", "T3", "T4"]:
        raise BadInput("quan: v1.1 cần bếp B1, B2 và bàn T1–T4")
    for dish_id, d in menu.items():
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
        recipe = d.get("recipe")
        if not isinstance(recipe, dict) or not recipe or any(k not in KINDS for k in recipe):
            raise BadInput(f"menu.{dish_id}.recipe chỉ gồm nguyên liệu {list(KINDS)}")
    if len(menu) != 6:
        raise BadInput("menu v1.1 phải có đúng 6 món")
    validate_day_plan(t.get("day_plan"), menu)
    if "freshness" in t:
        _validate_freshness(t["freshness"])
    _validate_shop(t.get("shop"))
