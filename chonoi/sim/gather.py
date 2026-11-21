"""Buổi sáng — Lặn & Hái (`gather`). Cá bơi/sinh theo TICKET-02; các luật khác theo lát Phase 1.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD mục 13.8, "Gather"):
  XONG (lát 1, NgChiVinh — `_oxygen_step`, test: tests/test_gather_lat1.py): bơi + oxy + biên + giỏ
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  XONG (lát 2, TrungHieuPh — tests/test_gather_lat2.py): hái + bắt cá
      - cập bến xét trước hái; runner ghi kho đúng một lần khi gather_end
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
  XONG (Phase 2, lát 1 — tests/test_gather_fish.py): cá bơi, đổi hướng và sinh theo lịch.
Cá Sấu và các tính năng Phase 2 khác được triển khai ở các lát riêng.
"""

import math

from ..ids import id_key, sort_by_id
from ..inventory import KINDS
from ..items import decay, list_json, new_item, order_json, parse_items, per_tick
from .monsters import build_monsters, update_monsters
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


def _reflect_axis(position, delta, low, high):
    if low == high:
        return low, 0.0
    position += delta
    while (position < low or position > high
           or (position == low and delta < 0)
           or (position == high and delta > 0)):
        if position < low:
            position = 2 * low - position
            delta = abs(delta)
        elif position > high:
            position = 2 * high - position
            delta = -abs(delta)
        else:
            delta = -delta
    return position, delta


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1):
        t = tuning["gather"]
        self.day = day  # Ngày hiện tại (--mode day); gather độc lập dùng bố trí Ngày 1 (quái from_day)
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
        self.phase_tick = 0
        self.monsters = build_monsters(t["monsters"], scenario.get("monsters"), ids, day=day)
        # v1.2: giỏ là mảng cá thể {id, kind, fresh} theo thứ tự vào giỏ (cuối = mới nhất). Ngày 1 giữ id của mẫu;
        # các Ngày kế cấp id mới theo thứ tự mảng với kind/fresh ban đầu (TICKET-03 mục Scenario).
        fr = tuning["freshness"]
        self.fresh_initial, self.spoiled_below = fr["initial"], fr["spoiled_below"]
        self.decay_step = per_tick(fr["gather_decay_per_s"])
        self.hold = parse_items(scenario.get("hold", []), KINDS, "gather.hold")
        if day > 1:
            for it in self.hold:
                it["id"] = ids.new("I")
        else:
            for it in self.hold:
                ids.reserve(it["id"])
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        # v1.1 (TICKET-02 mục 1.1, 4.3): random_fish (mặc định true) bật cá mặc định + bơi + sinh.
        #   fish khai trong scenario THAY đàn ban đầu (vẫn bơi/sinh nếu cờ bật); random_fish=false -> cá fixture đứng yên.
        self.random_fish = scenario.get("random_fish", True)
        src_fish = scenario.get("fish", [])
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0), "age_ticks": f.get("age_ticks", 0)} for f in src_fish]
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        if self.random_fish and "fish" not in scenario:
            # Đầu ca fish_initial đàn ở các điểm khác nhau (cách mọi đàn > fish_spawn_clearance)
            for _ in range(int(t["fish_initial"])):
                f = self._spawn_one()
                if f is None:
                    break
                self.fish.append(f)
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> list:
        """Kho bàn giao (v1.2): các cá thể còn trong giỏ, giữ nguyên id và độ tươi."""
        return [dict(it) for it in self.hold]

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": order_json(self.hold), "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      "age_ticks": f["age_ticks"]} for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "kind": m["kind"], "pos": m["pos"],
                          "waypoints": m["waypoints"], "target_idx": m["target_idx"],
                          "state": m["state"], "state_ticks_left": m["state_ticks_left"],
                          "recoil_dir": m["recoil_dir"]} for m in sort_by_id(self.monsters)],
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
        # 1b. độ tươi hàng có sẵn trong giỏ (cá thể mới bắt/hái hao từ bước sau)
        decay(self.hold, self.decay_step, self.spoiled_below, "hold", events)
        # 2. bơi + chặn mép, dive/surface, oxy, ngạt, ngất (lát 1)
        was_surface = self._at_surface()
        self._move(inp)
        if self._oxygen_step(was_surface, events):
            return events
        # 3. Quái cập nhật sau bơi/oxy và trước tương tác (TICKET-02 mục 4.5).
        # Bất tử đã giảm ở bước 1 (mục 4.5, như hồi bắt): 'hết bất tử' xét theo giá trị SAU khi giảm.
        if update_monsters(self, events, can_hit=self.invuln_ticks == 0):
            return events
        # 4. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if self._at_surface():
                candidates = [n for n in self.nodes
                              if n["regrow_ticks"] == 0
                              and math.dist(self.pos, n["pos"]) <= self.t["interact_radius"]]
                if candidates:
                    node = min(candidates, key=lambda n: (math.dist(self.pos, n["pos"]), id_key(n["id"])))
                    amount = int(self.t["node_yield"])
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free < amount:
                        events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                                     "required": amount, "free": free}))
                    else:
                        self.hold.extend(new_item(self.ids, node["kind"], self.fresh_initial) for _ in range(amount))
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {"node_id": node["id"], "kind": node["kind"],
                                                  "amount": amount}))
        # 5. bắt cá
        if inp.pressed("catch"):
            if self.catch_cd_ticks == 0 and not self._at_surface():
                candidates = [f for f in self.fish
                              if math.dist(self.pos, f["pos"]) <= self.t["catch_radius"]]
                if candidates:
                    fish = min(candidates, key=lambda f: (math.dist(self.pos, f["pos"]), id_key(f["id"])))
                    amount = int(self.t["fish_yield"][fish["kind"]])
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free < amount:
                        events.append(("hold_full", {"action": "catch", "fish_id": fish["id"],
                                                     "required": amount, "free": free}))
                    else:
                        self.hold.extend(new_item(self.ids, fish["kind"], self.fresh_initial) for _ in range(amount))
                        self.fish.remove(fish)
                        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"],
                                                       "yield": amount}))
        # 5. Cá bơi sau khi tương tác; cá mới sinh chỉ tham gia từ bước sau.
        if self.random_fish and self.time_left_ticks > 0:
            self._advance_fish(events)
        # 6. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _spawn_one(self):
        """Chọn một đàn mới theo seed (TICKET-02 mục 1.1). Trả dict cá hoặc None nếu hết điểm hợp lệ.

        Điểm hợp lệ: (x, d) trong fish_spawn_x × fish_spawn_depths[loài], cách MỌI đàn đang sống > clearance.
        Loài chọn theo fish_weights, chuẩn hóa lại trên các loài còn điểm; rồi chọn đều một điểm; hướng theo seed.
        Dùng chung cho đầu ca (khung) và sinh theo lịch mỗi fish_spawn_ticks (lát 1).
        """
        t = self.t
        rng = self.rng.get("fish_spawn")
        clearance = float(t["fish_spawn_clearance"])
        cands = {}
        for kind in sorted(t["fish_spawn_depths"]):  # duyệt loài theo mã Unicode (thứ tự cố định)
            pts = [(float(x), float(d)) for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]
                   if all(math.dist((x, d), f["pos"]) > clearance for f in self.fish)]
            if pts and t["fish_weights"][kind] > 0:
                cands[kind] = pts
        if not cands:
            return None
        kinds = list(cands)
        r = rng.random() * sum(t["fish_weights"][k] for k in kinds)
        kind = kinds[-1]
        for k in kinds:
            r -= t["fish_weights"][k]
            if r < 0:
                kind = k
                break
        x, d = rng.choice(cands[kind])
        heading = rng.uniform(0.0, 360.0)
        return {"id": self.ids.new("F"), "kind": kind, "pos": [x, d], "heading_deg": heading, "age_ticks": 0}

    def _advance_fish(self, events):
        t = self.t
        turn_rng = self.rng.get("fish_turn")
        for fish in sort_by_id(self.fish):
            fish["age_ticks"] += 1
            if fish["age_ticks"] % int(t["fish_turn_ticks"]) == 0:
                fish["heading_deg"] = turn_rng.uniform(0.0, 360.0)

            angle = math.radians(fish["heading_deg"])
            distance = float(t["fish_speed"]) / TICK
            dx = distance * math.cos(angle)
            dd = distance * math.sin(angle)
            x_bounds = t["fish_x"]
            d_bounds = t["fish_depths"][fish["kind"]]
            x, dx = _reflect_axis(fish["pos"][0], dx, *x_bounds)
            d, dd = _reflect_axis(fish["pos"][1], dd, *d_bounds)
            fish["pos"] = [x, d]
            if dx != 0.0 or dd != 0.0:
                fish["heading_deg"] = math.degrees(math.atan2(dd, dx)) % 360

        if self.phase_tick % int(t["fish_spawn_ticks"]) == 0 and len(self.fish) < int(t["fish_max"]):
            fish = self._spawn_one()
            if fish is not None:
                self.fish.append(fish)
                events.append(("fish_spawned", {"id": fish["id"], "kind": fish["kind"],
                                                "pos": list(fish["pos"])}))

    def _oxygen_step(self, was_surface, events) -> bool:
        """Lát 1 — mục F Gather bước 2. Trả True nếu ngất (bước dừng tại đây)."""
        t = self.t
        at_surface = self._at_surface()
        if was_surface != at_surface:
            events.append(("surface" if at_surface else "dive", {"pos": list(self.pos)}))
        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + int(t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0
            return False
        before = self.oxygen_ticks
        self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
        if before > 0 and self.oxygen_ticks == 0:
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        if self.oxygen_ticks > 0:
            return False
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks < int(t["choke_interval_ticks"]):
            return False
        self.zero_oxy_ticks = 0
        self.hp = max(0, self.hp - 1)
        events.append(("choke", {"hp": self.hp}))
        if self.hp > 0:
            return False
        lost = order_json(reversed(self.hold))  # bỏ theo LIFO: nhặt sau bỏ trước (mảng cá thể)
        self.hold = []
        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
        self._finish("fainted", events)
        return True

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": list_json(self.hold)}}))

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
