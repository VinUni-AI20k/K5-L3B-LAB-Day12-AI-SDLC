# bachvx1709 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Chịu trách nhiệm module `client/ui` và vai trò QA Lead, Release cho Phase 1.
  - Viết bộ unit test `tests/test_phase1_gameplay.py` và chạy smoke test hộp đen theo Test Contract v1.0.
  - Lập ma trận kiểm chứng `docs/verification/phase-1.md` và thu thập toàn bộ log/bằng chứng thật trong `docs/proof/phase-1/`.
  - Tích hợp 3 tính năng sáng tạo đặc sắc cho nhóm: Hệ thống âm thanh Web Audio API, Hộp thoại Nam Bộ tương tác, và Hiệu ứng đồ họa sông nước/khói bếp trên Canvas (commit `1d4943e`).
- **Tôi đã review (kèm link):**
  - Review chéo logic mô phỏng `chonoi/sim/gather.py` và `chonoi/sim/quan.py`, bảo đảm tuân thủ nghiêm ngặt Test Contract v1.0 và tính xác định (determinism).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI viết test giữ phím `interact=True` liên tục làm mất cạnh lên (rising edge), khiến lệnh phục vụ bàn không nhận. Tôi phát hiện qua assertion failure của unittest và sửa nhả phím `interact=False`.
- **Điều tôi học được:**
  - Hiểu sâu về kiến trúc tick-based deterministic simulation và quy trình cộng tác phân tách rõ ràng giữa mô phỏng headless và tầng giao diện người dùng.
