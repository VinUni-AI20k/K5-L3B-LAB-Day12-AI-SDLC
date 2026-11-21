# double-n-021 (Bùi Đặng Nhật Nguyên) — phản tư cá nhân (≤ 200 từ)

- **Vai trò trong nhóm:** QA Lead / PO kiêm hỗ trợ kỹ thuật 3D & Test Contract cho cả 4 lát.
- **Tôi đã làm:**
  - Thiết lập bộ AI Harness cho nhóm: `.agents/skills/headless-contract-check/SKILL.md`, `.agents/skills/phase-gate-audit/SKILL.md` và quy tắc chia helper chống đụng độ code trong `AGENTS.md`.
  - Soạn hợp đồng tích hợp `docs/contracts/README.md`, kế hoạch `docs/plan/phase-1.md`, bảng `docs/clarify.md` và ma trận kiểm chứng `docs/verification/phase-1.md`.
  - Xây dựng thế giới 3D Godot (`godot/main.tscn`, `godot/main.gd` dùng `Node3D`, `Camera3D`, `DirectionalLight3D`) đồng bộ trực tiếp với `chonoi.live` qua HTTP JSON bridge mà vẫn giữ nguyên 100% tính tất định của `chonoi.headless`.
  - Viết bộ kiểm thử tự động `tests/test_p1_team_suite.py` và thu thập bằng chứng chạy thật vào `docs/proof/phase-1/`.
- **AI sai ở đâu và tôi phát hiện thế nào:** Ban đầu AI đọc đề của lớp L3 chung (game cá nhân); tôi đã đối chiếu URL repo lớp L3B và yêu cầu AI kiểm toán lại toàn bộ codebase `chonoi/` cùng `tools/check_team.py`.
- **Điều tôi học được:** Tách biệt hoàn toàn lớp Simulation tất định (Python headless) với lớp Hiển thị 3D (Godot 3D client đọc snapshot) giúp nhóm 6 người vừa có đồ họa 3D vừa đạt tuyệt đối bài chấm hộp đen.
