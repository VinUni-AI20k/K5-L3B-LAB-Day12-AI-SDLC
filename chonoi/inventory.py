"""Kho cá thể v1.2; chỉ adapter nội bộ còn nhận dữ liệu đếm Phase 1/2."""

import json
import math
import os
import re
import tempfile
from copy import deepcopy

from .errors import BadInput

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_P2 = (*KINDS_P1, "ca_keo", "keo_neo")
_ITEM_ID = re.compile(r"I[1-9][0-9]*\Z")


def validate_inventory_items(items, valid_kinds=KINDS_P2):
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể")
    seen = set()
    result = []
    for item in items:
        if not isinstance(item, dict) or set(item) != {"id", "kind", "fresh"}:
            raise BadInput("mỗi nguyên liệu cần đúng id, kind, fresh")
        ident, kind, fresh = item["id"], item["kind"], item["fresh"]
        if not isinstance(ident, str) or not _ITEM_ID.fullmatch(ident) or ident in seen:
            raise BadInput(f"id nguyên liệu sai hoặc trùng: {ident!r}")
        if not isinstance(kind, str) or kind not in valid_kinds:
            raise BadInput(f"nguyên liệu lạ: {kind!r}")
        if (isinstance(fresh, bool) or not isinstance(fresh, (int, float))
                or not math.isfinite(fresh) or not 0 <= fresh <= 100):
            raise BadInput(f"độ tươi không hợp lệ cho {ident}: {fresh!r}")
        seen.add(ident)
        result.append({"id": ident, "kind": kind, "fresh": float(fresh)})
    return result


def clone_items(items):
    return deepcopy(validate_inventory_items(items))


def items_to_counts(items):
    counts = {}
    for item in validate_inventory_items(items):
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    return counts


def materialize_items(raw, ids, *, allow_legacy=False):
    """Dựng kho cá thể; dữ liệu cũ chỉ được chuyển đổi ở ranh giới sim nội bộ."""
    if isinstance(raw, list) and all(isinstance(item, dict) for item in raw):
        items = validate_inventory_items(raw)
        ids.observe_item_ids(items)
        return items
    if not allow_legacy:
        raise BadInput("kho phải là mảng cá thể v1.2")
    if isinstance(raw, dict):
        counts = validate_items(raw)
        kinds = [kind for kind in sorted(counts) for _ in range(counts[kind])]
    elif isinstance(raw, list) and all(isinstance(kind, str) and kind in KINDS_P2 for kind in raw):
        kinds = raw
    else:
        raise BadInput("kho/giỏ nội bộ không hợp lệ")
    return [{"id": ids.next_item_id(), "kind": kind, "fresh": 100.0} for kind in kinds]


def validate_items(items, kinds=KINDS_P2):
    """Adapter đếm nội bộ cho luật bếp Phase 1/2; không dùng cho file kho."""
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for kind, count in items.items():
        if kind not in kinds or type(count) is not int or count < 0:
            raise BadInput(f"số lượng không hợp lệ cho {kind}: {count!r}")
        if count:
            out[kind] = count
    return out


def read_inventory(path: str, kinds=KINDS_P2):
    try:
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, ValueError) as error:
        raise BadInput(f"không đọc được file kho {path}: {error}")
    if not isinstance(data, dict) or set(data) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_inventory_items(data["items"], kinds)


def hold_to_items(hold):
    """Adapter đếm cũ cho code/test Phase 1/2, không phải schema file v1.2."""
    counts = {}
    for kind in hold:
        counts[kind] = counts.get(kind, 0) + 1
    return {kind: counts[kind] for kind in sorted(counts)}


def save_inventory_atomic(path, items):
    items = validate_inventory_items(items)
    directory = os.path.dirname(os.path.abspath(path))
    fd, temp_path = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump({"items": items}, stream, ensure_ascii=False, separators=(",", ":"))
            stream.write("\n")
        os.replace(temp_path, path)
    except BaseException:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


write_inventory = save_inventory_atomic
