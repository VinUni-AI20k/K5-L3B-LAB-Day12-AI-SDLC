# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | hungdt31 | Claude Code (Opus 5.5) | Kiểm chứng Phase 1: sinh inputs e2e gather→kho→quan, chạy lại test/smoke tại `9b691bd`, lập ma trận AC, viết skill `qa-verify-phase` | ~1 phiên | Chạy test trên `main` thì đỏ 16 test do bump v1.1, nên chuyển sang kiểm tại commit Phase 1 qua worktree. AI nghi `score` 564 là sai; đọc `runner.py:34` thì thấy dùng `floor(reputation)` nên đúng |
