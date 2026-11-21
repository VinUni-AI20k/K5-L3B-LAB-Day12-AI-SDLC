# TV5 · HUD độ tươi (chuẩn bị Phase 3, TICKET-03)

Yêu cầu: *"Cho người chơi đọc được độ tươi hoặc nhận ra hàng ươn bằng số, thanh, nhãn hoặc biểu tượng."*

| Chỗ hiển thị | Cách thể hiện |
|---|---|
| Giỏ (HUD sáng) | Mỗi ô có thanh độ tươi (xanh ≥ 60, cam 30–60, đỏ < 30); hàng ươn: ô viền đỏ, biểu tượng xám + 🤢; nhãn "Giỏ 8/12 · 2 ươn"; di chuột xem `id · tươi xx.x` |
| Má Tư dặn | Chỉ đếm hàng **chưa ươn** vào đã lấy/cần; dòng phụ thanh + "tươi TB", "· n ươn" |
| EveningIntro | Mỗi loại: số lượng, "tươi TB", số ươn; "nấu được" chỉ tính hàng chưa ươn |
| Kho khả dụng (HUD quán) | Mỗi loại: còn trống / chưa ươn, thanh + "tươi" của cá thể tươi nhất, "· n ươn"; trừ phần giữ theo **id** (`reserved` mảng id) |
| Event | `spoiled` → toast "🤢 Cá lóc I6 đã ươn trong giỏ/kho" + tiếng; `cook_started` có giá chốt thấp hơn niêm yết → toast "giá chốt …k" |

Client đọc được cả v1.2 (mảng `{id,kind,fresh}`) lẫn v1.1 (mảng kind / object đếm), nên ghép lúc nào main cũng chạy.
Ngưỡng ươn: `fresh < 30` (so trước làm tròn; hiển thị cắt xuống 1 chữ số thập phân).

## Bằng chứng

- Ảnh 1280×720 (thu nhỏ 800×450): [01-hud-gather-freshness.jpg](ui/01-hud-gather-freshness.jpg) · [02-evening-intro-freshness.jpg](ui/02-evening-intro-freshness.jpg) · [03-hud-quan-freshness.jpg](ui/03-hud-quan-freshness.jpg)
- **Trung thực:** lúc chụp, sim trên main còn v1.1 (chưa có `fresh`). Ảnh dùng game thật (`chonoi.live --mode day`) nhưng snapshot được **giả lập v1.2 trong trình duyệt**: gắn `fresh` cố định [100, 88.5, 61, 47.25, 31, 29.5, 12, 95, …] cho từng cá thể và chèn một event `spoiled` mẫu. Chụp lại trên sim thật khi TV1–TV4 ghép xong độ tươi.
- Test lớp live: `tests/test_live_day.py::FreshnessV12ReadyTest` — đếm hàng dùng được bỏ hàng ươn (đúng 30 chưa ươn), Chợ Chú Sáu bán cá thể chưa ươn tươi nhất, hòa theo id (I2 trước I10).

## Bổ sung (UI)

- Ảnh: [06 hướng dẫn Ngày 1](ui/06-tutorial-day1-gather.jpg) · [07 sprite mới + Cá Sấu đuổi](ui/07-new-sprites-croc-chase.jpg) · [08 hiệu ứng ươn + đồng hồ ươn](ui/08-hold-spoil-effects-timer.jpg) · [09 Má Tư chấm hàng](ui/09-evening-matu-judge.jpg) · [10 quán mới + giá dự kiến](ui/10-quan-new-scene-price-estimate.jpg) · [11 quán trên sim thật, đang nấu, hướng dẫn bước 3](ui/11-quan-real-sim-cooking-tutorial.jpg)
- Ảnh 08–10 dùng snapshot giả lập v1.2 như trên; ảnh 06, 07, 11 là sim thật (v1.1).
- Đóng quán sớm: `tests/test_live_day.py::CloseEarlyTest` — `closed_early` → `customer_left(reason: closing)` → `quan_end` cùng bước, uy tín không đổi, sang DayResult.

## Kiểm trên sim v1.2 thật (sau PR #14–#17)

Chạy `chonoi.live --mode day` từ bản sao bật `contract_version 1.2`, giỏ mẫu 8 cá thể fresh 100 → 30.2:
- [12](ui/12-v12-real-gather-spoiled-events.jpg): sim phát `spoiled` I7, I5 → toast + giỏ "2 ươn", "⏳ I4 ươn sau 14 s".
- [13](ui/13-v12-real-hold-freshness.jpg): thanh tươi từng ô, hàng ươn viền đỏ, Má Tư dặn chỉ đếm hàng chưa ươn.
- [14](ui/14-v12-real-evening-matu.jpg): EveningIntro theo `gather_end.inventory` cá thể, cá lóc ươn hết → 0 suất, Má Tư chấm hàng.
- [15](ui/15-v12-real-quan-stock-freshness.jpg): kho quán theo cá thể, tươi nhất, ⏳ giây tới lúc ươn, số ươn.

Checkpoint headless: [qa-report.md](qa-report.md) (`python3 tools/qa_p3.py`).
