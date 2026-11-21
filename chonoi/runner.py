"""Vòng tick (Contract B / v1.1): gather, quan, day và pause/resumed."""

from __future__ import annotations

import math

from .ids import IdAllocator
from .inputs import BUTTONS_V11, InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    if mode == "quan":
        return QuanSim(tuning, scenario, streams, ids, inventory=inventory)
    from .sim.day import DaySim
    return DaySim(tuning, scenario, streams, ids, days=days)


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot",
        "tick": tick,
        "sim_tick": sim_tick,
        "mode": sim.mode,
        "phase": sim.phase,
        "phase_tick": phase_tick,
        "state": state,
        "time_left_ticks": sim.time_left_ticks,
        "money": sim.money,
        "earned": sim.earned,
        "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


def _format_event(sim, tick, ev):
    if len(ev) == 4:
        phase, day, name, data = ev
    else:
        name, data = ev
        phase = sim.phase
        day = getattr(sim, "day", None)
    row = {"type": "event", "tick": tick, "phase": phase}
    if sim.mode == "day":
        row["day"] = day
    row["name"] = name
    row["data"] = data
    return row


class Session:
    """Một lượt chơi: dựng sim, bước từng tick (có pause), lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days=days)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def initial_events(self) -> list:
        fn = getattr(self.sim, "initial_events", None)
        if fn is None:
            return []
        return [_format_event(self.sim, 0, ev) for ev in fn()]

    def snapshot(self) -> dict:
        state = "paused" if self.paused else ("finished" if self.sim.done else "playing")
        ptick = getattr(self.sim, "phase_tick", self.sim_tick)
        s = _common(self.sim, self.tick, self.sim_tick, ptick, self.tuning, state)
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (hỗ trợ pause/resumed trước mọi hành động)."""
        out = []
        pause_edge = inp.pressed("pause")
        if self.paused:
            if not pause_edge:
                self.tick += 1
                return out
            self.paused = False
            self.tick += 1
            out.append(_format_event(self.sim, self.tick, ("resumed", {})))
            self.sim_tick += 1
            for ev in self.sim.step(inp):
                out.append(_format_event(self.sim, self.tick, ev))
            return out

        if pause_edge:
            self.paused = True
            self.tick += 1
            out.append(_format_event(self.sim, self.tick, ("paused", {})))
            return out

        self.tick += 1
        self.sim_tick += 1
        for ev in self.sim.step(inp):
            out.append(_format_event(self.sim, self.tick, ev))
        return out

    def end_row(self) -> dict:
        sim = self.sim
        mult = self.tuning["score"]["reputation_multiplier"]
        score = sim.earned + mult * math.floor(sim.reputation)
        row = {
            "type": "end",
            "ticks": self.tick,
            "sim_tick": self.sim_tick,
            "mode": sim.mode,
            "state": "finished" if sim.done else "playing",
            "reason": sim.reason if sim.done else "tick_limit",
            "money": sim.money,
            "earned": sim.earned,
            "reputation": sim.reputation,
            "score": score,
        }
        if self.mode == "day":
            row["days_completed"] = int(getattr(sim, "days_completed", 0))
        return row

    def write_inventory_if_done(self, inventory_out):
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every,
        inventory=None, inventory_out=None, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days=days)
    player = InputPlayer(frames, buttons=BUTTONS_V11)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_events():
            w.write(row)
        w.write(sess.snapshot())
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)
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
