"""Gather lát 2 — hái nút + bắt cá.

`gather.py` đã gọi sẵn hai hàm dưới đây đúng chỗ trong một bước:
  - `try_gather`: khi bấm `interact` mà KHÔNG ở bến (bến đã xét trước).
  - `try_catch`:  khi bấm `catch`.

Dùng được trên `sim` (GatherSim):
  sim.t (tuning gather), sim.pos, sim.nodes, sim.fish, sim.hold, sim.catch_cd_ticks, sim._at_surface()
  sim._add_to_hold(kind, n, events) -> bool   # thêm cuối giỏ; thiếu chỗ thì tự phát hold_full, trả False
Số liệu chỉ đọc từ sim.t (interact_radius, node_yield, regrow_s, catch_radius, catch_cooldown_s, fish_yield).
Sự kiện: events.append((tên, data)).
"""


import math

from ..ids import sort_by_id

TICK = 60.0


def _nearest(sim, items, radius):
    """Phần tử gần người chơi nhất trong `radius`; bằng khoảng cách thì id nhỏ hơn (sort_by_id ổn định)."""
    best, best_d = None, None
    for e in sort_by_id(items):
        d = math.dist(sim.pos, e["pos"])
        if d <= radius and (best_d is None or d < best_d):
            best, best_d = e, d
    return best


def try_gather(sim, events):
    """Hái nút `ready` gần nhất trong interact_radius, chỉ khi đang ở mặt nước.

    - Giỏ không đủ chỗ: `_add_to_hold` tự phát `hold_full`, nút giữ nguyên (vẫn ready).
    - Thành công: phát `gather`, nút phải chờ regrow_s giây mới hái lại được.
    """
    if not sim._at_surface():
        return
    ready = [n for n in sim.nodes if n["regrow_ticks"] == 0]
    node = _nearest(sim, ready, float(sim.t["interact_radius"]))
    if node is None:
        return
    count = int(sim.t["node_yield"])
    if not sim._add_to_hold(node["kind"], count, events):
        return
    node["regrow_ticks"] = int(round(sim.t["regrow_s"] * TICK))
    events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "count": count,
                              "hold_count": len(sim.hold)}))


def try_catch(sim, events):
    """Bắt cá gần nhất trong catch_radius, chỉ khi hết hồi chiêu và đang dưới nước.

    - Giỏ không đủ chỗ cho cả `fish_yield[kind]` món: phát `hold_full`, cá ở lại, KHÔNG vào hồi chiêu.
    - Thành công: xóa cá khỏi đàn, phát `fish_caught`, đặt catch_cd_ticks = catch_cooldown_s * 60.
    """
    if sim.catch_cd_ticks > 0 or sim._at_surface():
        return
    fish = _nearest(sim, sim.fish, float(sim.t["catch_radius"]))
    if fish is None:
        return
    count = int(sim.t["fish_yield"][fish["kind"]])
    if not sim._add_to_hold(fish["kind"], count, events):
        return
    sim.fish.remove(fish)
    sim.catch_cd_ticks = int(round(sim.t["catch_cooldown_s"] * TICK))
    events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "count": count,
                                   "hold_count": len(sim.hold)}))
