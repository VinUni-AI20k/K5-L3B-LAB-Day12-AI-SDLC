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
from fractions import Fraction

from ..ids import sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


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
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.freshness = tuning.get("freshness")
        self.hold = [dict(item) for item in scenario.get("hold", [])] if self.freshness else list(scenario.get("hold", []))
        self._fresh_values = {}
        if self.freshness:
            for item in self.hold:
                ids.reserve(item["id"])
                self._fresh_values[item["id"]] = Fraction(str(item["fresh"]))
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        self.random_fish = scenario.get("random_fish", True)
        self.phase_tick = 0
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif self.random_fish and isinstance(t["fish_initial"], list):
            src_fish = t["fish_initial"]
        else:
            src_fish = []
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0), "age_ticks": f.get("age_ticks", 0)} for f in src_fish]
        self.monsters = []
        config = t.get("monsters")
        if config:
            source = scenario.get("monsters", [m for m in config["spawns"] if m["from_day"] <= 1])
            for m in source:
                self.monsters.append({"id": m["id"], "kind": m["kind"], "pos": list(m["pos"]),
                    "waypoints": [list(p) for p in m["waypoints"]], "target_idx": m.get("target_idx", 1),
                    "state": m.get("state", "patrol"), "state_ticks_left": m.get("state_ticks_left", 0),
                    "recoil_dir": m.get("recoil_dir")})
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        if self.random_fish and "fish" not in scenario and isinstance(t["fish_initial"], int):
            for _ in range(t["fish_initial"]):
                self._spawn_fish(initial=True)
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self):
        if self.freshness:
            return [dict(item) for item in sort_by_id(self.hold)]
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
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [{k: m[k] for k in ("id", "kind", "pos", "state", "target_idx", "state_ticks_left", "recoil_dir")} for m in sort_by_id(self.monsters)],
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
        if self.freshness:
            self._decay_hold(events)
        # 2. bơi + chặn mép
        was_surface = self._at_surface()
        self._move(inp)
        surface = self._at_surface()
        if surface != was_surface:
            events.append(("surface" if surface else "dive", {"pos": list(self.pos)}))
        if surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
        else:
            previous_oxygen = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if previous_oxygen > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
                    self.zero_oxy_ticks = 0
                    self.hp -= 1
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp == 0:
                        lost = list(reversed(self.hold))
                        self.hold.clear()
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events
            else:
                self.zero_oxy_ticks = 0
        self._move_monsters(events)
        if self.done:
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if surface:
                node = self._nearest([n for n in self.nodes if n["regrow_ticks"] == 0], self.t["interact_radius"])
                if node is not None:
                    amount = self.t["node_yield"]
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free < amount:
                        events.append(("hold_full", {"action": "gather", "node_id": node["id"], "required": amount, "free": free}))
                    else:
                        self._add_to_hold(node["kind"], amount)
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": amount}))
        # 4. bắt cá
        if inp.pressed("catch") and not surface and self.catch_cd_ticks == 0:
            fish = self._nearest(self.fish, self.t["catch_radius"])
            if fish is not None:
                amount = self.t["fish_yield"][fish["kind"]]
                free = self.t["hold_capacity"] - len(self.hold)
                if free < amount:
                    events.append(("hold_full", {"action": "catch", "fish_id": fish["id"], "required": amount, "free": free}))
                else:
                    self._add_to_hold(fish["kind"], amount)
                    self.fish.remove(fish)
                    self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                    events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": amount}))
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        elif self.random_fish and "fish_speed" in self.t:
            self._move_fish()
            if self.phase_tick % self.t["fish_spawn_ticks"] == 0 and len(self.fish) < self.t["fish_max"]:
                fish = self._spawn_fish()
                if fish:
                    events.append(("fish_spawned", {k: fish[k] for k in ("id", "kind", "pos")}))
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _add_to_hold(self, kind, amount):
        for _ in range(amount):
            if self.freshness:
                item = {"id": self.ids.new("I"), "kind": kind, "fresh": self.freshness["initial"]}
                self._fresh_values[item["id"]] = Fraction(str(item["fresh"]))
                self.hold.append(item)
            else:
                self.hold.append(kind)

    def _decay_hold(self, events):
        decay = Fraction(str(self.freshness["gather_decay_per_s"])) / Fraction(str(TICK))
        threshold = Fraction(str(self.freshness["spoiled_below"]))
        for item in sort_by_id(self.hold):
            previous = self._fresh_values[item["id"]]
            current = max(Fraction(0), previous - decay)
            self._fresh_values[item["id"]] = current
            item["fresh"] = float(current)
            if previous >= threshold > current:
                events.append(("spoiled", {"item_id": item["id"], "kind": item["kind"], "location": "hold"}))

    def _spawn_fish(self, initial=False):
        t = self.t
        choices = {}
        for kind in sorted(t["fish_weights"]):
            choices[kind] = [[x, d] for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]
                             if all(math.dist([x, d], f["pos"]) > (0 if initial else t["fish_spawn_clearance"]) for f in self.fish)]
        kinds = [k for k in choices if choices[k]]
        if not kinds:
            return None
        rng = self.rng.get("fish_spawn")
        kind = rng.choices(kinds, weights=[t["fish_weights"][k] for k in kinds])[0]
        fish = {"id": self.ids.new("F"), "kind": kind, "pos": list(rng.choice(choices[kind])),
                "heading_deg": rng.uniform(0, 360), "age_ticks": 0}
        self.fish.append(fish)
        return fish

    def _move_fish(self):
        t = self.t
        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if f["age_ticks"] % t["fish_turn_ticks"] == 0:
                f["heading_deg"] = self.rng.get("fish_turn").uniform(0, 360)
            angle = math.radians(f["heading_deg"])
            velocity = [math.cos(angle), math.sin(angle)]
            for i, (lo, hi) in enumerate((t["fish_x"], t["fish_depths"][f["kind"]])):
                value = f["pos"][i] + velocity[i] * t["fish_speed"] / TICK
                while value <= lo or value >= hi:
                    if value <= lo:
                        value = 2 * lo - value
                    else:
                        value = 2 * hi - value
                    velocity[i] = -velocity[i]
                    if lo < value < hi:
                        break
                    if value == lo or value == hi:
                        break
                f["pos"][i] = value
            f["heading_deg"] = math.degrees(math.atan2(velocity[1], velocity[0])) % 360

    def _move_monsters(self, events):
        if not self.monsters:
            return
        cfg = self.t["monsters"]
        eligible = []
        for m in sort_by_id(self.monsters):
            spec = cfg["species"][m["kind"]]
            if m["state"] == "recoil":
                direction = m["recoil_dir"] or [1, 0]
                m["pos"] = [m["pos"][i] + direction[i] * spec["recoil_dist"] for i in range(2)]
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] == 0:
                    m["state"] = "patrol"
                active = False
            else:
                distance = math.dist(m["pos"], self.pos)
                if m["state"] == "chase" and (distance > spec["exit_radius"] or self.pos[1] < spec["depths"][0]):
                    m["state"] = "patrol"
                elif m["state"] == "patrol" and self.pos[1] >= spec["depths"][0] and distance <= spec["detect_radius"]:
                    m["state"] = "chase"
                target = self.pos if m["state"] == "chase" else m["waypoints"][m["target_idx"]]
                distance = math.dist(m["pos"], target)
                speed = spec["chase_speed"] if m["state"] == "chase" else spec["patrol_speed"]
                if distance:
                    amount = min(distance, speed / TICK)
                    m["pos"] = [m["pos"][i] + (target[i] - m["pos"][i]) * amount / distance for i in range(2)]
                if m["state"] == "patrol" and distance <= speed / TICK:
                    m["target_idx"] = 1 - m["target_idx"]
                active = True
            for i, bounds in enumerate((self.t["bounds"]["x"], spec["depths"])):
                m["pos"][i] = max(bounds[0], min(bounds[1], m["pos"][i]))
            if active and self.pos[1] >= spec["depths"][0] and math.dist(m["pos"], self.pos) <= spec["hit_radius"]:
                eligible.append(m)
        if eligible and self.invuln_ticks == 0:
            m = min(eligible, key=lambda x: math.dist(x["pos"], self.pos))
            spec = cfg["species"][m["kind"]]
            self.hp -= 1
            lost = [self.hold.pop() for _ in range(math.floor(len(self.hold) * cfg["loss_ratio"]))]
            self.invuln_ticks = cfg["invuln_ticks"]
            events.append(("monster_hit", {"monster_id": m["id"], "hp": self.hp, "lost": lost, "pos": list(self.pos)}))
            delta = [m["pos"][i] - self.pos[i] for i in range(2)]
            length = math.hypot(*delta)
            m["recoil_dir"] = [v / length for v in delta] if length else [1, 0]
            m["state"] = "recoil"
            m["state_ticks_left"] = spec["recoil_ticks"]
            if self.hp == 0:
                lost = list(reversed(self.hold))
                self.hold.clear()
                events.append(("faint", {"cause": "monster", "lost": lost, "hp": 0}))
                self._finish("fainted", events)

    def _nearest(self, entities, radius):
        candidates = [e for e in sort_by_id(entities) if math.dist(self.pos, e["pos"]) <= radius]
        return min(candidates, key=lambda e: math.dist(self.pos, e["pos"])) if candidates else None

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
