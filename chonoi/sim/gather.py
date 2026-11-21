"""Buổi sáng — Lặn & Hái (`gather`): bơi, cá, thủy quái, cập bến và xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Lát 1 xử lý bơi, oxy, ngạt, Máu, giỏ và thủy quái. Lát 2 xử lý hái, bắt cá,
cá bơi/sinh và xuất kho. Các số liệu luật chơi lấy từ game.contract.json.
"""

from fractions import Fraction
import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import format_item, hold_to_items, to_fraction, validate_items
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
        self.fresh_cfg = tuning["freshness"]
        self.tick_hz = tuning["tick_hz"]
        self.decay_per_tick = to_fraction(self.fresh_cfg["gather_decay_per_s"]) / Fraction(int(self.tick_hz))
        self.spoiled_below = to_fraction(self.fresh_cfg["spoiled_below"])
        self.initial_fresh = to_fraction(self.fresh_cfg["initial"])

        self.current_cfg = t.get("current")
        self.random_current = scenario.get("random_current", bool(self.current_cfg))
        self.current_direction = scenario.get("current_direction")
        self.current = None

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
        raw_hold = validate_items(scenario.get("hold", []))
        if len(raw_hold) > t["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
        self.hold = [{"id": it["id"], "kind": it["kind"], "fresh": to_fraction(it["fresh"])}
                     for it in raw_hold]  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        self.random_fish = scenario.get("random_fish", True)
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif self.random_fish:
            src_fish = t.get("fish_initial", [])
        else:
            src_fish = []
        initial_count = src_fish if isinstance(src_fish, int) else 0
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0), "age_ticks": f.get("age_ticks", 0)}
                     for f in src_fish] if isinstance(src_fish, list) else []
        self.phase_tick = 0

        # Thủy quái (Cá Sấu) — TV1 phụ trách
        self.day = scenario.get("day", 1)
        m_cfg = t.get("monsters", {})
        self.monsters_cfg = m_cfg
        self.monsters = []
        if "monsters" in scenario:
            for m in scenario["monsters"]:
                wps = [[float(c) for c in wp] for wp in m.get("waypoints", [[float(c) for c in m["pos"]], [float(c) for c in m["pos"]]])]
                self.monsters.append({
                    "id": m["id"],
                    "kind": m.get("kind", "ca_sau"),
                    "pos": [float(c) for c in m["pos"]],
                    "waypoints": wps,
                    "target_idx": m.get("target_idx", 1),
                    "state": m.get("state", "patrol"),
                    "state_ticks_left": m.get("state_ticks_left", 0),
                    "recoil_dir": [float(c) for c in m["recoil_dir"]] if m.get("recoil_dir") else None,
                })
        else:
            spawns = m_cfg.get("spawns", [])
            for s in spawns:
                if s.get("from_day", 1) <= self.day:
                    wps = [[float(c) for c in wp] for wp in s["waypoints"]]
                    self.monsters.append({
                        "id": s["id"],
                        "kind": s["kind"],
                        "pos": [float(c) for c in s["pos"]],
                        "waypoints": wps,
                        "target_idx": 1,
                        "state": "patrol",
                        "state_ticks_left": 0,
                        "recoil_dir": None,
                    })

        seen_entity_ids = set()
        for coll in (self.nodes, self.fish, self.monsters, self.hold):
            for e in coll:
                if e["id"] in seen_entity_ids:
                    raise BadInput(f"id trùng giữa các thực thể gather: {e['id']}")
                seen_entity_ids.add(e["id"])
                ids.reserve(e["id"])
        if initial_count:
            for _ in range(initial_count):
                fish = self._new_fish()
                if fish is None:
                    break
                self.fish.append(fish)
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    def enable_live_creative(self):
        """Sáng tạo của nhóm: chỉ bật khi chơi trực tiếp (--mode live --creative, ADR-0002).
        Mở rộng tuần tra Cá Sấu, thêm M2/M3 và bầy cá kèo đắt tiền ở tầng nước sâu.
        """
        for m in self.monsters:
            if m["id"] == "M1":
                m["waypoints"] = [[45.0, 24.0], [70.0, 24.0]]
        if not any(m["id"] == "M2" for m in self.monsters):
            self.monsters.append({
                "id": "M2",
                "kind": "ca_sau",
                "pos": [80.0, 18.0],
                "waypoints": [[75.0, 18.0], [95.0, 18.0]],
                "target_idx": 1,
                "state": "patrol",
                "state_ticks_left": 0,
                "recoil_dir": None,
            })
            self.ids.reserve("M2")
        if not any(m["id"] == "M3" for m in self.monsters):
            self.monsters.append({
                "id": "M3",
                "kind": "ca_sau",
                "pos": [25.0, 22.0],
                "waypoints": [[15.0, 22.0], [40.0, 22.0]],
                "target_idx": 1,
                "state": "patrol",
                "state_ticks_left": 0,
                "recoil_dir": None,
            })
            self.ids.reserve("M3")
        deep_fishes = [
            {"id": "FK1", "kind": "ca_keo", "pos": [30.0, 25.0], "heading_deg": 0, "age_ticks": 0},
            {"id": "FK2", "kind": "ca_keo", "pos": [55.0, 26.5], "heading_deg": 180, "age_ticks": 0},
            {"id": "FK3", "kind": "ca_keo", "pos": [85.0, 24.0], "heading_deg": 0, "age_ticks": 0},
        ]
        for df in deep_fishes:
            if not any(f["id"] == df["id"] for f in self.fish):
                self.fish.append(df)
                self.ids.reserve(df["id"])

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> list:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": [format_item(it) for it in self.hold], "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "current": dict(self.current) if self.current is not None else None,
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"],
                      "heading_deg": f["heading_deg"], "age_ticks": f["age_ticks"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "kind": m["kind"], "pos": m["pos"],
                          "waypoints": m["waypoints"], "target_idx": m["target_idx"],
                          "state": m["state"], "state_ticks_left": m["state_ticks_left"],
                          "recoil_dir": m["recoil_dir"]}
                         for m in sort_by_id(self.monsters)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        self.phase_tick += 1
        # 1. đồng hồ, cooldown, hồi nút và độ tươi của hàng có sẵn ở đầu bước
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        self._tick_hold_freshness(events)

        # 2. lịch dòng lũ nếu bật
        self._tick_current(events)

        # 3. bơi + chặn mép, oxy và ngạt
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()

        # so phân vùng đầu/cuối bước -> dive / surface (data: pos)
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and now_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        # oxy theo d CUỐI bước (mặt nước hồi, dưới nước trừ), oxygen_empty khi từ dương xuống 0
        if now_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
        else:
            if self.oxygen_ticks > 0:
                self.oxygen_ticks -= 1
                if self.oxygen_ticks == 0:
                    events.append(("oxygen_empty", {}))
            else:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
                    self.zero_oxy_ticks = 0
                    self.hp -= 1
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp <= 0:
                        self._end_current_if_active(events)
                        lost = [format_item(it) for it in reversed(self.hold)]
                        self.hold = []
                        events.append(("faint", {"cause": "choke", "hp": 0, "lost": lost}))
                        self._finish("fainted", events)
                        return events
        # 4. Quái update theo ID, xét tối đa một hit (TV1)
        self._update_monsters()
        if self._check_monster_hit(events):
            return events

        # 5. interact: bến trước, rồi hái (TV2)
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if self._at_surface():
                self._try_gather(events)
        # 6. bắt cá (TV2)
        if inp.pressed("catch"):
            self._try_catch(events)
        # 7. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events

        # 8. Khi còn giờ: cá bơi, cá sinh (TV2)
        if self.random_fish:
            self._move_fish()
        self._spawn_fish(events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _tick_hold_freshness(self, events):
        newly_spoiled = []
        for it in self.hold:
            old_f = it["fresh"]
            new_f = max(Fraction(0), old_f - self.decay_per_tick)
            it["fresh"] = new_f
            if old_f >= self.spoiled_below and new_f < self.spoiled_below:
                newly_spoiled.append(it)
        for it in sort_by_id(newly_spoiled):
            events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "hold"}))

    def _tick_current(self, events):
        if self.current is not None:
            self.current["ticks_left"] -= 1
            if self.current["ticks_left"] <= 0:
                events.append(("current_end", {"direction": self.current["direction"], "reason": "elapsed"}))
                self.current = None
        if not self.random_current or not self.current_cfg:
            return
        interval = int(self.current_cfg["interval_ticks"])
        warn = int(self.current_cfg["warning_ticks"])
        dur = int(self.current_cfg["duration_ticks"])
        if self.phase_tick + warn >= interval and (self.phase_tick + warn) % interval == 0:
            events.append(("current_warning", {"starts_at_phase_tick": self.phase_tick + warn}))
        if self.phase_tick > 0 and self.phase_tick % interval == 0:
            if self.current_direction is not None:
                direction = int(self.current_direction)
            else:
                direction = int(self.rng.get("current").choice((-1, 1)))
            self.current = {"direction": direction, "ticks_left": dur}
            events.append(("current_start", {"direction": direction, "duration_ticks": dur}))

    def _end_current_if_active(self, events):
        if self.current is not None:
            events.append(("current_end", {"direction": self.current["direction"], "reason": "phase_end"}))
            self.current = None

    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self._end_current_if_active(events)
        if reason == "fainted":
            self.hold.clear()
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _try_gather(self, events):
        radius = self.t["interact_radius"]
        nearby = [n for n in self.nodes
                  if n["regrow_ticks"] == 0 and math.dist(self.pos, n["pos"]) <= radius]
        if not nearby:
            return
        node = min(nearby, key=lambda n: (math.dist(self.pos, n["pos"]), id_key(n["id"])))
        amount = self.t["node_yield"]
        if len(self.hold) + amount > self.t["hold_capacity"]:
            events.append(("hold_full", {"source": "node", "source_id": node["id"]}))
            return
        for _ in range(amount):
            self.hold.append({"id": self.ids.new("I"), "kind": node["kind"], "fresh": self.initial_fresh})
        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "yield": amount}))

    def _try_catch(self, events):
        if self._at_surface() or self.catch_cd_ticks > 0:
            return
        radius = self.t["catch_radius"]
        nearby = [f for f in self.fish if math.dist(self.pos, f["pos"]) <= radius]
        if not nearby:
            return
        fish = min(nearby, key=lambda f: (math.dist(self.pos, f["pos"]), id_key(f["id"])))
        amount = self.t["fish_yield"][fish["kind"]]
        if len(self.hold) + amount > self.t["hold_capacity"]:
            events.append(("hold_full", {"source": "fish", "source_id": fish["id"]}))
            return
        for _ in range(amount):
            self.hold.append({"id": self.ids.new("I"), "kind": fish["kind"], "fresh": self.initial_fresh})
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": amount}))
        self.fish.remove(fish)

    def _move(self, inp):
        d_start = self.pos[1]
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        current_dx = 0.0
        if self.current is not None and self.current_cfg and d_start >= self.current_cfg["min_depth"]:
            current_dx = self.current["direction"] * (self.current_cfg["speed"] / TICK)
        deltas = (self.vel[0] / TICK + current_dx, self.vel[1] / TICK)
        for i, axis in enumerate(AXES):
            self.pos[i] += deltas[i]
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])

    # --- Thủy quái (Cá Sấu) — TV1 ----------------------------------------------
    def _update_monsters(self):
        species_cfg = self.monsters_cfg.get("species", {}).get("ca_sau", {})
        patrol_speed = species_cfg.get("patrol_speed", 1.0)
        chase_speed = species_cfg.get("chase_speed", 3.0)
        detect_radius = species_cfg.get("detect_radius", 10.0)
        exit_radius = species_cfg.get("exit_radius", 16.0)
        depths = species_cfg.get("depths", [10, 30])
        bounds_x = self.t["bounds"]["x"]

        for m in sort_by_id(self.monsters):
            state = m["state"]
            if state == "recoil":
                m["state_ticks_left"] -= 1
                recoil_speed = 2.0  # mỗi bước 2/60 m
                rdir = m.get("recoil_dir") or [1.0, 0.0]
                m["pos"][0] += rdir[0] * (recoil_speed / TICK)
                m["pos"][1] += rdir[1] * (recoil_speed / TICK)
                m["pos"][0] = max(bounds_x[0], min(bounds_x[1], m["pos"][0]))
                m["pos"][1] = max(depths[0], min(depths[1], m["pos"][1]))
                if m["state_ticks_left"] <= 0:
                    m["state"] = "patrol"
                    m["recoil_dir"] = None

            elif state == "chase":
                dist_to_p = math.dist(m["pos"], self.pos)
                if dist_to_p > exit_radius or self.pos[1] < depths[0]:
                    m["state"] = "patrol"
                else:
                    dx = self.pos[0] - m["pos"][0]
                    dd = self.pos[1] - m["pos"][1]
                    dist_to_p = math.hypot(dx, dd)
                    if dist_to_p > 0:
                        step_d = min(dist_to_p, chase_speed / TICK)
                        m["pos"][0] += (dx / dist_to_p) * step_d
                        m["pos"][1] += (dd / dist_to_p) * step_d
                    m["pos"][0] = max(bounds_x[0], min(bounds_x[1], m["pos"][0]))
                    m["pos"][1] = max(depths[0], min(depths[1], m["pos"][1]))

            if m["state"] == "patrol":
                dist_to_p = math.dist(m["pos"], self.pos)
                if self.pos[1] >= depths[0] and dist_to_p <= detect_radius:
                    m["state"] = "chase"
                    dx = self.pos[0] - m["pos"][0]
                    dd = self.pos[1] - m["pos"][1]
                    dist_to_p = math.hypot(dx, dd)
                    if dist_to_p > 0:
                        step_d = min(dist_to_p, chase_speed / TICK)
                        m["pos"][0] += (dx / dist_to_p) * step_d
                        m["pos"][1] += (dd / dist_to_p) * step_d
                    m["pos"][0] = max(bounds_x[0], min(bounds_x[1], m["pos"][0]))
                    m["pos"][1] = max(depths[0], min(depths[1], m["pos"][1]))
                else:
                    target = m["waypoints"][m["target_idx"]]
                    dx = target[0] - m["pos"][0]
                    dd = target[1] - m["pos"][1]
                    dist_tgt = math.hypot(dx, dd)
                    step_d = patrol_speed / TICK
                    if dist_tgt <= step_d:
                        m["pos"][0] = target[0]
                        m["pos"][1] = target[1]
                        m["target_idx"] = 1 - m["target_idx"]
                    else:
                        m["pos"][0] += (dx / dist_tgt) * step_d
                        m["pos"][1] += (dd / dist_tgt) * step_d
                    m["pos"][0] = max(bounds_x[0], min(bounds_x[1], m["pos"][0]))
                    m["pos"][1] = max(depths[0], min(depths[1], m["pos"][1]))

    def _check_monster_hit(self, events) -> bool:
        if self.invuln_ticks > 0 or self.pos[1] < 10.0:
            return False

        species_cfg = self.monsters_cfg.get("species", {}).get("ca_sau", {})
        hit_radius = species_cfg.get("hit_radius", 1.5)

        candidates = [m for m in self.monsters
                      if m["state"] != "recoil" and math.dist(self.pos, m["pos"]) <= hit_radius]
        if not candidates:
            return False

        m = min(candidates, key=lambda mon: (math.dist(self.pos, mon["pos"]), id_key(mon["id"])))

        self.hp -= 1
        lost_count = len(self.hold) // 2
        lost = []
        for _ in range(lost_count):
            lost.append(format_item(self.hold.pop()))

        self.invuln_ticks = self.monsters_cfg.get("invuln_ticks", 90)

        events.append(("monster_hit", {
            "monster_id": m["id"],
            "hp": self.hp,
            "lost": lost,
            "pos": list(self.pos),
        }))

        dx = m["pos"][0] - self.pos[0]
        dd = m["pos"][1] - self.pos[1]
        dist_mp = math.hypot(dx, dd)
        if dist_mp == 0:
            recoil_dir = [1.0, 0.0]
        else:
            recoil_dir = [dx / dist_mp, dd / dist_mp]

        m["state"] = "recoil"
        m["state_ticks_left"] = species_cfg.get("recoil_ticks", 60)
        m["recoil_dir"] = recoil_dir

        if self.hp <= 0:
            self._end_current_if_active(events)
            remaining_lost = [format_item(it) for it in reversed(self.hold)]
            self.hold = []
            events.append(("faint", {"cause": "monster", "hp": 0, "lost": remaining_lost}))
            self._finish("fainted", events)
            return True

        return False

    def _fish_spawn_candidates(self):
        x_values = self.t["fish_spawn_x"]
        depths = self.t["fish_spawn_depths"]
        clearance = self.t["fish_spawn_clearance"]
        candidates = {}
        for kind in sorted(self.t["fish_yield"]):
            points = []
            for x in x_values:
                for d in depths[kind]:
                    pos = [float(x), float(d)]
                    if all(math.dist(pos, fish["pos"]) > clearance for fish in self.fish):
                        points.append(pos)
            if points:
                candidates[kind] = points
        return candidates

    def _new_fish(self):
        candidates = self._fish_spawn_candidates()
        if not candidates:
            return None
        kinds = list(candidates)
        weights = [self.t["fish_weights"][kind] for kind in kinds]
        rng = self.rng.get("fish_spawn")
        kind = rng.choices(kinds, weights=weights, k=1)[0]
        pos = rng.choice(candidates[kind])
        return {
            "id": self.ids.new("F"),
            "kind": kind,
            "pos": pos,
            "heading_deg": rng.uniform(0.0, 360.0),
            "age_ticks": 0,
        }

    def _move_fish(self):
        speed = self.t["fish_speed"] / TICK
        turn_ticks = self.t["fish_turn_ticks"]
        turn_rng = self.rng.get("fish_turn")
        x_bounds = self.t["fish_x"]
        for fish in sort_by_id(self.fish):
            fish.setdefault("age_ticks", 0)
            fish["age_ticks"] += 1
            if fish["age_ticks"] % turn_ticks == 0:
                fish["heading_deg"] = turn_rng.uniform(0.0, 360.0)
            self._move_fish_with_reflection(fish, speed, x_bounds, self.t["fish_depths"][fish["kind"]])

    @staticmethod
    def _move_fish_with_reflection(fish, distance, x_bounds, depth_bounds):
        x, d = fish["pos"]
        angle = math.radians(fish["heading_deg"])
        vx, vd = math.cos(angle), math.sin(angle)
        remaining = distance
        epsilon = 1e-12

        for _ in range(8):
            if remaining <= epsilon:
                break
            x_hit = ((x_bounds[1] - x) / vx) if vx > epsilon else (
                (x_bounds[0] - x) / vx if vx < -epsilon else math.inf
            )
            d_hit = ((depth_bounds[1] - d) / vd) if vd > epsilon else (
                (depth_bounds[0] - d) / vd if vd < -epsilon else math.inf
            )
            hit_distance = min(x_hit, d_hit)
            if hit_distance < -epsilon:
                hit_distance = 0.0
            if hit_distance > remaining + epsilon:
                x += vx * remaining
                d += vd * remaining
                remaining = 0.0
                break

            travel = max(0.0, hit_distance)
            x += vx * travel
            d += vd * travel
            remaining = max(0.0, remaining - travel)
            if abs(x_hit - hit_distance) <= epsilon:
                x = x_bounds[1] if vx > 0 else x_bounds[0]
                vx = -vx
            if abs(d_hit - hit_distance) <= epsilon:
                d = depth_bounds[1] if vd > 0 else depth_bounds[0]
                vd = -vd

        fish["pos"] = [x, d]
        fish["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360.0

    def _spawn_fish(self, events):
        spawn_ticks = self.t["fish_spawn_ticks"]
        if (not self.random_fish or self.phase_tick % spawn_ticks != 0
                or len(self.fish) >= self.t["fish_max"]):
            return
        fish = self._new_fish()
        if fish is None:
            return
        self.fish.append(fish)
        events.append(("fish_spawned", {
            "id": fish["id"],
            "kind": fish["kind"],
            "pos": list(fish["pos"]),
        }))
