"""Hook PreToolUse: hỏi lại người dùng trước khi agent sửa file khóa của nhóm.

AGENTS.md mục "Nên tránh": không sửa `docs/contracts/`, `game.contract.json` hay schema kho khi chưa báo
cả nhóm. Hook không cấm hẳn (Integrator vẫn có lúc phải sửa): nó trả `permissionDecision: "ask"` để
người dùng thấy cảnh báo và tự quyết định cho từng lần sửa.

Dùng với Claude Code (xem .claude/settings.json). Đọc JSON từ stdin, in JSON ra stdout, luôn thoát 0.
Chỉ dùng thư viện chuẩn.
"""

import json
import os
import sys

# Đường dẫn (tính từ gốc repo, dùng dấu /) được bảo vệ. Mục kết thúc bằng "/" là cả thư mục.
LOCKED = (
    "game.contract.json",
    "docs/contracts/",
    "chonoi/inventory.py",  # schema kho
)
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def locked_match(rel):
    for entry in LOCKED:
        if entry.endswith("/"):
            if rel.startswith(entry):
                return entry
        elif rel == entry:
            return entry
    return None


def relative_path(file_path, project_dir):
    """Đường dẫn tương đối so với gốc repo (dấu /); trả None nếu nằm ngoài repo."""
    path = os.path.normpath(file_path if os.path.isabs(file_path) else os.path.join(project_dir, file_path))
    rel = os.path.relpath(path, os.path.normpath(project_dir))
    if rel.startswith(".."):
        return None
    return rel.replace(os.sep, "/")


def decide(payload, project_dir):
    """Trả dict kết quả hook, hoặc None nếu cho qua."""
    if payload.get("tool_name") not in EDIT_TOOLS:
        return None
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(file_path, str) or not file_path:
        return None
    rel = relative_path(file_path, project_dir)
    entry = locked_match(rel) if rel else None
    if entry is None:
        return None
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": (
            f"{rel} là file khóa của nhóm ({entry}). Đổi hợp đồng ảnh hưởng mọi module: báo cả nhóm trong "
            "kênh chung và ghi lý do (docs/contracts/README.md mục 'Lịch sử đổi' hoặc ADR) trước khi sửa. "
            "Chỉ cho phép nếu Integrator đã đồng ý."),
    }}


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0  # không hiểu đầu vào thì không chặn
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    result = decide(payload, project_dir)
    if result is not None:
        json.dump(result, sys.stdout)  # ASCII an toàn trên Windows (cp1252)
    return 0


if __name__ == "__main__":
    sys.exit(main())
