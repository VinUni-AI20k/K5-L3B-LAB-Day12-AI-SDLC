---
name: verify-contract
description: Kiểm tra toàn diện Test Contract, tính tất định headless, và danh sách thành viên trước khi commit/push.
---

# Skill: verify-contract

Dùng khi chuẩn bị commit hoặc tích hợp vào `main`:
1. Kiểm tra danh sách thành viên:
   ```bash
   python3 tools/check_team.py
   ```
2. Chạy toàn bộ test suites:
   ```bash
   PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
   ```
3. Chạy kiểm tra tất định headless 2 lần cùng seed 42 và so sánh byte-identical:
   ```bash
   python3 -m chonoi.headless --mode gather --seed 42 --ticks 300 --out /tmp/run1.jsonl
   python3 -m chonoi.headless --mode gather --seed 42 --ticks 300 --out /tmp/run2.jsonl
   cmp /tmp/run1.jsonl /tmp/run2.jsonl
   ```
