"""Vòng ngày `--mode day` (Test Contract v1.1, TICKET-02 mục 2, 4.3–4.5) + Shop.

DayIntro → gather → EveningIntro → quan → DayResult → Shop → Ngày kế (hoặc kết thúc sau `--days`).
Headless chỉ chạy ba pha gameplay gather / quan / shop; các màn Intro/Result là phần hiển thị.

Gọi lại GatherSim / QuanSim của các lát, KHÔNG nhân đôi luật. Runner `day` giữ trạng thái xuyên Ngày:
money, earned, reputation, upgrades (đã mua), active_upgrades (đang áp dụng), days_completed.
Bàn giao kho gather → quan trong bộ nhớ, đúng object `gather_end.data.inventory`.
"""

import copy
import math

from .contract import recipe_sum
from .items import ItemIds, is_v12, public_list, to_fresh, validate_public_items
from .ids import IdAllocator
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim


class ShopSim:
    """Shop cuối Ngày: mua cấp kế tiếp, tự đóng sau shop.max_ticks bước hoạt động."""

    mode = "day"
    phase = "shop"

    def __init__(self, tuning, day_state, stock):
        self.t = tuning["shop"]
        self.ds = day_state
        # kho dư từ ca, bỏ sau Shop. v1.2: mảng cá thể, KHÔNG hao tươi trong Shop
        if isinstance(stock, list):
            self.stock = [dict(it) for it in stock]
        else:
            self.stock = {k: stock[k] for k in sorted(stock) if stock[k] > 0}
        self.time_left_ticks = int(self.t["max_ticks"])
        self.done = False
        self.reason = None

    money = property(lambda self: self.ds.money)
    earned = property(lambda self: self.ds.earned)
    reputation = property(lambda self: self.ds.reputation)

    def snapshot(self) -> dict:
        if isinstance(self.stock, list):
            return {"stock": public_list(self.stock, by_id=True)}
        return {"stock": dict(self.stock)}

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy:  # xử lý một buy TRƯỚC cạnh shop_done, kể cả ở bước cuối
            events.append(self._buy(inp.buy))
        if inp.pressed("shop_done"):
            self._finish("done", events)
        elif self.time_left_ticks == 0:
            self._finish("time", events)
        return events

    def _buy(self, action):
        levels = self.t["upgrades"].get(action)
        if levels is None:
            return ("buy_failed", {"action": action, "reason": "unknown"})
        level = self.ds.upgrades.get(action, 0)
        if level >= len(levels):
            return ("buy_failed", {"action": action, "reason": "max_level"})
        price = levels[level]["price"]
        if self.ds.money < price:  # đủ đúng giá vẫn mua được
            return ("buy_failed", {"action": action, "reason": "funds"})
        self.ds.money -= price  # earned và điểm giữ nguyên
        self.ds.upgrades[action] = level + 1  # hiển thị ngay, hiệu lực từ Ngày kế
        return ("bought", {"upgrade": action, "level": level + 1, "price": price, "money": self.ds.money})

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("shop_end", {"reason": reason}))


class DaySession:
    """Cùng giao diện với runner.Session (tick, done, step, snapshot, end_row) để dùng chung `run()`."""

    mode = "day"

    def __init__(self, tuning, scenario, seed, days=1):
        self.tuning = tuning
        self.scenario = scenario or {}
        self.seed = seed
        self.days = days
        d = self.scenario.get("day", {})
        q = tuning["quan"]
        self.money = d.get("money", 0)
        self.earned = d.get("earned", 0)
        self.reputation = d.get("reputation", q["reputation_initial"])
        self.upgrades = dict(d.get("upgrades", {}))
        self.active_upgrades = {}
        self.plan = {p["day"]: {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])}
                     for p in tuning["day_plan"]}
        for p in d.get("day_plan", []):  # ghi đè theo số Ngày; ingredients tính lại
            self.plan[p["day"]] = {"dishes": dict(p["dishes"]), "ingredients": recipe_sum(p["dishes"], tuning["menu"])}
        self.day = 0
        self.days_completed = 0
        self.tick = 0
        self.sim_tick = 0
        self.phase_tick = 0
        self.paused = False
        self.phase_changed = False
        self.done = False
        self.reason = None
        self.sim = None
        # v1.2: một bộ cấp id cá thể cho cả lượt; id trong mẫu gather.hold giữ nguyên ở Ngày 1
        self.v12 = is_v12(tuning)
        self.item_ids = ItemIds()
        self._hold_template = None
        if self.v12 and "hold" in self.scenario.get("gather", {}):
            self._hold_template = validate_public_items(self.scenario["gather"]["hold"], "gather.hold")
            for it in self._hold_template:
                self.item_ids.reserve(it["id"])
        self._initial = self._start_day()

    def day_plan(self) -> dict:
        """Kế hoạch của Ngày hiện tại; từ Ngày 6 lặp lại D1–D5 (soak v1.3, TICKET-04 mục 2)."""
        return self.plan[(self.day - 1) % len(self.plan) + 1]

    # --- dựng pha -----------------------------------------------------------------
    def _day_tuning(self):
        """Tuning của Ngày hiện tại: oxy/Máu theo cấp đang áp dụng (quái lọc theo from_day trong GatherSim(day=…)).
        Menu giữ đủ 6 món; lọc theo kế hoạch do QuanSim(menu_filter=…) làm (hợp đồng mục 5.3), để fixture
        có món ngoài kế hoạch báo mã 2 thay vì KeyError."""
        t = copy.deepcopy(self.tuning)
        ups = t["shop"]["upgrades"]
        g = t["gather"]
        if self.active_upgrades.get("oxygen"):
            g["oxygen_max_s"] = ups["oxygen"][self.active_upgrades["oxygen"] - 1]["oxygen_max_s"]
        if self.active_upgrades.get("hp"):
            g["hp_max"] = ups["hp"][self.active_upgrades["hp"] - 1]["hp_max"]
        return t

    def _start_day(self) -> list:
        self.day += 1
        self.active_upgrades = dict(self.upgrades)  # chỉ khi dựng Ngày mới mới chép cấp đã mua
        self._day_t = self._day_tuning()
        self._streams = Streams(f"{self.seed}:day{self.day}")
        self.sim = GatherSim(self._day_t, self._gather_scenario(), self._streams, IdAllocator(), day=self.day,
                             item_ids=self.item_ids)
        self._sync_into(self.sim)
        self.phase_tick = 0
        plan = self.day_plan()
        return [self._event("day_start", {}, "gather"),
                self._event("day_plan", {"dishes": plan["dishes"], "ingredients": plan["ingredients"]}, "gather"),
                self._event("phase_start", {}, "gather")]

    def _gather_scenario(self) -> dict:
        """Mẫu gather mỗi Ngày. v1.2: Ngày 1 giữ id của mẫu hold; Ngày kế cấp id mới theo thứ tự mảng,
        kind/fresh như mẫu (TICKET-03, Scenario)."""
        sc = copy.deepcopy(self.scenario.get("gather", {}))
        if self._hold_template is not None and self.day > 1:
            sc["hold"] = [{"id": self.item_ids.new(), "kind": it["kind"], "fresh": to_fresh(it["fresh_units"])}
                          for it in self._hold_template]
        return sc

    def _sync_into(self, sim):
        sim.money, sim.earned, sim.reputation = self.money, self.earned, self.reputation

    def _sync_from(self, sim):
        self.money, self.earned, self.reputation = sim.money, sim.earned, sim.reputation

    def _next_phase(self) -> list:
        """Gọi ngay khi pha hiện tại kết thúc; dựng pha mới cùng tick (TICKET-02 mục 4.5)."""
        phase = self.sim.phase
        if phase == "gather":
            inventory = self.sim.inventory_items()  # ngất -> rỗng; quán vẫn mở
            quan_sc = copy.deepcopy(self.scenario.get("quan", {}))
            # v1.2: bàn giao mảng cá thể ngay tick đổi pha, không hao thêm; ca quán chạy từ bước sau
            self.sim = QuanSim(self._day_t, quan_sc, self._streams, IdAllocator(), inventory=inventory,
                               item_ids=self.item_ids,
                               menu_filter=sorted(self.day_plan()["dishes"]))  # lọc kế hoạch trước nguyên liệu
            self._sync_into(self.sim)
            self.phase_tick = 0
            return [self._event("phase_start", {}, "quan")]
        if phase == "quan":
            self._sync_from(self.sim)
            self.sim = ShopSim(self.tuning, self, self.sim.stock)
            self.phase_tick = 0
            return [self._event("phase_start", {}, "shop")]
        # shop đóng: Ngày hoàn tất
        self.days_completed += 1
        if self.days_completed >= self.days:
            self.done = True
            self.reason = "days_complete"
            return []
        return self._start_day()

    # --- giao diện runner -----------------------------------------------------------
    def initial_rows(self) -> list:
        return self._initial

    def state(self) -> str:
        return "finished" if self.done else ("paused" if self.paused else "playing")

    def _event(self, name, data, phase=None):
        return {"type": "event", "tick": self.tick, "phase": phase or self.sim.phase, "day": self.day,
                "name": name, "data": data}

    def _score(self):
        return self.earned + self.tuning["score"]["reputation_multiplier"] * math.floor(self.reputation)

    def step(self, inp) -> list:
        self.phase_changed = False
        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                self.tick += 1
                return [self._event("paused", {})]
            self.paused = False
            rows = [dict(self._event("resumed", {}), tick=self.tick + 1)]
        elif self.paused:
            self.tick += 1
            return []
        else:
            rows = []
        events = self.sim.step(inp)
        self.tick += 1
        self.sim_tick += 1
        self.phase_tick += 1
        phase = self.sim.phase
        rows += [self._event(n, d, phase) for n, d in events]  # event kết thúc mang pha cũ
        if self.sim.phase != "shop":
            self._sync_from(self.sim)
        if self.sim.done:
            rows += self._next_phase()
            self.phase_changed = True
        return rows

    def snapshot(self) -> dict:
        sim = self.sim
        s = {"type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick, "mode": "day", "phase": sim.phase,
             "phase_tick": self.phase_tick, "state": self.state(), "time_left_ticks": sim.time_left_ticks,
             "money": self.money, "earned": self.earned, "reputation": self.reputation, "score": self._score(),
             "day": self.day, "day_plan": self.day_plan(), "upgrades": dict(self.upgrades),
             "active_upgrades": dict(self.active_upgrades)}
        s.update(sim.snapshot())
        return s

    def end_row(self) -> dict:
        return {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": "day",
                "state": "finished" if self.done else "playing",
                "reason": self.reason if self.done else "tick_limit",
                "money": self.money, "earned": self.earned, "reputation": self.reputation, "score": self._score(),
                "days_completed": self.days_completed}

    def write_inventory_if_done(self, inventory_out):
        """`day` bàn giao kho trong bộ nhớ; không ghi file (cờ file kho chỉ cho hai mode độc lập)."""
