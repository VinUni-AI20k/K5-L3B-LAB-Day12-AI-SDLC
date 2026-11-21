"""Cuối ngày — Shop nâng cấp (`shop`, chỉ có trong --mode day). TICKET-02 mục 2 "Shop và nâng cấp", 4.2, 4.5.

- `buy` (chuỗi, chỉ tại frame khai báo): oxygen / hp mua cấp kế tiếp. Đủ đúng giá vẫn mua được. Trừ money,
  giữ earned. Thiếu tiền -> buy_failed(funds); đã tối đa -> buy_failed(max_level); lệnh không hỗ trợ
  (kể cả mở rộng chưa bật) -> buy_failed(unknown).
- Xử lý một buy TRƯỚC cạnh shop_done, kể cả bước cuối. shop_done -> shop_end(done);
  hết max_ticks bước hoạt động (pause không tính, do runner lo) -> shop_end(time).
- Cấp vừa mua hiện ngay trong `purchased`; có hiệu lực từ Ngày kế (day.py sao sang active_upgrades).
"""

TICK = 60.0
CORE_UPGRADES = ("oxygen", "hp")


class ShopSim:
    mode = "shop"
    phase = "shop"

    def __init__(self, tuning, money, earned, reputation, purchased, stock):
        self.t = tuning["shop"]
        self.money = money
        self.earned = earned
        self.reputation = reputation
        self.purchased = dict(purchased)
        self.stock = [dict(it) for it in stock]  # v1.2: kho dư cá thể từ ca, không hao ở Shop, bị bỏ sau Shop
        self.time_left_ticks = int(self.t["max_ticks"])
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        from ..items import list_json
        return {"stock": list_json(self.stock)}

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy is not None:
            self._buy(inp.buy, events)
        if inp.pressed("shop_done"):
            self._finish("done", events)
        elif self.time_left_ticks <= 0:
            self._finish("time", events)
        return events

    def _buy(self, cmd, events):
        if cmd not in CORE_UPGRADES:
            events.append(("buy_failed", {"action": cmd, "reason": "unknown"}))
            return
        levels = self.t["upgrades"][cmd]
        cur = int(self.purchased.get(cmd, 0))
        if cur >= len(levels):
            events.append(("buy_failed", {"action": cmd, "reason": "max_level"}))
            return
        price = int(levels[cur]["price"])
        if self.money < price:
            events.append(("buy_failed", {"action": cmd, "reason": "funds"}))
            return
        self.money -= price
        self.purchased[cmd] = cur + 1
        events.append(("bought", {"upgrade": cmd, "level": cur + 1, "price": price, "money": self.money}))

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("shop_end", {"reason": reason}))
