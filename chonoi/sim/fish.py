"""Phase 2, ticket 02: bơi và sinh đàn cá theo tuning v1.1.

GatherSim và catch dùng chung danh sách schools. Một lần advance tương ứng
một bước gameplay; caller không gọi khi pause. Cá mới có age_ticks = 0 nên
chỉ tham gia từ bước kế tiếp.
"""

import math

from ..ids import sort_by_id


def _reflect(pos, delta, lo, hi):
    """Gấp quãng đường vượt mép trở vào, kể cả vượt nhiều lần trong một bước."""
    width = hi - lo
    offset = (pos + delta - lo) % (2 * width)
    if offset == 0:
        return lo, abs(delta)
    if offset == width:
        return hi, -abs(delta)
    if offset < width:
        return lo + offset, delta
    return hi - (offset - width), -delta


class FishSchools:
    def __init__(self, tuning, tick_hz, scenario, streams, ids):
        self.t = tuning
        self.tick_hz = tick_hz
        self.streams = streams
        self.ids = ids
        self.phase_tick = 0
        self.enabled = scenario.get("random_fish", True)
        source = scenario.get("fish", tuning["fish_initial"] if self.enabled else [])
        self.schools = [{"id": f["id"], "kind": f["kind"],
                         "pos": [float(c) for c in f["pos"]],
                         "heading_deg": f.get("heading_deg", 0),
                         "age_ticks": f.get("age_ticks", 0)} for f in source]
        for fish in self.schools:
            ids.reserve(fish["id"])

    def advance(self, events):
        self.phase_tick += 1
        for fish in sort_by_id(self.schools):
            fish["age_ticks"] += 1
            if not self.enabled:
                continue
            if self.phase_tick % self.t["fish_turn_ticks"] == 0:
                fish["heading_deg"] = self.streams.get("fish_turn").uniform(0, 360)
            self._swim(fish)
        if self.enabled and self.phase_tick % self.t["fish_spawn_ticks"] == 0:
            self._spawn(events)

    def _swim(self, fish):
        angle = math.radians(fish["heading_deg"])
        step = self.t["fish_speed"] / self.tick_hz
        x, dx = _reflect(fish["pos"][0], math.cos(angle) * step, *self.t["fish_x"])
        depth, dd = _reflect(fish["pos"][1], math.sin(angle) * step,
                             *self.t["fish_depths"][fish["kind"]])
        fish["pos"] = [x, depth]
        if step:
            fish["heading_deg"] = math.degrees(math.atan2(dd, dx)) % 360

    def _spawn(self, events):
        if len(self.schools) >= self.t["fish_max"]:
            return
        available = []
        clearance = self.t["fish_spawn_clearance"]
        for kind, weight in sorted(self.t["fish_weights"].items()):
            points = [[x, depth] for x in self.t["fish_spawn_x"]
                      for depth in self.t["fish_spawn_depths"][kind]
                      if all(math.dist((x, depth), f["pos"]) > clearance for f in self.schools)]
            if points and weight > 0:
                available.append((kind, weight, points))
        if not available:
            return
        rng = self.streams.get("fish_spawn")
        draw = rng.random() * sum(weight for _, weight, _ in available)
        chosen = available[-1]
        for candidate in available:
            draw -= candidate[1]
            if draw < 0:
                chosen = candidate
                break
        kind, _, points = chosen
        fish = {"id": self.ids.new("F"), "kind": kind, "pos": list(rng.choice(points)),
                "heading_deg": self.streams.get("fish_heading").uniform(0, 360), "age_ticks": 0}
        self.schools.append(fish)
        events.append(("fish_spawned", {"id": fish["id"], "kind": kind, "pos": fish["pos"].copy()}))
