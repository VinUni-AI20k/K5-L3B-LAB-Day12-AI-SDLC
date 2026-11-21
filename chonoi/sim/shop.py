"""Module Shop & Upgrades (Người B — Phase 2 / TICKET-02).

Quản lý giai đoạn cửa hàng (giữa các ca):
- Mua nâng cấp Bình oxy (oxygen) và Máu/Thể lực (hp):
  + oxygen: Lv 1 (200k -> 45s / 2700 ticks), Lv 2 (400k -> 60s / 3600 ticks).
  + hp: Lv 1 (250k -> 4 HP), Lv 2 (500k -> 5 HP).
- Quy tắc mua:
  + Mua tuần tự (Lv 1 -> Lv 2).
  + Trừ tiền trong ví (money), KHÔNG giảm tổng doanh thu (earned) và điểm số (score).
  + Phát sự kiện `upgrade_bought` khi mua thành công.
  + Phát sự kiện `buy_failed` khi không đủ tiền hoặc đã đạt cấp tối đa (giữ nguyên tiền và cấp).
- Thời gian mở cửa hàng:
  + Tối đa 600 ticks (10s) hoặc kết thúc sớm khi nhận lệnh hoàn tất/interact (`shop_done`).
  + Các nâng cấp có hiệu lực ở buổi tiếp theo (next day / next shift).
"""

import math
from typing import Any, Dict, List, Optional, Tuple

TICK = 60.0
SHOP_DURATION_TICKS = 600  # 10s

UPGRADE_CATALOG = {
    "oxygen": {
        1: {"price": 200, "val": 45, "ticks": 2700, "attr": "oxygen_max_s"},
        2: {"price": 400, "val": 60, "ticks": 3600, "attr": "oxygen_max_s"},
    },
    "hp": {
        1: {"price": 250, "val": 4, "attr": "hp_max"},
        2: {"price": 500, "val": 5, "attr": "hp_max"},
    },
}


class ShopSim:
    mode = "shop"
    phase = "shop"

    def __init__(
        self,
        tuning: Optional[Dict[str, Any]] = None,
        scenario: Optional[Dict[str, Any]] = None,
        streams: Any = None,
        ids: Any = None,
        money: int = 0,
        earned: Optional[int] = None,
        reputation: float = 3.0,
        upgrades: Optional[Dict[str, int]] = None,
        time_left_ticks: int = SHOP_DURATION_TICKS,
    ):
        scen = scenario or {}
        tune = tuning or {}
        shop_tuning = tune.get("shop", {})

        self.tuning = tune
        self.scenario = scen
        self.rng = streams
        self.ids = ids

        # Tiền hiện có (để tiêu dùng)
        self.money = int(scen.get("money", money))
        # Doanh thu tích lũy (không bị trừ khi mua sắm)
        self.earned = int(scen.get("earned", earned if earned is not None else self.money))
        self.reputation = float(scen.get("reputation", reputation))

        # Cấp độ nâng cấp hiện tại: {"oxygen": 0, "hp": 0}
        initial_upgrades = {"oxygen": 0, "hp": 0}
        if upgrades:
            initial_upgrades.update(upgrades)
        if "upgrades" in scen:
            initial_upgrades.update(scen["upgrades"])
        self.upgrades = initial_upgrades

        # Hiệu ứng chờ áp dụng cho ngày tiếp theo
        self.pending_effects: Dict[str, Any] = {}
        for up_id, lvl in self.upgrades.items():
            if up_id in UPGRADE_CATALOG and lvl in UPGRADE_CATALOG[up_id]:
                info = UPGRADE_CATALOG[up_id][lvl]
                self.pending_effects[info["attr"]] = info["val"]

        self.duration_ticks = int(scen.get("time_left_ticks", shop_tuning.get("duration_ticks", time_left_ticks)))
        self.time_left_ticks = self.duration_ticks
        self.phase_tick = 0
        self.done = False
        self.reason: Optional[str] = None

    @property
    def score(self) -> int:
        """Điểm số = earned + 100 * floor(reputation)."""
        mult = 100
        if isinstance(self.tuning, dict) and "score" in self.tuning:
            mult = self.tuning["score"].get("reputation_multiplier", 100)
        return self.earned + mult * math.floor(self.reputation)

    def buy(self, upgrade_id: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Thực hiện mua nâng cấp tuần tự theo upgrade_id ('oxygen' hoặc 'hp')."""
        events: List[Tuple[str, Dict[str, Any]]] = []

        if self.done:
            return events

        if upgrade_id not in UPGRADE_CATALOG:
            events.append(("buy_failed", {
                "upgrade_id": upgrade_id,
                "id": upgrade_id,
                "reason": "invalid_upgrade",
                "money": self.money,
            }))
            return events

        curr_lvl = self.upgrades.get(upgrade_id, 0)
        target_lvl = curr_lvl + 1

        if target_lvl not in UPGRADE_CATALOG[upgrade_id]:
            # Đã đạt cấp tối đa
            events.append(("buy_failed", {
                "upgrade_id": upgrade_id,
                "id": upgrade_id,
                "reason": "max_level",
                "level": curr_lvl,
                "money": self.money,
            }))
            return events

        upgrade_info = UPGRADE_CATALOG[upgrade_id][target_lvl]
        price = upgrade_info["price"]

        if self.money < price:
            # Không đủ tiền
            events.append(("buy_failed", {
                "upgrade_id": upgrade_id,
                "id": upgrade_id,
                "reason": "insufficient_money",
                "price": price,
                "money": self.money,
            }))
            return events

        # Trừ tiền, bảo toàn earned
        self.money -= price
        self.upgrades[upgrade_id] = target_lvl
        self.pending_effects[upgrade_info["attr"]] = upgrade_info["val"]

        events.append(("upgrade_bought", {
            "upgrade_id": upgrade_id,
            "id": upgrade_id,
            "level": target_lvl,
            "price": price,
            "cost": price,
            "money": self.money,
            "value": upgrade_info["val"],
        }))
        return events

    def finish(self, reason: str = "user") -> List[Tuple[str, Dict[str, Any]]]:
        """Đóng cửa hàng sớm."""
        events: List[Tuple[str, Dict[str, Any]]] = []
        if not self.done:
            self.done = True
            self.reason = reason
            events.append(("shop_done", {
                "money": self.money,
                "upgrades": dict(self.upgrades),
                "pending_effects": dict(self.pending_effects),
                "reason": self.reason,
            }))
        return events

    def step(self, inp: Any = None) -> List[Tuple[str, Dict[str, Any]]]:
        """Bước một tick mô phỏng cửa hàng (60 Hz)."""
        events: List[Tuple[str, Dict[str, Any]]] = []
        if self.done:
            return events

        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # Xử lý input nếu có
        if inp is not None:
            # Người chơi bấm E (interact) hoặc lệnh kết thúc
            if hasattr(inp, "pressed") and inp.pressed("interact"):
                self.done = True
                self.reason = "user"
            elif getattr(inp, "finish", False) or getattr(inp, "done", False):
                self.done = True
                self.reason = "user"
            # Nếu input có chỉ thị mua nâng cấp
            buy_req = getattr(inp, "buy", None)
            if buy_req:
                events.extend(self.buy(buy_req))

        if self.time_left_ticks <= 0 and not self.done:
            self.done = True
            self.reason = "time"

        if self.done:
            events.append(("shop_done", {
                "money": self.money,
                "upgrades": dict(self.upgrades),
                "pending_effects": dict(self.pending_effects),
                "reason": self.reason,
            }))

        return events

    def apply_to_tuning(self, tuning: Dict[str, Any]) -> Dict[str, Any]:
        """Áp dụng các nâng cấp đã mua vào tuning cho ngày tiếp theo."""
        if "gather" in tuning:
            g = tuning["gather"]
            if "oxygen_max_s" in self.pending_effects:
                g["oxygen_max_s"] = self.pending_effects["oxygen_max_s"]
            if "hp_max" in self.pending_effects:
                g["hp_max"] = self.pending_effects["hp_max"]
        return tuning

    def snapshot(self) -> Dict[str, Any]:
        """Tạo snapshot trạng thái cửa hàng."""
        return {
            "money": self.money,
            "earned": self.earned,
            "reputation": self.reputation,
            "score": self.score,
            "upgrades": dict(self.upgrades),
            "pending_effects": dict(self.pending_effects),
            "time_left_ticks": self.time_left_ticks,
            "phase_tick": self.phase_tick,
            "done": self.done,
            "reason": self.reason,
        }
