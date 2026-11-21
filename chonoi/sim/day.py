"""Module Day — Vòng lặp Ngày (Người B — Phase 3 / Chế độ --mode day).

Quản lý vòng lặp Ngày 1 đến Ngày 5 (D1..D5):
  DayIntro -> gather -> EveningIntro -> quan -> DayResult -> Shop -> Next Day

Đặc tả:
1. DayIntro: Mở đầu ngày D_i, công bố thực đơn Má Tư (D1..D5).
2. gather: Buổi sáng lặn hái và bắt cá (GatherSim) với tuning đã áp dụng nâng cấp.
3. EveningIntro: Chuyển giao kho thu hoạch sang quán tối, chuẩn bị mở cửa.
4. quan: Mở quán tối (QuanSim), khách chỉ gọi món trong thực đơn ngày nếu đủ kho.
5. DayResult: Tổng kết ca, tiền kiếm được, tiền boa và uy tín.
6. Shop: Mở cửa hàng nâng cấp (ShopSim), mua bình oxy/máu -> nạp hiệu ứng cho ngày tiếp theo.
7. Next Day / Day End: Chuyển sang ngày tiếp theo (bảo lưu tiền, uy tín, nâng cấp) hoặc kết thúc sau D5.
"""

import copy
import math
from typing import Any, Dict, List, Optional, Tuple

from ..ids import IdAllocator
from ..rng import Streams
from .gather import GatherSim
from .quan import QuanSim
from .shop import ShopSim

TICK = 60.0

# Thực đơn kế hoạch mặc định của Má Tư từ Ngày 1 đến Ngày 5
DEFAULT_DAILY_MENU: Dict[int, List[str]] = {
    1: ["ca_loc_nuong_trui", "goi_bong_sung"],
    2: ["ca_loc_nuong_trui", "goi_bong_sung", "canh_chua_ca_loc"],
    3: ["ca_loc_nuong_trui", "goi_bong_sung", "canh_chua_ca_loc", "ca_keo_nuong"],
    4: ["ca_loc_nuong_trui", "goi_bong_sung", "canh_chua_ca_loc", "ca_keo_nuong", "lau_ca_linh_dien_dien"],
    5: ["ca_loc_nuong_trui", "goi_bong_sung", "canh_chua_ca_loc", "ca_keo_nuong", "lau_ca_linh_dien_dien", "lau_mam"],
}


class DaySim:
    mode = "day"

    def __init__(
        self,
        tuning: Dict[str, Any],
        scenario: Optional[Dict[str, Any]] = None,
        streams: Optional[Any] = None,
        ids: Optional[Any] = None,
        inventory: Optional[Dict[str, int]] = None,
    ):
        self.tuning = copy.deepcopy(tuning)
        scen = scenario or {}
        self.scenario = scen
        self.rng = streams or Streams(1)
        self.ids = ids or IdAllocator()

        # Thông số ngày
        self.day = int(scen.get("day", 1))
        self.max_days = int(scen.get("max_days", 5))

        # Tài chính và uy tín tích lũy qua các ngày
        self.money = int(scen.get("money", 0))
        self.earned = int(scen.get("earned", self.money))
        init_rep = float(tuning.get("quan", {}).get("reputation_initial", 3.0))
        self.reputation = float(scen.get("reputation", init_rep))

        # Cấp độ nâng cấp tích lũy
        self.upgrades = dict(scen.get("upgrades", {"oxygen": 0, "hp": 0}))

        # Kho nguyên liệu tích lũy
        self.stock = dict(inventory if inventory is not None else scen.get("stock", {}))

        # Thời lượng các pha chuyển cảnh (ticks, mặc định 60 = 1s)
        self.intro_ticks_duration = int(scen.get("intro_ticks", 60))

        # Pha hiện tại
        self.phase = "day_intro"
        self.phase_tick = 0
        self.time_left_ticks = self.intro_ticks_duration
        self.active_sim: Optional[Any] = None

        self.done = False
        self.reason: Optional[str] = None

    @property
    def score(self) -> int:
        """Điểm số tích lũy: score = earned + 100 * floor(reputation)."""
        mult = 100
        if "score" in self.tuning and isinstance(self.tuning["score"], dict):
            mult = self.tuning["score"].get("reputation_multiplier", 100)
        return self.earned + mult * math.floor(self.reputation)

    def get_daily_menu(self, day: int) -> List[str]:
        """Lấy thực đơn kế hoạch Má Tư cho ngày `day`. Ưu tiên gọi hàm của Người A nếu có."""
        try:
            from .kitchen import get_daily_menu as kitchen_menu
            res = kitchen_menu(day)
            if res:
                return list(res)
        except (ImportError, AttributeError):
            pass

        # Tra trong scenario / tuning nếu có
        if "daily_menu" in self.scenario:
            dm = self.scenario["daily_menu"]
            if str(day) in dm:
                return list(dm[str(day)])
            if day in dm:
                return list(dm[day])

        all_menu = list(self.tuning.get("menu", {}).keys())
        return list(DEFAULT_DAILY_MENU.get(day, all_menu))

    def _start_gather(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Bắt đầu buổi sáng: lặn hái và bắt cá."""
        self.phase = "gather"
        self.phase_tick = 0
        gather_scen = dict(self.scenario.get("gather", {}))
        self.active_sim = GatherSim(self.tuning, gather_scen, self.rng, self.ids, day=self.day)
        self.time_left_ticks = self.active_sim.time_left_ticks
        return [("phase_started", {"phase": "gather", "day": self.day})]

    def _start_evening_intro(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Chuyển giao từ sáng sang tối: kiểm kê kho thu hoạch."""
        self.phase = "evening_intro"
        self.phase_tick = 0
        self.time_left_ticks = self.intro_ticks_duration
        self.active_sim = None
        return [("evening_intro", {
            "day": self.day,
            "stock": dict(self.stock),
            "menu": self.get_daily_menu(self.day),
        })]

    def _start_quan(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Bắt đầu buổi tối: mở quán ăn với thực đơn kế hoạch của ngày."""
        self.phase = "quan"
        self.phase_tick = 0

        # Lọc thực đơn theo kế hoạch Má Tư công bố đầu ngày
        planned_dishes = self.get_daily_menu(self.day)
        quan_tuning = copy.deepcopy(self.tuning)
        if "menu" in quan_tuning:
            quan_tuning["menu"] = {k: v for k, v in quan_tuning["menu"].items() if k in planned_dishes}

        quan_scen = dict(self.scenario.get("quan", {}))
        quan_scen["stock"] = dict(self.stock)
        quan_scen["reputation"] = self.reputation

        self.active_sim = QuanSim(quan_tuning, quan_scen, self.rng, self.ids, inventory=self.stock)
        # Đồng bộ tài chính tích lũy
        self.active_sim.money = self.money
        self.active_sim.earned = self.earned
        self.time_left_ticks = self.active_sim.time_left_ticks

        return [("phase_started", {
            "phase": "quan",
            "day": self.day,
            "menu": planned_dishes,
            "stock": dict(self.stock),
        })]

    def _start_day_result(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Tổng kết kết quả ngày sau khi quán đóng cửa."""
        self.phase = "day_result"
        self.phase_tick = 0
        self.time_left_ticks = self.intro_ticks_duration
        self.active_sim = None
        return [("day_result", {
            "day": self.day,
            "money": self.money,
            "earned": self.earned,
            "reputation": round(float(self.reputation), 3),
            "score": self.score,
        })]

    def _start_shop(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Mở cửa hàng ban đêm cho người chơi nâng cấp trang bị."""
        self.phase = "shop"
        self.phase_tick = 0
        shop_scen = dict(self.scenario.get("shop", {}))
        self.active_sim = ShopSim(
            self.tuning,
            shop_scen,
            self.rng,
            self.ids,
            money=self.money,
            earned=self.earned,
            reputation=self.reputation,
            upgrades=self.upgrades,
        )
        self.time_left_ticks = self.active_sim.time_left_ticks
        return [("phase_started", {"phase": "shop", "day": self.day, "money": self.money})]

    def step(self, inp: Any) -> List[Tuple[str, Dict[str, Any]]]:
        """Bước một tick của chế độ Day (60 Hz)."""
        events: List[Tuple[str, Dict[str, Any]]] = []
        if self.done:
            return events

        self.phase_tick += 1

        # 1. Pha DayIntro (Đầu ngày)
        if self.phase == "day_intro":
            self.time_left_ticks = max(0, self.time_left_ticks - 1)
            # Khởi tạo ngày ở tick đầu tiên
            if self.phase_tick == 1:
                menu = self.get_daily_menu(self.day)
                events.append(("day_start", {"day": self.day, "menu": menu}))
                events.append(("day_intro", {"day": self.day, "menu": menu}))

            user_skip = hasattr(inp, "pressed") and inp.pressed("interact")
            if self.time_left_ticks <= 0 or user_skip:
                events.extend(self._start_gather())
            return events

        # 2. Pha Gather (Buổi sáng)
        elif self.phase == "gather":
            if self.active_sim is not None:
                sub_evs = self.active_sim.step(inp)
                events.extend(sub_evs)
                self.time_left_ticks = self.active_sim.time_left_ticks

                if self.active_sim.done:
                    # Thu thập nguyên liệu từ giỏ
                    harvest = self.active_sim.inventory_items()
                    for k, q in harvest.items():
                        self.stock[k] = self.stock.get(k, 0) + q

                    events.append(("gather_completed", {
                        "day": self.day,
                        "harvest": harvest,
                        "stock": dict(self.stock),
                    }))
                    events.extend(self._start_evening_intro())
            return events

        # 3. Pha EveningIntro (Chiều tối giao mùa)
        elif self.phase == "evening_intro":
            self.time_left_ticks = max(0, self.time_left_ticks - 1)
            user_skip = hasattr(inp, "pressed") and inp.pressed("interact")
            if self.time_left_ticks <= 0 or user_skip:
                events.extend(self._start_quan())
            return events

        # 4. Pha Quan (Buổi tối)
        elif self.phase == "quan":
            if self.active_sim is not None:
                sub_evs = self.active_sim.step(inp)
                events.extend(sub_evs)
                self.time_left_ticks = self.active_sim.time_left_ticks

                if self.active_sim.done:
                    # Cập nhật tiền, uy tín và kho tồn
                    self.money = self.active_sim.money
                    self.earned = self.active_sim.earned
                    self.reputation = self.active_sim.reputation
                    self.stock = dict(self.active_sim.stock)

                    events.append(("quan_completed", {
                        "day": self.day,
                        "money": self.money,
                        "earned": self.earned,
                        "reputation": round(float(self.reputation), 3),
                    }))
                    events.extend(self._start_day_result())
            return events

        # 5. Pha DayResult (Tổng kết ngày)
        elif self.phase == "day_result":
            self.time_left_ticks = max(0, self.time_left_ticks - 1)
            user_skip = hasattr(inp, "pressed") and inp.pressed("interact")
            if self.time_left_ticks <= 0 or user_skip:
                events.extend(self._start_shop())
            return events

        # 6. Pha Shop (Ban đêm)
        elif self.phase == "shop":
            if self.active_sim is not None:
                sub_evs = self.active_sim.step(inp)
                events.extend(sub_evs)
                self.time_left_ticks = self.active_sim.time_left_ticks

                if self.active_sim.done:
                    # Cập nhật tiền và cấp nâng cấp
                    self.money = self.active_sim.money
                    self.upgrades = dict(self.active_sim.upgrades)
                    # Áp dụng chỉ số nâng cấp vào tuning cho ngày tiếp theo
                    self.active_sim.apply_to_tuning(self.tuning)

                    events.append(("shop_completed", {
                        "day": self.day,
                        "money": self.money,
                        "upgrades": dict(self.upgrades),
                    }))

                    # Kiểm tra chuyển ngày hoặc kết thúc game (sau D5)
                    if self.day < self.max_days:
                        self.day += 1
                        self.phase = "day_intro"
                        self.phase_tick = 0
                        self.time_left_ticks = self.intro_ticks_duration
                        events.append(("next_day", {"day": self.day}))
                    else:
                        self.done = True
                        self.reason = "completed"
                        events.append(("day_end", {
                            "total_days": self.day,
                            "score": self.score,
                            "money": self.money,
                            "earned": self.earned,
                            "reputation": round(float(self.reputation), 3),
                            "upgrades": dict(self.upgrades),
                        }))
            return events

        return events

    def snapshot(self) -> Dict[str, Any]:
        """Tạo snapshot trạng thái của chế độ Day."""
        snap = {
            "day": self.day,
            "max_days": self.max_days,
            "phase": self.phase,
            "money": self.money,
            "earned": self.earned,
            "reputation": round(float(self.reputation), 3),
            "score": self.score,
            "upgrades": dict(self.upgrades),
            "stock": dict(self.stock),
            "time_left_ticks": self.time_left_ticks,
            "phase_tick": self.phase_tick,
            "done": self.done,
            "reason": self.reason,
        }
        if self.active_sim is not None and hasattr(self.active_sim, "snapshot"):
            snap["sub_sim"] = self.active_sim.snapshot()
        return snap
