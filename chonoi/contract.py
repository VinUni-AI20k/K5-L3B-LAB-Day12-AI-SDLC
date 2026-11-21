"""Đọc game.contract.json và kiểm dải hợp lệ của tuning (v1.0 PRD-0 mục A; v1.1 TICKET-02 mục 1–2, 4.1)."""

import json
import os

from .errors import BadInput

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")


FISH_SPECIES = ("ca_linh", "ca_loc", "ca_keo")
NODE_SPECIES = ("bong_dien_dien", "bong_sung", "keo_neo")
MENU_IDS = ("ca_loc_nuong_trui", "goi_bong_sung", "lau_ca_linh_dien_dien", "canh_chua_ca_loc", "ca_keo_nuong",
            "lau_mam")
MONSTER_KEYS = ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "depths", "hit_radius",
                "recoil_ticks", "recoil_dist")


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
    # v1.3 (TICKET-04): thêm bench_cmd, soak_cmd ở gốc; gameplay, tuning, kho, JSONL giữ nguyên v1.2
    if c.get("contract_version") != "1.3":
        raise BadInput('contract_version phải là "1.3" (TICKET-04)')
    for key in ("bench_cmd", "soak_cmd"):
        if not isinstance(c.get(key), str) or not c[key].strip():
            raise BadInput(f"{key} phải là lệnh khác rỗng ở gốc game.contract.json (v1.3)")
    fr = (c.get("tuning") or {}).get("freshness")
    if not isinstance(fr, dict) or set(fr) != {"initial", "gather_decay_per_s", "quan_decay_per_s", "spoiled_below"}             or not all(_num(v) and v >= 0 for v in fr.values()) or not 0 < fr["spoiled_below"] <= fr["initial"] <= 100:
        raise BadInput("tuning.freshness phải có initial, gather_decay_per_s, quan_decay_per_s, spoiled_below hợp lệ")
    if not isinstance(c.get("extensions", []), list):
        raise BadInput("extensions phải là mảng mã mở rộng")
    validate_tuning(c.get("tuning"), extensions=c.get("extensions", []))
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
    if not isinstance(fy, dict) or set(fy) != set(FISH_SPECIES):
        raise BadInput(f"tuning.gather.fish_yield phải có đúng {list(FISH_SPECIES)}")
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
        if n.get("kind") not in NODE_SPECIES:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải thuộc {list(NODE_SPECIES)}")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if kinds != set(NODE_SPECIES):
        raise BadInput(f"tuning.gather.nodes phải có ít nhất một nút mỗi loại {list(NODE_SPECIES)}")
    _validate_fish(g, b)
    _validate_monsters(g.get("monsters"), b)


def _species_ranges(name, m, lo, hi):
    if not isinstance(m, dict) or set(m) != set(FISH_SPECIES):
        raise BadInput(f"tuning.{name} phải có đúng {list(FISH_SPECIES)}")
    for k, v in m.items():
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and lo <= v[0] <= v[1] <= hi):
            raise BadInput(f"tuning.{name}.{k} phải là [a, b] trong [{lo}, {hi}]")


def _validate_fish(g, b):
    """v1.1 mục 1.1: fish_initial là số đàn đầu ca; cá bơi/sinh theo dữ liệu."""
    _int_between("gather.fish_max", g.get("fish_max"), 1, 100)
    _int_between("gather.fish_initial", g.get("fish_initial"), 1, g["fish_max"])
    _between("gather.fish_speed", g.get("fish_speed"), 0, 10)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 100)
    fx = g.get("fish_x")
    if not (isinstance(fx, list) and len(fx) == 2 and all(_num(c) for c in fx)
            and b["x"][0] <= fx[0] < fx[1] <= b["x"][1]):
        raise BadInput("tuning.gather.fish_x phải là [a, b] trong bounds.x")
    _species_ranges("gather.fish_depths", g.get("fish_depths"), g["surface_depth"], b["d"][1])
    sx = g.get("fish_spawn_x")
    if not (isinstance(sx, list) and sx and all(_num(c) and fx[0] <= c <= fx[1] for c in sx)):
        raise BadInput("tuning.gather.fish_spawn_x phải là danh sách x trong fish_x")
    sd = g.get("fish_spawn_depths")
    if not isinstance(sd, dict) or set(sd) != set(FISH_SPECIES):
        raise BadInput(f"tuning.gather.fish_spawn_depths phải có đúng {list(FISH_SPECIES)}")
    for k, ds in sd.items():
        lo, hi = g["fish_depths"][k]
        if not (isinstance(ds, list) and ds and all(_num(d) and lo <= d <= hi for d in ds)):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải nằm trong fish_depths.{k}")
    w = g.get("fish_weights")
    if (not isinstance(w, dict) or set(w) != set(FISH_SPECIES) or not all(_num(v) and v >= 0 for v in w.values())
            or sum(w.values()) <= 0):
        raise BadInput("tuning.gather.fish_weights phải có trọng số không âm cho mỗi loài, tổng > 0")
    # fish_initial đàn đầu ca ở các điểm khác nhau -> cần đủ vị trí hình học
    points = {(x, d) for k in FISH_SPECIES for x in sx for d in sd[k]}
    if len(points) < g["fish_initial"]:
        raise BadInput("tuning.gather: không đủ điểm sinh khác nhau cho fish_initial")


def _validate_monsters(m, b):
    """v1.1 mục 1.2, 4.1: species{...}, spawns[], invuln_ticks, loss_ratio."""
    if not isinstance(m, dict):
        raise BadInput("tuning.gather.monsters phải là object")
    sp = m.get("species")
    if not isinstance(sp, dict) or "ca_sau" not in sp:
        raise BadInput("tuning.gather.monsters.species phải có ca_sau")
    for kind, s in sp.items():
        if not isinstance(s, dict) or set(s) != set(MONSTER_KEYS):
            raise BadInput(f"tuning.gather.monsters.species.{kind} phải có đúng {list(MONSTER_KEYS)}")
        for k in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "hit_radius", "recoil_dist"):
            if not (_num(s[k]) and s[k] > 0):
                raise BadInput(f"tuning.gather.monsters.species.{kind}.{k} phải > 0")
        _int_between(f"gather.monsters.species.{kind}.recoil_ticks", s["recoil_ticks"], 1, 100_000)
        d = s["depths"]
        if not (isinstance(d, list) and len(d) == 2 and all(_num(c) for c in d)
                and b["d"][0] <= d[0] <= d[1] <= b["d"][1]):
            raise BadInput(f"tuning.gather.monsters.species.{kind}.depths phải là [a, b] trong bounds.d")
    _int_between("gather.monsters.invuln_ticks", m.get("invuln_ticks"), 0, 100_000)
    if not (_num(m.get("loss_ratio")) and 0 <= m["loss_ratio"] <= 1):
        raise BadInput("tuning.gather.monsters.loss_ratio phải trong [0, 1]")
    spawns, seen = m.get("spawns"), set()
    if not isinstance(spawns, list):
        raise BadInput("tuning.gather.monsters.spawns phải là mảng")
    for e in spawns:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or e["id"] in seen:
            raise BadInput("tuning.gather.monsters.spawns: mỗi con cần id duy nhất")
        seen.add(e["id"])
        if e.get("kind") not in sp:
            raise BadInput(f"tuning.gather.monsters.spawns.{e['id']}: kind phải thuộc species")
        _int_between(f"gather.monsters.spawns.{e['id']}.from_day", e.get("from_day"), 1, 5)
        wps = e.get("waypoints")
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"tuning.gather.monsters.spawns.{e['id']}: cần đúng 2 waypoint")
        for wp in [e.get("pos"), *wps]:
            _pos_in(f"gather.monsters.spawns.{e['id']}.pos/waypoints", wp, b, ("x", "d"))
        if e["pos"] != wps[0]:
            raise BadInput(f"tuning.gather.monsters.spawns.{e['id']}: waypoint đầu là vị trí xuất phát")


def plan_ingredients(dishes, menu) -> dict:
    """Tổng công thức × số suất, khóa sắp theo id nguyên liệu (v1.1 mục 4.1)."""
    out = {}
    for d, n in dishes.items():
        for k, qty in menu[d]["recipe"].items():
            out[k] = out.get(k, 0) + qty * n
    return {k: out[k] for k in sorted(out)}


def _validate_day_plan(plan, menu):
    """v1.1 mục 2, 4.1: 5 Ngày {day, dishes, ingredients}."""
    if not isinstance(plan, list) or [p.get("day") if isinstance(p, dict) else None for p in plan] != [1, 2, 3, 4, 5]:
        raise BadInput("tuning.day_plan phải là mảng 5 Ngày theo thứ tự day 1..5")
    for p in plan:
        dishes = p.get("dishes")
        if (not isinstance(dishes, dict) or not dishes or any(d not in menu for d in dishes)
                or not all(isinstance(n, int) and not isinstance(n, bool) and n > 0 for n in dishes.values())):
            raise BadInput(f"tuning.day_plan.{p['day']}.dishes phải là map id món -> số nguyên dương")
        if p.get("ingredients") != plan_ingredients(dishes, menu):
            raise BadInput(f"tuning.day_plan.{p['day']}.ingredients phải bằng tổng công thức × số suất")


def _validate_shop(shop):
    """v1.1 mục 2, 4.1: {max_ticks, upgrades{oxygen[], hp[]}}, mảng theo cấp 1, 2, ..."""
    if not isinstance(shop, dict):
        raise BadInput("tuning.shop phải là object")
    _int_between("shop.max_ticks", shop.get("max_ticks"), 1, 100_000)
    ups = shop.get("upgrades")
    if not isinstance(ups, dict) or not {"oxygen", "hp"} <= set(ups):
        raise BadInput("tuning.shop.upgrades phải có oxygen và hp")
    for kind, field, lo, hi in (("oxygen", "oxygen_max_s", 10, 120), ("hp", "hp_max", 1, 99)):
        levels = ups[kind]
        if (not isinstance(levels, list)
                or [e.get("level") if isinstance(e, dict) else None for e in levels] != list(range(1, len(levels) + 1))):
            raise BadInput(f"tuning.shop.upgrades.{kind} phải là mảng theo cấp 1, 2, ...")
        for e in levels:
            if isinstance(e.get("price"), bool) or not isinstance(e.get("price"), int) or e["price"] <= 0:
                raise BadInput(f"tuning.shop.upgrades.{kind}.{e['level']}.price phải là số nguyên dương")
            _between(f"shop.upgrades.{kind}.{e['level']}.{field}", e.get(field), lo, hi)


def validate_tuning(t, extensions=()):
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
    if "burn" in extensions:
        _between("quan.burn_s", q.get("burn_s"), 0.1, 600)
    elif q.get("burn_s") is not None:
        raise BadInput("burn_s phải là null khi chưa bật mở rộng burn")
    for name, need in (("stoves", ["B1", "B2"]), ("tables", ["T1", "T2", "T3", "T4"])):
        items = q.get(name)
        if not isinstance(items, list) or [e.get("id") for e in items] != need:
            raise BadInput(f"tuning.quan.{name} phải có đúng {need} (v1.1)")
        for e in items:
            _pos_in(f"quan.{name}.{e['id']}.pos", e.get("pos"), q["bounds"], ("x", "z"))
    for dish_id, d in menu.items():
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
    if set(menu) != set(MENU_IDS):
        raise BadInput(f"menu phải có đúng 6 món {list(MENU_IDS)}")
    _validate_day_plan(t.get("day_plan"), menu)
    _validate_shop(t.get("shop"))
