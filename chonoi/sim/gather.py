"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã có: bơi + tăng/giảm tốc, chặn mép (d không âm), oxy, ngạt, ngất và bỏ giỏ theo LIFO,
đồng hồ và hết giờ, cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`, xét TRƯỚC hái),
hái nút ở mặt nước (gather, hold_full, mọc lại sau regrow_s), bắt đàn cá dưới nước (fish_caught,
hold_full, hồi chiêu catch_cd_ticks), giỏ dùng chung `_add_to_hold`, xuất kho (ghi đúng một lần do runner lo),
snapshot đầy đủ trường gather.

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

    def __init__(self, tuning, scenario, streams, ids):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self._depth_rounding_error = 0.0
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
        # Đàn cá đứng yên ở phase này. Cá bơi / sinh thêm là việc của phase sau.
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0)} for f in src_fish]
        for coll in (self.nodes, self.fish):
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
        # 2. bơi, chặn mép, tính oxy và ngạt theo độ sâu cuối bước
        was_surface = self._at_surface()
        self._move(inp)
        self._update_oxygen(events, was_surface)
        if self.done:
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if self._at_surface():
                self._try_gather(events)
        # 4. bắt cá
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not self._at_surface():
            self._try_catch(events)
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        return events

    # --- lát 2: giỏ, hái, bắt cá --------------------------------------------------
    def _add_to_hold(self, kinds) -> bool:
        """Thêm đủ `kinds` theo thứ tự nhặt nếu còn chỗ; thiếu chỗ thì không thêm gì và trả False.
        Dùng chung cho lát 1 và lát 2 (hợp đồng mục 5)."""
        if len(self.hold) + len(kinds) > self.t["hold_capacity"]:
            return False
        self.hold.extend(kinds)
        return True

    def _hold_free(self) -> int:
        return self.t["hold_capacity"] - len(self.hold)

    def _nearest(self, items, radius):
        """Thực thể gần nhất trong `radius` (đúng mép vẫn tính); bằng khoảng cách thì id nhỏ."""
        best, best_d = None, None
        for e in sort_by_id(items):
            d = math.dist(self.pos, e["pos"])
            if d <= radius and (best is None or d < best_d):
                best, best_d = e, d
        return best

    def _try_gather(self, events):
        ready = [n for n in self.nodes if n["regrow_ticks"] == 0]
        n = self._nearest(ready, self.t["interact_radius"])
        if n is None:
            return
        count = self.t["node_yield"]
        if self._add_to_hold([n["kind"]] * count):
            n["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
            events.append(("gather", {"node_id": n["id"], "kind": n["kind"], "count": count}))
        else:
            events.append(("hold_full", {"action": "gather", "node_id": n["id"],
                                         "required": count, "free": self._hold_free()}))

    def _try_catch(self, events):
        f = self._nearest(self.fish, self.t["catch_radius"])
        if f is None:
            return
        count = self.t["fish_yield"][f["kind"]]
        if self._add_to_hold([f["kind"]] * count):
            self.fish.remove(f)
            self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
            events.append(("fish_caught", {"fish_id": f["id"], "kind": f["kind"], "count": count}))
        else:
            events.append(("hold_full", {"action": "catch", "fish_id": f["id"],
                                         "required": count, "free": self._hold_free()}))

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _update_oxygen(self, events, was_surface: bool) -> None:
        at_surface = self._at_surface()
        if at_surface != was_surface:
            events.append(("surface" if at_surface else "dive", {"pos": self.pos.copy()}))

        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
            return

        had_oxygen = self.oxygen_ticks > 0
        self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
        if self.oxygen_ticks > 0:
            return
        if had_oxygen:
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))

        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks < self.t["choke_interval_ticks"]:
            return

        self.zero_oxy_ticks = 0
        self.hp -= 1
        events.append(("choke", {"hp": self.hp}))
        if self.hp == 0:
            lost = list(reversed(self.hold))
            self.hold.clear()
            events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
            self._finish("fainted", events)

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
            delta = self.vel[i] / TICK
            lo, hi = b[axis]
            if axis == "d":
                # Cộng bù sai số để đi tới đúng ngưỡng mặt nước sau nhiều bước.
                delta -= self._depth_rounding_error
                depth = self.pos[i] + delta
                self._depth_rounding_error = (
                    (depth - self.pos[i]) - delta if lo < depth < hi else 0.0
                )
                self.pos[i] = depth
            else:
                self.pos[i] += delta
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
