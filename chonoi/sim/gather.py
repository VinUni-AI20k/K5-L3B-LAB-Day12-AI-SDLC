"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Luật của nhóm theo DocsPhase.txt (PRD-0 mục F "Gather", payload event theo mục E), đúng thứ tự một bước:
  - đã làm: dive / surface khi đổi phía biên mặt nước giữa đầu và cuối bước (pos sau di chuyển); oxy theo d
    CUỐI bước (mặt nước hồi oxygen_refill_per_tick + reset ngạt, dưới nước -1, kẹp [0, max]), oxygen_empty,
    đếm ngạt kể cả bước vừa chạm 0 -> đủ choke_interval_ticks thì -1 Máu (choke)
  - đã làm: Máu về 0 -> bỏ giỏ LIFO, faint {cause, lost, hp}, gather_end reason `fainted` với kho rỗng, dừng
    bước (ngất đi trước cập bến và hết giờ cùng bước)
  - đã làm: cập bến xét TRƯỚC hái; hái nút ready gần nhất trong interact_radius chỉ ở mặt nước (gather /
    hold_full, đặt regrow_ticks); bắt đúng đàn gần nhất trong catch_radius khi hết hồi và dưới nước
    (fish_caught / hold_full, đặt hồi chiêu); hòa khoảng cách theo id; lấy đủ yield hoặc giữ nguyên, không thử
    ứng viên khác; giỏ theo thứ tự nhặt, sức chứa hold_capacity; ghi kho đúng một lần do runner lo
  - có sẵn: hết giờ -> gather_end reason `time` ở mọi độ sâu, sau các hành động hợp lệ của bước, giữ giỏ

v1.1 (Ticket-02 mục 1.1, Test Contract 4.5), bật khi tuning có số liệu cá bơi (`fish_speed`); tuning v1.0 giữ nguyên
luật P1 (đàn đứng yên):
  - `fish_initial` là SỐ đàn sinh theo seed ở các điểm sinh khác nhau (loài theo trọng số, điểm chọn đều, hướng theo seed)
  - random_fish bật: bắt cá dùng vị trí cá TRƯỚC khi bơi; nếu còn giờ, mọi đàn bơi fish_speed theo id (đổi hướng theo
    seed ở bước bơi thứ fish_turn_ticks·k trước khi di chuyển; tới mép miền x / dải độ sâu loài thì phản xạ phần
    quãng đường còn lại và đảo thành phần vuông góc), rồi tại phase_tick = fish_spawn_ticks·k sinh tối đa một đàn
    (fish_spawned) nếu dưới fish_max và còn điểm cách mọi đàn > fish_spawn_clearance; cá mới bơi từ bước sau
  - random_fish=false: cá fixture đứng yên, không bơi, không sinh
  - thủy quái (Ticket-02 mục 1.2), bật khi tuning có `monsters`: bố trí theo Ngày (`from_day`, gather độc lập = Ngày
    1) hoặc scenario.monsters. Sau ngạt, cập nhật quái theo id: recoil lùi recoil_dist/recoil_ticks mỗi bước theo hướng
    đã chốt; patrol tới waypoint (tới thì bước sau đổi waypoint), chuyển chase khi người chơi ở d >= ngưỡng độ sâu
    loài và cách <= detect_radius, về patrol khi cách > exit_radius hoặc người chơi lên trên ngưỡng; chặn theo biên
    map và dải độ sâu loài. Rồi tối đa một hit (con gần nhất, hòa theo id, cách <= hit_radius, người chơi dưới ngưỡng,
    hết bất tử): -1 Máu, rơi floor(n·loss_ratio) theo LIFO, bất tử invuln_ticks, con gây hit recoil từ bước sau,
    monster_hit; Máu 0 -> faint cause "monster" với phần giỏ còn lại, gather_end(fainted). Ngạt xuyên bất tử.
"""

import bisect
import math
from itertools import repeat

from ..freshness import age_items, new_item, parse_items, view_items
from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items, inventory_kinds
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")
ARRIVE_EPS = 1e-9  # dung sai khi coi quái đã tới đích: cộng dồn float làm tới trễ 1 bước so với toán học


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, *, day=1):
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
        self.freshness = tuning.get("freshness")
        self.tick_hz = tuning["tick_hz"]
        hold = scenario.get("hold", [])
        self.hold = parse_items(hold, inventory_kinds(tuning)) if self.freshness else list(hold)
        if self.freshness:
            for item in self.hold:
                ids.reserve(item["id"])
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        # v1.1 (tuning có số liệu cá bơi): fish_initial là SỐ đàn sinh theo seed, không phải danh sách
        self._fish_v11 = "fish_speed" in t
        random_fish = scenario.get("random_fish", True)
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif random_fish and not self._fish_v11:
            src_fish = t["fish_initial"]
        else:
            src_fish = []
        # v1.0: đàn cá đứng yên. v1.1: bơi và sinh khi random_fish bật (xem _fish_tick). Luôn sắp theo id.
        self.fish = sort_by_id([{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                                 "heading_deg": f.get("heading_deg", 0), "age_ticks": f.get("age_ticks", 0)}
                                for f in src_fish])
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None
        # hằng luật đọc từ contract MỘT lần (không literal, không tra lại mỗi tick)
        self._refill = t["oxygen_refill_per_tick"]
        self._choke_every = t["choke_interval_ticks"]
        self._cap = t["hold_capacity"]
        self._node_yield = t["node_yield"]
        self._fish_yield = t["fish_yield"]
        self._r_interact = t["interact_radius"]
        self._r_catch = t["catch_radius"]
        self._regrow_full = int(round(t["regrow_s"] * TICK))
        self._catch_cd_full = int(round(t["catch_cooldown_s"] * TICK))
        # thủy quái (v1.1): scenario.monsters thay bố trí mặc định; bỏ mảng thì dùng bố trí đúng Ngày
        rules = t.get("monsters")
        self._has_monsters = rules is not None
        self.monsters = []
        if self._has_monsters:
            src = scenario["monsters"] if "monsters" in scenario else [
                m for m in rules["spawns"] if m.get("from_day", 1) <= day]
            self.monsters = sort_by_id([{
                "id": m["id"], "kind": m["kind"], "pos": [float(c) for c in m["pos"]],
                "waypoints": [[float(c) for c in w] for w in m["waypoints"]], "target_idx": m.get("target_idx", 1),
                "state": m.get("state", "patrol"), "state_ticks_left": m.get("state_ticks_left", 0),
                "recoil_dir": m.get("recoil_dir")} for m in src])
            for m in self.monsters:
                ids.reserve(m["id"])
            bx, bd = t["bounds"]["x"], t["bounds"]["d"]
            self._mon = {}  # số liệu mỗi loài đọc MỘT lần: bước đi theo tick, ngưỡng độ sâu, miền chặn
            for kind, sp in rules["species"].items():
                lo, hi = sp["depths"]
                self._mon[kind] = {"patrol": sp["patrol_speed"] / TICK, "chase": sp["chase_speed"] / TICK,
                                   "recoil": sp["recoil_dist"] / sp["recoil_ticks"], "recoil_ticks": sp["recoil_ticks"],
                                   "detect": sp["detect_radius"], "exit": sp["exit_radius"], "hit": sp["hit_radius"],
                                   "depth": lo,
                                   "lim": tuple(map(float, (bx[0], bx[1], max(bd[0], lo), min(bd[1], hi))))}
            self._invuln_full = rules["invuln_ticks"]
            self._loss_ratio = rules["loss_ratio"]
        # lịch theo phase_tick SAU khi tăng ở đầu bước (mục F), kể cả khi scenario rút ngắn ca
        self._phase_tick = 0
        self._swim = self._fish_v11 and random_fish
        if self._swim:
            self._fish_step = t["fish_speed"] / TICK
            self._turn_every = t["fish_turn_ticks"]
            self._fish_max = t["fish_max"]
            self._spawn_every = t["fish_spawn_ticks"]
            self._clearance = t["fish_spawn_clearance"]
            self._fish_x = t["fish_x"]
            self._fish_depths = t["fish_depths"]
            self._fish_weights = t["fish_weights"]
            self._fish_kinds = sorted(self._fish_weights)  # thứ tự cố định theo id loài
            self._spawn_points = {k: sorted((float(x), float(d)) for x in t["fish_spawn_x"]
                                            for d in t["fish_spawn_depths"][k]) for k in self._fish_kinds}
            self._rng_turn = streams.get("fish_turn")
            self._rng_spawn = streams.get("fish_spawn")
            for f in self.fish:
                self._set_heading(f, f["heading_deg"])
            if "fish" not in scenario:  # đầu ca: fish_initial đàn ở các điểm khác nhau, không phát event
                for _ in range(t["fish_initial"]):
                    if self._spawn_one() is None:
                        break

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self):
        if self.freshness:
            return [item.copy() for item in sort_by_id(self.hold)]
        return hold_to_items(self.hold)

    def _hold_view(self, items):
        return view_items(items, self.freshness["spoiled_below"]) if self.freshness else list(items)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self._hold_view(self.hold), "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [self._fish_view(f) for f in sort_by_id(self.fish)],
            **({"monsters": [{k: m[k] for k in ("id", "kind", "pos", "waypoints", "target_idx", "state",
                                                  "state_ticks_left", "recoil_dir")} for m in self.monsters]}
               if self._has_monsters else {}),
        }

    def _fish_view(self, f) -> dict:
        """Trường đàn cá trong snapshot: {id, pos, kind, heading_deg}; v1.1 thêm age_ticks (mục 4.3)."""
        view = {"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
        if self._fish_v11:
            view["age_ticks"] = f["age_ticks"]
        return view

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self._phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        if self.freshness:
            events.extend(age_items(self.hold, self.freshness["gather_decay_per_s"], self.tick_hz,
                                    self.freshness["spoiled_below"], "hold"))
        # 2. bơi + chặn mép; so phía biên mặt nước đầu/cuối bước -> dive / surface (pos sau di chuyển)
        was_surface = self._at_surface()
        self._move(inp)
        surface = self._at_surface()
        if surface != was_surface:
            # chép giá trị: self.pos đổi tại chỗ ở bước sau, chonoi.live giữ event theo tham chiếu
            events.append(("surface" if surface else "dive", {"pos": list(self.pos)}))
        # oxy theo d CUỐI bước -> oxygen_empty, ngạt (choke); Máu 0 -> ngất, dừng bước
        if self._breathe(surface, events):
            return events
        # thủy quái (v1.1): cập nhật theo id rồi tối đa một hit; Máu 0 -> ngất, dừng bước
        if self.monsters and self._monsters_step(events):
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if surface:  # ngoài bến chỉ hái khi ở mặt nước
                self._gather_node(events)
        # 4. bắt cá: chỉ khi hết hồi và đang dưới nước
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not surface:
            self._catch_fish(events)
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        # 6. còn giờ (v1.1): cá bơi (bắt cá ở trên đã dùng vị trí trước khi bơi), rồi sinh thêm theo lịch
        if self._swim:
            self._fish_tick(events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        items = self.inventory_items()
        if self.freshness:
            items = self._hold_view(items)
        events.append(("gather_end", {"reason": reason, "inventory": {"items": items}}))

    def _breathe(self, surface, events) -> bool:
        """Oxy theo d CUỐI bước (PRD-0 mục F): mặt nước hồi và reset ngạt; dưới nước trừ 1, kẹp 0.

        Mỗi bước dưới nước kết thúc với oxy 0, kể cả bước vừa chạm 0, tăng zero_oxy_ticks; đủ
        choke_interval_ticks thì đặt lại về 0, trừ 1 Máu, phát choke. Chạm 0 ở t -> ngạt lần đầu ở t+59.
        Trả True khi Máu về 0 và đã ngất (buổi sáng kết thúc, bước phải dừng).
        """
        if surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self._refill)
            self.zero_oxy_ticks = 0
            return False
        if self.oxygen_ticks > 0:
            self.oxygen_ticks -= 1
            if self.oxygen_ticks > 0:
                self.zero_oxy_ticks = 0  # còn oxy thì không có nhịp ngạt (v1.1: reset khi oxy > 0)
                return False
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks < self._choke_every:
            return False
        self.zero_oxy_ticks = 0
        self.hp -= 1
        events.append(("choke", {"hp": self.hp}))
        if self.hp > 0:
            return False
        self._faint("choke", events)
        return True

    def _faint(self, cause, events):
        """Máu 0: bỏ toàn bộ giỏ theo LIFO, phát faint rồi gather_end(fainted) với kho rỗng."""
        lost = self._drop_lifo(len(self.hold))
        events.append(("faint", {"cause": cause, "lost": lost, "hp": self.hp}))
        self._finish("fainted", events)

    def _drop_lifo(self, n) -> list:
        """Bỏ n món mới nhất khỏi giỏ (nhặt sau bỏ trước); trả các món theo thứ tự bỏ. Một bản sao, đảo tại chỗ."""
        k = max(0, len(self.hold) - n)
        lost = self.hold[k:]
        lost.reverse()
        del self.hold[k:]
        return self._hold_view(lost)

    def _nearest(self, coll, radius):
        """Thực thể gần nhất trong `radius` (tính cả đúng mép), hòa khoảng cách theo id; None nếu không có.

        Một lượt qua `coll`, chọn bằng min (lõi C). Thực thể gần nhất ngoài tầm thì mọi thực thể đều ngoài tầm.
        id duy nhất trong mỗi danh sách nên tuple không bao giờ phải so tới dict.
        """
        best = min(((math.dist(self.pos, e["pos"]), id_key(e["id"]), e) for e in coll), default=None)
        return best[2] if best is not None and best[0] <= radius else None

    def _room(self) -> int:
        return self._cap - len(self.hold)

    def _put(self, kind, n):
        """Thêm n nguyên liệu `kind` vào cuối giỏ (thứ tự nhặt, mới nhất cuối)."""
        if self.freshness:
            self.hold.extend(new_item(self.ids, kind, self.freshness["initial"]) for _ in range(n))
        else:
            self.hold.extend(repeat(kind, n))

    def _gather_node(self, events):
        """Hái nút ready gần nhất trong interact_radius: đủ chỗ thì lấy và đặt mọc lại, thiếu chỗ giữ nguyên nút."""
        node = self._nearest((n for n in self.nodes if n["regrow_ticks"] == 0), self._r_interact)
        if node is None:
            return
        need, free = self._node_yield, self._room()
        if free < need:
            events.append(("hold_full", {"action": "gather", "node_id": node["id"], "required": need, "free": free}))
            return
        self._put(node["kind"], need)
        node["regrow_ticks"] = self._regrow_full
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": need}))

    def _catch_fish(self, events):
        """Bắt đúng đàn gần nhất trong catch_radius: lấy cả yield, xoá đàn, đặt hồi chiêu.

        Thiếu chỗ: hold_full, giữ đàn và cooldown, không thử đàn khác. Không đàn trong tầm: không event, không hồi.
        """
        fish = self._nearest(self.fish, self._r_catch)
        if fish is None:
            return
        need, free = self._fish_yield[fish["kind"]], self._room()
        if free < need:
            events.append(("hold_full", {"action": "catch", "fish_id": fish["id"], "required": need, "free": free}))
            return
        self._put(fish["kind"], need)
        self.fish.remove(fish)
        self.catch_cd_ticks = self._catch_cd_full
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": need}))

    # --- thủy quái (v1.1) ---------------------------------------------------------
    def _monsters_step(self, events) -> bool:
        """Cập nhật quái theo id, rồi xét tối đa một hit. Trả True khi người chơi ngất (bước phải dừng)."""
        pd = self.pos[1]
        hittable = []  # quái không ở recoil đầu bước này mới được phát hiện/chạm
        for m in self.monsters:
            sp = self._mon[m["kind"]]
            if m["state"] == "recoil":
                p, r = m["pos"], m["recoil_dir"]
                p[0] += r[0] * sp["recoil"]
                p[1] += r[1] * sp["recoil"]
                self._clamp(p, sp["lim"])
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:  # hết recoil: về patrol, xét phát hiện/chạm từ bước kế
                    m["state"], m["state_ticks_left"], m["recoil_dir"] = "patrol", 0, None
                continue
            dist = math.dist(m["pos"], self.pos)
            if m["state"] == "patrol" and pd >= sp["depth"] and dist <= sp["detect"]:
                m["state"] = "chase"
            elif m["state"] == "chase" and (dist > sp["exit"] or pd < sp["depth"]):
                m["state"] = "patrol"
            if m["state"] == "chase":
                self._toward(m["pos"], self.pos, sp["chase"], sp["lim"])
            elif self._toward(m["pos"], m["waypoints"][m["target_idx"]], sp["patrol"], sp["lim"]):
                m["target_idx"] = 1 - m["target_idx"]  # tới waypoint: bước sau đi tới waypoint kia
            hittable.append(m)
        if self.invuln_ticks > 0:  # bất tử: không hit, không đẩy quái sang recoil
            return False
        best = None
        for m in hittable:
            sp = self._mon[m["kind"]]
            dist = math.dist(m["pos"], self.pos)
            if pd >= sp["depth"] and dist <= sp["hit"]:
                key = (dist, id_key(m["id"]))
                if best is None or key < best[0]:
                    best = (key, m)
        return best is not None and self._monster_hit(best[1], events)

    def _monster_hit(self, m, events) -> bool:
        """-1 Máu, rơi floor(n·loss_ratio) món theo LIFO, bất tử; con gây hit recoil từ bước sau. True nếu ngất."""
        self.hp -= 1
        lost = self._drop_lifo(math.floor(len(self.hold) * self._loss_ratio))
        self.invuln_ticks = self._invuln_full
        dx, dd = m["pos"][0] - self.pos[0], m["pos"][1] - self.pos[1]
        n = math.hypot(dx, dd)
        m["state"], m["state_ticks_left"] = "recoil", self._mon[m["kind"]]["recoil_ticks"]
        m["recoil_dir"] = [dx / n, dd / n] if n > 0 else [1.0, 0.0]  # hướng xa người chơi; trùng tâm dùng +x
        events.append(("monster_hit", {"monster_id": m["id"], "hp": self.hp, "lost": lost, "pos": list(self.pos)}))
        if self.hp > 0:
            return False
        self._faint("monster", events)
        return True

    @staticmethod
    def _toward(p, target, step, lim) -> bool:
        """Đi tối đa `step` về `target` (không vượt), rồi chặn trong `lim`. True nếu đã tới đích."""
        dx, dd = target[0] - p[0], target[1] - p[1]
        dist = math.hypot(dx, dd)
        arrived = dist <= step + ARRIVE_EPS
        if arrived:
            p[0], p[1] = target[0], target[1]
        else:
            p[0] += dx * step / dist
            p[1] += dd * step / dist
        GatherSim._clamp(p, lim)
        return arrived

    @staticmethod
    def _clamp(p, lim):
        x_lo, x_hi, d_lo, d_hi = lim
        p[0] = min(max(p[0], x_lo), x_hi)
        p[1] = min(max(p[1], d_lo), d_hi)

    # --- cá bơi / sinh (v1.1) ------------------------------------------------------
    def _set_heading(self, f, heading):
        """Đặt hướng (độ; 0 = +x, 90 = xuống) và vận tốc mỗi tick fish_speed/60 theo hướng đó."""
        f["heading_deg"] = float(heading)
        r = math.radians(heading)
        f["_v"] = [self._fish_step * math.cos(r), self._fish_step * math.sin(r)]

    def _fish_tick(self, events):
        """Mọi đàn bơi một bước theo id; tại phase_tick = fish_spawn_ticks·k sinh tối đa một đàn."""
        for f in self.fish:  # luôn sắp theo id
            self._swim_fish(f)
        if self._phase_tick % self._spawn_every == 0 and len(self.fish) < self._fish_max:
            f = self._spawn_one()
            if f is not None:
                events.append(("fish_spawned", {"id": f["id"], "kind": f["kind"], "pos": list(f["pos"])}))

    def _swim_fish(self, f):
        """Bước bơi thứ age+1: đổi hướng theo seed trước khi đi nếu là bội fish_turn_ticks; phản xạ ở mép."""
        f["age_ticks"] += 1
        if f["age_ticks"] % self._turn_every == 0:
            self._set_heading(f, self._rng_turn.random() * 360.0)
        p, v = f["pos"], f["_v"]
        flipped = False
        for i, (lo, hi) in enumerate((self._fish_x, self._fish_depths[f["kind"]])):
            q = p[i] + v[i]
            if q > hi:  # phản xạ phần quãng đường còn lại, đảo thành phần vuông góc với mép
                q, v[i], flipped = 2 * hi - q, -v[i], True
            elif q < lo:
                q, v[i], flipped = 2 * lo - q, -v[i], True
            p[i] = q
        if flipped:  # chạm góc thì cả hai thành phần đã đảo
            f["heading_deg"] = math.degrees(math.atan2(v[1], v[0])) % 360

    def _spawn_one(self):
        """Sinh một đàn: loài theo trọng số chuẩn hóa trên các loài còn điểm cách mọi đàn > clearance, điểm chọn
        đều trong các điểm hợp lệ của loài, hướng ban đầu theo seed. Hết điểm thì trả None (bỏ lượt)."""
        options = []
        for kind in self._fish_kinds:
            pts = [q for q in self._spawn_points[kind]
                   if all(math.dist(q, f["pos"]) > self._clearance for f in self.fish)]
            if pts:
                options.append((kind, pts))
        if not options:
            return None
        rng = self._rng_spawn
        r = rng.random() * sum(self._fish_weights[k] for k, _ in options)
        for kind, pts in options:
            r -= self._fish_weights[kind]
            if r < 0:
                break
        x, d = pts[rng.randrange(len(pts))]
        f = {"id": self.ids.new("F"), "kind": kind, "pos": [x, d], "heading_deg": 0.0, "age_ticks": 0}
        self._set_heading(f, rng.random() * 360.0)
        bisect.insort(self.fish, f, key=lambda e: id_key(e["id"]))
        return f

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
