"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

Kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ, và các mâu thuẫn mức luật của nhóm (khách giữ chỗ
quá kho, đơn assigned phải có đúng một món, khách eating thiếu giá/tip, kho cá thể và giữ chỗ theo id từ contract 1.2...)
-> mã thoát 2 (PRD-0 mục D, 'Mâu thuẫn -> mã 2').
"""

import json
import math

from .errors import BadInput
from .inventory import KINDS_P1, inventory_schema, validate_individuals, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}


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


def load_scenario(path, mode: str, tuning: dict, version="1.1") -> dict:
    """`version` là contract_version: từ 1.2 `gather.hold`, `quan.stock` và `customers[].reserved` là cá thể (mảng)."""
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if mode == "day":
        return _load_day(data, tuning, version)
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    return _check_block(mode, block, tuning, version)


def _check_block(mode, block, tuning, version="1.1"):
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
        _validate_gather(block, tuning, version)
    else:
        _validate_quan(block, tuning, version)
    return block


DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def _load_day(data, tuning, version="1.1"):
    """Scenario của chế độ day: khối `day` (trạng thái xuyên Ngày), `gather` và `quan` là mẫu khởi tạo mỗi Ngày."""
    if not isinstance(data, dict) or not set(data) <= {"day", "gather", "quan"}:
        raise BadInput("scenario của day chỉ được có các khối 'day', 'gather', 'quan'")
    out = {}
    for name in ("gather", "quan"):
        if name in data:
            out[name] = _check_block(name, data[name], tuning, version)
    quan = out.get("quan", {})
    for forbidden in ("stock", "reputation"):
        if forbidden in quan:
            raise BadInput(f"quan.{forbidden} không dùng với day (dùng gather.hold để dựng hàng, day.reputation cho uy tín)")
    if "day" in data:
        out["day"] = _validate_day_block(data["day"], tuning)
    return out


def _validate_day_block(b, tuning):
    if not isinstance(b, dict):
        raise BadInput("khối day phải là object")
    extra = set(b) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    q = tuning["quan"]
    if ("money" in b) != ("earned" in b):
        raise BadInput("day.money và day.earned phải khai cùng nhau")
    if "money" in b:
        _nonneg_int("day.money", b["money"])
        _nonneg_int("day.earned", b["earned"])
        if b["money"] > b["earned"]:
            raise BadInput("day.money không được lớn hơn day.earned")
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput(f"day.reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")
    if "upgrades" in b:
        ups = b["upgrades"]
        levels = tuning["shop"]["upgrades"]
        if not isinstance(ups, dict) or set(ups) - set(levels):
            raise BadInput(f"day.upgrades phải là object với khóa thuộc {sorted(levels)}")
        for name, lv in ups.items():
            if isinstance(lv, bool) or not isinstance(lv, int) or not 0 <= lv <= len(levels[name]):
                raise BadInput(f"day.upgrades.{name} phải là số nguyên trong [0, {len(levels[name])}]")
    if "day_plan" in b:
        _validate_day_plan_override(b["day_plan"], tuning)
    return b


def _validate_day_plan_override(plan, tuning):
    menu = tuning["menu"]
    if not isinstance(plan, list) or not plan:
        raise BadInput("day.day_plan phải là mảng không rỗng")
    for i, d in enumerate(plan, 1):
        if not isinstance(d, dict) or set(d) - {"day", "dishes", "ingredients"}:
            raise BadInput(f"day.day_plan[{i - 1}] chỉ có day, dishes, ingredients")
        if "day" in d and (isinstance(d["day"], bool) or d["day"] != i):
            raise BadInput(f"day.day_plan[{i - 1}].day phải bằng {i} (ghi đè theo số Ngày)")
        dishes = d.get("dishes")
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"day.day_plan[{i - 1}].dishes phải là object không rỗng")
        need = {}
        for dish, n in dishes.items():
            if not isinstance(dish, str) or dish not in menu or isinstance(n, bool) or not isinstance(n, int) or n <= 0:
                raise BadInput(f"day.day_plan[{i - 1}].dishes.{dish}: món phải có trong menu, suất là số nguyên > 0")
            for kind, qty in menu[dish]["recipe"].items():
                need[kind] = need.get(kind, 0) + qty * n
        if "ingredients" in d and d["ingredients"] != need:  # tính lại và so với giá trị khai
            raise BadInput(f"day.day_plan[{i - 1}].ingredients khác tổng công thức × suất: {need}")


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


def _validate_gather(b, tuning, version="1.1"):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if inventory_schema(version) == "individuals":
            h = validate_individuals(h, tuning["freshness"]["initial"])  # v1.2: mảng cá thể {id, kind, fresh}
        elif not isinstance(h, list) or any(k not in KINDS_P1 for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    v11 = isinstance(g["fish_initial"], int)
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    # quyết định 4 (docs/plan/phase-2.md): invuln_ticks bị từ chối ở v1.0, chấp nhận ở v1.1
    extra = set(p) - GATHER_PLAYER_KEYS - ({"invuln_ticks"} if v11 else set())
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp", "invuln_ticks"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "invuln_ticks" in p and "monsters" in g and p["invuln_ticks"] > g["monsters"]["invuln_ticks"]:
        raise BadInput("player.invuln_ticks vượt gather.monsters.invuln_ticks")
    if "monsters" in b:
        _validate_monsters(b["monsters"], g)
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
        name = f"fish.{f['id']}"
        allowed = {"id", "kind", "pos", "heading_deg"}
        if v11:
            allowed.add("age_ticks")
        if set(f) - allowed:
            raise BadInput(f"{name}: trường lạ {sorted(set(f) - allowed)}")
        kind = f.get("kind")
        if not isinstance(kind, str) or kind not in g["fish_yield"]:
            raise BadInput(f"{name}: kind phải thuộc fish_yield")
        fish_bounds = bounds
        if v11 and b.get("random_fish", True):
            fish_bounds = {"x": g["fish_x"], "d": g["fish_depths"][kind]}
        _pos(f"{name}.pos", f.get("pos"), fish_bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"{name}: đàn cá phải ở dưới nước")
        heading = f.get("heading_deg", 0)
        if not _num(heading) or not math.isfinite(heading):
            raise BadInput(f"{name}.heading_deg phải là số hữu hạn")
        if "age_ticks" in f:
            _nonneg_int(f"{name}.age_ticks", f["age_ticks"])


MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "state", "waypoint_index"}


def _validate_monsters(arr, g):
    """Cá Sấu trong scenario (v1.1, P2-04): thay thế bố trí mặc định; `[]` là không có quái."""
    mt = g.get("monsters")
    if mt is None:
        raise BadInput("monsters chỉ dùng được khi contract có gather.monsters (v1.1)")
    _check_ids("monsters", arr)
    for m in arr:
        name = f"monsters.{m['id']}"
        if set(m) - MONSTER_KEYS:
            raise BadInput(f"{name}: trường lạ {sorted(set(m) - MONSTER_KEYS)}")
        kind = m.get("kind")
        if not isinstance(kind, str) or kind not in mt["species"]:
            raise BadInput(f"{name}: kind phải thuộc gather.monsters.species")
        area = {"x": g["bounds"]["x"], "d": mt["species"][kind]["depths"]}
        _pos(f"{name}.pos", m.get("pos"), area)
        wps = m.get("waypoints", [m["pos"]])
        if not isinstance(wps, list) or not wps:
            raise BadInput(f"{name}.waypoints phải là mảng không rỗng")
        for k, wp in enumerate(wps):
            _pos(f"{name}.waypoints.{k}", wp, area)
        if m.get("state", "patrol") not in ("patrol", "chase"):
            raise BadInput(f"{name}.state phải là patrol hoặc chase")
        if "waypoint_index" in m:
            _nonneg_int(f"{name}.waypoint_index", m["waypoint_index"])
            if m["waypoint_index"] >= len(wps):
                raise BadInput(f"{name}.waypoint_index vượt số waypoint")


def _validate_quan(b, tuning, version="1.1"):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    individuals = inventory_schema(version) == "individuals"
    if "stock" in b:
        if individuals:
            validate_individuals(b["stock"], tuning["freshness"]["initial"])
        else:
            validate_items(b["stock"])
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
    _validate_quan_rules(b, tuning, individuals)


ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")
DISH_PAYLOAD_KEYS = {"order_id", "dish_id", "base_price"}


def _dish_payload(name, v, menu):
    """Payload món (PRD-0 mục D): {order_id, dish_id, base_price}; hand và stoves[].dish là null hoặc payload."""
    if v is None:
        return None
    if not isinstance(v, dict) or set(v) != DISH_PAYLOAD_KEYS:
        raise BadInput(f"{name} phải là null hoặc {{order_id, dish_id, base_price}}")
    if not isinstance(v["order_id"], str) or not v["order_id"]:
        raise BadInput(f"{name}.order_id phải là chuỗi khác rỗng")
    if not isinstance(v["dish_id"], str) or v["dish_id"] not in menu:
        raise BadInput(f"{name}.dish_id phải là một món trong menu")
    _nonneg_int(f"{name}.base_price", v["base_price"])
    return v


def _validate_quan_rules(b, tuning, individuals=False):
    """Mâu thuẫn mức luật của quán (PRD-0 mục D): payload món, đơn assigned/unfulfillable/served,
    khách eating, giữ chỗ khác công thức hoặc quá tồn, bếp và tay giữ cùng đơn hoặc món không khớp đơn."""
    menu = tuning["menu"]
    q = tuning["quan"]
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput(f"reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")

    customers = {c["id"]: c for c in b.get("customers", [])}
    held = {}  # order_id -> nơi giữ món ("hand" hoặc "stoves.<id>")

    def hold_payload(where, payload):
        if payload is None:
            return
        oid = payload["order_id"]
        if oid not in customers:
            raise BadInput(f"{where}: order_id {oid!r} không phải khách nào trong scenario")
        dish = customers[oid].get("dish_id")
        if dish is not None and dish != payload["dish_id"]:
            raise BadInput(f"{where}: món {payload['dish_id']!r} không khớp đơn của khách {oid!r} ({dish!r})")
        if oid in held:
            raise BadInput(f"{where} và {held[oid]} cùng giữ đơn {oid!r}")
        held[oid] = where

    hold_payload("hand", _dish_payload("hand", b.get("hand"), menu))
    for s in b.get("stoves", []):
        where = f"stoves.{s['id']}"
        hold_payload(where, _dish_payload(f"{where}.dish", s.get("dish"), menu))
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in s:
                _nonneg_int(f"{where}.{key}", s[key])

    reserved_total = {}
    reserved_ids = {}  # v1.2: id cá thể -> khách đang giữ
    kinds_of = {it["id"]: it["kind"] for it in b.get("stock", [])} if individuals and "stock" in b else None
    for cid, c in customers.items():
        status = c.get("order_status", "reserved")
        if status not in ORDER_STATUSES:
            raise BadInput(f"customers.{cid}.order_status phải thuộc {ORDER_STATUSES}")
        if individuals:
            reserved = _reserved_ids(cid, c["reserved"], reserved_ids, kinds_of) if "reserved" in c else None
        else:
            reserved = validate_items(c["reserved"]) if "reserved" in c else None
        dish = c.get("dish_id")
        if dish is not None and dish not in menu:
            raise BadInput(f"customers.{cid}.dish_id không có trong menu ({dish!r})")
        if status == "reserved" and reserved is not None and dish is not None:
            if individuals:
                if kinds_of is not None and _kind_counts(kinds_of[i] for i in reserved) != menu[dish]["recipe"]:
                    raise BadInput(f"customers.{cid}: phần giữ chỗ khác công thức của {dish}")
            elif reserved != menu[dish]["recipe"]:
                raise BadInput(f"customers.{cid}: phần giữ chỗ khác công thức của {dish}")
        if status == "assigned":
            if cid not in held:
                raise BadInput(f"customers.{cid}: đơn assigned phải có đúng một món ở bếp hoặc tay")
            if reserved:
                raise BadInput(f"customers.{cid}: đơn assigned phải có phần giữ rỗng")
        if status == "unfulfillable":
            if reserved:
                raise BadInput(f"customers.{cid}: đơn unfulfillable phải có phần giữ rỗng")
            if cid in held:
                raise BadInput(f"customers.{cid}: đơn unfulfillable không có món")
        if c.get("state") == "eating":
            if status != "served":
                raise BadInput(f"customers.{cid}: khách eating phải có order_status served")
            eat = c.get("eat_ticks_left")
            if isinstance(eat, bool) or not isinstance(eat, int) or eat <= 0:
                raise BadInput(f"customers.{cid}: khách eating cần eat_ticks_left dương")
            for key in ("base_price", "tip"):
                _nonneg_int(f"customers.{cid}.{key}", c.get(key))
        if not individuals:
            for k, v in (reserved or {}).items():
                reserved_total[k] = reserved_total.get(k, 0) + v
    # Kho đến từ --inventory thì load_scenario không biết; headless gọi check_reserved_within_stock sau khi đọc kho.
    if "stock" in b and not individuals:
        _check_within_stock(reserved_total, b["stock"])


def _kind_counts(kinds):
    out = {}
    for k in kinds:
        out[k] = out.get(k, 0) + 1
    return out


def _reserved_ids(cid, ids, owners, kinds_of):
    """v1.2: `reserved` là mảng id cá thể không trùng; mỗi id có trong kho (nếu khai kho) và chỉ một khách giữ."""
    if not isinstance(ids, list) or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise BadInput(f"customers.{cid}.reserved phải là mảng id cá thể không trùng")
    for i in ids:
        if kinds_of is not None and i not in kinds_of:
            raise BadInput(f"customers.{cid}: giữ chỗ cá thể {i} không có trong kho")
        if i in owners:
            raise BadInput(f"customers.{cid}: cá thể {i} đã được khách {owners[i]} giữ chỗ")
        owners[i] = cid
    return ids


def _check_within_stock(need, stock):
    for k in sorted(need):
        if need[k] > stock.get(k, 0):
            raise BadInput(f"khách giữ chỗ {k} = {need[k]} vượt kho ({stock.get(k, 0)})")


def check_reserved_within_stock(block, stock):
    """Phần giữ chỗ nguyên liệu của khách (ghi rõ trong `customers[].reserved`) không được vượt kho (PRD-0 mục D, mã 2).
    Dùng cho kho nạp từ --inventory; `block` là khối quan đã qua load_scenario nên `reserved` đã hợp lệ."""
    if isinstance(stock, list):  # v1.2: giữ chỗ theo id, mỗi id phải có trong kho và chỉ một khách giữ
        _reserved_by_id(block, stock)
        return
    need = {}
    for c in block.get("customers", []):
        for k, v in (c.get("reserved") or {}).items():
            need[k] = need.get(k, 0) + v
    _check_within_stock(need, stock)


def _reserved_by_id(block, stock):
    kinds_of = {it["id"]: it["kind"] for it in stock}
    owners = {}
    for c in block.get("customers", []):
        if "reserved" in c:
            _reserved_ids(c["id"], c["reserved"], owners, kinds_of)
