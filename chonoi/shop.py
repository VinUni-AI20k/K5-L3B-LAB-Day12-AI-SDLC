"""Shop cuối Ngày (Test Contract v1.1): mua nâng cấp, đóng bằng shop_done hoặc tự đóng sau shop.max_ticks.

Mỗi bước: xử lý tối đa một `buy` (chỉ ở frame khai báo) TRƯỚC cạnh shop_done, kể cả bước cuối.
Nâng cấp theo dữ liệu tuning.shop.upgrades; mua cấp kế tiếp, đủ đúng giá vẫn mua được; trừ money, giữ earned.
Cấp vừa mua ghi vào `upgrades` (hiển thị ngay); `active_upgrades` chỉ đổi khi dựng Ngày mới (day.py lo).
"""


class ShopSim:
    mode = "day"
    phase = "shop"

    def __init__(self, tuning, money, earned, reputation, upgrades, stock):
        self.cfg = tuning["shop"]
        self.money = money
        self.earned = earned
        self.reputation = reputation
        self.upgrades = upgrades  # dict dùng chung với DaySession: cấp đã mua
        self.stock = dict(stock)  # kho dư từ ca, chỉ để hiển thị (bị bỏ sau Shop)
        self.time_left_ticks = int(self.cfg["max_ticks"])
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        return {"stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}}

    def buy(self, action, events):
        levels = self.cfg["upgrades"].get(action)
        if levels is None:  # lệnh không hỗ trợ (mở rộng chưa bật, Chợ...)
            events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            return
        level = self.upgrades.get(action, 0) + 1
        if level > len(levels):
            events.append(("buy_failed", {"action": action, "reason": "max_level"}))
            return
        price = levels[level - 1]["price"]
        if price > self.money:
            events.append(("buy_failed", {"action": action, "reason": "funds"}))
            return
        self.money -= price
        self.upgrades[action] = level
        events.append(("bought", {"upgrade": action, "level": level, "price": price, "money": self.money}))

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy:
            self.buy(inp.buy, events)
        if inp.pressed("shop_done"):
            self._end("done", events)
        elif self.time_left_ticks <= 0:
            self._end("time", events)
        return events

    def _end(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("shop_end", {"reason": reason}))
