"""Cá Sấu Năm Chèo v1.1 — tuần tra, đuổi, chạm, recoil.

`gather.py` gọi:
  - `build(sim, scenario)`: khi dựng buổi -> danh sách quái (scenario.monsters thay mặc định).
  - `update(sim, events) -> bool`: mỗi bước sau oxy/ngạt; trả True nếu người chơi ngất (dừng bước).
  - `snapshot(sim)`: mảng `monsters[]` trong snapshot.

Số liệu: sim.t["monsters"] {species, spawns, invuln_ticks, loss_ratio}. Ngày hiện tại: sim.day.
Ngất do chạm: gọi sim._faint(events, "monster").
"""

from ..ids import sort_by_id


def build(sim, scenario):
    """Bố trí mặc định theo Ngày (from_day <= sim.day). Waypoint đầu là vị trí xuất phát, target_idx mặc định 1.
    TODO(Cá Sấu): nhận scenario["monsters"] {id,kind,pos,waypoints,target_idx,state,state_ticks_left,recoil_dir}."""
    out = []
    for sp in sim.t["monsters"]["spawns"]:
        if sp["from_day"] <= sim.day:
            out.append({"id": sp["id"], "kind": sp["kind"], "pos": [float(c) for c in sp["pos"]],
                        "waypoints": [list(w) for w in sp["waypoints"]], "target_idx": 1,
                        "state": "patrol", "state_ticks_left": 0, "recoil_dir": None})
    for m in out:
        sim.ids.reserve(m["id"])
    return sort_by_id(out)


def update(sim, events) -> bool:
    """TODO(Cá Sấu): theo id: patrol 1.0 m/s giữa 2 waypoint / chase 3.0 m/s khi người chơi d ≥ 10 và
    cách ≤ 10 m / về patrol khi > 16 m hoặc người chơi lên d < 10 / recoil 60 bước, mỗi bước 2/60 m.
    Sau khi di chuyển: tối đa MỘT hit (gần nhất, hòa theo id) nếu ≤ 1.5 m, người chơi d ≥ 10, hết bất tử:
    -1 Máu, bỏ floor(len(hold) * loss_ratio) món theo LIFO, bất tử invuln_ticks, phát monster_hit
    {monster_id, hp, lost, pos}. Máu 0 -> sim._faint(events, "monster"); return True."""
    return False


def snapshot(sim):
    return [{k: m[k] for k in ("id", "kind", "pos", "state", "target_idx", "state_ticks_left", "recoil_dir")}
            for m in sort_by_id(sim.monsters)]
