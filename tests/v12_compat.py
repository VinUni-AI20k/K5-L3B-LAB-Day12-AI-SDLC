"""Lớp chuyển fixture P1–P2 (kho đếm) sang schema v1.2 (kho cá thể) cho regression còn hiệu lực.

Lý do (TICKET-03 [THAY THẾ] "Kho đếm theo loại -> kho cá thể"): file kho / quan.stock / customers[].reserved
đổi schema. Luật P1–P2 khác (lịch khách, bếp, bàn, kiên nhẫn, tiền) vẫn hiệu lực, nên test cũ giữ nguyên
khẳng định và chỉ đi qua lớp này:
  - ghi: stock {kind:n} -> [{id:S1..,kind,fresh:100}] (sắp kind); reserved {kind:n} -> mảng id lấy từ stock
    (thiếu -> id "MISSING" để vẫn ra mã 2); file kho {"items":{...}} -> mảng cá thể.
  - gather.hold mảng kind -> mảng cá thể H1.. fresh 100; đọc lại hold / lost / gather_end.inventory -> kind/đếm.
  - đọc: snapshot stock (mảng) -> {kind:n}; customers[].reserved (mảng id) -> {kind:n};
    cook_started.items (mảng cá thể) -> mảng kind.
Giá đã chốt theo fresh (base_price) là luật mới: test nào phụ thuộc giá ghi rõ giá mới tại chỗ.
"""

import copy

import helpers


def to_items(counts, prefix="S"):
    out, n = [], 0
    for k in sorted(counts):
        for _ in range(int(counts[k])):
            n += 1
            out.append({"id": f"{prefix}{n}", "kind": k, "fresh": 100})
    return out


def _conv_quan(q):
    if isinstance(q.get("stock"), dict) and _ok_counts(q["stock"]):
        q["stock"] = to_items(q["stock"])
    pool = {}
    for it in q.get("stock", []) or []:
        pool.setdefault(it["kind"], []).append(it["id"])
    for c in q.get("customers", []) or []:
        r = c.get("reserved")
        if isinstance(r, dict):
            ids = []
            for k in sorted(r):
                for _ in range(r[k]):
                    ids.append(pool[k].pop(0) if pool.get(k) else "MISSING")
            c["reserved"] = ids


def _ok_counts(d):
    return all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in d.values())


def to_v12(obj):
    obj = copy.deepcopy(obj)
    if isinstance(obj, dict):
        g = obj.get("gather")
        if isinstance(g, dict) and isinstance(g.get("hold"), list) and all(isinstance(k, str) for k in g["hold"]):
            g["hold"] = [{"id": f"H{i + 1}", "kind": k, "fresh": 100} for i, k in enumerate(g["hold"])]
        if isinstance(obj.get("items"), dict) and _ok_counts(obj["items"]):
            obj["items"] = to_items(obj["items"])
        if isinstance(obj.get("quan"), dict):
            _conv_quan(obj["quan"])
    return obj


def counts(items):
    out = {}
    for it in items:
        out[it["kind"]] = out.get(it["kind"], 0) + 1
    return {k: out[k] for k in sorted(out)}


def from_v12(row):
    if row.get("type") == "snapshot" and isinstance(row.get("stock"), list):
        kinds = {it["id"]: it["kind"] for it in row["stock"]}
        row["stock"] = counts(row["stock"])
        for c in row.get("customers", []) or []:
            if isinstance(c.get("reserved"), list):
                c["reserved"] = counts([{"kind": kinds.get(i, "?")} for i in c["reserved"]])
    if row.get("type") == "snapshot" and isinstance(row.get("hold"), list):
        row["hold"] = [x["kind"] if isinstance(x, dict) else x for x in row["hold"]]
    if row.get("type") == "event" and row.get("name") == "gather_end":
        inv = row["data"].get("inventory", {})
        if isinstance(inv.get("items"), list):
            inv["items"] = counts(inv["items"])
    if row.get("type") == "event" and row.get("name") in ("monster_hit", "faint"):
        lost = row["data"].get("lost")
        if isinstance(lost, list):
            row["data"]["lost"] = [x["kind"] if isinstance(x, dict) else x for x in lost]
    if row.get("type") == "event" and row.get("name") == "cook_started":
        it = row["data"].get("items")
        if isinstance(it, list) and it and isinstance(it[0], dict):
            row["data"]["items"] = [x["kind"] for x in it]
    return row


def write_json(path, obj):
    return helpers.write_json(path, to_v12(obj))


def read_jsonl(path):
    return [from_v12(r) for r in helpers.read_jsonl(path)]
