"""Cá Sấu Năm Chèo: spawn, tuần tra, đuổi, va chạm và recoil ở Gather."""

import math

from ..errors import BadInput
from ..ids import sort_by_id


DEFAULT_MONSTERS = {
    "species": {"ca_sau": {
        "patrol_speed": 1.0, "chase_speed": 3.0,
        "detect_radius": 10.0, "exit_radius": 16.0,
        "depths": [10, 30], "hit_radius": 1.5,
        "recoil_ticks": 60, "recoil_dist": 2.0,
    }},
    "spawns": [
        {"id": "M1", "kind": "ca_sau", "pos": [60, 24],
         "waypoints": [[60, 24], [64, 24]], "from_day": 1},
        {"id": "M2", "kind": "ca_sau", "pos": [85, 18],
         "waypoints": [[85, 18], [89, 18]], "from_day": 3},
    ],
    "invuln_ticks": 90,
    "loss_ratio": 0.5,
}

DEFAULT_UPGRADES = {
    "oxygen": [
        {"level": 1, "price": 200, "oxygen_max_s": 45},
        {"level": 2, "price": 400, "oxygen_max_s": 60},
    ],
    "hp": [
        {"level": 1, "price": 250, "hp_max": 4},
        {"level": 2, "price": 500, "hp_max": 5},
    ],
}


def upgrade_limit(tuning, category, level, field, base):
    if isinstance(level, bool) or not isinstance(level, int):
        raise BadInput(f"cấp nâng cấp {category} không hợp lệ: {level!r}")
    if level == 0:
        return base
    upgrades = tuning.get("shop", {}).get("upgrades") or DEFAULT_UPGRADES
    for item in upgrades.get(category, []):
        if item["level"] == level:
            return item[field]
    raise BadInput(f"cấp nâng cấp {category} không tồn tại: {level}")


def monster_config(gather_cfg):
    """V1.1 dùng manifest; manifest v1.0 chưa có khóa thì dùng preset v1.1."""
    return gather_cfg.get("monsters") or DEFAULT_MONSTERS


def init_monsters(gather_cfg, scenario_block, day=1):
    cfg = monster_config(gather_cfg)
    source = (scenario_block["monsters"] if "monsters" in scenario_block else
              [m for m in cfg["spawns"] if m["from_day"] <= day])
    monsters = []
    for m in source:
        monsters.append({
            "id": m["id"], "kind": m["kind"],
            "pos": [float(v) for v in m["pos"]],
            "waypoints": [[float(v) for v in point] for point in m["waypoints"]],
            "target_idx": m.get("target_idx", 1),
            "state": m.get("state", "patrol"),
            "state_ticks_left": m.get("state_ticks_left", 0),
            "recoil_dir": (None if m.get("recoil_dir") is None else
                           [float(v) for v in m["recoil_dir"]]),
        })
    return sort_by_id(monsters)


def _clamp(pos, bounds, depths):
    pos[0] = min(max(pos[0], bounds["x"][0]), bounds["x"][1])
    pos[1] = min(max(pos[1], depths[0]), depths[1])


def _toward(monster, target, distance):
    dx = target[0] - monster["pos"][0]
    dd = target[1] - monster["pos"][1]
    norm = math.hypot(dx, dd)
    if norm <= distance + 1e-12:
        monster["pos"][:] = target
        return True
    if norm:
        step = distance / norm
        monster["pos"][0] += dx * step
        monster["pos"][1] += dd * step
    return False


def _output_pos(pos):
    return [0.0 if round(v, 3) == 0 else round(v, 3) for v in pos]


def monster_snapshot(monsters):
    """Không làm tròn trạng thái mô phỏng; chỉ định dạng bản sao khi xuất."""
    return [{**m, "pos": _output_pos(m["pos"]),
             "waypoints": [_output_pos(p) for p in m["waypoints"]],
             "recoil_dir": (None if m["recoil_dir"] is None else list(m["recoil_dir"]))}
            for m in sort_by_id(monsters)]


def step_monsters(monsters, gather_cfg, player_pos, hp, invuln_ticks, hold, tick_hz=60):
    """Cập nhật quái sau bước bơi/ngạt; trả (hp, bất tử, events, ngất)."""
    cfg = monster_config(gather_cfg)
    bounds = gather_cfg["bounds"]
    just_finished_recoil = set()
    for m in sort_by_id(monsters):
        species = cfg["species"][m["kind"]]
        depths = species["depths"]
        if m["state"] == "recoil":
            distance = species["recoil_dist"] / species["recoil_ticks"]
            m["pos"][0] += m["recoil_dir"][0] * distance
            m["pos"][1] += m["recoil_dir"][1] * distance
            _clamp(m["pos"], bounds, depths)
            m["state_ticks_left"] -= 1
            if m["state_ticks_left"] == 0:
                m["state"] = "patrol"
                m["recoil_dir"] = None
                just_finished_recoil.add(m["id"])
            continue
        if m["state"] == "stunned":
            m["state_ticks_left"] -= 1
            if m["state_ticks_left"] == 0:
                m["state"] = "patrol"
                just_finished_recoil.add(m["id"])
            continue

        distance_to_player = math.dist(m["pos"], player_pos)
        if m["state"] == "patrol" and player_pos[1] >= depths[0] and distance_to_player <= species["detect_radius"]:
            m["state"] = "chase"
        elif m["state"] == "chase" and (player_pos[1] < depths[0] or distance_to_player > species["exit_radius"]):
            m["state"] = "patrol"

        if m["state"] == "chase":
            _toward(m, player_pos, species["chase_speed"] / tick_hz)
        else:
            arrived = _toward(m, m["waypoints"][m["target_idx"]], species["patrol_speed"] / tick_hz)
            if arrived:
                m["target_idx"] = 1 - m["target_idx"]
        _clamp(m["pos"], bounds, depths)

    if invuln_ticks:
        return hp, invuln_ticks, [], False
    candidates = []
    for m in sort_by_id(monsters):
        if m["state"] not in ("patrol", "chase") or m["id"] in just_finished_recoil:
            continue
        species = cfg["species"][m["kind"]]
        if player_pos[1] >= species["depths"][0]:
            distance = math.dist(m["pos"], player_pos)
            if distance <= species["hit_radius"]:
                candidates.append((distance, m))
    if not candidates:
        return hp, invuln_ticks, [], False

    _, monster = min(candidates, key=lambda pair: pair[0])  # sort_by_id giữ hòa theo id
    species = cfg["species"][monster["kind"]]
    hp = max(0, hp - 1)
    invuln_ticks = cfg["invuln_ticks"]
    drop_count = math.floor(len(hold) * cfg["loss_ratio"])
    lost = [hold.pop() for _ in range(drop_count)]
    dx = monster["pos"][0] - player_pos[0]
    dd = monster["pos"][1] - player_pos[1]
    norm = math.hypot(dx, dd)
    monster["recoil_dir"] = [dx / norm, dd / norm] if norm else [1.0, 0.0]
    monster["state"] = "recoil"
    monster["state_ticks_left"] = species["recoil_ticks"]
    events = [("monster_hit", {"monster_id": monster["id"], "hp": hp,
                               "lost": lost, "pos": _output_pos(player_pos)})]
    if hp == 0:
        events.append(("faint", {"cause": "monster", "lost": list(reversed(hold)), "hp": 0}))
        hold.clear()
    return hp, invuln_ticks, events, hp == 0
