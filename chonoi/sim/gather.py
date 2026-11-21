"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD mục 13.8, "Gather"):
  TODO(nhóm, lát 1): bơi + oxy + biên + giỏ
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  TODO(nhóm, lát 2): hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..ids import sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, upgrades=None):
        """`day`: số Ngày (bố trí Cá Sấu theo from_day; gather độc lập dùng Ngày 1).
        `upgrades`: cấp ĐANG ÁP DỤNG {"oxygen": n, "hp": n} (Ticket-02 mục 2), mặc định cấp 0."""
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
        oxygen_s, self.hp_max = _apply_upgrades(t, tuning.get("shop"), upgrades or {})
        self.oxygen_max = int(round(oxygen_s * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        # Cá (v1.1): random_fish (mặc định true) bật cá mặc định + bơi/sinh; false -> chỉ cá fixture, đứng yên.
        # Khai `fish` khi cờ bật thì THAY đàn ban đầu, vẫn bơi/sinh.
        self.random_fish = scenario.get("random_fish", True)
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0), "age_ticks": f.get("age_ticks", 0)}
                     for f in scenario.get("fish", [])]
        # Cá Sấu: scenario.monsters thay bố trí mặc định của Ngày (spawns có from_day <= day).
        if "monsters" in scenario:
            src_m = scenario["monsters"]
        else:
            src_m = [s for s in t["monsters"]["spawns"] if s["from_day"] <= day]
        self.monsters = [{"id": m["id"], "kind": m["kind"], "pos": [float(c) for c in m["pos"]],
                          "waypoints": [[float(c) for c in w] for w in m["waypoints"]],
                          "target_idx": m.get("target_idx", 1), "state": m.get("state", "patrol"),
                          "state_ticks_left": m.get("state_ticks_left", 0),
                          "recoil_dir": m.get("recoil_dir")} for m in src_m]
        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])
        if "fish" not in scenario and self.random_fish:
            for _ in range(t["fish_initial"]):
                if not self._spawn_one():
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
                      "age_ticks": f["age_ticks"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [{k: m[k] for k in ("id", "kind", "pos", "waypoints", "target_idx", "state",
                                             "state_ticks_left", "recoil_dir")}
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
        # 2. bơi + chặn mép
        was_surface = self._at_surface()
        self._move(inp)
        # 2b. lát 1: dive/surface, oxy, ngạt, ngất. True = đã ngất (gather_end đã phát) -> dừng bước.
        if self._update_oxygen(events, was_surface):
            return events
        # 2c. lát 1 (v1.1): Cá Sấu theo id, rồi xét tối đa một hit. True = đã ngất -> dừng bước.
        if self._update_monsters(events):
            return events
        # 3. interact: bến trước, rồi hái (lát 2)
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            self._try_gather(events)
        # 4. bắt cá (lát 2)
        if inp.pressed("catch"):
            self._try_catch(events)
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        return events

    # --- lát 1 (sở hữu: người làm gather lát 1) ---------------------------------
    def _update_oxygen(self, events, was_surface) -> bool:
        """Gọi SAU khi bơi. Trả True nếu người chơi vừa ngất (đã gọi _finish("fainted")).

        PRD-0 mục F, Gather bước 2 (docs/prd/phase-1.md):
          - dive / surface khi đổi phía biên mặt nước (d <= surface_depth), data: pos sau di chuyển.
          - oxy theo d CUỐI bước: mặt nước +oxygen_refill_per_tick (kẹp tối đa) và reset đếm ngạt;
            dưới nước -1 (kẹp 0), oxygen_empty khi từ dương xuống 0.
          - mỗi bước dưới nước kết thúc với oxy 0 (kể cả bước vừa chạm 0): zero_oxy_ticks += 1;
            đủ choke_interval_ticks -> đặt lại 0, hp -= 1, choke {hp}. Chạm 0 ở t -> ngạt lần đầu ở t+59.
          - hp == 0 -> bỏ giỏ theo LIFO, faint {cause, lost, hp}, gather_end("fainted") với kho rỗng.
        """
        t = self.t
        surface = self._at_surface()
        if surface != was_surface:
            events.append(("surface" if surface else "dive", {"pos": list(self.pos)}))
        if surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
            return False
        before = self.oxygen_ticks
        self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
        if before > 0 and self.oxygen_ticks == 0:
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        if self.oxygen_ticks > 0:
            return False
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks < t["choke_interval_ticks"]:
            return False
        self.zero_oxy_ticks = 0
        self.hp = max(0, self.hp - 1)
        events.append(("choke", {"hp": self.hp}))
        if self.hp > 0:
            return False
        self._faint("choke", events)
        return True

    def _faint(self, cause, events):
        """Máu về 0: bỏ toàn bộ giỏ theo LIFO, faint {cause, lost, hp: 0} rồi gather_end("fainted") với kho rỗng."""
        lost = list(reversed(self.hold))  # nhặt sau bỏ trước
        self.hold = []
        events.append(("faint", {"cause": cause, "lost": lost, "hp": 0}))
        self._finish("fainted", events)

    def _update_monsters(self, events) -> bool:
        """Cá Sấu (Ticket-02 mục 1.2, thứ tự mục 4.5). Gọi SAU oxy/ngạt. Trả True nếu người chơi vừa ngất.

        Từng con theo id:
          - recoil: lùi recoil_dist/recoil_ticks mỗi bước theo recoil_dir (chặn mép), không gây hit; hết timer về
            patrol và chỉ xét phát hiện/chạm từ bước kế.
          - stunned (mở rộng Lao): đứng yên tới hết timer rồi về patrol.
          - patrol <-> chase: chase khi người chơi ở d >= ngưỡng loài (depths[0]) và cách <= detect_radius;
            về patrol khi cách > exit_radius hoặc người chơi lên trên ngưỡng. Khoảng cách xét TRƯỚC khi con di chuyển.
          - patrol đi patrol_speed tới waypoints[target_idx], tới nơi thì đổi mục tiêu cho bước sau;
            chase bơi chase_speed về phía người chơi. Chặn theo biên map và dải độ sâu của loài.
        Sau khi cả hai di chuyển: tối đa MỘT hit — con gần nhất (hòa theo id) trong hit_radius, người chơi ở
        d >= ngưỡng, hết bất tử. Hit: -1 Máu, bỏ floor(số đang mang × loss_ratio) theo LIFO, bất tử invuln_ticks,
        con đó vào recoil recoil_ticks bước (từ bước sau) theo hướng xa người chơi chốt lúc chạm (trùng tâm: +x).
        """
        mon = self.t["monsters"]
        species = mon["species"]
        b = self.t["bounds"]
        can_hit = []
        for m in sort_by_id(self.monsters):
            s = species[m["kind"]]
            if m["state"] in ("recoil", "stunned"):
                if m["state"] == "recoil":
                    step = s["recoil_dist"] / s["recoil_ticks"]
                    self._clamp_monster(m, [m["pos"][0] + m["recoil_dir"][0] * step,
                                            m["pos"][1] + m["recoil_dir"][1] * step], s, b)
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"], m["state_ticks_left"], m["recoil_dir"] = "patrol", 0, None
                continue
            deep = self.pos[1] >= s["depths"][0]
            dist = math.dist(m["pos"], self.pos)
            if m["state"] == "patrol" and deep and dist <= s["detect_radius"]:
                m["state"] = "chase"
            elif m["state"] == "chase" and (not deep or dist > s["exit_radius"]):
                m["state"] = "patrol"
            if m["state"] == "chase":
                self._clamp_monster(m, _toward(m["pos"], self.pos, s["chase_speed"] / TICK), s, b)
            else:
                wp = m["waypoints"][m["target_idx"]]
                self._clamp_monster(m, _toward(m["pos"], wp, s["patrol_speed"] / TICK), s, b)
                if math.dist(m["pos"], wp) <= 1e-9:
                    m["target_idx"] = 1 - m["target_idx"]
            can_hit.append(m)
        if self.invuln_ticks > 0:
            return False
        best = None
        for m in can_hit:  # đã theo thứ tự id -> hòa khoảng cách giữ con id nhỏ
            s = species[m["kind"]]
            d = math.dist(m["pos"], self.pos)
            if self.pos[1] >= s["depths"][0] and d <= s["hit_radius"] and (best is None or d < best[0]):
                best = (d, m)
        if best is None:
            return False
        m = best[1]
        s = species[m["kind"]]
        self.hp = max(0, self.hp - 1)
        n_lost = math.floor(len(self.hold) * mon["loss_ratio"])
        lost = [self.hold.pop() for _ in range(n_lost)]  # nhặt sau mất trước
        self.invuln_ticks = mon["invuln_ticks"]
        dx, dd = m["pos"][0] - self.pos[0], m["pos"][1] - self.pos[1]
        n = math.hypot(dx, dd)
        m["recoil_dir"] = [dx / n, dd / n] if n > 0 else [1.0, 0.0]
        m["state"], m["state_ticks_left"] = "recoil", s["recoil_ticks"]
        events.append(("monster_hit", {"monster_id": m["id"], "hp": self.hp, "lost": lost, "pos": list(self.pos)}))
        if self.hp > 0:
            return False
        self._faint("monster", events)
        return True

    def _clamp_monster(self, m, pos, s, b):
        lo_d, hi_d = max(b["d"][0], s["depths"][0]), min(b["d"][1], s["depths"][1])
        m["pos"] = [min(max(pos[0], b["x"][0]), b["x"][1]), min(max(pos[1], lo_d), hi_d)]

    # --- lát 2 (sở hữu: người làm gather lát 2) ---------------------------------
    def _try_gather(self, events):
        """Chỉ khi ở mặt nước: nút `ready` gần nhất trong interact_radius
        (id nhỏ khi bằng nhau). Dùng self._add_to_hold([kind] * node_yield):
        thành công -> gather + regrow_ticks = regrow_s * TICK; thất bại -> hold_full."""
        if not self._at_surface():
            return

        radius = self.t["interact_radius"]
        px, pd = self.pos

        best_node = None
        best_dist = None
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] != 0:
                continue
            dist = math.hypot(px - n["pos"][0], pd - n["pos"][1])
            if dist <= radius and (best_dist is None or dist < best_dist):
                best_dist = dist
                best_node = n

        if best_node is None:
            return

        kind = best_node["kind"]
        amount = self.t["node_yield"]
        if self._add_to_hold([kind] * amount):
            best_node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
            events.append(("gather", {
                "node_id": best_node["id"],
                "kind": kind,
                "amount": amount,
            }))
        else:
            free = self.t["hold_capacity"] - len(self.hold)
            events.append(("hold_full", {
                "action": "gather",
                "node_id": best_node["id"],
                "required": amount,
                "free": free,
            }))

    def _try_catch(self, events):
        """Chỉ khi catch_cd_ticks == 0 và dưới nước: đàn cá gần nhất trong catch_radius
        (id nhỏ khi bằng nhau). Dùng self._add_to_hold([kind] * fish_yield[kind]):
        thành công -> fish_caught (xóa đàn cá); thất bại -> hold_full. Đặt catch_cd_ticks theo PRD."""
        if self.catch_cd_ticks != 0 or self._at_surface():
            return

        radius = self.t["catch_radius"]
        px, pd = self.pos

        best_fish = None
        best_dist = None
        for f in sort_by_id(self.fish):
            dist = math.hypot(px - f["pos"][0], pd - f["pos"][1])
            if dist <= radius and (best_dist is None or dist < best_dist):
                best_dist = dist
                best_fish = f

        if best_fish is None:
            return

        kind = best_fish["kind"]
        yield_amt = self.t["fish_yield"][kind]
        if self._add_to_hold([kind] * yield_amt):
            self.fish.remove(best_fish)
            self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
            events.append(("fish_caught", {
                "fish_id": best_fish["id"],
                "kind": kind,
                "yield": yield_amt,
            }))
        else:
            free = self.t["hold_capacity"] - len(self.hold)
            events.append(("hold_full", {
                "action": "catch",
                "fish_id": best_fish["id"],
                "required": yield_amt,
                "free": free,
            }))

    # --- dùng chung (lát 1 + lát 2): mọi thao tác thêm vào giỏ đi qua đây ----------
    def _add_to_hold(self, kinds) -> bool:
        """Thêm theo thứ tự nhặt (cuối mảng = mới nhất). Không đủ chỗ thì KHÔNG thêm gì, trả False.
        Kiểm lại với PRD-0: nếu cho phép nhặt một phần thì sửa ở đây (một chỗ duy nhất)."""
        if len(self.hold) + len(kinds) > self.t["hold_capacity"]:
            return False
        self.hold.extend(kinds)
        return True

    # --- dùng chung (lát 0 tạo; lát 2 gọi lại cho lịch sinh cá mỗi fish_spawn_ticks) ---------
    def _spawn_one(self):
        """Sinh MỘT đàn theo Ticket-02 mục 1.1 "Sinh cá". Trả đàn mới (dict), hoặc False nếu đủ trần / hết điểm.
        Lát 2 phát sự kiện `fish_spawned {id, kind, pos}` khi gọi theo lịch (đàn đầu ca không phát).

        Điểm hợp lệ của loài: (x, d) với x ∈ fish_spawn_x, d ∈ fish_spawn_depths[loài], cách MỌI đàn đang sống
        > fish_spawn_clearance. Loài chọn theo fish_weights, chuẩn hóa lại trên các loài còn điểm; rồi chọn đều
        một điểm của loài, hướng ban đầu theo seed. Mọi số ngẫu nhiên qua stream "fish_spawn".
        """
        t = self.t
        if len(self.fish) >= t["fish_max"]:
            return False
        clear = t["fish_spawn_clearance"]
        options = {}
        for kind in sorted(t["fish_spawn_depths"]):
            pts = [[float(x), float(d)] for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]
                   if all(math.dist((x, d), f["pos"]) > clear for f in self.fish)]
            if pts and t["fish_weights"][kind] > 0:
                options[kind] = pts
        if not options:
            return False
        rng = self.rng.get("fish_spawn")
        kinds = sorted(options)
        total = sum(t["fish_weights"][k] for k in kinds)
        r, acc, kind = rng.random() * total, 0.0, kinds[-1]
        for k in kinds:
            acc += t["fish_weights"][k]
            if r < acc:
                kind = k
                break
        pos = options[kind][rng.randrange(len(options[kind]))]
        heading = rng.randrange(360)  # TODO(lát 2): thống nhất cách lấy hướng theo seed với luật đổi hướng
        f = {"id": self.ids.new("F"), "kind": kind, "pos": pos, "heading_deg": heading, "age_ticks": 0}
        self.fish.append(f)
        return f

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


def _apply_upgrades(g, shop, active):
    """(oxygen_max_s, hp_max) theo cấp ĐANG ÁP DỤNG (Ticket-02 mục 2 "Shop và nâng cấp"). Cấp 0 = số cơ sở."""
    oxygen_s, hp_max = g["oxygen_max_s"], g["hp_max"]
    ups = (shop or {}).get("upgrades", {})
    lv = active.get("oxygen", 0)
    if lv:
        oxygen_s = ups["oxygen"][lv - 1]["oxygen_max_s"]
    lv = active.get("hp", 0)
    if lv:
        hp_max = ups["hp"][lv - 1]["hp_max"]
    return oxygen_s, hp_max


def _toward(src, dst, step):
    """Đi tối đa `step` từ src về dst, không vượt quá đích."""
    dx, dy = dst[0] - src[0], dst[1] - src[1]
    n = math.hypot(dx, dy)
    if n <= step:
        return [float(dst[0]), float(dst[1])]
    return [src[0] + dx / n * step, src[1] + dy / n * step]
