"""Shared tuning and fixture rules for day mode."""

from collections import Counter

from .errors import BadInput


def day_plans(tuning, overrides=()):
    """Resolve each plan against the menu and compute its ingredient targets."""
    plans = {}
    for entries in (tuning["day_plan"], overrides):
        if not isinstance(entries, (list, tuple)):
            raise BadInput("day_plan phải là mảng")
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) - {"day", "dishes", "ingredients"}:
                raise BadInput("mỗi day_plan chỉ có day, dishes, ingredients")
            day, dishes = entry.get("day"), entry.get("dishes")
            if type(day) is not int or not 1 <= day <= 5 or day in seen:
                raise BadInput("day_plan.day phải là số Ngày duy nhất từ 1 đến 5")
            seen.add(day)
            if not isinstance(dishes, dict) or not dishes:
                raise BadInput("day_plan.dishes phải là object món và số suất")
            ingredients = Counter()
            for dish, servings in dishes.items():
                if dish not in tuning["menu"] or type(servings) is not int or servings <= 0:
                    raise BadInput(f"ngày {day}: món hoặc số suất không hợp lệ: {dish}")
                ingredients.update({kind: count * servings
                                    for kind, count in tuning["menu"][dish]["recipe"].items()})
            declared = entry.get("ingredients", ingredients)
            if (not isinstance(declared, dict) or any(type(count) is not int for count in declared.values())
                    or declared != ingredients):
                raise BadInput(f"ngày {day}: ingredients không khớp công thức và số suất")
            plans[day] = {"day": day, "dishes": dict(sorted(dishes.items())),
                          "ingredients": dict(sorted(ingredients.items()))}
    if set(plans) != set(range(1, 6)):
        raise BadInput("day_plan phải có đủ 5 ngày")
    return plans


def gather_tuning(tuning, upgrades):
    """Select capacity for the day without mutating the shared preset."""
    gather = tuning["gather"].copy()
    if not isinstance(upgrades, dict):
        raise BadInput("day.upgrades phải là object")
    for kind, level in upgrades.items():
        levels = tuning["shop"]["upgrades"].get(kind)
        if levels is None or type(level) is not int or not 0 <= level <= len(levels):
            raise BadInput(f"cấp nâng cấp không hợp lệ: {kind}")
        if level:
            gather.update({key: value for key, value in levels[level - 1].items() if key not in ("price", "level")})
    return {**tuning, "gather": gather}
