"""Đọc game.contract.json và kiểm dải hợp lệ của tuning P1 (PRD mục 13.2, Test Contract)."""

import json
import os

from .errors import BadInput

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
    if not isinstance(fy, dict) or not {"ca_linh", "ca_loc", "ca_keo"} <= set(fy):
        raise BadInput("tuning.gather.fish_yield phải có ca_linh, ca_loc và ca_keo")
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
        if n.get("kind") not in ("bong_dien_dien", "bong_sung", "keo_neo"):
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải là bong_dien_dien, bong_sung hoặc keo_neo")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if kinds != {"bong_dien_dien", "bong_sung", "keo_neo"}:
        raise BadInput("tuning.gather.nodes phải có ít nhất một nút mỗi loại (bong_dien_dien, bong_sung, keo_neo)")
    fish = g.get("fish_initial")
    if not isinstance(fish, list) or len(fish) != 8:
        raise BadInput("tuning.gather.fish_initial phải là danh sách đúng 8 đàn (contract v1.1)")
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


def _span(name, v, lo, hi):
    if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and lo <= v[0] < v[1] <= hi):
        raise BadInput(f"{name} phải là [lo, hi] trong [{lo}, {hi}]")


def _validate_v11(t):
    """Các khối mới của contract v1.1: cá bơi/sinh, thú, kế hoạch ngày, shop."""
    g, menu = t["gather"], t["menu"]
    b = g["bounds"]
    species = sorted(g["fish_yield"])

    _between("gather.fish_speed", g.get("fish_speed"), 0.1, 10)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 10_000)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _int_between("gather.fish_max", g.get("fish_max"), 1, 100)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 20)
    if g["fish_max"] < len(g["fish_initial"]):
        raise BadInput("tuning.gather.fish_max nhỏ hơn số đàn ban đầu")

    fx = g.get("fish_x")
    if not (isinstance(fx, list) and len(fx) == 2 and all(_num(c) for c in fx)
            and b["x"][0] <= fx[0] < fx[1] <= b["x"][1]):
        raise BadInput("tuning.gather.fish_x phải là [lo, hi] trong bounds.x")

    for key in ("fish_depths", "fish_spawn_depths"):
        m = g.get(key)
        if not isinstance(m, dict) or sorted(m) != species:
            raise BadInput(f"tuning.gather.{key} phải có đủ loài {species}")
        for sp, span in m.items():
            if not (isinstance(span, list) and len(span) == 2 and all(_num(c) for c in span)
                    and span[0] > g["surface_depth"] and span[0] < span[1] <= b["d"][1]):
                raise BadInput(f"tuning.gather.{key}.{sp} phải là [lo, hi] dưới mặt nước")

    sx = g.get("fish_spawn_x")
    if not (isinstance(sx, list) and sx and all(_num(c) and b["x"][0] <= c <= b["x"][1] for c in sx)):
        raise BadInput("tuning.gather.fish_spawn_x phải là mảng x trong bounds.x")

    w = g.get("fish_weights")
    if not isinstance(w, dict) or sorted(w) != species or not all(_num(v) and v > 0 for v in w.values()):
        raise BadInput("tuning.gather.fish_weights phải có trọng số dương cho từng loài")

    m = g.get("monsters")
    if not isinstance(m, dict):
        raise BadInput("tuning.gather.monsters phải là object")
    sp = m.get("species")
    if not isinstance(sp, dict) or not sp:
        raise BadInput("tuning.gather.monsters.species phải có ít nhất một loài")
    for name, s in sp.items():
        for key, lo, hi in (("patrol_speed", 0.1, 10), ("chase_speed", 0.1, 20),
                            ("detect_radius", 0, 50), ("exit_radius", 0, 50),
                            ("hit_radius", 0.1, 10)):
            _between(f"gather.monsters.species.{name}.{key}", s.get(key), lo, hi)
        if not (isinstance(s.get("depths"), list) and len(s["depths"]) == 2
                and all(_num(c) for c in s["depths"])
                and 0 <= s["depths"][0] < s["depths"][1] <= b["d"][1]):
            raise BadInput(f"gather.monsters.species.{name}.depths không hợp lệ")
        _int_between(f"gather.monsters.species.{name}.recoil_ticks", s.get("recoil_ticks"), 0, 10_000)
        _between(f"gather.monsters.species.{name}.recoil_dist", s.get("recoil_dist"), 0, 50)
    _int_between("gather.monsters.invuln_ticks", m.get("invuln_ticks"), 0, 10_000)
    _between("gather.monsters.loss_ratio", m.get("loss_ratio"), 0, 1)

    spawns, seen = m.get("spawns"), set()
    if not isinstance(spawns, list):
        raise BadInput("gather.monsters.spawns phải là mảng")
    for s in spawns:
        if not isinstance(s, dict) or not isinstance(s.get("id"), str) or s["id"] in seen:
            raise BadInput("gather.monsters.spawns: mỗi con cần id duy nhất")
        seen.add(s["id"])
        if s.get("kind") not in sp:
            raise BadInput(f"gather.monsters.spawns.{s['id']}: kind không có trong species")
        _pos_in(f"gather.monsters.spawns.{s['id']}.pos", s.get("pos"), b, ("x", "d"))
        wps = s.get("waypoints")
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"gather.monsters.spawns.{s['id']}: cần đúng 2 waypoint")
        for wp in wps:
            _pos_in(f"gather.monsters.spawns.{s['id']}.waypoints", wp, b, ("x", "d"))
        _int_between(f"gather.monsters.spawns.{s['id']}.from_day", s.get("from_day"), 1, 5)

    if len(menu) != 6:
        raise BadInput("menu v1.1 phải đúng 6 món theo PRD")

    dp = t.get("day_plan")
    if not isinstance(dp, list) or len(dp) != 5:
        raise BadInput("tuning.day_plan phải có đúng 5 Ngày")
    for i, d in enumerate(dp, 1):
        if not isinstance(d, dict) or d.get("day") != i:
            raise BadInput(f"tuning.day_plan[{i - 1}].day phải bằng {i}")
        dishes, ing = d.get("dishes"), d.get("ingredients")
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"tuning.day_plan.{i}.dishes phải là object không rỗng")
        calc = {}
        for dish, n in dishes.items():
            if dish not in menu:
                raise BadInput(f"tuning.day_plan.{i}: món {dish} không có trong menu")
            _int_between(f"tuning.day_plan.{i}.dishes.{dish}", n, 1, 99)
            for k, v in menu[dish]["recipe"].items():
                calc[k] = calc.get(k, 0) + v * n
        if calc != ing:
            raise BadInput(f"tuning.day_plan.{i}.ingredients phải bằng tổng công thức ({calc})")

    sh = t.get("shop")
    if not isinstance(sh, dict) or not isinstance(sh.get("upgrades"), dict):
        raise BadInput("tuning.shop phải có max_ticks và upgrades")
    _int_between("shop.max_ticks", sh.get("max_ticks"), 1, 100_000)
    for key, field in (("oxygen", "oxygen_max_s"), ("hp", "hp_max")):
        arr = sh["upgrades"].get(key)
        if not isinstance(arr, list) or len(arr) != 2:
            raise BadInput(f"tuning.shop.upgrades.{key} phải có đúng 2 cấp")
        for j, up in enumerate(arr, 1):
            if up.get("level") != j:
                raise BadInput(f"tuning.shop.upgrades.{key}[{j - 1}].level phải bằng {j}")
            _int_between(f"shop.upgrades.{key}[{j - 1}].price", up.get("price"), 1, 10_000)
            if not _num(up.get(field)) or up[field] <= 0:
                raise BadInput(f"tuning.shop.upgrades.{key}[{j - 1}].{field} phải > 0")
        if arr[1]["price"] <= arr[0]["price"] or arr[1][field] <= arr[0][field]:
            raise BadInput(f"tuning.shop.upgrades.{key}: cấp 2 phải đắt và mạnh hơn cấp 1")


def validate_tuning(t):
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    _validate_gather(g)
    _validate_v11(t)
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
    # TODO(nhóm): bổ sung kiểm các khóa còn lại nếu muốn chặt hơn (bếp/bàn, uy tín, ...).
    for dish_id, d in menu.items():
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
