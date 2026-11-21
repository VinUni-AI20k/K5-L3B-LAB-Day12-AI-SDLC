"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD-0 mục F, "Gather"):
  ĐÃ LÀM (lát 1): `_dive_surface`, `_oxygen_and_choke`
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  ĐÃ LÀM (lát 2): `_try_harvest`, `_try_catch` — hái + bắt cá (cập bến + kho đã có)
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo

v1.1 (Ticket-02, thứ tự một bước theo mục 4.5):
  đồng hồ, cooldown, bất tử, hồi nút -> bơi, oxy, ngạt -> quái theo id rồi tối đa một hit -> tương tác
  (bến trước hái) -> bắt cá theo vị trí cá TRƯỚC khi bơi -> hết giờ -> nếu còn giờ: cá bơi, sinh cá.
  KHUNG (Integrator): `day`, `active_upgrades` (oxy/Máu tối đa theo cấp), quái theo Ngày (`from_day`),
  snapshot `monsters[]`, thứ tự step().
  TODO(A): `_update_monsters` (Cá Sấu: patrol/chase/recoil, hit, bất tử, ngất do quái).
  8 đàn đầu ca (`_pick_spawn`, `_initial_fish`): A viết để main xanh, B sở hữu (review, test, chỉnh theo clarify).
  TODO(B): `_fish_swim`, `_spawn_fish` (cá bơi, phản xạ mép, đổi hướng theo seed, nối lịch sinh).
"""

import math

from ..contract import upgrade_value
from ..ids import sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, active_upgrades=None):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.day = day  # gather độc lập dùng bố trí Ngày 1
        ups = active_upgrades or {}
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(upgrade_value(tuning, "oxygen", ups.get("oxygen", 0), t["oxygen_max_s"]) * TICK))
        self.hp_max = upgrade_value(tuning, "hp", ups.get("hp", 0), t["hp_max"])
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = 0
        # nút, đàn cá, quái: scenario THAY THẾ danh sách mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        # random_fish=false: tắt cá mặc định, bơi và sinh; cá fixture đứng yên (Ticket-02 mục 4.3)
        self.random_fish = scenario.get("random_fish", True)
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0), "age_ticks": f.get("age_ticks", 0)}
                     for f in scenario.get("fish", [])]
        if "monsters" in scenario:
            src_mon = scenario["monsters"]
        else:
            src_mon = [m for m in t["monsters"]["spawns"] if m["from_day"] <= day]
        self.monsters = [{"id": m["id"], "kind": m["kind"], "pos": [float(c) for c in m["pos"]],
                          "waypoints": [[float(c) for c in wp] for wp in m["waypoints"]],
                          "target_idx": m.get("target_idx", 1), "state": m.get("state", "patrol"),
                          "state_ticks_left": m.get("state_ticks_left", 0), "recoil_dir": m.get("recoil_dir")}
                         for m in src_mon]
        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])
        if "fish" not in scenario and self.random_fish:
            self._initial_fish()
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
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      "age_ticks": f["age_ticks"]} for f in sort_by_id(self.fish)],
            "monsters": [{k: m[k] for k in ("id", "kind", "pos", "waypoints", "target_idx", "state",
                                            "state_ticks_left", "recoil_dir")} for m in sort_by_id(self.monsters)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        """Thứ tự theo Ticket-02 mục 4.5. Khung do Integrator cố định; muốn đổi thứ tự gọi thì báo cả nhóm."""
        events = []
        self.phase_tick += 1  # lịch sinh cá dùng phase_tick SAU khi tăng
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 2. bơi + chặn mép, rồi dive/surface và oxy theo d CUỐI bước (lát 1)
        was_surface = self._at_surface()
        self._move(inp)
        self._dive_surface(was_surface, events)
        if self._oxygen_and_choke(events):
            return events  # ngất: đã phát faint + gather_end("fainted"), dừng bước
        # 2b. quái theo id rồi tối đa một hit (v1.1, A); ngạt cùng tick đã xét trước
        if self._update_monsters(events):
            return events  # ngất do quái: đã phát faint + gather_end("fainted")
        # 3. interact: bến trước, rồi hái (lát 2)
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            self._try_harvest(events)
        # 4. bắt cá (lát 2), theo vị trí cá TRƯỚC khi bơi
        if inp.pressed("catch"):
            self._try_catch(events)
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        # 6. còn giờ: cá bơi rồi sinh thêm theo lịch (v1.1, B). random_fish=false thì cá fixture đứng yên.
        if self.random_fish:
            self._fish_swim()
            self._spawn_fish(events)
        return events

    # --- lát 1: dive/surface, oxy, ngạt, Máu, ngất (PRD-0 mục F, Gather bước 2) ---
    def _dive_surface(self, was_surface, events):
        """Phát dive/surface khi đổi phía biên mặt nước (d <= surface_depth là mặt nước). data: pos sau di chuyển."""
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and now_surface:
            events.append(("surface", {"pos": list(self.pos)}))

    def _oxygen_and_choke(self, events) -> bool:
        """Oxy theo d cuối bước, đếm ngạt, trừ Máu. Trả True nếu ngất (buổi sáng kết thúc, dừng bước)."""
        if self._at_surface():
            refill = int(self.t["oxygen_refill_per_tick"])
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + refill)
            self.zero_oxy_ticks = 0
            return False
        before = self.oxygen_ticks
        self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
        if before > 0 and self.oxygen_ticks == 0:
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        if self.oxygen_ticks > 0:
            return False
        # dưới nước, oxy = 0 cuối bước (kể cả bước vừa chạm 0): đếm ngạt
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks < int(self.t["choke_interval_ticks"]):
            return False
        self.zero_oxy_ticks = 0
        self.hp = max(0, self.hp - 1)
        events.append(("choke", {"hp": self.hp}))
        if self.hp > 0:
            return False
        lost = list(reversed(self.hold))  # bỏ theo LIFO: nhặt sau bỏ trước
        self.hold = []
        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
        self._finish("fainted", events)
        return True

    # --- v1.1: quái (A viết thân hàm) -------------------------------------------------
    def _update_monsters(self, events) -> bool:
        """TODO(A, Ticket-02 mục 1.2): duyệt quái theo id: patrol/chase/recoil, chặn theo biên và dải độ sâu loài;
        sau khi cả hai di chuyển xét tối đa một hit (con gần nhất, hòa id): -1 Máu, bỏ floor(n*loss_ratio) theo
        LIFO, invuln_ticks, monster_hit, con đó vào recoil. Máu 0: faint(cause monster) + gather_end(fainted),
        trả True."""
        return False

    # --- v1.1: đàn cá đầu ca (khung) và cá bơi/sinh (B viết thân hàm) -------------------
    # Ghi chú sở hữu: `_pick_spawn` và `_initial_fish` do A (LeBao403, Integrator) viết trong nền v1.1 để main
    # xanh khi `fish_initial` đổi từ danh sách sang số 8. Đây là phần lát của B: B sở hữu đoạn này (review, viết
    # test cho cá, chỉnh lại sau khi có câu trả lời trong docs/clarify.md). Xem docs/contracts/README.md mục 5.6.
    def _pick_spawn(self, rng):
        """Chọn (kind, pos, heading) cho một đàn mới theo luật sinh (Ticket-02 mục 1.1), hoặc None nếu hết điểm.

        Điểm hợp lệ: (x, d) với x thuộc fish_spawn_x, d thuộc fish_spawn_depths của loài, cách mọi đàn đang sống
        > fish_spawn_clearance. Loài chọn theo fish_weights, chuẩn hóa lại trên các loài còn điểm (duyệt loài theo
        id cố định). Sau đó chọn đều một điểm của loài và lấy hướng ban đầu theo seed.
        """
        t = self.t
        live = [f["pos"] for f in self.fish]
        options = {}
        for kind in sorted(t["fish_weights"]):
            pts = [[float(x), float(d)] for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]
                   if all(math.dist((x, d), q) > t["fish_spawn_clearance"] for q in live)]
            if pts:
                options[kind] = pts
        if not options:
            return None
        kinds = list(options)
        r = rng.random() * sum(t["fish_weights"][k] for k in kinds)
        chosen = kinds[-1]
        for k in kinds:
            r -= t["fish_weights"][k]
            if r < 0:
                chosen = k
                break
        pts = options[chosen]
        pos = pts[rng.randrange(len(pts))]
        heading = rng.uniform(0.0, 360.0)
        return chosen, pos, heading

    def _initial_fish(self):
        """Đầu ca: fish_initial (8) đàn ở 8 điểm khác nhau. Giả định (chờ xác nhận trong docs/clarify.md): dùng
        đúng luật sinh lặp fish_initial lần với luồng RNG `fish_init`."""
        rng = self.rng.get("fish_init")
        for _ in range(int(self.t["fish_initial"])):
            pick = self._pick_spawn(rng)
            if pick is None:
                break
            kind, pos, heading = pick
            self.fish.append({"id": self.ids.new("F"), "kind": kind, "pos": pos, "heading_deg": heading,
                              "age_ticks": 0})

    def _fish_swim(self):
        """TODO(B, Ticket-02 mục 1.1): mỗi đàn bơi fish_speed trong x thuộc fish_x và dải fish_depths của loài.
        Ở bước bơi thứ fish_turn_ticks * k (theo age_ticks) đổi hướng theo seed (luồng `fish_turn`) TRƯỚC khi
        di chuyển. Tới mép: phản xạ phần quãng còn lại, đảo thành phần hướng vuông góc với mép (góc: đảo cả hai).
        Tăng age_ticks mỗi bước bơi."""

    def _spawn_fish(self, events):
        """TODO(B, Ticket-02 mục 1.1): tại phase_tick = fish_spawn_ticks * k (k >= 1), sau khi cá bơi, nếu còn
        dưới fish_max: pick = self._pick_spawn(self.rng.get("fish_spawn")); None thì bỏ lượt; có thì thêm đàn id
        self.ids.new("F"), age_ticks 0, phát fish_spawned{id, kind, pos}. Cá mới tham gia từ bước sau."""

    # --- lát 2: hái, bắt cá (B viết thân hàm) ---------------------------------------
    def _try_harvest(self, events):
        """Hái nút (lát 2 - B): chỉ ở mặt nước. Nút ready gần nhất trong interact_radius (hòa: id nhỏ).
        Đủ chỗ: thêm node_yield vào cuối hold, regrow_ticks = regrow_s*60, phát gather{node_id,kind,amount}.
        Thiếu chỗ: hold_full{action:"gather",node_id,required,free}, nút giữ nguyên."""
        if not self._at_surface():
            return
        node = self._nearest([n for n in self.nodes if n["regrow_ticks"] == 0], self.t["interact_radius"])
        if node is None:
            return
        amount = int(self.t["node_yield"])
        free = self._hold_free()
        if amount > free:
            events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                         "required": amount, "free": free}))
            return
        self.hold.extend([node["kind"]] * amount)
        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": amount}))

    def _try_catch(self, events):
        """Bắt cá (lát 2 - B): chỉ khi catch_cd_ticks == 0 và dưới nước. Đàn gần nhất trong catch_radius
        (hòa: id nhỏ). Đủ chỗ cho cả fish_yield: thêm vào hold, xóa đàn, fish_caught{fish_id,kind,yield},
        catch_cd_ticks = catch_cooldown_s*60. Thiếu chỗ: hold_full{action:"catch",fish_id,required,free},
        giữ đàn, không đặt hồi chiêu, không thử đàn khác. Không có đàn trong tầm: không làm gì."""
        if self.catch_cd_ticks > 0 or self._at_surface():
            return
        fish = self._nearest(self.fish, self.t["catch_radius"])
        if fish is None:
            return
        amount = int(self.t["fish_yield"][fish["kind"]])
        free = self._hold_free()
        if amount > free:
            events.append(("hold_full", {"action": "catch", "fish_id": fish["id"],
                                         "required": amount, "free": free}))
            return
        self.hold.extend([fish["kind"]] * amount)
        self.fish.remove(fish)
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": amount}))

    def _hold_free(self) -> int:
        return int(self.t["hold_capacity"]) - len(self.hold)

    def _nearest(self, candidates, radius):
        """Phần tử gần người chơi nhất trong `radius` (tính cả mép); hòa khoảng cách thì id nhỏ hơn."""
        best = None
        for e in sort_by_id(candidates):  # đã sắp theo id nên `<` nghiêm ngặt giữ id nhỏ khi hòa
            d = math.dist(self.pos, e["pos"])
            if d <= radius and (best is None or d < best[0]):
                best = (d, e)
        return best[1] if best else None

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
