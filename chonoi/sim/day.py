"""Vòng Ngày (`--mode day`, Test Contract v1.1 mục 2, 4.1, 4.3–4.5).

Một Ngày: day_start -> day_plan -> phase_start(gather) -> gather -> (gather_end) dựng quán từ kho bàn giao
trong bộ nhớ + phase_start(quan) CÙNG tick (kể cả ngất: kho rỗng) -> quan -> (quan_end) dựng Shop +
phase_start(shop) cùng tick -> Shop -> (shop_end) days_completed += 1 -> dựng Ngày kế cùng tick, hoặc kết
thúc `days_complete`. Pha mới chỉ chạy gameplay từ bước sau.

Xuyên Ngày: money, earned, reputation, cấp đã mua (`upgrades`). Chỉ khi DỰNG Ngày mới mới chép
`upgrades` sang `active_upgrades`; oxy và Máu hồi đầy theo cấp đang áp dụng; giỏ dựng lại từ mẫu
scenario; kho dư sau Shop bị bỏ.

Mỗi event trả về là dict {phase, day, name, data}: một bước có thể đi qua nhiều pha / Ngày (ví dụ
shop_end của Ngày 1 rồi day_start của Ngày 2), nên vỏ event lấy pha và Ngày tại lúc phát.
"""

import copy
import inspect

from ..errors import BadInput
from .gather import GatherSim
from .quan import QuanSim
from .shop import ShopSim

UPGRADE_FIELD = {"oxygen": "oxygen_max_s", "hp": "hp_max"}


def recipe_total(menu, dishes):
    """Tổng nguyên liệu = tổng công thức × số suất, sắp theo id nguyên liệu."""
    total = {}
    for dish_id in sorted(dishes):
        for k, n in menu[dish_id]["recipe"].items():
            total[k] = total.get(k, 0) + n * dishes[dish_id]
    return {k: total[k] for k in sorted(total)}


def upgrade_value(tuning, upgrade, level):
    """Giá trị tuning theo cấp (0 = cơ sở trong tuning.gather)."""
    field = UPGRADE_FIELD[upgrade]
    if not level:
        return tuning["gather"][field]
    lv = next(x for x in tuning["shop"]["upgrades"][upgrade] if x["level"] == level)
    return lv[field]


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.streams = streams
        self.ids = ids
        self.days = days
        self.tpl_gather = scenario.get("gather", {})
        self.tpl_quan = scenario.get("quan", {})
        d = scenario.get("day", {})
        self.money = d.get("money", 0)
        self.earned = d.get("earned", 0)
        self.reputation = d.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(d.get("upgrades", {}))
        self.active_upgrades = {}
        self.plans = {p["day"]: p for p in tuning["day_plan"]}
        for p in d.get("day_plan", []):
            self.plans[p["day"]] = {"day": p["day"], "dishes": dict(p["dishes"]),
                                    "ingredients": recipe_total(tuning["menu"], p["dishes"])}
        self.day = 0
        self.days_completed = 0
        self.cur = None
        self.phase = "gather"
        self.done = False
        self.reason = None
        self.initial_events = []
        self._start_day(self.initial_events)

    # --- giao diện cho runner -----------------------------------------------------
    @property
    def phase_tick(self):
        return getattr(self.cur, "phase_tick", self._gather_tick)

    @property
    def time_left_ticks(self):
        return self.cur.time_left_ticks

    def plan(self):
        p = self.plans[self.day]
        return {"dishes": {k: p["dishes"][k] for k in sorted(p["dishes"])}, "ingredients": dict(p["ingredients"])}

    def snapshot(self) -> dict:
        s = {"day": self.day, "day_plan": self.plan(), "days_completed": self.days_completed,
             "upgrades": {k: self.upgrades[k] for k in sorted(self.upgrades)},
             "active_upgrades": {k: self.active_upgrades[k] for k in sorted(self.active_upgrades)}}
        s.update(self.cur.snapshot())
        return s

    def step(self, inp):
        out = []
        raw = self.cur.step(inp)
        if self.phase == "gather":
            self._gather_tick += 1
        self._emit(out, raw)
        if self.cur.done:
            if self.phase == "gather":
                self._open_quan(out)
            elif self.phase == "quan":
                self.money, self.earned, self.reputation = self.cur.money, self.cur.earned, self.cur.reputation
                self._open_shop(out)
            else:
                self.money = self.cur.money
                self.days_completed += 1
                if self.days_completed >= self.days:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    self._start_day(out)
        elif self.phase == "quan":
            self.money, self.earned, self.reputation = self.cur.money, self.cur.earned, self.cur.reputation
        elif self.phase == "shop":
            self.money = self.cur.money
        return out

    # --- đổi pha --------------------------------------------------------------------
    def _emit(self, out, raw):
        for name, data in raw:
            out.append({"phase": self.phase, "day": self.day, "name": name, "data": data})

    def _start_day(self, out):
        self.day += 1
        self.active_upgrades = dict(self.upgrades)  # chỉ lúc dựng Ngày mới
        self.phase = "gather"
        self._gather_tick = 0
        self.cur = self._build_gather()
        self._emit(out, [("day_start", {}), ("day_plan", self.plan()), ("phase_start", {})])

    def _build_gather(self):
        t = copy.deepcopy(self.tuning)
        oxy = upgrade_value(self.tuning, "oxygen", self.active_upgrades.get("oxygen", 0))
        hp = upgrade_value(self.tuning, "hp", self.active_upgrades.get("hp", 0))
        t["gather"]["oxygen_max_s"], t["gather"]["hp_max"] = oxy, hp
        params = inspect.signature(GatherSim.__init__).parameters
        kw = {}
        if "day" in params:
            kw["day"] = self.day
        if "oxygen_max_s" in params:
            kw["oxygen_max_s"] = oxy
        if "hp_max" in params:
            kw["hp_max"] = hp
        if "reissue_hold_ids" in params:
            # v1.2: Ngày đầu giữ id mẫu gather.hold; Ngày kế cấp id mới theo thứ tự mảng, kind/fresh ban đầu
            kw["reissue_hold_ids"] = self.day > 1
        g = GatherSim(t, copy.deepcopy(self.tpl_gather), self.streams, self.ids, **kw)
        g.money, g.earned, g.reputation = self.money, self.earned, self.reputation
        return g

    def _open_quan(self, out):
        # v1.2: bàn giao trong bộ nhớ CÙNG tick gather_end (không hao thêm), mảng cá thể giữ id/độ tươi
        # (kể cả hàng ươn; rỗng nếu ngất). Quán chạy gameplay từ bước sau.
        stock = [dict(it) for it in self.cur.inventory_items()]
        try:
            q = QuanSim(self.tuning, copy.deepcopy(self.tpl_quan), self.streams, self.ids, inventory=stock,
                        menu_filter=list(self.plans[self.day]["dishes"]), reputation=self.reputation,
                        money=self.money, earned=self.earned)
        except BadInput as e:
            raise BadInput(f"Ngày {self.day}, mở quán với kho thực {stock}: {e}")
        self.phase, self.cur = "quan", q
        self._emit(out, [("phase_start", {})])

    def _open_shop(self, out):
        leftover = self.cur.stock  # v1.2: mảng cá thể (kể cả hàng ươn), Shop không hao tươi
        self.phase = "shop"
        self.cur = ShopSim(self.tuning, self.money, self.upgrades, stock=leftover)
        self._emit(out, [("phase_start", {})])
