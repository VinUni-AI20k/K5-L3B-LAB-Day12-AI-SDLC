"""Nạp và kiểm scenario (Contract D, v1.1). Trả về dict của đúng khối theo mode.

gather/quan: trả khối của mode. day (v1.1): trả {"gather": ..., "quan": ..., "day": ...}; khối gather và quan
là mẫu khởi tạo mỗi Ngày, khối day dựng trạng thái xuyên Ngày (Ticket-02 mục 4.3).

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .contract import FISH_KINDS, NODE_KINDS, plan_ingredients
from .inventory import KINDS_P1, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
FISH_KEYS = {"id", "kind", "pos", "heading_deg", "age_ticks"}
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
MONSTER_STATES = ("patrol", "chase", "recoil")  # "stunned" chỉ có khi bật mở rộng Lao (weapon)
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}
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
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    _validate_block(mode, block, tuning)
    return block


def _validate_block(mode, block, tuning, in_day=False):
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
        _validate_gather(block, tuning, in_day)
    else:
        _validate_quan(block, tuning)


def _load_day(data, tuning):
    """--mode day: nhận khối gather, quan (mẫu mỗi Ngày) và day (xuyên Ngày). Ticket-02 mục 4.3."""
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan", "day"}:
        raise BadInput("scenario của day chỉ được có khối 'gather', 'quan', 'day'")
    out = {}
    for mode in ("gather", "quan"):
        block = data.get(mode, {})
        if not isinstance(block, dict):
            raise BadInput(f"khối {mode} phải là object")
        if mode == "quan":
            for banned in ("stock", "reputation"):
                if banned in block:
                    raise BadInput(f"chạy day không được khai quan.{banned} (dùng gather.hold / day.reputation)")
        _validate_block(mode, block, tuning, in_day=True)
        out[mode] = block
    day = data.get("day", {})
    if not isinstance(day, dict):
        raise BadInput("khối day phải là object")
    extra = set(day) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    # Mâu thuẫn kho/khách/bếp với kho thực lúc mở quán: QuanSim kiểm khi dựng với kho bàn giao (BadInput -> mã 2).
    out["day"] = _validate_day(day, tuning)
    return out


def effective_day_plan(tuning, day_block=None):
    """Kế hoạch 5 Ngày khi chạy: preset tuning.day_plan, ghi đè theo số Ngày bằng day.day_plan của scenario."""
    plan = {p["day"]: dict(p) for p in tuning["day_plan"]}
    for p in (day_block or {}).get("day_plan", []):
        plan[p["day"]] = dict(p)
    return [plan[d] for d in sorted(plan)]


def _validate_day(b, tuning):
    """Giá trị khối day (Ticket-02 mục 4.3). Mâu thuẫn -> BadInput (mã 2)."""
    for key in ("money", "earned"):
        if key in b:
            _nonneg_int(f"day.{key}", b[key])
    if "money" in b and "earned" not in b:
        raise BadInput("day: có tiền đầu kỳ (money) thì phải khai cả earned")
    if b.get("money", 0) > b.get("earned", 0):
        raise BadInput("day: cần 0 <= money <= earned")
    q = tuning["quan"]
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput(f"day.reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")
    if "upgrades" in b:
        up = b["upgrades"]
        if not isinstance(up, dict):
            raise BadInput("day.upgrades phải là object {id nâng cấp: cấp}")
        levels = {k: len(v) for k, v in tuning["shop"]["upgrades"].items()}
        for k, lv in up.items():
            if k not in levels:
                raise BadInput(f"day.upgrades.{k}: không có trong shop.upgrades {sorted(levels)}")
            _nonneg_int(f"day.upgrades.{k}", lv)
            if lv > levels[k]:
                raise BadInput(f"day.upgrades.{k}: cấp {lv} vượt cấp tối đa {levels[k]}")
    if "day_plan" in b:
        b["day_plan"] = _validate_day_plan_override(b["day_plan"], tuning)
    return b


DAY_PLAN_KEYS = {"day", "dishes", "ingredients"}


def _validate_day_plan_override(plan, tuning):
    """day.day_plan ghi đè theo số Ngày; ingredients luôn tính lại, khai mà khác thì báo lỗi."""
    if not isinstance(plan, list):
        raise BadInput("day.day_plan phải là mảng")
    menu = tuning["menu"]
    n_days = len(tuning["day_plan"])
    seen, out = set(), []
    for p in plan:
        if not isinstance(p, dict) or set(p) - DAY_PLAN_KEYS:
            raise BadInput(f"day.day_plan: mỗi mục chỉ có {sorted(DAY_PLAN_KEYS)}")
        d = p.get("day")
        if isinstance(d, bool) or not isinstance(d, int) or not (1 <= d <= n_days):
            raise BadInput(f"day.day_plan.day phải là số nguyên trong [1, {n_days}]")
        if d in seen:
            raise BadInput(f"day.day_plan: Ngày {d} khai hai lần")
        seen.add(d)
        dishes = p.get("dishes")
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"day.day_plan Ngày {d}: dishes phải là object không rỗng")
        for dish_id, n in dishes.items():
            if dish_id not in menu:
                raise BadInput(f"day.day_plan Ngày {d}: món ngoài menu {dish_id!r}")
            if isinstance(n, bool) or not isinstance(n, int) or n < 1:
                raise BadInput(f"day.day_plan Ngày {d}: số suất {dish_id} phải là số nguyên dương")
        ing = plan_ingredients(menu, dishes)
        ing = {k: ing[k] for k in sorted(ing)}
        if "ingredients" in p:
            declared = p["ingredients"]
            if not isinstance(declared, dict) or {k: v for k, v in declared.items() if v} != ing:
                raise BadInput(f"day.day_plan Ngày {d}: ingredients khác tổng công thức × số suất {ing}")
        out.append({"day": d, "dishes": dict(dishes), "ingredients": ing})
    return out


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


def _caps(tuning, in_day):
    """Trần oxy (tick) và Máu cho fixture: gather độc lập theo tuning, day cho phép tới cấp nâng cấp cao nhất."""
    g = tuning["gather"]
    omax, hmax = g["oxygen_max_s"], g["hp_max"]
    if in_day:
        ups = tuning["shop"]["upgrades"]
        omax = max([omax] + [lv["oxygen_max_s"] for lv in ups["oxygen"]])
        hmax = max([hmax] + [lv["hp_max"] for lv in ups["hp"]])
    return int(round(omax * 60)), hmax


def _validate_gather(b, tuning, in_day=False):
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
    omax, hmax = _caps(tuning, in_day)
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= hmax):
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
        extra = set(f) - FISH_KEYS
        if extra:
            raise BadInput(f"fish.{f['id']}: trường lạ {sorted(extra)}")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    _validate_monsters(b.get("monsters", []), g)


def _validate_monsters(monsters, g):
    """gather.monsters[] (Ticket-02 mục 4.3): thay danh sách mặc định của Ngày."""
    bounds, species = g["bounds"], g["monsters"]["species"]
    for m in monsters:
        mid = m["id"]
        extra = set(m) - MONSTER_KEYS
        if extra:
            raise BadInput(f"monsters.{mid}: trường lạ {sorted(extra)}")
        if m.get("kind") not in species:
            raise BadInput(f"monsters.{mid}.kind phải thuộc {sorted(species)}")
        lo, hi = species[m["kind"]]["depths"]
        _pos(f"monsters.{mid}.pos", m.get("pos"), bounds)
        if not (lo <= m["pos"][1] <= hi):
            raise BadInput(f"monsters.{mid}.pos nằm ngoài dải độ sâu của loài [{lo}, {hi}]")
        wps = m.get("waypoints")
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"monsters.{mid}.waypoints phải có đúng 2 điểm")
        for i, wp in enumerate(wps):
            _pos(f"monsters.{mid}.waypoints[{i}]", wp, bounds)
        if isinstance(m.get("target_idx"), bool) or m.get("target_idx", 1) not in (0, 1):
            raise BadInput(f"monsters.{mid}.target_idx phải là 0 hoặc 1")
        state = m.get("state", "patrol")
        if state not in MONSTER_STATES:
            raise BadInput(f"monsters.{mid}.state phải là một trong {MONSTER_STATES}")
        ticks = m.get("state_ticks_left", 0)
        _nonneg_int(f"monsters.{mid}.state_ticks_left", ticks)
        rd = m.get("recoil_dir")
        if state == "recoil":
            if ticks < 1:
                raise BadInput(f"monsters.{mid}: recoil cần state_ticks_left > 0")
            if not (isinstance(rd, list) and len(rd) == 2 and all(_num(c) for c in rd)
                    and abs((rd[0] ** 2 + rd[1] ** 2) - 1) < 1e-6):
                raise BadInput(f"monsters.{mid}.recoil_dir phải là vector đơn vị khi recoil")
        elif rd is not None:
            raise BadInput(f"monsters.{mid}.recoil_dir chỉ khác null khi recoil")


def _validate_quan(b, tuning):
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
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
    _validate_quan_customers(b, tuning)


CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
                 "order_status", "reserved", "base_price", "tip"}
CUSTOMER_STATES = ("waiting", "eating")
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")


def _validate_quan_customers(b, tuning):
    """Mâu thuẫn mức luật của quan.customers (PRD-0 mục D). Vượt tồn kho kiểm thêm trong QuanSim vì kho có thể đến từ --inventory."""
    menu = tuning["menu"]
    patience_max = int(round(tuning["quan"]["patience_s"] * 60))
    eat_max = int(round(tuning["quan"]["eat_s"] * 60))
    holders = {}  # order_id -> số món đang giữ trên bếp + tay
    for s in b.get("stoves", []):
        dish = s.get("dish")
        if dish is not None:
            if not isinstance(dish, dict) or not isinstance(dish.get("order_id"), str):
                raise BadInput(f"stoves.{s['id']}.dish phải có order_id")
            holders[dish["order_id"]] = holders.get(dish["order_id"], 0) + 1
    hand = b.get("hand")
    if hand is not None:
        if not isinstance(hand, dict) or not isinstance(hand.get("order_id"), str):
            raise BadInput("hand phải là null hoặc object có order_id")
        holders[hand["order_id"]] = holders.get(hand["order_id"], 0) + 1
    if any(n > 1 for n in holders.values()):
        raise BadInput("bếp và tay (hoặc hai bếp) cùng giữ món của một đơn")
    held = {}
    cids = set()
    for c in b.get("customers", []):
        cid = c["id"]
        cids.add(cid)
        extra = set(c) - CUSTOMER_KEYS
        if extra:
            raise BadInput(f"customers.{cid}: trường lạ {sorted(extra)}")
        state = c.get("state", "waiting")
        status = c.get("order_status", "reserved")
        if state not in CUSTOMER_STATES:
            raise BadInput(f"customers.{cid}.state phải là một trong {CUSTOMER_STATES}")
        if status not in ORDER_STATUSES:
            raise BadInput(f"customers.{cid}.order_status phải là một trong {ORDER_STATUSES}")
        dish_id = c.get("dish_id")
        if status != "unfulfillable" and dish_id not in menu:
            raise BadInput(f"customers.{cid}.dish_id không có trong menu: {dish_id!r}")
        if dish_id is not None and dish_id not in menu:
            raise BadInput(f"customers.{cid}.dish_id không có trong menu: {dish_id!r}")
        if (state == "eating") != (status == "served"):
            raise BadInput(f"customers.{cid}: eating khi và chỉ khi order_status là served")
        for key in ("order_tick", "patience_ticks_left", "eat_ticks_left", "base_price", "tip"):
            if key in c:
                _nonneg_int(f"customers.{cid}.{key}", c[key])
        if c.get("patience_ticks_left", 0) > patience_max:
            raise BadInput(f"customers.{cid}.patience_ticks_left vượt kiên nhẫn tối đa")
        if c.get("eat_ticks_left", 0) > eat_max:
            raise BadInput(f"customers.{cid}.eat_ticks_left vượt thời gian ăn")
        if state == "eating" and c.get("eat_ticks_left", 0) < 1:
            raise BadInput(f"customers.{cid}: khách eating cần eat_ticks_left >= 1")
        if "base_price" in c and dish_id in menu and c["base_price"] != menu[dish_id]["price"]:
            raise BadInput(f"customers.{cid}.base_price khác giá món")
        if "reserved" in c:
            validate_items(c["reserved"])
            reserved = {k: v for k, v in c["reserved"].items() if v > 0}
        else:
            reserved = dict(menu[dish_id]["recipe"]) if status == "reserved" else {}
        if status == "reserved" and reserved != menu[dish_id]["recipe"]:
            raise BadInput(f"customers.{cid}.reserved khác công thức {dish_id}")
        if status != "reserved" and reserved:
            raise BadInput(f"customers.{cid}: chỉ đơn reserved mới được giữ nguyên liệu")
        n_dish = holders.get(cid, 0)
        if status == "assigned" and n_dish != 1:
            raise BadInput(f"customers.{cid}: đơn assigned phải có đúng một món trên bếp hoặc trên tay")
        if status != "assigned" and n_dish:
            raise BadInput(f"customers.{cid}: chỉ đơn assigned mới có món trên bếp/tay")
        for k, n in reserved.items():
            held[k] = held.get(k, 0) + n
    orphans = set(holders) - cids
    if orphans:
        raise BadInput(f"món trên bếp/tay thuộc đơn không có khách: {sorted(orphans)}")
    if "stock" in b:
        for k, n in held.items():
            if n > b["stock"].get(k, 0):
                raise BadInput(f"khách giữ {n} {k} vượt tồn kho")
