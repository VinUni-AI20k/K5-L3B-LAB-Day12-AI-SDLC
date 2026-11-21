---
name: mekong-ui
description: Chuyên gia đồ họa Web Canvas & hiệu ứng sông nước miền Tây cho Chợ Nổi
---

# Mekong UI Skill

Dùng khi nâng cấp giao diện `chonoi/web/index.html`.

## Nguyên tắc:
1. Client là thuần View thụ động: nhận snapshot từ `/state` và gửi phím qua `/input`.
2. Không can thiệp vào logic tính toán va chạm hay sinh số ngẫu nhiên của sim.
3. Hỗ trợ 2 chế độ:
   - `gather`: Mặt cắt ngang sông, hiệu ứng nước sâu, sóng cuộn, bọt khí lặn, ghe bến đỗ.
   - `quan`: Mặt sàn gỗ quán nổi ban đêm, đèn lồng vàng ấm áp, khói bếp than, bubble order khách.
4. Đảm bảo tốc độ hiển thị 60 FPS mượt mà và camera làm mượt (LERP damping).
