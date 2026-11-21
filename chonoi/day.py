"""`--mode day` — vòng ngày gather -> quan -> shop (TICKET-02 mục 2, Test Contract v1.1 mục 4.3–4.5).

Đổi pha (cùng tick với event kết thúc của pha cũ; pha mới chạy gameplay từ bước sau):
  dựng Ngày:  day_start -> day_plan -> phase_start(gather)      (Ngày 1: ở tick 0, trước snapshot đầu)
  gather_end  -> dựng quán từ kho bàn giao (kể cả ngất: kho rỗng) -> phase_start(quan)
  quan_end    -> dựng Shop -> phase_start(shop)
  shop_end    -> days_completed += 1 -> Ngày kế (sao cấp đã mua sang active_upgrades) hoặc kết thúc days_complete
Xuyên Ngày: money, earned, reputation, upgrades (đã mua). Oxy/Máu hồi đầy theo active_upgrades, giỏ làm mới,
kho dư bị bỏ sau Shop. Một Streams và một IdAllocator cho cả lượt (tất định theo seed).
Snapshot mọi pha thêm day, day_plan, upgrades, active_upgrades; event có thêm `day`.
"""

import copy

from .contract import plan_ingredients
from .errors import BadInput
from .ids import IdAllocator
from .rng import Streams
from .runner import Session, score_of
from .sim.gather import GatherSim
from .sim.quan import QuanSim
from .sim.shop import ShopSim


def merged_day_plan(tuning, override, days=5):
    """Kế hoạch preset D1–D5 lặp lại; ghi đè scenario cũng lặp theo chu kỳ."""
    plan = {p["day"]: {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])}
            for p in tuning["day_plan"]}
    for p in override or []:
        plan[p["day"]] = {"dishes": dict(p["dishes"]), "ingredients": plan_ingredients(p["dishes"], tuning["menu"])}
    return {
        day: {key: dict(value) for key, value in plan[(day - 1) % 5 + 1].items()}
        for day in range(1, days + 1)
    }


class DaySession(Session):
    def __init__(self, tuning, scenario, seed, days=1):
        if isinstance(days, bool) or not isinstance(days, int) or days < 1:
            raise BadInput("days phải là số nguyên dương")
        self.mode = "day"
        self.tuning = tuning
        self.gather_tpl = scenario.get("gather", {})
        self.quan_tpl = scenario.get("quan", {})
        d = scenario.get("day", {})
        self.streams = Streams(seed)
        self.ids = IdAllocator()
        self.money = d.get("money", 0)
        self.earned = d.get("earned", 0)
        self.reputation = float(d.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = dict(d.get("upgrades", {}))   # cấp đã mua
        self.active_upgrades = {}                     # cấp đang áp dụng (sao khi dựng Ngày)
        self.plan = merged_day_plan(tuning, d.get("day_plan"), days)
        self.days = days
        self.day = 0
        self.days_completed = 0
        self._done = False
        self._reason = None
        self.tick = 0
        self.sim_tick = 0
        self.phase_tick = 0
        self.paused = False
        self._initial = []
        self._start_day(self._initial)

    # --- trạng thái ---------------------------------------------------------------
    @property
    def done(self) -> bool:
        return self._done

    @property
    def reason(self):
        return self._reason

    def abort(self, reason):
        self._done = True
        self._reason = reason

    def initial_rows(self) -> list:
        return [self._event(0, *ev) for ev in self._initial]

    def _event(self, tick, phase, name, data, day=None) -> dict:
        return {"type": "event", "tick": tick, "phase": phase, "day": self.day if day is None else day,
                "name": name, "data": data}

    def _day_fields(self) -> dict:
        p = self.plan[self.day]
        return {"day": self.day, "day_plan": {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])},
                "upgrades": dict(sorted(self.upgrades.items())),
                "active_upgrades": dict(sorted(self.active_upgrades.items()))}

    def snapshot(self) -> dict:
        s = Session.snapshot(self)
        s.update(self._day_fields())
        return s

    def end_row(self) -> dict:
        row = Session.end_row(self)
        row["days_completed"] = self.days_completed
        return row

    # --- dựng pha -------------------------------------------------------------------
    def _sync_from_sim(self):
        self.money, self.earned, self.reputation = self.sim.money, self.sim.earned, self.sim.reputation
        if isinstance(self.sim, ShopSim):  # "cấp vừa mua hiển thị ngay" (active_upgrades vẫn đợi Ngày kế)
            self.upgrades = dict(self.sim.purchased)

    def _push_to_sim(self, sim):
        sim.money, sim.earned, sim.reputation = self.money, self.earned, self.reputation
        return sim

    def _start_day(self, out):
        self.day += 1
        self.active_upgrades = dict(self.upgrades)  # chỉ khi dựng Ngày mới mới sao cấp đã mua
        tun = copy.deepcopy(self.tuning)
        g, ups = tun["gather"], tun["shop"]["upgrades"]
        if self.active_upgrades.get("oxygen", 0) > 0:
            g["oxygen_max_s"] = ups["oxygen"][self.active_upgrades["oxygen"] - 1]["oxygen_max_s"]
        if self.active_upgrades.get("hp", 0) > 0:
            g["hp_max"] = ups["hp"][self.active_upgrades["hp"] - 1]["hp_max"]
        self.sim = self._push_to_sim(GatherSim(tun, self.gather_tpl, self.streams, self.ids, day=self.day))
        self.phase_tick = 0
        p = self.plan[self.day]
        out += [("gather", "day_start", {}, self.day),
                ("gather", "day_plan", {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])}, self.day),
                ("gather", "phase_start", {}, self.day)]

    def _start_quan(self, inventory, out):
        sim = QuanSim(self.tuning, self.quan_tpl, self.streams, self.ids, inventory=inventory,
                      menu_filter=list(self.plan[self.day]["dishes"]))
        sim.shift_earned = 0
        self.sim = self._push_to_sim(sim)
        self.phase_tick = 0
        out.append(("quan", "phase_start", {}, self.day))

    def _start_shop(self, stock, out):
        self.sim = ShopSim(self.tuning, self.money, self.earned, self.reputation, self.upgrades, stock)
        self.phase_tick = 0
        out.append(("shop", "phase_start", {}, self.day))

    # --- một bước gameplay ------------------------------------------------------------
    def _gameplay(self, inp) -> list:
        self.phase_tick += 1
        phase = self.sim.phase
        out = [(phase, name, data, self.day) for name, data in self.sim.step(inp)]  # event kết thúc mang pha/Ngày cũ
        self._sync_from_sim()
        if self.sim.done:
            if phase == "gather":
                self._start_quan(self.sim.inventory_items(), out)
            elif phase == "quan":
                self._start_shop(self.sim.stock, out)
            else:  # shop
                self.upgrades = dict(self.sim.purchased)
                self.days_completed += 1
                if self.day < self.days:
                    self._start_day(out)
                else:
                    self._done = True
                    self._reason = "days_complete"
        return out

    def write_inventory_if_done(self, inventory_out):
        """day tự bàn giao kho trong bộ nhớ; cờ file kho chỉ dành cho hai mode độc lập."""
        return None


__all__ = ["DaySession", "merged_day_plan", "score_of"]
