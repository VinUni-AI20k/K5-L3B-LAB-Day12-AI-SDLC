"""Shop lõi v1.1. Luồng day chuyển buy và cạnh shop_done vào mỗi tick hoạt động."""

from ..errors import BadInput


GATHER_FIELDS = {"oxygen": "oxygen_max_s", "hp": "hp_max"}


def _copy_stock(stock):
    if isinstance(stock, list):
        return [item.copy() for item in stock]
    return dict(stock or {})


def apply_gather_upgrades(tuning, active_upgrades):
    """Tạo tuning của ngày mới sau khi day chốt các cấp đang có hiệu lực."""
    gather = tuning["gather"].copy()
    levels_by_name = tuning["shop"]["upgrades"]
    for name, field in GATHER_FIELDS.items():
        level = active_upgrades.get(name, 0)
        levels = levels_by_name[name]
        if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= len(levels):
            raise BadInput(f"shop.upgrades.{name}: cấp không hợp lệ: {level!r}")
        if level > 0:
            gather[field] = levels[level - 1][field]
    return {**tuning, "gather": gather}


class ShopSim:
    phase = "shop"

    def __init__(self, tuning, *, money, earned, reputation, stock=None, upgrades=None):
        self.money = money
        self.earned = earned
        self.reputation = reputation
        self.stock = _copy_stock(stock)
        self.upgrades = dict(upgrades or {})
        self.time_left_ticks = tuning["shop"]["max_ticks"]
        self._levels = tuning["shop"]["upgrades"]
        self.done = False
        self.reason = None

    def snapshot(self):
        return {
            "money": self.money, "earned": self.earned, "reputation": self.reputation,
            "time_left_ticks": self.time_left_ticks, "stock": _copy_stock(self.stock),
            "upgrades": self.upgrades.copy(),
        }

    def step(self, buy=None, *, done=False):
        """Xử lý lệnh mua tại frame hiện tại rồi xét đóng Shop."""
        if self.done:
            return []
        self.time_left_ticks -= 1
        events = []
        if buy is not None:
            events.append(self._buy(buy))
        if done or self.time_left_ticks == 0:
            self.done = True
            self.reason = "done" if done else "time"
            events.append(("shop_end", {"reason": self.reason}))
        return events

    def _buy(self, name):
        if name not in GATHER_FIELDS:
            return "buy_failed", {"action": name, "reason": "unknown"}
        levels = self._levels[name]
        current = self.upgrades.get(name, 0)
        if current >= len(levels):
            return "buy_failed", {"action": name, "reason": "max_level"}

        upgrade = levels[current]
        price = upgrade["price"]
        if price > self.money:
            return "buy_failed", {"action": name, "reason": "funds"}

        level = upgrade["level"]
        self.money -= price
        self.upgrades[name] = level
        return "bought", {"upgrade": name, "level": level, "price": price, "money": self.money}
