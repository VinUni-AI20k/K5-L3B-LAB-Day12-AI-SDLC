"""Cá Sấu Năm Chèo: di chuyển trước, chọn tối đa một va chạm sau cùng."""

import math

from ..ids import sort_by_id


def make_monsters(config, scenario, day):
    spawns = scenario.get("monsters")
    if spawns is None:
        spawns = [m for m in config["spawns"] if m["from_day"] <= day]
    return sort_by_id([
        {"id": m["id"], "kind": m["kind"], "pos": list(m["pos"]), "waypoints": m["waypoints"],
         "target_idx": m.get("target_idx", 1), "state": m.get("state", "patrol"),
         "state_ticks_left": m.get("state_ticks_left", 0), "recoil_dir": m.get("recoil_dir")}
        for m in spawns
    ])


def _approach(pos, target, distance):
    dx, dd = target[0] - pos[0], target[1] - pos[1]
    length = math.hypot(dx, dd)
    if length <= distance:
        pos[:] = target
        return True
    pos[0] += dx * distance / length
    pos[1] += dd * distance / length
    return False


def move_and_choose_hit(monsters, player, config, bounds, hz, invulnerable):
    nearest = None
    nearest_distance = math.inf
    for m in monsters:  # sorted by id, so equal distances keep the first monster
        spec = config["species"][m["kind"]]
        pos = m["pos"]
        depth_min, depth_max = spec["depths"]
        recovering = m["state"] == "recoil"
        if recovering:
            step = spec["recoil_dist"] / spec["recoil_ticks"]
            pos[0] += step * m["recoil_dir"][0]
            pos[1] += step * m["recoil_dir"][1]
            m["state_ticks_left"] -= 1
            if m["state_ticks_left"] == 0:
                m.update(state="patrol", recoil_dir=None)
        else:
            distance = math.dist(pos, player)
            if player[1] < depth_min or distance > spec["exit_radius"]:
                m["state"] = "patrol"
            elif distance <= spec["detect_radius"]:
                m["state"] = "chase"
            if m["state"] == "chase":
                _approach(pos, player, spec["chase_speed"] / hz)
            else:
                if _approach(pos, m["waypoints"][m["target_idx"]], spec["patrol_speed"] / hz):
                    m["target_idx"] = 1 - m["target_idx"]

        pos[0] = min(bounds["x"][1], max(bounds["x"][0], pos[0]))
        pos[1] = min(depth_max, max(depth_min, pos[1]))
        if not recovering and not invulnerable and player[1] >= depth_min:
            distance = math.dist(pos, player)
            if distance <= spec["hit_radius"] and distance < nearest_distance:
                nearest, nearest_distance = m, distance
    if nearest is not None:
        dx = nearest["pos"][0] - player[0]
        dd = nearest["pos"][1] - player[1]
        direction = [dx / nearest_distance, dd / nearest_distance] if nearest_distance else [1.0, 0.0]
        nearest.update(state="recoil", recoil_dir=direction,
                       state_ticks_left=config["species"][nearest["kind"]]["recoil_ticks"])
    return nearest
