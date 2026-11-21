"""Ghi JSONL tất định: làm tròn 3 chữ số khi XUẤT (tính toán dùng giá trị chính xác)."""

import json


FRESH_DIGITS = 6  # v1.2: độ tươi xuất 6 chữ số (clarify P3-01), số thực khác giữ 3 chữ số


def _clean(v, digits=3):
    if isinstance(v, float):
        r = round(v, digits)
        return 0.0 if r == 0 else r  # tránh -0.0
    if isinstance(v, dict):
        return {k: _clean(x, FRESH_DIGITS if k == "fresh" else 3) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x, key) for x in v]
    return v


def dumps(obj) -> str:
    return json.dumps(_clean(obj), ensure_ascii=False, separators=(",", ":"))


class JsonlWriter:
    def __init__(self, path: str):
        self._f = open(path, "w", encoding="utf-8", newline="\n")

    def write(self, obj):
        self._f.write(dumps(obj) + "\n")

    def close(self):
        self._f.close()
