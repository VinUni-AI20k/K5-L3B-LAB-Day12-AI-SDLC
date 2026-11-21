"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> sự kiện tick 0 (chỉ `day`) -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot
(nếu tới lượt hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.

v1.1: `pause` (cả ba chế độ) do Session xử lý, không do sim. Khi pause: chỉ `tick` ngoài tăng, sim đứng yên,
cạnh hành động và `buy` bị bỏ qua; cạnh `pause` kế tiếp phát `resumed` và chạy gameplay ngay trong bước đó.
`sim_tick` là số bước gameplay đã chạy, `phase_tick` là số bước từ lúc pha hiện tại bắt đầu.
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import inventory_schema, write_inventory, write_inventory_v12
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1, contract_version="1.1"):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids, contract_version=contract_version)
    if mode == "day":
        return DaySim(tuning, scenario, streams, days, contract_version=contract_version)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory, contract_version=contract_version)


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

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1, contract_version="1.1"):
        self.mode = mode
        self.tuning = tuning
        self.contract_version = contract_version
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days, contract_version)
        self.tick = 0  # tick ngoài: tăng cả lúc pause
        self.sim_ticks = 0  # bước gameplay đã chạy
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def _phase_tick(self) -> int:
        return getattr(self.sim, "phase_tick", self.sim_ticks)

    def snapshot(self) -> dict:
        state = "finished" if self.sim.done else ("paused" if self.paused else "playing")
        s = _common(self.sim, self.tick, self.sim_ticks, self._phase_tick(), self.tuning, state)
        s.update(self.sim.snapshot())
        return s

    def _rows(self, events, tick):
        """Đổi danh sách (tên, data[, meta]) của sim thành dòng event. `meta` có thể ghi đè phase và day."""
        rows = []
        for ev in events:
            name, data = ev[0], ev[1]
            meta = ev[2] if len(ev) > 2 else {}
            row = {"type": "event", "tick": tick, "phase": meta.get("phase", self.sim.phase)}
            day = meta.get("day", getattr(self.sim, "day", None))
            if day is not None and self.mode == "day":
                row["day"] = day
            row["name"], row["data"] = name, data
            rows.append(row)
        return rows

    def start_rows(self) -> list:
        """Sự kiện ở tick 0 (chế độ day: day_start, day_plan, phase_start). Ghi ngay sau snapshot tick 0."""
        start = getattr(self.sim, "start_events", None)
        return self._rows(start(), 0) if start else []

    def _gameplay(self, inp) -> list:
        events = self.sim.step(inp)
        self.sim_ticks += 1
        return events

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        events = []
        if self.paused:
            if inp.pressed("pause"):
                self.paused = False
                events.append(("resumed", {}))
                events.extend(self._gameplay(inp))  # chạy gameplay ngay trong bước hết pause
        elif inp.pressed("pause"):
            self.paused = True
            events.append(("paused", {}))
        else:
            events = self._gameplay(inp)
        self.tick += 1
        return self._rows(events, self.tick)

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.sim_ticks, self._phase_tick(), self.tuning, "")["score"]
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_ticks, "mode": sim.mode,
               "state": "finished" if sim.done else "playing",
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}
        if sim.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            if inventory_schema(self.contract_version) == "individuals":
                write_inventory_v12(inventory_out, self.sim.inventory_items())  # v1.2: kho cá thể
            else:
                write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1, contract_version="1.1"):
    sess = Session(mode, tuning, scenario, seed, inventory, days, contract_version)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        for row in sess.start_rows():
            w.write(row)
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
