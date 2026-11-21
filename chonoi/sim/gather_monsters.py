import math

from ..ids import sort_by_id


TICK = 60.0


def init_monsters(sim, scenario, day=1):
    tuning = sim.t["monsters"] if "monsters" in sim.t else []
    entries = scenario.get("monsters")
    if entries is None:
        entries = [
            dict(m, pos=list(m["pos"]), heading_deg=m.get("heading_deg", 180))
            for m in tuning
            if int(m.get("day", 1)) == int(day) or int(m.get("day", 1)) == int(day)
        ]
    monsters = []
    for entry in entries:
        monster_day = int(entry.get("day", day))
        if monster_day not in (day, 1 if day == 1 else 3):
            continue
        if monster_day == 1 and day not in (1, 2):
            continue
        if monster_day == 3 and day < 3:
            continue
        kind = entry.get("kind", "ca_sau")
        if kind == "ca_sau" and (monster_day == 1 and day == 1 or monster_day == 3 and day == 3):
            monsters.append({
                "id": entry["id"],
                "kind": kind,
                "pos": [float(c) for c in entry["pos"]],
                "heading_deg": float(entry.get("heading_deg", 180)),
                "state": entry.get("state", "patrol"),
                "recoil_ticks": int(entry.get("recoil_ticks", 0)),
                "hit_cooldown_ticks": int(entry.get("hit_cooldown_ticks", 0)),
                "age_ticks": int(entry.get("age_ticks", 0)),
            })
    for monster in monsters:
        sim.ids.reserve(monster["id"])
    return monsters


def step_monsters(sim, events):
    tuning = sim.t
    bounds = tuning["bounds"]
    patrol_speed = float(tuning.get("monster_patrol_speed", 1.0))
    chase_speed = float(tuning.get("monster_chase_speed", 3.0))
    enter_m = float(tuning.get("monster_chase_enter_m", 10))
    exit_m = float(tuning.get("monster_chase_exit_m", 16))
    min_depth = float(tuning.get("monster_chase_min_depth", 10))
    hit_radius = float(tuning.get("monster_hit_radius", 1.5))
    invuln_ticks = int(tuning.get("monster_invuln_ticks", 90))
    recoil_ticks = int(tuning.get("monster_recoil_ticks", 60))
    recoil_m = float(tuning.get("monster_recoil_m", 2.0))
    hit_in_step = False

    for monster in sort_by_id(sim.monsters):
        monster["age_ticks"] = monster.get("age_ticks", 0) + 1
        monster["recoil_ticks"] = max(0, monster.get("recoil_ticks", 0) - 1)
        monster["hit_cooldown_ticks"] = max(0, monster.get("hit_cooldown_ticks", 0) - 1)
        dx = sim.pos[0] - monster["pos"][0]
        dd = sim.pos[1] - monster["pos"][1]
        distance = math.hypot(dx, dd)

        if monster["state"] == "chase":
            if distance > exit_m or sim.pos[1] < min_depth:
                monster["state"] = "patrol"
        elif distance <= enter_m and sim.pos[1] >= min_depth:
            monster["state"] = "chase"

        if monster["state"] == "chase":
            if distance > 0:
                monster["pos"][0] += dx / distance * chase_speed / TICK
                monster["pos"][1] += dd / distance * chase_speed / TICK
                monster["heading_deg"] = math.degrees(math.atan2(dd, dx)) % 360
        else:
            heading = math.radians(monster["heading_deg"])
            monster["pos"][0] += math.cos(heading) * patrol_speed / TICK
            monster["pos"][1] += math.sin(heading) * patrol_speed / TICK

        lo_x, hi_x = bounds["x"]
        lo_d, hi_d = bounds["d"]
        if monster["pos"][0] <= 4:
            monster["pos"][0] = 4
            monster["heading_deg"] = 0
        elif monster["pos"][0] >= 96:
            monster["pos"][0] = 96
            monster["heading_deg"] = 180
        if monster["pos"][1] <= max(lo_d, 10):
            monster["pos"][1] = max(lo_d, 10)
            monster["heading_deg"] = 270
        elif monster["pos"][1] >= hi_d:
            monster["pos"][1] = hi_d
            monster["heading_deg"] = 90
        monster["pos"][0] = min(hi_x, max(lo_x, monster["pos"][0]))
        monster["pos"][1] = min(hi_d, max(10, monster["pos"][1]))

        monster_dx = sim.pos[0] - monster["pos"][0]
        monster_dd = sim.pos[1] - monster["pos"][1]
        collision_distance = math.hypot(monster_dx, monster_dd)
        if collision_distance <= hit_radius and sim.invuln_ticks == 0 and monster["hit_cooldown_ticks"] == 0:
            remove_count = len(sim.hold) // 2
            removed = sim.hold[-remove_count:] if remove_count else []
            if remove_count:
                del sim.hold[-remove_count:]
            sim.hp = max(0, sim.hp - 1)
            sim.invuln_ticks = invuln_ticks
            monster["hit_cooldown_ticks"] = invuln_ticks
            sim.recoil = {
                "ticks": recoil_ticks,
                "dx": 0.0 if monster_dx == 0 else monster_dx / max(collision_distance, 0.001),
                "dd": 0.0 if monster_dd == 0 else monster_dd / max(collision_distance, 0.001),
                "distance_per_tick": recoil_m / recoil_ticks,
            }
            sim.recoil_ticks = recoil_ticks
            hit_in_step = True
            events.append(("monster_hit", {
                "monster_id": monster["id"],
                "damage": 1,
                "hp": sim.hp,
                "removed": removed,
                "removed_count": len(removed),
                "invuln_ticks": invuln_ticks,
            }))
            if sim.hp == 0:
                sim.done = True
                sim.reason = "fainted"
                sim.hold = []
                events.append(("faint", {
                    "cause": "monster",
                    "pos": list(sim.pos),
                    "monster_id": monster["id"],
                }))
                events.append(("gather_end", {
                    "reason": "fainted",
                    "inventory": {"items": {}},
                }))
                return True

    if getattr(sim, "recoil_ticks", 0) > 0 and not hit_in_step:
        recoil = sim.recoil
        sim.pos[0] += recoil["dx"] * recoil["distance_per_tick"]
        sim.pos[1] += recoil["dd"] * recoil["distance_per_tick"]
        sim.pos[0] = min(bounds["x"][1], max(bounds["x"][0], sim.pos[0]))
        sim.pos[1] = min(bounds["d"][1], max(bounds["d"][0], sim.pos[1]))
        sim.recoil_ticks -= 1
    return False
