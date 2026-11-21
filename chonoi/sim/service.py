
"""Module Service (Người B): Quản lý bàn ăn, phục vụ món, tiến trình ăn, thanh toán & uy tín.

Được thiết kế độc lập, có try-catch đầy đủ để phòng thủ lỗi khi chạy headless và hiển thị Web UI (live).

Quy ước tích hợp với QuanSim:
  1. Trong QuanSim.step(): gọi `events.extend(update_service(self))` mỗi tick.
  2. Khi phím E (interact) bấm gần bàn: gọi `events.extend(handle_table_interact(self, table))`.
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)
TICK = 60.0


def get_customer_at_table(sim: Any, table_id: str) -> Optional[Dict[str, Any]]:
    """Tìm an toàn khách hàng đang ngồi tại bàn `table_id`."""
    try:
        if not hasattr(sim, "customers") or not isinstance(sim.customers, list):
            return None
        for c in sim.customers:
            if isinstance(c, dict) and c.get("table_id") == table_id:
                return c
        return None
    except Exception as e:
        logger.error(f"[service] Lỗi khi tìm khách tại bàn {table_id}: {e}")
        return None


def handle_table_interact(sim: Any, table: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """Xử lý khi người chơi ấn 'interact' (phím E) tại một bàn ăn:
    
    - Kiểm tra người chơi có đang bưng món trên tay (`sim.hand`) không.
    - Kiểm tra bàn có khách đang chờ món (`state == 'waiting_dish'`) không.
    - So sánh món trên tay với món khách đã gọi (`dish` / `dish_id`).
    - Nếu khớp: đặt món lên bàn, sim.hand về None, khách chuyển sang 'eating'.
    - Bắn sự kiện: ('served', {'table_id': ..., 'customer_id': ..., 'dish': ...})
    """
    events: List[Tuple[str, Dict[str, Any]]] = []
    try:
        if not table or not isinstance(table, dict):
            return events

        table_id = table.get("id")
        if not table_id:
            return events

        # 1. Kiểm tra người chơi có đang cầm món ăn trên tay không
        hand = getattr(sim, "hand", None)
        if not hand:
            return events

        # Chuẩn hóa tên món trên tay (hỗ trợ cả dạng string và object)
        hand_dish = hand if isinstance(hand, str) else hand.get("dish_id") or hand.get("dish")
        if not hand_dish:
            return events

        # 2. Tìm khách hàng đang ngồi tại bàn này
        customer = get_customer_at_table(sim, table_id)
        if not customer:
            return events

        # Khách phải đang ở trạng thái chờ món
        state = customer.get("state", "waiting_dish")
        if state not in ("waiting", "waiting_dish"):
            return events

        # 3. Đối chiếu món khách gọi
        customer_dish = customer.get("dish") or customer.get("dish_id")
        if hand_dish != customer_dish:
            # Món trên tay không đúng món khách này gọi -> không phục vụ nhầm
            return events

        # 4. Phục vụ thành công
        sim.hand = None
        customer["state"] = "eating"
        customer["order_status"] = "served"

        # Thời gian ăn đọc từ tuning (mặc định 10s)
        eat_s = 10.0
        if hasattr(sim, "t") and isinstance(sim.t, dict):
            eat_s = float(sim.t.get("eat_s", 10.0))

        eat_ticks = int(round(eat_s * TICK))
        customer["eat_ticks_left"] = eat_ticks
        customer["eat_max_ticks"] = eat_ticks

        # Tính trước tip khi phục vụ:
        # Nếu còn >= 50% kiên nhẫn lúc giao: boa = floor(giá * 0.2)
        patience_left = customer.get("patience_ticks_left", customer.get("patience_ticks", 0))
        pat_s = float(sim.t.get("patience_s", 60.0)) if hasattr(sim, "t") else 60.0
        patience_total = max(1, customer.get("patience_ticks") or customer.get("patience_max_ticks") or int(round(pat_s * TICK)))
        patience_ratio = patience_left / patience_total
        tip = 0
        dish_info = sim.menu.get(hand_dish, {}) if hasattr(sim, "menu") else {}
        base_price = (
            customer.get("base_price")
            or (hand.get("base_price") if isinstance(hand, dict) else 0)
            or int(dish_info.get("price", 0))
        )
        customer["base_price"] = base_price
        tip_min_ratio = float(sim.t.get("tip_min_patience_ratio", 0.5)) if hasattr(sim, "t") else 0.5
        tip_rate = float(sim.t.get("tip_rate", 0.2)) if hasattr(sim, "t") else 0.2
        if patience_ratio >= tip_min_ratio:
            tip = int(math.floor(base_price * tip_rate))
        customer["tip"] = tip

        # Bắn sự kiện served
        order_id = customer.get("id") or customer.get("order_id", "")
        customer_id = customer.get("customer_id") or order_id
        event_data = {
            "order_id": order_id,
            "table_id": table_id,
            "customer_id": customer_id,
            "dish_id": hand_dish,
            "dish": hand_dish,
            "tip": tip,
        }
        events.append(("served", event_data))

    except Exception as e:
        logger.error(f"[service] Ngoại lệ trong handle_table_interact: {e}")

    return events


def update_dining(sim: Any) -> List[Tuple[str, Dict[str, Any]]]:
    """Cập nhật tiến trình ăn của khách hàng tại bàn mỗi tick (60 Hz):
    
    - Khách đang 'eating' đếm ngược `eat_ticks_left`.
    - Khi hết giờ ăn (`eat_ticks_left <= 0`):
      + Tính tiền cơ bản theo `sim.menu[dish]['price']`.
      + Kiểm tra tỷ lệ kiên nhẫn còn lại để tính tiền boa (tip) và cộng uy tín (tip_reputation).
      + Cộng tiền vào `sim.money`, `sim.earned`, `sim.shift_earned`.
      + Kẹp uy tín `sim.reputation` trong [reputation_min, reputation_max].
      + Bắn sự kiện: ('paid', {'customer_id': ..., 'dish': ..., 'amount': ..., 'tip': ..., 'reputation': ...}).
      + Khách rời đi (giải phóng bàn).
    """
    events: List[Tuple[str, Dict[str, Any]]] = []
    try:
        if not hasattr(sim, "customers") or not isinstance(sim.customers, list):
            return events

        # Lấy thông số cấu hình từ sim.t
        t = getattr(sim, "t", {})
        menu = getattr(sim, "menu", {})
        rep_min = float(t.get("reputation_min", 0.0))
        rep_max = float(t.get("reputation_max", 5.0))
        tip_rate = float(t.get("tip_rate", 0.2))
        tip_min_ratio = float(t.get("tip_min_patience_ratio", 0.5))
        tip_reputation = float(t.get("tip_reputation", 0.2))
        patience_s = float(t.get("patience_s", 60.0))
        pat_max_ticks = max(1, int(round(patience_s * TICK)))

        finished_customer_ids = []

        for c in sim.customers:
            if not isinstance(c, dict):
                continue

            if c.get("state") != "eating":
                continue

            try:
                if c.get("eat_ticks_left", 0) <= 0:
                    # Khách đã ăn xong -> Tiến hành thanh toán
                    dish = c.get("dish") or c.get("dish_id", "")
                    dish_info = menu.get(dish, {}) if isinstance(menu, dict) else {}
                    base_price = c.get("base_price") or int(dish_info.get("price", 0))

                    tip = c.get("tip", 0)
                    if tip > 0:
                        current_rep = getattr(sim, "reputation", 3.0)
                        sim.reputation = max(rep_min, min(rep_max, current_rep + tip_reputation))

                    total_amount = base_price + tip
                    sim.money = getattr(sim, "money", 0) + total_amount
                    sim.earned = getattr(sim, "earned", 0) + total_amount
                    sim.shift_earned = getattr(sim, "shift_earned", 0) + total_amount

                    # Kẹp uy tín an toàn
                    sim.reputation = max(rep_min, min(rep_max, getattr(sim, "reputation", 3.0)))

                    events.append(("paid", {
                        "order_id": c.get("id"),
                        "customer_id": c.get("id", ""),
                        "dish_id": dish,
                        "dish": dish,
                        "amount": total_amount,
                        "tip": tip,
                        "reputation": round(float(sim.reputation), 3),
                        "reason": "finished_eating",
                    }))

                    finished_customer_ids.append(c.get("id"))

            except Exception as item_err:
                logger.error(f"[service] Lỗi khi xử lý khách ăn xong {c.get('id')}: {item_err}")

        # Xóa các khách đã thanh toán rời quán (giải phóng bàn)
        if finished_customer_ids:
            sim.customers = [c for c in sim.customers if c.get("id") not in finished_customer_ids]

    except Exception as e:
        logger.error(f"[service] Ngoại lệ trong update_dining: {e}")

    return events


def update_patience(sim: Any) -> List[Tuple[str, Dict[str, Any]]]:
    """Cập nhật độ kiên nhẫn của khách đang chờ món:
    
    - Khách đang 'waiting_dish' đếm lùi `patience_ticks_left`.
    - Khi hết kiên nhẫn (`patience_ticks_left <= 0`):
      + Khách bỏ về.
      + Trừ uy tín `left_reputation_delta` (mặc định -0.5).
      + Bắn sự kiện: ('customer_left', {'customer_id': ..., 'reason': 'impatient', 'reputation': ...}).
      + Giải phóng bàn.
    """
    events: List[Tuple[str, Dict[str, Any]]] = []
    try:
        if not hasattr(sim, "customers") or not isinstance(sim.customers, list):
            return events

        t = getattr(sim, "t", {})
        rep_min = float(t.get("reputation_min", 0.0))
        rep_max = float(t.get("reputation_max", 5.0))
        left_delta = float(t.get("left_reputation_delta", -0.5))

        left_customer_ids = []

        for c in sim.customers:
            if not isinstance(c, dict):
                continue

            # Chỉ trừ kiên nhẫn khi khách còn đang chờ món
            if c.get("state") not in ("waiting", "waiting_dish"):
                continue

            try:
                if c.get("patience_ticks_left", 0) <= 0:
                    # Khách hết kiên nhẫn bỏ về
                    current_rep = getattr(sim, "reputation", 3.0)
                    sim.reputation = max(rep_min, min(rep_max, current_rep + left_delta))

                    if hasattr(sim, "_release_customer_order"):
                        sim._release_customer_order(c.get("id"))

                    events.append(("customer_left", {
                        "order_id": c.get("id"),
                        "customer_id": c.get("id", ""),
                        "table_id": c.get("table_id"),
                        "reason": "patience",
                        "reputation": round(float(sim.reputation), 3),
                    }))

                    left_customer_ids.append(c.get("id"))

            except Exception as item_err:
                logger.error(f"[service] Lỗi khi xử lý kiên nhẫn khách {c.get('id')}: {item_err}")

        # Xóa các khách đã bỏ đi
        if left_customer_ids:
            sim.customers = [c for c in sim.customers if c.get("id") not in left_customer_ids]

    except Exception as e:
        logger.error(f"[service] Ngoại lệ trong update_patience: {e}")

    return events


def update_service(sim: Any) -> List[Tuple[str, Dict[str, Any]]]:
    """Hàm tổng hợp gọi mỗi tick từ QuanSim.step():
    
    1. Cập nhật tiến trình ăn & thanh toán (update_dining)
    2. Cập nhật thanh kiên nhẫn & xử lý khách bỏ về (update_patience)
    """
    events: List[Tuple[str, Dict[str, Any]]] = []
    events.extend(update_dining(sim))
    events.extend(update_patience(sim))
    return events
