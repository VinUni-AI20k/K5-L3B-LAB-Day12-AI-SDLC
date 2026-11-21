# Nguyễn Tùng Dương (nguyenduong43) — Phản tư cá nhân (MSSV: 2A202603850)

- **Tôi đã làm:**
  - Thiết kế và cài đặt 2 skills tự động hóa cho AI agent trong `.agents/skills/` (`verify-contract` và `qa-blackbox-check`), cập nhật tài liệu hướng dẫn trong `AGENTS.md`.
  - Cập nhật và sửa lỗi phụ thuộc trong `tests/test_team_check.py` (tách test template thành chuỗi mẫu độc lập và bổ sung test kiểm tra `TEAM.md` thực tế với `team_size: 5`).
  - Xây dựng bộ kiểm thử hộp đen hồi quy `tests/test_qa_regression_p1.py` bám sát các tiêu chí nghiệm thu (AC-P1-01 đến AC-P1-08), kiểm tra tính tất định từng byte và mã thoát `2`.
  - Hoàn thiện ma trận truy vết kiểm chứng `docs/verification/phase-1.md`, thu thập log bằng chứng vào `docs/proof/phase-1/` và ghi nhật ký AI tại `docs/ai-usage-log.md`.
- **Tôi đã review:**
  - Review PR #2 (nlamtung - Lát 1&2 `gather`), PR #3 (Tiberu2611 - Lát 3 `quan`) và PR #4 (khanhduyvu1 - Lát 4 `quan`).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI đề xuất test phụ thuộc vào file `TEAM.md` thật khiến test case kiểm tra template bị sai logic khi repo đã điền thông tin nhóm; phát hiện qua đối chiếu kế hoạch `docs/plan/phase-1.md`.
- **Điều tôi học được:**
  - Hiểu sâu về Test Contract, kiểm thử hộp đen phần mềm tất định và cách vận hành quy trình AI SDLC song song với nhiều agent.
