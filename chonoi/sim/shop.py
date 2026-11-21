"""Shop cuối ngày trong contract v1.1."""


def gather_tuning(tuning, upgrades):
    """Thông số ca sáng với các cấp đã có hiệu lực."""
    gather = dict(tuning["gather"])
    for upgrade, field in (("oxygen", "oxygen_max_s"), ("hp", "hp_max")):
        level = upgrades.get(upgrade, 0)
        if level:
            gather[field] = tuning["shop"]["upgrades"][upgrade][level - 1][field]
    return gather


class ShopSim:
    phase = "shop"

    def __init__(self, tuning, stock, money, upgrades):
        self.time_left_ticks = tuning["max_ticks"]
        self.catalog = tuning["upgrades"]
        self.stock = stock
        self.money = money
        self.upgrades = upgrades
        self.done = False

    def snapshot(self):
        return {"stock": {kind: n for kind, n in sorted(self.stock.items()) if n > 0}}

    def step(self, inp):
        events = []
        self.time_left_ticks -= 1
        if inp.buy is not None:
            events.append(self._buy(inp.buy))
        if inp.pressed("shop_done") or self.time_left_ticks == 0:
            self.done = True
            reason = "done" if inp.pressed("shop_done") else "time"
            events.append(("shop_end", {"reason": reason}))
        return events

    def _buy(self, action):
        levels = self.catalog.get(action)
        level = self.upgrades.get(action, 0)
        if levels is None:
            return "buy_failed", {"action": action, "reason": "unknown"}
        if level >= len(levels):
            return "buy_failed", {"action": action, "reason": "max_level"}
        purchase = levels[level]
        price = purchase["price"]
        if self.money < price:
            return "buy_failed", {"action": action, "reason": "funds"}
        self.money -= price
        self.upgrades[action] = purchase["level"]
        return "bought", {"upgrade": action, "level": purchase["level"], "price": price, "money": self.money}
