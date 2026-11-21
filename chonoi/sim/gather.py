"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD mục 13.8, "Gather"):
  ĐÃ LÀM (lát 1): bơi + oxy + biên + giỏ
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  ĐÃ LÀM (lát 2): hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
  ĐÃ LÀM (Phase 2, Test Contract v1.1 §1.1, §1.2, §4.3–4.5):
      - đàn cá bơi (đổi hướng theo seed mỗi fish_turn_ticks bước bơi, phản xạ mép), age_ticks
      - 8 đàn đầu ca ở 8 điểm sinh khác nhau, sinh theo lịch (trần, khoảng hở, trọng số loài)
      - Cá Sấu (patrol/chase/recoil), Máu, bất tử, rơi hàng LIFO, ngất do bị chạm
      - tham số day / oxygen_max_s / hp_max cho chế độ day (bố trí theo Ngày, nâng cấp đang áp dụng)
"""

import math

from ..errors import BadInput
from ..ids import sort_by_id
from ..inventory import FISH_KINDS, KINDS, NODE_KINDS, hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")
EPS = 1e-9
MONSTER_STATES = ("patrol", "chase", "recoil")
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
GATHER_SCENARIO_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, oxygen_max_s=None, hp_max=None):
        """`day`: số Ngày (bố trí Cá Sấu theo from_day; gather độc lập = 1).
        `oxygen_max_s` / `hp_max`: giá trị theo cấp nâng cấp ĐANG ÁP DỤNG (None = cơ sở trong tuning)."""
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.day = int(day)
        self.hp_max = int(hp_max if hp_max is not None else t["hp_max"])
        omax_s = oxygen_max_s if oxygen_max_s is not None else t["oxygen_max_s"]
        validate_gather_scenario(scenario, tuning, oxygen_max_s=omax_s, hp_max=self.hp_max)
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(omax_s * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self._rested = set()
        self.phase_tick = 0  # số bước gameplay đã chạy trong pha này (lịch sinh cá theo phase_tick)
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định, bơi và sinh
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        self.random_fish = scenario.get("random_fish", True)
        src_fish = scenario.get("fish", [])
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": float(f.get("heading_deg", 0)), "age_ticks": f.get("age_ticks", 0)}
                     for f in src_fish]
        mt = t["monsters"]
        if "monsters" in scenario:
            src_m = scenario["monsters"]
        else:
            src_m = [m for m in mt["spawns"] if m["from_day"] <= self.day]
        self.monsters = []
        for m in src_m:
            state = m.get("state", "patrol")
            rd = m.get("recoil_dir")
            self.monsters.append({
                "id": m["id"], "kind": m["kind"], "pos": [float(c) for c in m["pos"]],
                "waypoints": [[float(c) for c in w] for w in m["waypoints"]],
                "target_idx": m.get("target_idx", 1), "state": state,
                "state_ticks_left": m.get("state_ticks_left", 0),
                "recoil_dir": [float(c) for c in rd] if rd is not None else None})
        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])
        if self.random_fish and "fish" not in scenario:
            for _ in range(int(t["fish_initial"])):
                f = self._spawn_one()
                if f is None:
                    break
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
            "monsters": [{"id": m["id"], "kind": m["kind"], "pos": m["pos"], "waypoints": m["waypoints"],
                          "target_idx": m["target_idx"], "state": m["state"],
                          "state_ticks_left": m["state_ticks_left"], "recoil_dir": m["recoil_dir"]}
                         for m in sort_by_id(self.monsters)],
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
        # 2. bơi + chặn mép, so phía biên mặt nước đầu/cuối bước
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif now_surface and not was_surface:
            events.append(("surface", {"pos": list(self.pos)}))
        # oxy theo d CUỐI bước
        if now_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + int(self.t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0
        else:
            before = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if before > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:  # kể cả bước vừa chạm 0
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
                    self.zero_oxy_ticks = 0
                    self.hp = max(0, self.hp - 1)
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp == 0:
                        self._faint("choke", events)
                        return events
        # 2b. Cá Sấu theo id rồi xét tối đa một hit (v1.1 §1.2)
        self._update_monsters()
        if self._monster_hit(events):
            return events
        # 3. interact (cạnh lên): bến trước, rồi hái ở mặt nước
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if now_surface:
                node = self._nearest(
                    [n for n in self.nodes if n["regrow_ticks"] == 0], self.t["interact_radius"])
                if node is not None:
                    amount = int(self.t["node_yield"])
                    free = self._free()
                    if amount <= free:
                        self.hold.extend([node["kind"]] * amount)
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": amount}))
                    else:
                        events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                                     "required": amount, "free": free}))
        # 4. bắt cá (cạnh lên), chỉ khi hết hồi chiêu và đang dưới nước
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not now_surface:
            fish = self._nearest(self.fish, self.t["catch_radius"])
            if fish is not None:
                y = int(self.t["fish_yield"][fish["kind"]])
                free = self._free()
                if y <= free:
                    self.hold.extend([fish["kind"]] * y)
                    self.fish = [f for f in self.fish if f is not fish]
                    events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": y}))
                    self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                else:
                    events.append(("hold_full", {"action": "catch", "fish_id": fish["id"],
                                                 "required": y, "free": free}))
        # 5. hết giờ (mọi độ sâu), giữ giỏ sau các hành động trên
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        # 6. còn giờ: cá bơi, rồi sinh theo lịch (cá mới tham gia từ bước sau)
        if self.random_fish:
            self._swim_fish()
            if self.phase_tick % int(self.t["fish_spawn_ticks"]) == 0:
                f = self._spawn_one()
                if f is not None:
                    events.append(("fish_spawned", {"id": f["id"], "kind": f["kind"], "pos": list(f["pos"])}))
        return events

    # --- đàn cá (v1.1 §1.1) ------------------------------------------------------
    def _swim_fish(self):
        t = self.t
        turn = int(t["fish_turn_ticks"])
        step = t["fish_speed"] / TICK
        xlo, xhi = t["fish_x"]
        rng = self.rng.get("fish_turn")
        for f in sort_by_id(self.fish):
            n = f["age_ticks"] + 1  # số thứ tự bước bơi này
            if n % turn == 0:  # đổi hướng TRƯỚC khi di chuyển
                f["heading_deg"] = rng.random() * 360.0
            a = math.radians(f["heading_deg"])
            v = [math.cos(a) * step, math.sin(a) * step]
            dlo, dhi = t["fish_depths"][f["kind"]]
            flipped = False
            for i, (lo, hi) in enumerate(((xlo, xhi), (dlo, dhi))):
                c = f["pos"][i] + v[i]
                if c > hi:
                    c = hi - (c - hi)
                    v[i] = -v[i]
                    flipped = True
                elif c < lo:
                    c = lo + (lo - c)
                    v[i] = -v[i]
                    flipped = True
                f["pos"][i] = min(hi, max(lo, c))
            if flipped:
                f["heading_deg"] = math.degrees(math.atan2(v[1], v[0])) % 360.0
            f["age_ticks"] = n

    def _spawn_points(self, kind):
        """Điểm sinh của loài còn hợp lệ: cách mọi đàn đang sống > fish_spawn_clearance."""
        t = self.t
        clear = t["fish_spawn_clearance"]
        pts = [[float(x), float(d)] for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]]
        return [p for p in pts if all(math.dist(p, f["pos"]) > clear for f in self.fish)]

    def _spawn_one(self):
        """Sinh tối đa một đàn: dưới trần, loài theo trọng số chuẩn hóa trên các loài còn điểm,
        điểm chọn đều, hướng theo seed. Trả đàn mới hoặc None (bỏ lượt)."""
        t = self.t
        if len(self.fish) >= int(t["fish_max"]):
            return None
        weights = t["fish_weights"]
        cands = [(k, self._spawn_points(k)) for k in weights]  # thứ tự khóa fish_weights trong contract
        cands = [(k, pts) for k, pts in cands if pts]
        if not cands:
            return None
        rng = self.rng.get("fish_spawn")
        total = sum(weights[k] for k, _ in cands)
        r = rng.random() * total
        kind, pts = cands[-1]
        for k, p in cands:
            if r < weights[k]:
                kind, pts = k, p
                break
            r -= weights[k]
        pos = pts[rng.randrange(len(pts))]
        f = {"id": self.ids.new("F"), "kind": kind, "pos": list(pos),
             "heading_deg": rng.random() * 360.0, "age_ticks": 0}
        self.fish.append(f)
        return f

    # --- Cá Sấu (v1.1 §1.2) --------------------------------------------------------
    def _species(self, m):
        return self.t["monsters"]["species"][m["kind"]]

    def _clamp_monster(self, m):
        b = self.t["bounds"]
        lo, hi = self._species(m)["depths"]
        m["pos"][0] = min(b["x"][1], max(b["x"][0], m["pos"][0]))
        m["pos"][1] = min(hi, max(lo, b["d"][0], min(b["d"][1], m["pos"][1])))

    @staticmethod
    def _move_toward(pos, target, dist):
        dd = math.dist(pos, target)
        if dd <= dist + EPS:  # dung sai số thực khi cộng dồn 1/60 m
            pos[0], pos[1] = float(target[0]), float(target[1])
            return True
        pos[0] += (target[0] - pos[0]) / dd * dist
        pos[1] += (target[1] - pos[1]) / dd * dist
        return False

    def _update_monsters(self):
        self._rested = set()  # con vừa hết recoil ở bước này: chưa phát hiện/chạm
        for m in sort_by_id(self.monsters):
            sp = self._species(m)
            if m["state"] == "recoil":
                step = sp["recoil_dist"] / sp["recoil_ticks"]
                m["pos"][0] += m["recoil_dir"][0] * step
                m["pos"][1] += m["recoil_dir"][1] * step
                self._clamp_monster(m)
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:  # hết recoil: về patrol, xét phát hiện/chạm từ bước kế
                    m["state"], m["state_ticks_left"], m["recoil_dir"] = "patrol", 0, None
                    self._rested.add(m["id"])
                continue
            deep = self.pos[1] >= sp["depths"][0]
            d = math.dist(m["pos"], self.pos)
            if m["state"] == "patrol" and deep and d <= sp["detect_radius"]:
                m["state"] = "chase"
            elif m["state"] == "chase" and (d > sp["exit_radius"] or not deep):
                m["state"] = "patrol"
            if m["state"] == "chase":
                self._move_toward(m["pos"], self.pos, sp["chase_speed"] / TICK)
            else:
                wp = m["waypoints"][m["target_idx"]]
                if self._move_toward(m["pos"], wp, sp["patrol_speed"] / TICK):
                    m["target_idx"] = 1 - m["target_idx"]  # tới nơi: đổi mục tiêu cho bước sau
            self._clamp_monster(m)

    def _monster_hit(self, events) -> bool:
        """Tối đa một hit mỗi bước (gần nhất, hòa theo id). Trả True nếu người chơi ngất."""
        if self.invuln_ticks > 0:
            return False
        best = None
        for m in sort_by_id(self.monsters):
            if m["state"] == "recoil" or m["id"] in self._rested:
                continue
            sp = self._species(m)
            dd = math.dist(m["pos"], self.pos)
            if dd <= sp["hit_radius"] and self.pos[1] >= sp["depths"][0] and (best is None or dd < best[0]):
                best = (dd, m)
        if best is None:
            return False
        dd, m = best
        mt = self.t["monsters"]
        n = math.floor(len(self.hold) * mt["loss_ratio"])
        lost = [self.hold.pop() for _ in range(n)]  # LIFO: nhặt sau mất trước
        self.hp = max(0, self.hp - 1)
        self.invuln_ticks = int(mt["invuln_ticks"])
        if dd > 0:
            rd = [(m["pos"][0] - self.pos[0]) / dd, (m["pos"][1] - self.pos[1]) / dd]
        else:
            rd = [1.0, 0.0]  # trùng tâm dùng +x
        m["state"], m["state_ticks_left"], m["recoil_dir"] = "recoil", int(self._species(m)["recoil_ticks"]), rd
        events.append(("monster_hit", {"monster_id": m["id"], "hp": self.hp, "lost": lost, "pos": list(self.pos)}))
        if self.hp == 0:
            self._faint("monster", events)
            return True
        return False

    def _faint(self, cause, events):
        lost = list(reversed(self.hold))  # LIFO: nhặt sau bỏ trước
        self.hold = []
        events.append(("faint", {"cause": cause, "lost": lost, "hp": 0}))
        self._finish("fainted", events)

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _free(self) -> int:
        return int(self.t["hold_capacity"]) - len(self.hold)

    def _nearest(self, items, radius):
        """Thực thể gần nhất trong bán kính (tính cả đúng mép), hòa theo id."""
        best = None
        for e in sort_by_id(items):
            dd = math.dist(self.pos, e["pos"])
            if dd <= radius and (best is None or dd < best[0]):
                best = (dd, e)
        return best[1] if best else None

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


# --- kiểm scenario gather v1.1 (§4.3), lỗi -> BadInput (mã 2) ------------------------
def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"gather.{name} phải là số nguyên không âm")


def _pt(name, v, bounds):
    if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v)):
        raise BadInput(f"gather.{name} phải là [x, d]")
    for c, axis in zip(v, AXES):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"gather.{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"gather.{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"] or e["id"] in seen:
            raise BadInput(f"gather.{name}: mỗi phần tử cần id duy nhất (chuỗi khác rỗng)")
        seen.add(e["id"])


def validate_gather_scenario(b, tuning, oxygen_max_s=None, hp_max=None):
    """Kiểm khối scenario `gather` theo v1.1 (gồm player.invuln_ticks, fish[].age_ticks, monsters[]).
    Dùng được độc lập (scenario.py / day mode) và được GatherSim gọi khi dựng."""
    if not isinstance(b, dict):
        raise BadInput("khối gather phải là object")
    g = tuning["gather"]
    bounds = g["bounds"]
    extra = set(b) - GATHER_SCENARIO_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather: {sorted(extra)}")
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    swim = b.get("random_fish", True)
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(k not in KINDS for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    if set(p) - GATHER_PLAYER_KEYS:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(set(p) - GATHER_PLAYER_KEYS)}")
    if "pos" in p:
        _pt("player.pos", p["pos"], bounds)
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    if p.get("invuln_ticks", 0) > g["monsters"]["invuln_ticks"]:
        raise BadInput("player.invuln_ticks vượt invuln_ticks")
    omax = int(round((oxygen_max_s if oxygen_max_s is not None else g["oxygen_max_s"]) * TICK))
    if p.get("oxygen_ticks", 0) > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    hmax = hp_max if hp_max is not None else g["hp_max"]
    if "hp" in p and not (1 <= p["hp"] <= hmax):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "nodes" in b:
        _ids("nodes", b["nodes"])
        for n in b["nodes"]:
            if n.get("kind") not in NODE_KINDS:
                raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
            _pt(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
            if n["pos"][1] != 0:
                raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
            if "regrow_ticks" in n:
                _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    if "fish" in b:
        _ids("fish", b["fish"])
        if swim and len(b["fish"]) > g["fish_max"]:
            raise BadInput("fish vượt fish_max")
        for f in b["fish"]:
            if f.get("kind") not in FISH_KINDS:
                raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
            _pt(f"fish.{f['id']}.pos", f.get("pos"), bounds)
            if f["pos"][1] <= g["surface_depth"]:
                raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
            if swim:  # đàn bơi phải nằm trong miền bơi của loài
                xlo, xhi = g["fish_x"]
                dlo, dhi = g["fish_depths"][f["kind"]]
                if not (xlo <= f["pos"][0] <= xhi and dlo <= f["pos"][1] <= dhi):
                    raise BadInput(f"fish.{f['id']}: đàn bơi phải trong x ∈ {g['fish_x']}, d ∈ [{dlo}, {dhi}]")
            if "heading_deg" in f and not _num(f["heading_deg"]):
                raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
            if "age_ticks" in f:
                _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    if "monsters" in b:
        _ids("monsters", b["monsters"])
        species = g["monsters"]["species"]
        for m in b["monsters"]:
            mid = m["id"]
            if set(m) - MONSTER_KEYS:
                raise BadInput(f"monsters.{mid}: trường lạ {sorted(set(m) - MONSTER_KEYS)}")
            if m.get("kind") not in species:
                raise BadInput(f"monsters.{mid}: kind phải thuộc {sorted(species)}")
            lo, hi = species[m["kind"]]["depths"]
            wps = m.get("waypoints")
            if not isinstance(wps, list) or len(wps) != 2:
                raise BadInput(f"monsters.{mid}: cần đúng 2 waypoint")
            for name, pt in [("pos", m.get("pos")), ("waypoints[0]", wps[0]), ("waypoints[1]", wps[1])]:
                _pt(f"monsters.{mid}.{name}", pt, bounds)
                if not (lo <= pt[1] <= hi):
                    raise BadInput(f"monsters.{mid}.{name}: ngoài dải độ sâu loài [{lo}, {hi}]")
            ti = m.get("target_idx", 1)
            if isinstance(ti, bool) or ti not in (0, 1):
                raise BadInput(f"monsters.{mid}.target_idx phải là 0 hoặc 1")
            state = m.get("state", "patrol")
            if state not in MONSTER_STATES:
                raise BadInput(f"monsters.{mid}.state phải là một trong {MONSTER_STATES}")
            left = m.get("state_ticks_left", 0)
            _nonneg_int(f"monsters.{mid}.state_ticks_left", left)
            rd = m.get("recoil_dir")
            if state == "recoil":
                if left <= 0:
                    raise BadInput(f"monsters.{mid}: recoil cần state_ticks_left dương")
                if not (isinstance(rd, list) and len(rd) == 2 and all(_num(c) for c in rd)
                        and abs(math.hypot(rd[0], rd[1]) - 1) <= 1e-6):
                    raise BadInput(f"monsters.{mid}: recoil cần recoil_dir là vector đơn vị")
            else:
                if rd is not None:
                    raise BadInput(f"monsters.{mid}: recoil_dir chỉ có khi recoil (mặc định null)")
                if left != 0:
                    raise BadInput(f"monsters.{mid}: state_ticks_left chỉ dương khi recoil")
