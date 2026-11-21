"""Cá Sấu, Máu, ngạt (v1.1, Ticket-02 mục 1.2). Gather gọi `MonsterDynamics.step` ngay sau bơi và oxy.

Mọi số đọc từ `tuning.gather.monsters` (`species`, `spawns`, `invuln_ticks`, `loss_ratio`). Không dùng RNG.

Mỗi bước, quái xét theo id tăng dần:
- `recoil`: lùi ra xa người chơi theo hướng chốt lúc cắn, mỗi bước `recoil_dist / recoil_ticks` (clarify #7);
  hết `recoil_ticks` thì về `patrol`. Đang lùi thì không cắn.
- `patrol`: bơi về waypoint hiện tại với `patrol_speed`; tới nơi thì chuyển waypoint kế (vòng lại).
  Người chơi dưới nước và cách quái `<= detect_radius` thì chuyển `chase` (xét trước khi bơi).
- `chase`: bơi thẳng về người chơi với `chase_speed`; người chơi nổi lên hoặc cách `> exit_radius` thì về `patrol`.
- Quái luôn bị chặn trong `bounds.x` và dải `depths` của loài.
- Sau khi bơi, quái `patrol` hoặc `chase` cách người chơi `<= hit_radius` mà người chơi hết bất tử thì cắn:
  Máu − 1, mất `floor(số món trong giỏ × loss_ratio)` món mới nhặt trước, bất tử `invuln_ticks`, quái chuyển
  `recoil`. Máu về 0 thì ngất (`cause: "monster"`), mất cả phần giỏ còn lại. Bất tử không chặn ngạt (clarify P1-04).
"""

import math

from ..ids import sort_by_id

STATES = ("patrol", "chase", "recoil")


def active_spawns(monsters_tuning, day):
    """Quái mặc định của Ngày `day`: những spawn có `from_day <= day` (clarify #10)."""
    return [sp for sp in monsters_tuning["spawns"] if sp.get("from_day", 1) <= day]


def make_monster(src):
    pos = [float(c) for c in src["pos"]]
    waypoints = [[float(c) for c in wp] for wp in src.get("waypoints", [src["pos"]])]
    return {"id": src["id"], "kind": src["kind"], "pos": pos, "state": src.get("state", "patrol"),
            "waypoints": waypoints, "waypoint_index": src.get("waypoint_index", 0),
            "recoil_ticks_left": 0, "recoil_dir": [0.0, 0.0]}


def snapshot_monster(m):
    return {"id": m["id"], "kind": m["kind"], "pos": m["pos"].copy(), "state": m["state"],
            "waypoint_index": m["waypoint_index"], "recoil_ticks_left": m["recoil_ticks_left"]}


def _step_toward(pos, target, dist_per_tick):
    gap = math.dist(pos, target)
    if gap <= dist_per_tick:
        return [float(target[0]), float(target[1])], True
    k = dist_per_tick / gap
    return [pos[0] + (target[0] - pos[0]) * k, pos[1] + (target[1] - pos[1]) * k], False


def _clamp(v, lo, hi):
    return min(hi, max(lo, v))


class MonsterDynamics:
    def __init__(self, gather_tuning, tick_hz):
        self.g = gather_tuning
        self.m = gather_tuning["monsters"]
        self.tick_hz = tick_hz

    def step(self, sim, at_surface, events):
        """Cập nhật quái và cắn. `sim` là GatherSim (đọc pos, sửa hp, hold, invuln_ticks)."""
        for mon in sort_by_id(sim.monsters):
            sp = self.m["species"][mon["kind"]]
            if mon["state"] == "recoil":
                self._recoil(mon, sp)
                continue
            gap = math.dist(mon["pos"], sim.pos)
            if mon["state"] == "patrol" and not at_surface and gap <= sp["detect_radius"]:
                mon["state"] = "chase"
            elif mon["state"] == "chase" and (at_surface or gap > sp["exit_radius"]):
                mon["state"] = "patrol"
            if mon["state"] == "chase":
                mon["pos"], _ = _step_toward(mon["pos"], sim.pos, sp["chase_speed"] / self.tick_hz)
            else:
                wp = mon["waypoints"][mon["waypoint_index"]]
                mon["pos"], arrived = _step_toward(mon["pos"], wp, sp["patrol_speed"] / self.tick_hz)
                if arrived:
                    mon["waypoint_index"] = (mon["waypoint_index"] + 1) % len(mon["waypoints"])
            self._clamp(mon, sp)
            if sim.invuln_ticks == 0 and math.dist(mon["pos"], sim.pos) <= sp["hit_radius"]:
                self._hit(sim, mon, sp, events)
                if sim.done:
                    return

    def _recoil(self, mon, sp):
        d = sp["recoil_dist"] / sp["recoil_ticks"]
        mon["pos"] = [mon["pos"][0] + mon["recoil_dir"][0] * d, mon["pos"][1] + mon["recoil_dir"][1] * d]
        self._clamp(mon, sp)
        mon["recoil_ticks_left"] -= 1
        if mon["recoil_ticks_left"] <= 0:
            mon["recoil_ticks_left"] = 0
            mon["state"] = "patrol"

    def _clamp(self, mon, sp):
        xlo, xhi = self.g["bounds"]["x"]
        dlo, dhi = sp["depths"]
        mon["pos"] = [_clamp(mon["pos"][0], xlo, xhi), _clamp(mon["pos"][1], dlo, dhi)]

    def _hit(self, sim, mon, sp, events):
        sim.hp -= 1
        count = math.floor(len(sim.hold) * self.m["loss_ratio"])
        lost = sim.hold[::-1][:count]
        if count:
            del sim.hold[-count:]
        sim.invuln_ticks = self.m["invuln_ticks"]
        # hướng lùi: từ người chơi ra quái; trùng vị trí thì lùi ngược hướng mặt người chơi
        dx, dd = mon["pos"][0] - sim.pos[0], mon["pos"][1] - sim.pos[1]
        norm = math.hypot(dx, dd)
        if norm == 0:
            a = math.radians(sim.heading)
            dx, dd, norm = -math.cos(a), -math.sin(a), 1.0
        mon["recoil_dir"] = [dx / norm, dd / norm]
        mon["state"] = "recoil"
        mon["recoil_ticks_left"] = sp["recoil_ticks"]
        events.append(("monster_hit", {"monster_id": mon["id"], "kind": mon["kind"], "hp": sim.hp, "lost": lost}))
        if sim.hp <= 0:
            sim.hp = 0
            rest = sim.hold[::-1]
            sim.hold.clear()
            events.append(("faint", {"cause": "monster", "lost": rest, "hp": 0}))
            sim._finish("fainted", events)
