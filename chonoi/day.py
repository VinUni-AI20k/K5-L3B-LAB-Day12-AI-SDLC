"""Vòng ngày `--mode day` (Test Contract v1.1, Ticket-02 mục 2, 4.4, 4.5). C viết. KHUNG: giao diện cố định.

DaySession phải có CÙNG giao diện với runner.Session để headless (`runner.run`) và cửa sổ chơi (`live.py`) dùng
chung:

    sess = DaySession(tuning, scenario, seed, days, contract=None)
    sess.tick, sess.done
    sess.snapshot() -> dict        # thêm day, day_plan, upgrades, active_upgrades; phase gather|quan|shop
    sess.step(inp) -> list[dict]   # dòng event, vỏ có thêm "day"
    sess.end_row() -> dict         # thêm days_completed; đủ Ngày thì reason "days_complete"
    sess.write_inventory_if_done(path)  # day không dùng file kho: không làm gì

Gợi ý dựng (xem docs/contracts/README.md, mục v1.1):
- `scenario` là {"gather": ..., "quan": ..., "day": ...} (scenario.load_scenario với mode "day").
- Một Streams(seed) và một IdAllocator cho cả lượt; một runner.PauseGate cho pause.
- Ngày mới: active_upgrades = copy(upgrades); phát day_start -> day_plan -> phase_start(gather) ở tick đó;
  GatherSim(tuning, scenario["gather"], streams, ids, day=day, active_upgrades=active_upgrades).
- gather_end (kể cả fainted): dựng QuanSim(tuning, scenario["quan"], streams, ids, inventory=kho bàn giao,
  plan_dishes=list(day_plan["dishes"]), carry={money, earned, reputation}); phát phase_start(quan) cùng tick.
- quan_end: dựng shop.ShopSim, phát phase_start(shop) cùng tick.
- shop_end: days_completed += 1; còn Ngày thì dựng Ngày kế ngay tick đó, hết thì done, reason "days_complete".
- Snapshot đổi pha ghi pha mới với phase_tick 0. Event kết thúc pha mang pha cũ.
- Một Ngày không pause tối đa 22.200 tick phải chạy headless dưới 20 s.
"""

import copy

from .ids import IdAllocator
from .rng import Streams
from .runner import PauseGate, score_of
from .scenario import effective_day_plan
from .shop import ShopSim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


class DaySession:
    mode = "day"

    def __init__(self, tuning, scenario, seed, days, contract=None):
        scenario = scenario or {}
        self.tuning = tuning
        self.days = days
        self._gather_tpl = scenario.get("gather", {})
        self._quan_tpl = scenario.get("quan", {})
        d = scenario.get("day", {})
        self.money = d.get("money", 0)
        self.earned = d.get("earned", 0)
        self.reputation = d.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(d.get("upgrades", {}))
        self.active_upgrades = {}
        self.plans = effective_day_plan(tuning, d)
        self.streams, self.ids = Streams(seed), IdAllocator()  # một lượt, một bộ RNG và id
        self.gate = PauseGate()
        self.tick = 0
        self.sim_tick = 0
        self.day = 0
        self.days_completed = 0
        self.done = False
        self.reason = None
        self.sim = None
        # Ngày 1 dựng ở tick 0: event mở Ngày được runner ghi trước snapshot tick 0 (start_rows).
        self._start = self._rows(self._opened(self._new_day()))

    # ---- vòng pha ---------------------------------------------------------------

    def _plan(self):
        return self.plans[self.day - 1]

    def _new_day(self):
        """day_start -> day_plan -> phase_start(gather), cùng tick. Cấp vừa mua có hiệu lực từ Ngày này."""
        self.day += 1
        self.active_upgrades = dict(self.upgrades)
        self.sim = GatherSim(self.tuning, copy.deepcopy(self._gather_tpl), self.streams, self.ids,
                             day=self.day, active_upgrades=self.active_upgrades)
        p = self._plan()
        return [(self.day, "day_start", {}),
                (self.day, "day_plan", {"dishes": p["dishes"], "ingredients": p["ingredients"]}),
                (self.day, "phase_start", {})]

    def _carry(self):
        return {"money": self.money, "earned": self.earned, "reputation": self.reputation}

    def _sync_from(self, sim):
        self.money, self.earned, self.reputation = sim.money, sim.earned, sim.reputation

    def _advance(self):
        """Pha hiện tại vừa kết thúc ở bước này: dựng pha kế ngay cùng tick, trả event mở pha (day, name, data)."""
        sim = self.sim
        if sim.phase == "gather":
            # kể cả fainted: kho bàn giao rỗng; QuanSim kiểm mâu thuẫn kho/khách lúc mở quán (BadInput -> mã 2)
            self.sim = QuanSim(self.tuning, copy.deepcopy(self._quan_tpl), self.streams, self.ids,
                               inventory=sim.inventory_items(), plan_dishes=list(self._plan()["dishes"]),
                               carry=self._carry())
            return [(self.day, "phase_start", {})]
        if sim.phase == "quan":
            self._sync_from(sim)
            self.sim = ShopSim(self.tuning, sim.stock, self._carry(), self.upgrades)
            return [(self.day, "phase_start", {})]
        # Shop đóng: Ngày hoàn tất; kho dư bị bỏ, giỏ làm mới ở Ngày kế.
        self._sync_from(sim)
        self.upgrades = dict(sim.upgrades)
        self.days_completed += 1
        if self.days_completed >= self.days:
            self.done = True
            self.reason = "days_complete"
            return []
        return self._new_day()

    # ---- giao diện Session ------------------------------------------------------

    def start_rows(self) -> list:
        """Event của tick 0 (mở Ngày 1). runner ghi một lần, trước snapshot tick 0."""
        rows, self._start = self._start, []
        return rows

    def _opened(self, events):
        """Event mở Ngày/pha mang pha MỚI (pha của sim vừa dựng)."""
        return [(day, self.sim.phase, name, data) for day, name, data in events]

    def _rows(self, events):
        return [{"type": "event", "tick": self.tick, "phase": phase, "day": day, "name": name, "data": data}
                for day, phase, name, data in events]

    def step(self, inp) -> list:
        self.tick += 1
        run, gate_events = self.gate.check(inp)
        events = [(self.day, self.sim.phase, n, d) for n, d in gate_events]
        if run:
            self.sim_tick += 1
            # event kết thúc pha (gather_end, quan_end, shop_end) mang pha cũ
            events += [(self.day, self.sim.phase, n, d) for n, d in self.sim.step(inp)]
            if self.sim.phase != "gather":
                self._sync_from(self.sim)
            if self.sim.done:
                events += self._opened(self._advance())
        return self._rows(events)

    def _state(self):
        if self.done:
            return "finished"
        return "paused" if self.gate.paused else "playing"

    def snapshot(self) -> dict:
        sim = self.sim
        p = self._plan()
        s = {
            "type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick, "mode": "day",
            "phase": sim.phase, "phase_tick": sim.phase_tick, "state": self._state(),
            "time_left_ticks": sim.time_left_ticks, "money": self.money, "earned": self.earned,
            "reputation": self.reputation, "score": score_of(self.tuning, self.earned, self.reputation),
            "day": self.day, "day_plan": {"dishes": p["dishes"], "ingredients": p["ingredients"]},
            "upgrades": dict(sim.upgrades if sim.phase == "shop" else self.upgrades),
            "active_upgrades": dict(self.active_upgrades),
        }
        s.update(sim.snapshot())
        return s

    def end_row(self) -> dict:
        return {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": "day",
                "state": self._state(), "reason": self.reason if self.done else "tick_limit",
                "money": self.money, "earned": self.earned, "reputation": self.reputation,
                "score": score_of(self.tuning, self.earned, self.reputation),
                "days_completed": self.days_completed}

    def write_inventory_if_done(self, inventory_out):
        """day tự bàn giao kho trong bộ nhớ, không dùng file kho."""
