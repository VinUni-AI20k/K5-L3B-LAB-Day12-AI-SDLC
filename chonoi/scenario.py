"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
Mâu thuẫn mức luật (PRD-0 mục D, 'Mâu thuẫn -> mã 2') nhóm kiểm trong luật, không ở đây:
`chonoi/sim/quan.py` `_load_customers` (giữ chỗ trỏ id không có trong kho / đã ươn / dùng chung) và
`_validate_state` (đơn assigned phải có đúng một món ở bếp hoặc tay, khách eating cần base_price + tip).
"""

import json

from .errors import BadInput
from .inventory import parse_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}
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


DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def load_scenario(path, mode: str, tuning: dict, days: int = 1) -> dict:
    """gather/quan: trả khối của mode. day: trả {"day","gather","quan"} (gather/quan là mẫu mỗi Ngày)."""
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    allowed_blocks = {"gather", "quan", "day"} if mode == "day" else {"gather", "quan"}
    if not isinstance(data, dict) or not set(data) <= allowed_blocks:
        raise BadInput(f"scenario chỉ được có khối {sorted(allowed_blocks)}")
    if mode != "day" and set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    for name, block in data.items():
        if not isinstance(block, dict):
            raise BadInput(f"khối {name} phải là object")
    if mode == "day":
        out = {k: data[k] for k in ("day", "gather", "quan") if k in data}
        q = out.get("quan", {})
        for banned in ("stock", "reputation"):
            if banned in q:
                raise BadInput(f"quan.{banned} bị cấm khi chạy day (dùng gather.hold / day.reputation)")
        if "gather" in out:
            _check_block(out["gather"], "gather", tuning)
        if "quan" in out:
            _check_block(q, "quan", tuning)
        _validate_day(out.get("day", {}), tuning, out.get("quan", {}), days)
        return out
    block = data.get(mode, {})
    _check_block(block, mode, tuning)
    return block


def _check_block(block, mode, tuning):
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
        from .sim.gather import validate_gather_scenario  # luật kiểm gather thuộc lát gather (v1.1)
        validate_gather_scenario(block, tuning)
    else:
        _validate_quan(block, tuning)


def _validate_day(d, tuning, quan_tpl, days):
    """Khối day (v1.1 mục 4.3): 0 <= money <= earned, uy tín trong dải, cấp hợp lệ, day_plan ghi đè."""
    from .sim.day import recipe_total
    extra = set(d) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    money, earned = d.get("money", 0), d.get("earned", 0)
    _nonneg_int("day.money", money)
    _nonneg_int("day.earned", earned)
    if money > earned:
        raise BadInput("day: cần 0 <= money <= earned (khai cả hai khi có tiền đầu kỳ)")
    q = tuning["quan"]
    if "reputation" in d:
        r = d["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput(f"day.reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")
    ups = d.get("upgrades", {})
    if not isinstance(ups, dict):
        raise BadInput("day.upgrades phải là object")
    for k, v in ups.items():
        if k not in ("oxygen", "hp"):
            raise BadInput(f"day.upgrades: nâng cấp không hỗ trợ {k}")
        levels = [lv["level"] for lv in tuning["shop"]["upgrades"][k]]
        if isinstance(v, bool) or not isinstance(v, int) or not (0 <= v <= max(levels)):
            raise BadInput(f"day.upgrades.{k} phải là cấp trong [0, {max(levels)}]")
    menu = tuning["menu"]
    plans = {p["day"]: p for p in tuning["day_plan"]}
    dp = d.get("day_plan", [])
    if not isinstance(dp, list):
        raise BadInput("day.day_plan phải là mảng {day,dishes[,ingredients]}")
    seen = set()
    for p in dp:
        if not isinstance(p, dict) or set(p) - {"day", "dishes", "ingredients"} or "dishes" not in p:
            raise BadInput("day.day_plan: mỗi mục là {day,dishes[,ingredients]}")
        n = p.get("day")
        if isinstance(n, bool) or not isinstance(n, int) or not (1 <= n <= 5) or n in seen:
            raise BadInput("day.day_plan: day phải là số nguyên 1..5, không trùng")
        seen.add(n)
        dishes = p["dishes"]
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"day.day_plan[{n}].dishes phải là map id món -> số nguyên dương")
        for k, v in dishes.items():
            if k not in menu or isinstance(v, bool) or not isinstance(v, int) or v <= 0:
                raise BadInput(f"day.day_plan[{n}].dishes: {k} phải là món có thật với số suất nguyên dương")
        if "ingredients" in p and p["ingredients"] != recipe_total(menu, dishes):
            raise BadInput(f"day.day_plan[{n}].ingredients khác tổng công thức × số suất")
        plans[n] = p
    # khách mẫu chỉ gọi món thuộc kế hoạch của mọi Ngày sẽ chạy (kho thực kiểm lúc mở quán)
    for c in quan_tpl.get("customers", []):
        for n in range(1, days + 1):
            if c.get("dish_id") not in plans[n]["dishes"]:
                raise BadInput(f"customers.{c.get('id')}: món {c.get('dish_id')} không thuộc kế hoạch Ngày {n}")


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


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        parse_items(b["stock"], where="quan.stock")  # v1.2: mảng cá thể {id,kind,fresh}
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
