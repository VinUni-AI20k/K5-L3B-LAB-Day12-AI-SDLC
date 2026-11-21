# Kế hoạch Phase 1 (Quán Ăn Chợ Nổi)

## Mục tiêu
Hoàn thành toàn bộ vòng lặp gameplay cốt lõi cho 2 chế độ:
1. Buổi sáng (`gather`): Út Sen lặn bắt cá, hái rau, quản lý oxy và cập bến ghe thuyền xuất kho nguyên liệu.
2. Buổi tối (`quan`): Đón thực khách ghé ghe, kiểm tra kho, nấu nướng tại bếp và phục vụ bàn, thu tiền, tính uy tín.
3. Giao diện Web: Hiển thị đồ họa sông nước miền Tây sống động trên trình duyệt.

## Phân chia 5 đầu việc làm game song song
Chi tiết xem tại [Bảng phân công nhiệm vụ](tasks-summary.md):
- **DEV 1:** [Lặn & Sinh tồn Út Sen (Oxy, Máu, Ngạt, Ngất)](task-1-gather-survival.md)
- **DEV 2:** [Hái Bông & Săn Bắt Cá (Node regrow, Fish catch)](task-2-gather-harvest.md)
- **DEV 3:** [Khách Hàng Quán Ăn & Menu (Đặt bàn, Giữ chỗ kho, Kiên nhẫn)](task-3-quan-customers.md)
- **DEV 4:** [Bếp Nấu, Bưng Bê & Kinh Tế Quán (Nấu, Phục vụ, Tiền & Uy tín)](task-4-quan-kitchen.md)
- **DEV 5:** [Đồ Họa Web, Hiệu Ứng Sông Nước & Âm Thanh](task-5-game-visuals.md)

## Rủi ro & Giải pháp
- **Rủi ro:** Xung đột git khi merge chung file sim.
  - **Giải pháp:** Mỗi dev làm trên nhánh riêng (`feat/*`), hàm và logic tách biệt rõ ràng theo từng đầu việc, chạy test xanh trước khi gộp vào `main`.
