---
name: chonoi-qa
description: Chuyên gia kiểm thử tự động, xác thực tính tất định và Test Contract cho Chợ Nổi
---

# Chợ Nổi QA Skill

Dùng khi chạy kiểm thử, xác thực tính tất định byte-for-byte và đóng gói bằng chứng cho các phase.

## Lệnh kiểm tra:
- Smoke tests: `py -3 -m unittest discover -s tests -v` (Windows) hoặc `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` (Linux)
- Kiểm tra danh sách thành viên: `py -3 tools/check_team.py`
- Kiểm tra tính tất định: Chạy headless 2 lần cùng seed so sánh byte đầu ra.
