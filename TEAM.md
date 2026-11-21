# TEAM

**Tên nhóm:** DoctorX (`team: "doctorx"`)  **Số người:** 6  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Trần Cảnh Hưng | danialtranz | `sim/gather` — Lát 1: bơi, oxy, biên, giỏ | Scrum/Release | Lát 2 (Phát) |
| Trương Đức Phát | trdphat | `sim/gather` — Lát 2: hái, bắt cá, cập bến, ghi kho | — | Lát 1 (Hưng) |
| Vũ Quang Minh | … | `sim/quan` — Lát 3: khách, giữ chỗ nguyên liệu, kiên nhẫn | PO | Lát 4 (Diệp) |
| Hoàng Minh Diệp | HoangMinhDiep | `sim/quan` — Lát 4: bếp, bưng, phục vụ, tiền, uy tín | Integrator (trưởng nhóm) | Lát 3 (Minh) |
| Phùng Thị Nhài | nhaipt342k4 | `client/ui` — HUD 2 buổi, `chonoi/web/`, `live.py`; mở rộng #1 | — | UI + chơi thử |
| Mai Xuân Khang | KhangMai123 | `qa` — `tests/`, ma trận truy vết, `docs/proof/`; mở rộng #2 | QA lead | `scenario.py` / `contract.py` |

> Mỗi người tự thay `…` bằng GitHub handle của mình (commit đầu tiên). `python3 tools/check_team.py` phải báo OK.

**Vai quy trình:** PO (đầu mối hỏi Anh Năm hàng xóm/giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gộp code, gắn tag `phase-1`) · QA lead (giữ bộ test, `docs/verification/phase-1.md`) · Scrum/Release (giữ mốc thời gian, standup, `docs/standup.md`, `CHANGELOG.md`).

## Chia việc Phase 1 chi tiết

| Người | Việc cụ thể (file chính) | Phụ thuộc | Xong khi |
|---|---|---|---|
| Hưng (Lát 1) | `chonoi/sim/gather.py`: `dive`/`surface` theo biên d ≤ 0.5; oxy theo d cuối bước (+6/tick trên mặt, −1 dưới nước, kẹp); `oxygen_empty`; `zero_oxy_ticks` → `choke` mỗi 60 tick; Máu 0 → bỏ giỏ LIFO, `faint`, `gather_end` fainted, kho rỗng; giỏ theo thứ tự nhặt, trần `hold_capacity` | Khung sẵn có | Test oxy/ngạt/ngất xanh (ngạt lần đầu ở t+59, nổi đúng bước ngạt thì không ngạt) |
| Phát (Lát 2) | `chonoi/sim/gather.py`: hái nút ready gần nhất (chỉ ở mặt nước, hòa theo id) → `gather`, `regrow_ticks`; `node_regrown`; `catch` dưới nước, hết hồi → `fish_caught` + cooldown; `hold_full` (không thử đàn khác); bến xét trước hái; kho khớp `gather_end.inventory` | Giỏ của Hưng (chốt API `hold` trước phút 15) | Smoke `dock.json` ra `catch.json` đúng; ghi kho thật trước phút 25 |
| Minh (Lát 3) | `chonoi/sim/quan.py`: khách fixture từ scenario + suy `reserved`; lịch khách `first_customer_tick` rồi mỗi `customer_interval_s`; bàn trống id nhỏ nhất; chọn đều theo seed trong món đủ kho khả dụng; `no_dish`; giữ chỗ ngay; kiên nhẫn giảm từ bước sau; `customer_left` patience (−0.5 uy tín) / closing | Kho mẫu `docs/contracts/inventory.sample.json` | Khách đến, giữ chỗ, bỏ đi đúng tick |
| Diệp (Lát 4) | `chonoi/sim/quan.py`: tối đa 1 interact chọn theo (khoảng cách, bếp trước bàn, id); bếp idle lấy đơn reserved cũ nhất → `cook_started`; `dish_ready`; `dish_picked` (`carry_limit` 1); `served` + boa `floor(price × 0.2)` nếu kiên nhẫn ≥ 50%; `paid`; tiền/`earned`/uy tín kẹp [0,5]; hết ca → `quan_end`; score | Trạng thái khách/đơn của Minh (chốt tên trường trước phút 15) | Một vòng nấu → bưng → phục vụ → trả tiền đúng event |
| Nhài (UI/HUD) | `chonoi/web/index.html`, `chonoi/live.py`: HUD sáng (thời gian, oxy, Máu, giỏ); HUD tối (kho khả dụng, món gọi, kiên nhẫn, trạng thái bếp, món trên tay, tiền, uy tín); hình khối 2D theo phong cách miền Tây; sau lõi làm **mở rộng #1** (phần thêm phải tắt ở headless) | Snapshot của các lát (đọc trường theo Test Contract E) | Chơi thử 2 buổi trên trình duyệt, HUD đọc được |
| Khang (QA) | `tests/`: test theo từng AC cho 4 lát (viết trước bằng scenario + inputs); smoke 2 tiến trình; kiểm mã thoát 0/1/2; `docs/verification/phase-1.md` + `docs/proof/phase-1/`; bổ sung kiểm fixture trong `scenario.py`/`contract.py` (TODO(nhóm)); sau lõi làm **mở rộng #2** | Có thể bắt đầu ngay từ PRD | Ma trận truy vết đủ AC, kết quả thật lưu trong `docs/proof/phase-1/` |

**Việc chung của từng vai:**
- **PO (Minh):** gom câu hỏi mơ hồ, hỏi Anh Năm, ghi `docs/clarify.md`; chọn 2 mục mở rộng cùng nhóm ở phút 15.
- **Integrator (Diệp):** chốt `docs/contracts/` (file kho + sự kiện/trạng thái sim↔UI) trước phút 15; `team_size`/`team` trong `game.contract.json`; gộp các lát; chạy smoke trên main; gắn và đẩy tag `phase-1` trước 1:00.
- **QA lead (Khang):** giữ bộ test xanh trên main; từ chối gộp nếu test đỏ.
- **Scrum/Release (Hưng):** nhắc mốc phút 15/20/25/45/55; ghi `docs/standup.md`, `CHANGELOG.md`, nhắc mọi người ghi `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.
- **Mọi người:** tối thiểu 3 commit có nội dung từ tài khoản của mình; tự viết `docs/members/<handle>.md`.

## Mốc thời gian (60 phút)

| Phút | Việc |
|---|---|
| 0–15 | Điền handle, chốt hợp đồng kho + tên trường trạng thái, Khang dựng test khung, các lát bắt đầu song song |
| 20 | Rà lát chậm; người xong trước (thường Nhài/Khang) sang hỗ trợ |
| 25 | Phát xuất file kho thật; Minh/Diệp thử nạp vào quán |
| 30 | Standup 2–3 phút: đã xong / sắp làm / đang vướng |
| 45–55 | Diệp gộp cuối, chạy smoke 2 tiến trình trên main; Khang hoàn thiện ma trận truy vết; cả nhóm chơi thử |
| 55–60 | Dự phòng; Diệp đẩy tag `phase-1` |

## Thỏa thuận làm việc nhóm

- Kênh liên lạc: nhóm chat chung của DoctorX (Zalo/Messenger); việc quan trọng ghi thêm vào issue trên GitHub.
- Khi bất đồng về thiết kế: nói tối đa 2 phút; không xong thì Integrator (Diệp) quyết, riêng chỗ PRD mơ hồ thì PO (Minh) hỏi Anh Năm, rồi ghi lại trong `docs/clarify.md` hoặc ADR.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh nhóm; người dự phòng ở bảng trên vào pair; quá 20 phút thì người dự phòng nhận tiếp phần việc.
- Giờ standup giữa phase: phút 30 của phase, 2–3 phút, Scrum (Hưng) điều phối.
- Cách đọc code của nhau: review chéo theo cặp dự phòng (Hưng↔Phát, Minh↔Diệp, Nhài↔Khang); xem PR hoặc xem trực tiếp.
- Cách làm việc với Git: nhánh ngắn `p1/<lat>-<ten>` → PR vào `main`, CI xanh và 1 người duyệt; chạy test trước khi đẩy; không sửa `docs/contracts/`, `game.contract.json` khi chưa báo nhóm; chỉ Integrator (Diệp) gắn tag.
