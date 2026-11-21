"""Kế hoạch, nâng cấp và ca Shop của vòng ngày."""

from collections import Counter
import math

from ..errors import BadInput


def plans_for_run(tuning, overrides):
    plans = {p["day"]: p for p in tuning["day_plan"]}
    if not isinstance(overrides, list):
        raise BadInput("day.day_plan phải là mảng theo ngày")
    seen = set()
    for item in overrides:
        if not isinstance(item, dict) or item.keys() - {"day", "dishes", "ingredients"}:
            raise BadInput("kế hoạch ngày sai schema")
        number = item.get("day")
        if type(number) is not int or number not in plans or number in seen:
            raise BadInput("ngày ngoài kế hoạch hoặc bị trùng")
        seen.add(number)
        dishes = item.get("dishes")
        if not isinstance(dishes, dict):
            raise BadInput("kế hoạch cần dishes")
        ingredients = Counter()
        for dish, count in dishes.items():
            if dish not in tuning["menu"] or type(count) is not int or count <= 0:
                raise BadInput("món hoặc số suất không hợp lệ")
            for kind, units in tuning["menu"][dish]["recipe"].items():
                ingredients[kind] += units * count
        if "ingredients" in item:
            given = item["ingredients"]
            if (not isinstance(given, dict) or any(type(v) is not int for v in given.values())
                    or given != ingredients):
                raise BadInput("nguyên liệu không khớp công thức")
        plans[number] = {"day": number, "dishes": dishes, "ingredients": dict(ingredients)}
    return plans


def validate_day(state, tuning):
    if not isinstance(state, dict) or state.keys() - {"money", "earned", "reputation", "day_plan", "upgrades"}:
        raise BadInput("khối day sai schema")
    money, earned = state.get("money", 0), state.get("earned", 0)
    if (("money" in state) != ("earned" in state) or type(money) is not int
            or type(earned) is not int or not 0 <= money <= earned):
        raise BadInput("cần 0 <= money <= earned, khai cả hai cùng lúc")
    rep = state.get("reputation", tuning["quan"]["reputation_initial"])
    if (type(rep) not in (int, float) or not math.isfinite(rep)
            or not tuning["quan"]["reputation_min"] <= rep <= tuning["quan"]["reputation_max"]):
        raise BadInput("uy tín đầu ngày ngoài miền")
    upgrades = state.get("upgrades", {})
    prices = tuning["shop"]["upgrades"]
    if not isinstance(upgrades, dict) or any(
        key not in prices or type(level) is not int or not 0 <= level <= len(prices[key])
        for key, level in upgrades.items()
    ):
        raise BadInput("cấp nâng cấp không hợp lệ")
    return plans_for_run(tuning, state.get("day_plan", []))


def gather_tuning(tuning, active):
    gather = tuning["gather"].copy()
    for key, field in (("oxygen", "oxygen_max_s"), ("hp", "hp_max")):
        level = active.get(key, 0)
        if level:
            gather[field] = tuning["shop"]["upgrades"][key][level - 1][field]
    return {**tuning, "gather": gather}


def check_evening_fixture(scenario, stock, menu):
    available = Counter(stock)
    customers = {c["id"]: c for c in scenario.get("customers", [])}
    assigned = set()
    for customer in customers.values():
        dish = customer.get("dish_id")
        if not isinstance(dish, str) or dish not in menu:
            raise BadInput("đơn quán ngoài kế hoạch ngày")
        status = customer.get("order_status", "reserved")
        if status == "reserved":
            recipe = menu[dish]["recipe"]
            if customer.get("reserved", recipe) != recipe:
                raise BadInput("giữ chỗ sai công thức")
            available.subtract(recipe)
        elif status in ("assigned", "served", "unfulfillable"):
            if customer.get("reserved", {}):
                raise BadInput("đơn không ở trạng thái reserved vẫn giữ nguyên liệu")
            if status == "assigned":
                assigned.add(customer["id"])
        else:
            raise BadInput("trạng thái đơn sai")
    if any(qty < 0 for qty in available.values()):
        raise BadInput("giữ chỗ vượt kho bàn giao")
    payloads = [scenario.get("hand")]
    for stove in scenario.get("stoves", []):
        state = stove.get("state", "idle")
        payload = stove.get("dish")
        remaining = stove.get("cook_ticks_left", 0)
        if (state not in ("idle", "cooking", "ready") or (state == "idle") != (payload is None)
                or type(remaining) is not int or remaining < 0 or (state == "cooking") != (remaining > 0)):
            raise BadInput("trạng thái bếp, món và timer mâu thuẫn")
        payloads.append(payload)
    for payload in payloads:
        if payload is None:
            continue
        if not isinstance(payload, dict):
            raise BadInput("payload món sai schema")
        order = payload.get("order_id")
        if (not isinstance(order, str) or order not in assigned
                or payload.get("dish_id") != customers[order]["dish_id"]
                or type(payload.get("base_price")) is not int or payload["base_price"] <= 0):
            raise BadInput("món ở bếp hoặc trên tay không khớp đơn assigned")
        assigned.remove(order)
    if assigned:
        raise BadInput("đơn assigned thiếu món")


class ShopSim:
    phase = "shop"

    def __init__(self, config, upgrades, previous):
        self.catalog = config["upgrades"]
        self.time_left_ticks = config["max_ticks"]
        self.upgrades = upgrades
        self.money, self.earned, self.reputation = previous.money, previous.earned, previous.reputation
        self.stock = dict(previous.stock)
        self.done = False
        self.reason = None

    def snapshot(self):
        return {"stock": {k: v for k, v in sorted(self.stock.items()) if v}}

    def step(self, inp):
        events = []
        self.time_left_ticks -= 1
        if inp.buy is not None:
            key = inp.buy
            current = self.upgrades.get(key, 0)
            if key not in self.catalog:
                reason = "unknown"
            elif current == len(self.catalog[key]):
                reason = "max_level"
            elif self.money < self.catalog[key][current]["price"]:
                reason = "funds"
            else:
                price = self.catalog[key][current]["price"]
                self.money -= price
                self.upgrades[key] = current + 1
                events.append(("bought", {"upgrade": key, "level": current + 1, "price": price, "money": self.money}))
                reason = None
            if reason:
                events.append(("buy_failed", {"action": key, "reason": reason}))
        if inp.pressed("shop_done") or self.time_left_ticks == 0:
            self.done = True
            self.reason = "done" if inp.pressed("shop_done") else "time"
            events.append(("shop_end", {"reason": self.reason}))
        return events
