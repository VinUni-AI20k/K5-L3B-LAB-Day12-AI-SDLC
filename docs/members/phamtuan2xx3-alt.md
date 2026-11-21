# phamtuan2xx3-alt (Phạm Quang Tuấn - 2A202603824) — phản tư cá nhân (≤ 200 từ)

- **Module phụ trách:** DEV 2 — Gameplay Sinh Thái & Săn Bắt Cá (`chonoi/sim/gather.py`)
- **Tôi đã làm (kèm link commit):**
  - Implement hái Bông Điên Điển, Bông Súng mặt nước & chu kỳ mọc lại 1200 ticks: commit `965d7ad`
  - Implement quăng lưới bắt Cá Linh, Cá Lóc có hồi chiêu 30 ticks, sản lượng & giỏ LIFO: commit `36b3d7a`
  - Viết bộ 12 ca kiểm thử độc lập bao phủ 100% ca biên tại `tests/test_dev2_harvest_catch.py`: commit `3a43731`
- **Tôi đã review (kèm link):**
  - Đợt phản biện chuyên sâu từ Swarm đa chiều (3 Critic Agents: Sim 60Hz, Test Contract, Game Feel).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI ban đầu dùng so sánh chuỗi `id` thông thường (`"F10" < "F2"`), làm vi phạm Contract E. Tôi dùng swarm phản biện và sửa lại chuẩn `id_key`.
  - AI ban đầu định bắn cả `hold_full` khi bắt cá lúc giỏ còn 1 chỗ. Tôi đã phát hiện và chuẩn hóa chỉ bắn duy nhất `fish_caught`.
- **Điều tôi học được:**
  - Kỹ thuật bảo đảm tính tất định byte-for-byte (khử nhiễu số thực float jitter bằng `round(dist, 6)`), thiết kế decoupled game loop và quy trình AI SDLC kỷ luật.
