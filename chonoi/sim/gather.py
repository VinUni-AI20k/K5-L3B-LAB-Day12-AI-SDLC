"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Thứ tự một bước theo PRD-0 mục F, Gather:
  Lát 1: bơi + oxy + biên + giỏ
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  Lát 2 (đã làm): hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Phase 2 (v1.1, đã làm): cá kèo, kèo nèo (N5/N6), 8 đàn đầu ca theo điểm sinh, cá bơi 1.5 m/s,
đổi hướng theo seed ở bước bơi thứ 120·k, phản xạ ở mép miền bơi của loài, sinh cá tại phase_tick 360·k (trần 12).
Thứ tự: bắt theo vị trí cá TRƯỚC khi bơi; hết giờ thì không bơi/sinh.
"""

import math

from ..ids import sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity
from .monsters import make_monsters, move_and_choose_hit

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
        self.monsters = make_monsters(t["monsters"], scenario, day)
        self.tick_hz = tuning["tick_hz"]
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
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        # random_fish=false: tắt cá mặc định, bơi và sinh; cá fixture đứng yên (v1.1 mục 4.3)
        self.fish_live = scenario.get("random_fish", True)
        self.phase_tick = 0
        src_fish = scenario.get("fish", [])
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": float(f.get("heading_deg", 0)), "age_ticks": f.get("age_ticks", 0)}
                     for f in src_fish]
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        if self.fish_live and "fish" not in scenario:
            for _ in range(t["fish_initial"]):  # đầu ca: fish_initial đàn ở các điểm sinh khác nhau
                self._spawn_fish()
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
            "monsters": self.monsters,
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      "age_ticks": f["age_ticks"]} for f in sort_by_id(self.fish)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.phase_tick += 1
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
        at_surface = self._at_surface()
        if was_at_surface != at_surface:
            events.append(("surface" if at_surface else "dive", {"pos": self.pos.copy()}))
        self._update_oxygen(at_surface, events)
        if self.hp == 0:
            self._faint("choke", events)
            return events
        config = self.t["monsters"]
        hit = move_and_choose_hit(self.monsters, self.pos, config, self.t["bounds"],
                                  self.tick_hz, self.invuln_ticks > 0)
        if hit is not None:
            self.hp -= 1
            lost = [self.hold.pop() for _ in range(math.floor(len(self.hold) * config["loss_ratio"]))]
            self.invuln_ticks = config["invuln_ticks"]
            events.append(("monster_hit", {"monster_id": hit["id"], "hp": self.hp,
                                           "lost": lost, "pos": self.pos.copy()}))
            if self.hp == 0:
                self._faint("monster", events)
                return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if at_surface:
                self._harvest(events)
        # 4. bắt cá
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not at_surface:
            self._catch(events)
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        # 6. còn giờ: cá bơi (sau khi bắt theo vị trí cũ), rồi sinh theo lịch; cá mới tham gia từ bước sau
        if self.fish_live:
            self._swim_fish()
            if self.phase_tick % self.t["fish_spawn_ticks"] == 0:
                f = self._spawn_fish()
                if f:
                    events.append(("fish_spawned", {"id": f["id"], "kind": f["kind"], "pos": f["pos"]}))
        return events

    # --- cá (v1.1 mục 1.1) --------------------------------------------------------
    def _swim_fish(self):
        t = self.t
        step = t["fish_speed"] / TICK
        turn = self.rng.get("fish_turn")
        for f in sort_by_id(self.fish):
            if (f["age_ticks"] + 1) % t["fish_turn_ticks"] == 0:  # bước bơi thứ 120, 240…: đổi hướng trước
                f["heading_deg"] = turn.uniform(0, 360)
            h = math.radians(f["heading_deg"])
            v = [math.cos(h) * step, math.sin(h) * step]
            flipped = False
            for i, (lo, hi) in enumerate((t["fish_x"], t["fish_depths"][f["kind"]])):
                n = f["pos"][i] + v[i]
                if n >= hi or n <= lo:  # tới mép: phản xạ phần quãng đường còn lại, đảo thành phần vuông góc
                    edge = hi if n >= hi else lo
                    n = 2 * edge - n
                    v[i] = -v[i]
                    flipped = True
                f["pos"][i] = n
            if flipped:
                f["heading_deg"] = math.degrees(math.atan2(v[1], v[0])) % 360
            f["age_ticks"] += 1

    def _spawn_fish(self):
        """Sinh tối đa một đàn: loài theo trọng số (chuẩn hóa trên loài còn điểm), rồi điểm đều, hướng theo seed."""
        t = self.t
        if len(self.fish) >= t["fish_max"]:
            return None
        clear = t["fish_spawn_clearance"]
        pts = {}
        for kind in sorted(t["fish_spawn_depths"]):
            ok = [[float(x), float(d)] for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]
                  if all(math.dist((x, d), f["pos"]) > clear for f in self.fish)]
            if ok:
                pts[kind] = ok
        if not pts:
            return None  # hết điểm hợp lệ: bỏ lượt
        rng = self.rng.get("fish_spawn")
        r = rng.random() * sum(t["fish_weights"][k] for k in pts)
        for kind in pts:
            r -= t["fish_weights"][kind]
            if r < 0:
                break
        f = {"id": self.ids.new("F"), "kind": kind, "pos": pts[kind][rng.randrange(len(pts[kind]))],
             "heading_deg": rng.uniform(0, 360), "age_ticks": 0}
        self.fish.append(f)
        return f

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _update_oxygen(self, at_surface, events):
        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
            return

        if self.oxygen_ticks > 0:
            self.oxygen_ticks -= 1
            if self.oxygen_ticks > 0:
                return
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))

        # Bước vừa chạm 0 là bước đầu tiên của chu kỳ ngạt.
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
            self.zero_oxy_ticks = 0
            self.hp -= 1
            events.append(("choke", {"hp": self.hp}))

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _nearest(self, coll, radius):
        """Thực thể gần nhất trong bán kính (tính cả đúng mép), hòa thì id nhỏ (min ổn định trên list đã sắp)."""
        cands = [e for e in sort_by_id(coll) if math.dist(self.pos, e["pos"]) <= radius]
        return min(cands, key=lambda e: math.dist(self.pos, e["pos"]), default=None)

    def _room(self, action, key, ident, need, events) -> bool:
        free = self.t["hold_capacity"] - len(self.hold)
        if free >= need:
            return True
        events.append(("hold_full", {"action": action, key: ident, "required": need, "free": free}))
        return False

    def _harvest(self, events):
        n = self._nearest([n for n in self.nodes if n["regrow_ticks"] == 0], self.t["interact_radius"])
        if n is None:
            return
        amount = self.t["node_yield"]
        if not self._room("gather", "node_id", n["id"], amount, events):
            return  # PRD F: thiếu chỗ thì nút giữ nguyên
        self.hold.extend([n["kind"]] * amount)
        n["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": n["id"], "kind": n["kind"], "amount": amount}))

    def _catch(self, events):
        f = self._nearest(self.fish, self.t["catch_radius"])
        if f is None:
            return  # không có đàn trong tầm: không sự kiện, không hồi chiêu
        y = self.t["fish_yield"][f["kind"]]
        if not self._room("catch", "fish_id", f["id"], y, events):
            return  # giữ đàn và cooldown, không thử đàn khác
        self.hold.extend([f["kind"]] * y)
        self.fish.remove(f)
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        events.append(("fish_caught", {"fish_id": f["id"], "kind": f["kind"], "yield": y}))

    def _faint(self, cause, events):
        lost = list(reversed(self.hold))
        self.hold.clear()
        events.append(("faint", {"cause": cause, "lost": lost, "hp": 0}))
        self._finish("fainted", events)

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
