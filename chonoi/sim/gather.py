"""Mô phỏng buổi sáng: bơi, oxy, hái rau, bắt cá và bàn giao kho.

Vị trí [x, d] nằm trong mặt cắt ngang của sông, với độ sâu d tăng xuống dưới.
Trong v1.1, đàn cá bơi và sinh theo seed ở cuối các bước còn thời gian.
"""

import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
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
        self.day = day
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
        for node in self.nodes:
            ids.reserve(node["id"])

        preset = t["fish_initial"]
        self._fish_v11 = isinstance(preset, int)
        self._random_fish = scenario.get("random_fish", True)
        self._fish_tick = 0
        if "fish" in scenario:
            initial_fish = scenario["fish"]
        elif self._random_fish and not self._fish_v11:
            initial_fish = preset
        else:
            initial_fish = []
        self.fish = [
            {"id": fish["id"], "kind": fish["kind"], "pos": list(map(float, fish["pos"])),
             "heading_deg": fish.get("heading_deg", 0), "age_ticks": fish.get("age_ticks", 0)}
            for fish in initial_fish
        ]
        for fish in self.fish:
            ids.reserve(fish["id"])

        if self._fish_v11 and self._random_fish:
            # Các điểm có thể trùng tọa độ giữa hai loài. Khi sinh, đối chiếu
            # với vị trí mọi đàn đang sống, kể cả đàn vừa được thêm đầu ca.
            self._fish_spawn_points = {
                kind: [(x, d) for x in sorted(t["fish_spawn_x"]) for d in sorted(depths)]
                for kind, depths in sorted(t["fish_spawn_depths"].items())
            }
            if "fish" not in scenario:
                for _ in range(preset):
                    if self._spawn_fish(clearance=0) is None:
                        raise BadInput("gather.fish_initial vượt số tọa độ sinh khác nhau")
        self._init_monsters(day, ids)
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        fish_fields = ("id", "pos", "kind", "heading_deg")
        if self._fish_v11:
            fish_fields += ("age_ticks",)
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
            "fish": [{field: f[field] for field in fish_fields} for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "kind": m["kind"], "pos": list(m["pos"]),
                          "state": m["state"], "heading_deg": m["heading_deg"]}
                         for m in sort_by_id(self.monsters)],
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
        # 4b. thủy quái (Cá Sấu Năm Chèo)
        if self.time_left_ticks > 0:
            self._update_monsters(at_surface, events)
            if self.done:
                return events
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        elif self._fish_v11 and self._random_fish:
            # Bắt dùng vị trí đầu bước. Cá sinh ở đây bắt đầu bơi từ bước sau.
            self._advance_fish(events)
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

    def _spawn_fish(self, clearance):
        # Lọc theo khoảng cách thực rồi chọn loài có trọng số. Nếu một loài
        # hết điểm, chỉ tính lại trọng số trên các loài còn điểm hợp lệ.
        points_by_kind = {}
        for kind, points in self._fish_spawn_points.items():
            available = [
                pos for pos in points
                if all(math.dist(pos, fish["pos"]) > clearance for fish in self.fish)
            ]
            if available:
                points_by_kind[kind] = available
        if not points_by_kind:
            return None

        rng = self.rng.get("fish_spawn")
        kinds = list(points_by_kind)
        weights = [self.t["fish_weights"][kind] for kind in kinds]
        kind = rng.choices(kinds, weights=weights, k=1)[0]
        fish = {
            "id": self.ids.new("F"),
            "kind": kind,
            "pos": list(rng.choice(points_by_kind[kind])),
            "heading_deg": rng.random() * 360,
            "age_ticks": 0,
        }
        self.fish.append(fish)
        return fish

    @staticmethod
    def _reflect_axis(position, delta, bounds):
        low, high = bounds
        width = high - low
        # Trải miền bơi thành các đoạn gương để giữ phần quãng đường còn
        # lại sau khi chạm mép. Hai trục phản xạ riêng nên góc đảo cả hai.
        offset = (position - low + delta) % (2 * width)
        if min(offset, 2 * width - offset) <= 1e-12:
            return low, abs(delta)
        if math.isclose(offset, width, rel_tol=0, abs_tol=1e-12):
            return high, -abs(delta)
        if offset < width:
            return low + offset, delta
        return high - (offset - width), -delta

    def _advance_fish(self, events):
        self._fish_tick += 1
        distance = self.t["fish_speed"] / TICK
        for fish in sort_by_id(self.fish):
            fish["age_ticks"] += 1
            heading = fish["heading_deg"]
            if fish["age_ticks"] % self.t["fish_turn_ticks"] == 0:
                # Đổi hướng trước khi bơi ở bước thứ 120, 240... của đàn.
                heading = self.rng.get("fish_turn").random() * 360
            angle = math.radians(heading)
            dx, dd = distance * math.cos(angle), distance * math.sin(angle)
            x, reflected_dx = self._reflect_axis(fish["pos"][0], dx, self.t["fish_x"])
            d, reflected_dd = self._reflect_axis(
                fish["pos"][1], dd, self.t["fish_depths"][fish["kind"]],
            )
            fish["pos"] = [x, d]
            if (reflected_dx, reflected_dd) != (dx, dd):
                heading = math.degrees(math.atan2(reflected_dd, reflected_dx)) % 360
            fish["heading_deg"] = heading

        if self._fish_tick % self.t["fish_spawn_ticks"] == 0 and len(self.fish) < self.t["fish_max"]:
            fish = self._spawn_fish(self.t["fish_spawn_clearance"])
            if fish is not None:
                events.append(("fish_spawned", {
                    "id": fish["id"], "kind": fish["kind"], "pos": fish["pos"].copy(),
                }))

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
        free = self.t["hold_capacity"] - len(self.hold)
        amount = self.t["node_yield"]
        if free < amount:
            events.append(("hold_full", {
                "action": "gather", "node_id": node["id"], "required": amount, "free": free,
            }))
            return
        self.hold.extend([node["kind"]] * amount)
        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": amount}))

    def _try_catch_fish(self, events: list):
        fish = self._nearest_in_radius(self.fish, self.t["catch_radius"])
        if fish is None:
            return
        free = self.t["hold_capacity"] - len(self.hold)
        amount = self.t["fish_yield"][fish["kind"]]
        if free < amount:
            # Không lấy một phần và không thử đàn khác nếu đàn gần nhất không vừa.
            events.append(("hold_full", {
                "action": "catch", "fish_id": fish["id"], "required": amount, "free": free,
            }))
            return
        self.hold.extend([fish["kind"]] * amount)
        self.fish.remove(fish)
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": amount}))

    def _init_monsters(self, day: int, ids):
        m_cfg = self.t.get("monsters") or {}
        self.monsters = []
        for sp in m_cfg.get("spawns", []):
            if sp.get("from_day", 1) > day:
                continue
            ids.reserve(sp["id"])
            wps = [[float(c) for c in wp] for wp in sp.get("waypoints", [sp["pos"]])]
            pos = [float(c) for c in sp["pos"]]
            wp_idx = 1 if len(wps) > 1 and pos == wps[0] else 0
            self.monsters.append({
                "id": sp["id"],
                "kind": sp["kind"],
                "pos": pos,
                "waypoints": wps,
                "wp_idx": wp_idx,
                "state": "patrol",
                "heading_deg": 0.0,
                "recoil_ticks": 0,
                "recoil_dir": [0.0, 0.0],
            })

    def _step_monster_toward(self, m: dict, target: list, speed: float, depths: list) -> bool:
        """Di chuyển thủy quái về phía target trong giới hạn x và depths; trả về True nếu chạm target."""
        dx = target[0] - m["pos"][0]
        dy = target[1] - m["pos"][1]
        dist = math.hypot(dx, dy)
        step = speed / TICK
        if dist > 1e-9:
            m["heading_deg"] = math.degrees(math.atan2(dy, dx)) % 360
        if dist <= step:
            nx, ny = target[0], target[1]
            arrived = True
        else:
            nx = m["pos"][0] + (dx / dist) * step
            ny = m["pos"][1] + (dy / dist) * step
            arrived = False
        bx = self.t["bounds"]["x"]
        m["pos"][0] = max(float(bx[0]), min(float(bx[1]), nx))
        m["pos"][1] = max(float(depths[0]), min(float(depths[1]), ny))
        return arrived

    def _update_monsters(self, at_surface: bool, events: list):
        m_cfg = self.t.get("monsters")
        if not m_cfg or not self.monsters:
            return
        species = m_cfg["species"]
        bx = self.t["bounds"]["x"]

        # 1. Di chuyển từng Cá Sấu (recoil hoặc patrol/chase)
        hit_candidates = []
        for m in sort_by_id(self.monsters):
            sp = species[m["kind"]]
            depths = sp["depths"]
            if m["state"] == "recoil":
                step = sp["recoil_dist"] / max(1, sp["recoil_ticks"])
                nx = m["pos"][0] + m["recoil_dir"][0] * step
                ny = m["pos"][1] + m["recoil_dir"][1] * step
                m["pos"][0] = max(float(bx[0]), min(float(bx[1]), nx))
                m["pos"][1] = max(float(depths[0]), min(float(depths[1]), ny))
                m["recoil_ticks"] -= 1
                if m["recoil_ticks"] <= 0:
                    m["state"] = "patrol"
                continue

            in_zone = self.pos[1] >= depths[0]
            dist = math.dist(m["pos"], self.pos)
            if m["state"] == "patrol":
                if in_zone and dist <= sp["detect_radius"]:
                    m["state"] = "chase"
            elif m["state"] == "chase":
                if not in_zone or dist > sp["exit_radius"]:
                    m["state"] = "patrol"

            if m["state"] == "chase":
                self._step_monster_toward(m, self.pos, sp["chase_speed"], depths)
            else:
                wp = m["waypoints"][m["wp_idx"]]
                if self._step_monster_toward(m, wp, sp["patrol_speed"], depths):
                    m["wp_idx"] = (m["wp_idx"] + 1) % len(m["waypoints"])

            if in_zone and self.invuln_ticks == 0:
                d_after = math.dist(m["pos"], self.pos)
                if d_after <= sp["hit_radius"]:
                    hit_candidates.append((d_after, id_key(m["id"]), m, sp))

        # 2. Tối đa một hit mỗi bước: chọn con gần nhất, hòa theo id
        if not hit_candidates:
            return
        _, _, m, sp = min(hit_candidates, key=lambda item: (item[0], item[1]))
        self.hp = max(0, self.hp - 1)
        self.invuln_ticks = m_cfg["invuln_ticks"]
        drop_n = math.floor(len(self.hold) * m_cfg["loss_ratio"])
        lost = [self.hold.pop() for _ in range(drop_n)]
        events.append(("monster_hit", {
            # Test Contract v1.1 mục 4.4: data = monster_id, hp, lost, pos (vị trí người chơi)
            "monster_id": m["id"], "hp": self.hp, "lost": lost, "pos": self.pos.copy(),
        }))
        dx, dy = m["pos"][0] - self.pos[0], m["pos"][1] - self.pos[1]
        norm = math.hypot(dx, dy)
        m["recoil_dir"] = [dx / norm, dy / norm] if norm > 1e-9 else [1.0, 0.0]
        m["state"] = "recoil"
        m["recoil_ticks"] = sp["recoil_ticks"]
        if self.hp == 0:
            faint_lost = list(reversed(self.hold))
            self.hold.clear()
            events.append(("faint", {"cause": "monster", "lost": faint_lost, "hp": 0}))
            self._finish("fainted", events)

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
