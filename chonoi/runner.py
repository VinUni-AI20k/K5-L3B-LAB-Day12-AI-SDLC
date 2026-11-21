"""Vòng tick (Contract B, mô hình tick). KHUNG — sửa cho v1.1 bởi TV6 (T243, T245), xem AGENTS.md.

Thứ tự ghi: [mode day: sự kiện tick 0] -> snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý)
rồi snapshot (nếu tới lượt, đổi pha, hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

Ba bộ đếm (v1.1): `tick` bước ngoài (tăng cả khi pause), `sim_tick` bước gameplay, `phase_tick` bước trong
pha hiện tại (0 ở snapshot đổi pha). Gather/quan độc lập: `phase_tick == sim_tick`.

Pause (đề §4.2) là lớp bọc chung ở `Session.step`, dùng cho cả ba mode: xét cạnh `pause` TRƯỚC; vào pause chỉ
tăng `tick`, phát `paused`; còn pause thì bỏ cạnh hành động/`buy`, không gọi sim (lịch, timer kể cả Shop
đứng yên); cạnh kế phát `resumed` rồi chạy gameplay ngay bước đó.

Kho v1.2 (TV6, T306): đọc/ghi theo `contract_version` qua hàm của TV1 (`inventory_io`); một `IdAllocator`
cho cả lượt chạy là bộ cấp id cá thể `I<n>` toàn cục (reserve mọi id cá thể nạp từ scenario/file trước khi
sim cấp mới); `--inventory-out` ghi đúng một lần khi có `gather_end` (ngất → `{"items":[]}`), chạm `--ticks`
trước thì không đụng đích. v1.0/v1.1 giữ nguyên từng byte.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import inspect
import math

from .ids import IdAllocator
from .inputs import BUTTONS_V10, InputPlayer
from .errors import BadInput
from .inventory import read_inventory, write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .scenario import is_v12
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def inventory_io(version):
    """(đọc, ghi) file kho theo phiên bản. v1.0/v1.1: hàm cũ y nguyên. v1.2: hàm của TV1 nhận `version`."""
    if not is_v12(version):
        return read_inventory, write_inventory
    ok = all("version" in inspect.signature(f).parameters for f in (read_inventory, write_inventory))
    if not ok:
        raise BadInput("kho cá thể v1.2 chưa hỗ trợ — chờ TV1: chonoi.inventory.read_inventory(path, version=…) "
                       "và write_inventory(path, items, version=…) (T301, T302)")
    return (lambda path: read_inventory(path, version=version),
            lambda path, items: write_inventory(path, items, version=version))


def _item_ids(scenario, inventory):
    """Id của mọi cá thể nạp sẵn (scenario hold/stock, file kho, mẫu day) — rỗng với kho đếm v1.0/v1.1."""
    arrays = [inventory]
    for b in (scenario, scenario.get("gather"), scenario.get("quan")):
        if isinstance(b, dict):
            arrays += [b.get("hold"), b.get("stock")]
    if isinstance(inventory, dict):
        arrays.append(inventory.get("items"))
    return [it["id"] for arr in arrays if isinstance(arr, list)
            for it in arr if isinstance(it, dict) and isinstance(it.get("id"), str)]


def build_sim(mode, tuning, scenario, seed, inventory, days=1, version=None):
    streams, ids = Streams(seed), IdAllocator()
    for iid in _item_ids(scenario, inventory):  # bộ cấp I<n> toàn cục tiếp tục sau id lớn nhất đã nạp
        ids.reserve(iid)
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    if mode == "day":
        return DaySim(tuning, scenario, streams, ids, days=days, version=version)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


def _score(sim, tuning):
    return sim.earned + tuning["score"]["reputation_multiplier"] * math.floor(sim.reputation)


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1, version=None):
        self.mode = mode
        self.version = version
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days, version)
        self.tick = 0
        self.sim_tick = 0
        self.phase_tick = 0
        self.paused = False
        self.phase_changed = False  # đổi pha ở bước vừa chạy → runner ghi snapshot

    @property
    def done(self) -> bool:
        return self.sim.done

    def _state(self):
        if self.sim.done:
            return "finished"
        return "paused" if self.paused else "playing"

    def _row(self, name, data, phase=None, day=None):
        row = {"type": "event", "tick": self.tick, "phase": phase if phase is not None else self.sim.phase}
        if self.mode == "day":
            row["day"] = day if day is not None else self.sim.day
        row["name"] = name
        row["data"] = data
        return row

    def initial_events(self) -> list:
        """Sự kiện tick 0 (mode day: day_start → day_plan → phase_start). Ghi TRƯỚC snapshot tick 0."""
        if not hasattr(self.sim, "initial_events"):
            return []
        return [self._row(*e) for e in self.sim.initial_events()]

    def snapshot(self) -> dict:
        sim = self.sim
        s = {"type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
             "phase": sim.phase, "phase_tick": self.phase_tick, "state": self._state(),
             "time_left_ticks": sim.time_left_ticks, "money": sim.money, "earned": sim.earned,
             "reputation": sim.reputation, "score": _score(sim, self.tuning)}
        s.update(sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        self.phase_changed = False
        self.tick += 1
        rows = []
        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                return [self._row("paused", {})]
            self.paused = False
            rows.append(self._row("resumed", {}))
        elif self.paused:
            return []
        events = self.sim.step(inp)
        self.sim_tick += 1
        self.phase_tick += 1
        for e in events:
            rows.append(self._row(*e) if len(e) > 2 else self._row(e[0], e[1]))
        if getattr(self.sim, "phase_changed", False):
            self.phase_changed = True
            self.phase_tick = 0
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
               "state": "finished" if sim.done else "playing",
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
               "score": _score(sim, self.tuning)}
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            items = self.sim.inventory_items()
            if is_v12(self.version) and not items:
                items = []  # ngất / giỏ rỗng → {"items":[]} (kể cả khi sim còn trả kho đếm rỗng)
            inventory_io(self.version)[1](inventory_out, items)


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1, buttons=BUTTONS_V10, strings=(), version=None):
    sess = Session(mode, tuning, scenario, seed, inventory, days, version)
    player = InputPlayer(frames, buttons, strings)
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
