"""TV3 · Kế hoạch ngày D1–D5: tính ingredients từ dishes × công thức menu."""

from .errors import BadInput
from .inventory import validate_items


def compute_ingredients(menu: dict, dishes: dict) -> dict:
    """Tổng nguyên liệu = công thức × số suất; bỏ khóa 0, sắp theo id."""
    if not isinstance(dishes, dict) or not dishes:
        raise BadInput("day_plan.dishes phải là object không rỗng")
    totals = {}
    for dish_id, servings in dishes.items():
        if dish_id not in menu:
            raise BadInput(f"day_plan: món lạ {dish_id}")
        if isinstance(servings, bool) or not isinstance(servings, int) or servings <= 0:
            raise BadInput(f"day_plan.dishes.{dish_id} phải là số nguyên dương")
        for kind, qty in menu[dish_id]["recipe"].items():
            totals[kind] = totals.get(kind, 0) + qty * servings
    return validate_items(totals)


def plan_for_day(tuning: dict, day: int) -> dict:
    """Lấy {day, dishes, ingredients} từ tuning.day_plan (1..5)."""
    plans = tuning.get("day_plan") or []
    for p in plans:
        if p.get("day") == day:
            dishes = dict(p["dishes"])
            ingredients = compute_ingredients(tuning["menu"], dishes)
            declared = p.get("ingredients")
            if declared is not None and validate_items(declared) != ingredients:
                raise BadInput(f"day_plan D{day}: ingredients không khớp công thức")
            return {"day": day, "dishes": dishes, "ingredients": ingredients}
    raise BadInput(f"thiếu day_plan cho Ngày {day}")
