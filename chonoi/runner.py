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
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "day":
        return DaySim(tuning, scenario, streams, days)
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
        self.tick = 0       # tick ngoài (tăng cả khi pause)
        self.sim_tick = 0   # tick mô phỏng (đứng yên khi pause)
        self.paused = False
        self._start_events = self._take_start_events()

    def _take_start_events(self):
        """Mode day: sự kiện tick 0 (day_start, day_plan, phase_start) dựng lúc khởi tạo, ghi sau snapshot 0."""
        rows = []
        for name, data, phase, day in getattr(self.sim, "_boot", []):
            rows.append({"type": "event", "tick": 0, "phase": phase, "day": day, "name": name, "data": data})
        return rows

    def start_events(self) -> list:
        rows, self._start_events = self._start_events, []
        return rows

    @property
    def snapshot_now(self) -> bool:
        """Đổi pha / Ngày ở tick vừa rồi: ghi snapshot (pha mới, phase_tick = 0)."""
        return bool(getattr(self.sim, "sim_changed", False))

    @property
    def done(self) -> bool:
        return self.sim.done

    def snapshot(self) -> dict:
        state = "finished" if self.sim.done else ("paused" if self.paused else "playing")
        phase_tick = getattr(self.sim, "phase_tick", self.sim_tick)
        s = _common(self.sim, self.tick, self.sim_tick, phase_tick, self.tuning, state)
        s.update(self.sim.snapshot())
        return s

    def _rows(self, events) -> list:
        rows = []
        for ev in events:
            name, data = ev[0], ev[1]
            phase = ev[2] if len(ev) > 2 else self.sim.phase
            row = {"type": "event", "tick": self.tick, "phase": phase, "name": name, "data": data}
            if len(ev) > 3:
                row["day"] = ev[3]
            elif hasattr(self.sim, "day"):  # mode day: mọi event có `day` (cả paused/resumed)
                row["day"] = self.sim.day
            rows.append(row)
        return rows

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1).

        Cạnh `pause` xét trước: vào pause chỉ tăng tick ngoài (event `paused`); đang pause thì bỏ qua mọi
        cạnh khác; cạnh tiếp theo phát `resumed` và chạy gameplay ngay trong bước đó."""
        self.tick += 1
        pre = []
        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                return self._rows([("paused", {})])
            self.paused = False
            pre = [("resumed", {})]
        elif self.paused:
            return []
        self.sim_tick += 1
        events = pre + self.sim.step(inp)
        return self._rows(events)

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.sim_tick, self.sim_tick, self.tuning, "")["score"]
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
               "state": "finished" if sim.done else "playing",
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}
        if hasattr(sim, "end_extra"):
            row.update(sim.end_extra())
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
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        for row in sess.start_events():
            w.write(row)
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done or sess.snapshot_now:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
