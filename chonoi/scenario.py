"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

v1.1 (TV6, T242): khối `day` (mode day), `gather.monsters[]`, `gather.fish[].age_ticks`; cấm `quan.stock`,
`quan.reputation` khi chạy day; `0 ≤ money ≤ earned`; `day.day_plan` tính lại ingredients và so.
v1.2 (TV3, TICKET-03): `quan.stock` mảng cá thể {id, kind, fresh}; `customers[].reserved` mảng id cá thể
(trỏ kho, còn tươi, không dùng chung, đủ công thức); thiếu reserved -> tự cấp tươi nhất trước theo
(order_tick, id_key(table_id)); kho đếm v1.0/v1.1 vẫn hợp lệ ở mode quan.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
quan (Commit 1 — TV3): kiểm mâu thuẫn mức luật theo PRD-0 mục D: khách reserved vượt kho,
đơn assigned phải có đúng một món ở bếp/tay, khách eating thiếu giá/tip... -> BadInput (mã 2).
"""

import json
import math

from .errors import BadInput
from .ids import id_key
from .inventory import menu_kinds, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}  # monsters: v1.1
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")  # keo_neo: v1.1, TV1
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")  # ca_keo: v1.1, TV1
QUAN_PLAYER_KEYS = {"pos", "vel"}
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}  # v1.1
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
MONSTER_STATES = ("patrol", "chase", "recoil")
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
QUAN_STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
QUAN_STOVE_STATES = ("idle", "cooking", "ready")
QUAN_CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                      "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
QUAN_CUSTOMER_STATES = ("waiting", "eating")
QUAN_ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")
DISH_KEYS = {"order_id", "dish_id", "base_price"}


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
    """gather/quan: trả dict của khối đó. day (v1.1): trả {"day":…, "gather":…, "quan":…} (khối vắng = {})."""
    if path is None:
        return {"day": {}, "gather": {}, "quan": {}} if mode == "day" else {}
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
    return _validate_block(mode, data.get(mode, {}), tuning)


def _validate_block(mode, block, tuning):
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
    """Scenario `day` (đề §4.3): khối day dựng trạng thái xuyên Ngày; gather/quan là mẫu khởi tạo mỗi Ngày."""
    if not isinstance(data, dict) or not set(data) <= {"day", "gather", "quan"}:
        raise BadInput("scenario day chỉ được có khối 'day', 'gather', 'quan'")
    q = data.get("quan", {})
    if isinstance(q, dict):
        bad = sorted(set(q) & {"stock", "reputation"})
        if bad:
            raise BadInput(f"chạy day cấm quan.{', quan.'.join(bad)} (dùng gather.hold / day.reputation)")
    out = {"day": _validate_day(data.get("day", {}), tuning),
           "gather": _validate_block("gather", data.get("gather", {}), tuning),
           "quan": _validate_block("quan", q, tuning)}
    return out


def _validate_day(b, tuning):
    if not isinstance(b, dict):
        raise BadInput("khối day phải là object")
    extra = set(b) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    for k in ("money", "earned"):
        if k in b:
            _nonneg_int(f"day.{k}", b[k])
    money, earned = b.get("money", 0), b.get("earned", 0)
    if money > earned:
        raise BadInput("day: cần 0 ≤ money ≤ earned (khai cả hai khi có tiền đầu kỳ)")
    if "reputation" in b:
        q = tuning["quan"]
        lo, hi = q.get("reputation_min", 0), q.get("reputation_max", 5)
        if not (_num(b["reputation"]) and lo <= b["reputation"] <= hi):
            raise BadInput(f"day.reputation phải trong [{lo}, {hi}]")
    shop = tuning.get("shop")
    if "upgrades" in b:
        u = b["upgrades"]
        if not isinstance(u, dict):
            raise BadInput("day.upgrades phải là object {id: cấp}")
        if not isinstance(shop, dict) or not isinstance(shop.get("upgrades"), dict):
            raise BadInput("contract chưa có khóa tuning.shop (chờ TV1)")
        for uid, lv in u.items():
            if uid not in shop["upgrades"]:
                raise BadInput(f"day.upgrades: nâng cấp lạ {uid}")
            _nonneg_int(f"day.upgrades.{uid}", lv)
            if lv > len(shop["upgrades"][uid]):
                raise BadInput(f"day.upgrades.{uid} vượt cấp tối đa")
    if "day_plan" in b:
        from .sim.day import plan_ingredients
        plans = b["day_plan"]
        if not isinstance(plans, list):
            raise BadInput("day.day_plan phải là mảng {day, dishes[, ingredients]}")
        seen = set()
        for i, p in enumerate(plans):
            if not isinstance(p, dict) or set(p) - {"day", "dishes", "ingredients"}:
                raise BadInput(f"day.day_plan[{i}] chỉ có day, dishes, ingredients")
            d = p.get("day")
            if isinstance(d, bool) or not isinstance(d, int) or not (1 <= d <= 5) or d in seen:
                raise BadInput(f"day.day_plan[{i}].day phải là số nguyên 1–5, không trùng")
            seen.add(d)
            dishes = p.get("dishes")
            if not isinstance(dishes, dict) or not dishes or any(
                    isinstance(n, bool) or not isinstance(n, int) or n <= 0 for n in dishes.values()):
                raise BadInput(f"day.day_plan[{i}].dishes phải là map món → số nguyên dương")
            ing = plan_ingredients(tuning["menu"], dishes)
            if "ingredients" in p and p["ingredients"] != ing:
                raise BadInput(f"day.day_plan[{i}].ingredients khác Σ công thức × suất ({ing})")
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
    for m in b.get("monsters", []):
        _validate_monster(m, g)
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(k not in menu_kinds(tuning["menu"]) for k in h):
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


def _validate_monster(m, g):
    """gather.monsters[] (đề §4.3): thay bố trí mặc định; loài phải có trong tuning.gather.monsters.species."""
    mid = m["id"]
    extra = set(m) - MONSTER_KEYS
    if extra:
        raise BadInput(f"monsters.{mid}: trường lạ {sorted(extra)}")
    species = (g.get("monsters") or {}).get("species")
    if not isinstance(species, dict):
        raise BadInput("contract chưa có khóa tuning.gather.monsters (chờ TV1)")
    if m.get("kind") not in species:
        raise BadInput(f"monsters.{mid}: kind phải là một trong {sorted(species)}")
    _pos(f"monsters.{mid}.pos", m.get("pos"), g["bounds"])
    wps = m.get("waypoints")
    if not (isinstance(wps, list) and len(wps) == 2):
        raise BadInput(f"monsters.{mid}.waypoints phải có đúng 2 điểm")
    for j, wp in enumerate(wps):
        _pos(f"monsters.{mid}.waypoints[{j}]", wp, g["bounds"])
    if m.get("target_idx", 1) not in (0, 1) or isinstance(m.get("target_idx"), bool):
        raise BadInput(f"monsters.{mid}.target_idx phải là 0 hoặc 1")
    state = m.get("state", "patrol")
    if state not in MONSTER_STATES:
        raise BadInput(f"monsters.{mid}.state phải là một trong {MONSTER_STATES}")
    if "state_ticks_left" in m:
        _nonneg_int(f"monsters.{mid}.state_ticks_left", m["state_ticks_left"])
    rd = m.get("recoil_dir")
    if state == "recoil":
        if m.get("state_ticks_left", 0) <= 0:
            raise BadInput(f"monsters.{mid}: recoil cần state_ticks_left > 0")
        if not (isinstance(rd, list) and len(rd) == 2 and all(_num(c) for c in rd)
                and abs(math.hypot(rd[0], rd[1]) - 1) <= 1e-6):
            raise BadInput(f"monsters.{mid}.recoil_dir phải là vector đơn vị khi recoil")
    elif rd is not None:
        raise BadInput(f"monsters.{mid}.recoil_dir chỉ khác null khi recoil")


def _check_dish(label, dish, menu, customer_ids):
    """Món đang nấu ở bếp hoặc giữ trên tay: payload {order_id, dish_id, base_price} khớp một đơn."""
    if not isinstance(dish, dict) or set(dish) != DISH_KEYS:
        raise BadInput(f"{label} phải là payload {{order_id, dish_id, base_price}}")
    if dish["dish_id"] not in menu:
        raise BadInput(f"{label}: dish_id phải là món trong menu")
    if dish["order_id"] not in customer_ids:
        raise BadInput(f"{label}: order_id phải khớp một khách tồn tại")
    if not _num(dish["base_price"]) or dish["base_price"] < 0:
        raise BadInput(f"{label}: base_price phải là số không âm")


def _validate_item_stock(stock, kinds):
    """quan.stock v1.2: mảng cá thể {id, kind, fresh}; trả map id -> cá thể để kiểm reserved."""
    out = {}
    for item in stock:
        if not isinstance(item, dict) or set(item) != {"id", "kind", "fresh"}:
            raise BadInput("quan.stock: mỗi cá thể cần đúng {id, kind, fresh}")
        iid = item["id"]
        if not isinstance(iid, str) or not iid:
            raise BadInput("quan.stock: id cá thể phải là chuỗi khác rỗng")
        if iid in out:
            raise BadInput(f"quan.stock: id cá thể trùng {iid}")
        if item["kind"] not in kinds:
            raise BadInput(f"quan.stock.{iid}: nguyên liệu lạ {item['kind']!r}")
        fresh = item["fresh"]
        if isinstance(fresh, bool) or not _num(fresh) or not math.isfinite(fresh) or not (0 <= fresh <= 100):
            raise BadInput(f"quan.stock.{iid}: fresh phải là số hữu hạn trong [0, 100]")
        out[iid] = item
    return out


def _validate_reserved_ids(cid, ids, items, dish_id, recipe, claimed, below):
    """reserved v1.2: mảng id cá thể — tồn tại trong kho, còn tươi, không dùng chung, đủ công thức."""
    if len(ids) != len(set(ids)):
        raise BadInput(f"customers.{cid}: reserved có id trùng lặp")
    counts = {}
    for iid in ids:
        if not isinstance(iid, str):
            raise BadInput(f"customers.{cid}: reserved phải là mảng id chuỗi")
        item = items.get(iid)
        if item is None:
            raise BadInput(f"customers.{cid}: reserved trỏ tới cá thể không có trong kho: {iid}")
        if item["fresh"] < below:
            raise BadInput(f"customers.{cid}: reserved dùng hàng ươn ({iid} fresh {item['fresh']} < {below})")
        if iid in claimed:
            raise BadInput(f"cá thể {iid} bị nhiều đơn cùng giữ")
        claimed.add(iid)
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    if counts != recipe:
        raise BadInput(f"customers.{cid}: reserved phải đủ đúng công thức của {dish_id}")
    return list(ids)


def _pick_fresh_ids(items, recipe, claimed, below):
    """Tự cấp giữ chỗ: cá thể tươi nhất trước (hòa id_key nhỏ); đủ công thức -> mảng id, thiếu -> None."""
    candidates = sorted((it for it in items.values()
                         if it["id"] not in claimed and it["fresh"] >= below),
                        key=lambda it: (-it["fresh"], id_key(it["id"])))
    counts, picked = {}, []
    for item in candidates:
        kind = item["kind"]
        if counts.get(kind, 0) < recipe.get(kind, 0):
            counts[kind] = counts.get(kind, 0) + 1
            picked.append(item["id"])
    if all(counts.get(kind, 0) >= n for kind, n in recipe.items()):
        return picked
    return None


def _validate_quan(b, tuning):
    q, menu = tuning["quan"], tuning["menu"]
    below = (tuning.get("freshness") or {}).get("spoiled_below", 30)  # ngưỡng ươn v1.2 (mặc định 30)
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    stock = b.get("stock")
    items = None  # v1.2: map id -> cá thể; None = kho đếm v1.0/v1.1
    if isinstance(stock, list):
        items = _validate_item_stock(stock, menu_kinds(menu))
    elif "stock" in b:
        validate_items(stock, kinds=menu_kinds(menu))
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b and not (_num(b["reputation"])
                                  and q["reputation_min"] <= b["reputation"] <= q["reputation_max"]):
        raise BadInput(f"reputation phải là số trong [{q['reputation_min']}, {q['reputation_max']}]")
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = q["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")

    customers = b.get("customers", [])
    customer_ids = {c["id"] for c in customers}

    # Món đang nấu/giữ: tay + mỗi bếp tối đa một món; mỗi đơn chỉ được giữ ở đúng một chỗ.
    holders = []
    hand = b.get("hand")
    if hand is not None:
        _check_dish("hand", hand, menu, customer_ids)
        holders.append(("hand", hand["order_id"]))
    for s in b.get("stoves", []):
        extra = set(s) - QUAN_STOVE_KEYS
        if extra:
            raise BadInput(f"stoves.{s['id']}: trường lạ {sorted(extra)}")
        state = s.get("state", "idle")
        if state not in QUAN_STOVE_STATES:
            raise BadInput(f"stoves.{s['id']}: state phải là một trong {QUAN_STOVE_STATES}")
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in s:
                _nonneg_int(f"stoves.{s['id']}.{key}", s[key])
        if state == "cooking":
            if s.get("cook_ticks_left", 0) <= 0:
                raise BadInput(f"stoves.{s['id']}: bếp đang cooking cần cook_ticks_left > 0")
            if s.get("dish") is None:
                raise BadInput(f"stoves.{s['id']}: bếp đang cooking thiếu dish")
        if s.get("dish") is not None:
            _check_dish(f"stoves.{s['id']}.dish", s["dish"], menu, customer_ids)
            holders.append((f"stoves.{s['id']}", s["dish"]["order_id"]))
    held_by = {}
    for where, oid in holders:
        if oid in held_by:
            raise BadInput(f"đơn {oid} bị giữ ở cả {held_by[oid]} và {where}")
        held_by[oid] = where

    known_tables = {t["id"] for t in q["tables"]} | {t.get("id") for t in b.get("tables", [])}
    table_ids = []
    reserved_total = {}
    claimed = set()  # v1.2: id cá thể đã bị một đơn giữ
    for c in customers:
        cid = c["id"]
        table_ids.append(c.get("table_id"))
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known_tables:
            raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
        extra = set(c) - QUAN_CUSTOMER_KEYS
        if extra:
            raise BadInput(f"customers.{cid}: trường lạ {sorted(extra)}")
        if c.get("dish_id") not in menu:
            raise BadInput(f"customers.{cid}: dish_id phải là món trong menu")
        for key in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
            if key in c:
                _nonneg_int(f"customers.{cid}.{key}", c[key])
        for key in ("base_price", "tip"):
            if key in c and not (_num(c[key]) and c[key] >= 0):
                raise BadInput(f"customers.{cid}: {key} phải là số không âm")
        state = c.get("state", "waiting")
        if state not in QUAN_CUSTOMER_STATES:
            raise BadInput(f"customers.{cid}: state phải là một trong {QUAN_CUSTOMER_STATES}")
        status = c.get("order_status", "reserved")
        if status not in QUAN_ORDER_STATUSES:
            raise BadInput(f"customers.{cid}: order_status phải là một trong {QUAN_ORDER_STATUSES}")
        recipe = menu[c["dish_id"]].get("recipe", {})
        reserved = None
        raw = c.get("reserved")
        if raw is not None:
            if isinstance(raw, list):  # v1.2: mảng id cá thể
                if items is None:
                    raise BadInput(f"customers.{cid}: reserved là mảng id nhưng quan.stock không phải kho cá thể v1.2")
                reserved = _validate_reserved_ids(cid, raw, items, c["dish_id"], recipe, claimed, below)
            elif isinstance(raw, dict):  # v1.0/v1.1: đếm theo loại
                if items is not None:
                    raise BadInput(f"customers.{cid}: kho cá thể v1.2 cần reserved là mảng id cá thể")
                try:
                    reserved = validate_items(raw, kinds=menu_kinds(menu))
                except BadInput as e:
                    raise BadInput(f"customers.{cid}: reserved không hợp lệ: {e}")
            else:
                raise BadInput(f"customers.{cid}: reserved phải là object nguyên liệu hoặc mảng id cá thể")
        holds = [where for where, oid in holders if oid == cid]
        if status == "reserved":
            if reserved is None:
                # Thiếu giữ chỗ -> suy ra: v1.2 cấp cá thể tươi nhất (hòa id_key) theo ưu tiên đơn;
                # v1.0/v1.1 lấy nguyên công thức (tổng reserved vẫn phải <= kho nên thứ tự không đổi kết luận).
                if items is None:
                    reserved = dict(recipe)
                    c["reserved"] = dict(recipe)
            elif items is not None:
                pass  # đã kiểm kỹ trong _validate_reserved_ids
            elif reserved != recipe:
                raise BadInput(f"customers.{cid}: reserved phải khớp đúng công thức của {c['dish_id']}")
        elif status == "assigned":
            if len(holds) != 1:
                raise BadInput(f"customers.{cid}: đơn assigned phải có đúng một món ở bếp hoặc trên tay")
            if reserved:
                raise BadInput(f"customers.{cid}: đơn assigned phải có reserved rỗng")
        elif status == "unfulfillable":
            if state != "waiting":
                raise BadInput(f"customers.{cid}: khách unfulfillable phải vẫn đang chờ (state=waiting)")
            if reserved:
                raise BadInput(f"customers.{cid}: khách unfulfillable phải có reserved rỗng")
            if holds:
                raise BadInput(f"customers.{cid}: đơn unfulfillable không được có món ở bếp/tay")
        if state == "eating":
            if status != "served":
                raise BadInput(f"customers.{cid}: khách đang ăn phải có order_status=served")
            if c.get("eat_ticks_left", 0) <= 0:
                raise BadInput(f"customers.{cid}: khách đang ăn cần eat_ticks_left > 0")
            if "base_price" not in c or "tip" not in c:
                raise BadInput(f"customers.{cid}: khách đang ăn cần khai base_price và tip đã chốt")
        if items is None:  # v1.0/v1.1: cộng dồn để đối chiếu kho
            for kind, n in (reserved or {}).items():
                reserved_total[kind] = reserved_total.get(kind, 0) + n
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
    if items is not None:
        # v1.2: đơn reserved thiếu reserved -> tự cấp theo (order_tick, id_key(table_id)),
        # cá thể tươi nhất trước, hòa id nhỏ; thiếu cá thể tươi là mâu thuẫn -> mã 2.
        for c in sorted((c for c in customers
                         if c.get("order_status", "reserved") == "reserved" and c.get("reserved") is None),
                        key=lambda c: (c.get("order_tick", 0), id_key(c.get("table_id")))):
            recipe = menu[c["dish_id"]].get("recipe", {})
            picked = _pick_fresh_ids(items, recipe, claimed, below)
            if picked is None:
                raise BadInput(f"customers.{c['id']}: không đủ cá thể tươi (>= {below}) "
                               f"để giữ chỗ cho {c['dish_id']}")
            c["reserved"] = picked
            claimed.update(picked)
    elif "stock" in b:
        for kind in sorted(reserved_total):
            if reserved_total[kind] > b["stock"].get(kind, 0):
                raise BadInput(f"tổng reserved của khách vượt kho: cần {reserved_total[kind]} '{kind}', "
                               f"kho chỉ còn {b['stock'].get(kind, 0)}")
