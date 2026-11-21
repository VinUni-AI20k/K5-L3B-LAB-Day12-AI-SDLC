---
name: qa-blackbox-check
description: Chạy bộ kiểm thử hộp đen, kiểm tra tính toàn vẹn của scenario/inputs, mã thoát (0, 2), và xuất bằng chứng nghiệm thu cho phase.
---

# Skill: qa-blackbox-check

Skill này hỗ trợ QA Lead và các agent tự động chạy kiểm thử hồi quy (regression) và kiểm thử hộp đen các hành vi biên trong `PRD-0.md`.

## Chức năng chính

1. **Kiểm tra mã thoát đúng chuẩn (Exit codes):**
   - Mã `0`: Khi chạy headless thành công, hoàn thành kịch bản hoặc chạm mốc ticks.
   - Mã `2`: Khi phát hiện lỗi cú pháp, dữ liệu kịch bản (`scenario`) sai hoặc mâu thuẫn (mode sai, id trùng lặp, timer âm, tham số nằm ngoài miền hợp lệ).
2. **Kiểm tra các hành vi biên:**
   - Oxy giảm về 0 và gây ngạt (`choke`) chính xác ở tick $t+59$.
   - Giỏ đầy (`hold_capacity`) không thể nhặt thêm.
   - Hết giờ hoặc cập bến ghi nhận chính xác kho.
3. **Thu thập bằng chứng tự động (Proof collection):**
   - Tự động chạy test suite và lưu log vào `docs/proof/phase-n/test-suite.txt`.

## Lệnh thực thi nhanh

```bash
# Chạy script kiểm tra QA và xuất log proof
python3 .agents/skills/qa-blackbox-check/run_qa.py
```
