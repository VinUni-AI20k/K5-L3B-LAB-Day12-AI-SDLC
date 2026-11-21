"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: [sự kiện tick 0 của mode day] -> snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý)
rồi snapshot (nếu tới lượt hoặc lượt kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

Pause (Ticket-02 mục 4.2, cả ba mode): xét cạnh `pause` trước. Vào pause chỉ tăng tick ngoài và phát `paused`;
khi còn pause bỏ qua cạnh hành động và `buy`, `sim_tick`/`phase_tick`/timer đứng yên; cạnh kế tiếp phát
`resumed` và chạy gameplay ngay trong bước đó.

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
    if mode == "day":
        return DaySim(tuning, scenario, seed, days)
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days)
        self.tick = 0       # số bước ngoài (kể cả bước pause)
        self.sim_tick = 0   # số bước gameplay toàn lượt
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    @property
    def phase_tick(self) -> int:
        # day reset theo pha; gather/quan độc lập chỉ có một pha nên bằng sim_tick
        return self.sim.phase_tick if self.mode == "day" else self.sim_tick

    def _state(self) -> str:
        if self.sim.done:
            return "finished"
        return "paused" if self.paused else "playing"

    def snapshot(self) -> dict:
        s = _common(self.sim, self.tick, self.sim_tick, self.phase_tick, self.tuning, self._state())
        s.update(self.sim.snapshot())
        return s

    def _row(self, ev) -> dict:
        if len(ev) == 4:  # mode day: (phase, day, name, data)
            phase, day, name, data = ev
            return {"type": "event", "tick": self.tick, "phase": phase, "day": day, "name": name, "data": data}
        name, data = ev
        return {"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data}

    def _shell(self, name) -> tuple:
        """Sự kiện của runner (paused/resumed) theo vỏ của mode hiện tại."""
        if self.mode == "day":
            return (self.sim.phase, self.sim.day, name, {})
        return (name, {})

    def start_rows(self) -> list:
        """Sự kiện ở tick 0 (trước snapshot tick 0): chỉ mode day có."""
        init = getattr(self.sim, "initial_events", None)
        return [self._row(e) for e in init()] if init else []

    def step(self, inp) -> list:
        """Chạy một bước ngoài với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        lead = []
        if inp.pressed("pause"):
            self.paused = not self.paused
            lead.append(self._shell("paused" if self.paused else "resumed"))
        if self.paused:
            self.tick += 1
            return [self._row(e) for e in lead]
        events = lead + list(self.sim.step(inp))
        self.tick += 1
        self.sim_tick += 1
        return [self._row(e) for e in events]

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.sim_tick, self.phase_tick, self.tuning, "")["score"]
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
               "state": "finished" if sim.done else "playing",
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None,
        inventory_out=None, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.start_rows():
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
