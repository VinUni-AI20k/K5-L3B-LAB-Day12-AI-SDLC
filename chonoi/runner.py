"""Vòng tick (Contract B, mô hình tick).

Thứ tự ghi: [day: event tick 0 day_start/day_plan/phase_start] -> snapshot tick 0 -> với mỗi bước: sự
kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt, buổi kết thúc, hoặc đổi pha trong mode day) ->
dòng 'end'. Mỗi tick tối đa một snapshot.

Pause (v1.1 mục 4.2) làm MỘT lần ở lớp này cho cả ba mode: xét cạnh `pause` trước. Bước vào pause chỉ
tăng tick ngoài và phát `paused`; khi còn pause bỏ qua cạnh hành động và `buy`, sim_tick / phase_tick /
lịch / timer đứng yên (sim không được gọi). Cạnh lên kế tiếp phát `resumed` rồi chạy gameplay ngay
trong bước đó.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    if mode == "day":
        return DaySim(tuning, scenario, streams, ids, days=days)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days)
        self.tick = 0       # tick ngoài (cả lúc pause)
        self.sim_tick = 0   # số bước gameplay đã chạy
        self.paused = False
        self.phase_changed = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def _phase_tick(self):
        return getattr(self.sim, "phase_tick", self.sim_tick) if self.mode == "day" else self.sim_tick

    def _score(self):
        mult = self.tuning["score"]["reputation_multiplier"]
        return self.sim.earned + mult * math.floor(self.sim.reputation)

    def snapshot(self) -> dict:
        sim = self.sim
        state = "finished" if sim.done else ("paused" if self.paused else "playing")
        s = {
            "type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode, "phase": sim.phase,
            "phase_tick": self._phase_tick(), "state": state, "time_left_ticks": sim.time_left_ticks,
            "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": self._score(),
        }
        s.update(sim.snapshot())
        return s

    def _row(self, ev):
        if isinstance(ev, dict):  # mode day: event đã mang pha và Ngày lúc phát
            return {"type": "event", "tick": self.tick, "phase": ev["phase"], "day": ev["day"],
                    "name": ev["name"], "data": ev["data"]}
        name, data = ev
        return {"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data}

    def _meta(self, name):
        if self.mode == "day":
            return {"phase": self.sim.phase, "day": self.sim.day, "name": name, "data": {}}
        return (name, {})

    def initial_events(self) -> list:
        """Event tick 0 (chỉ mode day: day_start, day_plan, phase_start(gather))."""
        return [self._row(e) for e in getattr(self.sim, "initial_events", [])]

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        self.tick += 1
        self.phase_changed = False
        pre = []
        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                return [self._row(self._meta("paused"))]
            self.paused = False
            pre.append(self._meta("resumed"))
        elif self.paused:
            return []
        phase_before = (self.sim.phase, getattr(self.sim, "day", None))
        events = self.sim.step(inp)
        self.sim_tick += 1
        self.phase_changed = (self.sim.phase, getattr(self.sim, "day", None)) != phase_before
        return [self._row(e) for e in pre + list(events)]

    def end_row(self) -> dict:
        sim = self.sim
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
               "state": "finished" if sim.done else ("paused" if self.paused else "playing"),
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": self._score()}
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_events():
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done or sess.phase_changed:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
