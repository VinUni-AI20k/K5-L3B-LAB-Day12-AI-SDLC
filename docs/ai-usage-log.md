# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | hungdt31 | Claude Code (Opus 5.5) | Kiểm chứng Phase 1: sinh inputs e2e gather→kho→quan, chạy lại test/smoke tại `9b691bd`, lập ma trận AC, viết skill `qa-verify-phase` | ~1 phiên | Chạy test trên `main` thì đỏ 16 test do bump v1.1, nên chuyển sang kiểm tại commit Phase 1 qua worktree. AI nghi `score` 564 là sai; đọc `runner.py:34` thì thấy dùng `floor(reputation)` nên đúng |
| 2 | hungdt31 | Claude Code (Opus 5.5) | Smoke tích hợp + `day` 5 Ngày bằng bot `tools/qa_autoplay.py`, kiểm Cá Sấu bằng `tools/qa_check_day.py`, sửa payload `monster_hit`, viết `verification/phase-2.md` | ~1 phiên | Script kiểm của AI báo nhầm 2 lần: (1) đọc `snapshot()` không deepcopy nên `hold` trước và sau trông như nhau; (2) đòi `invuln_ticks == 0` trước bước, trong khi ticket mục 4.5 giảm bất tử ở đầu bước. Phát hiện khi đối chiếu với code và ticket. Payload `monster_hit` lệch ticket thì phát hiện bằng cách so với bảng 4.4 |
