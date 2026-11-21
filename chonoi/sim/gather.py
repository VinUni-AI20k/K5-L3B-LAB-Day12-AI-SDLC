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
  ĐÃ LÀM (A): `_update_monsters` (Cá Sấu: patrol/chase/recoil, hit, bất tử, ngất do quái).
  8 đàn đầu ca (`_pick_spawn`, `_initial_fish`): A viết để main xanh, B sở hữu (review, test, chỉnh theo clarify).
  ĐÃ LÀM (B): `_fish_swim`, `_spawn_fish` (cá bơi, phản xạ mép, đổi hướng theo seed, nối lịch sinh).
"""

import math

from .. import fresh
from ..contract import upgrade_value
from ..ids import id_key, sort_by_id
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
        self.tuning = tuning  # cần cho chonoi.fresh (khối freshness ở gốc tuning, v1.2)
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
        # v1.2 (khung): fixture hold là cá thể {id, kind, fresh} -> cá thể trong code {id, kind, u}; giữ nguyên id
        self.fresh_on = fresh.enabled(tuning)
        if self.fresh_on:
            self.hold = [fresh.from_public(it) for it in self.hold]
            for it in self.hold:
                ids.reserve(it["id"])
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
    def inventory_items(self):
        """Kho bàn giao khi gather_end: v1.1 dict đếm; v1.2 mảng cá thể public sắp theo id (Ticket-03 mục 1)."""
        if self.fresh_on:
            return fresh.public_list(sort_by_id(self.hold))
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": fresh.out(self.hold), "hold_count": len(self.hold),
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
        if self.fresh_on:
            self._decay_hold(events)  # v1.2 (B): độ tươi của hàng có sẵn trong giỏ, ở đầu bước
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
        events.append(("faint", {"cause": "choke", "lost": fresh.out(lost), "hp": 0}))
        self._finish("fainted", events)
        return True

    # --- v1.2: độ tươi trong giỏ (B viết thân hàm) -------------------------------------
    def _decay_hold(self, events):
        """TODO(B, Ticket-03 mục 1): mỗi bước giỏ hao fresh.cfg(tuning)["gather_decay_u"] (2 đơn vị = 0.5/s);
        với mỗi cá thể vừa ươn (fresh.decay trả theo id) phát spoiled{item_id, kind, location: "hold"}.
        Hàng mới bắt/hái có fresh 100 và hao từ bước sau. Gợi ý:
            for it in fresh.decay(self.hold, fresh.cfg(self.tuning)["gather_decay_u"], self.tuning): ...
        B cũng đổi _try_harvest/_try_catch: khi self.fresh_on thì thêm fresh.new_item(self.ids, kind, tuning)."""

    # --- v1.1: quái (A viết thân hàm) -------------------------------------------------
    def _update_monsters(self, events) -> bool:
        """Quái (Ticket-02 mục 1.2), gọi sau bơi, oxy và ngạt. Trả True nếu người chơi ngất do quái.

        1. Duyệt quái theo id, mỗi con đi một bước theo trạng thái:
           - recoil: lùi recoil_dist / recoil_ticks mét theo hướng đã chốt lúc chạm, rồi chặn; hết đếm thì về
             patrol nhưng chỉ xét phát hiện và chạm từ bước kế.
           - patrol / chase: đổi trạng thái theo vị trí người chơi (phát hiện khi d >= ngưỡng loài và cách
             <= detect_radius; thôi đuổi khi cách > exit_radius hoặc người chơi lên d < ngưỡng), rồi đi:
             patrol về waypoint đích với patrol_speed (tới nơi thì đổi đích cho bước sau), chase về phía người
             chơi với chase_speed.
           - Chặn theo biên map và dải độ sâu `depths` của loài.
        2. Sau khi cả hai đã di chuyển, xét tối đa MỘT hit: con gần nhất (hòa id) trong hit_radius, không ở
           recoil, người chơi ở d >= ngưỡng loài và hết bất tử. Hit: -1 Máu, bỏ floor(số đang mang × loss_ratio)
           nguyên liệu theo LIFO, bất tử invuln_ticks, phát monster_hit, con đó vào recoil từ bước sau.
        3. Máu 0: faint{cause: "monster", lost: phần giỏ còn lại theo LIFO, hp: 0} rồi gather_end(fainted).

        Ngưỡng độ sâu của loài là depths[0] (giả định, docs/contracts/README.md mục 5.6).
        """
        if not self.monsters:
            return False
        cfg = self.t["monsters"]
        species = cfg["species"]
        can_engage = []  # quái được xét chạm ở bước này
        for m in sort_by_id(self.monsters):
            sp = species[m["kind"]]
            if m["state"] == "recoil":
                step = sp["recoil_dist"] / sp["recoil_ticks"]
                m["pos"] = [m["pos"][0] + m["recoil_dir"][0] * step, m["pos"][1] + m["recoil_dir"][1] * step]
                self._clamp_monster(m, sp)
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"], m["state_ticks_left"], m["recoil_dir"] = "patrol", 0, None
                continue
            deep_enough = self.pos[1] >= sp["depths"][0]
            dist = math.dist(m["pos"], self.pos)
            if m["state"] == "patrol" and deep_enough and dist <= sp["detect_radius"]:
                m["state"] = "chase"
            elif m["state"] == "chase" and (not deep_enough or dist > sp["exit_radius"]):
                m["state"] = "patrol"
            if m["state"] == "chase":
                self._move_monster_toward(m, self.pos, sp["chase_speed"] / TICK)
            else:
                target = m["waypoints"][m["target_idx"]]
                if self._move_monster_toward(m, target, sp["patrol_speed"] / TICK):
                    m["target_idx"] = 1 - m["target_idx"]
            self._clamp_monster(m, sp)
            can_engage.append(m)
        # 2. tối đa một hit
        if self.invuln_ticks > 0:
            return False
        hits = [m for m in can_engage
                if self.pos[1] >= species[m["kind"]]["depths"][0]
                and math.dist(m["pos"], self.pos) <= species[m["kind"]]["hit_radius"]]
        if not hits:
            return False
        m = min(hits, key=lambda e: (math.dist(e["pos"], self.pos), id_key(e["id"])))
        sp = species[m["kind"]]
        self.hp = max(0, self.hp - 1)
        n_lost = math.floor(len(self.hold) * cfg["loss_ratio"])
        lost = list(reversed(self.hold[len(self.hold) - n_lost:])) if n_lost else []
        if n_lost:
            self.hold = self.hold[:len(self.hold) - n_lost]
        self.invuln_ticks = int(cfg["invuln_ticks"])
        events.append(("monster_hit", {"monster_id": m["id"], "hp": self.hp, "lost": fresh.out(lost),
                                       "pos": list(self.pos)}))
        dx, dd = m["pos"][0] - self.pos[0], m["pos"][1] - self.pos[1]
        norm = math.hypot(dx, dd)
        m["state"], m["state_ticks_left"] = "recoil", int(sp["recoil_ticks"])
        m["recoil_dir"] = [dx / norm, dd / norm] if norm > 0 else [1.0, 0.0]  # trùng tâm dùng +x
        if self.hp > 0:
            return False
        rest = list(reversed(self.hold))
        self.hold = []
        events.append(("faint", {"cause": "monster", "lost": fresh.out(rest), "hp": 0}))
        self._finish("fainted", events)
        return True

    @staticmethod
    def _move_monster_toward(m, target, step) -> bool:
        """Đi tối đa `step` mét về `target`. Trả True nếu tới đúng đích ở bước này."""
        dx, dd = target[0] - m["pos"][0], target[1] - m["pos"][1]
        dist = math.hypot(dx, dd)
        if dist <= step + 1e-9:  # dung sai cộng dồn dấu phẩy động (240 bước × 1/60 m)
            m["pos"] = [float(target[0]), float(target[1])]
            return True
        m["pos"] = [m["pos"][0] + dx / dist * step, m["pos"][1] + dd / dist * step]
        return False

    def _clamp_monster(self, m, sp):
        """Chặn quái theo biên map và dải độ sâu của loài."""
        bx, bd = self.t["bounds"]["x"], self.t["bounds"]["d"]
        lo, hi = max(bd[0], sp["depths"][0]), min(bd[1], sp["depths"][1])
        m["pos"] = [min(max(m["pos"][0], bx[0]), bx[1]), min(max(m["pos"][1], lo), hi)]

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
        """Cá bơi (Ticket-02 mục 1.1), mỗi bước còn giờ, duyệt đàn theo id: age_ticks += 1; ở bước bơi thứ
        fish_turn_ticks * k đổi hướng theo seed (luồng `fish_turn`) TRƯỚC khi đi; đi fish_speed / 60 m trong
        x thuộc fish_x và dải fish_depths của loài. Tới mép: phản xạ phần quãng còn lại và đảo thành phần
        hướng vuông góc với mép (chạm góc: đảo cả hai); heading_deg cập nhật theo hướng mới."""
        t = self.t
        step = float(t["fish_speed"]) / TICK
        turn = int(t["fish_turn_ticks"])
        xlo, xhi = t["fish_x"]
        rng = self.rng.get("fish_turn")
        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if f["age_ticks"] % turn == 0:
                f["heading_deg"] = rng.uniform(0.0, 360.0)
            a = math.radians(f["heading_deg"])
            dx, dd = math.cos(a) * step, math.sin(a) * step
            dlo, dhi = t["fish_depths"][f["kind"]]
            x, flip_x = _reflect(f["pos"][0] + dx, xlo, xhi)
            d, flip_d = _reflect(f["pos"][1] + dd, dlo, dhi)
            if flip_x or flip_d:
                dx = -dx if flip_x else dx
                dd = -dd if flip_d else dd
                f["heading_deg"] = math.degrees(math.atan2(dd, dx)) % 360.0
            f["pos"] = [x, d]

    def _spawn_fish(self, events):
        """Cá sinh (Ticket-02 mục 1.1): tại phase_tick = fish_spawn_ticks * k (k >= 1), sau khi cá bơi, nếu còn
        dưới fish_max đàn: chọn bằng `_pick_spawn` với luồng `fish_spawn`; hết điểm hợp lệ thì bỏ lượt; có thì
        thêm đàn (id mới, age_ticks 0) và phát fish_spawned{id, kind, pos}. Cá mới bơi từ bước sau."""
        if self.phase_tick % int(self.t["fish_spawn_ticks"]) != 0:
            return
        if len(self.fish) >= int(self.t["fish_max"]):
            return
        pick = self._pick_spawn(self.rng.get("fish_spawn"))
        if pick is None:
            return
        kind, pos, heading = pick
        fid = self.ids.new("F")
        self.fish.append({"id": fid, "kind": kind, "pos": list(pos), "heading_deg": heading, "age_ticks": 0})
        events.append(("fish_spawned", {"id": fid, "kind": kind, "pos": list(pos)}))

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


def _reflect(v, lo, hi):
    """Phản xạ tọa độ `v` vào [lo, hi]: vượt mép thì phần quãng còn lại đi ngược. Trả (giá trị, có đảo hướng)."""
    if v > hi:
        return min(max(2 * hi - v, lo), hi), True
    if v < lo:
        return max(min(2 * lo - v, hi), lo), True
    return v, False
