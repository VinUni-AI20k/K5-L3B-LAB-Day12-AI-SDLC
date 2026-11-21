"""Shop cuối Ngày (Test Contract v1.1, Ticket-02 mục 2 và 4.5). C viết. KHUNG: giao diện gợi ý.

Luật:
- Tự đóng sau tuning.shop.max_ticks (600) tick hoạt động (pause không tính) -> shop_end{reason: "time"}.
- `inp.buy` (chuỗi, chỉ có hiệu lực tại frame khai báo): "oxygen" | "hp" mua cấp kế tiếp. Đủ đúng giá vẫn mua.
  Trừ money, giữ earned và điểm, phát bought{upgrade, level, price, money}. Thiếu tiền -> buy_failed{action,
  reason: "funds"}; đã tối đa -> "max_level"; lệnh lạ hoặc mở rộng chưa bật -> "unknown". Thất bại giữ nguyên tiền, cấp.
- Xử lý một buy TRƯỚC cạnh shop_done trong cùng bước. Cạnh shop_done -> shop_end{reason: "done"}.
- Cấp vừa mua hiện ngay trong `upgrades`, chỉ có hiệu lực từ Ngày kế (DaySession chép sang active_upgrades).
- Snapshot Shop có `stock` dư từ ca quán và `time_left_ticks` tới lúc đóng.

Dùng `contract.upgrade_value(tuning, kind, level, base)` để đọc giá trị theo cấp và
`tuning["shop"]["upgrades"][kind][level - 1]["price"]` để đọc giá.
"""

from . import fresh
from .ids import sort_by_id

TICK = 60.0


class ShopSim:
    mode = "day"
    phase = "shop"

    def __init__(self, tuning, stock, carry, upgrades):
        self.t = tuning["shop"]
        # kho dư từ ca quán: v1.1 dict đếm, v1.2 mảng cá thể (Shop không hao tươi)
        self.stock = [dict(it) for it in stock] if isinstance(stock, list) else dict(stock)
        self.money = carry["money"]
        self.earned = carry["earned"]
        self.reputation = carry["reputation"]
        self.upgrades = dict(upgrades)
        self.time_left_ticks = int(self.t["max_ticks"])
        self.phase_tick = 0
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        """Ticket-02 mục 4.4: Shop có `stock` dư từ ca quán (bỏ mục bằng 0). `upgrades` do DaySession thêm.
        v1.2: mảng cá thể public sắp theo id."""
        if isinstance(self.stock, list):
            return {"stock": fresh.public_list(sort_by_id(self.stock))}
        return {"stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}}

    def step(self, inp):
        """Một bước Shop: một `buy` -> cạnh `shop_done` -> hết giờ. Trả list (name, data)."""
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
        levels = self.t["upgrades"].get(action)
        if levels is None:  # lệnh lạ, buy:/sell: của Chợ hoặc mở rộng chưa bật
            events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            return
        level = self.upgrades.get(action, 0)
        if level >= len(levels):
            events.append(("buy_failed", {"action": action, "reason": "max_level"}))
            return
        price = levels[level]["price"]
        if self.money < price:  # đủ đúng giá vẫn mua
            events.append(("buy_failed", {"action": action, "reason": "funds"}))
            return
        self.money -= price  # earned và điểm giữ nguyên
        self.upgrades[action] = level + 1
        events.append(("bought", {"upgrade": action, "level": level + 1, "price": price, "money": self.money}))

    def _close(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("shop_end", {"reason": reason}))
