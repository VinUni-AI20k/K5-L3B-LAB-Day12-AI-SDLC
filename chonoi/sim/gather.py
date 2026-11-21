"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Lát 1 xử lý bơi, chặn biên, oxy và ngất làm rơi giỏ theo LIFO.

Nhóm viết tiếp theo mục F của Test Contract v1.0:
  TODO(nhóm, lát 2): hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..ids import id_key, sort_by_id
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
                       "catch_cd_ticks": self.catch_cd_ticks,
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
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 2. Bơi và chặn biên trước khi tính oxy theo độ sâu thực ở cuối bước.
        was_at_surface = self._at_surface()
        self._move(inp)
        at_surface = self._at_surface()
        if at_surface != was_at_surface:
            name = "surface" if at_surface else "dive"
            # Sao chép vị trí để payload phản ánh đúng tick chuyển vùng.
            events.append((name, {"pos": self.pos.copy()}))

        self._update_oxygen(at_surface, events)
        if self.done:
            # Ngất chốt lượt ngay, trước cập bến, hái, bắt cá và hết giờ.
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if at_surface:
                self._try_gather_node(events)
        # 4. bắt cá
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not at_surface:
            self._try_catch_fish(events)
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _update_oxygen(self, at_surface, events):
        if at_surface:
            # Nổi lên dừng chuỗi thiếu oxy ngay cả ở tick đáng lẽ bị ngạt.
            refill = self.t["oxygen_refill_per_tick"]
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + refill)
            self.zero_oxy_ticks = 0
            return

        # Mỗi bước dưới nước tiêu một tick oxy. Sự kiện oxygen_empty chỉ phát
        # ở bước chuyển từ oxy dương về 0.
        previous_oxygen = self.oxygen_ticks
        self.oxygen_ticks = max(0, previous_oxygen - 1)
        if self.oxygen_ticks > 0:
            return
        if previous_oxygen > 0:
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))

        # Tick vừa cạn oxy là tick thứ nhất của chuỗi ngạt.
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks < self.t["choke_interval_ticks"]:
            return

        self.zero_oxy_ticks = 0
        self.hp -= 1
        events.append(("choke", {"hp": self.hp}))
        if self.hp == 0:
            # Giỏ lưu cũ → mới. Payload mất đồ lưu theo thứ tự bỏ mới → cũ.
            lost = list(reversed(self.hold))
            self.hold.clear()
            events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
            # Runner dùng cùng giỏ đã rỗng để ghi inventory-out.
            self._finish("fainted", events)

    def _nearest_in_radius(self, items: list, radius: float, pred=None):
        """Tìm phần tử gần nhất trong bán kính, hòa khoảng cách thì ưu tiên id nhỏ."""
        best = None
        best_key = None
        for item in items:
            if pred is not None and not pred(item):
                continue
            dist = math.dist(self.pos, item["pos"])
            if dist <= radius:
                key = (dist, id_key(item["id"]))
                if best_key is None or key < best_key:
                    best = item
                    best_key = key
        return best

    def _harvest_target(self):
        return self._nearest_in_radius(
            self.nodes, self.t["interact_radius"], pred=lambda n: n["regrow_ticks"] == 0
        )

    def live_hints(self):
        if self.done or len(self.hold) >= self.t["hold_capacity"]:
            return {}
        if self._at_surface():
            node = None if self._in_dock() else self._harvest_target()
            return {"harvest_target_id": node["id"]} if node else {}
        fish = None if self.catch_cd_ticks else self._nearest_in_radius(self.fish, self.t["catch_radius"])
        return {"catch_target_id": fish["id"]} if fish else {}

    def _try_gather_node(self, events: list):
        node = self._harvest_target()
        if node is None:
            return
        space = self.t["hold_capacity"] - len(self.hold)
        if space <= 0:
            events.append(("hold_full", {"kind": node["kind"], "node_id": node["id"]}))
            return
        added = min(self.t["node_yield"], space)
        self.hold.extend([node["kind"]] * added)
        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "count": added}))

    def _try_catch_fish(self, events: list):
        fish = self._nearest_in_radius(self.fish, self.t["catch_radius"])
        if fish is None:
            return
        space = self.t["hold_capacity"] - len(self.hold)
        if space <= 0:
            events.append(("hold_full", {"kind": fish["kind"], "fish_id": fish["id"]}))
            return
        yield_amt = self.t["fish_yield"][fish["kind"]]
        added = min(yield_amt, space)
        self.hold.extend([fish["kind"]] * added)
        self.fish.remove(fish)
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "count": added}))

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
