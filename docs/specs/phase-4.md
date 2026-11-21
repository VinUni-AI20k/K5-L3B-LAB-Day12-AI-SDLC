# Spec — Phase 4: Phát hành v1.0.0 (contract v1.3)

> Nguồn: TICKET-04 / PRD Phase 4 (lab board `#phase-4`). Điều kiện vào: `phase-2` và `phase-3` đã tag —
> cảnh bench cần **cá bơi + Cá Sấu + độ tươi**, soak cần **vòng ngày + Shop**.

## Problem Statement

Game đã chơi được nhưng không ai biết nó nặng bao nhiêu, cảnh báo nguy hiểm có dễ nhận ra không, và không có
cách nào để người khác chạy thử từ repo sạch rồi tin rằng bản này ổn. Cũng chưa có bằng chứng game chịu được
nhiều Ngày liên tiếp mà không vỡ.

## Solution

Đóng gói một **bản phát hành v1.0.0** có số đo: `bench_cmd` đo FPS thật của cảnh chuẩn (có render, 1280×720,
làm nóng 3 s, đo 30 s, xuất `bench.json`); `soak_cmd` chạy 10 Ngày headless và xuất `soak.json`; ba cảnh báo
nguy hiểm có chữ/biểu tượng + chế độ tương phản cao; README 3 lệnh từ clone sạch; GitHub Release kèm gói chạy được,
release notes, CHANGELOG theo phase, CREDITS/LICENSE rà lại.

## User Stories

1. Là người chấm, tôi muốn chạy một lệnh và nhận `bench.json` đúng 5 trường, để so hiệu năng giữa các nhóm.
2. Là người chấm, tôi muốn `bench` đo cảnh thật (có render, 1280×720), không phải mô phỏng trần.
3. Là người chấm, tôi muốn `soak --days 10` chạy hết 10 Ngày với 0 crash, để biết game không rò rỉ trạng thái.
4. Là người chấm, tôi muốn soak tất định ở phần gameplay (bỏ số đo thời gian), để so hai lần chạy.
5. Là người chơi, tôi muốn thấy "Thủy quái!" kèm biểu tượng khi Cá Sấu gần, để không bị cắn từ phía sau.
6. Là người chơi, tôi muốn cảnh báo oxy sắp hết rõ ràng, để kịp nổi lên.
7. Là người chơi, tôi muốn thấy khách sắp giận, để ưu tiên đúng người.
8. Là người chơi, tôi muốn chế độ tương phản cao, để chơi được trên màn hình kém hoặc khi mù màu.
9. Là người dùng mới, tôi muốn clone rồi chạy trong 3 lệnh, để không phải đọc code.
10. Là giảng viên, tôi muốn GitHub Release v1.0.0 kèm gói chạy được và release notes, để lưu trữ và chấm.
11. Là người chơi, tôi muốn bảng xếp hạng cục bộ top 10, để có lý do chơi lại (mở rộng).
12. Là người khiếm thính, tôi muốn phụ đề cho hiệu ứng âm thanh, để không mất thông tin (mở rộng).

## Implementation Decisions

- **`bench_cmd` đo bằng trình duyệt thật.** Khởi động `chonoi.live` trên cổng ngẫu nhiên, mở Chrome headless
  qua DevTools Protocol ở 1280×720, chờ khung hình đầu (`load_ms`), làm nóng 3 s, rồi đo 30 s bằng
  `requestAnimationFrame` trong trang. Cảnh đo: buổi sáng lõi, Út Sen đứng yên ở bến, seed 42.
- **Công thức `p1_low_fps`**: lấy `n = max(1, ceil(0.01 × frames))` khung chậm nhất, `p1 = 1 / (tổng thời gian
  của n khung / n)`. Không dùng trung bình cộng FPS của các khung.
- **Bench ghi đúng 5 trường** `avg_fps, p1_low_fps, frames, measured_s, load_ms`; số nguyên cho `frames`,
  số thực cho phần còn lại. Không thêm trường (runner so cấu trúc).
- **`soak_cmd` dùng cùng lớp sim**, chạy `day` bằng **bot tất định** (input sinh từ trạng thái, không RNG ngoài
  `Streams`), `--seed` và `--days`; mỗi Ngày ghi `results[]` tại lúc Shop đóng; đếm `crashes` bằng try/except
  quanh từng bước. So sánh lặp: bỏ `duration_s`.
- **Contract 1.3 chỉ thêm lệnh**: `contract_version: "1.3"`, `bench_cmd`, `soak_cmd`; gameplay/tuning/kho/JSONL
  vẫn là v1.2 — không đổi một con số luật nào.
- **Cảnh báo** dùng **chữ + biểu tượng** (không chỉ màu): "Thủy quái!" + viền, "Hết hơi!" + nhấp nháy theo nhịp,
  "Khách sắp giận" + mặt buồn. Chế độ tương phản cao (phím `C`) tăng tương phản nền/chữ, tắt hiệu ứng rườm.
- **Gói phát hành**: zip chứa repo ở commit tag (không kèm `.git`), kèm `README` và script chạy; đính vào
  GitHub Release `v1.0.0` cùng commit với tag `phase-4`.
- **Leaderboard (mở rộng)**: lưu top 10 cục bộ, một mục mỗi lượt đủ 5 Ngày; `run_cmd --export-leaderboard`;
  headless `day` nhận `--leaderboard` + `--player-name`; file xếp hạng **không** đổi JSONL.

## Testing Decisions

- Bench: test cấu trúc `bench.json` (đủ 5 trường, kiểu đúng, `frames > 0`, `measured_s > 0`), không chấm ngưỡng.
- Soak: 10 Ngày → `days_completed == days`, `crashes == 0`; chạy lại cùng seed → `results` giống nhau sau khi
  bỏ `duration_s`.
- Cảnh báo: kiểm bằng ảnh chụp ba cảnh (thủy quái, hết hơi, khách sắp giận) **ở chế độ tương phản cao**.
- Đóng gói: clone sạch vào thư mục tạm, chạy đúng 3 lệnh README, chụp màn hình.
- Regression P1–P3 chạy lại trên commit tag; test nào đổi phải ghi lý do.

## Out of Scope

- Đổi engine/asset ngoài; leaderboard online; multiplayer; lưu game.
- Các mở rộng không chọn (Lao, Vợt, Rắn, Cháy, Chợ) — chỉ làm `net` nếu P2 chọn, và leaderboard/SFX nếu đủ giờ.

## Further Notes

- **Không tag `phase-4` trước khi P2 và P3 xong**: bench sẽ đo cảnh thiếu cá bơi/Cá Sấu/độ tươi, soak không có
  `day` để chạy 10 Ngày — tag sẽ là bằng chứng sai.
- Máy chấm là Linux; `bench_cmd` phải tự tìm trình duyệt (`CHROME`/`chromium`/`chrome`) và báo mã 2 nếu không có.

## Đo thử trên máy hiện tại (obscura, không GPU)

| Cảnh | avg_fps |
|---|---|
| Trang trống (chỉ rAF) | 57,5 |
| Canvas 1280×720, **một** `fillRect`/khung | 21,5 |
| Trang game (cảnh sáng lõi) | **6,2** |
| Trang game, `?fx=0` | 6,7 |

Kết luận: **obscura rasterize canvas bằng CPU**, trần ~21 FPS cho một khung 1280×720, nên số đo ở máy này phản ánh
trình duyệt chứ không phản ánh game. `bench_cmd` vì vậy ưu tiên **Playwright → obscura → chrome**; số báo cáo trong
`docs/proof/phase-4/` phải chạy trên máy có Playwright/GPU (máy chấm Linux), và ghi rõ môi trường đo.
