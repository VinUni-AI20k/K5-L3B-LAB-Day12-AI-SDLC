"""Shop cuối Ngày (Ticket-02 mục 2 "Shop và nâng cấp", 4.5 "Shop"). Lát 5.

Mỗi bước: giảm đồng hồ Shop -> xử lý tối đa một `buy` -> cạnh `shop_done` -> hết giờ.
Mua cấp kế tiếp theo dữ liệu `tuning.shop.upgrades`; đủ đúng giá vẫn mua được; trừ `money`, giữ `earned`.
Cấp vừa mua ghi vào `upgrades` ngay; DaySim chỉ chép sang `active_upgrades` khi dựng Ngày mới.
"""


from ..ids import sort_by_id


class ShopSim:
    phase = "shop"

    def __init__(self, shop_tuning: dict, money: int, upgrades: dict, stock: dict):
        self.table = shop_tuning["upgrades"]
        self.money = money
        self.upgrades = dict(upgrades)
        # Kho dư từ ca tối, bỏ khi Shop đóng. Hàng thô ở Shop KHÔNG hao tươi (Ticket-03). v1.2: mảng cá thể
        # theo id (giữ nguyên id, kind, fresh); v1.1: kho đếm.
        if isinstance(stock, dict):
            self.stock = {k: n for k, n in sorted(stock.items()) if n > 0}
        else:
            self.stock = [dict(i) for i in sort_by_id(stock)]
        self.time_left_ticks = int(shop_tuning["max_ticks"])
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        return {"stock": self.stock}

    def step(self, inp) -> list:
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy is not None:
            events.append(self._buy(inp.buy))
        if inp.pressed("shop_done"):
            self._close("done", events)
        elif self.time_left_ticks == 0:
            self._close("time", events)
        return events

    def _buy(self, action: str):
        levels = self.table.get(action)
        if levels is None:  # lệnh không hỗ trợ / mở rộng chưa bật
            return ("buy_failed", {"action": action, "reason": "unknown"})
        level = self.upgrades.get(action, 0)
        if level >= len(levels):
            return ("buy_failed", {"action": action, "reason": "max_level"})
        price = levels[level]["price"]
        if self.money < price:
            return ("buy_failed", {"action": action, "reason": "funds"})
        self.money -= price
        self.upgrades[action] = level + 1
        return ("bought", {"upgrade": action, "level": level + 1, "price": price, "money": self.money})

    def _close(self, reason: str, events: list):
        self.done = True
        self.reason = reason
        events.append(("shop_end", {"reason": reason}))
