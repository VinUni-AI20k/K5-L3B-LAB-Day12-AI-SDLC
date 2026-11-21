"""Thủy quái buổi sáng — Cá Sấu Năm Chèo (Phase 2, TICKET-02 §1.2, §4.3–4.5, T220–T223).

Hoàn toàn đọc thông số từ `tuning["gather"]["monsters"]` (không hard-code số chuẩn):
  - Patrol: di chuyển tới waypoint đích ở `patrol_speed`, đến nơi đổi mục tiêu cho bước sau.
  - Chase: khi người chơi ở `d >= depths[0]` và cách `<= detect_radius`, đuổi ở `chase_speed`;
    trở về `patrol` khi cách `> exit_radius` hoặc người chơi lên `d < depths[0]`.
  - Recoil: 60 bước tính từ bước sau sau khi gây hit, lùi `recoil_dist / recoil_ticks` mỗi bước
    theo hướng xa người chơi chốt lúc chạm (trùng tâm dùng `+x`), không gây hit; hết recoil về
    `patrol`, chỉ xét phát hiện/chạm từ bước kế tiếp.
  - Hit: sau khi cả hai di chuyển, tối đa 1 hit/bước (gần nhất, hòa theo `id_key`), yêu cầu
    `invuln_ticks == 0`, khoảng cách `<= hit_radius`, `d >= depths[0]`.
"""

import math

from ..ids import id_key, sort_by_id

TICK = 60.0


def build_monsters(monster_cfg, scenario_monsters, day: int, ids) -> list:
    """Dựng danh sách thủy quái theo `scenario.gather.monsters[]` hoặc `spawns[]` lọc theo `from_day`."""
    if scenario_monsters is not None:
        src = scenario_monsters
    elif isinstance(monster_cfg, dict) and isinstance(monster_cfg.get("spawns"), list):
        src = [sp for sp in monster_cfg["spawns"] if int(sp.get("from_day", 1)) <= day]
    else:
        src = []

    monsters = []
    for m in src:
        wps = [[float(wp[0]), float(wp[1])] for wp in m["waypoints"]]
        pos_src = m.get("pos", wps[0])
        rd = m.get("recoil_dir")
        entry = {
            "id": m["id"],
            "kind": m["kind"],
            "pos": [float(pos_src[0]), float(pos_src[1])],
            "waypoints": wps,
            "target_idx": int(m.get("target_idx", 1)),
            "state": m.get("state", "patrol"),
            "state_ticks_left": int(m.get("state_ticks_left", 0)),
            "recoil_dir": [float(rd[0]), float(rd[1])] if rd is not None else None,
        }
        ids.reserve(entry["id"])
        monsters.append(entry)
    return monsters


def serialize_monsters(monsters) -> list:
    """Xuất danh sách thủy quái cho snapshot, sắp tất định theo id."""
    return [
        {
            "id": m["id"],
            "kind": m["kind"],
            "pos": [m["pos"][0], m["pos"][1]],
            "waypoints": [[wp[0], wp[1]] for wp in m["waypoints"]],
            "target_idx": m["target_idx"],
            "state": m["state"],
            "state_ticks_left": m["state_ticks_left"],
            "recoil_dir": [m["recoil_dir"][0], m["recoil_dir"][1]] if m["recoil_dir"] is not None else None,
        }
        for m in sort_by_id(monsters)
    ]


def _clamp_pos(pos: list, bounds: dict, depths: list) -> None:
    x_lo, x_hi = bounds["x"]
    d_lo = max(bounds["d"][0], depths[0])
    d_hi = min(bounds["d"][1], depths[1])
    if pos[0] < x_lo:
        pos[0] = float(x_lo)
    elif pos[0] > x_hi:
        pos[0] = float(x_hi)
    if pos[1] < d_lo:
        pos[1] = float(d_lo)
    elif pos[1] > d_hi:
        pos[1] = float(d_hi)


def _move_toward(pos: list, target: list, step_dist: float) -> bool:
    """Di chuyển `pos` về `target` tối đa `step_dist`. Trả True nếu chạm mục tiêu."""
    dx = target[0] - pos[0]
    dd = target[1] - pos[1]
    dist = math.hypot(dx, dd)
    if dist <= step_dist + 1e-9:
        pos[0] = float(target[0])
        pos[1] = float(target[1])
        return True
    pos[0] += (dx / dist) * step_dist
    pos[1] += (dd / dist) * step_dist
    return False


def _patrol_step(m: dict, sp: dict, bounds: dict) -> None:
    wp = m["waypoints"][m["target_idx"]]
    arrived = _move_toward(m["pos"], wp, float(sp["patrol_speed"]) / TICK)
    _clamp_pos(m["pos"], bounds, sp["depths"])
    if arrived:
        m["target_idx"] = 1 - m["target_idx"]


def step_monsters(monsters: list, monster_cfg: dict, bounds: dict, player_pos: list, invuln_ticks: int):
    """Cập nhật toàn bộ thủy quái theo id rồi xét tối đa một hit.

    Trả về con thủy quái gây hit (dict) hoặc None nếu không có hit trong bước này.
    Con gây hit được chuyển sẵn sang trạng thái `recoil` (bắt đầu lùi từ bước kế tiếp).
    """
    if not monsters or not isinstance(monster_cfg, dict):
        return None
    species_map = monster_cfg.get("species") or {}
    eligible_for_hit = []

    for m in sort_by_id(monsters):
        sp = species_map.get(m["kind"])
        if sp is None:
            continue
        depths = sp["depths"]
        min_depth = float(depths[0])
        state = m["state"]

        if state == "recoil":
            recoil_ticks = max(1, int(sp["recoil_ticks"]))
            step_dist = float(sp["recoil_dist"]) / recoil_ticks
            rx, rd = m["recoil_dir"] if m["recoil_dir"] is not None else (1.0, 0.0)
            m["pos"][0] += rx * step_dist
            m["pos"][1] += rd * step_dist
            _clamp_pos(m["pos"], bounds, depths)
            m["state_ticks_left"] -= 1
            if m["state_ticks_left"] <= 0:
                # Hết recoil về patrol; chỉ xét phát hiện và chạm từ bước kế tiếp (TICKET-02 §1.2).
                m["state"] = "patrol"
                m["state_ticks_left"] = 0
                m["recoil_dir"] = None
            continue

        dist = math.dist(m["pos"], player_pos)
        if state == "patrol":
            if player_pos[1] >= min_depth and dist <= float(sp["detect_radius"]):
                m["state"] = "chase"
                _move_toward(m["pos"], player_pos, float(sp["chase_speed"]) / TICK)
                _clamp_pos(m["pos"], bounds, depths)
            else:
                _patrol_step(m, sp, bounds)
        elif state == "chase":
            if player_pos[1] < min_depth or dist > float(sp["exit_radius"]):
                m["state"] = "patrol"
                _patrol_step(m, sp, bounds)
            else:
                _move_toward(m["pos"], player_pos, float(sp["chase_speed"]) / TICK)
                _clamp_pos(m["pos"], bounds, depths)

        eligible_for_hit.append((m, sp))

    if invuln_ticks > 0:
        return None

    hitter = None
    best_key = None
    for m, sp in eligible_for_hit:
        if player_pos[1] < float(sp["depths"][0]):
            continue
        dist = math.dist(m["pos"], player_pos)
        if dist <= float(sp["hit_radius"]):
            key = (dist, id_key(m["id"]))
            if best_key is None or key < best_key:
                best_key = key
                hitter = (m, sp)

    if hitter is None:
        return None

    m, sp = hitter
    dx = m["pos"][0] - player_pos[0]
    dd = m["pos"][1] - player_pos[1]
    norm = math.hypot(dx, dd)
    recoil_dir = [1.0, 0.0] if norm == 0.0 else [dx / norm, dd / norm]
    m["state"] = "recoil"
    m["state_ticks_left"] = int(sp["recoil_ticks"])
    m["recoil_dir"] = recoil_dir
    return m
