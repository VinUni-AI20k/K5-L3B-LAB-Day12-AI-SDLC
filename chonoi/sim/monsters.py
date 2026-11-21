"""Cá Sấu Năm Chèo và va chạm trong buổi lặn (TICKET-02 mục 1.2)."""

import math

from ..ids import id_key, sort_by_id
from ..items import order_json

TICK = 60.0


def build_monsters(tuning, fixtures, ids, day=1):
    """Scenario thay toàn bộ quái mặc định; standalone gather dùng bố trí Ngày 1."""
    source = fixtures if fixtures is not None else [
        spawn for spawn in tuning["spawns"] if spawn["from_day"] <= day
    ]
    monsters = []
    for source_monster in source:
        m = dict(source_monster)
        m["pos"] = [float(v) for v in m["pos"]]
        m["waypoints"] = [[float(v) for v in point] for point in m["waypoints"]]
        m["target_idx"] = int(m.get("target_idx", 1))
        m["state"] = m.get("state", "patrol")
        m["state_ticks_left"] = int(m.get("state_ticks_left", 0))
        recoil_dir = m.get("recoil_dir")
        m["recoil_dir"] = [float(v) for v in recoil_dir] if recoil_dir is not None else None
        ids.reserve(m["id"])
        monsters.append(m)
    return sort_by_id(monsters)


def update_monsters(sim, events, can_hit=True):
    """Di chuyển quái theo id, áp dụng tối đa một va chạm; trả True nếu người chơi ngất."""
    tuning = sim.t["monsters"]
    # Con đang recoil ở ĐẦU bước không được chạm trong bước này, kể cả khi vừa hết recoil
    # ('hết recoil về patrol, xét phát hiện/chạm từ bước kế').
    recoiling = {m["id"] for m in sim.monsters if m["state"] == "recoil"}
    for monster in sort_by_id(sim.monsters):
        species = tuning["species"][monster["kind"]]
        if monster["state"] == "recoil":
            _move_recoil(monster, species, sim.t["bounds"])
            monster["state_ticks_left"] -= 1
            if monster["state_ticks_left"] <= 0:
                monster["state"] = "patrol"
                monster["state_ticks_left"] = 0
                monster["recoil_dir"] = None
            # Hết recoil thì chỉ về patrol từ bước sau.
            continue

        distance = math.dist(monster["pos"], sim.pos)
        too_shallow = sim.pos[1] < species["depths"][0]
        if monster["state"] == "chase" and (distance > species["exit_radius"] or too_shallow):
            monster["state"] = "patrol"
        elif (monster["state"] == "patrol" and not too_shallow
              and distance <= species["detect_radius"]):
            monster["state"] = "chase"

        if monster["state"] == "chase":
            _move_towards(monster["pos"], sim.pos, species["chase_speed"], sim.t["bounds"], species["depths"])
        else:
            target = monster["waypoints"][monster["target_idx"]]
            arrived = _move_towards(monster["pos"], target, species["patrol_speed"],
                                    sim.t["bounds"], species["depths"])
            if arrived:
                monster["target_idx"] = 1 - monster["target_idx"]

    if not can_hit:
        return False
    contacts = []
    for monster in sim.monsters:
        if monster["state"] == "recoil" or monster["id"] in recoiling:
            continue
        species = tuning["species"][monster["kind"]]
        if sim.pos[1] >= species["depths"][0]:
            distance = math.dist(monster["pos"], sim.pos)
            if distance <= species["hit_radius"]:
                contacts.append((distance, id_key(monster["id"]), monster))
    if not contacts:
        return False

    monster = min(contacts, key=lambda hit: (hit[0], hit[1]))[2]
    distance = math.dist(monster["pos"], sim.pos)
    if distance == 0:
        recoil_dir = [1.0, 0.0]
    else:
        recoil_dir = [(monster["pos"][i] - sim.pos[i]) / distance for i in range(2)]
    lost_count = math.floor(len(sim.hold) * tuning["loss_ratio"])
    lost = order_json(reversed(sim.hold[-lost_count:])) if lost_count else []  # mảng cá thể, thứ tự bỏ LIFO
    if lost_count:
        del sim.hold[-lost_count:]
    sim.hp = max(0, sim.hp - 1)
    sim.invuln_ticks = int(tuning["invuln_ticks"])
    monster["state"] = "recoil"
    monster["state_ticks_left"] = int(tuning["species"][monster["kind"]]["recoil_ticks"])
    monster["recoil_dir"] = recoil_dir
    events.append(("monster_hit", {"monster_id": monster["id"], "hp": sim.hp,
                                    "lost": lost, "pos": list(sim.pos)}))
    if sim.hp > 0:
        return False

    faint_lost = order_json(reversed(sim.hold))
    sim.hold = []
    events.append(("faint", {"cause": "monster", "lost": faint_lost, "hp": 0}))
    sim._finish("fainted", events)
    return True


def _move_towards(pos, target, speed, bounds, depths):
    dx, dd = target[0] - pos[0], target[1] - pos[1]
    distance = math.hypot(dx, dd)
    step = speed / TICK
    if distance <= step:
        pos[0], pos[1] = target[0], target[1]
        arrived = True
    else:
        pos[0] += dx / distance * step
        pos[1] += dd / distance * step
        arrived = False
    _clamp(pos, bounds, depths)
    return arrived


def _move_recoil(monster, species, bounds):
    direction = monster["recoil_dir"] or [1.0, 0.0]
    distance = species["recoil_dist"] / species["recoil_ticks"]
    monster["pos"][0] += direction[0] * distance
    monster["pos"][1] += direction[1] * distance
    _clamp(monster["pos"], bounds, species["depths"])


def _clamp(pos, bounds, depths):
    pos[0] = min(bounds["x"][1], max(bounds["x"][0], pos[0]))
    pos[1] = min(depths[1], max(depths[0], pos[1]))
