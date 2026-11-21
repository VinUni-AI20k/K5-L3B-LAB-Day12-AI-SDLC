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

TICK = 60.0


class ShopSim:
    mode = "day"
    phase = "shop"

    def __init__(self, tuning, stock, carry, upgrades):
        self.t = tuning["shop"]
        self.stock = dict(stock)
        self.money = carry["money"]
        self.earned = carry["earned"]
        self.reputation = carry["reputation"]
        self.upgrades = dict(upgrades)
        self.time_left_ticks = int(self.t["max_ticks"])
        self.phase_tick = 0
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        """TODO(C): stock dư (bỏ mục bằng 0), upgrades, ... theo Ticket-02 mục 4.4."""
        return {}

    def step(self, inp):
        """TODO(C): buy -> shop_done -> hết giờ (shop_end), theo luật ở docstring module. Trả list (name, data)."""
        return []
