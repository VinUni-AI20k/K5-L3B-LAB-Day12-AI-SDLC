"""Buổi sáng — Lặn & Hái (`gather`). Phase 1 hoàn chỉnh (Lát 1 + Lát 2).

Mặt cắt dòng sông nhìn NGANG: vị trí [x, d] (x sang phải, d độ sâu hướng xuống, d=0 là mặt nước).
move = [x, d]: thành phần thứ hai DƯƠNG = bơi xuống.

Lát 1: bơi, oxy, dive/surface, ngạt (choke), faint, giỏ LIFO.
Lát 2: hái nút mặt nước, bắt cá dưới nước, cập bến, ghi kho.

Thứ tự xử lý mỗi bước (PRD-0 mục F):
  1. Giảm đồng hồ, timer, nút mọc lại.
  2. Bơi + chặn biên, so vị trí đầu/cuối → dive/surface.
  3. Tính oxy theo d cuối bước → oxygen_empty, choke, faint.
  4. interact: bến trước → docked; ngoài bến + mặt nước → hái.
  5. catch: dưới nước + hết hồi → bắt cá.
  6. Hết giờ → time.
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
        self.hold = list(scenario.get("hold", []))   # LIFO: cuối mảng = mới nhất
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
        # Đàn cá đứng yên ở phase này.
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

    # --- giao diện cho runner ---------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": list(self.hold), "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
                     for f in sort_by_id(self.fish)],
        }

    # --- một bước (PRD-0 mục F) -------------------------------------------------
    def step(self, inp):
        events = []

        # ── 1. Đồng hồ, timer, nút mọc lại ─────────────────────────────────────
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))

        # ── 2. Bơi + chặn biên, ghi nhận vị trí trước để so dive/surface ───────
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()

        # dive: từ mặt nước xuống dưới
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        # surface: từ dưới nước lên mặt
        elif not was_surface and now_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        # ── 3. Lát 1: Oxy, ngạt, faint ──────────────────────────────────────────
        if self._at_surface():
            # Mặt nước: hồi oxy, reset đếm ngạt
            prev_oxy = self.oxygen_ticks
            self.oxygen_ticks = min(self.oxygen_max,
                                    self.oxygen_ticks + int(self.t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0
        else:
            # Dưới nước: trừ oxy
            prev_oxy = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if prev_oxy > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            # Mỗi bước dưới nước kết thúc với oxy = 0 → tăng đếm ngạt
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
                    self.zero_oxy_ticks = 0
                    self.hp -= 1
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp <= 0:
                        # Faint: bỏ giỏ theo LIFO (mảng đảo ngược), kho rỗng
                        lost = list(reversed(self.hold))
                        self.hold.clear()
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events

        # ── 4. Lát 2: interact — bến trước, rồi hái ─────────────────────────────
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            # Hái nút: chỉ khi ở mặt nước
            if self._at_surface():
                node = self._nearest_ready_node()
                if node is not None:
                    cap = self.t["hold_capacity"]
                    free = cap - len(self.hold)
                    amount = int(self.t["node_yield"])
                    if free < amount:
                        events.append(("hold_full", {
                            "action": "gather",
                            "node_id": node["id"],
                            "required": amount,
                            "free": free,
                        }))
                    else:
                        for _ in range(amount):
                            self.hold.append(node["kind"])
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {
                            "node_id": node["id"],
                            "kind": node["kind"],
                            "amount": amount,
                        }))

        # ── 5. Lát 2: catch — chỉ dưới nước, hết hồi chiêu ─────────────────────
        if inp.pressed("catch"):
            if not self._at_surface() and self.catch_cd_ticks == 0:
                fish = self._nearest_fish()
                if fish is not None:
                    cap = self.t["hold_capacity"]
                    yield_count = int(self.t["fish_yield"].get(fish["kind"], 1))
                    free = cap - len(self.hold)
                    if free < yield_count:
                        # Thiếu chỗ: giữ cá và cooldown nguyên
                        events.append(("hold_full", {
                            "action": "catch",
                            "fish_id": fish["id"],
                            "required": yield_count,
                            "free": free,
                        }))
                    else:
                        # Đủ chỗ: thêm toàn bộ yield, xóa đàn, đặt cooldown
                        for _ in range(yield_count):
                            self.hold.append(fish["kind"])
                        self.fish.remove(fish)
                        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                        events.append(("fish_caught", {
                            "fish_id": fish["id"],
                            "kind": fish["kind"],
                            "yield": yield_count,
                        }))
                # Không có đàn trong tầm: không có sự kiện, không đặt hồi chiêu

        # ── 6. Hết giờ ──────────────────────────────────────────────────────────
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _nearest_ready_node(self):
        """Nút sẵn sàng (regrow_ticks == 0) gần nhất trong interact_radius; tie-break id nhỏ hơn."""
        radius = self.t["interact_radius"]
        best, best_dist, best_id = None, float("inf"), ""
        for n in self.nodes:
            if n["regrow_ticks"] != 0:
                continue
            d = math.dist(self.pos, n["pos"])
            if d > radius:
                continue
            if best is None or d < best_dist or (d == best_dist and n["id"] < best_id):
                best, best_dist, best_id = n, d, n["id"]
        return best

    def _nearest_fish(self):
        """Cá gần nhất trong catch_radius; tie-break id nhỏ hơn."""
        radius = self.t["catch_radius"]
        best, best_dist, best_id = None, float("inf"), ""
        for f in self.fish:
            d = math.dist(self.pos, f["pos"])
            if d > radius:
                continue
            if best is None or d < best_dist or (d == best_dist and f["id"] < best_id):
                best, best_dist, best_id = f, d, f["id"]
        return best

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        inv = {"items": {}} if reason == "fainted" else {"items": self.inventory_items()}
        events.append(("gather_end", {"reason": reason, "inventory": inv}))

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
