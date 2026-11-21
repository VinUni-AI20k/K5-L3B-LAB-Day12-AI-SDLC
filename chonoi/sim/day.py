"""Chế độ `day` (v1.1, Ticket-02 mục 2 và 4): một Ngày = Lặn và Hái → Mở Quán → Shop, lặp theo `--days`.

`DaySim` ghép các sim đã có (GatherSim, QuanSim, ShopSim) mà không đổi luật của chúng. Nó có cùng giao diện với
GatherSim và QuanSim để `runner.Session` dùng chung: step(inp), snapshot(), done, reason, phase, mode,
time_left_ticks, money, earned, reputation.

Thứ tự chuyển pha (mục 4.5): day_start → day_plan → phase_start(gather) lúc tick 0; sau gather_end dựng quán và
phát phase_start(quan) CÙNG tick (kể cả khi ngất); sau quan_end dựng Shop và phát phase_start(shop) cùng tick;
đóng Shop thì tăng days_completed rồi kết thúc (reason days_complete) hoặc dựng Ngày mới ngay tick đó.
Pha mới chỉ chạy gameplay từ bước sau. Sự kiện kết thúc (gather_end, quan_end, shop_end) mang pha cũ.

Bàn giao kho theo schema kho đếm v1.0, trong bộ nhớ. Tiền, tổng thu, uy tín và cấp nâng cấp giữ xuyên Ngày;
oxy và Máu hồi đầy mỗi Ngày theo cấp ĐANG CÓ HIỆU LỰC (`active_upgrades`), cấp vừa mua (`upgrades`) chỉ có hiệu lực
khi dựng Ngày mới.
"""

from ..ids import IdAllocator
from ..inventory import inventory_schema
from ..scenario import check_reserved_within_stock
from .gather import GatherSim
from .quan import QuanSim
from .shop import ShopSim, apply_gather_upgrades


def plan_ingredients(menu, dishes):
    """Nguyên liệu cần = tổng công thức × số suất (mục 2, bảng kế hoạch Ngày)."""
    need = {}
    for dish, count in dishes.items():
        for kind, qty in menu[dish]["recipe"].items():
            need[kind] = need.get(kind, 0) + qty * count
    return need


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, days, *, contract_version="1.1"):
        self.tuning = tuning
        self.streams = streams
        self.days = days
        self.contract_version = contract_version
        self._item_ids = IdAllocator() if inventory_schema(contract_version) == "individuals" else None
        block = scenario.get("day", {})
        self._gather_tpl = scenario.get("gather", {})
        self._quan_tpl = scenario.get("quan", {})
        self._plan_override = block.get("day_plan", [])
        self._money = block.get("money", 0)
        self._earned = block.get("earned", 0)
        self._reputation = block.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = {"oxygen": 0, "hp": 0, **block.get("upgrades", {})}
        self.active_upgrades = dict(self.upgrades)
        self.day = 0
        self.days_completed = 0
        self.sim_tick = 0
        self.phase_tick = 0
        self.done = False
        self.reason = None
        self.plan = None
        self.phase = None
        self.current = None
        self._pending = []
        self._start_day()

    # --- giao diện cho runner -------------------------------------------------------
    @property
    def time_left_ticks(self):
        return self.current.time_left_ticks

    @property
    def money(self):
        return self.current.money

    @property
    def earned(self):
        return self.current.earned

    @property
    def reputation(self):
        return self.current.reputation

    def start_events(self):
        """Sự kiện ở tick 0 (một lần)."""
        events, self._pending = self._pending, []
        return events

    def snapshot(self) -> dict:
        snap = self.current.snapshot()
        upgrades = self.current.upgrades if self.phase == "shop" else self.upgrades  # cấp vừa mua hiện ngay
        snap.update({"day": self.day, "day_plan": self.plan, "upgrades": dict(upgrades),
                     "active_upgrades": dict(self.active_upgrades)})
        return snap

    def step(self, inp):
        self.sim_tick += 1
        self.phase_tick += 1
        phase = self.phase
        if phase == "shop":
            events = self.current.step(inp.buy, done=inp.pressed("shop_done"))
        else:
            events = self.current.step(inp)
        out = [(name, data, {"phase": phase, "day": self.day}) for name, data in events]
        if self.current.done:
            out.extend({"gather": self._open_quan, "quan": self._open_shop, "shop": self._close_day}[phase]())
        return out

    # --- chuyển pha -----------------------------------------------------------------
    def _meta(self, phase):
        return {"phase": phase, "day": self.day}

    def _plan_for(self, day):
        menu = self.tuning["menu"]
        i = day - 1
        if i < len(self._plan_override):
            dishes = dict(self._plan_override[i]["dishes"])
        else:
            dishes = dict(self.tuning["day_plan"][i % len(self.tuning["day_plan"])]["dishes"])
        return {"dishes": dishes, "ingredients": plan_ingredients(menu, dishes)}

    def _start_day(self):
        self.day += 1
        self.active_upgrades = dict(self.upgrades)
        self.plan = self._plan_for(self.day)
        gather_tuning = apply_gather_upgrades(self.tuning, self.active_upgrades)
        scenario = self._gather_tpl
        if self._item_ids is not None and self.day > 1 and scenario.get("hold"):
            # Mẫu áp lại mỗi ngày nhưng mỗi món của ngày mới là cá thể mới.
            scenario = {**scenario, "hold": [
                {**item, "id": self._item_ids.new("I")} for item in scenario["hold"]
            ]}
        sim = GatherSim(gather_tuning, scenario, self.streams, IdAllocator(), day=self.day,
                        contract_version=self.contract_version, item_ids=self._item_ids)
        sim.money, sim.earned, sim.reputation = self._money, self._earned, self._reputation
        self.current, self.phase, self.phase_tick = sim, "gather", 0
        meta = self._meta("gather")
        self._pending = [("day_start", {}, meta), ("day_plan", self.plan, meta), ("phase_start", {}, meta)]

    def _open_quan(self):
        gather = self.current
        stock = gather.inventory_items()
        options = {}
        if self._item_ids is None:
            check_reserved_within_stock(self._quan_tpl, stock)
        else:
            # Quan v1.2 kiểm giữ chỗ theo ID trên kho thực nhận.
            options["contract_version"] = self.contract_version
        quan = QuanSim(self.tuning, self._quan_tpl, self.streams, IdAllocator(), inventory=stock,
                       allowed_dishes=self.plan["dishes"], money=gather.money, earned=gather.earned,
                       shift_earned=0, reputation=gather.reputation, **options)
        self.current, self.phase, self.phase_tick = quan, "quan", 0
        return [("phase_start", {}, self._meta("quan"))]

    def _open_shop(self):
        quan = self.current
        leftover = quan.snapshot()["stock"]  # dạng xuất, chỉ để hiển thị và bỏ sau Shop
        shop = ShopSim(self.tuning, money=quan.money, earned=quan.earned, reputation=quan.reputation,
                       stock=leftover, upgrades=self.upgrades)
        self.current, self.phase, self.phase_tick = shop, "shop", 0
        return [("phase_start", {}, self._meta("shop"))]

    def _close_day(self):
        shop = self.current
        self._money, self._earned, self._reputation = shop.money, shop.earned, shop.reputation
        self.upgrades = dict(shop.upgrades)
        self.days_completed += 1
        if self.day >= self.days:
            self.done, self.reason = True, "days_complete"
            return []
        self._start_day()
        return self.start_events()
