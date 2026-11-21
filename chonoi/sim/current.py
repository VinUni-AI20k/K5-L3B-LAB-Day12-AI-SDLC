"""Dòng nước lũ, chỉ hoạt động khi extension current được truyền vào sim."""


class Current:
    def __init__(self, config, scenario, streams, tick_hz):
        self.t = config
        self.enabled = scenario.get("random_current", True)
        self.locked_direction = scenario.get("current_direction")
        self.streams = streams
        self.tick_hz = tick_hz
        self.phase_tick = 0
        self.direction = None
        self.ends_at = None

    def advance(self, events):
        self.phase_tick += 1
        if not self.enabled:
            return
        if self.direction is not None and self.phase_tick >= self.ends_at:
            self.end(events, "elapsed")
        interval = self.t["interval_ticks"]
        if (self.phase_tick + self.t["warning_ticks"]) % interval == 0:
            events.append(("current_warning", {"starts_at_phase_tick": self.phase_tick + self.t["warning_ticks"]}))
        if self.phase_tick % interval == 0:
            self.direction = (self.locked_direction if self.locked_direction is not None
                              else self.streams.get("current").choice((-1, 1)))
            self.ends_at = self.phase_tick + self.t["duration_ticks"]

    def displacement(self, start_depth):
        if self.direction is None or start_depth < self.t["min_depth"]:
            return 0
        return self.direction * self.t["speed"] / self.tick_hz

    def snapshot(self):
        if self.direction is None:
            return None
        return {"direction": self.direction, "ticks_left": self.ends_at - self.phase_tick}

    def end(self, events, reason):
        if self.direction is not None:
            event = ("current_end", {"direction": self.direction, "reason": reason})
            # Monster helper can have appended faint before invoking GatherSim._finish.
            index = next((i for i, (name, _) in enumerate(events) if name == "faint"), len(events))
            events.insert(index, event)
            self.direction = None
            self.ends_at = None
