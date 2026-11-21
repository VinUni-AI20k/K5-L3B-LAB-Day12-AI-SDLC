"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD mục 13.8, "Gather"):
  TODO(nhóm, lát 1): bơi + oxy + biên + giỏ
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  TODO(nhóm, lát 2): hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..ids import sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.random_fish = scenario.get("random_fish", True)
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = 0  # Chỉ tăng khi mô phỏng buổi sáng thực sự chạy một bước.
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        for node in self.nodes:
            ids.reserve(node["id"])
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif self.random_fish:
            src_fish = self._create_initial_fish()
        else:
            src_fish = []
        # Đàn cá đứng yên ở phase này. Cá bơi / sinh thêm là việc của phase sau.
        # Phase 2: cá bơi khi random_fish bật; fixture đứng yên khi cờ tắt.
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0), "age_ticks": f.get("age_ticks", 0)}
                     for f in src_fish]
        for fish in self.fish:
            ids.reserve(fish["id"])
        self.monster_config = t["monsters"]
        # Gather độc lập mặc định Ngày 1; vòng ngày truyền ngày hiện tại.
        initial_monsters = scenario.get("monsters")
        if initial_monsters is None:
            initial_monsters = [m for m in self.monster_config["spawns"] if m["from_day"] <= day]
        self.monsters = [{"id": m["id"], "kind": m["kind"], "pos": list(map(float, m["pos"])),
                          "waypoints": [list(map(float, p)) for p in m["waypoints"]],
                          "target_idx": m.get("target_idx", 1), "state": m.get("state", "patrol"),
                          "state_ticks_left": m.get("state_ticks_left", 0),
                          "recoil_dir": m.get("recoil_dir")} for m in initial_monsters]
        for monster in self.monsters:
            ids.reserve(monster["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    def _create_initial_fish(self):
        """Chọn điểm hình học khác nhau, rồi chọn loài phù hợp theo seed."""
        rng = self.rng.get("fish_initial")
        choices = {}
        for kind, depths in sorted(self.t["fish_spawn_depths"].items()):
            for x in sorted(self.t["fish_spawn_x"]):
                for depth in sorted(depths):
                    choices.setdefault((x, depth), []).append(kind)
        positions = sorted(choices)
        selected = rng.sample(positions, self.t["fish_initial"])
        return [{"id": self.ids.new("F"), "kind": rng.choice(choices[pos]),
                 "pos": list(pos), "heading_deg": rng.uniform(0, 360), "age_ticks": 0}
                for pos in selected]

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"],
                      "heading_deg": f["heading_deg"], "age_ticks": f["age_ticks"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [dict(m) for m in sort_by_id(self.monsters)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        self.phase_tick += 1
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 2. bơi + chặn mép
        was_at_surface = self._at_surface()
        self._move(inp)
        is_at_surface = self._at_surface()

        # Phát sự kiện khi đi qua ranh giới mặt nước
        if was_at_surface and not is_at_surface:
            events.append(("dive", {"pos": self.pos.copy()}))
        elif not was_at_surface and is_at_surface:
            events.append(("surface", {"pos": self.pos.copy()}))

        # Oxy được tính theo độ sâu CUỐI bước
        old_oxygen = self.oxygen_ticks

        if is_at_surface:
            self.oxygen_ticks = min(
                self.oxygen_max,
                self.oxygen_ticks + self.t["oxygen_refill_per_tick"]
            )
            self.zero_oxy_ticks = 0
        else:
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)

            if old_oxygen > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))

            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1

                choke_interval = getattr(
                    self,
                    "live_choke_interval_ticks",
                    self.t["choke_interval_ticks"]
                )

                if self.zero_oxy_ticks >= choke_interval:
                    self.zero_oxy_ticks = 0
                    self.hp -= 1
                    events.append(("choke", {"hp": self.hp}))

                    if self.hp == 0:
                        lost = list(reversed(self.hold))
                        self.hold.clear()

                        events.append(("faint", {
                            "cause": "choke",
                            "lost": lost,
                            "hp": 0
                        }))
                        self._finish("fainted", events)
                        return events

        # TODO(nhóm, lát 1): so phân vùng đầu/cuối bước -> dive / surface (data: pos).
        # TODO(nhóm, lát 1): oxy theo d CUỐI bước (mặt nước hồi, dưới nước trừ), oxygen_empty khi từ dương
        #   xuống 0, đếm ngạt, choke (-1 Máu). Máu 0 -> faint + gather_end("fainted") với giỏ rỗng, return.
        self._update_monsters(events)
        if self.done:
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            # TODO(nhóm, lát 2): chỉ khi ở mặt nước: hái nút `ready` gần nhất trong interact_radius
            #   (id nhỏ khi bằng nhau): gather / hold_full; đặt regrow_ticks cho nút.
            if self._at_surface():
                candidates = [n for n in sort_by_id(self.nodes)
                              if n["regrow_ticks"] == 0
                              and math.dist(self.pos, n["pos"]) <= self.t["interact_radius"]]
                if candidates:
                    node = min(candidates, key=lambda n: math.dist(self.pos, n["pos"]))
                    amount = self.t["node_yield"]
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free >= amount:
                        self.hold.extend([node["kind"]] * amount)
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {"node_id": node["id"],
                                                  "kind": node["kind"], "amount": amount}))
                    else:
                        events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                                     "required": amount, "free": free}))
        # 4. bắt cá
        if inp.pressed("catch"):
            pass  # TODO(nhóm, lát 2): chỉ khi catch_cd_ticks == 0 và dưới nước: fish_caught / hold_full.
            if self.catch_cd_ticks == 0 and not self._at_surface():
                candidates = [f for f in sort_by_id(self.fish)
                              if math.dist(self.pos, f["pos"]) <= self.t["catch_radius"]]
                if candidates:
                    fish = min(candidates, key=lambda f: math.dist(self.pos, f["pos"]))
                    amount = self.t["fish_yield"][fish["kind"]]
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free >= amount:
                        self.hold.extend([fish["kind"]] * amount)
                        self.fish.remove(fish)
                        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                        events.append(("fish_caught", {"fish_id": fish["id"],
                                                       "kind": fish["kind"], "yield": amount}))
                    else:
                        events.append(("hold_full", {"action": "catch", "fish_id": fish["id"],
                                                     "required": amount, "free": free}))
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        elif self.random_fish:
            self._move_fish()
            if self.phase_tick % self.t["fish_spawn_ticks"] == 0:
                self._spawn_fish(events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _update_monsters(self, events):
        """Di chuyển theo trạng thái, rồi xét tối đa một va chạm ở cuối bước."""
        hittable = []
        for monster in sort_by_id(self.monsters):
            spec = self.monster_config["species"][monster["kind"]]
            if monster["state"] == "recoil":
                direction = monster["recoil_dir"]
                self._move_monster(monster, direction, spec["recoil_dist"] / TICK, spec)
                monster["state_ticks_left"] -= 1
                if monster["state_ticks_left"] == 0:
                    monster["state"] = "patrol"
                    monster["recoil_dir"] = None
                continue
            distance = math.dist(monster["pos"], self.pos)
            can_detect = self.pos[1] >= spec["depths"][0]
            if monster["state"] == "chase":
                if not can_detect or distance > spec["exit_radius"]:
                    monster["state"] = "patrol"
            elif can_detect and distance <= spec["detect_radius"]:
                monster["state"] = "chase"
            target = self.pos if monster["state"] == "chase" else monster["waypoints"][monster["target_idx"]]
            speed = spec["chase_speed"] if monster["state"] == "chase" else spec["patrol_speed"]
            dx, dd = target[0] - monster["pos"][0], target[1] - monster["pos"][1]
            length = math.hypot(dx, dd)
            if length:
                self._move_monster(monster, [dx / length, dd / length], min(length, speed / TICK), spec)
            if monster["state"] == "patrol" and length <= speed / TICK:
                monster["target_idx"] = 1 - monster["target_idx"]
            if can_detect and math.dist(monster["pos"], self.pos) <= spec["hit_radius"]:
                hittable.append(monster)
        if not hittable or self.invuln_ticks > 0:
            return
        monster = min(hittable, key=lambda m: math.dist(m["pos"], self.pos))
        spec = self.monster_config["species"][monster["kind"]]
        lost = [self.hold.pop() for _ in range(math.floor(len(self.hold) * self.monster_config["loss_ratio"]))]
        self.hp -= 1
        self.invuln_ticks = self.monster_config["invuln_ticks"]
        dx, dd = monster["pos"][0] - self.pos[0], monster["pos"][1] - self.pos[1]
        length = math.hypot(dx, dd)
        monster["recoil_dir"] = [dx / length, dd / length] if length else [1.0, 0.0]
        monster["state"] = "recoil"
        monster["state_ticks_left"] = spec["recoil_ticks"]
        events.append(("monster_hit", {"monster_id": monster["id"], "hp": self.hp,
                                       "lost": lost, "pos": self.pos.copy()}))
        if self.hp == 0:
            remaining = list(reversed(self.hold))
            self.hold.clear()
            events.append(("faint", {"cause": "monster", "lost": remaining, "hp": 0}))
            self._finish("fainted", events)

    def _move_monster(self, monster, direction, distance, spec):
        for axis, (lo, hi) in enumerate((self.t["bounds"]["x"], spec["depths"])):
            monster["pos"][axis] = min(hi, max(lo, monster["pos"][axis] + direction[axis] * distance))

    def _spawn_fish(self, events):
        """Sinh tối đa một đàn tại điểm trống, sau khi các đàn đang sống đã bơi."""
        if len(self.fish) >= self.t["fish_max"]:
            return
        eligible = {}
        for kind, depths in sorted(self.t["fish_spawn_depths"].items()):
            points = [(x, depth) for x in sorted(self.t["fish_spawn_x"])
                      for depth in sorted(depths)]
            eligible[kind] = [point for point in points
                              if all(math.dist(point, fish["pos"]) > self.t["fish_spawn_clearance"]
                                     for fish in self.fish)]
        kinds = [kind for kind in sorted(eligible) if eligible[kind]]
        if not kinds:
            return
        rng = self.rng.get("fish_spawn")
        kind = rng.choices(kinds, weights=[self.t["fish_weights"][k] for k in kinds], k=1)[0]
        pos = list(rng.choice(eligible[kind]))
        fish = {"id": self.ids.new("F"), "kind": kind, "pos": pos,
                "heading_deg": rng.uniform(0, 360), "age_ticks": 0}
        self.fish.append(fish)
        events.append(("fish_spawned", {"id": fish["id"], "kind": kind, "pos": pos[:]}))

    def _move_fish(self):
        """Cá đổi hướng trước khi bơi và phản xạ quãng đường dư tại biên."""
        for fish in sort_by_id(self.fish):
            fish["age_ticks"] += 1
            if fish["age_ticks"] % self.t["fish_turn_ticks"] == 0:
                fish["heading_deg"] = self.rng.get("fish_turn").uniform(0, 360)
            angle = math.radians(fish["heading_deg"])
            delta = [math.cos(angle) * self.t["fish_speed"] / TICK,
                     math.sin(angle) * self.t["fish_speed"] / TICK]
            bounds = (self.t["fish_x"], self.t["fish_depths"][fish["kind"]])
            for axis, (lo, hi) in enumerate(bounds):
                pos = fish["pos"][axis] + delta[axis]
                while pos < lo or pos > hi:
                    if pos < lo:
                        pos = 2 * lo - pos
                    else:
                        pos = 2 * hi - pos
                    delta[axis] = -delta[axis]
                if (pos == lo and delta[axis] < 0) or (pos == hi and delta[axis] > 0):
                    delta[axis] = -delta[axis]
                fish["pos"][axis] = pos
            fish["heading_deg"] = math.degrees(math.atan2(delta[1], delta[0])) % 360

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

        # STAMINA LIVE ONLY: active only if LiveGame enabled it.
        if getattr(self, "_live_stamina_enabled", False):
            stamina = self._live_stamina
            moving = mx != 0 or md != 0
            sprint_held = inp.held.get("sprint", False)
            exhausted = self._live_stamina_exhausted

            # Prevent auto sprint/recovery oscillation at zero.
            if stamina <= 0:
                exhausted = True
            if exhausted and stamina >= 20:
                exhausted = False

            sprinting = bool(moving and sprint_held and not exhausted and stamina > 0)
            if sprinting:
                speed *= 1.5  # 4 m/s -> 6 m/s in Live with default tuning
                stamina = max(0.0, stamina - 20.0 / TICK)
                if stamina == 0:
                    exhausted = True
            else:
                stamina = min(100.0, stamina + 12.0 / TICK)

            self._live_stamina = stamina
            self._live_stamina_exhausted = exhausted
            self._live_sprinting = sprinting
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
