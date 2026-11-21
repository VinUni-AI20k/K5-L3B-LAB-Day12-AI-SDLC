"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
v1.2 (khi tuning có `freshness`, xem docs/clarify.md #3-#5):
- `gather.hold`, `quan.stock` là mảng cá thể {id, kind, fresh}, id duy nhất, fresh trong [0, 100].
- `customers[].reserved` là mảng id; mỗi id giữ cho tối đa một đơn, phải có trong kho, còn tươi
  và đủ đúng công thức. Đơn chờ nấu chưa khai được cấp theo (order_tick, table_id), tươi nhất trước,
  hòa thì id nhỏ hơn (`prepare_quan_reservations`).
TODO(nhóm): các mâu thuẫn mức luật khác (đơn assigned phải có đúng một món, khách eating thiếu
giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

from collections import Counter
import json
import math

from .errors import BadInput
from .ids import id_key
from .inventory import KINDS_V11, validate_fresh_items, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "monsters", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {
    "pos", "vel", "heading_deg", "hp", "oxygen_ticks",
    "zero_oxy_ticks", "catch_cd_ticks", "invuln_ticks",
}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
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
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan", "day"}:
        raise BadInput("scenario chỉ được có khối 'gather', 'quan' hoặc 'day'")
    if mode == "day":
        out = {}
        for k in ("day", "gather", "quan"):
            if k not in data:
                continue
            blk = data[k]
            if not isinstance(blk, dict):
                raise BadInput(f"khối {k} phải là object")
            if k == "day":
                _validate_day(blk, tuning)
            elif k == "gather":
                _validate_block_keys(blk, GATHER_KEYS, "gather")
                _validate_time_left(blk, tuning, "gather")
                _validate_gather(blk, tuning)
            elif k == "quan":
                if "stock" in blk or "reputation" in blk:
                    raise BadInput("cấm quan.stock và quan.reputation khi chạy --mode day")
                _validate_block_keys(blk, QUAN_KEYS, "quan")
                _validate_time_left(blk, tuning, "quan")
                _validate_quan(blk, tuning)
            out[k] = blk
        return out
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    _validate_block_keys(block, allowed, mode)
    _validate_time_left(block, tuning, mode)
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _validate_block_keys(block, allowed, mode):
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")


def _validate_time_left(block, tuning, mode):
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")


def _validate_day(b, tuning):
    extra = set(b) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    if ("money" in b) != ("earned" in b):
        raise BadInput("day: cần khai cả money và earned khi có tiền đầu kỳ")
    if "money" in b:
        m, e = b["money"], b["earned"]
        _nonneg_int("day.money", m)
        _nonneg_int("day.earned", e)
        if m > e:
            raise BadInput("day.money không được vượt day.earned")
    if "reputation" in b:
        r = b["reputation"]
        q = tuning["quan"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput("day.reputation nằm ngoài miền hợp lệ")
    if "upgrades" in b:
        up = b["upgrades"]
        if not isinstance(up, dict):
            raise BadInput("day.upgrades phải là object")
        shop_ups = tuning.get("shop", {}).get("upgrades", {})
        for k, lvl in up.items():
            if k not in shop_ups:
                raise BadInput(f"day.upgrades: nâng cấp không hợp lệ {k!r}")
            max_lvl = max((u["level"] for u in shop_ups[k]), default=0)
            if isinstance(lvl, bool) or not isinstance(lvl, int) or not (0 <= lvl <= max_lvl):
                raise BadInput(f"day.upgrades.{k} phải trong [0, {max_lvl}]")
    if "day_plan" in b:
        dp = b["day_plan"]
        if not isinstance(dp, list):
            raise BadInput("day.day_plan phải là mảng")
        menu = tuning["menu"]
        for item in dp:
            if not isinstance(item, dict) or not isinstance(item.get("day"), int) or not (1 <= item["day"] <= 5):
                raise BadInput("day.day_plan: mỗi mục cần day trong [1, 5]")
            dishes = item.get("dishes")
            if not isinstance(dishes, dict) or not dishes:
                raise BadInput("day.day_plan: thiếu dishes")
            recomp = {}
            for did, cnt in dishes.items():
                if did not in menu or isinstance(cnt, bool) or not isinstance(cnt, int) or cnt <= 0:
                    raise BadInput(f"day.day_plan: món hoặc số suất không hợp lệ ({did!r}: {cnt!r})")
                for ing, amt in menu[did]["recipe"].items():
                    recomp[ing] = recomp.get(ing, 0) + amt * cnt
            if "ingredients" in item and item["ingredients"] != recomp:
                raise BadInput(f"day.day_plan ngày {item['day']}: ingredients không khớp tổng công thức")


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
    if "monsters" in b:
        _validate_monsters(b["monsters"], g)
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if "freshness" in tuning:
            _validate_fresh_items("gather.hold", h)
        elif not isinstance(h, list) or any(k not in KINDS_V11 for k in h):
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
        # Fixture bắt đầu trước mốc mất Máu kế tiếp, theo cùng interval với sim.
        limit = g["choke_interval_ticks"] - 1
        if p["zero_oxy_ticks"] > limit:
            raise BadInput(f"player.zero_oxy_ticks phải trong [0, {limit}]")
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


def _validate_monsters(monsters, gather_tuning):
    # Mảng tường minh thay preset; [] dùng để dựng fixture không có cá sấu.
    _check_ids("gather.monsters", monsters)
    species = gather_tuning.get("monsters", {}).get("species", {})
    allowed = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
    for monster in monsters:
        name = f"gather.monsters.{monster['id']}"
        kind = monster.get("kind")
        if set(monster) - allowed or not isinstance(kind, str) or kind not in species:
            raise BadInput(f"{name}: trường hoặc loài thủy quái không hợp lệ")
        bounds = {"x": gather_tuning["bounds"]["x"], "d": species[kind]["depths"]}
        _pos(f"{name}.pos", monster.get("pos"), bounds)
        waypoints = monster.get("waypoints")
        if not isinstance(waypoints, list) or len(waypoints) != 2:
            raise BadInput(f"{name}.waypoints cần hai tọa độ")
        for idx, point in enumerate(waypoints):
            _pos(f"{name}.waypoints[{idx}]", point, bounds)

        target = monster.get("target_idx", 1)
        if isinstance(target, bool) or not isinstance(target, int) or target not in (0, 1):
            raise BadInput(f"{name}.target_idx phải là 0 hoặc 1")
        state = monster.get("state", "patrol")
        if state not in ("patrol", "chase", "recoil"):
            raise BadInput(f"{name}.state không hợp lệ")
        ticks = monster.get("state_ticks_left", 0)
        _nonneg_int(f"{name}.state_ticks_left", ticks)
        direction = monster.get("recoil_dir")
        if state == "recoil":
            if (ticks == 0 or not isinstance(direction, list) or len(direction) != 2
                    or not all(_num(component) and -1 <= component <= 1 for component in direction)
                    or not math.isclose(math.hypot(*direction), 1.0, abs_tol=1e-9)):
                raise BadInput(f"{name}: recoil cần timer dương và recoil_dir là vector đơn vị")
        elif direction is not None:
            raise BadInput(f"{name}.recoil_dir phải là null ngoài trạng thái recoil")


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b and "freshness" not in tuning:
        validate_items(b["stock"])
    for stove in b.get("stoves", []):
        name = f"stoves.{stove['id']}"
        if stove.get("state") in ("cooking", "ready"):
            dish = stove.get("dish")
            if not isinstance(dish, dict):
                raise BadInput(f"{name}: bếp đang nấu hoặc đã chín phải có dish")
            dish_id = dish.get("dish_id")
            if not isinstance(dish_id, str) or dish_id not in tuning["menu"]:
                raise BadInput(f"{name}.dish: dish_id phải có trong menu")
            if not isinstance(dish.get("order_id"), str) or not dish["order_id"]:
                raise BadInput(f"{name}.dish: order_id phải là chuỗi khác rỗng")
            _nonneg_int(f"{name}.dish.base_price", dish.get("base_price"))
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
    if "freshness" in tuning:
        customers = b.get("customers", [])
        if "stock" in b:
            if customers:
                b["customers"] = prepare_quan_reservations(customers, b["stock"], tuning)
            else:
                _validate_fresh_items("quan.stock", b["stock"])
        else:
            claimed = set()
            for customer in customers:
                _reservation_fields(customer, tuning["menu"])
                for ident in customer.get("reserved", []):
                    if ident in claimed:
                        raise BadInput(f"customers.{customer['id']}.reserved: ID đã được giữ {ident}")
                    claimed.add(ident)


def _validate_fresh_items(name, items):
    validate_fresh_items(items, name=name)


def _reservation_fields(customer, menu):
    name = f"customers.{customer['id']}"
    dish = customer.get("dish_id")
    if not isinstance(dish, str) or dish not in menu:
        raise BadInput(f"{name}.dish_id phải có trong menu")
    _nonneg_int(f"{name}.order_tick", customer.get("order_tick", 0))
    if "reserved" not in customer:
        return
    reserved = customer["reserved"]
    if not isinstance(reserved, list) or any(not isinstance(i, str) or not i for i in reserved):
        raise BadInput(f"{name}.reserved phải là mảng ID nguyên liệu")
    if len(reserved) != len(set(reserved)):
        raise BadInput(f"{name}.reserved có ID trùng")
    if reserved and not _awaiting_reservation(customer):
        raise BadInput(f"{name}.reserved chỉ dành cho đơn đang chờ nấu")


def _awaiting_reservation(customer):
    return customer.get("state", "waiting") == "waiting" and customer.get("order_status", "reserved") == "reserved"


def prepare_quan_reservations(customers, stock, tuning):
    """Kiểm và cấp giữ chỗ khi đã có kho thật. Giữ thứ tự khách trong scenario."""
    _validate_fresh_items("quan.stock", stock)
    menu = tuning["menu"]
    threshold = tuning["freshness"].get("spoiled_below")
    if not _num(threshold) or not 0 <= threshold <= 100:
        raise BadInput("freshness.spoiled_below phải trong [0, 100]")
    by_id = {item["id"]: item for item in stock}
    claimed = set()
    prepared = [dict(customer) for customer in customers]
    pending = []
    for customer in prepared:
        _reservation_fields(customer, menu)
        name = f"customers.{customer['id']}.reserved"
        if not _awaiting_reservation(customer):
            customer.setdefault("reserved", [])
            continue
        recipe = menu[customer["dish_id"]]["recipe"]
        if "reserved" not in customer:
            pending.append(customer)
            continue
        counts = Counter()
        for ident in customer["reserved"]:
            if ident in claimed:
                raise BadInput(f"{name}: ID đã được giữ {ident}")
            item = by_id.get(ident)
            if item is None or item["fresh"] < threshold:
                raise BadInput(f"{name}: ID không có trong kho hoặc đã ươn {ident}")
            claimed.add(ident)
            counts[item["kind"]] += 1
        if counts != recipe:
            raise BadInput(f"{name}: nguyên liệu giữ chỗ không khớp công thức")

    available = {}
    for item in sorted(stock, key=lambda item: (-item["fresh"], id_key(item["id"]))):
        if item["id"] not in claimed and item["fresh"] >= threshold:
            available.setdefault(item["kind"], []).append(item["id"])

    pending.sort(key=lambda customer: (customer.get("order_tick", 0), id_key(customer["table_id"])))
    for customer in pending:
        reserved = []
        recipe = menu[customer["dish_id"]]["recipe"]
        for kind, count in sorted(recipe.items()):
            choices = available.get(kind, [])
            if len(choices) < count:
                raise BadInput(f"customers.{customer['id']}.reserved: không đủ {kind} còn tươi")
            reserved.extend(choices[:count])
            del choices[:count]
        customer["reserved"] = reserved
    return prepared
