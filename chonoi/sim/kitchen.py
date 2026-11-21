"""Lát 4A — Bếp & Bưng món (`kitchen`): đếm giờ nấu, chín món, cháy món, bắt đầu nấu và lấy món lên tay."""

import math

from ..ids import id_key, sort_by_id

TICK = 60.0

# Sáng tạo (chỉ dùng cho UI/thoại, không ảnh hưởng logic/snapshot headless):
DISH_QUOTES = {
    "ca_loc_nuong_trui": "Má Tư: \"Cá lóc đồng nướng trui rơm thơm lừng, trở đều tay kẻo khét nghen Út!\"",
    "goi_bong_sung": "Má Tư: \"Bông súng giòn rụm trộn nước mắm me chua ngọt là hết sẩy!\"",
    "lau_ca_linh_dien_dien": "Má Tư: \"Mùa nước nổi có nồi lẩu cá linh bông điên điển là khách thương nhớ hoài!\"",
    "canh_chua_ca_loc": "Má Tư: \"Canh chua cá lóc bông điên điển thanh mát, nêm vừa miệng nghen con!\"",
    "ca_keo_nuong": "Má Tư: \"Cá kèo nướng muối ớt xèo xèo trên than hồng là bắt cơm lắm à!\"",
    "lau_mam": "Má Tư: \"Nồi lẩu mắm miền Tây đủ vị cá linh, cá kèo, kèo nèo mới đúng bài!\"",
}


def kitchen_story_note(stoves, hand) -> str:
    """Trả về lời thoại Nam Bộ theo trạng thái bếp (tắt ở headless, chỉ phục vụ hiển thị)."""
    if hand is not None:
        return "Út Sen: \"Món nóng hổi rồi, bưng ra bàn cho khách lẹ tay thôi!\""
    for s in sort_by_id(stoves):
        if s["state"] == "ready" and s.get("dish"):
            return "Má Tư: \"Chín tới rồi Út ơi, nhấc xuống bưng ra cho khách kẻo nguội!\""
        if s["state"] == "cooking" and s.get("dish"):
            return DISH_QUOTES.get(s["dish"]["dish_id"], "Má Tư: \"Giữ lửa than củi tràm đều tay nghen con!\"")
    return "Má Tư: \"Bếp than hồng sẵn sàng rồi, chờ khách gọi món là lên lửa liền!\""


def _available_stock(sim) -> dict:
    avail = dict(sim.stock)
    for c in sim.customers:
        for k, q in c.get("reserved", {}).items():
            avail[k] = avail.get(k, 0) - q
    return avail


def _re_reserve_v12(sim, customer, recipe, spoiled_below):
    """Giữ lại cá thể tươi nhất (chưa ươn, hòa theo id) cho `customer` khi dùng kho cá thể v1.2."""
    taken = {iid for c in sim.customers if c is not customer for iid in c.get("reserved", [])}
    picked_ids = []
    for kind in sorted(recipe.keys()):
        need = recipe[kind]
        cands = [
            it for it in sim.stock
            if it["kind"] == kind and it["id"] not in taken and it["fresh"] >= spoiled_below
        ]
        if len(cands) < need:
            customer["order_status"] = "unfulfillable"
            customer["reserved"] = []
            return
        cands.sort(key=lambda it: (-it["fresh"], id_key(it["id"])))
        for it in cands[:need]:
            picked_ids.append(it["id"])
            taken.add(it["id"])
    customer["order_status"] = "reserved"
    customer["reserved"] = picked_ids


def step_stoves(sim, events):
    """Cập nhật bộ đếm bếp đầu bước, chuyển chín (`dish_ready`) và xử lý cháy món nếu bật `burn_s`."""
    for s in sort_by_id(sim.stoves):
        if s["state"] == "cooking":
            s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
        elif s["state"] == "ready":
            s["ready_ticks"] += 1

    for s in sort_by_id(sim.stoves):
        if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
            s["state"] = "ready"
            s["ready_ticks"] = 0
            events.append(("dish_ready", {
                "stove_id": s["id"],
                "order_id": s["dish"]["order_id"],
                "dish_id": s["dish"]["dish_id"],
            }))

    burn_s = sim.t.get("burn_s")
    if burn_s is not None:
        burn_ticks = int(round(burn_s * TICK))
        spoiled_below = float(getattr(sim, "freshness", {}).get("spoiled_below", 30))
        for s in sort_by_id(sim.stoves):
            if s["state"] == "ready" and s["ready_ticks"] > burn_ticks:
                dish = s["dish"]
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0
                c = next((x for x in sim.customers if x["id"] == dish["order_id"]), None)
                new_status = "unfulfillable"
                if c is not None:
                    if c.get("reservation_id") is not None:
                        c["order_status"] = "failed"
                        c["reserved"] = [] if isinstance(sim.stock, list) else {}
                    else:
                        recipe = sim.menu[dish["dish_id"]]["recipe"]
                        if isinstance(sim.stock, list):
                            _re_reserve_v12(sim, c, recipe, spoiled_below)
                        else:
                            avail = _available_stock(sim)
                            if all(avail.get(k, 0) >= q for k, q in recipe.items()):
                                c["order_status"] = "reserved"
                                c["reserved"] = dict(recipe)
                            else:
                                c["order_status"] = "unfulfillable"
                                c["reserved"] = {}
                    new_status = c["order_status"]
                events.append(("dish_burnt", {
                    "stove_id": s["id"],
                    "order_id": dish["order_id"],
                    "dish_id": dish["dish_id"],
                    "order_status": new_status,
                }))


def interact_stove(sim, stove, events):
    """Tương tác với bếp: bếp `idle` nhận đơn `reserved` cũ nhất, bếp `ready` giao lên tay trống."""
    if stove["state"] == "idle":
        waiting_res = [
            c for c in sim.customers
            if c["state"] in ("waiting", "waiting_dish") and c["order_status"] == "reserved"
        ]
        if not waiting_res:
            return
        waiting_res.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        c = waiting_res[0]
        listed_price = int(sim.menu[c["dish_id"]]["price"])
        if isinstance(sim.stock, list):
            res_ids = set(c["reserved"])
            used_items = [it for it in sim.stock if it["id"] in res_ids]
            sim.stock = [it for it in sim.stock if it["id"] not in res_ids]
            items_used = sorted(used_items, key=lambda it: (it["kind"], id_key(it["id"])))
            avg_fresh = sum(it["fresh"] for it in items_used) / len(items_used) if items_used else 100.0
            base_price = int(math.floor(listed_price * avg_fresh / 100.0))
            if c.get("reservation_id") is not None:
                mult = float(getattr(sim, "reservation_price_multiplier", 1.5))
                base_price = int(math.floor(base_price * mult))
            c["reserved"] = []
        else:
            items_used = []
            for k in sorted(c["reserved"].keys()):
                qty = c["reserved"][k]
                sim.stock[k] = sim.stock.get(k, 0) - qty
                if sim.stock[k] <= 0:
                    sim.stock.pop(k, None)
                items_used.extend([k] * qty)
            c["reserved"] = {}
            base_price = listed_price
        c["order_status"] = "assigned"
        stove["state"] = "cooking"
        stove["dish"] = {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": base_price}
        stove["cook_ticks_left"] = int(round(sim.menu[c["dish_id"]]["cook_s"] * TICK))
        stove["ready_ticks"] = 0
        events.append(("cook_started", {
            "stove_id": stove["id"],
            "order_id": c["id"],
            "dish_id": c["dish_id"],
            "items": items_used,
            "base_price": base_price,
        }))
    elif stove["state"] == "ready" and sim.hand is None:
        dish = stove["dish"]
        sim.hand = dish
        stove["state"] = "idle"
        stove["dish"] = None
        stove["cook_ticks_left"] = 0
        stove["ready_ticks"] = 0
        events.append(("dish_picked", {
            "stove_id": stove["id"],
            "order_id": dish["order_id"],
            "dish_id": dish["dish_id"],
        }))
