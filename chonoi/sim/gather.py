"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD mục 13.8, "Gather"):
  ĐÃ LÀM (lát 1, haidoan2426): bơi + oxy + biên + ngạt/ngất
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint (test: tests/test_gather_sinh_ton.py)
  TODO(nhóm, lát 1 còn lại): giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  TODO(nhóm, lát 2): hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..ids import sort_by_id
from ..inventory import hold_to_items
from .monsters import init_monsters, monster_snapshot, step_monsters, upgrade_limit
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, active_upgrades=None):
        t = tuning["gather"]
        self.t = t
        self.tick_hz = tuning["tick_hz"]
        self.day = day
        self.active_upgrades = dict(active_upgrades or {})
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        oxygen_s = upgrade_limit(tuning, "oxygen", self.active_upgrades.get("oxygen", 0),
                                 "oxygen_max_s", t["oxygen_max_s"])
        self.oxygen_max = int(round(oxygen_s * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp_max = upgrade_limit(tuning, "hp", self.active_upgrades.get("hp", 0),
                                    "hp_max", t["hp_max"])
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif scenario.get("random_fish", True):
            src_fish = t["fish_initial"]
        else:
            src_fish = []
        self.fish_spawn_ticks = 0
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0), "move_ticks": 0} for f in src_fish]
        self.monsters = init_monsters(t, scenario, day=day)
        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])
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
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
                     for f in sort_by_id(self.fish)],
            "monsters": monster_snapshot(self.monsters),
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 2. bơi + chặn mép + sinh tồn
        was_at_surface = self._at_surface()
        self._move(inp)
        at_surface = self._at_surface()
        if was_at_surface and not at_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_at_surface and at_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        oxygen_before = self.oxygen_ticks
        if at_surface:
            self.oxygen_ticks = min(
                self.oxygen_max,
                self.oxygen_ticks + int(self.t["oxygen_refill_per_tick"]),
            )
            self.zero_oxy_ticks = 0
        else:
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if oxygen_before > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"pos": list(self.pos)}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                choke_interval = int(self.t["choke_interval_ticks"])
                if self.zero_oxy_ticks >= choke_interval:
                    self.zero_oxy_ticks = 0
                    self.hp = max(0, self.hp - 1)
                    events.append(("choke", {"hp": self.hp, "pos": list(self.pos)}))
                    if self.hp == 0:
                        events.append(("faint", {
                            "cause": "choke", "lost": list(reversed(self.hold)), "hp": self.hp,
                        }))
                        self.hold.clear()
                        self._finish("fainted", events)
                        return events
        self.hp, self.invuln_ticks, monster_events, fainted = step_monsters(
            self.monsters, self.t, self.pos, self.hp, self.invuln_ticks,
            self.hold, tick_hz=self.tick_hz)
        events.extend(monster_events)
        if fainted:
            self._finish("fainted", events)
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            # hái nút `ready` gần nhất trong interact_radius, chỉ khi ở mặt nước
            if self._at_surface():
                candidates = [n for n in sort_by_id(self.nodes)
                              if n["regrow_ticks"] == 0
                              and math.dist(self.pos, n["pos"]) <= self.t["interact_radius"]]
                if candidates:
                    node = min(candidates, key=lambda n: math.dist(self.pos, n["pos"]))
                    amount = int(self.t["node_yield"])
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free < amount:
                        events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                                     "required": amount, "free": free}))
                    else:
                        self.hold.extend([node["kind"]] * amount)
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {"node_id": node["id"], "kind": node["kind"],
                                                  "amount": amount}))
        # 4. bắt cá
        if inp.pressed("catch"):
            # bắt đàn gần nhất trong catch_radius, chỉ khi hết hồi chiêu và dưới nước
            if self.catch_cd_ticks == 0 and not self._at_surface():
                candidates = [f for f in sort_by_id(self.fish)
                              if math.dist(self.pos, f["pos"]) <= self.t["catch_radius"]]
                if candidates:
                    fish = min(candidates, key=lambda f: math.dist(self.pos, f["pos"]))
                    amount = int(self.t["fish_yield"][fish["kind"]])
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free < amount:
                        events.append(("hold_full", {"action": "catch", "fish_id": fish["id"],
                                                     "required": amount, "free": free}))
                    else:
                        self.hold.extend([fish["kind"]] * amount)
                        self.fish.remove(fish)
                        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"],
                                                       "yield": amount}))
        # 5. hết giờ trước khi cá thường bơi và sinh đàn
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        # 6. cá bơi và sinh đàn mới (sau khi người chơi đã bắt theo vị trí trước khi cá bơi)
        self._move_fish()
        self.fish_spawn_ticks += 1
        if self.fish_spawn_ticks >= int(self.t["fish_spawn_ticks"]):
            self.fish_spawn_ticks = 0
            self._spawn_fish()
        return events

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

    def _move_fish(self):
        speed = float(self.t["fish_speed"])
        turn_ticks = int(self.t["fish_turn_ticks"])
        rng = self.rng.get("fish_swim")
        bounds = self.t["bounds"]
        for fish in sort_by_id(self.fish):
            fish["move_ticks"] += 1
            if fish["move_ticks"] >= turn_ticks:
                fish["move_ticks"] = 0
                fish["heading_deg"] = rng.random() * 360.0
            angle = math.radians(fish["heading_deg"])
            fish["pos"][0] += math.cos(angle) * speed / TICK
            fish["pos"][1] += math.sin(angle) * speed / TICK
            if fish["pos"][0] <= bounds["x"][0] or fish["pos"][0] >= bounds["x"][1]:
                fish["pos"][0] = min(bounds["x"][1], max(bounds["x"][0], fish["pos"][0]))
                fish["heading_deg"] = (180.0 - fish["heading_deg"]) % 360.0
            if fish["pos"][1] <= self.t["surface_depth"] or fish["pos"][1] >= bounds["d"][1]:
                fish["pos"][1] = min(bounds["d"][1], max(self.t["surface_depth"] + 1e-9, fish["pos"][1]))
                fish["heading_deg"] = (-fish["heading_deg"]) % 360.0

    def _spawn_fish(self):
        if len(self.fish) >= int(self.t["fish_max"]):
            return
        rng = self.rng.get("fish_spawn")
        b = self.t["bounds"]
        roll = rng.random()
        weights = self.t["fish_spawn_weights"]
        if roll < weights["ca_linh"]:
            kind = "ca_linh"
        elif roll < weights["ca_linh"] + weights["ca_loc"]:
            kind = "ca_loc"
        else:
            kind = "ca_keo"
        pos = [b["x"][0] + rng.random() * (b["x"][1] - b["x"][0]),
               self.t["surface_depth"] + 0.1 + rng.random() * (b["d"][1] - self.t["surface_depth"] - 0.1)]
        self.fish.append({"id": self.ids.new("F"), "kind": kind, "pos": pos,
                          "heading_deg": rng.random() * 360.0, "move_ticks": 0})
