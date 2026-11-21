"""Vòng tick (Contract B, mô hình tick).

Thứ tự ghi: [event khởi tạo tick 0 (day)] -> snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý)
rồi snapshot (nếu tới lượt hoặc lượt kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

Pause (v1.1, TICKET-02 mục 4.2) xử lý ở đây cho cả 3 mode: xét cạnh `pause` TRƯỚC. Vào pause chỉ tăng tick
ngoài và phát `paused`; khi còn pause bỏ qua mọi cạnh hành động và buy, sim_tick/phase_tick/timer đứng yên;
cạnh lên tiếp theo phát `resumed` rồi chạy gameplay ngay trong bước đó.

`Session` là API bước tick dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim. `--mode day` dùng `chonoi.day.DaySession` (kế thừa Session).
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


def score_of(tuning, earned, reputation):
    return earned + tuning["score"]["reputation_multiplier"] * math.floor(reputation)


class Session:
    """Một lượt chơi gather/quan: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory)
        self.tick = 0        # số bước ngoài (kể cả bước pause)
        self.sim_tick = 0    # số bước gameplay toàn lượt
        self.phase_tick = 0  # số bước gameplay trong pha hiện tại
        self.paused = False

    # --- trạng thái ---------------------------------------------------------------
    @property
    def done(self) -> bool:
        return self.sim.done

    @property
    def reason(self):
        return self.sim.reason

    def abort(self, reason):
        """Dừng lượt (cửa sổ live gặp lỗi)."""
        self.sim.done = True
        self.sim.reason = reason

    def state(self) -> str:
        return "finished" if self.done else ("paused" if self.paused else "playing")

    def initial_rows(self) -> list:
        """Event ở tick 0, ghi trước snapshot tick 0 (gather/quan: không có)."""
        return []

    def snapshot(self) -> dict:
        sim = self.sim
        s = {"type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick, "mode": self.mode,
             "phase": sim.phase, "phase_tick": self.phase_tick, "state": self.state(),
             "time_left_ticks": sim.time_left_ticks, "money": sim.money, "earned": sim.earned,
             "reputation": sim.reputation, "score": score_of(self.tuning, sim.earned, sim.reputation)}
        s.update(sim.snapshot())
        return s

    def end_row(self) -> dict:
        sim = self.sim
        return {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": self.mode,
                "state": "finished" if self.done else "playing",
                "reason": self.reason if self.done else "tick_limit",
                "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
                "score": score_of(self.tuning, sim.earned, sim.reputation)}

    # --- một bước -----------------------------------------------------------------
    def _event(self, tick, phase, name, data, day=None) -> dict:
        return {"type": "event", "tick": tick, "phase": phase, "name": name, "data": data}

    def current_phase(self) -> str:
        return self.sim.phase

    def _gameplay(self, inp) -> list:
        """Một bước gameplay; trả [(phase, name, data)]. DaySession ghi đè để đổi pha."""
        self.phase_tick += 1
        return [(self.sim.phase, name, data) for name, data in self.sim.step(inp)]

    def step(self, inp) -> list:
        """Chạy một bước ngoài với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        nxt = self.tick + 1
        rows = []
        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                self.tick = nxt
                return [self._event(nxt, self.current_phase(), "paused", {})]
            self.paused = False
            rows.append(self._event(nxt, self.current_phase(), "resumed", {}))
        elif self.paused:
            self.tick = nxt
            return []
        for ev in self._gameplay(inp):  # (phase, name, data[, day])
            rows.append(self._event(nxt, *ev))
        self.sim_tick += 1
        self.tick = nxt
        return rows

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def make_session(mode, tuning, scenario, seed, inventory=None, days=1):
    if mode == "day":
        from .day import DaySession
        return DaySession(tuning, scenario, seed, days)
    return Session(mode, tuning, scenario, seed, inventory)


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1):
    sess = make_session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_rows():
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
    return sess
