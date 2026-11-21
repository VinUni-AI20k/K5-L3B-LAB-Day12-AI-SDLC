"""Soát nhanh quy ước AGENTS.md trong code luật (mặc định chonoi/sim/*.py).

    python .agents/skills/python-fact-grounded-coding/scripts/check_rules.py
    python .agents/skills/python-fact-grounded-coding/scripts/check_rules.py chonoi/sim/quan.py

LỖI (mã thoát 1): ngẫu nhiên/đồng hồ không qua Streams -> phá tất định của headless.
CẦN XEM (không làm fail): số literal khác 0, 1, -1, 2 — có thể là số liệu đáng lẽ đọc từ
game.contract.json. Đây là gợi ý để người/agent tự kiểm, không phải phán quyết.
"""

import ast
import glob
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
FORBIDDEN_MODULES = {"random", "time", "datetime", "secrets", "uuid"}
FORBIDDEN_CALLS = {("os", "urandom")}
ALLOWED_NUMBERS = {0, 1, -1, 2, 0.0, 1.0, 0.5, 100}


def scan(path):
    errors, review = [], []
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.split(".")[0] in FORBIDDEN_MODULES:
                    errors.append((node.lineno, f"import {n.name} — dùng Streams (chonoi/rng.py), không dùng ngẫu nhiên/đồng hồ toàn cục"))
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in FORBIDDEN_MODULES:
            errors.append((node.lineno, f"from {node.module} import … — dùng Streams, không dùng ngẫu nhiên/đồng hồ"))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if (node.func.value.id, node.func.attr) in FORBIDDEN_CALLS:
                errors.append((node.lineno, f"{node.func.value.id}.{node.func.attr}() — không tất định"))
        elif isinstance(node, ast.Constant) and type(node.value) in (int, float) and not isinstance(node.value, bool):
            if node.value not in ALLOWED_NUMBERS:
                review.append((node.lineno, f"số {node.value!r} — số liệu này có trong game.contract.json không?"))
    return sorted(errors), sorted(review)


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    paths = argv or sorted(glob.glob(os.path.join(ROOT, "chonoi", "sim", "*.py")))
    n_err = 0
    for p in paths:
        errors, review = scan(p)
        rel = os.path.relpath(os.path.abspath(p), ROOT).replace(os.sep, "/")
        for line, msg in errors:
            print(f"LỖI     {rel}:{line}: {msg}")
        for line, msg in review:
            print(f"CẦN XEM {rel}:{line}: {msg}")
        n_err += len(errors)
    print(f"{len(paths)} file, {n_err} lỗi quy ước.")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
