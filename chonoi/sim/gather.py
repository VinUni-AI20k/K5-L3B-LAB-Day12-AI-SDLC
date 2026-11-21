"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD mục 13.8, "Gather"):
  Lát 1 (đã có): oxy, ngạt, Máu, ngất, giỏ.
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke), rồi đếm lại từ 0
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface (data: pos) / oxygen_empty / choke / faint
      - giỏ: TV2 gọi try_add_hold — cuối mảng là món mới nhất (LIFO), đầy thì hold_full và không thêm
  Lát 2 (đã có): hái + bắt cá + cập bến + kho.
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks tính từ lần bắt thành công, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items
from .freshness import (
    build_hold_items,
    decay_hold,
    make_fresh_item,
    parse_freshness_config,
    serialize_hold,
    serialize_inventory_items,
)
from .monsters import build_monsters, serialize_monsters, step_monsters
from .fish import initial_schools, spawn_if_due, swim
from .ramp import ramp_velocity
from .shop import upgrade_entry

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day: int = 1, active_upgrades=None, item_ids=None):
        t = self._apply_active_upgrades(tuning["gather"], tuning.get("shop"), active_upgrades)
        self.t = t
        self.day = max(1, int(day))
        self.active_upgrades = dict(active_upgrades or {})
        self.rng = streams
        self.ids = ids
        self._freshness = parse_freshness_config(tuning)
        self._item_ids = item_ids if item_ids is not None else ids
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
        raw_hold = scenario.get("hold", [])
        # thứ tự nhặt, cuối mảng là mới nhất; v1.2 lưu cá thể {id, kind, u}
        self.hold = (build_hold_items(raw_hold, self._freshness, self._item_ids)
                     if self._freshness is not None else list(raw_hold))
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        # random_fish:false → cá fixture đứng yên, không bơi/sinh. Có fish_speed mới là contract v1.1.
        random_fish = scenario.get("random_fish", True)
        self._fish_live = bool(random_fish) and "fish_speed" in t
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif self._fish_live and isinstance(t.get("fish_initial"), int):
            self.fish = initial_schools(t, self.rng, ids, int(t["fish_initial"]))
            src_fish = None
        elif random_fish and isinstance(t.get("fish_initial"), list):
            src_fish = t["fish_initial"]
        else:
            src_fish = []
        if src_fish is not None:
            self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                          "heading_deg": f.get("heading_deg", 0), "age_ticks": f.get("age_ticks", 0)}
                         for f in src_fish]
        self.phase_tick = 0
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        # Thủy quái (Phase 2, T220–T223 & T246): chỉ kích hoạt khi có tuning.gather.monsters
        self._monster_cfg = t.get("monsters") if isinstance(t.get("monsters"), dict) else None
        sc_monsters = scenario["monsters"] if "monsters" in scenario else None
        self.monsters = build_monsters(self._monster_cfg, sc_monsters, self.day, ids)
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    @staticmethod
    def _apply_active_upgrades(gather_tuning: dict, shop_tuning, active_upgrades) -> dict:
        """Áp các cấp nâng cấp đang hiệu lực (`active_upgrades`) lên bản sao `tuning.gather` (T246)."""
        t = dict(gather_tuning)
        if not active_upgrades or not isinstance(shop_tuning, dict) or not isinstance(shop_tuning.get("upgrades"), dict):
            return t
        for uid in sorted(active_upgrades):
            lv = int(active_upgrades[uid])
            if lv <= 0:
                continue
            entry = upgrade_entry(shop_tuning, uid, lv)
            if entry:
                for k, v in entry.items():
                    if k not in ("level", "price"):
                        t[k] = v
        return t

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self):
        if self._freshness is not None:
            return serialize_inventory_items(self.hold)
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        hold_view = serialize_hold(self.hold) if self._freshness is not None else list(self.hold)
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": hold_view, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                       "age_ticks": f.get("age_ticks", 0)}
                     for f in sort_by_id(self.fish)],
            "monsters": serialize_monsters(self.monsters),
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        self.phase_tick += 1
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại, hao độ tươi giỏ (v1.2)
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        if self._freshness is not None:
            decay_hold(self.hold, self._freshness, events)
        # 2. bơi + chặn mép, rồi oxy theo độ sâu CUỐI bước
        was_surface = self._at_surface()
        self._move(inp)
        if self._oxygen_and_breath(events, was_surface):
            return events
        # 2b. thủy quái (Cá Sấu Năm Chèo — TICKET-02 §1.2, §4.5): cập nhật theo id rồi tối đa 1 hit
        if self._monsters_step(events):
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            self._try_harvest(events)
        # 4. bắt cá
        if inp.pressed("catch"):
            self._try_catch(events)
        # 5. hết giờ. Còn giờ thì cá bơi rồi mới sinh (cá mới bơi từ bước sau).
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        if self._fish_live:
            swim(self.fish, self.t, self.rng)
            spawn_if_due(self.fish, self.t, self.rng, self.ids, self.phase_tick, events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def try_add_hold(self, kind, events) -> bool:
        """Thêm một món vào cuối giỏ (LIFO). TV2 gọi khi hái hoặc bắt cá.

        Đầy (`hold_capacity`) thì không thêm, phát `hold_full` và trả False.
        """
        if len(self.hold) >= int(self.t["hold_capacity"]):
            events.append(("hold_full", {"kind": kind}))
            return False
        entry = (make_fresh_item(self._item_ids, kind, self._freshness)
                 if self._freshness is not None else kind)
        self.hold.append(entry)
        return True

    def _drop_hold_lifo(self, count: int) -> list:
        """Bỏ `count` món từ cuối giỏ (LIFO); v1.2 xuất mảng cá thể `{id, kind, fresh}`."""
        raw_lost = [self.hold.pop() for _ in range(min(count, len(self.hold)))]
        return serialize_hold(raw_lost) if self._freshness is not None else raw_lost

    def _pos_data(self) -> dict:
        return {"pos": [self.pos[0], self.pos[1]]}

    def _oxygen_and_breath(self, events, was_surface: bool) -> bool:
        """Oxy, ngạt, ngất sau khi đã bơi. Trả True nếu buổi kết thúc trong tick này."""
        now_surface = self._at_surface()
        if was_surface != now_surface:
            events.append(("surface" if now_surface else "dive", self._pos_data()))
        prev = self.oxygen_ticks
        if now_surface:
            self.oxygen_ticks = min(self.oxygen_max, prev + int(self.t["oxygen_refill_per_tick"]))
        else:
            self.oxygen_ticks = max(0, prev - 1)
        if prev > 0 and self.oxygen_ticks == 0:
            events.append(("oxygen_empty", {}))
        if self.oxygen_ticks == 0 and not now_surface:
            self.zero_oxy_ticks += 1
            if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
                self.zero_oxy_ticks = 0
                self.hp -= 1
                events.append(("choke", {"hp": self.hp}))
                if self.hp <= 0:
                    if self._freshness is not None:
                        lost = self._drop_hold_lifo(len(self.hold))
                    else:
                        lost = list(self.hold)
                        self.hold.clear()
                    events.append(("faint", {"hp": 0, "lost": lost}))
                    self._finish("fainted", events)
                    return True
        else:
            self.zero_oxy_ticks = 0
        return False

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

    # --- lát 2 (TV2): gọi giỏ qua TV1, hái nút mặt nước, bắt cá dưới nước -----
    def _try_add_hold_batch(self, kind: str, events, count: int, *,
                            action: str, target_key: str, target_id: str) -> bool:
        """Thêm nguyên tử `count` món qua `try_add_hold` của TV1 mà không sửa hàm TV1.

        Kiểm chỗ trống TRƯỚC khi gọi `try_add_hold` để:
        - Bảo đảm nguyên tử cả đàn (TICKET-02 §1.1) cho mọi `count >= 1`.
        - Phát đúng payload `hold_full` chính thức theo PRD-0 v1.0
          (`{"action", "node_id"|"fish_id", "required", "free"}`).
        """
        if count <= 0:
            return False
        free = max(0, int(self.t["hold_capacity"]) - len(self.hold))
        if free < count:
            events.append(("hold_full", {
                "action": action,
                target_key: target_id,
                "required": count,
                "free": free,
            }))
            return False
        for _ in range(count):
            if not self.try_add_hold(kind, events):
                return False
        return True

    def _nearest_in_radius(self, entities, radius: float):
        """Chọn thực thể gần nhất trong `radius` (<=), tie-break tất định bằng `id_key`."""
        best = None
        best_key = None
        for e in entities:
            dist = math.dist(self.pos, e["pos"])
            if dist <= radius:
                key = (dist, id_key(e["id"]))
                if best_key is None or key < best_key:
                    best = e
                    best_key = key
        return best

    def _try_harvest(self, events):
        """Hái nút rau `ready` gần nhất khi đang ở mặt nước (PRD-0 v1.0, TICKET-02 §1.1)."""
        if not self._at_surface():
            return
        ready_nodes = (n for n in self.nodes if n["regrow_ticks"] == 0)
        node = self._nearest_in_radius(ready_nodes, self.t["interact_radius"])
        if node is None:
            return
        amount = int(self.t["node_yield"])
        if not self._try_add_hold_batch(node["kind"], events, amount,
                                        action="gather", target_key="node_id", target_id=node["id"]):
            return
        node["regrow_ticks"] = max(1, int(round(self.t["regrow_s"] * TICK)))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": amount}))

    def _try_catch(self, events):
        """Bắt đàn cá gần nhất khi dưới nước và hết hồi chiêu (PRD-0 v1.0, TICKET-02 §1.1)."""
        if self.catch_cd_ticks > 0 or self._at_surface():
            return
        fish = self._nearest_in_radius(self.fish, self.t["catch_radius"])
        if fish is None:
            return
        amount = int(self.t["fish_yield"][fish["kind"]])
        if not self._try_add_hold_batch(fish["kind"], events, amount,
                                        action="catch", target_key="fish_id", target_id=fish["id"]):
            return
        self.fish = [f for f in self.fish if f["id"] != fish["id"]]
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": amount}))

    # --- Phase 2 (TV2, T220–T223): Cá Sấu Năm Chèo, rơi hàng LIFO, ngất --------
    def _monsters_step(self, events) -> bool:
        """Cập nhật thủy quái và xử lý tối đa một hit. Trả True nếu buổi kết thúc vì ngất."""
        if not self.monsters or self._monster_cfg is None:
            return False
        hitter = step_monsters(self.monsters, self._monster_cfg, self.t["bounds"], self.pos, self.invuln_ticks)
        if hitter is None:
            return False
        self.hp -= 1
        loss_ratio = float(self._monster_cfg.get("loss_ratio", 0.5))
        drop_count = math.floor(len(self.hold) * loss_ratio)
        lost = self._drop_hold_lifo(drop_count)
        self.invuln_ticks = int(self._monster_cfg.get("invuln_ticks", 90))
        events.append(("monster_hit", {
            "monster_id": hitter["id"],
            "hp": self.hp,
            "lost": lost,
            "pos": [self.pos[0], self.pos[1]],
        }))
        if self.hp <= 0:
            rem_lost = self._drop_hold_lifo(len(self.hold))
            events.append(("faint", {
                "cause": "monster",
                "lost": rem_lost,
                "hp": 0,
            }))
            self._finish("fainted", events)
            return True
        return False
