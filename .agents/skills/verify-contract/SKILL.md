---
name: verify-contract
description: Kiểm tra tính tuân thủ của game contract (game.contract.json), tính hợp lệ của schema kho và tính tất định từng byte qua headless simulation.
---

# Skill: verify-contract

Skill này giúp thành viên nhóm hoặc AI agent kiểm tra nhanh tính tương thích của trò chơi với **Test Contract v1.0** được quy định trong `PRD-0.md`.

## Các bước kiểm tra tự động

1. **Kiểm tra cấu hình contract:**
   - Đọc `game.contract.json` và xác thực trường `team_size` khớp với số lượng thành viên trong `TEAM.md`.
   - Kiểm tra các trường tuning cốt lõi: thời lượng ca, dung tích giỏ, thời gian nấu, menu, công thức nguyên liệu.

2. **Kiểm tra tính tất định từng byte (Byte-level determinism):**
   - Chạy 2 phiên headless độc lập với cùng seed và các tham số giống nhau.
   - So sánh hash SHA-256 hoặc so sánh từng byte file output `.jsonl` và file kho `.json`. Hai lần chạy bắt buộc phải giống hệt nhau 100%.

3. **Kiểm tra schema kho:**
   - Xác thực cấu trúc file kho theo đúng `docs/contracts/` (`items: { kind: count }`).

## Lệnh thực thi nhanh

```bash
# Chạy script kiểm tra contract và determinism
python3 .agents/skills/verify-contract/verify.py
```
