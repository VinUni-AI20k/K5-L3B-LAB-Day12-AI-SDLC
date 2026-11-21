"""Đàn cá v1.1. Gather gọi sau tương tác và khi ca còn giờ."""

import math

from ..errors import BadInput
from ..ids import sort_by_id


FULL_TURN = math.degrees(math.tau)


def _reflect_axis(position, delta, bounds):
    lo, hi = bounds
    target = position + delta
    if lo < target < hi:
        return target, False

    # Gập phần đường còn lại qua mép. Chu kỳ hai lần bề rộng cũng xử lý
    # được bước đi qua nhiều mép nếu dùng tuning khác.
    width = hi - lo
    offset = (target - lo) % (2 * width)
    if offset == 0:
        return lo, delta < 0
    if offset == width:
        return hi, delta > 0
    if offset < width:
        return lo + offset, False
    return hi - (offset - width), True


class FishDynamics:
    def __init__(self, tuning, tick_hz, streams, ids):
        self.t = tuning
        self.distance_per_tick = tuning["fish_speed"] / tick_hz
        self.spawn_rng = streams.get("fish_spawn")
        self.turn_rng = streams.get("fish_turn")
        self.ids = ids
        self.spawn_points = {
            kind: [(x, d) for x in sorted(tuning["fish_spawn_x"]) for d in sorted(set(depths))]
            for kind, depths in sorted(tuning["fish_spawn_depths"].items())
        }

    def populate(self, schools):
        # Cùng quy tắc khoảng cách và chọn loài như lượt sinh định kỳ (clarify #8).
        for _ in range(self.t["fish_initial"]):
            if self._spawn(schools) is None:
                raise BadInput("không đủ điểm hợp lệ để sinh đàn cá đầu ca")

    def step(self, schools, phase_tick, events):
        for fish in sort_by_id(schools):
            self._swim(fish)
        if phase_tick % self.t["fish_spawn_ticks"] == 0 and len(schools) < self.t["fish_max"]:
            fish = self._spawn(schools)
            if fish is not None:
                events.append(("fish_spawned", {"id": fish["id"], "kind": fish["kind"], "pos": fish["pos"].copy()}))

    def _swim(self, fish):
        fish["age_ticks"] += 1
        if fish["age_ticks"] % self.t["fish_turn_ticks"] == 0:
            fish["heading_deg"] = self.turn_rng.random() * FULL_TURN
        angle = math.radians(fish["heading_deg"])
        dx, dd = math.cos(angle), math.sin(angle)
        x, d = fish["pos"]
        x, flip_x = _reflect_axis(x, dx * self.distance_per_tick, self.t["fish_x"])
        d, flip_d = _reflect_axis(d, dd * self.distance_per_tick, self.t["fish_depths"][fish["kind"]])
        fish["pos"] = [x, d]
        if flip_x or flip_d:
            fish["heading_deg"] = math.degrees(math.atan2(-dd if flip_d else dd, -dx if flip_x else dx)) % FULL_TURN

    def _spawn(self, schools):
        clearance = self.t["fish_spawn_clearance"]
        eligible = {}
        for kind, points in self.spawn_points.items():
            available = [p for p in points if all(math.dist(p, fish["pos"]) > clearance for fish in schools)]
            if available:
                eligible[kind] = available
        if not eligible:
            return None

        kinds = list(eligible)
        weights = [self.t["fish_weights"][kind] for kind in kinds]
        kind = self.spawn_rng.choices(kinds, weights)[0]
        fish = {
            "id": self.ids.new("F"), "kind": kind, "pos": list(self.spawn_rng.choice(eligible[kind])),
            "heading_deg": self.spawn_rng.random() * FULL_TURN, "age_ticks": 0,
        }
        schools.append(fish)
        return fish
