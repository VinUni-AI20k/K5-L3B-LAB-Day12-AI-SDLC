"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .inventory import validate_item_list, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "monsters", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks", "reservations", "random_reservations"}
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


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
    allowed_top = {"gather", "quan", "day"} if mode == "day" else {mode}
    if not isinstance(data, dict) or not set(data) <= allowed_top:
        raise BadInput("scenario có khối không hợp lệ cho mode đã chọn")
    if mode != "day" and set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    if mode == "day":
        for phase in ("gather", "quan"):
            child = data.get(phase, {})
            if not isinstance(child, dict):
                raise BadInput(f"khối {phase} phải là object")
            if phase == "quan" and ("stock" in child or "reputation" in child):
                raise BadInput("không khai quan.stock hoặc quan.reputation khi chạy day")
            _validate_block(child, phase, tuning)
        day = data.get("day", {})
        if not isinstance(day, dict) or set(day) - DAY_KEYS:
            raise BadInput("day có trường lạ hoặc không phải object")
        money, earned = day.get("money", 0), day.get("earned", 0)
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in (money, earned)):
            raise BadInput("day.money và day.earned phải là số nguyên không âm")
        if money > earned:
            raise BadInput("day.money không được lớn hơn day.earned")
        if "reputation" in day:
            rep, q = day["reputation"], tuning["quan"]
            if not _num(rep) or not q["reputation_min"] <= rep <= q["reputation_max"]:
                raise BadInput("day.reputation nằm ngoài giới hạn")
        upgrades = day.get("upgrades", {})
        if not isinstance(upgrades, dict):
            raise BadInput("day.upgrades phải là object")
        for name, level in upgrades.items():
            options = tuning["shop"]["upgrades"].get(name)
            if options is None or isinstance(level, bool) or not isinstance(level, int) or not any(u["level"] == level for u in options):
                raise BadInput(f"day.upgrades.{name} không hợp lệ")
        plan = day.get("day_plan")
        if plan is not None:
            if isinstance(plan, dict):
                try:
                    plan = [{"day": int(k), **v} for k, v in plan.items()]
                except (TypeError, ValueError):
                    raise BadInput("day.day_plan có khóa ngày sai")
            if not isinstance(plan, list):
                raise BadInput("day.day_plan phải là object hoặc mảng")
            seen_days = set()
            for item in plan:
                if not isinstance(item, dict) or set(item) - {"day", "dishes", "ingredients"}:
                    raise BadInput("mỗi mục day_plan chỉ có day, dishes, ingredients")
                d = item.get("day")
                if isinstance(d, bool) or not isinstance(d, int) or not 1 <= d <= 5 or d in seen_days:
                    raise BadInput("day_plan.day phải duy nhất trong [1, 5]")
                seen_days.add(d)
                dishes = item.get("dishes")
                if not isinstance(dishes, dict) or any(k not in tuning["menu"] or isinstance(v, bool) or not isinstance(v, int) or v <= 0 for k, v in dishes.items()):
                    raise BadInput("day_plan.dishes không hợp lệ")
                totals = {}
                for dish, count in dishes.items():
                    for kind, amount in tuning["menu"][dish]["recipe"].items():
                        totals[kind] = totals.get(kind, 0) + amount * count
                if item.get("ingredients", totals) != totals:
                    raise BadInput("day_plan.ingredients không khớp tổng công thức")
        return data
    block = data.get(mode, {})
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


def _validate_block(block, mode, tuning):
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    duration = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not 1 <= t <= duration:
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {duration}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)


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
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        # v1.2: mảng cá thể {id, kind, fresh}; đổi fresh sang Fraction để so ngưỡng chính xác.
        try:
            h = b["hold"] = validate_item_list(b["hold"])
        except BadInput as e:
            raise BadInput(f"gather.hold: {e}")
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
    # v1.1: quái (Cá Sấu) — PRD mục D: {id,kind,pos,waypoints,target_idx,state,
    # state_ticks_left,recoil_dir}; recoil/stunned cần timer dương.
    if "monsters" in b:
        species = g.get("monsters", {}).get("species", {})
        for m in b["monsters"]:
            if m.get("kind") not in species:
                raise BadInput(f"monsters.{m.get('id')}: kind phải thuộc species của tuning.monsters")
            _pos(f"monsters.{m['id']}.pos", m.get("pos"), bounds)
            wps = m.get("waypoints")
            if not (isinstance(wps, list) and len(wps) == 2):
                raise BadInput(f"monsters.{m['id']}.waypoints phải là 2 điểm")
            for i, wp in enumerate(wps):
                _pos(f"monsters.{m['id']}.waypoints[{i}]", wp, bounds)
            if "target_idx" in m and m["target_idx"] not in (0, 1):
                raise BadInput(f"monsters.{m['id']}.target_idx phải là 0 hoặc 1")
            state = m.get("state", "patrol")
            if state not in ("patrol", "chase", "recoil", "stunned"):
                raise BadInput(f"monsters.{m['id']}.state không hợp lệ: {state!r}")
            if state in ("recoil", "stunned"):
                tl = m.get("state_ticks_left")
                if isinstance(tl, bool) or not isinstance(tl, int) or tl <= 0:
                    raise BadInput(f"monsters.{m['id']}: state {state} cần state_ticks_left dương")
            rd = m.get("recoil_dir")
            if rd is not None and not (isinstance(rd, list) and len(rd) == 2
                                       and all(_num(c) for c in rd)):
                raise BadInput(f"monsters.{m['id']}.recoil_dir phải là vector [x, d] hoặc null")


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers", "reservations"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        if isinstance(b["stock"], list):
            b["stock"] = validate_item_list(b["stock"])
        else:
            validate_items(b["stock"])
    if "random_reservations" in b and not isinstance(b["random_reservations"], bool):
        raise BadInput("random_reservations phải là boolean")
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
    stock_by_id = {item["id"]: item for item in b.get("stock", [])} if isinstance(b.get("stock"), list) else {}
    reserved_ids = set()
    for customer in b.get("customers", []):
        if "reserved" not in customer or isinstance(customer["reserved"], dict):
            continue  # Historical count-based fixtures remain readable during fixture migration.
        if "stock" not in b:
            continue  # --inventory is checked against these IDs when QuanSim is constructed.
        reserved = customer["reserved"]
        if (not isinstance(reserved, list) or
                any(not isinstance(iid, str) or iid not in stock_by_id for iid in reserved)):
            raise BadInput(f"customers.{customer['id']}.reserved phải trỏ tới id có trong quan.stock")
        if len(reserved) != len(set(reserved)) or reserved_ids.intersection(reserved):
            raise BadInput("customers.reserved không được dùng chung id cá thể")
        for iid in reserved:
            if stock_by_id[iid]["fresh"] < tuning["freshness"]["spoiled_below"]:
                raise BadInput(f"customers.{customer['id']}.reserved không được giữ hàng đã ươn")
        reserved_ids.update(reserved)
    reservation_ids = set()
    reservation_tables = set()
    reservation_cfg = tuning["quan"]["reservations"]
    for reservation in b.get("reservations", []):
        rid = reservation["id"]
        if set(reservation) != {"id", "table_id", "dish_id", "arrival_tick"}:
            raise BadInput(f"reservations.{rid} chỉ có id, table_id, dish_id, arrival_tick")
        if rid in reservation_ids:
            raise BadInput(f"reservations: id trùng {rid}")
        reservation_ids.add(rid)
        if reservation.get("table_id") not in known or reservation["table_id"] in reservation_tables:
            raise BadInput("reservations.table_id phải là bàn có thật và khác các đơn khác")
        reservation_tables.add(reservation["table_id"])
        if reservation.get("dish_id") not in tuning["menu"]:
            raise BadInput(f"reservations.{rid}.dish_id không thuộc menu")
        tick = reservation.get("arrival_tick")
        duration = int(round(tuning["quan"]["duration_s"] * 60))
        if isinstance(tick, bool) or not isinstance(tick, int) or not 0 < tick < duration:
            raise BadInput(f"reservations.{rid}.arrival_tick phải thuộc (0, {duration})")
    for customer in b.get("customers", []):
        reservation_id = customer.get("reservation_id")
        if reservation_id is not None and reservation_id not in reservation_ids:
            raise BadInput(f"customers.{customer['id']}.reservation_id không có trong quan.reservations")
    if len(b.get("reservations", [])) > reservation_cfg["count"]:
        raise BadInput(f"reservations tối đa {reservation_cfg['count']} đơn")
