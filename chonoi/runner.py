"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim
from .sim.day import ShopSim, check_evening_fixture, gather_tuning, validate_day


def _common(sim, mode, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.streams, self.ids = Streams(seed), IdAllocator()
        self.scenario = scenario
        self.tick = 0
        self.sim_tick = 0
        self.phase_tick = 0
        self.paused = False
        self.initial_events = []
        if mode == "day":
            state = scenario.get("day", {})
            self.plans = validate_day(state, tuning)
            self.days = days
            self.days_completed = 0
            self.upgrades = dict(state.get("upgrades", {}))
            self.initial_events = self._start_day(state.get("money", 0), state.get("earned", 0),
                                                  state.get("reputation", tuning["quan"]["reputation_initial"]))
        elif mode == "gather":
            self.sim = GatherSim(tuning, scenario, self.streams, self.ids)
        else:
            self.sim = QuanSim(tuning, scenario, self.streams, self.ids, inventory)

    def _events(self, pairs):
        common = {"type": "event", "tick": self.tick, "phase": self.sim.phase}
        if self.mode == "day":
            common["day"] = self.day
        return [{**common, "name": name, "data": data} for name, data in pairs]

    def _start_day(self, money, earned, reputation):
        self.day = self.days_completed + 1
        self.active_upgrades = self.upgrades.copy()
        self.plan = self.plans[self.day]
        tuning = gather_tuning(self.tuning, self.active_upgrades)
        self.sim = GatherSim(tuning, self.scenario.get("gather", {}), self.streams, self.ids, self.day)
        self.sim.money, self.sim.earned, self.sim.reputation = money, earned, reputation
        self.phase_tick = 0
        data = {key: self.plan[key] for key in ("dishes", "ingredients")}
        return self._events([("day_start", {}), ("day_plan", data), ("phase_start", {})])

    def _change_phase(self):
        previous = self.sim
        if previous.phase == "gather":
            stock = previous.inventory_items()
            menu = {key: self.tuning["menu"][key] for key in self.plan["dishes"]}
            fixture = self.scenario.get("quan", {})
            check_evening_fixture(fixture, stock, menu)
            self.sim = QuanSim({**self.tuning, "menu": menu}, fixture, self.streams, self.ids, stock)
            self.sim.money, self.sim.earned, self.sim.reputation = previous.money, previous.earned, previous.reputation
        elif previous.phase == "quan":
            self.sim = ShopSim(self.tuning["shop"], self.upgrades, previous)
        else:
            self.days_completed += 1
            if self.days_completed == self.days:
                self.sim.reason = "days_complete"
                return []
            return self._start_day(previous.money, previous.earned, previous.reputation)
        self.phase_tick = 0
        return self._events([("phase_start", {})])

    @property
    def done(self) -> bool:
        return self.sim.done

    def snapshot(self) -> dict:
        state = "paused" if self.paused else "finished" if self.done else "playing"
        s = _common(self.sim, self.mode, self.tick, self.sim_tick, self.phase_tick, self.tuning, state)
        s.update(self.sim.snapshot())
        if self.mode == "day":
            s.update(day=self.day, day_plan=self.plan, upgrades=self.upgrades.copy(),
                     active_upgrades=self.active_upgrades.copy())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        self.tick += 1
        rows = []
        if inp.pressed("pause"):
            self.paused = not self.paused
            rows = self._events([("paused" if self.paused else "resumed", {})])
        if self.paused:
            return rows
        self.sim_tick += 1
        self.phase_tick += 1
        rows.extend(self._events(self.sim.step(inp)))
        if self.mode == "day" and self.sim.done:
            rows.extend(self._change_phase())
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        snap = self.snapshot()
        row = {k: snap[k] for k in ("mode", "state", "sim_tick", "money", "earned", "reputation", "score")}
        row.update(type="end", ticks=self.tick, reason=sim.reason if sim.done else "tick_limit")
        if self.mode == "day":
            row["days_completed"] = self.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_events:
            w.write(row)
        w.write(sess.snapshot())
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done or (mode == "day" and sess.phase_tick == 0 and not sess.paused):
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
