"""Buổi sáng — Lặn & Hái (`gather`). Hỗ trợ Contract v1.0 và v1.1.

Mặt cắt dòng sông nhìn NGANG: vị trí [x, d] (x sang phải, d độ sâu hướng xuống, d=0 là mặt nước).
move = [x, d]: thành phần thứ hai DƯƠNG = bơi xuống.

Lát 1: bơi, oxy, dive/surface, ngạt (choke), faint, giỏ LIFO.
Lát 2: hái nút mặt nước (N1..N6), bắt cá dưới nước (linh, lóc, kèo), cá bơi và sinh cá theo lịch, cập bến, ghi kho.

v1.2: giỏ là mảng cá thể {id, kind, fresh} (fresh là Fraction trong sim), hao 0.5/s, ươn < 30.

Thứ tự xử lý mỗi bước (PRD Phase 2 mục 4.5, Phase 3 mục 1):
  1. Giảm đồng hồ, timer, nút mọc lại, giảm cooldown và bất tử; hao tươi hàng có sẵn → spoiled.
  2. Bơi + chặn biên, so vị trí đầu/cuối → dive/surface.
  3. Tính oxy theo d cuối bước → oxygen_empty, choke, faint.
  4. Cập nhật quái (Cá Sấu) theo id rồi xét tối đa một hit → monster_hit/faint.
  5. interact: bến trước → docked; ngoài bến + mặt nước → hái.
  6. catch: dưới nước + hết hồi → bắt cá (theo vị trí cá trước khi bơi).
  7. Hết giờ → time.
  8. Nếu còn giờ: cá bơi, sinh cá theo lịch (phase_tick = 360*k).
"""

import math
from fractions import Fraction

from ..ids import sort_by_id
from ..inventory import item_out, items_out
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")

FISH_BOUNDS_X = (4.0, 96.0)
FISH_DEPTHS = {
    "ca_linh": (3.0, 12.0),
    "ca_loc": (8.0, 20.0),
    "ca_keo": (22.0, 28.0),
}
SPAWN_X = [15.0, 30.0, 45.0, 60.0, 75.0, 90.0]
SPAWN_DEPTHS = {
    "ca_linh": [5.0, 10.0],
    "ca_loc": [10.0, 16.0],
    "ca_keo": [24.0, 27.0],
}
SPECIES_WEIGHTS = {
    "ca_linh": 0.4,
    "ca_loc": 0.3,
    "ca_keo": 0.3,
}
DEFAULT_FISH_YIELD = {
    "ca_linh": 3,
    "ca_loc": 1,
    "ca_keo": 2,
}


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.phase_tick = int(scenario.get("phase_tick", 0))
        self.random_fish = bool(scenario.get("random_fish", True))
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
        # v1.2: giỏ là mảng cá thể; thứ tự mảng = thứ tự vào giỏ (LIFO: cuối mảng = mới nhất).
        # scenario.load_scenario đã đổi fresh sang Fraction; id I.. giữ chỗ để cấp tiếp.
        fr = tuning["freshness"]
        self.fresh_initial = Fraction(str(fr["initial"]))
        self.spoiled_below = Fraction(str(fr["spoiled_below"]))
        self.fresh_decay = Fraction(str(fr["gather_decay_per_s"])) / int(TICK)  # mỗi tick
        self.hold = [dict(it) for it in scenario.get("hold", [])]
        for it in self.hold:
            ids.reserve(it["id"])
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))

        # Nút hái
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]

        # Đàn cá ban đầu
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif self.random_fish:
            initial_def = t.get("fish_initial")
            if isinstance(initial_def, list):
                src_fish = initial_def
            else:
                src_fish = self._generate_initial_fish(int(initial_def) if initial_def else 8)
        else:
            src_fish = []

        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": float(f.get("heading_deg", 0.0)),
                      "age_ticks": int(f.get("age_ticks", 0))} for f in src_fish]

        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])

        # v1.1: Cá Sấu Năm Chèo — gather độc lập dùng bố trí Ngày 1 (from_day <= 1);
        # scenario gather.monsters[] thay danh sách mặc định (PRD mục D, 1.2).
        mconf = t.get("monsters", {})
        self.monster_species = mconf.get("species", {})
        self.monster_cfg = mconf
        if "monsters" in scenario:
            src_monsters = scenario["monsters"]
        else:
            src_monsters = [s for s in mconf.get("spawns", []) if int(s.get("from_day", 1)) <= 1]
        self.monsters = [{
            "id": s["id"], "kind": s["kind"],
            "pos": [float(c) for c in s["pos"]],
            "waypoints": [[float(c) for c in wp] for wp in s.get("waypoints", [s["pos"], s["pos"]])],
            "target_idx": int(s.get("target_idx", 1)),
            "state": s.get("state", "patrol"),
            "state_ticks_left": int(s.get("state_ticks_left", 0)),
            "recoil_dir": s.get("recoil_dir"),
        } for s in src_monsters]
        for m in self.monsters:
            ids.reserve(m["id"])

        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    def _generate_initial_fish(self, count):
        """Đầu ca sinh `count` đàn (chuẩn 8) ở các điểm khác nhau."""
        spawn_xs = self.t.get("fish_spawn_x", SPAWN_X)
        spawn_ds_map = self.t.get("fish_spawn_depths", SPAWN_DEPTHS)
        weights_map = self.t.get("fish_weights", SPECIES_WEIGHTS)
        rng = self.rng.get("fish_spawn")

        initial_fish = []
        occupied_points = set()

        for _ in range(count):
            valid_points_by_species = {}
            for kind in ("ca_linh", "ca_loc", "ca_keo"):
                depths = spawn_ds_map.get(kind, [])
                valid_pts = []
                for sx in spawn_xs:
                    for sd in depths:
                        pt_key = (float(sx), float(sd))
                        if pt_key not in occupied_points:
                            valid_pts.append([float(sx), float(sd)])
                if valid_pts:
                    valid_points_by_species[kind] = valid_pts

            if not valid_points_by_species:
                break

            available = [k for k in ("ca_linh", "ca_loc", "ca_keo") if k in valid_points_by_species]
            weights = [weights_map.get(k, 1.0) for k in available]
            total_w = sum(weights)
            r = rng.random() * total_w
            acc = 0.0
            chosen_kind = available[-1]
            for sp, w in zip(available, weights):
                acc += w
                if r <= acc:
                    chosen_kind = sp
                    break

            pts = valid_points_by_species[chosen_kind]
            pts.sort(key=lambda p: (p[0], p[1]))
            chosen_pt = pts[int(rng.random() * len(pts))]
            occupied_points.add((chosen_pt[0], chosen_pt[1]))

            heading = rng.uniform(0, 360)
            fish_id = self.ids.new("F")
            initial_fish.append({
                "id": fish_id,
                "kind": chosen_kind,
                "pos": chosen_pt,
                "heading_deg": heading,
                "age_ticks": 0,
            })
        return initial_fish

    # --- giao diện cho runner ---------------------------------------------------
    def inventory_items(self) -> list:
        return self.hold

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": [item_out(it) for it in self.hold], "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                       "age_ticks": f.get("age_ticks", 0)}
                      for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "kind": m["kind"], "pos": m["pos"], "waypoints": m["waypoints"],
                          "target_idx": m["target_idx"], "state": m["state"],
                          "state_ticks_left": m["state_ticks_left"], "recoil_dir": m["recoil_dir"]}
                         for m in sort_by_id(self.monsters)],
        }

    # --- một bước (PRD-0 mục F & Phase 2 mục 4.5) -------------------------------
    def step(self, inp):
        events = []
        self.phase_tick += 1

        # ── 1. Đồng hồ, timer, nút mọc lại ─────────────────────────────────────
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        self._decay_hold(events)

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
                        self._faint(events, "choke")
                        return events

        # ── 4. v1.1: cập nhật quái theo id rồi xét tối đa một hit (mục 1.2, 4.5) ─
        just_recoiled = set()
        for m in sort_by_id(self.monsters):
            if self._update_monster(m):
                just_recoiled.add(m["id"])  # hết recoil đúng bước này: xét chạm từ bước kế
        if self._monster_hit(events, just_recoiled):
            return events

        # ── 5. Lát 2: interact — bến trước, rồi hái ─────────────────────────────
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
                            self._add_item(node["kind"])
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {
                            "node_id": node["id"],
                            "kind": node["kind"],
                            "amount": amount,
                        }))

        # ── 6. Lát 2: catch — chỉ dưới nước, hết hồi chiêu ─────────────────────
        # (Thực hiện theo vị trí cá TRƯỚC khi cá bơi ở bước này)
        if inp.pressed("catch"):
            if not self._at_surface() and self.catch_cd_ticks == 0:
                fish = self._nearest_fish()
                if fish is not None:
                    cap = self.t["hold_capacity"]
                    fy_map = self.t.get("fish_yield", DEFAULT_FISH_YIELD)
                    yield_count = int(fy_map.get(fish["kind"], DEFAULT_FISH_YIELD.get(fish["kind"], 1)))
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
                            self._add_item(fish["kind"])
                        self.fish.remove(fish)
                        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                        events.append(("fish_caught", {
                            "fish_id": fish["id"],
                            "kind": fish["kind"],
                            "yield": yield_count,
                        }))

        # ── 7. Hết giờ ──────────────────────────────────────────────────────────
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events

        # ── 8. Cá bơi & Sinh cá theo lịch (khi ca còn tiếp tục) ─────────────────
        self._move_fish()
        self._spawn_fish(events)

        return events

    def _move_fish(self):
        """Đàn cá bơi 1.5 m/s, đổi hướng ở bước 120, 240..., phản xạ mép."""
        if not self.random_fish:
            return

        speed = float(self.t.get("fish_speed", 1.5))
        ds = speed / TICK
        x_bounds = self.t.get("fish_x", FISH_BOUNDS_X)
        depths_map = self.t.get("fish_depths", FISH_DEPTHS)
        turn_interval = int(self.t.get("fish_turn_ticks", 120))

        for f in sort_by_id(self.fish):
            f["age_ticks"] = f.get("age_ticks", 0) + 1
            if f["age_ticks"] % turn_interval == 0:
                f["heading_deg"] = self.rng.get("fish_heading").uniform(0, 360)

            rad = math.radians(f["heading_deg"])
            dx = ds * math.cos(rad)
            dd = ds * math.sin(rad)

            x, d = f["pos"]
            x_min, x_max = x_bounds
            d_min, d_max = depths_map.get(f["kind"], (3.0, 28.0))

            new_x = x + dx
            if new_x < x_min:
                new_x = 2 * x_min - (x + dx)
                dx = -dx
            elif new_x > x_max:
                new_x = 2 * x_max - (x + dx)
                dx = -dx

            new_d = d + dd
            if new_d < d_min:
                new_d = 2 * d_min - (d + dd)
                dd = -dd
            elif new_d > d_max:
                new_d = 2 * d_max - (d + dd)
                dd = -dd

            f["heading_deg"] = math.degrees(math.atan2(dd, dx)) % 360
            f["pos"] = [max(x_min, min(x_max, new_x)), max(d_min, min(d_max, new_d))]

    def _spawn_fish(self, events):
        """Sinh tối đa 1 đàn tại phase_tick = 360*k nếu dưới trần và có điểm cách đàn khác > 1m."""
        if not self.random_fish:
            return
        spawn_ticks = int(self.t.get("fish_spawn_ticks", 360))
        if self.phase_tick <= 0 or self.phase_tick % spawn_ticks != 0:
            return

        max_fish = int(self.t.get("fish_max", 12))
        if len(self.fish) >= max_fish:
            return

        clearance = float(self.t.get("fish_spawn_clearance", 1.0))
        spawn_xs = self.t.get("fish_spawn_x", SPAWN_X)
        spawn_ds_map = self.t.get("fish_spawn_depths", SPAWN_DEPTHS)
        weights_map = self.t.get("fish_weights", SPECIES_WEIGHTS)

        valid_points_by_species = {}
        for kind in ("ca_linh", "ca_loc", "ca_keo"):
            depths = spawn_ds_map.get(kind, [])
            valid_pts = []
            for sx in spawn_xs:
                for sd in depths:
                    pt = [float(sx), float(sd)]
                    if all(math.dist(pt, f["pos"]) > clearance for f in self.fish):
                        valid_pts.append(pt)
            if valid_pts:
                valid_points_by_species[kind] = valid_pts

        if not valid_points_by_species:
            return

        available = [k for k in ("ca_linh", "ca_loc", "ca_keo") if k in valid_points_by_species]
        weights = [weights_map.get(k, 1.0) for k in available]
        total_w = sum(weights)

        rng = self.rng.get("fish_spawn")
        r = rng.random() * total_w
        acc = 0.0
        chosen_kind = available[-1]
        for sp, w in zip(available, weights):
            acc += w
            if r <= acc:
                chosen_kind = sp
                break

        pts = valid_points_by_species[chosen_kind]
        pts.sort(key=lambda p: (p[0], p[1]))
        chosen_pt = pts[int(rng.random() * len(pts))]

        heading = rng.uniform(0, 360)
        new_id = self.ids.new("F")

        new_fish = {
            "id": new_id,
            "kind": chosen_kind,
            "pos": chosen_pt,
            "heading_deg": heading,
            "age_ticks": 0,
        }
        self.fish.append(new_fish)
        events.append(("fish_spawned", {"id": new_id, "kind": chosen_kind, "pos": list(chosen_pt)}))

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

    # --- v1.2: độ tươi giỏ (Phase 3 mục 1) ----------------------------------------
    def _add_item(self, kind):
        """Hàng mới: id I.. tăng theo thứ tự vào giỏ, fresh = initial, hao từ bước sau."""
        self.hold.append({"id": self.ids.new("I"), "kind": kind, "fresh": self.fresh_initial})

    def _decay_hold(self, events):
        """Giỏ giảm gather_decay_per_s, kẹp đáy 0; spoiled đúng một lần khi đi từ >= 30
        xuống < 30, nhiều cá thể thì theo id."""
        for it in sort_by_id(self.hold):
            before = it["fresh"]
            it["fresh"] = max(Fraction(0), before - self.fresh_decay)
            if before >= self.spoiled_below > it["fresh"]:
                events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "hold"}))

    # --- v1.1: Cá Sấu Năm Chèo (mục 1.2) ------------------------------------------
    def _monster_zone(self, m):
        """Miền chặn của quái: biên map x + dải độ sâu của loài; ngưỡng sâu = mép dải."""
        sp = self.monster_species.get(m["kind"], {})
        xlo, xhi = self.t["bounds"]["x"]
        dlo, dhi = sp.get("depths", (10.0, 30.0))
        return float(xlo), float(xhi), float(dlo), float(dhi)

    def _update_monster(self, m):
        """Di chuyển một con quái (patrol/chase/recoil). Trả True nếu nó vừa HẾT recoil
        đúng bước này (không xét phát hiện/chạm ở bước đó — PRD 'xét ... từ bước kế')."""
        sp = self.monster_species.get(m["kind"], {})
        xlo, xhi, dlo, dhi = self._monster_zone(m)
        if m["state"] == "recoil":
            if m["state_ticks_left"] > 0:
                step = float(sp.get("recoil_dist", 2.0)) / TICK  # mỗi bước recoil_dist/60 m
                direction = m["recoil_dir"] or [1.0, 0.0]
                self._move_entity(m["pos"], direction, step, xlo, xhi, dlo, dhi)
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"] = "patrol"
                    m["recoil_dir"] = None
                    return True
            return False
        dist_player = math.dist(m["pos"], self.pos)
        if m["state"] == "chase":
            # Trở về patrol khi cách > exit_radius hoặc người chơi lên trên dải sâu
            if dist_player > float(sp.get("exit_radius", 16.0)) or self.pos[1] < dlo:
                m["state"] = "patrol"
        elif (self.pos[1] >= dlo and dist_player <= float(sp.get("detect_radius", 10.0))):
            m["state"] = "chase"
        if m["state"] == "chase":
            step = float(sp.get("chase_speed", 3.0)) / TICK
            dx, dd = self.pos[0] - m["pos"][0], self.pos[1] - m["pos"][1]
            norm = math.hypot(dx, dd) or 1.0
            self._move_entity(m["pos"], [dx / norm, dd / norm], step, xlo, xhi, dlo, dhi)
        else:
            # patrol: tới waypoint hiện tại, đến thì đổi mục tiêu cho bước sau
            tgt = m["waypoints"][m["target_idx"]]
            step = float(sp.get("patrol_speed", 1.0)) / TICK
            dx, dd = tgt[0] - m["pos"][0], tgt[1] - m["pos"][1]
            dist_t = math.hypot(dx, dd)
            if dist_t <= step + 1e-9:  # dung sai cộng dồn float: 240 bước × 1/60 phải chạm đúng 4 m
                m["pos"] = list(tgt)
                m["target_idx"] = 1 - m["target_idx"]
            else:
                self._move_entity(m["pos"], [dx / dist_t, dd / dist_t], step, xlo, xhi, dlo, dhi)
        return False

    def _monster_hit(self, events, just_recoiled):
        """Tối đa MỘT hit mỗi bước: con gần nhất trong hit_radius, hòa theo id; người chơi
        phải ở dải sâu và hết bất tử; con đang recoil (hoặc vừa hết) không gây hit.
        Trả True nếu người chơi ngất (đã phát faint + gather_end)."""
        if self.invuln_ticks > 0 or not self.monsters:
            return False
        best, best_dist = None, None
        for m in sort_by_id(self.monsters):
            if m["state"] == "recoil" or m["id"] in just_recoiled:
                continue  # đang lùi / vừa hết lùi: không gây hit
            sp = self.monster_species.get(m["kind"], {})
            d = math.dist(self.pos, m["pos"])
            dlo, _ = self._monster_zone(m)[2:]
            if d > float(sp.get("hit_radius", 1.5)) or self.pos[1] < dlo:
                continue
            if best is None or d < best_dist:
                best, best_dist = m, d
            elif d == best_dist and m["id"] < best["id"]:
                best, best_dist = m, d
        if best is None:
            return False
        sp = self.monster_species.get(best["kind"], {})
        self.hp -= 1
        # bỏ floor(số đang mang × loss_ratio) nguyên liệu theo LIFO (nhặt sau mất trước)
        drop = math.floor(len(self.hold) * float(self.monster_cfg.get("loss_ratio", 0.5)))
        lost = [self.hold.pop() for _ in range(drop)]
        self.invuln_ticks = int(self.monster_cfg.get("invuln_ticks", 90))
        # recoil 60 bước tính từ bước sau, lùi theo hướng xa người chơi chốt lúc chạm
        best["state"] = "recoil"
        best["state_ticks_left"] = int(sp.get("recoil_ticks", 60))
        dx, dd = best["pos"][0] - self.pos[0], best["pos"][1] - self.pos[1]
        norm = math.hypot(dx, dd)
        if norm == 0:
            dx, dd, norm = 1.0, 0.0, 1.0  # trùng tâm dùng +x
        best["recoil_dir"] = [dx / norm, dd / norm]
        events.append(("monster_hit", {"monster_id": best["id"], "hp": self.hp,
                                       "lost": [item_out(it) for it in lost], "pos": list(self.pos)}))
        if self.hp <= 0:
            self._faint(events, "monster")
            return True
        return False

    def _move_entity(self, pos, direction, step, xlo, xhi, dlo, dhi):
        """Di chuyển thẳng theo vector đơn vị rồi chặn biên map + dải sâu của loài."""
        pos[0] += direction[0] * step
        pos[1] += direction[1] * step
        pos[0] = min(max(pos[0], xlo), xhi)
        pos[1] = min(max(pos[1], dlo), dhi)

    def _faint(self, events, cause):
        """Máu về 0: bỏ giỏ LIFO, phát faint (cause choke|monster) rồi gather_end kho rỗng.
        lost là mảng cá thể v1.2 (test so luật qua kinds())."""
        lost = [item_out(self.hold.pop()) for _ in range(len(self.hold))]  # LIFO
        events.append(("faint", {"cause": cause, "lost": lost, "hp": 0}))
        self._finish("fainted", events)

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        inv = {"items": [] if reason == "fainted" else items_out(self.hold)}
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
