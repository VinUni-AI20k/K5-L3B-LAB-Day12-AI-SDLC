"""Lớp màn hình vòng ngày cho CỬA SỔ CHƠI (TV5 · UI). Chỉ dùng trong `chonoi.live --mode day`.

Lõi là `runner.Session("day")` — CÙNG DaySim của TV4 mà headless dùng. Lớp này chỉ:
  1. Giữ các màn UI không có trong headless: day_intro (tự chuyển sau 240 tick thật hoặc khi bấm phím),
     evening_intro (sau gather_end) và day_result (sau quan_end). Khi giữ màn, KHÔNG bước Session,
     nên mọi timer gameplay đứng yên; headless không bị ảnh hưởng.
  2. Gộp số liệu cho UI từ event (served/paid/customer_left/gather_end) → DayResult, Summary.
  3. Mở rộng "Chợ Chú Sáu" (vendor) bản live: lệnh `buy` dạng `sell:<kind>` / `buy:<kind>` bị chặn ở đây,
     không tới DaySim; hàng mua được nạp vào kho quán Ngày kế ngay khi quán vừa dựng (trước bước gameplay đầu).

Pause do Session xử lý (cạnh `pause`), giống headless.
"""

import math

from .inputs import InputState
from .runner import Session

INTRO_AUTO_TICKS = 4 * 60
HOLD_SCREENS = ("day_intro", "evening_intro", "day_result")

# Mở rộng vendor (TICKET-02 mục 3). Đọc tuning.shop.vendor nếu manifest có, không thì bảng chuẩn.
DEFAULT_VENDOR = {
    "buy_multiplier": 1.5,
    "sell_prices": {"ca_loc": 20, "ca_linh": 8, "ca_keo": 10, "bong_dien_dien": 5, "bong_sung": 5, "keo_neo": 5},
}


class LiveDaySession:
    """Giao diện giống `runner.Session` (tick, done, sim, snapshot, step, initial_events) cho `chonoi.live`."""

    mode = "day"

    def __init__(self, tuning, scenario, seed, days=5):
        self.tuning = tuning
        self.core = Session("day", tuning, scenario, seed, days=days)
        self.days = days
        self.vendor_cfg = tuning.get("shop", {}).get("vendor") or DEFAULT_VENDOR
        self.screen = "day_intro"
        self.screen_ticks = 0
        self.vendor_pending = {}     # mua hôm nay → kho quán tối mai
        self.vendor_delivery = {}    # đã giao cho quán hôm nay
        self.dish_sold = {}
        self.history = []
        self.day_result = None
        self._new_day_stats()

    # --- giao diện Session --------------------------------------------------------------
    @property
    def sim(self):
        return self.core.sim

    @property
    def tick(self):
        return self.core.tick

    @property
    def paused(self):
        return self.core.paused

    @property
    def done(self):
        return self.core.done

    def initial_events(self):
        return self.core.initial_events()

    def _new_day_stats(self):
        self.stats = {"served": 0, "left": 0, "income": 0, "tips": 0,
                      "rep_start": self.core.sim.reputation, "gather_reason": None, "handover": {}}
        self.quan_money_start = self.core.sim.money

    def _row(self, name, data):
        return {"type": "event", "tick": self.core.tick, "phase": self.core.sim.phase, "day": self.core.sim.day,
                "name": name, "data": data}

    def step(self, inp):
        if self.done:
            return []
        if self.screen in HOLD_SCREENS:
            # màn chờ của UI: không bước sim (timer đứng yên), pause bỏ qua
            self.screen_ticks += 1
            go = inp.pressed("continue") or inp.pressed("interact")
            if go or (self.screen == "day_intro" and self.screen_ticks >= INTRO_AUTO_TICKS):
                self.screen = self.core.sim.phase
                self.screen_ticks = 0
            return []
        rows = []
        if inp.buy and inp.buy.startswith(("sell:", "buy:")):
            if self.core.sim.phase == "shop" and not self.core.paused:
                rows.append(self._row(*self._trade(inp.buy)))
            inp = InputState(inp.move, inp.held, inp._edges, None)
        phase, day = self.core.sim.phase, self.core.sim.day
        core_rows = self.core.step(inp)
        for r in core_rows:
            self._collect(r)
        rows.extend(core_rows)
        sim = self.core.sim
        if sim.phase != phase or sim.day != day or self.done:
            if phase == "quan":
                self.day_result = self._result_view()
            if self.done:
                self._close_day()
                self.screen = "summary"
            elif sim.day != day:             # Shop đóng, sang Ngày mới
                self._close_day()
                self.screen = "day_intro"
            elif sim.phase == "quan":        # vừa dựng quán: giao hàng Chợ trước bước gameplay đầu
                self._deliver_vendor()
                self.quan_money_start = sim.money
                self.screen = "evening_intro"
            elif sim.phase == "shop":
                self.screen = "day_result"
            self.screen_ticks = 0
        return rows

    # --- số liệu ------------------------------------------------------------------------------
    def _collect(self, r):
        name, d = r["name"], r["data"]
        if name == "gather_end":
            self.stats["gather_reason"] = d.get("reason")
            self.stats["handover"] = dict(d.get("inventory", {}).get("items", {}))
        elif name == "served":
            self.stats["served"] += 1
            self.dish_sold[d["dish_id"]] = self.dish_sold.get(d["dish_id"], 0) + 1
        elif name == "paid":
            self.stats["income"] += d["amount"]
            self.stats["tips"] += d["tip"]
        elif name == "customer_left" and d.get("reason") == "patience":
            self.stats["left"] += 1

    def _result_view(self):
        st = self.stats
        return {"served": st["served"], "left": st["left"], "income": st["income"], "tips": st["tips"],
                "reputation_delta": round(self.core.sim.reputation - st["rep_start"], 2),
                "gather_reason": st["gather_reason"]}

    def _close_day(self):
        self.history.append({"day": len(self.history) + 1, **(self.day_result or self._result_view())})
        self.day_result = None
        self.vendor_delivery, self.vendor_pending = self.vendor_pending, {}
        self._new_day_stats()

    # --- Chợ Chú Sáu --------------------------------------------------------------------------
    def vendor_buy_price(self, kind):
        return math.floor(self.vendor_cfg["sell_prices"][kind] * self.vendor_cfg["buy_multiplier"])

    def _trade(self, action):
        """Mỗi lệnh một đơn vị. sell: bán kho dư (cộng money + earned). buy: hàng về kho quán Ngày kế."""
        sim = self.core.sim
        side, kind = action.split(":", 1)
        prices = self.vendor_cfg["sell_prices"]
        if kind not in prices:
            return "buy_failed", {"action": action, "reason": "unknown"}
        if side == "sell":
            stock = sim.shift.stock  # pha shop: kho dư của ca tối
            if stock.get(kind, 0) <= 0:
                return "buy_failed", {"action": action, "reason": "out_of_stock"}
            price = prices[kind]
            stock[kind] -= 1
            sim.money += price
            sim.earned += price
        else:
            price = self.vendor_buy_price(kind)
            if sim.money < price:
                return "buy_failed", {"action": action, "reason": "funds"}
            sim.money -= price
            self.vendor_pending[kind] = self.vendor_pending.get(kind, 0) + 1
        return "vendor_trade", {"action": side, "kind": kind, "price": price, "money": sim.money}

    def _deliver_vendor(self):
        stock = self.core.sim.shift.stock
        for k, n in self.vendor_delivery.items():
            stock[k] = stock.get(k, 0) + n

    # --- snapshot cho UI ----------------------------------------------------------------------
    def _cookable(self, stock):
        menu = self.tuning["menu"]
        return {d: min((stock.get(k, 0) // q for k, q in menu[d]["recipe"].items()), default=0)
                for d in self.core.sim.plans[self.core.sim.day]["dishes"]}

    def score(self):
        mult = self.tuning["score"]["reputation_multiplier"]
        return self.core.sim.earned + mult * math.floor(self.core.sim.reputation)

    def snapshot(self):
        s = self.core.snapshot()
        sim = self.core.sim
        s.update(screen=self.screen, days=self.days, days_completed=sim.days_completed,
                 menu_info={d: {"price": m["price"], "cook_s": m["cook_s"], "recipe": m["recipe"]}
                            for d, m in self.tuning["menu"].items()})
        if self.screen == "day_intro":
            s["intro_ticks_left"] = max(0, INTRO_AUTO_TICKS - self.screen_ticks)
        if sim.phase == "quan" and not self.done:
            s["shift_money"] = sim.money - self.quan_money_start
        if self.screen == "evening_intro":
            s["handover"] = dict(self.stats["handover"])
            s["vendor_delivery"] = dict(self.vendor_delivery)
            s["cookable"] = self._cookable(sim.shift.stock)
            s["gather_reason"] = self.stats["gather_reason"]
        if sim.phase == "shop" and not self.done:
            s["result"] = self.day_result or self._result_view()
            s["shop"] = {k: {"level": sim.upgrades.get(k, 0), "max_level": len(v),
                             "next": v[sim.upgrades.get(k, 0)] if sim.upgrades.get(k, 0) < len(v) else None}
                         for k, v in sim.shop["upgrades"].items()}
            s["vendor"] = {"sell_prices": dict(self.vendor_cfg["sell_prices"]),
                           "buy_prices": {k: self.vendor_buy_price(k) for k in self.vendor_cfg["sell_prices"]},
                           "pending": dict(self.vendor_pending)}
        if self.screen == "summary":
            best = max(sorted(self.dish_sold), key=lambda d: self.dish_sold[d], default=None)
            s["summary"] = {"money": sim.money, "earned": sim.earned, "score": self.score(),
                            "reputation": sim.reputation, "best_dish": best,
                            "best_count": self.dish_sold.get(best, 0), "history": self.history}
        return s
