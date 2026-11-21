"""Vòng ngày (DaySim) — Phase 2: D1..D5, đổi pha Gather -> Quán -> Shop.

- Mỗi ngày:
    1. Đầu ngày: phát day_start, day_plan (theo cấu hình D1..D5), phase_start (gather).
    2. Pha Gather: chạy GatherSim với nâng cấp active_upgrades đã kích hoạt.
    3. Hết Gather: bàn giao kho nguyên liệu trong bộ nhớ sang QuanSim.
    4. Pha Quán: chạy QuanSim với kho từ Gather và thực đơn lọc theo day_plan.
    5. Hết Quán: phát phase_start (shop), chuyển sang pha Shop.
    6. Pha Shop: đếm 600 tick, nhận lệnh buy và nút shop_done; phát bought / buy_failed / shop_end.
    7. Hết Shop: kích hoạt nâng cấp cho Ngày kế tiếp (active_upgrades), tăng day.
       Nếu đã hoàn thành đủ số ngày yêu cầu (days_completed >= max_days), kết thúc vòng chơi.
- Tạm dừng / Tiếp tục: nhận nút pause (cạnh lên), tạm dừng đồng hồ và phát paused / resumed.
"""

from ..inventory import merge_items
from .gather import GatherSim
from .quan import QuanSim


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, days=1):
        self.tuning = tuning
        self.streams = streams
        self.ids = ids
        self.scenario = scenario if isinstance(scenario, dict) else {}

        day_block = self.scenario.get("day", {})
        if not isinstance(day_block, dict):
            day_block = {}

        self.max_days = day_block.get("days") or self.scenario.get("days") or days or 1
        if self.max_days < 1:
            self.max_days = 1

        self.day = day_block.get("day", 1)
        self.days_completed = 0
        self.money = day_block.get("money", 0)
        self.earned = 0
        self.reputation = float(self.scenario.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = dict(day_block.get("upgrades", {}))
        self.active_upgrades = dict(day_block.get("active_upgrades", {}))

        self.state = "paused" if day_block.get("state") == "paused" else "running"
        self.done = False
        self.reason = None

        self.phase = "gather"
        self.phase_tick = 0
        self.stock = dict(inventory) if inventory is not None else dict(self.scenario.get("stock", {}))
        self.shop_max_ticks = int(self.tuning.get("shop", {}).get("max_ticks", 600))
        self.shop_time_left_ticks = self.shop_max_ticks

        self.pending_events = []
        self._start_day()

    @property
    def inventory(self) -> dict:
        return self.inventory_items()

    @property
    def quan(self):
        return self.sub_sim if self.phase == "quan" else None

    @property
    def gather(self):
        return self.sub_sim if self.phase == "gather" else None

    def _get_current_plan(self) -> dict:
        plans = self.tuning.get("day_plan", {})
        plan = None
        if isinstance(plans, list):
            for p in plans:
                if p.get("day") == self.day:
                    plan = p
                    break
            if not plan and plans:
                plan = plans[0]
        elif isinstance(plans, dict):
            plan = plans.get(str(self.day)) or plans.get(self.day)
            if not plan and plans:
                plan = plans.get("1") or plans.get(1)
        return dict(plan or {})

    def _start_day(self):
        plan = self._get_current_plan()
        day_plan_data = {
            "dishes": plan.get("dishes", {}),
            "ingredients": plan.get("ingredients", {}),
        }
        self.pending_events.append(("day_start", {}, "gather", self.day))
        self.pending_events.append(("day_plan", day_plan_data, "gather", self.day))
        self.pending_events.append(("phase_start", {}, "gather", self.day))
        self._init_gather()

    def _init_gather(self):
        gather_tuning = dict(self.tuning)
        g = dict(self.tuning["gather"])

        oxy_lvl = self.active_upgrades.get("oxygen")
        if oxy_lvl:
            up_list = self.tuning.get("shop", {}).get("upgrades", {}).get("oxygen", [])
            up_info = next((u for u in up_list if u["level"] == oxy_lvl), None)
            if up_info:
                g["oxygen_max_s"] = up_info["oxygen_max_s"]

        hp_lvl = self.active_upgrades.get("hp")
        if hp_lvl:
            up_list = self.tuning.get("shop", {}).get("upgrades", {}).get("hp", [])
            up_info = next((u for u in up_list if u["level"] == hp_lvl), None)
            if up_info:
                g["hp_max"] = up_info["hp_max"]

        gather_tuning["gather"] = g
        gather_sc = self.scenario.get("gather", {}) if isinstance(self.scenario, dict) else {}
        self.sub_sim = GatherSim(gather_tuning, gather_sc, self.streams, self.ids, day=self.day)
        self.phase = "gather"
        self.phase_tick = 0

    def _init_quan(self):
        plan = self._get_current_plan()
        menu_filter = set(plan.get("dishes", {}).keys()) if plan.get("dishes") else None

        quan_sc = dict(self.scenario.get("quan", {}) if isinstance(self.scenario, dict) else {})
        # Bàn giao kho trong bộ nhớ từ gather
        quan_sc["stock"] = dict(self.stock)

        self.sub_sim = QuanSim(
            self.tuning, quan_sc, self.streams, self.ids,
            menu_filter=menu_filter
        )
        self.phase = "quan"
        self.phase_tick = 0

    def _init_shop(self):
        self.sub_sim = None
        self.phase = "shop"
        self.phase_tick = 0
        self.shop_max_ticks = int(self.tuning.get("shop", {}).get("max_ticks", 600))
        self.shop_time_left_ticks = self.shop_max_ticks

    @property
    def time_left_ticks(self) -> int:
        if self.sub_sim is not None:
            return self.sub_sim.time_left_ticks
        return self.shop_time_left_ticks

    def inventory_items(self) -> dict:
        if self.phase == "gather" and self.sub_sim is not None:
            return merge_items(self.stock, self.sub_sim.inventory_items())
        elif self.phase == "quan" and self.sub_sim is not None:
            return dict(self.sub_sim.stock)
        return dict(self.stock)

    def snapshot(self) -> dict:
        plan = self._get_current_plan()
        snap = {
            "day": self.day,
            "day_plan": {
                "dishes": plan.get("dishes", {}),
                "ingredients": plan.get("ingredients", {}),
            },
            "upgrades": dict(self.upgrades),
            "active_upgrades": dict(self.active_upgrades),
            "menu": self.tuning.get("menu", {}),
            "state": "paused" if self.state == "paused" else ("finished" if self.done else "running"),
        }
        if self.phase == "gather" and self.sub_sim:
            sub_snap = self.sub_sim.snapshot()
            snap.update(sub_snap)
        elif self.phase == "quan" and self.sub_sim:
            sub_snap = self.sub_sim.snapshot()
            snap.update(sub_snap)
        elif self.phase == "shop":
            snap.update({
                "stock": dict(self.stock),
                "time_left_ticks": self.shop_time_left_ticks,
                "meta": {
                    "max_ticks": self.shop_max_ticks,
                    "upgrades": self.tuning.get("shop", {}).get("upgrades", {})
                }
            })
        return snap

    def step(self, inp) -> list:
        if self.done:
            return []

        evs = []
        if self.pending_events:
            evs.extend(self.pending_events)
            self.pending_events = []

        # Xử lý pause / resume
        if inp.pressed("pause"):
            if self.state == "running":
                self.state = "paused"
                evs.append(("paused", {}, self.phase, self.day))
            else:
                self.state = "running"
                evs.append(("resumed", {}, self.phase, self.day))

        if self.state == "paused":
            return evs

        if self.phase == "gather":
            sub_evs = self.sub_sim.step(inp)
            self.phase_tick += 1
            for e in sub_evs:
                evs.append((e[0], e[1], "gather", self.day))

            if self.sub_sim.done or self.sub_sim.time_left_ticks <= 0:
                if self.sub_sim.reason == "fainted":
                    self.stock = {}
                else:
                    self.stock = merge_items(self.stock, self.sub_sim.inventory_items())
                self._init_quan()
                evs.append(("phase_start", {}, "quan", self.day))

        elif self.phase == "quan":
            sub_evs = self.sub_sim.step(inp)
            self.phase_tick += 1
            for e in sub_evs:
                evs.append((e[0], e[1], "quan", self.day))

            if self.sub_sim.done or self.sub_sim.time_left_ticks <= 0:
                self.money += self.sub_sim.earned
                self.earned += self.sub_sim.earned
                self.reputation = self.sub_sim.reputation
                self.stock = dict(self.sub_sim.stock)
                self._init_shop()
                evs.append(("phase_start", {}, "shop", self.day))

        elif self.phase == "shop":
            self.phase_tick += 1
            self.shop_time_left_ticks -= 1

            buy_item = getattr(inp, "buy", None)
            if buy_item:
                shop_upgrades = self.tuning.get("shop", {}).get("upgrades", {})
                if buy_item not in shop_upgrades:
                    evs.append(("buy_failed", {"action": buy_item, "reason": "unknown"}, "shop", self.day))
                else:
                    upgrades_cat = shop_upgrades[buy_item]
                    cur_lvl = self.upgrades.get(buy_item, 0)
                    next_item = next((u for u in upgrades_cat if u["level"] == cur_lvl + 1), None)
                    if next_item:
                        if self.money >= next_item["price"]:
                            self.money -= next_item["price"]
                            self.upgrades[buy_item] = cur_lvl + 1
                            evs.append(("bought", {
                                "upgrade": buy_item,
                                "level": cur_lvl + 1,
                                "price": next_item["price"],
                                "money": self.money
                            }, "shop", self.day))
                        else:
                            evs.append(("buy_failed", {"action": buy_item, "reason": "funds"}, "shop", self.day))
                    else:
                        evs.append(("buy_failed", {"action": buy_item, "reason": "max_level"}, "shop", self.day))

            if inp.pressed("shop_done") or self.shop_time_left_ticks <= 0:
                reason = "done" if inp.pressed("shop_done") else "time"
                evs.append(("shop_end", {"reason": reason}, "shop", self.day))
                self.days_completed += 1
                if self.days_completed >= self.max_days:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    self.day += 1
                    # Nâng cấp mua ở shop có hiệu lực từ Ngày tiếp theo
                    self.active_upgrades = dict(self.upgrades)
                    self._start_day()
                    evs.extend(self.pending_events)
                    self.pending_events = []

        return evs
