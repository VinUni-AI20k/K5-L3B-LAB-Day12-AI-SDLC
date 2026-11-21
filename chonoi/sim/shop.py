"""Shop cuối Ngày (Test Contract v1.1 mục 2 "Shop và nâng cấp", 4.2, 4.5 "Shop").

Một bước Shop:
  1. đồng hồ: phase_tick + 1, time_left_ticks - 1
  2. tối đa MỘT lệnh `buy` của frame này (xử lý TRƯỚC cạnh shop_done, kể cả ở bước cuối)
  3. cạnh shop_done -> shop_end(done); nếu không và hết giờ -> shop_end(time)

Mua: cấp kế tiếp của nâng cấp theo dữ liệu `tuning.shop.upgrades.<id>[]`, mỗi cấp một lần, đủ đúng giá
vẫn mua được, chỉ trừ `money` (giữ earned và điểm). Đã tối đa -> buy_failed max_level; thiếu tiền ->
buy_failed funds; lệnh không hỗ trợ (kể cả mở rộng chưa bật) -> buy_failed unknown. Cấp vừa mua chỉ ghi
vào `upgrades` (đã mua); DaySim chép sang `active_upgrades` khi dựng Ngày kế.
"""


class ShopSim:
    phase = "shop"

    def __init__(self, tuning, money, upgrades, stock=None):
        self.cfg = tuning["shop"]
        self.money = money
        self.upgrades = upgrades  # dict dùng chung với DaySim (cấp đã mua)
        self.stock = dict(stock or {})  # kho dư từ ca tối, chỉ để hiển thị; bị bỏ khi sang Ngày mới
        self.time_left_ticks = int(self.cfg["max_ticks"])
        self.phase_tick = 0
        self.done = False
        self.reason = None

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy is not None:
            self._buy(inp.buy, events)
        if inp.pressed("shop_done"):
            self._close("done", events)
        elif self.time_left_ticks <= 0:
            self._close("time", events)
        return events

    def _buy(self, action, events):
        levels = self.cfg["upgrades"].get(action)
        if not isinstance(levels, list) or action not in ("oxygen", "hp"):
            events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            return
        cur = self.upgrades.get(action, 0)
        nxt = next((lv for lv in levels if lv["level"] == cur + 1), None)
        if nxt is None:
            events.append(("buy_failed", {"action": action, "reason": "max_level"}))
            return
        price = int(nxt["price"])
        if price > self.money:
            events.append(("buy_failed", {"action": action, "reason": "funds"}))
            return
        self.money -= price
        self.upgrades[action] = nxt["level"]
        events.append(("bought", {"upgrade": action, "level": nxt["level"], "price": price, "money": self.money}))

    def _close(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("shop_end", {"reason": reason}))

    def snapshot(self):
        return {"stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}}
