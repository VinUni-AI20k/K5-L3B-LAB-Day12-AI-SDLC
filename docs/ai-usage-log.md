# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Nhật Nguyên (`double-n-021`) | Antigravity Agent | Kiểm toán repo, tạo 2 AI skills (`headless-contract-check`, `phase-gate-audit`), cập nhật `AGENTS.md`, chốt `docs/contracts/README.md`, nâng cấp scene Godot 3D (`godot/main.gd`, `godot/main.tscn`) kết nối `chonoi.live` và viết bộ test `tests/test_p1_team_suite.py`. | ~18k tokens (~$0.06) | Ban đầu AI nhầm với đề cá nhân `K5-L3`; người dùng phát hiện và trỏ đúng sang repo nhóm `K5-L3B-LAB-Day12-AI-SDLC`. Đã cập nhật `AGENTS.md` để khóa quy ước repo nhóm. |
| Phase 1 | Hoàng Vũ (`hoangvu1806`) | AI Coding Assistant | Khởi tạo `TEAM.md` 6 thành viên, đồng bộ `team_size: 6` trong `game.contract.json`, triển khai Lát 3 (`chonoi/sim/quan.py`). | ~10k tokens (~$0.03) | Kiểm tra `check_team.py` xanh trước khi push. |
| Phase 1 | Nguyễn An (`AnK17-UIT`) | AI Coding Assistant | Khởi tạo cấu hình `godot/project.godot` và triển khai Lát 1 (`chonoi/sim/gather.py`). | ~10k tokens (~$0.03) | Đảm bảo không làm thay đổi `headless_cmd` trong `game.contract.json`. |
