"""Bằng chứng dẫn trong ma trận phải tồn tại.

    python3 tools/check_evidence.py

Quy tắc: một dòng trong `docs/verification/*.md` hoặc `docs/plan/*.md` mà
  - dẫn đường dẫn `docs/proof/...`, và
  - ghi kết quả **đạt** (không phải "chưa đạt")
thì đường dẫn đó phải có thật trong repo. Ngược lại là lỗi (mã thoát 1).

Dòng ghi "chưa đạt" được phép dẫn file chưa có — đó là kế hoạch, không phải claim.
Đường dẫn còn placeholder (`<...>`, `...`) thì bỏ qua.

Mã thoát: 0 OK · 1 có claim thiếu bằng chứng · 2 không đọc được thư mục.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_DIRS = ("docs/verification", "docs/plan", "docs/tickets")
PATH_RE = re.compile(r"docs/proof/[A-Za-z0-9._/-]+")
MISSING_OK = ("chưa đạt", "chưa có", "chưa làm", "chưa chạy")


def is_claim(line: str) -> bool:
    low = line.lower()
    if "docs/proof/" not in line:
        return False
    if any(m in low for m in MISSING_OK):
        return False
    return "đạt" in low


def main() -> int:
    errors, checked, warnings = [], 0, []
    for rel_dir in SCAN_DIRS:
        d = os.path.join(ROOT, rel_dir)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".md"):
                continue
            path = os.path.join(d, name)
            with open(path, encoding="utf-8") as f:
                for lineno, line in enumerate(f, 1):
                    for ref in PATH_RE.findall(line):
                        ref = ref.rstrip(".,);:")
                        if "<" in ref or "..." in ref:
                            continue
                        exists = os.path.exists(os.path.join(ROOT, ref))
                        checked += 1
                        if exists:
                            continue
                        where = f"{rel_dir}/{name}:{lineno}"
                        if is_claim(line):
                            errors.append(f"{where}: claim đạt nhưng thiếu {ref}")
                        else:
                            warnings.append(f"{where}: dẫn {ref} (chưa có, không phải claim đạt)")

    for w in warnings:
        print(f"cảnh báo  {w}")
    if errors:
        print("\nBẰNG CHỨNG KHÔNG ĐẠT:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"OK: {checked} đường dẫn bằng chứng được dẫn, không có claim nào thiếu file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
