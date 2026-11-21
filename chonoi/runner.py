"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import merge_items, read_inventory_or_empty, write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim
from .sim.day import DaySim


def build_sim(mode, tuning, scenario, seed, inventory):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    if mode == "quan":
        return QuanSim(tuning, scenario, streams, ids, inventory=inventory)
    if mode == "day":
        return DaySim(tuning, scenario, streams, ids, inventory=inventory)
    raise ValueError(f"mode không hỗ trợ: {mode}")


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

    def __init__(self, mode, tuning, scenario, seed, inventory=None):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory)
        self.tick = 0

    @property
    def done(self) -> bool:
        return self.sim.done

    def snapshot(self) -> dict:
        s = _common(self.sim, self.tick, self.tick, self.tick, self.tuning, "finished" if self.sim.done else "playing")
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        events = self.sim.step(inp)
        self.tick += 1
        rows = []
        for name, data in events:
            event_phase = self.sim.phase
            if self.mode == "day":
                if name == "gather_end":
                    event_phase = "gather"
                elif name == "phase_start":
                    event_phase = "quan"
            rows.append({"type": "event", "tick": self.tick, "phase": event_phase,
                         "name": name, "data": data})
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.tick, self.tick, self.tuning, "")["score"]
        return {"type": "end", "ticks": self.tick, "sim_tick": self.tick, "mode": sim.mode,
                "state": "finished" if sim.done else "playing",
                "reason": sim.reason if sim.done else "tick_limit",
                "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}

    def write_inventory_if_done(self, inventory_out, inventory_base=None):
        """Persist the run's held items on top of the inventory present at run start."""
        if self.mode in ("gather", "day") and self.sim.done and inventory_out:
            write_inventory(inventory_out, merge_items(inventory_base or {}, self.sim.inventory_items()))


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None):
    sess = Session(mode, tuning, scenario, seed, inventory)
    inventory_base = read_inventory_or_empty(inventory_out) if mode in ("gather", "day") and inventory_out else {}
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            rows = sess.step(inp)
            if mode in ("gather", "day") and inventory_out:
                if any(row["name"] in {"gather", "fish_caught", "faint", "gather_end"} for row in rows):
                    write_inventory(inventory_out,
                                    merge_items(inventory_base, sess.sim.inventory_items()))
            for row in rows:
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out, inventory_base)
    return sess.sim
