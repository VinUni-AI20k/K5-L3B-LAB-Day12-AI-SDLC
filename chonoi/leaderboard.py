"""Bảng xếp hạng cục bộ (TICKET-04 mục 3, mở rộng "leaderboard").

File lưu (store) và file xuất cùng một dạng: {"entries":[{"name","score","days_completed","seed"}]}.
- Giữ top 10, sắp `score` giảm dần; hòa điểm thì mục ghi trước đứng trước (sắp ổn định, mục mới nối cuối).
- Chỉ ghi khi một lượt `--mode day` chuẩn đủ 5 Ngày: không scenario, kết thúc `days_complete`.
- Ghi nguyên tử: file tạm cùng thư mục rồi `os.replace`, nên lỗi giữa chừng không làm hỏng store cũ.

Store không tồn tại = bảng rỗng. Store sai dạng → BadInput (mã 2), kiểm TRƯỚC khi chạy sim.
"""

import json
import os
import tempfile

from .errors import BadInput

TOP_N = 10
STANDARD_DAYS = 5
NAME_MAX = 32
# mặc định cho `--export-leaderboard` khi không có `--leaderboard`: ở gốc repo, đã gitignore
DEFAULT_STORE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "leaderboard.json")
_KEYS = {"name", "score", "days_completed", "seed"}


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def validate_name(name):
    if not isinstance(name, str) or not name.strip():
        raise BadInput("--player-name không được rỗng")
    if len(name) > NAME_MAX:
        raise BadInput(f"--player-name tối đa {NAME_MAX} ký tự")
    if any(ord(c) < 32 for c in name):
        raise BadInput("--player-name không được chứa ký tự điều khiển")
    return name


def _check_entry(e, i):
    if not isinstance(e, dict) or set(e) != _KEYS:
        raise BadInput(f"leaderboard: mục #{i} phải có đúng các khóa {sorted(_KEYS)}")
    if not isinstance(e["name"], str) or not e["name"]:
        raise BadInput(f"leaderboard: mục #{i} có name không hợp lệ")
    for k in ("score", "days_completed", "seed"):
        if not _is_int(e[k]):
            raise BadInput(f"leaderboard: mục #{i} có {k} không phải số nguyên")
    if e["days_completed"] < 0:
        raise BadInput(f"leaderboard: mục #{i} có days_completed âm")


def load(path):
    """Đọc store; thiếu file → []. Trả danh sách mục đã sắp và cắt top 10."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được leaderboard {path}: {e}")
    if not isinstance(data, dict) or set(data) != {"entries"} or not isinstance(data["entries"], list):
        raise BadInput('leaderboard phải có dạng {"entries":[...]}')
    for i, e in enumerate(data["entries"]):
        _check_entry(e, i)
    return rank(data["entries"])


def rank(entries):
    """Sắp điểm giảm dần, giữ thứ tự ghi khi hòa (sorted ổn định), cắt TOP_N."""
    return sorted(entries, key=lambda e: -e["score"])[:TOP_N]


def add(entries, name, score, days_completed, seed):
    """Nối mục mới SAU các mục cũ rồi xếp lại: hòa điểm thì mục cũ đứng trước."""
    entry = {"name": name, "score": int(score), "days_completed": int(days_completed), "seed": int(seed)}
    return rank(list(entries) + [entry])


def save(path, entries):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".lb-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"entries": rank(entries)}, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def qualifies(days, scenario_path, end_row):
    """Lượt chuẩn: 5 Ngày, không scenario, dòng end `days_complete` và đủ 5 Ngày đã đóng Shop."""
    return (days == STANDARD_DAYS and scenario_path is None and end_row.get("reason") == "days_complete"
            and end_row.get("days_completed") == STANDARD_DAYS)


def export(store_path, out_path):
    """Xuất top 10 từ store (thiếu store → bảng rỗng) ra `out_path`."""
    save(out_path, load(store_path))
