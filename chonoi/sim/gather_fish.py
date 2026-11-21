"""Đàn cá v1.1 — sinh đầu ca, sinh theo lịch, bơi.

`gather.py` gọi:
  - `spawn_initial(sim)`: khi dựng buổi (random_fish bật, scenario không khai fish).
  - `swim(sim, events)` rồi `spawn_scheduled(sim, events)`: cuối bước, chỉ khi còn giờ và random_fish bật.

Số liệu đọc từ sim.t: fish_initial, fish_max, fish_spawn_ticks, fish_spawn_clearance, fish_spawn_x,
fish_spawn_depths, fish_weights, fish_speed, fish_turn_ticks, fish_x, fish_depths.
Ngẫu nhiên chỉ qua sim.rng.get("fish_spawn") / sim.rng.get("fish_turn").
"""

import math

TICK = 60.0


def _valid_points(sim, kind):
    t = sim.t
    clear = t["fish_spawn_clearance"]
    pts = []
    for x in t["fish_spawn_x"]:
        for d in t["fish_spawn_depths"][kind]:
            p = (float(x), float(d))
            if all(math.dist(p, f["pos"]) > clear for f in sim.fish):
                pts.append(p)
    return pts


def spawn_one(sim):
    """Sinh tối đa một đàn: chọn loài theo trọng số (chuẩn hóa trên các loài còn điểm hợp lệ),
    chọn đều một điểm của loài, hướng ban đầu theo seed. Trả đàn mới hoặc None nếu hết điểm."""
    rng = sim.rng.get("fish_spawn")
    weights = sim.t["fish_weights"]
    options = [(k, _valid_points(sim, k)) for k in weights]
    options = [(k, pts) for k, pts in options if pts]
    if not options:
        return None
    total = sum(weights[k] for k, _ in options)
    r = rng.random() * total
    kind, pts = options[-1]
    for k, p in options:
        if r < weights[k]:
            kind, pts = k, p
            break
        r -= weights[k]
    pos = pts[rng.randrange(len(pts))]
    f = {"id": sim.ids.new("F"), "kind": kind, "pos": list(pos),
         "heading_deg": rng.uniform(0, 360), "age_ticks": 0}
    sim.fish.append(f)
    return f


def spawn_initial(sim):
    """Đầu ca: fish_initial đàn ở các điểm khác nhau (khoảng cách > clearance bảo đảm khác điểm)."""
    for _ in range(int(sim.t["fish_initial"])):
        if spawn_one(sim) is None:
            break


def spawn_scheduled(sim, events):
    """Tại phase_tick = fish_spawn_ticks·k (k ≥ 1), sau khi cá bơi: sinh tối đa một đàn nếu dưới trần."""
    every = int(sim.t["fish_spawn_ticks"])
    if sim.phase_tick % every != 0 or len(sim.fish) >= int(sim.t["fish_max"]):
        return
    f = spawn_one(sim)
    if f is not None:
        events.append(("fish_spawned", {"id": f["id"], "kind": f["kind"], "pos": list(f["pos"])}))


def swim(sim, events):
    """TODO(cá bơi): mỗi đàn (theo id) bơi fish_speed m/s trong fish_x × fish_depths[loài].
    Ở bước bơi thứ fish_turn_ticks·k (theo age_ticks) đổi hướng theo seed TRƯỚC khi di chuyển.
    Tới mép: phản xạ phần quãng đường còn lại, đảo thành phần hướng vuông góc mép (chạm góc đảo cả hai).
    Tăng age_ticks sau mỗi bước bơi. Đàn vừa sinh tham gia từ bước sau."""
