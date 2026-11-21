"""Mode `day` (contract v1.1) — BẢN TẠM của TV4: vòng nhiều ngày Gather -> Quán -> Shop.

Chưa có TICKET-02 trong repo nên bản này dựng theo `game.contract.json` (day_plan, shop) và
TV1_ACTION_PLAN_PHASE2 mục D4. Tên sự kiện, tên trường snapshot, nút bấm Shop/pause và cách chia
RNG là GIẢ ĐỊNH, đánh dấu `TODO(TV4, TICKET-02)`; ghi ở docs/clarify.md (Q9).

Vòng đời một ngày (D4):
  day_start -> day_plan -> phase_start(gather)
  gather_end  -> phase_start(quan) CÙNG tick, Quán chạy từ bước sau
  quan_end    -> phase_start(shop) CÙNG tick, Shop chạy từ bước sau
  Shop đóng   -> day_end; còn ngày thì day_start ngày sau (Gather chạy từ bước sau)
Pause: `tick` ngoài vẫn tăng (runner), `sim_tick` / `phase_tick` / mọi bộ đếm giờ đứng yên.
Nâng cấp mua ở Shop chỉ có hiệu lực từ NGÀY KẾ TIẾP (`active_upgrades` chốt lúc day_start).
Kho còn dư sau Quán bị bỏ sau Shop. Ngất ở Gather -> kho rỗng, Quán tối vẫn mở.
"""

import copy

from ..errors import BadInput
from .gather import GatherSim
from .quan import QuanSim

# TODO(TV4, TICKET-02): tên nút thật cho pause và mua nâng cấp. `interact` ở Shop = rời Shop.
BUTTONS_DAY = ("interact", "catch", "pause", "buy_oxygen", "buy_hp")
UPGRADE_KEYS = {"oxygen": "oxygen_max_s", "hp": "hp_max"}


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        plans = tuning["day_plan"]
        if not isinstance(days, int) or isinstance(days, bool) or not (1 <= days <= len(plans)):
            raise BadInput(f"--days phải trong [1, {len(plans)}]")
        if scenario:
            # TODO(TV4, TICKET-02): scenario cho mode day (bắt đầu giữa ngày, có sẵn tiền/nâng cấp...).
            raise BadInput("mode day chưa hỗ trợ --scenario")
        self.tuning = tuning
        self.plans = {p["day"]: p for p in plans}
        self.days = days
        # TODO(TV4, TICKET-02): dùng chung Streams/IdAllocator cho mọi pha hay tách theo ngày/pha.
        self.rng = streams
        self.ids = ids
        self.shop_cfg = tuning["shop"]
        self.wallet = 0          # tiền mang qua các ngày (Quán luôn mở ca với money = 0)
        self.total_earned = 0
        self.rep = tuning["quan"]["reputation_initial"]
        self.upgrades = {k: 0 for k in UPGRADE_KEYS}
        self.active_upgrades = dict(self.upgrades)
        self.sim_tick = 0
        self.phase_tick = 0
        self.paused = False
        self.done = False
        self.reason = None
        self.day = 0
        self.phase = None
        self.sub = None
        self.shop_ticks_left = 0
        self._pending = []
        self._start_day(1, self._pending)  # sự kiện ngày 1 phát ở bước đầu tiên

    # --- chuyển pha -------------------------------------------------------------
    def _gather_tuning(self):
        t = copy.deepcopy(self.tuning)
        for kind, key in UPGRADE_KEYS.items():
            level = self.active_upgrades[kind]
            if level:
                t["gather"][key] = self.shop_cfg["upgrades"][kind][level - 1][key]
        return t

    def _start_day(self, day, events):
        self.day = day
        self.active_upgrades = dict(self.upgrades)
        plan = self.plans[day]
        events.append(("day_start", {"day": day, "active_upgrades": dict(self.active_upgrades)}))
        events.append(("day_plan", {"day": day, "dishes": dict(plan["dishes"]),
                                    "ingredients": dict(plan["ingredients"])}))
        self.sub = GatherSim(self._gather_tuning(), {"day": day}, self.rng, self.ids)
        self._open_phase("gather", events)

    def _open_phase(self, name, events):
        self.phase = name
        self.phase_tick = 0
        events.append(("phase_start", {"day": self.day, "phase": name}))

    def _open_quan(self, events):
        items = self.sub.inventory_items()  # ngất -> rỗng; Quán vẫn mở
        plan = self.plans[self.day]
        self.sub = QuanSim(self.tuning, {"reputation": self.rep}, self.rng, self.ids,
                           inventory=items, day_dishes=list(plan["dishes"]))
        self._open_phase("quan", events)

    def _open_shop(self, events):
        q = self.sub
        self.wallet += q.money
        self.total_earned += q.earned
        self.rep = q.reputation
        self.sub = None  # kho còn dư của Quán bị bỏ
        self.shop_ticks_left = int(self.shop_cfg["max_ticks"])
        self._open_phase("shop", events)

    def _close_shop(self, reason, events):
        events.append(("shop_end", {"day": self.day, "reason": reason, "upgrades": dict(self.upgrades)}))
        events.append(("day_end", {"day": self.day, "money": self.wallet, "earned": self.total_earned,
                                   "reputation": self.rep}))
        if self.day < self.days:
            self._start_day(self.day + 1, events)
        else:
            self.phase = "done"
            self.done = True
            self.reason = "days_complete"  # TODO(TV4, TICKET-02): tên reason khi chạy hết số ngày

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events, self._pending = self._pending, []
        if inp.pressed("pause"):
            self.paused = not self.paused
            events.append(("resumed" if not self.paused else "paused", {"day": self.day, "phase": self.phase}))
        if self.paused:
            return events
        self.sim_tick += 1
        self.phase_tick += 1
        if self.phase in ("gather", "quan"):
            sub_events = self.sub.step(inp)
            events.extend(sub_events)
            if self.sub.done:
                if self.phase == "gather":
                    self._open_quan(events)
                else:
                    self._open_shop(events)
        elif self.phase == "shop":
            self._shop_step(inp, events)
        return events

    def _shop_step(self, inp, events):
        for kind, button in (("oxygen", "buy_oxygen"), ("hp", "buy_hp")):
            if inp.pressed(button):
                self._buy(kind, events)
        self.shop_ticks_left = max(0, self.shop_ticks_left - 1)
        if inp.pressed("interact"):
            self._close_shop("left", events)
        elif self.shop_ticks_left == 0:
            self._close_shop("time", events)

    def _buy(self, kind, events):
        levels = self.shop_cfg["upgrades"][kind]
        level = self.upgrades[kind]
        if level >= len(levels):
            events.append(("buy_failed", {"upgrade": kind, "reason": "max_level"}))
            return
        price = levels[level]["price"]
        if self.wallet < price:
            events.append(("buy_failed", {"upgrade": kind, "reason": "money"}))
            return
        self.wallet -= price
        self.upgrades[kind] = level + 1
        events.append(("upgrade_bought", {"upgrade": kind, "level": level + 1, "price": price,
                                          "money": self.wallet}))

    # --- giao diện cho runner ---------------------------------------------------
    @property
    def money(self):
        return self.wallet + (self.sub.money if self.phase == "quan" else 0)

    @property
    def earned(self):
        return self.total_earned + (self.sub.earned if self.phase == "quan" else 0)

    @property
    def reputation(self):
        return self.sub.reputation if self.phase == "quan" else self.rep

    @property
    def time_left_ticks(self):
        if self.phase in ("gather", "quan"):
            return self.sub.time_left_ticks
        return self.shop_ticks_left if self.phase == "shop" else 0

    def snapshot(self) -> dict:
        # TODO(TV4, TICKET-02): tên và vị trí các trường day/shop/pause trong snapshot.
        s = {"day": self.day, "days": self.days, "day_phase": self.phase, "paused": self.paused,
             "upgrades": dict(self.upgrades), "active_upgrades": dict(self.active_upgrades)}
        if self.phase in ("gather", "quan"):
            s.update(self.sub.snapshot())
        elif self.phase == "shop":
            s["shop"] = {"ticks_left": self.shop_ticks_left,
                         "offers": {k: (lv[self.upgrades[k]] if self.upgrades[k] < len(lv) else None)
                                    for k, lv in self.shop_cfg["upgrades"].items()}}
        return s
