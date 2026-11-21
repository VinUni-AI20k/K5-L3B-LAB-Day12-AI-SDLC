---
name: run-smoke
description: Tự động chạy toàn bộ bộ kiểm thử đơn vị và kịch bản headless smoke test của dự án Chợ Nổi để đảm bảo không gãy contract trước khi commit.
---

# Skill: run-smoke

## Khi nào dùng
Dùng trước mỗi lần commit và push để đảm bảo:
1. Nhánh chính luôn chạy được (`tests/` xanh 100%).
2. Chế độ headless hoạt động đúng chuẩn Test Contract (mã thoát 0, xuất JSONL tất định, ghi kho atomic).

## Lệnh chạy
```bash
# 1. Chạy toàn bộ test suites (smoke test + unit test)
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v

# 2. Chạy thử nghiệm headless mode gather
python3 -m chonoi.headless --mode gather --seed 1 --ticks 120 --out /tmp/smoke_gather.jsonl

# 3. Chạy thử nghiệm headless mode quan
python3 -m chonoi.headless --mode quan --seed 1 --ticks 120 --out /tmp/smoke_quan.jsonl

# 4. Kiểm tra danh sách thành viên hợp lệ
python3 tools/check_team.py
```
