"""Vòng tick (Contract B, mô hình tick). KHUNG.

Thứ tự ghi: (event dựng lượt ở tick 0 nếu có) -> snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý)
rồi snapshot (nếu tới lượt hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.

v1.1 (TICKET-02 mục 4.2, TV3 sửa khung — lý do: pause ở cả ba mode và `--mode day` cần tách bước ngoài khỏi bước
gameplay): `tick` là số bước ngoài, `sim_tick`/`phase_tick` chỉ tăng khi gameplay chạy. Khi pause, bước chỉ tăng
`tick`, phát `paused`; cạnh `pause` kế tiếp phát `resumed` và chạy gameplay ngay trong bước đó. `--mode day` dùng
`chonoi.sim.day.DaySession` (cùng giao diện).
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


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": score_of(tuning, sim.earned, sim.reputation),
    }


class PauseGate:
    """Xét cạnh `pause` TRƯỚC mọi thứ (v1.1 mục 4.2). Trả (có chạy gameplay không, event pause/resume)."""

    def __init__(self):
        self.paused = False

    def filter(self, inp):
        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                return False, [("paused", {})]
            self.paused = False
            return True, [("resumed", {})]
        if self.paused:
            return False, []  # bỏ qua cạnh hành động và buy; sim_tick, phase_tick, lịch, timer đứng yên
        return True, []


class Session:
    """Một lượt chơi gather/quan: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory)
        self.tick = 0
        self.sim_tick = 0
        self.gate = PauseGate()
        self.initial_rows = []

    @property
    def done(self) -> bool:
        return self.sim.done

    @property
    def paused(self) -> bool:
        return self.gate.paused

    def _state(self):
        if self.sim.done:
            return "finished"
        return "paused" if self.gate.paused else "playing"

    def snapshot(self) -> dict:
        s = _common(self.sim, self.tick, self.sim_tick, self.sim_tick, self.tuning, self._state())
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        run_gameplay, events = self.gate.filter(inp)
        if run_gameplay:
            events = events + self.sim.step(inp)
            self.sim_tick += 1
        self.tick += 1
        return [{"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data}
                for name, data in events]

    def end_row(self) -> dict:
        sim = self.sim
        return {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
                "state": self._state(),
                "reason": sim.reason if sim.done else "tick_limit",
                "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
                "score": score_of(self.tuning, sim.earned, sim.reputation)}

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def make_session(mode, tuning, scenario, seed, inventory=None, days=1):
    if mode == "day":
        from .sim.day import DaySession  # nhập muộn: day cần cấu hình v1.1 (day_plan, shop)
        return DaySession(tuning, scenario, seed, days)
    return Session(mode, tuning, scenario, seed, inventory)


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1):
    sess = make_session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_rows:  # day: day_start, day_plan, phase_start(gather) ở tick 0
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
    if mode != "day":
        sess.write_inventory_if_done(inventory_out)
    return sess
