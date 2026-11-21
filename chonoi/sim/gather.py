"""Buổi sáng — Lặn & Hái (`gather`), theo PRD-0 và TICKET-02 (Phase 2, Contract v1.1).

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Thứ tự xử lý một bước (Contract v1.1 mục 4.5):
  1. Đồng hồ, cooldown, giảm bất tử và hồi nút.
  2. Bơi, oxy, ngạt (choke -> Máu về 0 -> faint -> gather_end fainted).
  3. Cập nhật quái theo id (patrol, chase, recoil), rồi xét tối đa một hit.
     Chạm: mất 1 Máu, bỏ floor(len(hold)/2) LIFO, bất tử 90 tick, quái recoil 60 tick. Máu về 0 -> faint -> gather_end.
  4. Tương tác: bến trước (docked), rồi hái (gather / hold_full).
  5. Bắt cá: theo vị trí cá TRƯỚC KHI BƠI (fish_caught, hold_full không hồi).
  6. Xét hết giờ: gather_end(time).
  7. Nếu còn giờ: cá bơi (phản xạ mép, đổi hướng mỗi 120 tick theo seed), sinh cá theo lịch (phase_tick = 360*k).
"""

import math

from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")
SPECIES_LIST = ("ca_linh", "ca_loc", "ca_keo")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(p.get("oxygen_max_s", t["oxygen_max_s"]) * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp_max = p.get("hp_max", t["hp_max"])
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = scenario.get("phase_tick", 0)
        self.day = scenario.get("day", 1)

        # 1. Nút hái
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]

        # 2. Đàn cá
        self.random_fish = scenario.get("random_fish", True)
        if "fish" in scenario:
            src_fish = scenario["fish"]
            self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                          "heading_deg": float(f.get("heading_deg", 0.0)),
                          "age_ticks": f.get("age_ticks", 0)} for f in src_fish]
        elif self.random_fish:
            if isinstance(t.get("fish_initial"), int):
                self.fish = self._spawn_initial_fish(t["fish_initial"])
            elif isinstance(t.get("fish_initial"), list):
                self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                              "heading_deg": float(f.get("heading_deg", 0.0)),
                              "age_ticks": f.get("age_ticks", 0)} for f in t["fish_initial"]]
            else:
                self.fish = []
        else:
            self.fish = []

        # 3. Quái Cá Sấu Năm Chèo
        if "monsters" in scenario:
            src_monsters = scenario["monsters"]
        else:
            spawns = t.get("monsters", {}).get("spawns", [
                {"id": "M1", "kind": "ca_sau", "pos": [60.0, 24.0], "waypoints": [[60.0, 24.0], [64.0, 24.0]], "from_day": 1},
                {"id": "M2", "kind": "ca_sau", "pos": [85.0, 18.0], "waypoints": [[85.0, 18.0], [89.0, 18.0]], "from_day": 3}
            ])
            src_monsters = [m for m in spawns if m.get("from_day", 1) <= self.day]

        self.monsters = []
        for m in src_monsters:
            self.monsters.append({
                "id": m["id"],
                "kind": m["kind"],
                "pos": [float(c) for c in m["pos"]],
                "waypoints": [[float(c) for c in wp] for wp in m.get("waypoints", [[m["pos"][0], m["pos"][1]], [m["pos"][0] + 4, m["pos"][1]]])],
                "target_idx": m.get("target_idx", 1),
                "state": m.get("state", "patrol"),
                "state_ticks_left": m.get("state_ticks_left", 0),
                "recoil_dir": [float(c) for c in m["recoil_dir"]] if m.get("recoil_dir") else None,
            })

        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                self.ids.reserve(e["id"])

        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {
                "pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                "at_surface": self._at_surface()
            },
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      "age_ticks": f.get("age_ticks", 0)}
                     for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "kind": m["kind"], "pos": m["pos"], "state": m["state"],
                          "state_ticks_left": m["state_ticks_left"], "target_idx": m["target_idx"],
                          "waypoints": m["waypoints"], "recoil_dir": m["recoil_dir"]}
                         for m in sort_by_id(self.monsters)],
        }

    # --- sinh cá ban đầu --------------------------------------------------------
    def _spawn_initial_fish(self, n: int) -> list:
        fishes = []
        spawn_x = self.t.get("fish_spawn_x", [15, 30, 45, 60, 75, 90])
        spawn_depths = self.t.get("fish_spawn_depths", {
            "ca_linh": [5, 10], "ca_loc": [10, 16], "ca_keo": [24, 27]
        })
        weights = self.t.get("fish_weights", {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3})
        clearance = self.t.get("fish_spawn_clearance", 1.0)

        for _ in range(n):
            valid_points = {}
            for s in SPECIES_LIST:
                pts = []
                for x in spawn_x:
                    for d in spawn_depths.get(s, []):
                        pt = [float(x), float(d)]
                        if all(math.dist(pt, f["pos"]) > clearance for f in fishes):
                            pts.append(pt)
                valid_points[s] = pts

            avail = [s for s in SPECIES_LIST if valid_points[s]]
            if not avail:
                break

            tot = sum(weights[s] for s in avail)
            r = self.rng.get("fish_spawn").random() * tot
            accum = 0.0
            chosen_s = avail[-1]
            for s in avail:
                accum += weights[s]
                if r < accum:
                    chosen_s = s
                    break

            pts = sorted(valid_points[chosen_s])
            chosen_pt = pts[self.rng.get("fish_spawn").randrange(len(pts))]
            heading = self.rng.get("fish_spawn").uniform(0.0, 360.0)
            fid = self.ids.new("F")
            fishes.append({
                "id": fid, "kind": chosen_s, "pos": [float(chosen_pt[0]), float(chosen_pt[1])],
                "heading_deg": heading, "age_ticks": 0
            })
        return fishes

    # --- một bước (thứ tự mục 4.5) ----------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ, cooldown, giảm bất tử và hồi nút
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.phase_tick += 1
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))

        # 2. bơi + oxy + ngạt
        d_before = self.pos[1]
        self._move(inp)
        d_after = self.pos[1]
        surface_depth = self.t["surface_depth"]

        if d_before <= surface_depth and d_after > surface_depth:
            events.append(("dive", {"pos": [self.pos[0], self.pos[1]]}))
        elif d_before > surface_depth and d_after <= surface_depth:
            events.append(("surface", {"pos": [self.pos[0], self.pos[1]]}))

        if self._at_surface():
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
        else:
            if self.oxygen_ticks > 0:
                self.oxygen_ticks -= 1
                if self.oxygen_ticks == 0:
                    events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
                    self.zero_oxy_ticks = 0
                    self.hp -= 1
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp <= 0:
                        self.hp = 0
                        lost = list(reversed(self.hold))
                        self.hold.clear()
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events

        # 3. quái Cá Sấu: cập nhật quái theo id rồi xét tối đa một hit
        self._update_monsters()
        if self._check_monster_hit(events):
            return events

        # 4. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            elif self._at_surface():
                ir = self.t["interact_radius"]
                candidates = []
                for n in self.nodes:
                    if n["regrow_ticks"] == 0:
                        dist = math.dist(self.pos, n["pos"])
                        if dist <= ir:
                            candidates.append((dist, id_key(n["id"]), n))
                if candidates:
                    candidates.sort(key=lambda c: (c[0], c[1]))
                    target = candidates[0][2]
                    free = self.t["hold_capacity"] - len(self.hold)
                    req = self.t["node_yield"]
                    if free < req:
                        events.append(("hold_full", {"action": "gather", "node_id": target["id"], "required": req, "free": free}))
                    else:
                        for _ in range(req):
                            self.hold.append(target["kind"])
                        target["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {"node_id": target["id"], "kind": target["kind"], "amount": req}))

        # 5. bắt cá theo vị trí cá TRƯỚC KHI BƠI
        if inp.pressed("catch"):
            if self.catch_cd_ticks == 0 and not self._at_surface():
                cr = self.t["catch_radius"]
                candidates = []
                for f in self.fish:
                    dist = math.dist(self.pos, f["pos"])
                    if dist <= cr:
                        candidates.append((dist, id_key(f["id"]), f))
                if candidates:
                    candidates.sort(key=lambda c: (c[0], c[1]))
                    target = candidates[0][2]
                    y = self.t["fish_yield"][target["kind"]]
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free < y:
                        events.append(("hold_full", {"action": "catch", "fish_id": target["id"], "required": y, "free": free}))
                    else:
                        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                        for _ in range(y):
                            self.hold.append(target["kind"])
                        self.fish.remove(target)
                        events.append(("fish_caught", {"fish_id": target["id"], "kind": target["kind"], "yield": y}))

        # 6. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events

        # 7. cá bơi và sinh thêm theo lịch (nếu còn giờ)
        if self.random_fish:
            self._move_fish()
            self._spawn_periodic_fish(events)

        return events

    # --- di chuyển và va chạm quái ----------------------------------------------
    def _update_monsters(self):
        px, pd = self.pos
        player_in_monster_depth = (pd >= 10.0)

        for m in sort_by_id(self.monsters):
            state = m["state"]

            if state == "recoil":
                # Lùi theo hướng recoil_dir ở tốc độ 2.0 m/s (2/60 m/tick)
                rd = m["recoil_dir"]
                if rd:
                    m["pos"][0] += rd[0] * (2.0 / TICK)
                    m["pos"][1] += rd[1] * (2.0 / TICK)
                    m["pos"][0] = max(0.0, min(100.0, m["pos"][0]))
                    m["pos"][1] = max(10.0, min(30.0, m["pos"][1]))
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"] = "patrol"
                    m["recoil_dir"] = None
                    m["state_ticks_left"] = 0

            elif state == "patrol":
                dist_p = math.dist(m["pos"], self.pos)
                if player_in_monster_depth and dist_p <= 10.0:
                    m["state"] = "chase"
                    self._monster_chase_step(m)
                else:
                    # Đi 1.0 m/s tới waypoint
                    wp = m["waypoints"][m["target_idx"]]
                    dx = wp[0] - m["pos"][0]
                    dd = wp[1] - m["pos"][1]
                    d_wp = math.hypot(dx, dd)
                    step = 1.0 / TICK
                    if d_wp <= step:
                        m["pos"] = [float(wp[0]), float(wp[1])]
                        m["target_idx"] = 1 - m["target_idx"]
                    else:
                        m["pos"][0] += (dx / d_wp) * step
                        m["pos"][1] += (dd / d_wp) * step
                    m["pos"][0] = max(0.0, min(100.0, m["pos"][0]))
                    m["pos"][1] = max(10.0, min(30.0, m["pos"][1]))

            elif state == "chase":
                dist_p = math.dist(m["pos"], self.pos)
                if dist_p > 16.0 or not player_in_monster_depth:
                    m["state"] = "patrol"
                    wp = m["waypoints"][m["target_idx"]]
                    dx = wp[0] - m["pos"][0]
                    dd = wp[1] - m["pos"][1]
                    d_wp = math.hypot(dx, dd)
                    step = 1.0 / TICK
                    if d_wp <= step:
                        m["pos"] = [float(wp[0]), float(wp[1])]
                        m["target_idx"] = 1 - m["target_idx"]
                    else:
                        m["pos"][0] += (dx / d_wp) * step
                        m["pos"][1] += (dd / d_wp) * step
                    m["pos"][0] = max(0.0, min(100.0, m["pos"][0]))
                    m["pos"][1] = max(10.0, min(30.0, m["pos"][1]))
                else:
                    self._monster_chase_step(m)

    def _monster_chase_step(self, m):
        dx = self.pos[0] - m["pos"][0]
        dd = self.pos[1] - m["pos"][1]
        dist = math.hypot(dx, dd)
        step = 3.0 / TICK
        if dist <= step:
            m["pos"] = [self.pos[0], self.pos[1]]
        else:
            m["pos"][0] += (dx / dist) * step
            m["pos"][1] += (dd / dist) * step
        m["pos"][0] = max(0.0, min(100.0, m["pos"][0]))
        m["pos"][1] = max(10.0, min(30.0, m["pos"][1]))

    def _check_monster_hit(self, events) -> bool:
        if self.invuln_ticks > 0 or self.pos[1] < 10.0:
            return False

        candidates = []
        for m in self.monsters:
            if m["state"] != "recoil":
                dist = math.dist(self.pos, m["pos"])
                if dist <= 1.5:
                    candidates.append((dist, id_key(m["id"]), m))

        if not candidates:
            return False

        candidates.sort(key=lambda c: (c[0], c[1]))
        attacker = candidates[0][2]

        # 1. Trừ máu
        self.hp -= 1

        # 2. Rơi floor(len(hold) / 2) nguyên liệu theo LIFO
        drop_count = len(self.hold) // 2
        lost = []
        for _ in range(drop_count):
            lost.append(self.hold.pop())

        # 3. Đặt bất tử 90 tick
        self.invuln_ticks = 90

        # 4. Quái gây hit vào recoil 60 bước, lùi xa người chơi (trùng tâm dùng +x)
        dx = attacker["pos"][0] - self.pos[0]
        dd = attacker["pos"][1] - self.pos[1]
        dist = math.hypot(dx, dd)
        if dist == 0:
            recoil_dir = [1.0, 0.0]
        else:
            recoil_dir = [dx / dist, dd / dist]
        attacker["state"] = "recoil"
        attacker["state_ticks_left"] = 60
        attacker["recoil_dir"] = recoil_dir

        events.append(("monster_hit", {
            "monster_id": attacker["id"], "hp": self.hp, "lost": lost,
            "pos": [self.pos[0], self.pos[1]]
        }))

        if self.hp <= 0:
            self.hp = 0
            remaining_lost = list(reversed(self.hold))
            self.hold.clear()
            events.append(("faint", {"cause": "monster", "lost": remaining_lost, "hp": 0}))
            self._finish("fainted", events)
            return True

        return False

    # --- cá bơi và sinh cá theo lịch --------------------------------------------
    def _move_fish(self):
        speed = self.t.get("fish_speed", 1.5)
        step = speed / TICK
        turn_interval = self.t.get("fish_turn_ticks", 120)
        x_bounds = self.t.get("fish_x", [4, 96])
        depths_map = self.t.get("fish_depths", {
            "ca_linh": [3, 12], "ca_loc": [8, 20], "ca_keo": [22, 28]
        })

        for f in sort_by_id(self.fish):
            f["age_ticks"] = f.get("age_ticks", 0) + 1
            if f["age_ticks"] % turn_interval == 0:
                f["heading_deg"] = self.rng.get("fish_turn").uniform(0.0, 360.0)

            rad = math.radians(f["heading_deg"])
            vx = step * math.cos(rad)
            vd = step * math.sin(rad)

            x = f["pos"][0] + vx
            d = f["pos"][1] + vd

            x_lo, x_hi = x_bounds
            d_lo, d_hi = depths_map.get(f["kind"], [0, 30])

            hit_x = False
            if x < x_lo:
                x = 2 * x_lo - x
                vx = -vx
                hit_x = True
            elif x > x_hi:
                x = 2 * x_hi - x
                vx = -vx
                hit_x = True

            hit_d = False
            if d < d_lo:
                d = 2 * d_lo - d
                vd = -vd
                hit_d = True
            elif d > d_hi:
                d = 2 * d_hi - d
                vd = -vd
                hit_d = True

            if hit_x or hit_d:
                f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360

            f["pos"] = [max(float(x_lo), min(float(x_hi), x)), max(float(d_lo), min(float(d_hi), d))]

    def _spawn_periodic_fish(self, events):
        spawn_ticks = self.t.get("fish_spawn_ticks", 360)
        if self.phase_tick <= 0 or self.phase_tick % spawn_ticks != 0:
            return

        if len(self.fish) >= self.t.get("fish_max", 12):
            return

        spawn_x = self.t.get("fish_spawn_x", [15, 30, 45, 60, 75, 90])
        spawn_depths = self.t.get("fish_spawn_depths", {
            "ca_linh": [5, 10], "ca_loc": [10, 16], "ca_keo": [24, 27]
        })
        weights = self.t.get("fish_weights", {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3})
        clearance = self.t.get("fish_spawn_clearance", 1.0)

        valid_points = {}
        for s in SPECIES_LIST:
            pts = []
            for x in spawn_x:
                for d in spawn_depths.get(s, []):
                    pt = [float(x), float(d)]
                    if all(math.dist(pt, f["pos"]) > clearance for f in self.fish):
                        pts.append(pt)
            valid_points[s] = pts

        avail = [s for s in SPECIES_LIST if valid_points[s]]
        if not avail:
            return

        tot = sum(weights[s] for s in avail)
        r = self.rng.get("fish_spawn").random() * tot
        accum = 0.0
        chosen_s = avail[-1]
        for s in avail:
            accum += weights[s]
            if r < accum:
                chosen_s = s
                break

        pts = sorted(valid_points[chosen_s])
        chosen_pt = pts[self.rng.get("fish_spawn").randrange(len(pts))]
        heading = self.rng.get("fish_spawn").uniform(0.0, 360.0)
        fid = self.ids.new("F")
        new_fish = {
            "id": fid, "kind": chosen_s, "pos": [float(chosen_pt[0]), float(chosen_pt[1])],
            "heading_deg": heading, "age_ticks": 0
        }
        self.fish.append(new_fish)
        events.append(("fish_spawned", {"id": fid, "kind": chosen_s, "pos": [float(chosen_pt[0]), float(chosen_pt[1])]}))

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
