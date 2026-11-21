"""Cá Sấu Năm Chèo: di chuyển và chọn va chạm theo Test Contract v1.1."""

import math

from ..ids import sort_by_id


def load_monsters(config, scenario, day):
    sources = scenario.get("monsters")
    if sources is None:
        sources = [spawn for spawn in config.get("spawns", []) if spawn["from_day"] <= day]
    return sort_by_id([
        {
            "id": source["id"],
            "kind": source["kind"],
            "pos": list(source["pos"]),
            "waypoints": [list(point) for point in source["waypoints"]],
            "target_idx": source.get("target_idx", 1),
            "state": source.get("state", "patrol"),
            "state_ticks_left": source.get("state_ticks_left", 0),
            "recoil_dir": source.get("recoil_dir"),
        }
        for source in sources
    ])


def update_monsters(monsters, config, bounds, tick_hz, player_pos, invulnerable):
    """Trả về quái gây hit sau khi mọi quái đã di chuyển."""
    closest = None
    closest_distance = math.inf
    for monster in monsters:
        species = config["species"][monster["kind"]]
        active = _move_monster(monster, species, bounds, tick_hz, player_pos)
        if not active or invulnerable or player_pos[1] < species["depths"][0]:
            continue
        distance = math.dist(monster["pos"], player_pos)
        # Danh sách đã sắp theo ID khi khởi tạo, giữ con đầu tiên nếu hòa.
        if distance <= species["hit_radius"] and distance < closest_distance:
            closest, closest_distance = monster, distance

    if closest is not None:
        species = config["species"][closest["kind"]]
        dx = closest["pos"][0] - player_pos[0]
        dd = closest["pos"][1] - player_pos[1]
        closest["state"] = "recoil"
        closest["state_ticks_left"] = species["recoil_ticks"]
        closest["recoil_dir"] = ([dx / closest_distance, dd / closest_distance]
                                 if closest_distance else [1, 0])
    return closest


def _move_monster(monster, species, bounds, tick_hz, player_pos):
    x, depth = monster["pos"]
    state = monster["state"]
    min_depth, max_depth = species["depths"]
    if state in ("recoil", "stunned"):
        if state == "recoil":
            dx, dd = monster["recoil_dir"]
            step = species["recoil_dist"] / species["recoil_ticks"]
            x, depth = x + dx * step, depth + dd * step
        monster["state_ticks_left"] -= 1
        if monster["state_ticks_left"] == 0:
            monster["state"] = "patrol"
            monster["recoil_dir"] = None
    else:
        distance = math.dist(monster["pos"], player_pos)
        radius = species["exit_radius"] if state == "chase" else species["detect_radius"]
        if player_pos[1] >= min_depth and distance <= radius:
            monster["state"] = "chase"
            x, depth = _toward(monster["pos"], player_pos, species["chase_speed"] / tick_hz)
        else:
            monster["state"] = "patrol"
            target_idx = monster["target_idx"]
            target_x, target_depth = monster["waypoints"][target_idx]
            target = (target_x, min(max_depth, max(min_depth, target_depth)))
            x, depth = _toward(monster["pos"], target, species["patrol_speed"] / tick_hz)
            if (x, depth) == target:
                monster["target_idx"] = 1 - target_idx

    left, right = bounds["x"]
    shallow, deep = bounds["d"]
    monster["pos"] = [min(right, max(left, x)),
                      min(deep, max(shallow, min(max_depth, max(min_depth, depth))))]
    return state not in ("recoil", "stunned")


def _toward(pos, target, step):
    distance = math.dist(pos, target)
    if distance <= step:
        return tuple(target)
    return tuple(start + (end - start) * (step / distance) for start, end in zip(pos, target))
