"""Cảnh báo dễ nhận biết (Phase 4, AC-P4-04). CHỈ ĐỌC snapshot và tuning, không đổi trạng thái sim.

Ba cảnh báo, mỗi cái có biểu tượng và chữ (không chỉ dựa vào màu):
- `monster_near` (thủy quái gần): người chơi dưới nước và một Cá Sấu cách `<= detect_radius` của loài, hoặc đang đuổi.
- `oxygen_low` (oxy sắp hết): dưới nước và oxy `<= OXYGEN_LOW_RATIO` của oxy tối đa; oxy = 0 thì mức `danger` (đang ngạt).
- `customer_angry` (khách sắp giận): khách đang chờ món và kiên nhẫn còn `<= CUSTOMER_ANGRY_RATIO` của `patience_s`.

Hai tỉ lệ dưới đây đề không cho số (Ticket-04 chưa đọc được bản gốc), ghi ở `docs/clarify.md` #14; đổi ở đây là đủ.
Chỉ dùng trong cửa sổ `chonoi.live` (trường `alerts` của GET /state); headless không ghi trường này.
"""

import math

OXYGEN_LOW_RATIO = 0.25  # trùng mốc thanh oxy chuyển đỏ trong HUD
CUSTOMER_ANGRY_RATIO = 0.25

LEVEL_ORDER = {"danger": 0, "warning": 1}


def _alert(kind, level, icon, text, **data):
    return {"id": kind, "level": level, "icon": icon, "text": text, **data}


def gather_alerts(snap, gather_tuning, tick_hz):
    p = snap.get("player")
    if not p or p.get("at_surface", True):
        return []
    out = []
    oxy, oxy_max = p.get("oxygen_ticks"), p.get("oxygen_max_ticks")
    if oxy is not None and oxy_max:
        if oxy == 0:
            out.append(_alert("oxygen_low", "danger", "🫁", "HẾT OXY — đang ngạt, nổi lên ngay!", seconds=0))
        elif oxy <= OXYGEN_LOW_RATIO * oxy_max:
            secs = math.ceil(oxy / tick_hz)
            out.append(_alert("oxygen_low", "warning", "🫁", f"OXY SẮP HẾT — còn {secs} s, nổi lên!", seconds=secs))
    species = (gather_tuning.get("monsters") or {}).get("species", {})
    near = []
    for m in snap.get("monsters") or []:
        sp = species.get(m.get("kind"))
        if sp is None:
            continue
        dist = math.dist(p["pos"], m["pos"])
        if m.get("state") == "chase" or dist <= sp["detect_radius"]:
            near.append((dist, m["id"]))
    if near:
        dist, mid = min(near)
        out.append(_alert("monster_near", "danger", "🐊", f"CÁ SẤU GẦN — {mid} cách {dist:.0f} m, tránh xa!",
                          monster_ids=[i for _, i in sorted(near)], distance=round(dist, 1)))
    return out


def quan_alerts(snap, quan_tuning, tick_hz):
    full = round(quan_tuning["patience_s"] * tick_hz)
    angry = []
    for c in snap.get("customers") or []:
        left = c.get("patience_ticks_left")
        if c.get("state") == "waiting" and left is not None and left <= CUSTOMER_ANGRY_RATIO * full:
            angry.append((left, c["id"], c.get("table_id")))
    if not angry:
        return []
    left, cid, table = min(angry)
    secs = math.ceil(left / tick_hz)
    return [_alert("customer_angry", "warning", "😠", f"KHÁCH SẮP GIẬN — {cid} bàn {table} còn {secs} s",
                   customer_ids=[a[1] for a in sorted(angry)], seconds=secs)]


def compute(snap, tuning):
    """Danh sách cảnh báo cho snapshot (danger trước, rồi theo id). Menu, Shop, đã kết thúc: rỗng."""
    if snap.get("state") == "finished":
        return []
    phase = snap.get("phase") or snap.get("mode")
    hz = tuning["tick_hz"]
    if phase == "gather":
        out = gather_alerts(snap, tuning["gather"], hz)
    elif phase == "quan":
        out = quan_alerts(snap, tuning["quan"], hz)
    else:
        out = []
    return sorted(out, key=lambda a: (LEVEL_ORDER[a["level"]], a["id"]))
