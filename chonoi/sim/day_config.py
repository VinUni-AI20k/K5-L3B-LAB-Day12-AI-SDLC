"""Kiểm dữ liệu vòng ngày/Shop (Ticket-02 4.3), không chứa số chuẩn gameplay."""

import copy
import math

from ..errors import BadInput


def nonnegative_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")
    return value


def plan_entry(entry, menu):
    if not isinstance(entry, dict) or set(entry) - {"day", "dishes", "ingredients"}:
        raise BadInput("day_plan: mục chỉ nhận day, dishes, ingredients")
    day = nonnegative_int("day_plan.day", entry.get("day"))
    if not 1 <= day <= 5:
        raise BadInput("day_plan.day phải trong [1, 5]")
    dishes = entry.get("dishes")
    if not isinstance(dishes, dict) or not dishes:
        raise BadInput("day_plan.dishes phải là map không rỗng")
    ingredients = {}
    for dish_id, count in sorted(dishes.items()):
        if dish_id not in menu or nonnegative_int("day_plan.dishes.count", count) == 0:
            raise BadInput("day_plan: món lạ hoặc số suất không dương")
        for kind, amount in menu[dish_id]["recipe"].items():
            ingredients[kind] = ingredients.get(kind, 0) + count * amount
    if "ingredients" in entry:
        supplied = entry["ingredients"]
        if not isinstance(supplied, dict):
            raise BadInput("day_plan.ingredients phải là map")
        for value in supplied.values():
            if nonnegative_int("day_plan.ingredients.count", value) == 0:
                raise BadInput("day_plan.ingredients phải có số lượng dương")
        if supplied != ingredients:
            raise BadInput("day_plan.ingredients khác tổng công thức nhân số suất")
    return {"day": day, "dishes": dict(sorted(dishes.items())), "ingredients": dict(sorted(ingredients.items()))}


def plans(tuning, overrides=None):
    raw = tuning.get("day_plan")
    if not isinstance(raw, list) or not raw:
        raise BadInput("thiếu tuning.day_plan v1.1; cần tích hợp cấu hình của Integrator")
    result = {}
    for entries in (raw, overrides if overrides is not None else []):
        if not isinstance(entries, list):
            raise BadInput("day.day_plan phải là mảng")
        seen = set()
        for entry in entries:
            parsed = plan_entry(entry, tuning["menu"])
            day = parsed["day"]
            if day in seen:
                raise BadInput("day_plan: trùng Ngày")
            seen.add(day)
            result[day] = parsed
    return result


def validate_day_scenario(data, tuning):
    """Trả cả ba khối: gather/quan là template, day là trạng thái xuyên Ngày."""
    from ..scenario import validate_phase_block

    if not isinstance(data, dict) or set(data) - {"day", "gather", "quan"}:
        raise BadInput("scenario day chỉ có day, gather, quan")
    state = data.get("day", {})
    if not isinstance(state, dict) or set(state) - {"money", "earned", "reputation", "upgrades", "day_plan"}:
        raise BadInput("day chỉ có money, earned, reputation, upgrades, day_plan")
    if "day_plan" in state and not isinstance(state["day_plan"], list):
        raise BadInput("day.day_plan phải là mảng")
    if ("money" in state) != ("earned" in state):
        raise BadInput("tiền đầu kỳ phải khai cả money và earned")
    money = nonnegative_int("day.money", state.get("money", 0))
    earned = nonnegative_int("day.earned", state.get("earned", 0))
    if money > earned:
        raise BadInput("day.money không được vượt earned")
    q = tuning["quan"]
    reputation = state.get("reputation", q["reputation_initial"])
    if (isinstance(reputation, bool) or not isinstance(reputation, (int, float)) or not math.isfinite(reputation)
            or not q["reputation_min"] <= reputation <= q["reputation_max"]):
        raise BadInput("day.reputation ngoài miền hợp lệ")
    plans(tuning, state.get("day_plan"))
    shop = tuning.get("shop")
    if not isinstance(shop, dict) or not isinstance(shop.get("upgrades"), dict):
        raise BadInput("thiếu tuning.shop v1.1; cần tích hợp cấu hình của Integrator")
    if not {"oxygen", "hp"} <= set(shop["upgrades"]):
        raise BadInput("shop.upgrades cần oxygen và hp")
    if nonnegative_int("shop.max_ticks", shop.get("max_ticks")) == 0:
        raise BadInput("shop.max_ticks phải dương")
    for name, levels in shop["upgrades"].items():
        if not isinstance(levels, list) or not levels:
            raise BadInput(f"shop.upgrades.{name}: cần mảng cấp")
        for expected, level in enumerate(levels, 1):
            if not isinstance(level, dict) or level.get("level") != expected or isinstance(level.get("level"), bool):
                raise BadInput(f"shop.upgrades.{name}: cấp phải liên tục từ 1")
            if nonnegative_int("upgrade.price", level.get("price")) == 0:
                raise BadInput("giá nâng cấp phải dương")
            field = {"oxygen": "oxygen_max_s", "hp": "hp_max"}.get(name)
            if field is not None:
                value = level.get(field)
                if (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
                        or value <= 0 or (field == "hp_max" and not isinstance(value, int))):
                    raise BadInput(f"upgrade.{field}: giá trị không hợp lệ")
    upgrades = state.get("upgrades", {})
    if not isinstance(upgrades, dict):
        raise BadInput("day.upgrades phải là map")
    for name, level in upgrades.items():
        if name not in shop["upgrades"] or nonnegative_int("upgrade.level", level) > len(shop["upgrades"][name]):
            raise BadInput("day.upgrades: id/cấp không hợp lệ")
    effective = copy.deepcopy(tuning)
    for name, field in (("oxygen", "oxygen_max_s"), ("hp", "hp_max")):
        level = upgrades.get(name, 0)
        if level:
            effective["gather"][field] = shop["upgrades"][name][level - 1][field]
    for mode in ("gather", "quan"):
        block = data.get(mode, {})
        if not isinstance(block, dict):
            raise BadInput(f"{mode} phải là object")
        if mode == "quan" and ({"stock", "reputation"} & set(block)):
            raise BadInput("day cấm quan.stock và quan.reputation")
        validate_phase_block(block, mode, effective)
    return copy.deepcopy(data)
