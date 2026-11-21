# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | NhomF7 / Copilot | Copilot SDK trong VS Code | Hoàn thiện Gather, Quán, test logic và verification | Không đo được | Đã đối chiếu contract trước sửa; test baseline và suite sau sửa đều xanh. |
| 1 | nganhduong123 / Claude Code | Claude Opus 5.5 (desktop app) | Viết 2 skill `.agents/skills/` (python-fact-grounded-coding, phase-1-verification) + script kiểm chứng, soát quy ước; ghi `docs/proof/phase-1/verify-run.txt` | Không đo được | Chạy thử thấy 21/44 test fail do `python3` trên Windows là lối tắt Store (mã 9009), không phải luật sai; thêm shim python3 trong script thay vì sửa contract. Sau đó 44/44 xanh, 9/9 bước đạt. |
