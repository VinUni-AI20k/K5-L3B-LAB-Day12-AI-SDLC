"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .inventory import KINDS_P1, validate_items
from .sim.shop import gather_tuning

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks",
               "monsters", "ca_ho"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks", "attack_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks", "reservations", "random_reservations"}
DAY_KEYS = {"day", "money", "earned", "reputation", "upgrades", "day_plan"}
MONSTER_STATES = ("patrol", "chase", "recoil", "stunned")


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
        return _load_day_scenario(data, tuning)
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    _validate_duration(block, tuning, mode)
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _validate_duration(block, tuning, mode):
    dur = int(round(tuning[mode]["duration_s"] * tuning["tick_hz"]))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")


def _load_day_scenario(data, tuning):
    """Chế độ day nhận cả ba khối; `quan.stock`/`quan.reputation` bị cấm (bàn giao trong bộ nhớ)."""
    day = data.get("day", {})
    if not isinstance(day, dict):
        raise BadInput("khối day phải là object")
    extra = set(day) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ trong day: {sorted(extra)}")
    for key in ("money", "earned"):
        if key in day:
            v = day[key]
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise BadInput(f"day.{key} phải là số nguyên không âm")
    if day.get("money", 0) > day.get("earned", 0):
        raise BadInput("day.money đầu kỳ cần day.earned và không được lớn hơn day.earned")
    if "day" in day and (type(day["day"]) is not int or day["day"] not in range(1, 6)):
        raise BadInput("day.day phải là số nguyên trong [1, 5]")
    q_tuning = tuning["quan"]
    if "reputation" in day:
        rep = day["reputation"]
        if not _num(rep) or not q_tuning["reputation_min"] <= rep <= q_tuning["reputation_max"]:
            raise BadInput("day.reputation ngoài khoảng cho phép")
    upgrades = day.get("upgrades", {})
    if not isinstance(upgrades, dict):
        raise BadInput("day.upgrades phải là object")
    catalog = tuning["shop"]["upgrades"]
    for name, level in upgrades.items():
        if name not in catalog or type(level) is not int or not 0 <= level <= len(catalog[name]):
            raise BadInput(f"day.upgrades.{name}: cấp không hợp lệ")
    day = dict(day, day_plan=_day_plan_overrides(day.get("day_plan", {}), tuning))
    g = data.get("gather", {})
    q = data.get("quan", {})
    if not isinstance(g, dict) or not isinstance(q, dict):
        raise BadInput("khối gather/quan trong day phải là object")
    if set(g) - GATHER_KEYS:
        raise BadInput(f"trường lạ trong gather: {sorted(set(g) - GATHER_KEYS)}")
    if set(q) - QUAN_KEYS:
        raise BadInput(f"trường lạ trong quan: {sorted(set(q) - QUAN_KEYS)}")
    if "stock" in q or "reputation" in q:
        raise BadInput("day không nhận quan.stock / quan.reputation (bàn giao trong bộ nhớ)")
    if "stoves" in q:
        q = dict(q, stoves=_day_stoves(q["stoves"]))
    _validate_duration(g, tuning, "gather")
    _validate_duration(q, tuning, "quan")
    _validate_gather(g, dict(tuning, gather=gather_tuning(tuning, upgrades)))
    _validate_quan(q, tuning, defer_stock=True)
    return dict(data, day=day, quan=q)


def _day_stoves(stoves):
    """Chuyển payload món của contract sang các trường bếp mà sim Quán dùng."""
    _check_ids("stoves", stoves)
    normalized = []
    for stove in stoves:
        dish = stove.get("dish")
        if isinstance(dish, dict):
            if (set(dish) != {"order_id", "dish_id", "base_price"}
                    or not isinstance(dish["order_id"], str) or not dish["order_id"]
                    or not isinstance(dish["dish_id"], str)
                    or type(dish["base_price"]) is not int or dish["base_price"] <= 0):
                raise BadInput(f"stoves.{stove['id']}: payload món không hợp lệ")
            stove = dict(stove, dish=dish["dish_id"], order_id=dish["order_id"], base_price=dish["base_price"])
        if stove.get("state") in ("cooking", "ready"):
            if not isinstance(stove.get("dish"), str) or not isinstance(stove.get("order_id"), str):
                raise BadInput(f"stoves.{stove['id']}: cần món và order_id")
        normalized.append(stove)
    return normalized


def _day_plan_overrides(plans, tuning):
    if not isinstance(plans, dict):
        raise BadInput("day.day_plan phải là object theo số Ngày")
    result = {}
    for number, plan in plans.items():
        if number not in {str(p["day"]) for p in tuning["day_plan"]}:
            raise BadInput(f"day.day_plan: Ngày không hợp lệ: {number}")
        if not isinstance(plan, dict) or set(plan) - {"dishes", "ingredients"}:
            raise BadInput(f"day.day_plan.{number} phải có dishes và tùy chọn ingredients")
        dishes = plan.get("dishes")
        if not isinstance(dishes, dict):
            raise BadInput(f"day.day_plan.{number}.dishes phải là object")
        ingredients = {}
        for dish_id, portions in dishes.items():
            if dish_id not in tuning["menu"] or type(portions) is not int or portions <= 0:
                raise BadInput(f"day.day_plan.{number}: món hoặc số suất không hợp lệ")
            for kind, amount in tuning["menu"][dish_id]["recipe"].items():
                ingredients[kind] = ingredients.get(kind, 0) + portions * amount
        if "ingredients" in plan and validate_items(plan["ingredients"]) != ingredients:
            raise BadInput(f"day.day_plan.{number}.ingredients khác tổng công thức")
        result[number] = {"dishes": dict(dishes), "ingredients": ingredients}
    return result


def validate_day_quan(scenario, tuning, stock):
    """Kiểm các liên kết và phần giữ với menu và kho đã bàn giao."""
    _validate_quan(dict(scenario, stock=stock), tuning, check_reserved_defaults=True)


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

    # --- quái (v1.1): dựng sẵn trạng thái giữa chừng ---
    if "monsters" in b:
        _check_ids("monsters", b["monsters"])
        species = tuning["gather"]["monsters"]["species"]
        for m in b["monsters"]:
            mid = m["id"]
            if m.get("kind") not in species:
                raise BadInput(f"monsters.{mid}: kind không có trong species")
            _pos(f"monsters.{mid}.pos", m.get("pos"), bounds)
            wps = m.get("waypoints")
            if not (isinstance(wps, list) and len(wps) == 2):
                raise BadInput(f"monsters.{mid}: cần đúng 2 waypoint")
            for wp in wps:
                _pos(f"monsters.{mid}.waypoints", wp, bounds)
            if "target_idx" in m and m["target_idx"] not in (0, 1):
                raise BadInput(f"monsters.{mid}.target_idx phải là 0 hoặc 1")
            state = m.get("state", "patrol")
            if state not in MONSTER_STATES:
                raise BadInput(f"monsters.{mid}: state không hợp lệ")
            if "state_ticks_left" in m:
                _nonneg_int(f"monsters.{mid}.state_ticks_left", m["state_ticks_left"])
            if state in ("recoil", "stunned") and not m.get("state_ticks_left"):
                raise BadInput(f"monsters.{mid}: recoil/stunned cần state_ticks_left dương")
            rd = m.get("recoil_dir")
            if rd is not None and not (isinstance(rd, list) and len(rd) == 2 and all(_num(c) for c in rd)):
                raise BadInput(f"monsters.{mid}.recoil_dir phải là [x, d] hoặc null")

    if "ca_ho" in b and b["ca_ho"] is not None:
        c = b["ca_ho"]
        if not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c["id"]:
            raise BadInput("ca_ho phải là object có id hoặc null")
        _pos("ca_ho.pos", c.get("pos"), bounds)
        if "heading_deg" in c and not _num(c["heading_deg"]):
            raise BadInput("ca_ho.heading_deg phải là số")
        if "photographed" in c and not isinstance(c["photographed"], bool):
            raise BadInput("ca_ho.photographed phải là boolean")


def _validate_quan(b, tuning, *, defer_stock=False, check_reserved_defaults=False):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")

    menu = tuning["menu"]
    stock = b.get("stock", {})
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]}
    for key in ("stoves", "tables"):
        known_ids = {e["id"] for e in tuning["quan"][key]}
        if any(e["id"] not in known_ids for e in b.get(key, [])):
            raise BadInput(f"{key}: id cập nhật không tồn tại")
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")

    # --- bếp: state hợp lệ, cooking phải còn timer, món phải có trong menu ---
    for s in b.get("stoves", []):
        state = s.get("state", "idle")
        if state not in ("idle", "cooking", "ready"):
            raise BadInput(f"stoves.{s['id']}: state phải là idle/cooking/ready")
        if state in ("cooking", "ready") and s.get("dish") not in menu:
            raise BadInput(f"stoves.{s['id']}: món phải có trong menu")
        if state == "cooking":
            v = s.get("cook_ticks_left")
            if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
                raise BadInput(f"stoves.{s['id']}: cooking phải có cook_ticks_left dương")
        if state == "ready" and "ready_ticks" in s:
            _nonneg_int(f"stoves.{s['id']}.ready_ticks", s["ready_ticks"])

    # --- tay: null hoặc payload {order_id, dish_id, base_price} ---
    hand = b.get("hand")
    if hand is not None:
        if not isinstance(hand, dict) or set(hand) != {"order_id", "dish_id", "base_price"}:
            raise BadInput("hand phải là null hoặc {order_id, dish_id, base_price}")
        if not isinstance(hand["order_id"], str) or not hand["order_id"]:
            raise BadInput("hand.order_id phải là chuỗi khác rỗng")
        if hand["dish_id"] not in menu:
            raise BadInput("hand.dish_id phải có trong menu")
        if isinstance(hand["base_price"], bool) or not isinstance(hand["base_price"], int) or hand["base_price"] <= 0:
            raise BadInput("hand.base_price phải là số nguyên dương")

    # --- khách: trạng thái, giữ chỗ, liên kết với bếp/tay ---
    holding = {}
    for s in b.get("stoves", []):
        if s.get("state") in ("cooking", "ready"):
            if s.get("order_id"):
                holding.setdefault(s["order_id"], []).append("stove")
    if hand is not None:
        holding.setdefault(hand["order_id"], []).append("hand")
    held_so_far = {}
    for c in b.get("customers", []):
        cid = c["id"]
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
        dish = c.get("dish_id")
        if dish not in menu:
            raise BadInput(f"customers.{cid}: dish_id phải có trong menu")
        state = c.get("state", "waiting")
        if state not in ("waiting", "eating"):
            raise BadInput(f"customers.{cid}: state phải là waiting hoặc eating")
        status = c.get("order_status", "reserved")
        if status not in ("reserved", "assigned", "unfulfillable", "served"):
            raise BadInput(f"customers.{cid}: order_status không hợp lệ")
        for key in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
            if key in c:
                _nonneg_int(f"customers.{cid}.{key}", c[key])
        reserved = c.get("reserved") or {}
        if check_reserved_defaults and status == "reserved" and not reserved:
            reserved = menu[dish]["recipe"]
        if reserved:
            reserved = validate_items(reserved)
            if reserved != menu[dish]["recipe"]:
                raise BadInput(f"customers.{cid}: reserved khác công thức của món")
            for kind, n in reserved.items():
                held_so_far[kind] = held_so_far.get(kind, 0) + n
                if not defer_stock and held_so_far[kind] > stock.get(kind, 0):
                    raise BadInput(f"customers.{cid}: tổng giữ {kind} quá tồn")
        if state == "eating":
            if status != "served":
                raise BadInput(f"customers.{cid}: đang ăn phải có order_status served")
            if not isinstance(c.get("eat_ticks_left"), int) or c["eat_ticks_left"] <= 0:
                raise BadInput(f"customers.{cid}: đang ăn phải có eat_ticks_left dương")
            for key in ("base_price", "tip"):
                if isinstance(c.get(key), bool) or not isinstance(c.get(key), int) or c[key] < 0:
                    raise BadInput(f"customers.{cid}: {key} phải là số nguyên không âm")
        if status == "unfulfillable" and (state != "waiting" or reserved):
            raise BadInput(f"customers.{cid}: unfulfillable phải đang chờ và không giữ chỗ")
        if status == "assigned":
            if reserved:
                raise BadInput(f"customers.{cid}: đơn assigned không giữ chỗ")
            if len(holding.get(cid, [])) != 1:
                raise BadInput(f"customers.{cid}: đơn assigned phải có đúng một món ở bếp hoặc tay")
    for s in b.get("stoves", []):
        oid = s.get("order_id")
        if oid:
            if hand is not None and hand["order_id"] == oid:
                raise BadInput("bếp và tay không được giữ cùng một đơn")
            match = [c for c in b.get("customers", []) if c["id"] == oid]
            if not match:
                raise BadInput(f"stoves.{s['id']}: order_id không có khách tương ứng")
            if match[0].get("dish_id") != s.get("dish"):
                raise BadInput(f"stoves.{s['id']}: món trên bếp không khớp đơn")
    if check_reserved_defaults and hand is not None:
        match = next((c for c in b.get("customers", []) if c["id"] == hand["order_id"]), None)
        if match is None or match["dish_id"] != hand["dish_id"] or match.get("order_status") != "assigned":
            raise BadInput("hand: món trên tay phải khớp đơn assigned")

    # --- khách đặt trước (mở rộng v1.2, khai trước để fixture dựng được) ---
    if "reservations" in b:
        _check_ids("reservations", b["reservations"])
        if len(b["reservations"]) > 2:
            raise BadInput("reservations tối đa 2 đơn mỗi Ngày")
        desks = [r.get("table_id") for r in b["reservations"]]
        if len(desks) != len(set(desks)):
            raise BadInput("reservations: hai đơn không được cùng bàn")
        for r in b["reservations"]:
            if r.get("table_id") not in known or r.get("dish_id") not in menu:
                raise BadInput(f"reservations.{r['id']}: bàn hoặc món không tồn tại")
            _nonneg_int(f"reservations.{r['id']}.arrival_tick", r.get("arrival_tick"))
