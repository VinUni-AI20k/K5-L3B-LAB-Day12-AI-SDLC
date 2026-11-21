"""Cá Sấu Năm Chèo v1.1 — tuần tra, đuổi, chạm, recoil.

`gather.py` gọi:
  - `build(sim, scenario)`: khi dựng buổi -> danh sách quái (scenario.monsters thay mặc định).
  - `update(sim, events) -> bool`: mỗi bước sau oxy/ngạt; trả True nếu người chơi ngất (dừng bước).
  - `snapshot(sim)`: mảng `monsters[]` trong snapshot.

Số liệu: sim.t["monsters"] {species, spawns, invuln_ticks, loss_ratio}. Ngày hiện tại: sim.day.
"""

import math

from ..ids import id_key, sort_by_id

TICK = 60.0


def build(sim, scenario):
    """scenario.monsters thay toàn bộ danh sách; bỏ mảng thì dùng bố trí đúng Ngày (from_day <= sim.day).
    Waypoint đầu là vị trí xuất phát, target_idx mặc định 1, state mặc định patrol."""
    if "monsters" in scenario:
        src = [{"id": m["id"], "kind": m["kind"], "pos": m["pos"], "waypoints": m["waypoints"],
                "target_idx": m.get("target_idx", 1), "state": m.get("state", "patrol"),
                "state_ticks_left": m.get("state_ticks_left", 0), "recoil_dir": m.get("recoil_dir")}
               for m in scenario["monsters"]]
    else:
        src = [{"id": sp["id"], "kind": sp["kind"], "pos": sp["pos"], "waypoints": sp["waypoints"],
                "target_idx": 1, "state": "patrol", "state_ticks_left": 0, "recoil_dir": None}
               for sp in sim.t["monsters"]["spawns"] if sp["from_day"] <= sim.day]
    out = []
    for m in src:
        m = dict(m, pos=[float(c) for c in m["pos"]], waypoints=[[float(c) for c in w] for w in m["waypoints"]])
        if m["recoil_dir"] is not None:
            m["recoil_dir"] = [float(c) for c in m["recoil_dir"]]
        out.append(m)
        sim.ids.reserve(m["id"])
    return sort_by_id(out)


def _species(sim, m):
    return sim.t["monsters"]["species"][m["kind"]]


def _clamp(sim, m):
    """Chặn theo biên map và dải độ sâu của loài."""
    lo, hi = _species(sim, m)["depths"]
    bx = sim.t["bounds"]["x"]
    m["pos"] = [min(max(m["pos"][0], bx[0]), bx[1]), min(max(m["pos"][1], lo), hi)]


def _toward(m, target, step):
    """Đi về `target` tối đa `step` m; trả True nếu tới nơi."""
    dx, dd = target[0] - m["pos"][0], target[1] - m["pos"][1]
    dist = math.hypot(dx, dd)
    if dist <= step:
        m["pos"] = [float(target[0]), float(target[1])]
        return True
    m["pos"] = [m["pos"][0] + dx / dist * step, m["pos"][1] + dd / dist * step]
    return False


def _move(sim, m):
    sp = _species(sim, m)
    if m["state"] in ("recoil", "stunned"):
        if m["state"] == "recoil":  # lùi 2/60 m mỗi bước theo hướng đã chốt, rồi chặn mép
            step = sp["recoil_dist"] / sp["recoil_ticks"]
            m["pos"] = [m["pos"][0] + m["recoil_dir"][0] * step, m["pos"][1] + m["recoil_dir"][1] * step]
            _clamp(sim, m)
        m["state_ticks_left"] -= 1
        if m["state_ticks_left"] <= 0:  # hết recoil -> patrol, xét phát hiện từ bước kế
            m["state"], m["state_ticks_left"], m["recoil_dir"] = "patrol", 0, None
        return
    p = sim.pos
    deep = p[1] >= sp["depths"][0]
    dist = math.dist(m["pos"], p)
    if m["state"] == "patrol" and deep and dist <= sp["detect_radius"]:
        m["state"] = "chase"
    elif m["state"] == "chase" and (dist > sp["exit_radius"] or not deep):
        m["state"] = "patrol"
    if m["state"] == "chase":
        _toward(m, p, sp["chase_speed"] / TICK)
    elif _toward(m, m["waypoints"][m["target_idx"]], sp["patrol_speed"] / TICK):
        m["target_idx"] = 1 - m["target_idx"]  # đổi mục tiêu cho bước sau
    _clamp(sim, m)


def update(sim, events) -> bool:
    """Cập nhật quái theo id rồi xét tối đa MỘT hit. Trả True nếu người chơi ngất."""
    for m in sort_by_id(sim.monsters):
        _move(sim, m)
    if sim.invuln_ticks > 0:
        return False
    cand = []
    for m in sim.monsters:
        if m["state"] in ("recoil", "stunned"):
            continue
        sp = _species(sim, m)
        d = math.dist(m["pos"], sim.pos)
        if sim.pos[1] >= sp["depths"][0] and d <= sp["hit_radius"]:
            cand.append((d, id_key(m["id"]), m))
    if not cand:
        return False
    m = min(cand, key=lambda c: (c[0], c[1]))[2]  # gần nhất, hòa theo id
    cfg = sim.t["monsters"]
    sim.hp = max(0, sim.hp - 1)
    n = math.floor(len(sim.hold) * cfg["loss_ratio"])
    lost = [sim.hold.pop() for _ in range(n)]  # LIFO: nhặt sau mất trước
    sim.invuln_ticks = int(cfg["invuln_ticks"])
    events.append(("monster_hit", {"monster_id": m["id"], "hp": sim.hp, "lost": lost, "pos": list(sim.pos)}))
    dx, dd = m["pos"][0] - sim.pos[0], m["pos"][1] - sim.pos[1]
    dist = math.hypot(dx, dd)
    m["recoil_dir"] = [dx / dist, dd / dist] if dist > 0 else [1.0, 0.0]  # trùng tâm dùng +x
    m["state"], m["state_ticks_left"] = "recoil", int(_species(sim, m)["recoil_ticks"])
    if sim.hp == 0:
        sim._faint(events, "monster")
        return True
    return False


def snapshot(sim):
    return [{k: m[k] for k in ("id", "kind", "pos", "state", "target_idx", "state_ticks_left", "recoil_dir")}
            for m in sort_by_id(sim.monsters)]
