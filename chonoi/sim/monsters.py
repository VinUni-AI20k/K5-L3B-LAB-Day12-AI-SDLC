"""Cá Sấu Năm Chèo (thủy quái) — ticket 03 Phase 2.

Luật (PRD Phase 2 §1.2):
- Patrol 1.0 m/s tới waypoint; tới nơi thì đổi mục tiêu cho **bước sau**.
- Chase 3.0 m/s khi người chơi ở d >= 10 và cách <= detect_radius; về patrol khi cách > exit_radius
  hoặc người chơi lên d < 10.
- Sau khi cả hai di chuyển: cách <= hit_radius, người chơi d >= 10, hết bất tử → mất 1 Máu,
  bỏ floor(giỏ/2) theo LIFO, bất tử 90 tick, con gây hit vào recoil 60 bước (từ bước sau).
- Recoil: lùi theo hướng xa người chơi đã chốt lúc chạm, mỗi bước 2/60 m, không gây hit.
"""

import math

from ..ids import id_key

TICK = 60


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _clamp_pos(pos, species, bounds):
    lo_x, hi_x = bounds["x"]
    lo_d, hi_d = species["depths"]
    return [_clamp(pos[0], lo_x, hi_x), _clamp(pos[1], max(lo_d, bounds["d"][0]), min(hi_d, bounds["d"][1]))]


def build(tuning, scenario, day=1):
    """Danh sách quái cho lượt: scenario thay thế toàn bộ; mặc định lấy spawn có from_day <= day."""
    conf = tuning["gather"]["monsters"]
    if "monsters" in scenario:
        out = []
        for m in scenario["monsters"]:
            out.append({
                "id": m["id"], "kind": m["kind"], "pos": [float(c) for c in m["pos"]],
                "waypoints": [[float(c) for c in w] for w in m["waypoints"]],
                "target_idx": m.get("target_idx", 1),
                "state": m.get("state", "patrol"),
                "state_ticks_left": m.get("state_ticks_left", 0),
                "recoil_dir": m.get("recoil_dir"),
            })
        return out
    out = []
    for s in conf["spawns"]:
        if s["from_day"] <= day:
            out.append({
                "id": s["id"], "kind": s["kind"], "pos": [float(c) for c in s["pos"]],
                "waypoints": [[float(c) for c in w] for w in s["waypoints"]],
                "target_idx": 1, "state": "patrol", "state_ticks_left": 0, "recoil_dir": None,
            })
    return out


def _move_one(sim, m, species, events):
    bounds = sim.t["bounds"]
    pos = m["pos"]

    if m["state"] == "recoil":
        d = m["recoil_dir"] or [1.0, 0.0]
        step_m = species["recoil_dist"] / max(1, species["recoil_ticks"])
        pos[0] += d[0] * step_m
        pos[1] += d[1] * step_m
        pos[:] = _clamp_pos(pos, species, bounds)
        m["state_ticks_left"] -= 1
        if m["state_ticks_left"] <= 0:
            m["state"] = "patrol"
            m["state_ticks_left"] = 0
            m["recoil_dir"] = None
        return

    if m["state"] == "stunned":
        m["state_ticks_left"] -= 1
        if m["state_ticks_left"] <= 0:
            m["state"] = "patrol"
            m["state_ticks_left"] = 0
        return

    dist_player = math.dist(pos, sim.pos)
    player_deep = sim.pos[1] >= species["depths"][0]

    if m["state"] == "patrol" and player_deep and dist_player <= species["detect_radius"]:
        m["state"] = "chase"
    elif m["state"] == "chase" and (not player_deep or dist_player > species["exit_radius"]):
        m["state"] = "patrol"

    if m["state"] == "chase":
        target = list(sim.pos)
        speed = species["chase_speed"]
    else:
        target = m["waypoints"][m["target_idx"]]
        speed = species["patrol_speed"]

    dx, dy = target[0] - pos[0], target[1] - pos[1]
    dist = math.hypot(dx, dy)
    step_m = speed / TICK
    if dist <= step_m:
        pos[0], pos[1] = target[0], target[1]
        if m["state"] == "patrol":
            m["target_idx"] = 1 - m["target_idx"]   # đổi mục tiêu cho bước sau
    else:
        pos[0] += dx / dist * step_m
        pos[1] += dy / dist * step_m
    pos[:] = _clamp_pos(pos, species, bounds)


def _hit(sim, conf, events):
    if sim.invuln_ticks > 0:
        return
    species_all = conf["species"]
    candidates = []
    for m in sim.monsters:
        if m["state"] in ("recoil", "stunned"):
            continue
        sp = species_all[m["kind"]]
        if sim.pos[1] < sp["depths"][0]:
            continue
        dist = math.dist(sim.pos, m["pos"])
        if dist <= sp["hit_radius"]:
            candidates.append((dist, id_key(m["id"]), m))
    if not candidates:
        return
    candidates.sort(key=lambda c: (c[0], c[1]))
    monster = candidates[0][2]
    sp = species_all[monster["kind"]]

    drop = len(sim.hold) // 2
    lost = list(reversed(sim.hold[-drop:])) if drop else []
    if drop:
        del sim.hold[-drop:]

    sim.hp -= 1
    sim.invuln_ticks = int(conf["invuln_ticks"])

    away = [sim.pos[0] - monster["pos"][0], sim.pos[1] - monster["pos"][1]]
    norm = math.hypot(*away)
    monster["recoil_dir"] = [away[0] / norm, away[1] / norm] if norm > 1e-9 else [1.0, 0.0]
    monster["state"] = "recoil"
    monster["state_ticks_left"] = int(sp["recoil_ticks"])

    events.append(("monster_hit", {"monster_id": monster["id"], "hp": sim.hp,
                                   "lost": lost, "pos": list(sim.pos)}))

    if sim.hp <= 0:
        rest = list(reversed(sim.hold))
        sim.hold.clear()
        events.append(("faint", {"cause": "monster", "lost": rest, "hp": 0}))
        sim._finish("fainted", events)


def step(sim, events):
    """Cập nhật quái rồi xét tối đa một hit (PRD: sau khi cả hai di chuyển)."""
    conf = sim.t["monsters"]
    for m in sorted(sim.monsters, key=lambda e: id_key(e["id"])):
        _move_one(sim, m, conf["species"][m["kind"]], events)
    _hit(sim, conf, events)
