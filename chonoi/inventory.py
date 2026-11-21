"""File kho v1.0 (Contract G): {"items": {id: số nguyên >= 0}}.
Từ contract 1.2 (Ticket-03) kho là KHO CÁ THỂ: {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}.

Đọc: từ chối sai schema / id lạ / số âm (BadInput -> mã 2).
Ghi: bỏ mục bằng 0, qua file tạm cùng thư mục rồi thay thế, byte-ổn-định.
"""

import json
import os
import re
import tempfile

from .errors import BadInput

KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")  # v1.1 thêm ca_keo, keo_neo
KINDS_P1 = KINDS  # tên cũ, giữ để mã cũ vẫn import được


def validate_items(items, kinds=KINDS_P1):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def read_inventory(path: str, kinds=KINDS_P1) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items: dict):
    items = {k: items[k] for k in sorted(items) if items[k] > 0}
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# --- kho cá thể (contract 1.2) -----------------------------------------------------------------
INDIVIDUAL_KEYS = {"id", "kind", "fresh"}
ID_RE = re.compile(r"^I[1-9][0-9]*$")
FRESH_DEFAULT = 100  # độ tươi cá thể mới vào kho (khớp tuning.freshness.initial)


def validate_individuals(items, fresh_max=FRESH_DEFAULT, kinds=KINDS):
    """Mảng cá thể {id, kind, fresh}: id dạng I<n> không trùng, kind hợp lệ, fresh số trong [0, fresh_max].

    Giữ nguyên thứ tự mảng (thứ tự vào kho; mất hàng theo LIFO dùng thứ tự này). Trả bản sao đã chuẩn hóa khóa.
    """
    if not isinstance(items, list):
        raise BadInput("kho v1.2: items phải là mảng cá thể (kho đếm của v1.1 bị từ chối)")
    out, seen = [], set()
    for it in items:
        if not isinstance(it, dict) or set(it) != INDIVIDUAL_KEYS:
            raise BadInput("cá thể phải có đúng id, kind, fresh")
        i, kind, fresh = it["id"], it["kind"], it["fresh"]
        if not isinstance(i, str) or not ID_RE.match(i) or i in seen:
            raise BadInput(f"id cá thể không hợp lệ hoặc trùng: {i!r}")
        seen.add(i)
        if kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind!r}")
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not 0 <= fresh <= fresh_max:
            raise BadInput(f"fresh của {i} phải là số trong [0, {fresh_max}]: {fresh!r}")
        out.append({"id": i, "kind": kind, "fresh": fresh})
    return out


def read_inventory_v12(path: str, fresh_max=FRESH_DEFAULT, kinds=KINDS) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_individuals(data["items"], fresh_max, kinds)


def write_inventory_v12(path: str, items: list):
    """Ghi MỘT lần, giữ thứ tự mảng, khóa theo thứ tự id, kind, fresh; byte-ổn-định."""
    items = [{"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]} for it in items]
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def inventory_schema(contract_version: str) -> str:
    """Schema file kho theo contract: "counts" (1.0, 1.1) hoặc "individuals" (1.2 trở đi)."""
    return "individuals" if contract_version >= "1.2" else "counts"


def read_inventory_for(path: str, contract_version: str, fresh_max=FRESH_DEFAULT):
    """Đọc file kho đúng schema của contract. Sai schema (đếm ở 1.2, cá thể ở 1.1) là BadInput (mã 2)."""
    if inventory_schema(contract_version) == "individuals":
        return read_inventory_v12(path, fresh_max)
    return read_inventory(path)


def counts_to_individuals(counts: dict, fresh=FRESH_DEFAULT, start_id=1, kinds=KINDS) -> list:
    """Adapter kho đếm -> kho cá thể: theo thứ tự `kinds`, id I<start_id>, I<start_id + 1>, ..., cùng độ tươi `fresh`."""
    out, n = [], start_id
    for kind in kinds:
        for _ in range(counts.get(kind, 0)):
            out.append({"id": f"I{n}", "kind": kind, "fresh": fresh})
            n += 1
    return out


def individuals_to_counts(items: list) -> dict:
    """Adapter kho cá thể -> kho đếm (bỏ id và độ tươi), sắp theo id nguyên liệu."""
    return hold_to_items([it["kind"] for it in items])


def hold_to_individuals(hold: list, fresh=FRESH_DEFAULT, start_id=1) -> list:
    """Giỏ cũ (mảng kind theo thứ tự nhặt) -> cá thể giữ nguyên thứ tự nhặt (LIFO không đổi)."""
    return [{"id": f"I{start_id + n}", "kind": kind, "fresh": fresh} for n, kind in enumerate(hold)]


def next_individual_id(items: list) -> int:
    """Số n nhỏ nhất lớn hơn mọi id I<n> đang có (id tăng xuyên pha; id đã dùng không được cấp lại trong một lượt)."""
    return max((int(it["id"][1:]) for it in items), default=0) + 1
