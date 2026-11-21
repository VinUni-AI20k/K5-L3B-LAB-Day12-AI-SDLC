"""Buổi sáng — Lặn & Hái (`gather`).

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Thứ tự mỗi bước: bộ đếm và mọc lại, bơi và oxy, Cá Sấu (v1.1, `monsters.py`), cập bến hoặc hái, bắt cá, hết giờ.
Khi ngất, bước kết thúc ngay và kho bàn giao rỗng.
"""

import math

from ..errors import BadInput
from ..freshness import Freshness
from ..ids import sort_by_id
from ..inventory import hold_to_items, inventory_schema, validate_individuals
from .fish import FishDynamics
from .monsters import MonsterDynamics, active_spawns, make_monster, snapshot_monster
from .ramp import ramp_velocity

AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, *, day=1, contract_version="1.1", item_ids=None):
        t = tuning["gather"]
        self.day = day  # số Ngày (chế độ day); quái mặc định theo `from_day` (P2-04)
        self.t = t
        self.tick_hz = tuning["tick_hz"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = round(t["oxygen_max_s"] * self.tick_hz)
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self._freshness = Freshness(tuning) if inventory_schema(contract_version) == "individuals" else None
        self._item_ids = ids if item_ids is None else item_ids
        self.hold = self._load_hold(scenario.get("hold", []))
        self.time_left_ticks = scenario.get("time_left_ticks", round(t["duration_s"] * self.tick_hz))
        self.phase_tick = 0
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        initial = t["fish_initial"]
        v11 = isinstance(initial, int)
        random_fish = scenario.get("random_fish", True)
        src_fish = scenario.get("fish", initial if random_fish and not v11 else [])
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0)} for f in src_fish]
        if v11:
            for fish, source in zip(self.fish, src_fish):
                fish["age_ticks"] = source.get("age_ticks", 0)
        # Cá Sấu (v1.1): scenario `monsters` THAY THẾ bố trí mặc định của Ngày
        mt = t.get("monsters")
        self.invuln_ticks = p.get("invuln_ticks", 0)
        src_monsters = scenario["monsters"] if "monsters" in scenario else (active_spawns(mt, day) if mt else [])
        self.monsters = [make_monster(m) for m in src_monsters]
        self._monster_dynamics = MonsterDynamics(t, self.tick_hz) if mt else None
        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])
        self._fish_dynamics = FishDynamics(t, self.tick_hz, streams, ids) if v11 and random_fish else None
        if self._fish_dynamics is not None and "fish" not in scenario:
            self._fish_dynamics.populate(self.fish)
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def _load_hold(self, hold):
        # Giữ thứ tự nhặt. Ở v1.2, fresh bên trong sim là số nguyên đơn vị.
        if self._freshness is None:
            return list(hold)
        if isinstance(hold, list) and len(hold) > self.t["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
        f = self._freshness
        items = validate_individuals(hold, f.to_points(f.max_units))
        for item in items:
            self._item_ids.reserve(item["id"])
            item["fresh"] = f.to_units(item["fresh"])
        return items

    def _visible_item(self, item):
        return {**item, "fresh": self._freshness.to_points(item["fresh"])}

    def _visible_hold(self, hold):
        return list(hold) if self._freshness is None else [self._visible_item(item) for item in hold]

    def inventory_items(self) -> dict | list:
        if self._freshness is not None:
            return self._visible_hold(self.hold)
        return hold_to_items(self.hold)

    def drop_hold(self, count):
        """Bỏ count món mới nhất. Payload theo thứ tự rơi, mới nhất trước."""
        if count <= 0:
            return []
        lost = self._visible_hold(self.hold[-count:][::-1])
        del self.hold[-count:]
        return lost

    def snapshot(self) -> dict:
        snap = {
            "player": {"pos": self.pos.copy(), "vel": self.vel.copy(), "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self._visible_hold(self.hold), "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{**f, "pos": f["pos"].copy()} for f in sort_by_id(self.fish)],
        }
        if self._monster_dynamics is not None:
            snap["player"]["invuln_ticks"] = self.invuln_ticks
            snap["monsters"] = [snapshot_monster(m) for m in sort_by_id(self.monsters)]
        return snap

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        self._age_hold(events)
        # 2. bơi + chặn mép, sau đó tính oxy tại vị trí mới
        was_at_surface = self._at_surface()
        self._move(inp)
        at_surface = self._at_surface()
        if at_surface != was_at_surface:
            events.append(("surface" if at_surface else "dive", {"pos": self.pos.copy()}))
        self._update_oxygen(at_surface, events)
        if self.done:
            return events
        # 2b. Cá Sấu: bơi, đuổi, cắn (Máu, mất giỏ, bất tử); Máu về 0 thì ngất
        if self._monster_dynamics is not None:
            self._monster_dynamics.step(self, at_surface, events)
            if self.done:
                return events

        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if at_surface:
                self._harvest(events)
        # 4. bắt cá
        if inp.pressed("catch") and not at_surface and self.catch_cd_ticks == 0:
            self._catch(events)
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        elif self._fish_dynamics is not None:
            self._fish_dynamics.step(self.fish, self.phase_tick, events)
        return events

    def _update_oxygen(self, at_surface, events):
        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
            return

        if self.oxygen_ticks > 0:
            self.oxygen_ticks -= 1
            if self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        if self.oxygen_ticks > 0:
            return

        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
            self.zero_oxy_ticks = 0
            self.hp -= 1
            events.append(("choke", {"hp": self.hp}))
            if self.hp == 0:
                lost = self.drop_hold(len(self.hold))
                events.append(("faint", {"cause": "choke", "lost": lost, "hp": self.hp}))
                self._finish("fainted", events)

    def _harvest(self, events):
        ready = (node for node in self.nodes if node["regrow_ticks"] == 0)
        node = self._nearest_in_range(ready, self.t["interact_radius"])
        if node is None:
            return
        node_id, kind = node["id"], node["kind"]
        amount = self.t["node_yield"]
        if not self._store_in_hold(kind, amount, events, {"action": "gather", "node_id": node_id}):
            return
        node["regrow_ticks"] = round(self.t["regrow_s"] * self.tick_hz)
        events.append(("gather", {"node_id": node_id, "kind": kind, "amount": amount}))

    def _catch(self, events):
        fish = self._nearest_in_range(self.fish, self.t["catch_radius"])
        if fish is None:
            return
        fish_id, kind = fish["id"], fish["kind"]
        count = self.t["fish_yield"][kind]
        if not self._store_in_hold(kind, count, events, {"action": "catch", "fish_id": fish_id}):
            return
        self.fish.remove(fish)
        self.catch_cd_ticks = round(self.t["catch_cooldown_s"] * self.tick_hz)
        events.append(("fish_caught", {"fish_id": fish_id, "kind": kind, "yield": count}))

    def _nearest_in_range(self, entities, radius):
        # Sắp theo id trước để khoảng cách bằng nhau luôn chọn id nhỏ hơn.
        selected = None
        nearest_distance = radius
        for entity in sort_by_id(entities):
            distance = math.dist(self.pos, entity["pos"])
            if distance < nearest_distance or (selected is None and distance == nearest_distance):
                selected = entity
                nearest_distance = distance
        return selected

    def _store_in_hold(self, kind, count, events, pickup):
        free = self.t["hold_capacity"] - len(self.hold)
        if count > free:
            events.append(("hold_full", {**pickup, "required": count, "free": free}))
            return False
        if self._freshness is None:
            self.hold.extend([kind] * count)
        else:
            self.hold.extend({"id": self._item_ids.new("I"), "kind": kind, "fresh": self._freshness.max_units}
                             for _ in range(count))
        return True

    def _age_hold(self, events):
        f = self._freshness
        if f is None:
            return
        decay = f.decay(self.phase)
        for item in sort_by_id(self.hold):
            before = item["fresh"]
            item["fresh"] = max(0, before - decay)
            if not f.is_spoiled(before) and f.is_spoiled(item["fresh"]):
                events.append(("spoiled", {"item_id": item["id"], "kind": item["kind"], "location": "hold"}))  # Ticket-03

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
            self.pos[i] += self.vel[i] / self.tick_hz
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
