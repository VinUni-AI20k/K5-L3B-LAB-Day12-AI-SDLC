"""Mode `day` (Ticket-02 mục 2, 4.3–4.5). Lát 5.

Một Ngày: day_start -> day_plan -> phase_start(gather) -> gather ... gather_end -> phase_start(quan)
-> quan ... quan_end -> phase_start(shop) -> shop ... shop_end -> (Ngày kế hoặc kết thúc days_complete).

- Chỉ gọi giao diện chung của từng pha: `step(inp)`, `done`, `snapshot()`, `inventory_items()` (gather).
- Kho bàn giao trong bộ nhớ; ngất vẫn mở quán với kho rỗng.
- Tiền, earned, uy tín và cấp đã mua giữ qua Ngày. Cấp mua trong Shop vào `upgrades` ngay,
  chỉ chép sang `active_upgrades` khi dựng Ngày mới; oxy/Máu tối đa của buổi sáng lấy theo `active_upgrades`.
- Sự kiện trả về dạng (phase, day, name, data): sự kiện kết thúc mang pha cũ, `phase_start` mang pha mới.
"""

import copy

from ..contract import plan_ingredients
from ..errors import BadInput
from ..ids import IdAllocator
from ..rng import Streams
from .gather import GatherSim
from .quan import QuanSim
from .shop import ShopSim

# nâng cấp -> khóa tuning.gather bị thay bằng giá trị của cấp đang áp dụng
UPGRADE_STAT = {"oxygen": "oxygen_max_s", "hp": "hp_max"}


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, seed, days):
        self.tuning = tuning
        self.days = days
        self.streams, self.ids = Streams(seed), IdAllocator()
        d = scenario.get("day", {})
        self._money = d.get("money", 0)
        self._earned = d.get("earned", 0)
        self._reputation = d.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(d.get("upgrades", {}))
        self.active_upgrades = {}
        self.plans = self._build_plans(d.get("day_plan", []))
        self._gather_tpl = scenario.get("gather", {})
        self._quan_tpl = scenario.get("quan", {})
        self.day = 0
        self.days_completed = 0
        self.done = False
        self.reason = None
        self.sub = None
        self.phase_tick = 0
        self._pending = []
        self._start_day(self._pending)

    # --- trạng thái chung cho runner ----------------------------------------------
    @property
    def phase(self) -> str:
        return self.sub.phase

    @property
    def time_left_ticks(self) -> int:
        return self.sub.time_left_ticks

    @property
    def money(self) -> int:
        return self.sub.money if isinstance(self.sub, (QuanSim, ShopSim)) else self._money

    @property
    def earned(self) -> int:
        return self.sub.earned if isinstance(self.sub, QuanSim) else self._earned

    @property
    def reputation(self):
        return self.sub.reputation if isinstance(self.sub, QuanSim) else self._reputation

    def initial_events(self) -> list:
        """Sự kiện tick 0 (day_start, day_plan, phase_start) — runner ghi trước snapshot tick 0."""
        out, self._pending = self._pending, []
        return out

    def snapshot(self) -> dict:
        bought = self.sub.upgrades if isinstance(self.sub, ShopSim) else self.upgrades  # cấp vừa mua hiện ngay
        s = {"day": self.day, "day_plan": self._plan_data(),
             "upgrades": dict(sorted(bought.items())),
             "active_upgrades": dict(sorted(self.active_upgrades.items()))}
        s.update(self.sub.snapshot())
        return s

    def step(self, inp) -> list:
        self.phase_tick += 1
        phase, day = self.sub.phase, self.day
        out = [(phase, day, name, data) for name, data in self.sub.step(inp)]
        if self.sub.done:
            self._next_phase(out)
        return out

    # --- chuyển pha ---------------------------------------------------------------
    def _next_phase(self, out):
        if isinstance(self.sub, GatherSim):
            self._open_quan(self.sub.inventory_items(), out)
        elif isinstance(self.sub, QuanSim):
            q = self.sub
            self._money, self._earned, self._reputation = q.money, q.earned, q.reputation
            self._begin("shop", ShopSim(self.tuning["shop"], self._money, self.upgrades, q.stock), out)
        else:
            self._money, self.upgrades = self.sub.money, dict(self.sub.upgrades)
            self.days_completed += 1
            if self.days_completed >= self.days:
                self.done = True
                self.reason = "days_complete"
            else:
                self._start_day(out)

    def _start_day(self, out):
        self.day += 1
        self.active_upgrades = dict(self.upgrades)
        gather = GatherSim(self._gather_tuning(), copy.deepcopy(self._gather_tpl), self.streams, self.ids,
                           day=self.day)  # bố trí Cá Sấu theo Ngày (M2 từ Ngày 3)
        out.append(("gather", self.day, "day_start", {}))
        out.append(("gather", self.day, "day_plan", self._plan_data()))
        self._begin("gather", gather, out)

    def _open_quan(self, items, out):
        dishes = self.plans[self.day]["dishes"]
        tpl = copy.deepcopy(self._quan_tpl)
        for c in tpl.get("customers", []):
            if c.get("dish_id") not in dishes:
                raise BadInput(f"Ngày {self.day}: khách {c.get('id')} gọi món ngoài kế hoạch")
        carry = {"money": self._money, "earned": self._earned, "reputation": self._reputation}
        quan = QuanSim(self.tuning, tpl, self.streams, self.ids, inventory=dict(items),
                       allowed_dishes=list(dishes), carry=carry)
        self._begin("quan", quan, out)

    def _begin(self, phase, sim, out):
        self.sub = sim
        self.phase_tick = 0
        out.append((phase, self.day, "phase_start", {}))

    # --- dữ liệu ----------------------------------------------------------------------
    def _build_plans(self, overrides) -> dict:
        menu = self.tuning["menu"]
        plans = {e["day"]: dict(e["dishes"]) for e in self.tuning["day_plan"]}
        for e in overrides:
            plans[e["day"]] = dict(e["dishes"])
        return {day: {"dishes": dishes, "ingredients": plan_ingredients(dishes, menu)}
                for day, dishes in plans.items()}

    def _plan_data(self) -> dict:
        p = self.plans[self.day]
        return {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])}

    def _gather_tuning(self) -> dict:
        """Bản sao tuning với oxy/Máu tối đa theo cấp đang áp dụng (cấp 0 = số cơ sở)."""
        t = copy.deepcopy(self.tuning)
        for kind, stat in UPGRADE_STAT.items():
            level = self.active_upgrades.get(kind, 0)
            if level:
                t["gather"][stat] = self.tuning["shop"]["upgrades"][kind][level - 1][stat]
        return t
