"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Theo PRD mục F, cập nhật oxy và ngạt sau khi bơi, trước khi xử lý nút bấm.
Hái và bắt cá ở gather_actions; tuning có fish_speed bật FishSchools (v1.1).
Contract v1.0 tiếp tục dùng cá đứng yên và giữ nguyên snapshot.
"""

import math

from ..ids import sort_by_id
from ..inventory import hold_to_items
from .fish import FishSchools
from .current import Current
from . import freshness, monsters
from .gather_actions import handle_catch_fish, handle_gather_node
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    @classmethod
    def from_contract(cls, contract, scenario, streams, ids, *, day=1, active_upgrades=None):
        """Điểm ghép cho runner/day: truyền manifest và nâng cấp đang có hiệu lực.

        Các caller cũ truyền tuning vẫn giữ API __init__ hiện tại. Owner runner
        dùng factory này khi ghép extension và adapter v1.2.
        """
        tuning = dict(contract["tuning"])
        if "freshness" in contract:
            tuning["freshness"] = contract["freshness"]
        return cls(tuning, scenario, streams, ids, day=day,
                   extensions=contract.get("extensions", ()), active_upgrades=active_upgrades)

    def __init__(self, tuning, scenario, streams, ids, day=1, *, extensions=None, active_upgrades=None):
        t = tuning["gather"]
        self.t = t
        self.tick_hz = tuning["tick_hz"]
        self.day = day
        self.extensions = frozenset(tuning.get("extensions", ()) if extensions is None else extensions)
        self.active_upgrades = dict(tuning.get("active_upgrades", {}) if active_upgrades is None else active_upgrades)
        self.shop_upgrades = tuning.get("shop", {}).get("upgrades", {})
        self.freshness = tuning.get("freshness")
        self.current = (Current(t["current"], scenario, streams, self.tick_hz)
                        if "current" in self.extensions else None)
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
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        if self.freshness is not None:
            self.hold = freshness.initialize(self.hold, ids)
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.monsters = monsters.build(tuning, scenario, day) if "monsters" in t else []
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif scenario.get("random_fish", True):
            src_fish = t["fish_initial"]
        else:
            src_fish = []
        # v1.0 giữ nguyên cá đứng yên; v1.1 dùng module bơi/sinh theo tuning.
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0)} for f in src_fish]
        self._fish_schools = None
        if "fish_speed" in t:
            self._fish_schools = FishSchools(t, self.tick_hz, scenario, streams, ids)
            self.fish = self._fish_schools.schools
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        if self.freshness is not None:
            return freshness.export(sort_by_id(self.hold))
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": freshness.export(self.hold) if self.freshness is not None else self.hold,
            "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      **({"age_ticks": f["age_ticks"]} if self._fish_schools is not None else {})}
                     for f in sort_by_id(self.fish)],
            **({"current": self.current.snapshot()} if self.current is not None else {}),
            **({"monsters": [{"id": m["id"], "kind": m["kind"], "pos": m["pos"], "state": m["state"],
                              "state_ticks_left": m["state_ticks_left"]} for m in sort_by_id(self.monsters)]}
               if "monsters" in self.t else {}),
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        if self.done:
            return []
        events = []
        if self.freshness is not None:
            freshness.advance(self.hold, self.freshness, self.tick_hz, events)
        if self.current is not None:
            self.current.advance(events)
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # Cá có sẵn bơi trước tương tác; đàn mới chưa tham gia cho tới bước sau.
        if self._fish_schools is not None:
            self._fish_schools.advance(events)
        # 2. bơi, chặn mép và tính oxy theo độ sâu cuối bước
        was_at_surface = self._at_surface()
        self._move(inp)
        at_surface = self._at_surface()
        if was_at_surface != at_surface:
            events.append(("surface" if at_surface else "dive", {"pos": self.pos.copy()}))
        self._update_oxygen(at_surface, events)
        if self.hp == 0:
            lost = list(reversed(self.hold))
            self.hold.clear()
            if self.current is not None:
                self.current.end(events, "phase_end")
            events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
            self._finish("fainted", events)
            return self._export_events(events)
        if "monsters" in self.t:
            monsters.step(self, events)
            if self.done:
                return self._export_events(events)
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return self._export_events(events)
            handle_gather_node(self, events)
        # 4. bắt cá
        if inp.pressed("catch"):
            handle_catch_fish(self, events)
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        return self._export_events(events)

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _update_oxygen(self, at_surface, events):
        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
            return

        if self.oxygen_ticks > 0:
            self.oxygen_ticks -= 1
            if self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))

        if self.oxygen_ticks == 0:
            # Bước vừa chạm oxy 0 cũng được tính vào thời gian ngạt.
            self.zero_oxy_ticks += 1
            if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
                self.zero_oxy_ticks = 0
                self.hp -= 1
                events.append(("choke", {"hp": self.hp}))

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        if self.current is not None:
            self.current.end(events, "phase_end")
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _export_events(self, events):
        if self.freshness is not None:
            for name, data in events:
                if name in ("faint", "monster_hit"):
                    data["lost"] = freshness.export(data["lost"])
        return events

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        drift = self.current.displacement(self.pos[1]) if self.current is not None else 0
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            if i == 0:
                self.pos[i] += drift
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
