# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| C-01 | 2026-11-21 Phase 1 | `hold_full` khi hái: `required` là gì? | Giả định: `required = node_yield` (1), `free = hold_capacity − số món trong giỏ`. Khi bắt: `required = fish_yield[kind]`. | Nhóm (chưa hỏi Anh Năm) |
| C-02 | 2026-11-21 Phase 1 | Id khách sinh mới dùng tiền tố nào? | Giả định: `C` + số (`C1`, `C2`…), nối sau hậu tố lớn nhất đã nạp qua `IdAllocator`. `order_id` = id khách. | Nhóm |
| C-03 | 2026-11-21 Phase 1 | Khách đang chờ có `base_price`/`tip` không? | Giả định: `null` cho tới khi chốt (giá chốt lúc `cook_started`, boa chốt lúc `served`). | Nhóm |
| C-04 | 2026-11-21 Phase 1 | Đơn `reserved` trong fixture thiếu `reserved` mà kho không đủ? | Giả định: chuyển `unfulfillable`, giữ chỗ rỗng (cấp theo `order_tick` rồi id bàn). | Nhóm |
| C-05 | 2026-11-21 Phase 1 | Khách ăn xong đúng tick hết ca: `paid` lý do nào? | Giả định: ưu tiên `finished_eating` (timer ăn về 0 xét trước), còn lại trả `closing`. | Nhóm |
| C-06 | 2026-11-21 Phase 1 | Bếp idle mà không có đơn reserved, hoặc tay đang cầm món mà bấm vào bếp ready? | Bỏ lượt, không event (mục F.3 "không tương tác được thì bỏ lượt"). | Nhóm |
| C-07 | 2026-11-21 Phase 1 | `invuln_ticks` (có trong khung) có chặn ngạt không? | Không — v1.0 không nhắc bất tử; chỉ đếm lùi, không ảnh hưởng luật. | Nhóm |
| C-08 | 2026-11-21 Phase 1 | Cộng dồn uy tín 0.2 bằng số thực có thể ra 3.9999… làm `floor` sai | Làm tròn 9 chữ số sau mỗi lần đổi uy tín rồi kẹp theo tuning. | Nhóm |

## Phase 2 (Test Contract v1.1)

### Lát 1–2: số chuẩn, cá bơi/sinh, Cá Sấu (agent A, `chonoi/sim/gather.py`)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| C-P2-A01 | 2026-11-21 Phase 2 | Cá đổi hướng thế nào? | Hướng mới = `rng("fish_turn").random() * 360`, duyệt cá theo id, đổi khi `(age_ticks + 1) % 120 == 0` TRƯỚC khi di chuyển. | Nhóm |
| C-P2-A02 | 2026-11-21 Phase 2 | Phản xạ mép? | Lật phần vượt theo từng trục và đổi dấu thành phần vận tốc đó; hướng tính lại bằng `atan2` mod 360; chạm góc đảo cả hai. | Nhóm |
| C-P2-A03 | 2026-11-21 Phase 2 | Chọn loài / điểm khi sinh? | Loài: `rng("fish_spawn").random() * Σ trọng số` trên các loài còn điểm hợp lệ, theo thứ tự khóa trong contract; điểm: `randrange` trên `fish_spawn_x × depths` của loài; hướng `random() * 360`. 8 đàn đầu ca dùng cùng thủ tục, không phát `fish_spawned`, id `F1..`. | Nhóm |
| C-P2-A04 | 2026-11-21 Phase 2 | Lịch sinh và scenario `fish`? | Sinh khi `phase_tick % 360 == 0` và chỉ khi `random_fish` true; khai `fish` (kể cả `[]`) khi cờ true thì thay đàn đầu ca, vẫn bơi/sinh. | Nhóm |
| C-P2-A05 | 2026-11-21 Phase 2 | Kiểm vị trí cá trong scenario? | `random_fish` true: cá phải nằm trong `fish_x` và dải độ sâu của loài, sai → mã 2; false: chỉ cần ở dưới nước. | Nhóm |
| C-P2-A06 | 2026-11-21 Phase 2 | Cá Sấu quyết trạng thái theo vị trí nào? | Theo vị trí người chơi SAU khi di chuyển; quái di chuyển theo trạng thái mới ngay bước đó; chase dừng tại người chơi không vượt; dung sai chạm waypoint 1e-9; ngưỡng độ sâu = `depths[0]` của loài. | Nhóm |
| C-P2-A07 | 2026-11-21 Phase 2 | Bất tử 90 tính thế nào? | Giảm bất tử đầu bước: hit ở bước t đặt 90 → bảo vệ các bước t+1…t+89. | Nhóm |
| C-P2-A08 | 2026-11-21 Phase 2 | Hết recoil? | Quái hết recoil ở bước k chuyển patrol sau khi di chuyển và không được xét hit ở bước k; phát hiện/hit lại từ k+1; recoil giữ `target_idx`. | Nhóm |
| C-P2-A09 | 2026-11-21 Phase 2 | Kiểm `gather.monsters[]` trong scenario? | Không recoil: `state_ticks_left` 0 và `recoil_dir` null; recoil: `state_ticks_left > 0` và `recoil_dir` đơn vị (dung sai 1e-6); pos/waypoints trong map + dải loài; `player.invuln_ticks ≤ 90`. | Nhóm |
| C-P2-A10 | 2026-11-21 Phase 2 | Dữ liệu `monster_hit` / `faint` do quái? | `monster_hit.lost` liệt kê kind bị rơi theo LIFO, `pos` = vị trí người chơi; `faint` do quái: `lost` = phần giỏ còn lại theo LIFO. | Nhóm |

### Lát 3–4: quán, pause, vòng Ngày, Shop (agent B)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| C-P2-B01 | 2026-11-21 Phase 2 | Event tick 0 của `day` (day_start, day_plan, phase_start) ghi trước hay sau snapshot tick 0? | Ghi TRƯỚC snapshot tick 0, giống thứ tự "event rồi snapshot" của mọi tick. | Nhóm |
| C-P2-B02 | 2026-11-21 Phase 2 | Bước resume có nhận cạnh hành động / `buy` cùng frame không? | Có: bước có cạnh `pause` lần hai phát `resumed` rồi chạy gameplay đầy đủ với input của frame đó. Cạnh hành động trong các bước còn pause bị bỏ (chốt vẫn cập nhật nên giữ nút qua pause không tạo cạnh mới). | PO (Duyet): **không hỏi kịp** giảng viên trước hạn `phase-4`, giữ giả định; test AC-P2-40 viết theo giả định này (ghi 2026-11-21, sau Release) |
| C-P2-B03 | 2026-11-21 Phase 2 | `phase_tick` / `sim_tick` trong snapshot? | `sim_tick` = số bước gameplay (không tính bước pause); mode độc lập `phase_tick = sim_tick`; `day`: số bước gameplay từ đầu pha hiện tại (0 ở snapshot đổi pha). Snapshot luôn được ghi ở tick đổi pha (ngoài `--snapshot-every`). | Nhóm |
| C-P2-B04 | 2026-11-21 Phase 2 | Mẫu `gather`/`quan` trong scenario `day` áp cho Ngày nào? | Áp cho MỌI Ngày ("mẫu khởi tạo mỗi Ngày"): giỏ mỗi Ngày dựng lại từ `gather.hold` (mặc định rỗng), khách mẫu dựng lại mỗi tối. Món của khách mẫu phải thuộc kế hoạch của mọi Ngày sẽ chạy (kiểm trước khi ghi đầu ra → mã 2). | PO (Duyet): **không hỏi kịp** giảng viên trước hạn `phase-4`, giữ giả định; chưa có test riêng cho mẫu áp mọi Ngày (ghi 2026-11-21, sau Release) |
| C-P2-B05 | 2026-11-21 Phase 2 | Mâu thuẫn chỉ phát hiện được trên kho thực lúc mở quán (vd. khách mẫu giữ chỗ vượt kho) | Thoát mã 2 và XÓA file đầu ra đã ghi dở (không thể biết kho thực trước khi chạy gather). | PO (Duyet): **không hỏi kịp** giảng viên trước hạn `phase-4`, giữ giả định; test AC-P2-72 viết theo giả định này (ghi 2026-11-21, sau Release) |
| C-P2-B06 | 2026-11-21 Phase 2 | `buy` `weapon`/`net`/`buy:<kind>`/`sell:<kind>` khi chưa bật mở rộng | `buy_failed {action, reason:"unknown"}` (lệnh không hỗ trợ). `buy` ngoài Shop (gather/quan) bị bỏ qua, không event. Nút `attack`/`photo` boolean được nhận và bỏ qua. | Nhóm |
| C-P2-B07 | 2026-11-21 Phase 2 | Thứ tự kiểm `buy_failed` | `unknown` → `max_level` (không còn cấp kế) → `funds` (giá > money). Đủ đúng giá vẫn mua. | Nhóm |
| C-P2-B08 | 2026-11-21 Phase 2 | `day.upgrades` trong scenario là cấp đã mua hay đang áp dụng? | Là cấp đã mua; Ngày 1 được dựng nên chép sang `active_upgrades` ngay → có hiệu lực từ Ngày 1. | Nhóm |
| C-P2-B09 | 2026-11-21 Phase 2 | Id khách / cá qua nhiều Ngày | Một `IdAllocator` và một `Streams` cho cả lượt: id khách tiếp tục tăng qua Ngày (`order_id` duy nhất trong file), luồng RNG nối tiếp. | Nhóm |
| C-P2-B10 | 2026-11-21 Phase 2 | Snapshot `day` có thêm gì ngoài khóa bắt buộc? | Thêm `days_completed` (số Shop đã đóng) cho HUD; `day_plan` trong snapshot = `{dishes, ingredients}` của Ngày hiện tại. | Nhóm |
| C-P2-B11 | 2026-11-21 Phase 2 | DayIntro 4 s / EveningIntro có chiếm tick headless? | Không: chỉ là màn UI; headless một Ngày = 10.800 + 10.800 + 600 = 22.200 tick đúng mốc tối đa của ticket. | Nhóm |

## Phase 3 (TICKET-03 v1.2) — giả định của lát Quán/day
- Nhiều đơn cùng có phần giữ vừa ươn trong một tick: nhả phần giữ của TẤT CẢ đơn bị ảnh hưởng trước, rồi giữ lại từng đơn một lần theo (order_tick, id bàn).
- Đơn chuyển unfulfillable do ươn không phát event riêng (contract không định nghĩa); thấy qua snapshot.
- Snapshot quán xuất `fresh` từ đơn vị nguyên; dung sai quan sát ±0.01 theo contract.
- `customers[].reserved` trong snapshot sắp theo kind rồi id.

## Phase 4 (TICKET-04 v1.3) — giả định Bench/Soak
- C-P4-01: `bench_cmd` = `python3 tools/bench.py`, `soak_cmd` = `python3 tools/soak.py` (chạy từ gốc repo). Chỉ stdlib; trình duyệt = Chrome/Chromium hệ thống (ghi đè bằng `CHONOI_BROWSER`). Không có Playwright/websockets → không dùng CDP; trang tự đo rồi POST `/bench-result` về server cục bộ.
- C-P4-02: "từ lúc khởi chạy" trong `load_ms` hiểu là từ lúc runner spawn trình duyệt (tham số `t0` epoch ms) tới khung rAF đầu tiên sau khi `state.mode === "gather"`.
- C-P4-03: Cảnh đo = `go("gather")` ở chế độ demo (Ngày 1 buổi sáng, hiệu ứng mặc định), không input → Út Sen đứng ở bến. Seed áp qua `Math.random` thay thế trong `client/src/bench.js`.
- C-P4-04: Soak Ngày > 5 dùng kế hoạch ((day-1) % 5) + 1 (`DaySim.plan_for`); headless `--days` giữ 1..5.
- C-P4-05: Mỗi phần tử `results` ghi tại event `shop_end`; `score = earned + 100 × floor(reputation)` như snapshot. Crash = ngoại lệ bất kỳ hoặc một Ngày quá 200 000 tick; được đếm, tiến trình không rơi.
