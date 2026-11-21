"""Module Lát 4: Dịch vụ quán ăn (chonoi/sim/quan_service.py).

Bếp nấu, bưng bê, phục vụ khách, tính tiền/boa, cập nhật uy tín, đóng ca
theo PRD-0 và Test Contract.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from ..ids import id_key, sort_by_id

TICK = 60.0


def get_order_id(customer: dict) -> str:
    """Lấy order_id của khách (ưu tiên 'order_id', fallback sang 'id')."""
    return customer.get("order_id") or customer.get("id", "")


def compute_score(earned: int, reputation: float, mult: int = 100) -> int:
    """Công thức tính score chuẩn: score = earned + mult * floor(reputation)."""
    return int(earned + mult * math.floor(reputation))


def advance_stoves_and_eating(sim: Any) -> List[Tuple[str, dict]]:
    """Bước 1 & 2:
    - Giảm cook_ticks_left của các bếp đang nấu; khi về 0 chuyển sang ready, dish_ready, ready_ticks = 0.
    - Tăng ready_ticks cho các món ĐÃ READY Ở ĐẦU BƯỚC.
    - Giảm eat_ticks_left cho các khách đang ăn (state == 'eating').
    """
    events: List[Tuple[str, dict]] = []

    # 1. Ghi nhận các bếp đã ready ở đầu bước
    stoves_ready_at_start = {
        s["id"] for s in sim.stoves if s.get("state") == "ready"
    }

    # 2. Xử lý các bếp nấu / ready theo id tăng dần
    for stove in sort_by_id(sim.stoves):
        state = stove.get("state", "idle")
        if state == "cooking":
            stove["cook_ticks_left"] = max(0, stove.get("cook_ticks_left", 0) - 1)
            if stove["cook_ticks_left"] == 0:
                stove["state"] = "ready"
                stove["ready_ticks"] = 0
                events.append((
                    "dish_ready",
                    {
                        "stove_id": stove["id"],
                        "order_id": stove.get("order_id"),
                        "dish_id": stove.get("dish"),
                    },
                ))
        elif state == "ready":
            if stove["id"] in stoves_ready_at_start:
                stove["ready_ticks"] = stove.get("ready_ticks", 0) + 1

    # 3. Giảm timer ăn của khách đang ăn
    for customer in sim.customers:
        if customer.get("state") == "eating":
            customer["eat_ticks_left"] = max(0, customer.get("eat_ticks_left", 0) - 1)

    return events


def find_interact_target(sim: Any) -> Optional[dict]:
    """Tìm đối tượng tương tác tốt nhất trong interact_radius.

    Ưu tiên:
      1. Khoảng cách gần nhất.
      2. Nếu bằng nhau: ưu tiên bếp trước bàn (type 0: stove, type 1: table).
      3. Nếu cùng loại: sắp theo id tăng dần (id_key).
    Trả về dict target chứa thông tin loại và entity, hoặc None nếu không có đối tượng nào.
    """
    interact_radius = sim.t.get("interact_radius", 1.5)
    candidates = []

    # Quét bếp
    for stove in sim.stoves:
        d = math.dist(sim.pos, stove["pos"])
        if d <= interact_radius:
            candidates.append((d, 0, id_key(stove["id"]), "stove", stove))

    # Quét bàn
    for table in sim.tables:
        d = math.dist(sim.pos, table["pos"])
        if d <= interact_radius:
            candidates.append((d, 1, id_key(table["id"]), "table", table))

    if not candidates:
        return None

    # Sắp xếp theo đúng thứ tự ưu tiên
    candidates.sort(key=lambda c: (c[0], c[1], c[2]))
    _, _, _, target_type, entity = candidates[0]
    return {"type": target_type, "entity": entity}


def handle_interact(sim: Any, inp: Optional[Any] = None) -> List[Tuple[str, dict]]:
    """Bước 4: Xử lý interact.
    Tối đa xử lý 1 đối tượng mỗi bước.
    Nếu đối tượng được chọn không thỏa mãn điều kiện tương tác: bỏ lượt ngay, không thử đối tượng khác.
    """
    if inp is not None and not inp.pressed("interact"):
        return []

    events: List[Tuple[str, dict]] = []
    target = find_interact_target(sim)
    if target is None:
        return events

    target_type = target["type"]
    entity = target["entity"]

    if target_type == "stove":
        stove = entity
        state = stove.get("state", "idle")

        if state == "idle":
            # Bếp idle: lấy đơn reserved cũ nhất (order_tick nhỏ nhất -> table_id nhỏ nhất)
            reserved_customers = [
                c for c in sim.customers
                if c.get("state") == "waiting" and c.get("order_status", "reserved") == "reserved"
            ]
            if not reserved_customers:
                # Không có đơn reserved -> bỏ lượt
                return events

            reserved_customers.sort(
                key=lambda c: (c.get("order_tick", 0), id_key(c.get("table_id", "")))
            )
            customer = reserved_customers[0]
            dish_id = customer.get("dish_id")
            if not dish_id or dish_id not in sim.menu:
                # Dữ liệu bất thường -> bỏ lượt
                return events

            menu_item = sim.menu[dish_id]
            recipe = menu_item.get("recipe", {})
            cook_s = menu_item.get("cook_s", 0)
            base_price = menu_item.get("price", 0)

            # Trừ đúng nguyên liệu từ kho stock
            # Tạo danh sách items sắp xếp alphabet
            items: List[str] = []
            for kind, count in recipe.items():
                items.extend([kind] * count)
                sim.stock[kind] = sim.stock.get(kind, 0) - count
                if sim.stock[kind] <= 0:
                    sim.stock.pop(kind, None)
            items.sort()

            # Cập nhật trạng thái đơn khách
            customer["order_status"] = "assigned"
            customer["reserved"] = {}

            # Cập nhật bếp sang cooking
            order_id = get_order_id(customer)
            stove["state"] = "cooking"
            stove["dish"] = dish_id
            stove["order_id"] = order_id
            stove["base_price"] = base_price
            stove["cook_ticks_left"] = int(round(cook_s * TICK))
            stove["ready_ticks"] = 0

            events.append((
                "cook_started",
                {
                    "stove_id": stove["id"],
                    "order_id": order_id,
                    "dish_id": dish_id,
                    "items": items,
                    "base_price": base_price,
                },
            ))
            return events

        elif state == "ready":
            # Bếp ready: nếu tay trống -> bốc món
            if sim.hand is None:
                order_id = stove.get("order_id")
                dish_id = stove.get("dish")
                base_price = stove.get("base_price", sim.menu.get(dish_id, {}).get("price", 0))

                sim.hand = {
                    "order_id": order_id,
                    "dish_id": dish_id,
                    "base_price": base_price,
                }
                stove["state"] = "idle"
                stove["dish"] = None
                stove["order_id"] = None
                stove["cook_ticks_left"] = 0
                stove["ready_ticks"] = 0
                stove.pop("base_price", None)

                events.append((
                    "dish_picked",
                    {
                        "stove_id": stove["id"],
                        "order_id": order_id,
                        "dish_id": dish_id,
                    },
                ))
                return events
            else:
                # Tay bận -> bỏ lượt ngay
                return events

        else:
            # Bếp đang cooking -> bỏ lượt ngay
            return events

    elif target_type == "table":
        table = entity
        table_id = table["id"]

        # Điều kiện phục vụ:
        # - Tay đang cầm món
        # - Bàn có khách đúng order_id
        # - Khách đang ở trạng thái waiting
        if sim.hand is None:
            # Không cầm món -> bỏ lượt
            return events

        # Tìm khách tại bàn
        customer_at_table = None
        for c in sim.customers:
            if c.get("table_id") == table_id:
                customer_at_table = c
                break

        if customer_at_table is None:
            # Bàn không có khách -> bỏ lượt
            return events

        if customer_at_table.get("state") != "waiting":
            # Khách không ở trạng thái waiting -> bỏ lượt
            return events

        order_id = get_order_id(customer_at_table)
        if order_id != sim.hand.get("order_id"):
            # Món trên tay không khớp đơn khách -> bỏ lượt
            return events

        # Giao món thành công
        dish_id = sim.hand.get("dish_id")
        base_price = sim.hand.get("base_price", sim.menu.get(dish_id, {}).get("price", 0))
        sim.hand = None

        eat_s = sim.t.get("eat_s", 10)
        customer_at_table["state"] = "eating"
        customer_at_table["order_status"] = "served"
        customer_at_table["eat_ticks_left"] = int(round(eat_s * TICK))
        customer_at_table["base_price"] = base_price

        # Tính tip
        patience_max_ticks = max(1, int(round(sim.t.get("patience_s", 60) * TICK)))
        patience_ticks_left = customer_at_table.get("patience_ticks_left", 0)
        ratio = patience_ticks_left / patience_max_ticks
        tip_min_ratio = sim.t.get("tip_min_patience_ratio", 0.5)
        tip_rate = sim.t.get("tip_rate", 0.2)

        if ratio >= tip_min_ratio:
            tip = math.floor(base_price * tip_rate)
        else:
            tip = 0

        customer_at_table["tip"] = tip

        events.append((
            "served",
            {
                "order_id": order_id,
                "table_id": table_id,
                "dish_id": dish_id,
                "patience_ticks_left": patience_ticks_left,
                "base_price": base_price,
                "tip": tip,
            },
        ))
        return events

    return events


def handle_finished_eating(sim: Any) -> List[Tuple[str, dict]]:
    """Bước 5: Khách ăn xong -> phát paid ('finished_eating'), thu tiền, cộng uy tín, rời bàn."""
    events: List[Tuple[str, dict]] = []
    eating_customers = [
        c for c in sim.customers
        if c.get("state") == "eating" and c.get("eat_ticks_left", 0) <= 0
    ]
    if not eating_customers:
        return events

    # Theo id bàn tăng dần
    eating_customers.sort(key=lambda c: id_key(c.get("table_id", "")))

    rep_min = sim.t.get("reputation_min", 0.0)
    rep_max = sim.t.get("reputation_max", 5.0)
    tip_rep = sim.t.get("tip_reputation", 0.2)

    finished_ids = set()
    for c in eating_customers:
        order_id = get_order_id(c)
        table_id = c.get("table_id")
        base_price = c.get("base_price", 0)
        tip = c.get("tip", 0)
        amount = base_price + tip

        events.append((
            "paid",
            {
                "order_id": order_id,
                "table_id": table_id,
                "base_price": base_price,
                "tip": tip,
                "amount": amount,
                "reason": "finished_eating",
            },
        ))

        sim.money += amount
        sim.earned += amount
        sim.shift_earned += amount

        if tip > 0:
            sim.reputation += tip_rep
            sim.reputation = max(rep_min, min(rep_max, sim.reputation))

        finished_ids.add(c.get("id"))

    # Loại bỏ khách đã thanh toán khỏi quán
    sim.customers = [c for c in sim.customers if c.get("id") not in finished_ids]
    return events


def handle_closing(sim: Any) -> List[Tuple[str, dict]]:
    """Bước 7: Đóng ca (khi time_left_ticks <= 0).
    - Khách đang ăn (kể cả vừa giao): thanh toán đủ, paid với reason 'closing'.
    - Khách đang chờ: rời quán, customer_left với reason 'closing', không trừ uy tín.
    - Dọn dẹp khách.
    - Phát quan_end đúng 1 lần: {reason: 'time', money, earned, shift_earned, reputation}.
    """
    events: List[Tuple[str, dict]] = []
    if sim.time_left_ticks > 0:
        return events

    rep_min = sim.t.get("reputation_min", 0.0)
    rep_max = sim.t.get("reputation_max", 5.0)
    tip_rep = sim.t.get("tip_reputation", 0.2)

    # 1. Khách đang ăn thanh toán (theo id bàn)
    eating_customers = [c for c in sim.customers if c.get("state") == "eating"]
    eating_customers.sort(key=lambda c: id_key(c.get("table_id", "")))
    for c in eating_customers:
        order_id = get_order_id(c)
        table_id = c.get("table_id")
        base_price = c.get("base_price", 0)
        tip = c.get("tip", 0)
        amount = base_price + tip

        events.append((
            "paid",
            {
                "order_id": order_id,
                "table_id": table_id,
                "base_price": base_price,
                "tip": tip,
                "amount": amount,
                "reason": "closing",
            },
        ))

        sim.money += amount
        sim.earned += amount
        sim.shift_earned += amount

        if tip > 0:
            sim.reputation += tip_rep
            sim.reputation = max(rep_min, min(rep_max, sim.reputation))

    # 2. Khách đang chờ rời quán không trừ uy tín (theo id bàn)
    waiting_customers = [c for c in sim.customers if c.get("state") == "waiting"]
    waiting_customers.sort(key=lambda c: id_key(c.get("table_id", "")))
    for c in waiting_customers:
        order_id = get_order_id(c)
        table_id = c.get("table_id")
        events.append((
            "customer_left",
            {
                "order_id": order_id,
                "table_id": table_id,
                "reason": "closing",
                "reputation": sim.reputation,
            },
        ))

    # Dọn khách
    sim.customers.clear()

    # Dọn dẹp bếp và tay
    sim.hand = None
    for stove in sim.stoves:
        stove["state"] = "idle"
        stove["dish"] = None
        stove["order_id"] = None
        stove["cook_ticks_left"] = 0
        stove["ready_ticks"] = 0
        stove.pop("base_price", None)

    # Kết thúc ca
    if not sim.done:
        sim.done = True
        sim.reason = "time"
        events.append((
            "quan_end",
            {
                "reason": "time",
                "money": sim.money,
                "earned": sim.earned,
                "shift_earned": sim.shift_earned,
                "reputation": sim.reputation,
            },
        ))

    return events


def cancel_customer_order(sim: Any, order_id: str) -> None:
    """Helper cho Lát 3 khi khách rời vì hết kiên nhẫn:
    Bỏ món của đơn đang nấu/ready/trên tay nếu khớp order_id; nguyên liệu đã dùng không hoàn lại.
    """
    if sim.hand and sim.hand.get("order_id") == order_id:
        sim.hand = None

    for stove in sim.stoves:
        if stove.get("order_id") == order_id:
            stove["state"] = "idle"
            stove["dish"] = None
            stove["order_id"] = None
            stove["cook_ticks_left"] = 0
            stove["ready_ticks"] = 0
            stove.pop("base_price", None)
