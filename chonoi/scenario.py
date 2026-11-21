"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json
import math

from .contract import FISH_KINDS, NODE_KINDS, validate_day_plan
from .errors import BadInput
from .inventory import KINDS, validate_items

KINDS_P1 = KINDS  # tên cũ; v1.1 thêm ca_keo, keo_neo
GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "monsters", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
FISH_ENTRY_KEYS = {"id", "kind", "pos", "heading_deg", "age_ticks"}
MONSTER_ENTRY_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
MONSTER_STATES = ("patrol", "chase", "recoil", "stunned")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
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
    if mode == "day":
        return _load_day(data, tuning)
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    return _check_block(mode, data.get(mode, {}), tuning)


def _check_block(mode, block, tuning):
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
    """Ticket-02 mục 4.3: khối day dựng trạng thái xuyên Ngày; gather/quan là mẫu khởi tạo mỗi Ngày."""
    if not isinstance(data, dict) or not set(data) <= {"day", "gather", "quan"}:
        raise BadInput("scenario --mode day chỉ nhận khối 'day', 'gather', 'quan'")
    quan = data.get("quan", {})
    if isinstance(quan, dict) and ({"stock", "reputation"} & set(quan)):
        raise BadInput("khi chạy day cấm quan.stock và quan.reputation (dùng gather.hold, day.reputation)")
    return {"day": _validate_day_block(data.get("day", {}), tuning),
            "gather": _check_block("gather", data.get("gather", {}), tuning),
            "quan": _check_block("quan", quan, tuning)}


def _validate_day_block(b, tuning):
    if not isinstance(b, dict):
        raise BadInput("khối day phải là object")
    extra = set(b) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    for key in ("money", "earned"):
        if key in b:
            _nonneg_int(f"day.{key}", b[key])
    if ("money" in b) != ("earned" in b) and (b.get("money", 0) or b.get("earned", 0)):
        raise BadInput("day: có tiền đầu kỳ thì khai cả money và earned")
    if not b.get("money", 0) <= b.get("earned", 0):
        raise BadInput("day: cần 0 <= money <= earned")
    q = tuning["quan"]
    if "reputation" in b and not (_num(b["reputation"]) and q["reputation_min"] <= b["reputation"] <= q["reputation_max"]):
        raise BadInput("day.reputation phải trong dải uy tín của tuning")
    ups = b.get("upgrades", {})
    if not isinstance(ups, dict):
        raise BadInput("day.upgrades phải là map id -> cấp")
    table = tuning["shop"]["upgrades"]
    for kind, lv in ups.items():
        if kind not in table:
            raise BadInput(f"day.upgrades: nâng cấp lạ {kind}")
        if isinstance(lv, bool) or not isinstance(lv, int) or not 0 <= lv <= len(table[kind]):
            raise BadInput(f"day.upgrades.{kind} phải là cấp nguyên trong [0, {len(table[kind])}]")
    if "day_plan" in b:
        validate_day_plan(b["day_plan"], tuning["menu"])
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
    if len(b.get("fish", [])) > g["fish_max"]:
        raise BadInput("fish vượt trần fish_max")
    for f in b.get("fish", []):
        if set(f) - FISH_ENTRY_KEYS:
            raise BadInput(f"fish.{f['id']}: trường lạ/chưa hỗ trợ {sorted(set(f) - FISH_ENTRY_KEYS)}")
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    _validate_monsters(b.get("monsters", []), g)


def _validate_monsters(monsters, g):
    """gather.monsters[] (Ticket-02 mục 4.3): thay danh sách mặc định của Ngày."""
    species = g["monsters"]["species"]
    for m in monsters:
        name = f"monsters.{m['id']}"
        if set(m) - MONSTER_ENTRY_KEYS:
            raise BadInput(f"{name}: trường lạ/chưa hỗ trợ {sorted(set(m) - MONSTER_ENTRY_KEYS)}")
        if m.get("kind") not in species:
            raise BadInput(f"{name}: kind phải thuộc {sorted(species)}")
        lo, hi = species[m["kind"]]["depths"]
        wps = m.get("waypoints")
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"{name}: cần đúng 2 waypoint")
        for p in [m.get("pos"), *wps]:
            _pos(name + ".pos", p, g["bounds"])
            if not lo <= p[1] <= hi:
                raise BadInput(f"{name}: nằm ngoài dải độ sâu của loài [{lo}, {hi}]")
        if m.get("target_idx", 1) not in (0, 1) or isinstance(m.get("target_idx"), bool):
            raise BadInput(f"{name}.target_idx phải là 0 hoặc 1")
        state = m.get("state", "patrol")
        if state not in MONSTER_STATES:
            raise BadInput(f"{name}.state phải thuộc {MONSTER_STATES}")
        timer = m.get("state_ticks_left", 0)
        _nonneg_int(name + ".state_ticks_left", timer)
        if (state in ("recoil", "stunned")) != (timer > 0):
            raise BadInput(f"{name}: recoil/stunned cần timer dương, trạng thái khác timer bằng 0")
        rd = m.get("recoil_dir")
        if state == "recoil":
            if not (isinstance(rd, list) and len(rd) == 2 and all(_num(c) and math.isfinite(c) for c in rd)
                    and abs(math.hypot(*rd) - 1) <= 1e-6):
                raise BadInput(f"{name}.recoil_dir phải là vector đơn vị khi recoil")
        elif rd is not None:
            raise BadInput(f"{name}.recoil_dir chỉ có khi recoil")


def _validate_quan(b, tuning):
    """Kiểm fixture quán và liên kết đơn - bếp - tay theo PRD-0 mục D.

    Nếu kho lấy từ --inventory, tổng giữ chỗ được kiểm lại khi dựng QuanSim.
    """
    q, menu = tuning["quan"], tuning["menu"]
    bounds = q["bounds"]
    for name in ("stoves", "tables", "customers"):
        if name in b:
            _check_ids(name, b[name])
    if "stock" in b:
        validate_items(b["stock"])
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b:
        v = b["reputation"]
        if not _num(v) or not math.isfinite(v) or not (q["reputation_min"] <= v <= q["reputation_max"]):
            raise BadInput("quan.reputation nằm ngoài giới hạn")
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(
            _num(c) and math.isfinite(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")

    stove_ids = {stove["id"] for stove in q["stoves"]}
    table_ids = {table["id"] for table in q["tables"]}
    stoves = {stove["id"]: dict(stove) for stove in q["stoves"]}
    for stove in b.get("stoves", []):
        if stove["id"] not in stove_ids or set(stove) - {
                "id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}:
            raise BadInput(f"stoves.{stove['id']}: id/trường không hợp lệ")
        stoves[stove["id"]].update(stove)
    for table in b.get("tables", []):
        if table["id"] not in table_ids or set(table) - {"id", "pos"}:
            raise BadInput(f"tables.{table['id']}: id/trường không hợp lệ")
        _pos(f"tables.{table['id']}.pos", table.get("pos", next(
            tb["pos"] for tb in q["tables"] if tb["id"] == table["id"])), bounds, axes=("x", "z"))

    def check_dish(name, dish):
        if not isinstance(dish, dict) or set(dish) != {"order_id", "dish_id", "base_price"}:
            raise BadInput(f"{name}: payload món phải có order_id, dish_id, base_price")
        if not isinstance(dish["order_id"], str) or not dish["order_id"]:
            raise BadInput(f"{name}.order_id không hợp lệ")
        if dish["dish_id"] not in menu:
            raise BadInput(f"{name}.dish_id không có trong menu")
        if (isinstance(dish["base_price"], bool) or not isinstance(dish["base_price"], int)
                or dish["base_price"] != menu[dish["dish_id"]]["price"]):
            raise BadInput(f"{name}.base_price không khớp giá món")
        return dish["order_id"]

    dishes = {}
    for stove in stoves.values():
        name = f"stoves.{stove['id']}"
        _pos(name + ".pos", stove.get("pos"), bounds, axes=("x", "z"))
        state = stove.get("state", "idle")
        if state not in ("idle", "cooking", "ready"):
            raise BadInput(f"{name}.state không hợp lệ")
        cook, ready = stove.get("cook_ticks_left", 0), stove.get("ready_ticks", 0)
        _nonneg_int(name + ".cook_ticks_left", cook)
        _nonneg_int(name + ".ready_ticks", ready)
        dish = stove.get("dish")
        if state == "idle":
            if dish is not None or cook != 0 or ready != 0:
                raise BadInput(f"{name}: bếp idle phải trống và timer bằng 0")
        else:
            oid = check_dish(name + ".dish", dish)
            if (state == "cooking" and (cook <= 0 or ready != 0)) or (state == "ready" and cook != 0):
                raise BadInput(f"{name}: timer không khớp trạng thái bếp")
            dishes.setdefault(oid, []).append(dish)

    if "hand" in b and b["hand"] is not None:
        oid = check_dish("hand", b["hand"])
        dishes.setdefault(oid, []).append(b["hand"])

    customers = b.get("customers", [])
    occupied = set()
    held = {}
    customer_ids = set()
    for c in customers:
        name = f"customers.{c['id']}"
        if set(c) - {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                      "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}:
            raise BadInput(f"{name}: trường lạ/chưa hỗ trợ")
        if c.get("table_id") not in table_ids or c["table_id"] in occupied:
            raise BadInput(f"{name}: bàn không tồn tại hoặc có hai khách")
        occupied.add(c["table_id"])
        customer_ids.add(c["id"])
        dish_id = c.get("dish_id")
        if dish_id not in menu:
            raise BadInput(f"{name}.dish_id không hợp lệ")
        state, status = c.get("state", "waiting"), c.get("order_status", "reserved")
        if state not in ("waiting", "eating") or status not in (
                "reserved", "assigned", "unfulfillable", "served"):
            raise BadInput(f"{name}: state/order_status không hợp lệ")
        for key, default in (("order_tick", 0), ("patience_ticks_left", int(round(q["patience_s"] * 60))),
                             ("eat_ticks_left", 0)):
            _nonneg_int(name + "." + key, c.get(key, default))
        patience = c.get("patience_ticks_left", int(round(q["patience_s"] * 60)))
        if patience > int(round(q["patience_s"] * 60)):
            raise BadInput(f"{name}: kiên nhẫn vượt tối đa")
        eating = state == "eating"
        if (eating != (status == "served") or (eating and c.get("eat_ticks_left", 0) <= 0)
                or (not eating and c.get("eat_ticks_left", 0) != 0)):
            raise BadInput(f"{name}: trạng thái khách và timer ăn mâu thuẫn")
        recipe = menu[dish_id]["recipe"]
        reserved = c.get("reserved")
        if reserved is not None and (not isinstance(reserved, dict) or any(
                not isinstance(k, str) or isinstance(v, bool) or not isinstance(v, int) or v < 0
                for k, v in reserved.items())):
            raise BadInput(f"{name}.reserved không hợp lệ")
        if status == "reserved":
            if reserved is not None and reserved != recipe:
                raise BadInput(f"{name}: giữ chỗ khác công thức")
            for k, count in recipe.items():
                held[k] = held.get(k, 0) + count
        elif reserved:
            raise BadInput(f"{name}: đơn không reserved phải có giữ chỗ rỗng")
        # Giá chốt khi bắt đầu nấu; boa chỉ chốt lúc giao món.
        base_price, tip = c.get("base_price"), c.get("tip")
        if status in ("reserved", "unfulfillable"):
            if base_price is not None or tip is not None:
                raise BadInput(f"{name}: đơn chưa nấu không có giá/boa")
        else:
            if isinstance(base_price, bool) or not isinstance(base_price, int) or base_price != menu[dish_id]["price"]:
                raise BadInput(f"{name}: base_price không khớp giá món")
            if status == "assigned" and tip is not None:
                raise BadInput(f"{name}: chưa giao món không có boa")
            if status == "served":
                maximum = math.floor(base_price * q["tip_rate"])
                if isinstance(tip, bool) or not isinstance(tip, int) or tip not in (0, maximum):
                    raise BadInput(f"{name}: boa không hợp lệ")
        linked = dishes.get(c["id"], [])
        if status == "assigned":
            if len(linked) != 1 or linked[0]["dish_id"] != dish_id or linked[0]["base_price"] != base_price:
                raise BadInput(f"{name}: đơn assigned phải có đúng một món khớp ở bếp hoặc tay")
        elif linked:
            raise BadInput(f"{name}: đơn không assigned không được còn món ở bếp/tay")

    if set(dishes) - customer_ids:
        raise BadInput("bếp/tay tham chiếu đến order_id không tồn tại")
    if "stock" in b and any(b["stock"].get(k, 0) < count for k, count in held.items()):
        raise BadInput("customers: tổng giữ chỗ vượt tồn kho")
