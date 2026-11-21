"""Nạp, kiểm và trả khối scenario của mode theo Test Contract mục D."""

import json

from .errors import BadInput
from .inventory import KINDS, validate_item_list, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "monsters", "time_left_ticks", "current", "random_current", "current_direction"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks", "day_plan", "reservations", "random_reservations"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là danh sách")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id chuỗi không rỗng")
        if e["id"] in seen:
            raise BadInput(f"{name}: trùng id {e['id']!r}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict, *, inventory=None) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file scenario {path}: {e}")
    if not isinstance(data, dict):
        raise BadInput("scenario phải là object JSON")
    known_modes = {"gather", "quan", "day"}
    for k in data:
        if k not in known_modes:
            raise BadInput(f"chế độ không hỗ trợ trong scenario: {k}")
    if mode == "day":
        for phase in ("gather", "quan"):
            if phase in data:
                _validate_phase(data[phase], phase, tuning, inventory=None)
        day = data.get("day", {})
        if not isinstance(day, dict) or set(day) - {"money", "earned", "reputation"}:
            raise BadInput("khối day chỉ nhận money, earned và reputation")
        for field in ("money", "earned"):
            if field in day:
                _nonneg_int(f"day.{field}", day[field])
        if "reputation" in day:
            value = day["reputation"]
            quan = tuning["quan"]
            if not _num(value) or not quan["reputation_min"] <= value <= quan["reputation_max"]:
                raise BadInput("day.reputation ngoài miền")
        return data
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    if mode not in data:
        return {}
    block = data[mode]
    _validate_phase(block, mode, tuning, inventory)
    return block


def _validate_phase(block, mode, tuning, inventory):
    if not isinstance(block, dict):
        raise BadInput(f"khối '{mode}' phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    unknown = set(block.keys()) - allowed
    if unknown:
        raise BadInput(f"trường lạ trong khối '{mode}': {sorted(unknown)}")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning, inventory)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not isinstance(pos, list) or len(pos) != 2 or not all(_num(c) for c in pos):
        raise BadInput(f"{name} phải là [số, số]")
    for c, ax in zip(pos, axes):
        lo, hi = bounds[ax]
        if not (lo <= c <= hi):
            raise BadInput(f"{name}: {ax}={c} nằm ngoài [{lo}, {hi}]")


def _validate_gather(b, tuning):
    for arr in ("nodes", "fish", "monsters"):
        if arr in b:
            _check_ids(arr, b[arr])
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - GATHER_PLAYER_KEYS:
        raise BadInput("gather.player chỉ có các trường pos, vel, heading_deg, hp, ...")
    bounds = tuning["gather"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    if "hp" in p and (isinstance(p["hp"], bool) or not isinstance(p["hp"], int) or p["hp"] <= 0):
        raise BadInput("player.hp phải là số nguyên dương")
    for key in ("oxygen_ticks", "zero_oxy_ticks", "invuln_ticks", "catch_cd_ticks"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])

    # Hold: mảng chuỗi kind hoặc mảng cá thể {id, kind, fresh}
    hold = b.get("hold", [])
    if not isinstance(hold, list):
        raise BadInput("gather.hold phải là danh sách")
    if len(hold) > tuning["gather"]["hold_capacity"]:
        raise BadInput("gather.hold vượt sức chứa giỏ")
    for item in hold:
        if isinstance(item, dict):
            if set(item.keys()) != {"id", "kind", "fresh"}:
                raise BadInput(f"cá thể hold phải có id, kind, fresh: {item!r}")
            if item["kind"] not in KINDS:
                raise BadInput(f"nguyên liệu lạ trong hold: {item['kind']}")
            if not isinstance(item["fresh"], (int, float)) or not (0 <= item["fresh"] <= 100):
                raise BadInput(f"fresh không hợp lệ trong hold: {item['fresh']!r}")
        elif isinstance(item, str):
            if item not in KINDS:
                raise BadInput(f"nguyên liệu lạ trong hold: {item}")
        else:
            raise BadInput("phần tử trong hold không hợp lệ")

    for node in b.get("nodes", []):
        if node.get("kind") not in NODE_KINDS:
            raise BadInput(f"node.kind phải thuộc {NODE_KINDS}")
        _pos(f"nodes.{node['id']}.pos", node.get("pos"), bounds)
        if node["pos"][1] != 0:
            raise BadInput("nút hái phải nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in node:
            _nonneg_int(f"nodes.{node['id']}.regrow_ticks", node["regrow_ticks"])

    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.kind phải thuộc {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= tuning["gather"]["surface_depth"]:
            raise BadInput("đàn cá phải ở dưới nước (d > surface_depth)")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")

    for m in b.get("monsters", []):
        if m.get("kind") != "ca_sau":
            raise BadInput("monsters.kind phải là ca_sau")
        _pos(f"monsters.{m['id']}.pos", m.get("pos"), bounds)
        points = m.get("waypoints")
        if not isinstance(points, list) or len(points) != 2:
            raise BadInput("monsters.waypoints phải có hai vị trí")
        for point in points:
            _pos("monsters.waypoints", point, bounds)
        if m.get("state", "patrol") not in ("patrol", "chase", "recoil"):
            raise BadInput("monsters.state không hợp lệ")
        if m.get("target_idx", 1) not in (0, 1):
            raise BadInput("monsters.target_idx không hợp lệ")
        if m.get("state", "patrol") == "recoil" and (not isinstance(m.get("state_ticks_left"), int) or m["state_ticks_left"] <= 0):
            raise BadInput("recoil cần state_ticks_left dương")


def _validate_quan(b, tuning, inventory):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if inventory is not None and "stock" in b:
        raise BadInput("vừa có quan.stock vừa có --inventory")

    raw_stock = b.get("stock", inventory if inventory is not None else [])
    if isinstance(raw_stock, list):
        stock_items = validate_item_list(raw_stock, KINDS)
        stock_counts = {}
        for it in stock_items:
            stock_counts[it["kind"]] = stock_counts.get(it["kind"], 0) + 1
    elif isinstance(raw_stock, dict):
        stock_counts = validate_items(raw_stock, KINDS)
        stock_items = None
    else:
        raise BadInput("quan.stock phải là mảng cá thể hoặc object đếm")

    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    menu = tuning["menu"]
    table_ids = {table["id"] for table in tuning["quan"]["tables"]} | {t["id"] for t in b.get("tables", []) if "id" in t}
    stove_ids = {stove["id"] for stove in tuning["quan"]["stoves"]} | {s["id"] for s in b.get("stoves", []) if "id" in s}

    for table in b.get("tables", []):
        if table["id"] not in table_ids or set(table) - {"id", "pos"}:
            raise BadInput(f"tables.{table['id']}: bàn hoặc trường không hợp lệ")
        if "pos" in table:
            _pos(f"tables.{table['id']}.pos", table["pos"], qb, axes=("x", "z"))

    dishes = {}
    _register_dish(b.get("hand"), dishes)
    for stove in b.get("stoves", []):
        name = f"stoves.{stove['id']}"
        if stove["id"] not in stove_ids or set(stove) - {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}:
            raise BadInput(f"{name}: bếp hoặc trường không hợp lệ")
        if "pos" in stove:
            _pos(f"{name}.pos", stove["pos"], qb, axes=("x", "z"))
        state = stove.get("state", "idle")
        cook_ticks = stove.get("cook_ticks_left", 0)
        ready_ticks = stove.get("ready_ticks", 0)
        _nonneg_int(f"{name}.cook_ticks_left", cook_ticks)
        _nonneg_int(f"{name}.ready_ticks", ready_ticks)
        dish = stove.get("dish")
        if (state not in ("idle", "cooking", "ready") or (state == "idle") != (dish is None)
                or (state == "cooking") != (cook_ticks > 0) or (state != "ready" and ready_ticks)):
            raise BadInput(f"{name}: trạng thái, món và bộ đếm mâu thuẫn")
        _register_dish(dish, dishes)

    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("quan.random_customers phải là boolean")
    if "reputation" in b:
        reputation = b["reputation"]
        quan = tuning["quan"]
        if not _num(reputation) or not quan["reputation_min"] <= reputation <= quan["reputation_max"]:
            raise BadInput("quan.reputation nằm ngoài miền")
    _validate_orders(b.get("customers", []), table_ids, menu, stock_counts, stock_items, dishes, tuning)


def _register_dish(dish, dishes):
    if dish is None:
        return
    if not isinstance(dish, dict) or set(dish) - {"order_id", "dish_id", "base_price", "items"}:
        raise BadInput("món trên bếp hoặc tay phải có order_id, dish_id và base_price")
    order_id = dish.get("order_id")
    if not isinstance(order_id, str) or not order_id or order_id in dishes:
        raise BadInput("món phải có order_id hợp lệ và duy nhất trên bếp hoặc tay")
    _nonneg_int("dish.base_price", dish.get("base_price", 0))
    dishes[order_id] = dish["dish_id"]


def _validate_orders(customers, table_ids, menu, stock_counts, stock_items, dishes, tuning):
    occupied = set()
    used_item_ids = set()
    reserved_totals = {}
    item_map = {it["id"]: it for it in stock_items} if stock_items else None
    spoiled_below = tuning.get("freshness", {}).get("spoiled_below", 30)

    for customer in customers:
        order_id = customer["id"]
        table_id = customer.get("table_id")
        dish_id = customer.get("dish_id")
        if not isinstance(table_id, str) or table_id not in table_ids or table_id in occupied:
            raise BadInput(f"customers.{order_id}: bàn không hợp lệ hoặc đã có khách")
        occupied.add(table_id)
        if not isinstance(dish_id, str) or dish_id not in menu:
            raise BadInput(f"customers.{order_id}: món không có trong menu")

        counters = {"order_tick", "patience_ticks_left", "eat_ticks_left", "base_price", "tip"}
        if set(customer) - counters - {"id", "table_id", "dish_id", "state", "order_status", "reserved"}:
            raise BadInput(f"customers.{order_id}: trường không hỗ trợ")
        for key in counters & customer.keys():
            _nonneg_int(f"customers.{order_id}.{key}", customer[key])
        state = customer.get("state", "waiting")
        status = customer.get("order_status", "reserved")
        if (state not in ("waiting", "eating") or status not in ("reserved", "assigned", "unfulfillable", "served")
                or (state == "eating") != (status == "served")):
            raise BadInput(f"customers.{order_id}: trạng thái khách và đơn mâu thuẫn")
        if state == "eating" and (not customer.get("eat_ticks_left") or not {"base_price", "tip"} <= customer.keys()):
            raise BadInput(f"customers.{order_id}: khách đang ăn cần timer dương và giá, boa đã chốt")
        if status == "assigned" and dishes.pop(order_id, None) != dish_id:
            raise BadInput(f"customers.{order_id}: đơn assigned cần đúng một món khớp đơn")

        recipe = menu[dish_id]["recipe"] if status == "reserved" else {}
        if "reserved" in customer:
            res = customer["reserved"]
            if isinstance(res, list):
                # v1.2 mảng id cá thể
                if status == "reserved":
                    for it_id in res:
                        if not isinstance(it_id, str):
                            raise BadInput(f"customers.{order_id}: reserved id phải là chuỗi")
                        if it_id in used_item_ids:
                            raise BadInput(f"customers.{order_id}: cá thể {it_id} đã được giữ bởi đơn khác")
                        used_item_ids.add(it_id)
                        if item_map is not None:
                            if it_id not in item_map:
                                raise BadInput(f"customers.{order_id}: cá thể {it_id} không có trong kho")
                            if item_map[it_id]["fresh"] < spoiled_below:
                                raise BadInput(f"customers.{order_id}: cá thể {it_id} đã bị ươn")
                    # Kiểm tra công thức
                    if item_map is not None:
                        counts_for_res = {}
                        for it_id in res:
                            k = item_map[it_id]["kind"]
                            counts_for_res[k] = counts_for_res.get(k, 0) + 1
                        if counts_for_res != recipe:
                            raise BadInput(f"customers.{order_id}: phần giữ không khớp công thức món")
            elif isinstance(res, dict):
                validate_items(res)
                if res != recipe:
                    raise BadInput(f"customers.{order_id}: giữ chỗ mâu thuẫn với đơn")
                for kind, amount in res.items():
                    reserved_totals[kind] = reserved_totals.get(kind, 0) + amount
        else:
            if status == "reserved":
                for kind, amount in recipe.items():
                    reserved_totals[kind] = reserved_totals.get(kind, 0) + amount

    if dishes:
        raise BadInput("món trên bếp hoặc tay thiếu đơn assigned tương ứng")
    for kind, amount in reserved_totals.items():
        if amount > stock_counts.get(kind, 0):
            raise BadInput(f"khách giữ chỗ '{kind}' ({amount}) vượt tồn kho ({stock_counts.get(kind, 0)})")
