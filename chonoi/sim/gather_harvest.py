"""Gather lát 2 — hái nút + bắt cá.

`gather.py` đã gọi sẵn hai hàm dưới đây đúng chỗ trong một bước:
  - `try_gather`: khi bấm `interact` mà KHÔNG ở bến (bến đã xét trước).
  - `try_catch`:  khi bấm `catch`.

Dùng được trên `sim` (GatherSim):
  sim.t (tuning gather), sim.pos, sim.nodes, sim.fish, sim.hold, sim.catch_cd_ticks, sim._at_surface()
  sim._add_to_hold(kind, n, events, source) -> bool   # thiếu chỗ: tự phát hold_full {**source, required, free}
      source = {"action": "catch", "fish_id": id} hoặc {"action": "gather", "node_id": id}
Số liệu chỉ đọc từ sim.t (interact_radius, node_yield, regrow_s, catch_radius, catch_cooldown_s, fish_yield).
Sự kiện: events.append((tên, data)).
Mở rộng net (TODO, khi bật "net" trong extensions): sim.net = {level, catch_radius, max_schools} hoặc None (cấp 0 = luật lõi).
"""


import math

from ..ids import sort_by_id
from . import gather_skills as skills

TICK = 60.0


def _within(sim, items, radius):
    """Các phần tử trong `radius`, gần nhất trước; bằng khoảng cách thì id nhỏ hơn (sort_by_id rồi sort ổn định)."""
    near = [(math.dist(sim.pos, e["pos"]), e) for e in sort_by_id(items)]
    return [e for d, e in sorted((x for x in near if x[0] <= radius), key=lambda x: x[0])]


def _nearest(sim, items, radius):
    """Phần tử gần người chơi nhất trong `radius`, hoặc None."""
    found = _within(sim, items, radius)
    return found[0] if found else None


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
    if not sim._add_to_hold(node["kind"], count, events, {"action": "gather", "node_id": node["id"]}):
        return
    node["regrow_ticks"] = int(round(sim.t["regrow_s"] * TICK))
    events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": count}))


def try_catch(sim, events):
    """Bắt cá gần nhất trong bán kính bắt, chỉ khi hết hồi chiêu và đang dưới nước.

    - Luật lõi: bán kính catch_radius, một đàn mỗi lần.
    - Kỹ năng lưới (giữ F, xem gather_skills.py): bán kính lớn hơn, tối đa net_max_schools đàn, gần nhất trước.
    - Giỏ không đủ chỗ cho cả `fish_yield[kind]` món: phát `hold_full`, cá ở lại. Nếu CHƯA bắt được đàn nào thì
      KHÔNG vào hồi chiêu; đã bắt được rồi thì dừng ở đàn không vừa.
    - Có bắt được: phát `fish_caught` cho từng đàn, đặt catch_cd_ticks = catch_cooldown_s * 60 một lần.
    """
    if sim.catch_cd_ticks > 0 or sim._at_surface():
        return
    caught = 0
    for fish in _within(sim, sim.fish, skills.catch_radius(sim))[:skills.max_catch(sim)]:
        count = int(sim.t["fish_yield"][fish["kind"]])
        if not sim._add_to_hold(fish["kind"], count, events, {"action": "catch", "fish_id": fish["id"]}):
            break
        sim.fish.remove(fish)
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": count}))
        caught += 1
    if caught:
        sim.catch_cd_ticks = int(round(sim.t["catch_cooldown_s"] * TICK))
