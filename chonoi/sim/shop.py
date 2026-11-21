"""Buổi tối muộn — Cửa hàng & Nâng cấp (`shop`).

TV4 (AnhQuanHANU - Phase 2): Xử lý mua nâng cấp (oxygen, hp), kiểm tra quỹ tiền,
cấp tối đa, phát bought / buy_failed và đóng cửa hàng (shop_done hoặc sau 600 tick).
"""

UPGRADES_DEFAULT = {
    "oxygen": {
        1: {"price": 200, "oxygen_max_s": 45},
        2: {"price": 400, "oxygen_max_s": 60},
    },
    "hp": {
        1: {"price": 250, "hp_max": 4},
        2: {"price": 500, "hp_max": 5},
    }
}


class ShopSim:
    mode = "shop"
    phase = "shop"

    def __init__(self, tuning=None, state=None, streams=None, ids=None):
        """
        Khởi tạo lượt Shop.
        state chứa:
          - money (int): số dư hiện tại
          - earned (int): tổng thu (không giảm khi mua)
          - reputation (float): điểm uy tín
          - stock (dict): hàng dư từ ca quán
          - upgrades (dict): map cấp đã mua, ví dụ {"oxygen": 0, "hp": 0}
          - active_upgrades (dict): map cấp đang áp dụng trong ngày hiện tại
          - time_left_ticks (int, mặc định 600)
        """
        self.tuning = tuning or {}
        state = state or {}

        shop_tuning = self.tuning.get("shop", {}) if self.tuning else {}
        self.max_ticks = int(shop_tuning.get("max_ticks", 600))
        self.time_left_ticks = int(state.get("time_left_ticks", self.max_ticks))

        self.money = int(state.get("money", 0))
        self.earned = int(state.get("earned", 0))
        self.reputation = float(state.get("reputation", 3.0))
        self.stock = dict(state.get("stock", {}))

        # upgrades: cấp đã mua (hiển thị ngay khi mua thành công)
        self.upgrades = dict(state.get("upgrades", {}))
        self.upgrades.setdefault("oxygen", 0)
        self.upgrades.setdefault("hp", 0)

        # active_upgrades: cấp đang áp dụng (áp dụng cho ngày hiện tại)
        self.active_upgrades = dict(state.get("active_upgrades", {}))
        self.active_upgrades.setdefault("oxygen", 0)
        self.active_upgrades.setdefault("hp", 0)

        self.day = state.get("day", 1)
        self.day_plan = state.get("day_plan", {})

        # Danh mục nâng cấp
        self.catalog = self._build_catalog(shop_tuning)

        self.done = False
        self.reason = None

    def _build_catalog(self, shop_tuning):
        if "upgrades" in shop_tuning:
            cat = {}
            for up_id, lvls in shop_tuning["upgrades"].items():
                cat[up_id] = {item["level"]: item for item in lvls}
            return cat
        return UPGRADES_DEFAULT

    def snapshot(self) -> dict:
        return {
            "phase": "shop",
            "time_left_ticks": self.time_left_ticks,
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "upgrades": dict(self.upgrades),
            "active_upgrades": dict(self.active_upgrades),
            "money": self.money,
            "earned": self.earned,
            "reputation": self.reputation,
        }

    def step(self, inp):
        events = []
        if self.done:
            return events

        # Đồng hồ đếm ngược thời gian mở Shop (tối đa 600 tick)
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # 1. Xử lý một lệnh buy trước cạnh shop_done, kể cả bước cuối
        buy_cmd = getattr(inp, "buy", None)
        if buy_cmd is None and isinstance(inp, dict):
            buy_cmd = inp.get("buy")

        if buy_cmd:
            self._handle_buy(buy_cmd, events)

        # 2. Đóng Shop: nút shop_done hoặc tự hết giờ
        is_done_button = False
        if hasattr(inp, "pressed") and inp.pressed("shop_done"):
            is_done_button = True
        elif isinstance(inp, dict) and inp.get("shop_done"):
            is_done_button = True

        if is_done_button:
            self.done = True
            self.reason = "done"
            events.append(("shop_end", {"reason": "done"}))
        elif self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("shop_end", {"reason": "time"}))

        return events

    def _handle_buy(self, action: str, events: list):
        # Lệnh không hỗ trợ
        if action not in self.catalog:
            events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            return

        current_level = self.upgrades.get(action, 0)
        next_level = current_level + 1
        level_catalog = self.catalog[action]

        # Đã đạt cấp tối đa
        if next_level not in level_catalog:
            events.append(("buy_failed", {"action": action, "reason": "max_level"}))
            return

        price = level_catalog[next_level]["price"]
        # Không đủ tiền
        if self.money < price:
            events.append(("buy_failed", {"action": action, "reason": "funds"}))
            return

        # Mua thành công: trừ money, giữ earned
        self.money -= price
        self.upgrades[action] = next_level
        events.append((
            "bought",
            {
                "upgrade": action,
                "level": next_level,
                "price": price,
                "money": self.money
            }
        ))

