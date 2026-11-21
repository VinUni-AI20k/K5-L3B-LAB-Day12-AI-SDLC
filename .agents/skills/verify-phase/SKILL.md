---
name: verify-phase
description: Kiểm chứng một phase trước khi merge lớn hoặc gắn tag phase-n — chạy toàn bộ test, kiểm tất định (cùng seed → giống từng byte), kiểm kho gather → quan, kiểm TEAM.md, rồi lưu bằng chứng vào docs/proof/phase-n/ và cập nhật docs/verification/phase-n.md. Dùng khi ai đó nói "kiểm chứng", "chuẩn bị tag", "gom bằng chứng", "verify phase".
---

# verify-phase — kiểm chứng và gom bằng chứng

## Khi nào dùng
- Trước khi Integrator gắn tag `phase-n` (bắt buộc).
- Sau khi merge một lát lớn vào `main`.

## Các bước
1. Đảm bảo working tree sạch hoặc đã commit (bằng chứng phải gắn với một commit có thật).
2. Chạy:
   ```
   python .agents/skills/verify-phase/verify.py --phase <n>
   ```
   Script ghi `docs/proof/phase-<n>/{tests,determinism,inventory,team}.txt` và `summary.md`; mã thoát 1 nếu có bước chưa đạt.
   - Trên Windows, lệnh `python3` trong `headless_cmd` phải tìm được (thêm `%LOCALAPPDATA%\Microsoft\WindowsApps` vào PATH nếu cần). **Không** sửa `headless_cmd`: CI và bộ chấm chạy `python3`.
3. Đọc `summary.md`. Bước nào chưa đạt: **không sửa test cho xanh**; sửa luật, hoặc ghi trung thực là chưa đạt.
4. Cập nhật `docs/verification/phase-<n>.md`: mỗi AC trong PRD của phase một dòng — cách kiểm chứng (tên test), link bằng chứng (`docs/proof/phase-<n>/...`), kết quả đạt / chưa đạt. Thêm mục "Đánh giá ngắn".
5. Commit bằng chứng (`docs/proof/phase-<n>/`, `docs/verification/phase-<n>.md`), ghi kết quả test vào mô tả commit.
6. Ghi một dòng vào `docs/ai-usage-log.md` nếu dùng agent để chạy skill này.

## Không làm
- Không bịa kết quả, không chép output cũ của commit khác.
- Không gắn tag khi `tests.txt` hoặc `determinism.txt` chưa đạt mà không ghi rõ lý do trong verification.
