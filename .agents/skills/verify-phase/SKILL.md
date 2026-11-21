---
name: verify-phase
description: Tự động chạy toàn bộ kiểm thử đơn vị, kiểm tra tính tất định byte-by-byte (SHA-256) và xuất log bằng chứng vào docs/proof/phase-<N>/.
---

# Skill: verify-phase (Kiểm chứng Phase tự động)

## Khi nào dùng
- Sử dụng trước khi gắn Git tag cho mỗi phase (`phase-1`, `phase-2`, `phase-3`, `phase-4`).
- Sử dụng để thu thập bằng chứng kiểm thử tự động ghi vào `docs/verification/phase-<N>.md`.

## Lệnh thực thi
```bash
python .agents/skills/verify-phase/run_verification.py --phase 1
```

## Kết quả đầu ra
1. Chạy toàn bộ test suites trong `tests/`.
2. Kiểm tra tính tất định byte-by-byte (chạy 2 lần cùng seed và so sánh mã băm SHA-256).
3. Tự động ghi log vào `docs/proof/phase-<N>/smoke_test.txt`.
