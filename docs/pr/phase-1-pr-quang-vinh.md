# Mô Tả PR Phase 1 — Nhánh `feat/quang-vinh`

> **Người mở PR:** Tào Quang Vinh (`@qvinhh2312`)  
> **Người review:** Trần Đình Nhật Minh (`@trandinhnhatminh1452`)  
> **Nhãn (Labels):** `phase-1`, `ready-for-review`, `ui`  
> **Tiêu đề PR:** `ui: hoàn thiện HUD 2 buổi sáng tối, prompt ngữ cảnh, âm thanh Web Audio và màn Game Over (Ticket 06)`

---

## 1. Tóm tắt thay đổi (Summary)
Hoàn thành trọn vẹn **Ticket 06: HUD hai buổi** theo đúng đặc tả PRD-0 Phase 1:
- **HUD Buổi Sáng:** Hiển thị đồng hồ đếm ngược ⏱ (chuyển đỏ khi < 30s), thanh Oxy 3 dải màu trực quan (đỏ rực cảnh báo khi < 25%), hiển thị Máu (HP) `♥♥♥`, giỏ hàng dạng slot trực quan kèm tóm tắt loài cá/rau và số lượng.
- **HUD Buổi Tối:** Bảng Kho dự trữ `stock`, thẻ Bàn ăn & Khách kèm thanh kiên nhẫn đổi màu động (xanh $\rightarrow$ vàng $\rightarrow$ đỏ), trạng thái bếp đếm ngược giây và sẵn sàng bưng món (`ready`), hiển thị món trên tay, tiền `💰`, sao uy tín `⭐` và điểm chung cuộc `🏆`.
- **Hệ thống Prompt Ngữ Cảnh Thông Minh (Contextual Prompts):** Tự động hiện banner nhắc phím khi đi vào vùng tương tác quanh Bến tàu `[E]`, Nút hái rau `[E]`, Đàn cá `[Space]`, Bếp và Bàn ăn `[E]` (kèm thông báo giỏ đầy / hồi chiêu).
- **Màn hình Game Over / Finished Screen:** Giải thích rõ nghĩa nguyên nhân kết thúc (`docked`, `time`, `fainted`), bảng tổng kết thành tích chi tiết và nút Chơi lại hỗ trợ cả click chuột trực tiếp lẫn phím `R`.
- **Sáng tạo bổ sung (Phase 2):**
  - Hệ thống âm thanh tự sinh bằng Web Audio API (0 KB asset, không dùng file ngoài).
  - Hệ thống hạt động VFX (bọt khí lặn sâu, gợn sóng nước, làn khói bếp).
  - Nút Bật/Tắt âm thanh `🔊 / 🔇` trực tiếp trên canvas (phím tắt `M`).

---

## 2. Tiêu chí chấp nhận đã kiểm chứng (Acceptance Criteria)
- [x] Buổi sáng: thời gian, thanh oxy đổi màu, máu, giỏ hàng, prompt ngữ cảnh bến/nút/cá.
- [x] Buổi tối: kho stock, khách + thanh kiên nhẫn đổi màu, bếp + đếm ngược, món trên tay, tiền, uy tín, prompt ngữ cảnh bếp/bàn.
- [x] Null-safety: Thiếu trường dữ liệu không làm văng lỗi JS console.
- [x] Bố cục HUD không che khuất vùng chơi trung tâm của nhân vật.
- [x] Màn kết thúc hiện lý do, điểm số, nút chơi lại hoạt động mượt mà.
- [x] Tuyệt đối không thay đổi mã nguồn trong `chonoi/sim/`, headless mode giữ nguyên 100% tính tất định.

---

## 3. Lệnh kiểm chứng đã chạy
```bash
# 1. Chơi thử trực tiếp giao diện buổi sáng
python3 -m chonoi.live --mode gather

# 2. Chơi thử trực tiếp giao diện buổi tối
python3 -m chonoi.live --mode quan

# 3. Kiểm thử tính bất biến headless JSONL
python3 -m chonoi.headless --mode gather --seed 1 --ticks 180 --out out_test.jsonl
```

---

## 4. Bằng chứng & Tài liệu đi kèm
- Bằng chứng nghiệm thu: [`docs/proof/phase-1/hud-ui.md`](docs/proof/phase-1/hud-ui.md)
- Ma trận truy vết: [`docs/verification/phase-1.md`](docs/verification/phase-1.md)
- Kịch bản demo 3 phút: [`docs/demo.md`](docs/demo.md)
- Phản tư cá nhân: [`docs/members/qvinhh2312.md`](docs/members/qvinhh2312.md)
- Bản quyền asset tự sinh: [`CREDITS.md`](CREDITS.md)

---

## 5. Phần AI hỗ trợ
- Công cụ: Antigravity (Gemini 3.8 Flash High).
- Đã sửa lỗi: AI ban đầu đề xuất dùng hàm `alert()` và popup DOM làm dừng animation loop của canvas; đã điều chỉnh sang canvas banner và modal overlay mượt mà.
