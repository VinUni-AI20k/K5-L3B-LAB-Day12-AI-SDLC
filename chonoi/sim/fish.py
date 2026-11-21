"""Đàn cá buổi sáng (TICKET-02 §1.1, lát 1 của TV1).

Số liệu chỉ đọc từ `tuning.gather`. Ngẫu nhiên qua `Streams`:
`fish_init` chọn 8 điểm đầu ca, `fish_turn:<id>` đổi hướng, `fish_spawn` sinh theo lịch.
"""

import math

from ..ids import sort_by_id

_KINDS = ("ca_linh", "ca_loc", "ca_keo")


def _pairs(g):
    """36 cặp loài–vị trí, thứ tự cố định."""
    out = []
    for kind in _KINDS:
        for x in g["fish_spawn_x"]:
            for d in g["fish_spawn_depths"][kind]:
                out.append((kind, float(x), float(d)))
    return out


def initial_schools(g, streams, ids, count):
    """Đầu ca: `count` đàn ở các điểm hình học khác nhau."""
    pairs = _pairs(g)
    streams.get("fish_init").shuffle(pairs)
    seen = set()
    schools = []
    for kind, x, d in pairs:
        if (x, d) in seen:
            continue
        seen.add((x, d))
        fid = ids.new("F")
        schools.append({
            "id": fid,
            "kind": kind,
            "pos": [x, d],
            "heading_deg": streams.get(f"fish_turn:{fid}").random() * 360.0,
            "age_ticks": 0,
        })
        if len(schools) == count:
            break
    return schools


def swim(fish, g, streams):
    """Một bước bơi. Đổi hướng khi `age_ticks` đã là bội của 120 (age > 0), rồi mới di chuyển."""
    speed = float(g["fish_speed"]) / 60.0
    turn = int(g["fish_turn_ticks"])
    x_lo, x_hi = g["fish_x"]
    for f in sort_by_id(fish):
        age = int(f.get("age_ticks", 0))
        if age > 0 and age % turn == 0:
            f["heading_deg"] = streams.get(f"fish_turn:{f['id']}").random() * 360.0
        rad = math.radians(f["heading_deg"])
        dx = speed * math.cos(rad)
        dd = speed * math.sin(rad)
        d_lo, d_hi = g["fish_depths"][f["kind"]]
        nx = f["pos"][0] + dx
        nd = f["pos"][1] + dd
        flipped = False
        if nx > x_hi:
            nx = x_hi - (nx - x_hi)
            dx = -dx
            flipped = True
        elif nx < x_lo:
            nx = x_lo + (x_lo - nx)
            dx = -dx
            flipped = True
        if nd > d_hi:
            nd = d_hi - (nd - d_hi)
            dd = -dd
            flipped = True
        elif nd < d_lo:
            nd = d_lo + (d_lo - nd)
            dd = -dd
            flipped = True
        f["pos"][0] = nx
        f["pos"][1] = nd
        if flipped and (dx != 0.0 or dd != 0.0):
            f["heading_deg"] = math.degrees(math.atan2(dd, dx)) % 360.0
        f["age_ticks"] = age + 1


def spawn_if_due(fish, g, streams, ids, phase_tick, events):
    """Tại phase_tick = 360·k (k ≥ 1), sau khi cá đã bơi: tối đa một đàn."""
    every = int(g["fish_spawn_ticks"])
    if phase_tick <= 0 or phase_tick % every != 0 or len(fish) >= int(g["fish_max"]):
        return
    clearance = float(g["fish_spawn_clearance"])
    living = [tuple(f["pos"]) for f in fish]

    def free(x, d):
        return all(math.dist((x, d), p) > clearance for p in living)

    available = {}
    for kind in _KINDS:
        pts = [(float(x), float(d)) for x in g["fish_spawn_x"] for d in g["fish_spawn_depths"][kind] if free(x, d)]
        if pts:
            available[kind] = sorted(pts)
    if not available:
        return
    weights = {k: float(g["fish_weights"][k]) for k in available}
    total = sum(weights.values())
    rng = streams.get("fish_spawn")
    roll = rng.random() * total
    acc = 0.0
    kind = sorted(available)[-1]
    for k in sorted(available):
        acc += weights[k]
        if roll < acc:
            kind = k
            break
    pts = available[kind]
    x, d = pts[rng.randrange(len(pts))]
    fid = ids.new("F")
    fish.append({
        "id": fid,
        "kind": kind,
        "pos": [x, d],
        "heading_deg": streams.get(f"fish_turn:{fid}").random() * 360.0,
        "age_ticks": 0,
    })
    events.append(("fish_spawned", {"id": fid, "kind": kind, "pos": [x, d]}))
