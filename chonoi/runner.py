"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math
import os
import tempfile

from .day import Day
from .freshness import view_items
from .ids import IdAllocator
from .inputs import BUTTONS_V10, BUTTONS_V11, InputPlayer
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
        self.tick = 0
        self.sim_tick = 0
        self.phase_tick = 0
        self.paused = False
        self.buttons = BUTTONS_V11 if "shop" in tuning else BUTTONS_V10
        self.day = Day(tuning, scenario, seed, days, GatherSim, QuanSim) if mode == "day" else None
        self.sim = self.day.sim if self.day else build_sim(mode, tuning, scenario, seed, inventory)

    @property
    def done(self) -> bool:
        return self.day.done if self.day else self.sim.done

    @property
    def state(self) -> str:
        if self.done:
            return "finished"
        return "paused" if self.paused else "playing"

    def _snapshot_base(self):
        snapshot = _common(self.sim, self.tick, self.sim_tick, self.phase_tick, self.tuning, self.state)
        snapshot["mode"] = self.mode
        if self.day:
            snapshot.update(self.day.snapshot_fields())
            multiplier = self.tuning["score"]["reputation_multiplier"]
            snapshot["score"] = snapshot["earned"] + multiplier * math.floor(snapshot["reputation"])
        return snapshot

    def snapshot(self) -> dict:
        s = self._snapshot_base()
        s.update(self.sim.snapshot())
        return s

    def _event(self, name, data):
        row = {"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data}
        if self.day:
            row["day"] = self.day.number
        return row

    def initial_events(self):
        return [self._event(name, data) for name, data in self.day.opening_events()] if self.day else []

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        self.tick += 1
        rows = []
        if "pause" in self.buttons and inp.pressed("pause"):
            self.paused = not self.paused
            rows.append(self._event("paused" if self.paused else "resumed", {}))
        if self.paused:
            return rows
        self.sim_tick += 1
        self.phase_tick += 1
        rows.extend(self._event(name, data) for name, data in self.sim.step(inp))
        if self.day and self.sim.done:
            events = self.day.advance()
            if events:
                self.sim = self.day.sim
                self.phase_tick = 0
                rows.extend(self._event(name, data) for name, data in events)
        return rows

    def end_row(self) -> dict:
        snapshot = self._snapshot_base()
        reason = "days_complete" if self.day else self.sim.reason
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": self.mode,
               "state": self.state, "reason": reason if self.done else "tick_limit",
               **{key: snapshot[key] for key in ("money", "earned", "reputation", "score")}}
        if self.day:
            row["days_completed"] = self.day.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            items = self.sim.inventory_items()
            if "freshness" in self.tuning:
                view = view_items(items, self.tuning["freshness"]["spoiled_below"])
                write_inventory(inventory_out, view, contract_version="1.2")
            else:
                write_inventory(inventory_out, items)


def _write_run(sess, frames, ticks, path, snapshot_every):
    player = InputPlayer(frames, sess.buttons)
    w = JsonlWriter(path)
    try:
        for row in sess.initial_events():
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            events = sess.step(inp)
            for row in events:
                w.write(row)
            changed_phase = any(row["name"] == "phase_start" for row in events)
            if sess.tick % snapshot_every == 0 or sess.done or changed_phase:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every,
        inventory=None, inventory_out=None, *, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days=days)
    if mode == "day":
        # Fixture Quán phụ thuộc kho lúc chuyển pha. Giữ output cũ nếu fixture bị từ chối.
        directory = os.path.dirname(os.path.abspath(out_path))
        fd, temporary = tempfile.mkstemp(prefix=".day-", suffix=".jsonl", dir=directory)
        os.close(fd)
        try:
            _write_run(sess, frames, ticks, temporary, snapshot_every)
            os.replace(temporary, out_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    else:
        _write_run(sess, frames, ticks, out_path, snapshot_every)
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
