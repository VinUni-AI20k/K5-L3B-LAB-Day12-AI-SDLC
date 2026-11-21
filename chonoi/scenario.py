"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json
import math

from .errors import BadInput
from .ids import id_key
from .inventory import KINDS_V11, fresh_to_units, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "monsters", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
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


def validate_day_scenario(data, tuning):
    """Kiểm tra khối scenario cho mode day (day, gather, quan) và chuẩn hóa kế hoạch D1-D5."""
    if not isinstance(data, dict):
        raise BadInput("scenario day phải là object")
    extra_root = set(data) - {"day", "gather", "quan"}
    if extra_root:
        raise BadInput(f"scenario day chỉ nhận khóa day/gather/quan, thừa: {sorted(extra_root)}")

    dcfg = data.get("day", {})
    if not isinstance(dcfg, dict):
        raise BadInput("khối day phải là object")
    extra_day = set(dcfg) - {"money", "earned", "reputation", "upgrades", "day_plan"}
    if extra_day:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra_day)}")

    if ("money" in dcfg) != ("earned" in dcfg):
        raise BadInput("day: phải khai cả money và earned khi đặt tiền đầu kỳ")
    if "money" in dcfg:
        _nonneg_int("day.money", dcfg["money"])
        _nonneg_int("day.earned", dcfg["earned"])
        if dcfg["money"] > dcfg["earned"]:
            raise BadInput("day: bắt buộc 0 <= money <= earned")

    qt = tuning["quan"]
    if "reputation" in dcfg:
        rep = dcfg["reputation"]
        if not _num(rep) or not (qt["reputation_min"] <= rep <= qt["reputation_max"]):
            raise BadInput("day.reputation ngoài miền tuning")

    shop_up = tuning["shop"]["upgrades"]
    if "upgrades" in dcfg:
        up = dcfg["upgrades"]
        if not isinstance(up, dict):
            raise BadInput("day.upgrades phải là object")
        for uk, lv in up.items():
            if uk not in shop_up:
                raise BadInput(f"day.upgrades: nâng cấp lạ {uk!r}")
            _nonneg_int(f"day.upgrades.{uk}", lv)
            max_lv = len(shop_up[uk])
            if lv > max_lv:
                raise BadInput(f"day.upgrades.{uk} vượt tối đa {max_lv}")

    plans = {
        int(p["day"]): {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])}
        for p in tuning["day_plan"]
    }
    menu = tuning["menu"]
    seen_days = set()
    for entry in dcfg.get("day_plan", []):
        if not isinstance(entry, dict):
            raise BadInput("day.day_plan[] phải là object")
        extra_p = set(entry) - {"day", "dishes", "ingredients"}
        if extra_p:
            raise BadInput(f"day.day_plan[]: trường lạ {sorted(extra_p)}")
        dn = entry.get("day")
        if isinstance(dn, bool) or not isinstance(dn, int) or not (1 <= dn <= 5) or dn in seen_days:
            raise BadInput(f"day.day_plan: day phải là số nguyên 1..5 duy nhất, đang là {dn!r}")
        seen_days.add(dn)
        dishes = entry.get("dishes")
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"day.day_plan[{dn}].dishes phải là object không rỗng")
        ing = {}
        for did, cnt in dishes.items():
            if did not in menu:
                raise BadInput(f"day.day_plan[{dn}]: món lạ {did!r}")
            _pos_int(f"day.day_plan[{dn}].dishes.{did}", cnt)
            for k, amt in menu[did]["recipe"].items():
                ing[k] = ing.get(k, 0) + amt * cnt
        if "ingredients" in entry and entry["ingredients"] != ing:
            raise BadInput(f"day.day_plan[{dn}].ingredients không khớp công thức")
        plans[dn] = {"dishes": dict(dishes), "ingredients": ing}

    g_block = data.get("gather", {})
    if not isinstance(g_block, dict):
        raise BadInput("khối gather phải là object")
    extra_g = set(g_block) - GATHER_KEYS
    if extra_g:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather: {sorted(extra_g)}")
    _validate_gather(g_block, tuning)

    q_block = data.get("quan", {})
    if not isinstance(q_block, dict):
        raise BadInput("khối quan phải là object")
    if "stock" in q_block or "reputation" in q_block:
        raise BadInput("cấm dùng quan.stock hoặc quan.reputation khi chạy day")
    validate_quan_state(q_block, tuning, stock_map=None)

    return dcfg, g_block, q_block, plans


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if mode == "day":
        validate_day_scenario(data, tuning)
        return data
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
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
    if "time_left_ticks" in b:
        _pos_int("gather.time_left_ticks", b["time_left_ticks"])
        if b["time_left_ticks"] > round(g["duration_s"] * tuning["tick_hz"]):
            raise BadInput("gather.time_left_ticks vượt thời lượng pha")
    if "hold" in b:
        h = b["hold"]
        validate_items(h, KINDS_V11, spoiled_below=tuning["freshness"]["spoiled_below"])
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
    species = g["monsters"]["species"]
    for m in b.get("monsters", []):
        mid = m["id"]
        allowed_m = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
        if set(m) - allowed_m:
            raise BadInput(f"monsters.{mid}: trường lạ {sorted(set(m) - allowed_m)}")
        kind = m.get("kind")
        if kind not in species:
            raise BadInput(f"monsters.{mid}: kind lạ {kind!r}")
        dlo, dhi = species[kind]["depths"]
        _pos(f"monsters.{mid}.pos", m.get("pos"), bounds)
        if not (dlo <= m["pos"][1] <= dhi):
            raise BadInput(f"monsters.{mid}.pos.d phải trong [{dlo}, {dhi}]")
        wps = m.get("waypoints")
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"monsters.{mid}.waypoints phải gồm 2 điểm")
        for idx, wp in enumerate(wps):
            _pos(f"monsters.{mid}.waypoints[{idx}]", wp, bounds)
            if not (dlo <= wp[1] <= dhi):
                raise BadInput(f"monsters.{mid}.waypoints[{idx}].d ngoài vùng loài")
        tidx = m.get("target_idx", 1)
        if isinstance(tidx, bool) or tidx not in (0, 1):
            raise BadInput(f"monsters.{mid}.target_idx phải là 0 hoặc 1")
        st = m.get("state", "patrol")
        if st not in ("patrol", "chase", "recoil"):
            raise BadInput(f"monsters.{mid}.state không hợp lệ: {st!r}")
        stl = m.get("state_ticks_left", 0)
        _nonneg_int(f"monsters.{mid}.state_ticks_left", stl)
        rdir = m.get("recoil_dir", None)
        if st == "recoil":
            if stl <= 0:
                raise BadInput(f"monsters.{mid}: recoil phải có state_ticks_left > 0")
            if not (isinstance(rdir, list) and len(rdir) == 2 and all(_num(c) for c in rdir) and abs(math.hypot(rdir[0], rdir[1]) - 1.0) <= 1e-3):
                raise BadInput(f"monsters.{mid}.recoil_dir phải là vector đơn vị")
        else:
            if stl != 0 or rdir is not None:
                raise BadInput(f"monsters.{mid}: trạng thái {st} không có recoil_dir hoặc state_ticks_left > 0")


def _pos_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
        raise BadInput(f"{name} phải là số nguyên dương")


def _validate_dish_payload(name, dish, menu):
    if not isinstance(dish, dict):
        raise BadInput(f"{name}: payload món phải là object")
    req = {"order_id", "dish_id", "base_price"}
    if set(dish) != req:
        raise BadInput(f"{name}: payload món phải có đúng {sorted(req)}")
    if not isinstance(dish["order_id"], str) or not dish["order_id"]:
        raise BadInput(f"{name}.order_id phải là chuỗi không rỗng")
    if not isinstance(dish["dish_id"], str) or dish["dish_id"] not in menu:
        raise BadInput(f"{name}.dish_id ngoài menu: {dish['dish_id']!r}")
    _pos_int(f"{name}.base_price", dish["base_price"])
    return dish["order_id"], dish["dish_id"]


def _validate_reserved_ids(name, r):
    if not isinstance(r, list):
        raise BadInput(f"{name}.reserved phải là mảng id cá thể")
    seen = set()
    out = []
    for iid in r:
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"{name}.reserved: id nguyên liệu phải là chuỗi không rỗng")
        if iid in seen:
            raise BadInput(f"{name}.reserved: trùng id {iid!r}")
        seen.add(iid)
        out.append(iid)
    return out


def validate_quan_state(b, tuning, stock_map=None):
    """Kiểm tra toàn bộ scenario/fixture quán theo PRD-0 + v1.2 và chuẩn hóa reserved theo id."""
    from collections import Counter

    qt = tuning["quan"]
    menu = tuning["menu"]
    kinds = set(KINDS_V11)
    spoil_th = float(tuning["freshness"]["spoiled_below"])
    spoil_u = fresh_to_units(spoil_th, spoil_th)
    tick_hz = tuning["tick_hz"]
    dur_ticks = round(qt["duration_s"] * tick_hz)
    qb = qt["bounds"]

    if not isinstance(b, dict):
        raise BadInput("quan phải là object")
    extra = set(b) - QUAN_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong quan: {sorted(extra)}")
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("quan.random_customers phải là bool")
    if "time_left_ticks" in b:
        _pos_int("quan.time_left_ticks", b["time_left_ticks"])
        if b["time_left_ticks"] > dur_ticks:
            raise BadInput("quan.time_left_ticks vượt thời lượng pha")
    if "reputation" in b:
        rep = b["reputation"]
        if not _num(rep) or not (qt["reputation_min"] <= rep <= qt["reputation_max"]):
            raise BadInput("quan.reputation ngoài miền tuning")

    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])

    if "stock" in b:
        validate_items(b["stock"], kinds=KINDS_V11, spoiled_below=spoil_th)

    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")

    known_stoves = {s["id"]: s for s in qt["stoves"]}
    slot_orders = {}
    for st in b.get("stoves", []):
        sid = st["id"]
        if sid not in known_stoves:
            raise BadInput(f"stoves.{sid}: id bếp không tồn tại trong tuning")
        allowed_st = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
        if set(st) - allowed_st:
            raise BadInput(f"stoves.{sid}: trường lạ {sorted(set(st) - allowed_st)}")
        if "pos" in st:
            _pos(f"stoves.{sid}.pos", st["pos"], qb, axes=("x", "z"))
        state = st.get("state", "idle")
        if state not in ("idle", "cooking", "ready"):
            raise BadInput(f"stoves.{sid}.state không hợp lệ: {state!r}")
        dish = st.get("dish")
        cook_left = st.get("cook_ticks_left", 0)
        ready_t = st.get("ready_ticks", 0)
        _nonneg_int(f"stoves.{sid}.cook_ticks_left", cook_left)
        _nonneg_int(f"stoves.{sid}.ready_ticks", ready_t)
        if state == "idle":
            if dish is not None or cook_left != 0 or ready_t != 0:
                raise BadInput(f"stoves.{sid}: bếp idle không được giữ món hoặc timer dương")
        elif state == "cooking":
            oid, did = _validate_dish_payload(f"stoves.{sid}.dish", dish, menu)
            if cook_left <= 0 or ready_t != 0:
                raise BadInput(f"stoves.{sid}: bếp cooking phải có cook_ticks_left > 0 và ready_ticks == 0")
            if oid in slot_orders:
                raise BadInput(f"trùng order_id {oid!r} trên nhiều bếp/tay")
            slot_orders[oid] = did
        else:
            oid, did = _validate_dish_payload(f"stoves.{sid}.dish", dish, menu)
            if cook_left != 0:
                raise BadInput(f"stoves.{sid}: bếp ready phải có cook_ticks_left == 0")
            if oid in slot_orders:
                raise BadInput(f"trùng order_id {oid!r} trên nhiều bếp/tay")
            slot_orders[oid] = did

    if b.get("hand") is not None:
        oid, did = _validate_dish_payload("quan.hand", b["hand"], menu)
        if oid in slot_orders:
            raise BadInput(f"trùng order_id {oid!r} giữa bếp và tay")
        slot_orders[oid] = did

    known_tables = {t["id"] for t in qt["tables"]}
    for tb in b.get("tables", []):
        tid = tb["id"]
        if tid not in known_tables:
            raise BadInput(f"tables.{tid}: id bàn không tồn tại trong tuning")
        if set(tb) - {"id", "pos"}:
            raise BadInput(f"tables.{tid}: trường lạ {sorted(set(tb) - {'id', 'pos'})}")
        if "pos" in tb:
            _pos(f"tables.{tid}.pos", tb["pos"], qb, axes=("x", "z"))

    custs = b.get("customers", [])
    allowed_c = {
        "id", "table_id", "dish_id", "order_tick", "state",
        "patience_ticks_left", "eat_ticks_left", "order_status",
        "reserved", "base_price", "tip",
    }
    seen_tables = set()
    assigned_seen = set()
    explicit_reserved = []
    seen_res_ids = set()
    need_auto_reserve = []
    for c in custs:
        cid = c["id"]
        if set(c) - allowed_c:
            raise BadInput(f"customers.{cid}: trường lạ {sorted(set(c) - allowed_c)}")
        tid = c.get("table_id")
        if not isinstance(tid, str) or tid not in known_tables:
            raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
        if tid in seen_tables:
            raise BadInput("hai khách cùng bàn")
        seen_tables.add(tid)

        did = c.get("dish_id")
        if not isinstance(did, str) or did not in menu:
            raise BadInput(f"customers.{cid}: dish_id không hợp lệ: {did!r}")
        otick = c.get("order_tick", 0)
        _nonneg_int(f"customers.{cid}.order_tick", otick)
        cstate = c.get("state", "waiting")
        if cstate not in ("waiting", "eating"):
            raise BadInput(f"customers.{cid}.state không hợp lệ: {cstate!r}")
        pat = c.get("patience_ticks_left", round(qt["patience_s"] * tick_hz))
        eat = c.get("eat_ticks_left", 0)
        _nonneg_int(f"customers.{cid}.patience_ticks_left", pat)
        _nonneg_int(f"customers.{cid}.eat_ticks_left", eat)
        ostatus = c.get("order_status", "reserved")
        if ostatus not in ("reserved", "assigned", "unfulfillable", "served"):
            raise BadInput(f"customers.{cid}.order_status không hợp lệ: {ostatus!r}")

        if cstate == "eating":
            if ostatus != "served" or eat <= 0:
                raise BadInput(f"customers.{cid}: khách eating phải served và có eat_ticks_left > 0")
            if cid in slot_orders:
                raise BadInput(f"customers.{cid}: khách eating không được còn món ở bếp/tay")
            if "reserved" in c and c["reserved"] != []:
                raise BadInput(f"customers.{cid}: khách eating phải có reserved rỗng []")
            if "base_price" not in c or "tip" not in c:
                raise BadInput(f"customers.{cid}: khách eating phải chốt base_price và tip")
            _pos_int(f"customers.{cid}.base_price", c["base_price"])
            _nonneg_int(f"customers.{cid}.tip", c["tip"])
        else:
            if eat != 0:
                raise BadInput(f"customers.{cid}: khách waiting phải có eat_ticks_left == 0")
            if ostatus == "served":
                raise BadInput(f"customers.{cid}: khách waiting không thể served")
            if "base_price" in c and c["base_price"] != 0:
                _pos_int(f"customers.{cid}.base_price", c["base_price"])
            if "tip" in c:
                _nonneg_int(f"customers.{cid}.tip", c["tip"])
            if ostatus == "assigned":
                if cid not in slot_orders or slot_orders[cid] != did:
                    raise BadInput(f"customers.{cid}: đơn assigned phải khớp đúng một món ở bếp hoặc tay")
                if "reserved" in c and c["reserved"] != []:
                    raise BadInput(f"customers.{cid}: đơn assigned phải có reserved rỗng []")
                assigned_seen.add(cid)
            elif ostatus == "unfulfillable":
                if cid in slot_orders:
                    raise BadInput(f"customers.{cid}: đơn unfulfillable không được có món ở bếp/tay")
                if "reserved" in c and c["reserved"] != []:
                    raise BadInput(f"customers.{cid}: đơn unfulfillable phải có reserved rỗng []")
            else:  # reserved
                if cid in slot_orders:
                    raise BadInput(f"customers.{cid}: đơn reserved không được có món ở bếp/tay")
                recipe = menu[did]["recipe"]
                if "reserved" in c:
                    rids = _validate_reserved_ids(f"customers.{cid}", c["reserved"])
                    for iid in rids:
                        if iid in seen_res_ids:
                            raise BadInput(f"dùng chung nguyên liệu giữ chỗ {iid!r}")
                        seen_res_ids.add(iid)
                    explicit_reserved.append((cid, did, rids))
                else:
                    need_auto_reserve.append((otick, id_key(tid), cid, dict(recipe)))

    orphan = set(slot_orders) - assigned_seen
    if orphan:
        raise BadInput(f"món trên bếp/tay không gắn với khách assigned: {sorted(orphan)}")

    check_stock = stock_map if stock_map is not None else b.get("stock")
    if check_stock is not None:
        norm_stock = validate_items(check_stock, kinds=KINDS_V11, spoiled_below=spoil_th)
        by_id = {it["id"]: it for it in norm_stock}
        for cid, did, rids in explicit_reserved:
            recipe = menu[did]["recipe"]
            counts = Counter()
            for iid in rids:
                it = by_id.get(iid)
                if it is None:
                    raise BadInput(f"customers.{cid}: thiếu nguyên liệu {iid!r} trong kho")
                if it["fresh_u"] < spoil_u:
                    raise BadInput(f"customers.{cid}: không được giữ chỗ nguyên liệu đã ươn {iid!r}")
                counts[it["kind"]] += 1
            if dict(counts) != recipe:
                raise BadInput(f"customers.{cid}: reserved khác công thức món {did}")

        avail = [it for it in norm_stock if it["id"] not in seen_res_ids and it["fresh_u"] >= spoil_u]
        need_auto_reserve.sort(key=lambda item: (item[0], item[1]))
        resolved = {}
        for _, _, cid, recipe in need_auto_reserve:
            picked = []
            for k, amt in sorted(recipe.items()):
                cands = [it for it in avail if it["kind"] == k]
                cands.sort(key=lambda it: (-it["fresh_u"], id_key(it["id"])))
                if len(cands) < amt:
                    raise BadInput(f"customers.{cid}: thiếu tồn kho tươi {k} để giữ chỗ")
                chosen = cands[:amt]
                chosen_ids = {it["id"] for it in chosen}
                avail = [it for it in avail if it["id"] not in chosen_ids]
                picked.extend(chosen_ids)
            resolved[cid] = sorted(picked, key=id_key)
        return resolved
    return {}


def _validate_quan(b, tuning):
    validate_quan_state(b, tuning, stock_map=b.get("stock") if "stock" in b else None)
