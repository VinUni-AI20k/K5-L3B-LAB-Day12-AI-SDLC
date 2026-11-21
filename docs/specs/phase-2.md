# Spec — Phase 2: Một ngày ở chợ nổi (contract v1.1)

> Nguồn: TICKET-02 / PRD Phase 2 (lab board `#phase-2`) + Test Contract v1.1.
> Danh sách khóa manifest: `docs/tickets/phase-2/01-contract-v11-prefactor.md`.

## Problem Statement

Hai buổi đã chạy được nhưng rời rạc: người chơi lặn xong thì hết, không có lý do để chọn mang gì về, không có gì để mua, không có lý do chơi lại. Cá đứng yên nên buổi sáng là bài tập bơi chứ không phải đi săn; không có nguy hiểm nên Máu vô nghĩa; quán chỉ có 1 bếp/1 bàn nên không có áp lực phối hợp.

## Solution

Biến hai buổi thành **một vòng ngày 5 Ngày**: sáng Má Tư công bố món cần nấu (kế hoạch), người chơi đi lấy đúng nguyên liệu đó trong khi cá bơi và Cá Sấu săn; tối quán mở với kho mang về; cuối ngày Shop bán nâng cấp có hiệu lực từ Ngày sau. Contract nâng lên v1.1 với số liệu chuẩn, 3 loài cá, 6 món, 2 bếp, 4 bàn, `--mode day`.

## User Stories

1. Là người chơi, tôi muốn biết sáng nay cần lấy gì, để không phải đoán.
2. Là người chơi, tôi muốn thấy "đã lấy 3/6 bông súng" ngay trên HUD, để biết còn thiếu gì.
3. Là người chơi, tôi muốn cá bơi theo dải độ sâu riêng, để phải lặn đúng tầng.
4. Là người chơi, tôi muốn cá sinh thêm theo thời gian, để không cạn nguồn.
5. Là người chơi, tôi muốn Cá Sấu tuần tra rồi đuổi khi tôi xuống sâu, để buổi sáng có nguy hiểm thật.
6. Là người chơi, tôi muốn bị cắn thì mất Máu và rơi nửa giỏ, để mỗi chuyến có giá.
7. Là người chơi, tôi muốn có 2 bếp và 4 bàn, để phục vụ nhiều khách hơn trong cùng thời gian.
8. Là người chơi, tôi muốn 6 món với nguyên liệu khác nhau, để chuyến lặn có mục tiêu đa dạng.
9. Là người chơi, tôi muốn chơi trọn một Ngày từ intro đến Shop, để thấy tiến bộ.
10. Là người chơi, tôi muốn nâng cấp bình oxy/áo phao bằng tiền kiếm được, để Ngày sau dễ hơn.
11. Là người chơi, tôi muốn mua không đủ tiền thì báo lý do, để hiểu vì sao không mua được.
12. Là người chơi, tôi muốn tạm dừng bằng Esc/P và mọi timer dừng theo, để không bị phạt khi có việc.
13. Là người chơi, tôi muốn xem kết quả ngày (khách phục vụ/bỏ đi, tiền, boa, uy tín), để biết hôm nay làm ăn thế nào.
14. Là người chơi, tôi muốn tổng kết sau Ngày 5, để biết mình chơi ra sao.
15. Là người chấm, tôi muốn `--mode day --days 1..5` chạy headless và ra JSONL tất định, để chấm tự động.
16. Là người chấm, tôi muốn fixture dựng được ngày có tiền/cấp nâng cấp/kho mang về, để test biên.
17. Là người chấm, tôi muốn một Ngày headless chạy ≤ 20 s và ≥ 30 FPS khi chơi, để không bị loại vì hiệu năng.
18. Là người chơi, tôi muốn mở rộng Vợt hút cá, để bắt nhiều đàn một lần.

## Implementation Decisions

- **Contract v1.1 là nguồn số duy nhất.** Mọi số mới (8 đàn, 1.5 m/s, 3.0 m/s chase, 90 tick bất tử…) nằm trong manifest; luật không hard-code.
- **Vòng đời pha** do runner điều khiển, không để `GatherSim` tự chuyển: `day_start → day_plan → phase_start(gather) → gather_end → phase_start(quan) → quan_end → phase_start(shop) → shop_end`, chuyển pha **cùng tick**, gameplay pha mới từ bước sau.
- **`sim_tick`/`phase_tick` không reset giữa các pha trong `day`**; `phase_tick` reset 0 ở mỗi pha. Pause đóng băng cả hai.
- **Day bàn giao trong bộ nhớ** — không ghi file kho giữa các pha. `--inventory-out` chỉ dùng cho `gather` độc lập.
- **Cá**: đổi hướng ở `phase_tick` bội số `fish_turn_ticks` **trước** khi di chuyển; sinh sau bước bơi tại `360·k`; cá mới tham gia từ bước sau.
- **Quái**: cập nhật trước `interact`; tối đa một hit mỗi bước, gần nhất, hòa theo id; recoil bắt đầu từ bước sau.
- **Quán trong `day`** lọc menu theo `day_plan.dishes` rồi mới lọc nguyên liệu khả dụng; quán độc lập dùng cả 6 món.
- **Shop**: xử lý `buy` trước cạnh `shop_done`; nâng cấp đã mua áp dụng từ Ngày kế (`active_upgrades`).
- **Pause**: xét cạnh `pause` đầu tiên; khi paused chỉ `tick` ngoài tăng; cạnh kế tiếp phát `resumed` và chạy gameplay ngay bước đó.
- **Giữ tương thích**: mọi trường snapshot của v1.0 giữ nguyên tên; chỉ thêm.
- **Mở rộng chọn 1 mục** (nhóm 5): **Vợt hút cá (net)** — dùng lại `catch`, khai mã `net` trong `extensions` ở manifest.

## Testing Decisions

- Hộp đen qua `headless_cmd`, đọc JSONL; không import module nội bộ.
- Ba lớp test: (a) đơn vị luật từng khối, (b) tích hợp `gather --inventory-out → quan --inventory`, (c) `day --days 1..3` + regression P1.
- Tất định: cùng seed/inputs → cùng byte, kể cả `day`.
- Biên phải có: ngạt + hit cùng tick, ngất do quái mở quán với kho rỗng, pause giữa lúc nấu, Shop đóng ở tick cuối, mua khi đủ đúng giá, mua khi đã cấp tối đa, cá sinh khi hết điểm hợp lệ.
- Dung sai như v1.0 (toạ độ ±0.1 m, uy tín ±0.01, thời gian ±2 tick); tiền/điểm/id/số lượng/lý do/thứ tự so chính xác.
- P1 test phải sửa **kèm lý do ghi trong commit**: `fish_initial` 6 → 8 (`contract.py`), `--mode day` không còn bị từ chối (`test_smoke_p1.py`), thêm 2 kind nguyên liệu (`KINDS_P1`).

## Out of Scope

- Các mở rộng không chọn: Lao (weapon), Rắn Hổ Mây (snake), Cháy món (burn), Chợ Chú Sáu (vendor), Sổ tay/Cá Hô, Settings âm thanh — để backlog.
- Đổi công nghệ; asset ngoài; nhiều người chơi; lưu game.

## Further Notes

- Hiệu năng là yêu cầu chấm: một Ngày ≤ 22.200 tick phải chạy ≤ 20 s headless. Đừng ghi snapshot dày khi test hiệu năng.
- Kế hoạch D4/D5 cần 11–12 ô nếu bắt theo đàn (yield 3/1/2), sát trần giỏ 12 — đây là chủ ý thiết kế, không phải lỗi.
- Phase 1 phải xong và tag trước khi số liệu đổi sang v1.1, nếu không tag `phase-1` sẽ sai hợp đồng.
