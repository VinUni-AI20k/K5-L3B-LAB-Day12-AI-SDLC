"""Shop cuối Ngày (Test Contract v1.1, đề §2 "Shop và nâng cấp", §4.5 "Shop"). TV6, T244; v1.2 T331.

Một bước (gọi bởi DaySim khi pha là `shop`, runner đã lo pause):
  1. đồng hồ hoạt động −1 (`shop.max_ticks` = 600 bước gameplay, đứng yên khi pause)
  2. một lệnh `buy` (chuỗi, chỉ ở frame khai báo) → `bought` hoặc `buy_failed`
  3. cạnh lên `shop_done` → `shop_end {reason:"done"}` (kể cả bước cuối)
  4. hết đồng hồ → `shop_end {reason:"time"}`

Nâng cấp hoàn toàn theo dữ liệu `tuning.shop.upgrades.<id>[]` ({level, price, ...}); mua cấp kế tiếp,
đủ đúng giá vẫn mua, trừ `money` (giữ `earned`). Cấp mua ghi vào `day.upgrades` ngay; DaySim chỉ chép sang
`active_upgrades` khi dựng Ngày mới. Shop không có kho bán (out_of_stock dành cho mở rộng Chợ).
v1.2: `stock` có thể là mảng cá thể — chỉ hiển thị, không hao tươi (T331).
"""

from ..ids import sort_by_id


def upgrade_entry(shop_tuning, upgrade, level):
    """Mục cấp `level` (1..) của nâng cấp `upgrade`, hoặc None."""
    for e in shop_tuning["upgrades"].get(upgrade, []):
        if e.get("level") == level:
            return e
    return None


class ShopSim:
    mode = "day"
    phase = "shop"

    def __init__(self, shop_tuning, day_state, stock):
        self.t = shop_tuning
        self.day = day_state  # DayState: money, upgrades (đọc/ghi)
        if isinstance(stock, list):
            self.stock = [dict(it) for it in stock]  # cá thể dư, không hao
        else:
            self.stock = {k: stock[k] for k in sorted(stock) if stock[k] > 0}  # kho đếm v1.0/v1.1
        self.time_left_ticks = int(shop_tuning["max_ticks"])
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        stock = sort_by_id(self.stock) if isinstance(self.stock, list) else dict(self.stock)
        return {"stock": stock, "shop": self.catalog()}

    def catalog(self) -> dict:
        """Cho UI: mỗi nâng cấp → cấp đã mua, cấp kế (giá) hoặc null khi tối đa."""
        out = {}
        for uid in sorted(self.t["upgrades"]):
            lv = self.day.upgrades.get(uid, 0)
            nxt = upgrade_entry(self.t, uid, lv + 1)
            out[uid] = {"level": lv, "max_level": len(self.t["upgrades"][uid]),
                        "next": dict(nxt) if nxt else None}
        return out

    def buy(self, action, events):
        if action not in self.t["upgrades"]:
            events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            return
        lv = self.day.upgrades.get(action, 0)
        nxt = upgrade_entry(self.t, action, lv + 1)
        if nxt is None:
            events.append(("buy_failed", {"action": action, "reason": "max_level"}))
            return
        price = nxt["price"]
        if self.day.money < price:
            events.append(("buy_failed", {"action": action, "reason": "funds"}))
            return
        self.day.money -= price
        self.day.upgrades[action] = lv + 1
        events.append(("bought", {"upgrade": action, "level": lv + 1, "price": price, "money": self.day.money}))

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy is not None:
            self.buy(inp.buy, events)
        if inp.pressed("shop_done"):
            self._finish("done", events)
        elif self.time_left_ticks <= 0:
            self._finish("time", events)
        return events

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("shop_end", {"reason": reason}))
