# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

Nguồn trả lời ưu tiên: **Anh Năm hàng xóm** (trợ giảng AI ở tab Phase 1 của lab board) → giảng viên → nhóm tự đặt giả định.

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| Q1 | | `catch` khi giỏ không đủ chỗ: có đặt hồi chiêu không? PRD ghi "giữ đàn và cooldown" | Giả định: **không** đặt hồi chiêu, giữ nguyên bộ đếm cũ | PO |
| Q2 | | `paid.amount` = `base_price + tip`? | Giả định: đúng (tổng khách trả) | PO |
| Q3 | | `cook_started.items` là mảng kind đã tiêu, có lặp lại? | Giả định: có lặp, sắp theo kind | PO |
| Q4 | | `gather.amount` luôn bằng `node_yield` (hiện = 1)? | Giả định: đúng | PO |
| Q5 | | `faint.lost` khi giỏ rỗng là `[]`? | Giả định: đúng | PO |
| Q6 | | Khách ăn xong và khách mới đến cùng một tick: thứ tự event? | Giả định: trả tiền/rời trước, sinh khách sau | PO |
| Q7 | | `phase_tick` khi `time_left_ticks` bị rút ngắn vẫn bắt đầu 0? | Giả định: đúng | PO |
| Q8 | | `invuln_ticks` (starter có, PRD mục D không có) — bỏ khỏi scenario/snapshot? | Giả định: bỏ khỏi scenario; snapshot có thể giữ để không vỡ client | Integrator |
| Q9 | | Scenario đặt sẵn `oxygen_ticks = 0`, `zero_oxy_ticks = 0`: ngạt đầu ở tick 59 hay 60? | Giả định: **60** — bước đầu tiên có oxy 0 là t = 1 nên ngạt ở t+59; ca ngập từ oxy đầy vẫn là 1859 | QA |
| Q10 | | `regrow_ticks = 1200` đặt ở tick hái (event tick) — nút mọc lại ở `tick_hái + 1200`? | Giả định: đúng, test tính theo `event.gather.tick + 1200` | QA |
| Q11 | 2026-11-21 | `bench_cmd` khi môi trường không có Google Chrome / Chromium? | Thoát mã 2 và in thông báo rõ ràng theo spec Phase 4 | Integrator |
| Q12 | 2026-11-21 | `soak_cmd` bỏ trường `duration_s` khi kiểm tra tính tất định cùng seed? | Đúng, vì thời gian chạy phụ thuộc vào tải CPU phần cứng của máy chấm | QA |
| Q13 | 2026-11-21 | Trạng thái Chế độ tương phản cao có cần lưu bền vững qua các phiên chơi? | Đúng, ghi nhớ trong `sessionStorage` của trình duyệt | UX/UI |

## Bàn giao PO — Nhật Minh, Phase 1 (2026-11-21)

- Ticket 03 triển khai theo **giả định Q1 hiện có**: bắt hụt vì giỏ thiếu chỗ giữ đàn, không đặt hồi chiêu mới. Test ghi rõ hành vi này; chưa có câu trả lời của trợ giảng để đóng Q1.
- Q2–Q8 vẫn là giả định, chưa có bằng chứng xác nhận. Cần đưa nguyên văn câu hỏi ở bảng trên cho Anh Năm/giảng viên và ghi nguồn trả lời trước khi đổi luật/contract.
- Phân công hiện hành lấy từ `TEAM.md`, `docs/plan/phase-1.md` và `docs/tickets/phase-1/README.md`: Nhật Minh làm ticket 03 + PO. Bảng trong conformance/team-split có phần dự kiến cũ; không tự nhận thêm luật quán của thành viên khác.
- Tại thời điểm làm P1 chỉ có yêu cầu P1 trong nhánh cá nhân. Nay đã đọc spec/ticket P2–P3 từ object `phase-1`/dependency v1.1; phần phân công mới theo README từng phase thay cho dự kiến trong team-split.
- Đã xác minh core ticket 02 vào repo chung qua PR #1, commit `9342f9e`. Core này và helper ticket 03 đã được ghép trong bản làm việc `feat/nhat-minh`, 62/62 test qua, gồm ca ngất/kho rỗng. [Bằng chứng lát 2](proof/phase-1/nhat-minh.md). Chưa có review của người cho phần Nhật Minh.

## Bàn giao PO — Phase 2–3

- Phân công xác nhận: P2 ticket 02 (cá) + 07 (net); P3 ticket 02 (độ tươi) + 07 (current). Không tự nhận phần quán, shop/day, contract hoặc adapter của thành viên khác.
- Dependency kiểm được: `c84eac9` (v1.1 prefactor), `6187354` (thêm Cá Sấu). Adapter `Stock` v1.2 chưa có trong các nguồn đã kiểm; cần owner cung cấp API/commit trước khi ghép kho, không coi component probe là bằng chứng migration.
- Quy ước kỹ thuật đề xuất cho net: mỗi cấp dùng `{level, price, radius, max_schools}`; đã chuẩn bị patch data đúng hai cấp của ticket. Integrator cần review tên trường và truyền `extensions` + `active_upgrades` vào gather.
- Tính tuổi trong giỏ dùng đơn vị nguyên theo ADR-0001; giao diện handoff xuất `{id, kind, fresh}`, không làm tròn trước so ngưỡng. Chưa xác nhận `Stock.add/take/items` cụ thể; cần ghép lớp này sau khi owner bàn giao.
- Current chỉ phát các event ticket đã định nghĩa: `current_warning` và `current_end`. Không tự thêm event bắt đầu. Validator cần nhận `random_current`/`current_direction`; lịch, hướng và lực đẩy đã kiểm ở lớp sim.
- Bằng chứng: [Phase 2](proof/phase-2/nhat-minh.md), [Phase 3](proof/phase-3/nhat-minh.md).
