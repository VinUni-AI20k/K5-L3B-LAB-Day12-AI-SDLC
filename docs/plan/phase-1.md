# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:** Hoàn thành lõi PRD-0 cho nhóm 5 người: buổi sáng `gather` (lặn/nổi, oxy, ngạt, hái, bắt cá, cập bến, xuất kho), buổi tối `quan` (khách, giữ chỗ, bếp, bưng, phục vụ, boa, tiền, uy tín), nối 2 tiến trình qua file kho đúng Test Contract v1.0, HUD đọc được, test xanh trên `main`, đủ bằng chứng DoD và gắn tag `phase-1` trước 1:00.

- **Bảng đầu việc theo AC:**

| Mã AC | Nội dung chính | Phụ trách | Phụ thuộc |
|---|---|---|---|
| `AC-P1-01` | Test Contract v1.0 (`--ticks 0`, tất định từng byte, mã thoát 2) | A, E | Khung sẵn |
| `AC-P1-02` | Bơi, tăng/giảm tốc `ramp_max_ticks`, hướng, chặn biên | A | Khung sẵn |
| `AC-P1-03` | Phân vùng mặt/dưới nước (`dive`/`surface`), hồi/trừ oxy, `oxygen_empty` | A (Lát 1) | `AC-P1-02` |
| `AC-P1-04` | Ngạt (`choke` ở t+59), Máu 0 → `faint` (mất giỏ LIFO, `gather_end` kho rỗng) | A (Lát 1) | `AC-P1-03` |
| `AC-P1-05` | Hái nút ở mặt nước (`gather`, `regrow_ticks`, `node_regrown`), `hold_full` | B (Lát 2) | `AC-P1-02` |
| `AC-P1-06` | Bắt cá dưới nước (`catch`, `fish_caught`, xóa đàn, hồi chiêu, `hold_full`) | B (Lát 2) | `AC-P1-02` |
| `AC-P1-07` | Cập bến ưu tiên trước hái (`docked`), hết giờ (`time`) giữ giỏ, ghi kho 1 lần | A, B | `AC-P1-05`, `AC-P1-06` |
| `AC-P1-08` | Hợp đồng kho & smoke 2 tiến trình (`gather --inventory-out` → `quan --inventory`) | E, B | `AC-P1-07` |
| `AC-P1-09` | Khách theo lịch (`first_customer_tick`, `customer_interval_s`), chọn món từ kho khả dụng, giữ chỗ, `no_dish` | C (Lát 3) | Hợp đồng kho |
| `AC-P1-10` | Giảm kiên nhẫn, khách bỏ đi (`patience`/`closing`), nhả giữ chỗ, kiểm `scenario.py` (mã 2) | C (Lát 3) | `AC-P1-09` |
| `AC-P1-11` | Tương tác quán (`khoảng cách`, `bếp < bàn`, `id`): nấu, bưng, phục vụ | D (Lát 4) | `AC-P1-09` |
| `AC-P1-12` | Ăn xong trả tiền (`paid`), tính boa, uy tín/điểm, dọn ca (`quan_end`) | D (Lát 4) | `AC-P1-11` |
| `AC-P1-13` | HUD 2 buổi trong `chonoi/web/index.html` đủ thông số sáng/tối & chơi thử mượt | E | `chonoi.live` |
| `AC-P1-14` | DoD & Quy trình: README ≤ 3 lệnh, `TEAM.md` 5 người + `team_size: 5`, 2 skill, verification + proof, log AI | E & cả nhóm | `AC-P1-01`..`13` |

- **Mốc phối hợp (60 phút):** `0–15` kickoff & chốt hợp đồng; `20` standup 1 (rà lát chậm để người dự phòng hỗ trợ); `25` B xuất kho thật & E chạy smoke 2 tiến trình; `45` standup 2 (đóng băng tính năng); `45–55` kiểm chứng trên `main`; `55–60` dự phòng & A đẩy tag `phase-1`.

- **Rủi ro & giảm thiểu:**
  - *Conflict `gather.py` (A/B) và `quan.py` (C/D):* tách rõ thân hàm trong `step()`, pull `main` thường xuyên trước khi merge.
  - *Windows thiếu `python3` cho `headless_cmd`:* chạy test qua WSL/Git Bash có `python3`, tuyệt đối không sửa `headless_cmd` trong `game.contract.json`.
  - *Chậm tiến độ lát:* A↔B và C↔D dự phòng chéo cho nhau, E hỗ trợ sau khi xong HUD & khung QA.
