"""HUD độ tươi (Phase 3, P3-06 / AC-P3-05). CHỈ ĐỌC snapshot và tuning, không đổi trạng thái sim.

Từ contract 1.2 (Ticket-03) giỏ `hold`, kho `stock` và `customers[].reserved` là mảng cá thể `{id, kind, fresh}`
(`docs/contracts/README.md`, mục kho cá thể). Hàm `view` gom cho cửa sổ chơi:
- `items`: cá thể đang hiển thị (giỏ khi Lặn, kho khi Quán hoặc Shop) với `fresh` (điểm) và `spoiled`;
- `spoiled_count`, `min_fresh`;
- `affected_orders`: đơn bị ảnh hưởng ở quán, gồm khách đang chờ có hàng giữ chỗ đã ươn (`spoiled_reserved`) và
  đơn không làm được (`order_status` là `unfulfillable`).
Ngưỡng ươn đọc từ `tuning.freshness.spoil_below` (ươn khi `fresh < spoil_below`, giống `chonoi/freshness.py`).
Snapshot v1.1 (giỏ là chuỗi loại, kho là object đếm) thì không có cá thể: `view` trả None và UI giữ cách hiển thị cũ.
"""


def _individuals(arr):
    if not isinstance(arr, list):
        return []
    return [x for x in arr if isinstance(x, dict) and "fresh" in x and "id" in x]


def _item(it, spoil_below):
    return {"id": it["id"], "kind": it.get("kind"), "fresh": it["fresh"], "spoiled": it["fresh"] < spoil_below}


def _reserved_ids(reserved):
    """`reserved` v1.2 là mảng cá thể (hoặc mảng id); v1.1 là object đếm thì không có id."""
    if not isinstance(reserved, list):
        return [], []
    ids, spoiled_inline = [], []
    for r in reserved:
        if isinstance(r, dict) and "id" in r:
            ids.append(r["id"])
            if "fresh" in r:
                spoiled_inline.append(r)
        elif isinstance(r, str):
            ids.append(r)
    return ids, spoiled_inline


def affected_orders(snap, spoil_below, spoiled_ids):
    out = []
    for c in snap.get("customers") or []:
        if c.get("state") != "waiting":
            continue
        ids, inline = _reserved_ids(c.get("reserved"))
        bad = sorted({i for i in ids if i in spoiled_ids} | {r["id"] for r in inline if r["fresh"] < spoil_below})
        if bad:
            reason = "spoiled_reserved"
        elif c.get("order_status") == "unfulfillable":
            reason = "unfulfillable"
        else:
            continue
        out.append({"customer_id": c["id"], "table_id": c.get("table_id"), "dish_id": c.get("dish_id"),
                    "reason": reason, "item_ids": bad})
    return out


def view(snap, tuning):
    """Dữ liệu HUD độ tươi, hoặc None nếu contract chưa có `freshness` hoặc snapshot chưa có cá thể."""
    f = tuning.get("freshness")
    if not isinstance(f, dict):
        return None
    spoil_below = f["spoil_below"]
    phase = snap.get("phase") or snap.get("mode")
    source = snap.get("hold") if phase == "gather" else snap.get("stock")
    items = [_item(it, spoil_below) for it in _individuals(source)]
    has_reserved = any(isinstance(c.get("reserved"), list) for c in snap.get("customers") or [])
    if not items and not has_reserved and not _individuals(snap.get("hold")) and not _individuals(snap.get("stock")):
        return None
    spoiled_ids = {i["id"] for i in items if i["spoiled"]}
    return {
        "fresh_max": f["fresh_max"],
        "spoil_below": spoil_below,
        "items": items,
        "spoiled_count": len(spoiled_ids),
        "min_fresh": min((i["fresh"] for i in items), default=None),
        "affected_orders": affected_orders(snap, spoil_below, spoiled_ids) if phase == "quan" else [],
    }
