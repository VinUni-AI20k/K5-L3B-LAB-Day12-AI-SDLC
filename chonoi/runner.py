"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math

from .ids import IdAllocator
from .inputs import BUTTONS_V11, InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory):
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

    def __init__(self, mode, tuning, scenario, seed, inventory=None, *, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = (DaySim(tuning, scenario, Streams(seed), days) if mode == "day"
                    else build_sim(mode, tuning, scenario, seed, inventory))
        self.tick = 0
        self.sim_tick = 0
        self.phase_tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    @property
    def state(self):
        if self.done:
            return "finished"
        return "paused" if self.paused else "playing"

    def snapshot(self) -> dict:
        s = _common(self.sim, self.tick, self.sim_tick, self.phase_tick, self.tuning, self.state)
        s.update(self.sim.snapshot())
        return s

    def _event_rows(self, events):
        return [self._event(name, data) for name, data in events]

    def _event(self, name, data):
        row = {"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data}
        if self.mode == "day":
            row["day"] = self.sim.day
        return row

    def initial_events(self):
        return self._event_rows(self.sim.day_start_events()) if self.mode == "day" else []

    def step(self, inp) -> list:
        """Bước ngoài k đọc input k, ghi sự kiện tại tick k+1."""
        if self.done:
            return []
        self.tick += 1
        rows = []
        if inp.pressed("pause"):
            self.paused = not self.paused
            rows.append(self._event("paused" if self.paused else "resumed", {}))
        if self.paused:
            return rows

        self.sim_tick += 1
        self.phase_tick += 1
        phase = self.sim.phase
        day = self.sim.day if self.mode == "day" else None
        for name, data in self.sim.step(inp):
            row = self._event(name, data)
            row["phase"] = phase
            if day is not None:
                row["day"] = day
            rows.append(row)
        if self.sim.phase != phase:
            self.phase_tick = 0
            events = self.sim.day_start_events() if self.sim.day != day else [("phase_start", {})]
            rows.extend(self._event_rows(events))
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.sim_tick, self.phase_tick, self.tuning, self.state)["score"]
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": self.mode,
               "state": self.state, "reason": sim.reason if self.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None, *, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days=days)
    player = InputPlayer(frames, buttons=BUTTONS_V11)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_events():
            w.write(row)
        w.write(sess.snapshot())
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            rows = sess.step(inp)
            for row in rows:
                w.write(row)
            if (sess.tick % snapshot_every == 0 or sess.done
                    or any(row["name"] == "phase_start" for row in rows)):
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
