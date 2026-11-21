---
name: phase-gate-audit
description: Checklist trước khi gắn tag phase-N. Dùng ở cuối mỗi phase để kiểm team, test, bằng chứng, nhật ký AI và số commit mỗi người.
---

# phase-gate-audit

Mục tiêu: không gắn tag khi thiếu bằng chứng hoặc thiếu dấu vết của thành viên.

## Khi nào dùng
- 5-10 phút cuối của mỗi phase, trước khi Integrator chạy `git tag phase-N`.

## Các bước
1. Đồng bộ và sạch: `git pull --ff-only` và `git status` (không còn file dở).
2. Kiểm danh sách thành viên: `python3 tools/check_team.py` phải in `OK`.
3. Test xanh: chạy skill `headless-contract-check`.
4. Số commit mỗi người (mục tiêu >= 3 commit có nội dung, cả nhóm):
   `git shortlog -sne HEAD`
   Người nào thiếu: báo trên nhóm chat, giao một việc nhỏ trước khi tag.
5. Hồ sơ phase có đủ và không còn bản mẫu rỗng:
   - `docs/verification/phase-N.md` (ma trận AC, cách kiểm chứng, link bằng chứng, đạt/chưa đạt)
   - `docs/proof/phase-N/` (output thật)
   - `docs/clarify.md` (câu hỏi, giả định, ai quyết)
   - `docs/ai-usage-log.md` (mỗi người một dòng: công cụ, việc, token ước tính, AI sai ở đâu)
6. Không có `.env`, API key, token: `git ls-files | findstr /i ".env key token"`.
7. Báo Integrator: chỉ khi 1-6 đạt mới `git tag phase-N` và `git push origin phase-N`.

## Quy tắc
- Chưa đạt thì ghi "chưa đạt" kèm lý do, không giấu.
- Không force push sau khi đã gắn tag.
- Hết giờ phase thì tag và đi tiếp.
