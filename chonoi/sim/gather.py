"""Buổi sáng — Lặn & Hái (`gather`) v1.1: bơi, oxy, ngạt, hái, cá bơi/sinh và hỗ trợ ngày."""

from __future__ import annotations

import math

from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")
SPECIES_ORDER = ("ca_linh", "ca_loc", "ca_keo")


def _r3(v: float) -> float:
    return round(float(v), 3)


def _weighted_choice(rng, candidates: list[str], weights: dict[str, float]) -> str:
    total = sum(float(weights[k]) for k in candidates)
    pick = rng.random() * total
    acc = 0.0
    for k in candidates:
        acc += float(weights[k])
        if pick <= acc:
            return k
    return candidates[-1]


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(
        self,
        tuning,
        scenario,
        streams,
        ids,
        *,
        day: int = 1,
        active_upgrades: dict | None = None,
        initial_money: int = 0,
        initial_earned: int = 0,
        initial_reputation: float | None = None,
    ):
        t = tuning["gather"]
        self.tuning = tuning
        self.t = t
        self.tick_hz = float(tuning.get("tick_hz", TICK))
        self.rng = streams
        self.ids = ids
        self.day = int(day)
        self.phase_tick = 0

        oxy_s = float(t["oxygen_max_s"])
        hp_max = int(t["hp_max"])
        if active_upgrades:
            shop_up = tuning.get("shop", {}).get("upgrades", {})
            ox_lv = int(active_upgrades.get("oxygen", 0))
            hp_lv = int(active_upgrades.get("hp", 0))
            for entry in shop_up.get("oxygen", []):
                if entry["level"] == ox_lv:
                    oxy_s = float(entry["oxygen_max_s"])
            for entry in shop_up.get("hp", []):
                if entry["level"] == hp_lv:
                    hp_max = int(entry["hp_max"])

        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(oxy_s * self.tick_hz))
        self.oxygen_ticks = int(p.get("oxygen_ticks", self.oxygen_max))
        self.hp_max = hp_max
        self.hp = int(p.get("hp", hp_max))
        self.zero_oxy_ticks = int(p.get("zero_oxy_ticks", 0))
        self.invuln_ticks = int(p.get("invuln_ticks", 0))
        self.catch_cd_ticks = int(p.get("catch_cd_ticks", 0))
        self.hold = list(scenario.get("hold", []))
        self.time_left_ticks = int(scenario.get("time_left_ticks", int(round(t["duration_s"] * self.tick_hz))))
        self.random_fish = bool(scenario.get("random_fish", True))

        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [
            {"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
             "regrow_ticks": int(n.get("regrow_ticks", 0))}
            for n in src_nodes
        ]
        for n in self.nodes:
            ids.reserve(n["id"])

        self.fish = []
        if "fish" in scenario:
            for f in scenario["fish"]:
                ids.reserve(f["id"])
                self.fish.append({
                    "id": f["id"],
                    "kind": f["kind"],
                    "pos": [float(c) for c in f["pos"]],
                    "heading_deg": float(f.get("heading_deg", 0.0)),
                    "age_ticks": int(f.get("age_ticks", 0)),
                })
        elif self.random_fish:
            self._spawn_initial_fish()

        self.monsters = []
        mcfg = t["monsters"]
        if "monsters" in scenario:
            for m in scenario["monsters"]:
                ids.reserve(m["id"])
                rdir = m.get("recoil_dir")
                self.monsters.append({
                    "id": m["id"],
                    "kind": m["kind"],
                    "pos": [float(c) for c in m["pos"]],
                    "waypoints": [[float(c) for c in wp] for wp in m["waypoints"]],
                    "target_idx": int(m.get("target_idx", 1)),
                    "state": m.get("state", "patrol"),
                    "state_ticks_left": int(m.get("state_ticks_left", 0)),
                    "recoil_dir": [float(rdir[0]), float(rdir[1])] if rdir is not None else None,
                })
        else:
            for sp in mcfg["spawns"]:
                if int(sp["from_day"]) <= self.day:
                    ids.reserve(sp["id"])
                    self.monsters.append({
                        "id": sp["id"],
                        "kind": sp["kind"],
                        "pos": [float(sp["pos"][0]), float(sp["pos"][1])],
                        "waypoints": [[float(c) for c in wp] for wp in sp["waypoints"]],
                        "target_idx": 1,
                        "state": "patrol",
                        "state_ticks_left": 0,
                        "recoil_dir": None,
                    })

        self.money = int(initial_money)
        self.earned = int(initial_earned)
        self.reputation = float(
            tuning["quan"]["reputation_initial"] if initial_reputation is None else initial_reputation
        )
        self.done = False
        self.reason = None

    def _spawn_initial_fish(self):
        count = int(self.t["fish_initial"])
        spawn_xs = [float(x) for x in self.t["fish_spawn_x"]]
        spawn_depths = self.t["fish_spawn_depths"]
        weights = self.t["fish_weights"]
        rng_spawn = self.rng.get("fish_spawn")
        rng_swim = self.rng.get("fish_swim")

        occupied = set()
        for _ in range(count):
            by_species = {}
            for sk in SPECIES_ORDER:
                pts = [(x, float(d)) for x in spawn_xs for d in spawn_depths[sk] if (x, float(d)) not in occupied]
                if pts:
                    by_species[sk] = pts
            if not by_species:
                break
            kind = _weighted_choice(rng_spawn, list(by_species), weights)
            px, pd = rng_spawn.choice(by_species[kind])
            occupied.add((px, pd))
            heading = rng_swim.uniform(0.0, 360.0)
            self.fish.append({
                "id": self.ids.new("F"),
                "kind": kind,
                "pos": [px, pd],
                "heading_deg": heading,
                "age_ticks": 0,
            })

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def _store_in_hold(self, kind, count) -> int:
        if count > self.t["hold_capacity"] - len(self.hold):
            return 0
        self.hold.extend([kind] * count)
        return count

    def snapshot(self) -> dict:
        return {
            "player": {
                "pos": [_r3(self.pos[0]), _r3(self.pos[1])],
                "vel": [_r3(self.vel[0]), _r3(self.vel[1])],
                "heading_deg": _r3(self.heading),
                "oxygen_ticks": self.oxygen_ticks,
                "oxygen_max_ticks": self.oxygen_max,
                "hp": self.hp,
                "hp_max": self.hp_max,
                "zero_oxy_ticks": self.zero_oxy_ticks,
                "invuln_ticks": self.invuln_ticks,
                "catch_cd_ticks": self.catch_cd_ticks,
                "at_surface": self._at_surface(),
            },
            "hold": list(self.hold),
            "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [
                {
                    "id": n["id"],
                    "pos": [_r3(n["pos"][0]), _r3(n["pos"][1])],
                    "kind": n["kind"],
                    "ready": n["regrow_ticks"] == 0,
                    "regrow_ticks": n["regrow_ticks"],
                }
                for n in sort_by_id(self.nodes)
            ],
            "fish": [
                {
                    "id": f["id"],
                    "pos": [_r3(f["pos"][0]), _r3(f["pos"][1])],
                    "kind": f["kind"],
                    "heading_deg": _r3(f["heading_deg"]),
                    "age_ticks": int(f["age_ticks"]),
                }
                for f in sort_by_id(self.fish)
            ],
            "monsters": [
                {
                    "id": m["id"],
                    "kind": m["kind"],
                    "pos": [_r3(m["pos"][0]), _r3(m["pos"][1])],
                    "waypoints": [[_r3(wp[0]), _r3(wp[1])] for wp in m["waypoints"]],
                    "target_idx": int(m["target_idx"]),
                    "state": m["state"],
                    "state_ticks_left": int(m["state_ticks_left"]),
                    "recoil_dir": (
                        [_r3(m["recoil_dir"][0]), _r3(m["recoil_dir"][1])]
                        if m["recoil_dir"] is not None else None
                    ),
                }
                for m in sort_by_id(self.monsters)
            ],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))

        was_at_surface = self._at_surface()
        self._move(inp)
        at_surface = self._at_surface()
        if was_at_surface != at_surface:
            events.append(("surface" if at_surface else "dive", {"pos": [_r3(self.pos[0]), _r3(self.pos[1])]}))

        oxygen_before = self.oxygen_ticks
        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
        else:
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if oxygen_before > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))

        if not at_surface and self.oxygen_ticks == 0:
            self.zero_oxy_ticks += 1
            if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
                self.zero_oxy_ticks = 0
                self.hp = max(0, self.hp - 1)
                events.append(("choke", {"hp": self.hp}))
                if self.hp == 0:
                    lost = self.hold[::-1]
                    self.hold = []
                    events.append(("faint", {"cause": "choke", "lost": lost, "hp": self.hp}))
                    self._finish("fainted", events)
                    return events
        else:
            self.zero_oxy_ticks = 0

        if self._step_monsters_and_hit(events):
            return events

        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            self._harvest(events)

        if inp.pressed("catch"):
            self._catch(events)

        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events

        if self.random_fish:
            self._step_fish_swim()
            self._maybe_spawn_fish(events)

        return events

    def _step_fish_swim(self):
        speed = float(self.t["fish_speed"]) / self.tick_hz
        turn_ticks = int(self.t["fish_turn_ticks"])
        xlo, xhi = [float(c) for c in self.t["fish_x"]]
        depths_map = self.t["fish_depths"]
        rng_swim = self.rng.get("fish_swim")

        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if f["age_ticks"] % turn_ticks == 0:
                f["heading_deg"] = rng_swim.uniform(0.0, 360.0)
            rad = math.radians(f["heading_deg"])
            hx, hd = math.cos(rad), math.sin(rad)
            nx = f["pos"][0] + speed * hx
            nd = f["pos"][1] + speed * hd
            dlo, dhi = [float(c) for c in depths_map[f["kind"]]]

            if nx < xlo:
                nx = min(xhi, xlo + (xlo - nx))
                hx = -hx
            elif nx > xhi:
                nx = max(xlo, xhi - (nx - xhi))
                hx = -hx
            if nd < dlo:
                nd = min(dhi, dlo + (dlo - nd))
                hd = -hd
            elif nd > dhi:
                nd = max(dlo, dhi - (nd - dhi))
                hd = -hd
            f["pos"] = [nx, nd]
            f["heading_deg"] = math.degrees(math.atan2(hd, hx)) % 360.0

    def _maybe_spawn_fish(self, events: list):
        spawn_ticks = int(self.t["fish_spawn_ticks"])
        if self.phase_tick <= 0 or self.phase_tick % spawn_ticks != 0:
            return
        if len(self.fish) >= int(self.t["fish_max"]):
            return
        clearance = float(self.t["fish_spawn_clearance"])
        spawn_xs = [float(x) for x in self.t["fish_spawn_x"]]
        spawn_depths = self.t["fish_spawn_depths"]
        by_species = {}
        for sk in SPECIES_ORDER:
            pts = [
                (x, float(d)) for x in spawn_xs for d in spawn_depths[sk]
                if all(math.dist((x, float(d)), f["pos"]) > clearance for f in self.fish)
            ]
            if pts:
                by_species[sk] = pts
        if not by_species:
            return
        rng_spawn = self.rng.get("fish_spawn")
        rng_swim = self.rng.get("fish_swim")
        kind = _weighted_choice(rng_spawn, list(by_species), self.t["fish_weights"])
        px, pd = rng_spawn.choice(by_species[kind])
        fid = self.ids.new("F")
        heading = rng_swim.uniform(0.0, 360.0)
        self.fish.append({
            "id": fid,
            "kind": kind,
            "pos": [px, pd],
            "heading_deg": heading,
            "age_ticks": 0,
        })
        events.append(("fish_spawned", {"id": fid, "kind": kind, "pos": [_r3(px), _r3(pd)]}))

    def _step_monsters_and_hit(self, events: list) -> bool:
        """Cập nhật thủy quái theo id và xét tối đa một hit; trả True nếu ngất."""
        mcfg = self.t["monsters"]
        species = mcfg["species"]
        xlo, xhi = [float(c) for c in self.t["bounds"]["x"]]
        can_hit_ids = []

        for m in sort_by_id(self.monsters):
            sp = species[m["kind"]]
            dlo, dhi = [float(c) for c in sp["depths"]]
            if m["state"] == "recoil":
                step_len = float(sp["recoil_dist"]) / float(sp["recoil_ticks"])
                rx, rd = m["recoil_dir"]
                m["pos"][0] = min(xhi, max(xlo, m["pos"][0] + rx * step_len))
                m["pos"][1] = min(dhi, max(dlo, m["pos"][1] + rd * step_len))
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"] = "patrol"
                    m["state_ticks_left"] = 0
                    m["recoil_dir"] = None
                continue

            dist_p = math.dist(self.pos, m["pos"])
            if m["state"] == "patrol":
                if self.pos[1] >= dlo and dist_p <= float(sp["detect_radius"]):
                    m["state"] = "chase"
            elif m["state"] == "chase":
                if self.pos[1] < dlo or dist_p > float(sp["exit_radius"]):
                    m["state"] = "patrol"

            if m["state"] == "chase":
                step_len = float(sp["chase_speed"]) / self.tick_hz
                dx = self.pos[0] - m["pos"][0]
                dd = self.pos[1] - m["pos"][1]
                norm = math.hypot(dx, dd)
                if norm > 1e-12:
                    mv = min(step_len, norm)
                    m["pos"][0] += (dx / norm) * mv
                    m["pos"][1] += (dd / norm) * mv
            else:
                step_len = float(sp["patrol_speed"]) / self.tick_hz
                wp = m["waypoints"][m["target_idx"]]
                dx = wp[0] - m["pos"][0]
                dd = wp[1] - m["pos"][1]
                norm = math.hypot(dx, dd)
                if norm <= step_len:
                    m["pos"] = [float(wp[0]), float(wp[1])]
                    m["target_idx"] = 1 - m["target_idx"]
                else:
                    m["pos"][0] += (dx / norm) * step_len
                    m["pos"][1] += (dd / norm) * step_len

            m["pos"][0] = min(xhi, max(xlo, m["pos"][0]))
            m["pos"][1] = min(dhi, max(dlo, m["pos"][1]))
            can_hit_ids.append(m)

        if self.invuln_ticks > 0:
            return False

        eligible = []
        for m in can_hit_ids:
            sp = species[m["kind"]]
            dlo = float(sp["depths"][0])
            if self.pos[1] >= dlo and math.dist(self.pos, m["pos"]) <= float(sp["hit_radius"]):
                eligible.append(m)
        if not eligible:
            return False

        hitter = min(eligible, key=lambda m: (math.dist(self.pos, m["pos"]), id_key(m["id"])))
        sp = species[hitter["kind"]]
        self.hp = max(0, self.hp - 1)
        drop_n = math.floor(len(self.hold) * float(mcfg["loss_ratio"]))
        lost = [self.hold.pop() for _ in range(drop_n)]
        self.invuln_ticks = int(mcfg["invuln_ticks"])

        dx = hitter["pos"][0] - self.pos[0]
        dd = hitter["pos"][1] - self.pos[1]
        norm = math.hypot(dx, dd)
        rdir = [1.0, 0.0] if norm <= 1e-12 else [dx / norm, dd / norm]
        hitter["state"] = "recoil"
        hitter["state_ticks_left"] = int(sp["recoil_ticks"])
        hitter["recoil_dir"] = rdir

        events.append(("monster_hit", {
            "monster_id": hitter["id"],
            "hp": self.hp,
            "lost": lost,
            "pos": [_r3(self.pos[0]), _r3(self.pos[1])],
        }))
        if self.hp == 0:
            rem_lost = self.hold[::-1]
            self.hold = []
            events.append(("faint", {"cause": "monster", "lost": rem_lost, "hp": 0}))
            self._finish("fainted", events)
            return True
        return False

    # --- lát 2: hái + bắt cá ------------------------------------------------------
    def _nearest(self, items, radius):
        cands = [e for e in items if math.dist(self.pos, e["pos"]) <= radius]
        return min(cands, key=lambda e: (math.dist(self.pos, e["pos"]), id_key(e["id"])), default=None)

    def _harvest(self, events):
        if not self._at_surface():
            return
        node = self._nearest([n for n in self.nodes if n["regrow_ticks"] == 0], self.t["interact_radius"])
        if node is None:
            return
        amount = self.t["node_yield"]
        free = self.t["hold_capacity"] - len(self.hold)
        if free < amount:
            events.append(("hold_full", {"action": "gather", "node_id": node["id"], "required": amount, "free": free}))
            return
        self._store_in_hold(node["kind"], amount)
        node["regrow_ticks"] = int(round(self.t["regrow_s"] * self.tick_hz))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": amount}))

    def _catch(self, events):
        if self.catch_cd_ticks > 0 or self._at_surface():
            return
        fish = self._nearest(self.fish, self.t["catch_radius"])
        if fish is None:
            return
        y = self.t["fish_yield"][fish["kind"]]
        free = self.t["hold_capacity"] - len(self.hold)
        if free < y:
            events.append(("hold_full", {"action": "catch", "fish_id": fish["id"], "required": y, "free": free}))
            return
        self._store_in_hold(fish["kind"], y)
        self.fish.remove(fish)
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * self.tick_hz))
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": y}))

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
            self.heading = math.degrees(math.atan2(md, mx)) % 360.0
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / self.tick_hz
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = float(lo)
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = float(hi)
                self.vel[i] = min(0.0, self.vel[i])
