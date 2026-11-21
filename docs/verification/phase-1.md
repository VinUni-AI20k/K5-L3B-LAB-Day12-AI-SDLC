# Ma trận truy vết Phase 1

Ghi đường dẫn bằng chứng và kết quả sau khi kiểm trên commit bàn giao ở `main`. Dùng Test Contract v1.0 mục E–F để đối chiếu payload và thứ tự event. Các mốc và số lượng dưới đây theo preset trong [kế hoạch Phase 1](../plan/phase-1.md).

| AC | Cách kiểm chứng | Bằng chứng (`docs/proof/phase-1/`) | Kết quả |
|---|---|---|---|
| AC-P1-01 | Đối chiếu khóa bắt buộc, giá trị cố định và dải tuning trong `game.contract.json` với mục A. Kiểm `team_size` bằng 6 và khớp `TEAM.md`. Đối chiếu schema và ví dụ kho với mục G. Nạp ví dụ bằng `quan --inventory ... --ticks 0` và so `stock` tick 0 với `items` trong file. | — | Chưa kiểm |
| AC-P1-02 | Dựng người chơi dưới nước với 1 tick oxy và giữ nguyên vị trí. Kiểm `oxygen_empty` tại tick `t`, Máu giữ nguyên đến hết `t+58` và `choke` tại `t+59`. Chạy riêng ca `d=0.51`, `vel=[0,-4]`, oxy 0, đếm ngạt 59 và `move=[0,-1]` ở bước đầu. Kiểm `surface`, oxy hồi, đếm ngạt về 0 và Máu giữ nguyên. | — | Chưa kiểm |
| AC-P1-03 | Dựng người chơi dưới nước còn 1 Máu, oxy 0, đếm ngạt 59 và có giỏ chứa nhiều loại nguyên liệu. Kiểm chuỗi `choke` → `faint` → `gather_end`, `lost` theo LIFO, snapshot cuối có giỏ rỗng và `end` lý do `fainted`. Đối chiếu file kho `{"items":{}}` với event. | — | Chưa kiểm |
| AC-P1-04 | Nhấn `interact` ở mặt nước, ngoài bến và đúng mép bán kính của một nút ready. Kiểm `gather.data` có `node_id`, `kind`, `amount: 1`, giỏ tăng 1 và `node_regrown` sau 1200 tick. Chạy thêm ca lặn và ca giỏ đầy. Giỏ đầy phát `hold_full` và giữ nút ready. | — | Chưa kiểm |
| AC-P1-05 | Nhấn `catch` dưới nước trong tầm đàn cá. Kiểm `fish_caught.data` có `fish_id`, `kind`, `yield` bằng 3 với cá linh hoặc 1 với cá lóc, và đàn bị xóa khi bắt thành công ở tick `t`. Thử bắt đàn khác ở `t+29` và `t+30` trong hai ca để kiểm hồi chiêu. Chạy thêm ca trên mặt nước và ca thiếu chỗ. Thiếu chỗ phát `hold_full`, giữ đàn và giữ nguyên hồi chiêu. | — | Chưa kiểm |
| AC-P1-06 | Dùng `dock.json` và `dock-inputs.json` theo mục G, seed 42. Chạy `gather` với `--inventory-out`, rồi cho `quan` nạp file và dựng snapshot tick 0. Đối chiếu `items` trong file, `gather_end.inventory.items` và `stock` với 2 `bong_sung` và 1 `ca_loc`. Chạy ca chạm giới hạn tick trước khi kết thúc với hai đích, một đường dẫn chưa có file và một file có sẵn. Kiểm file mới chỉ xuất hiện khi có `gather_end` và file có sẵn giữ nguyên khi `tick_limit`. | — | Chưa kiểm |
| AC-P1-07 | Dùng kho rỗng để bàn luôn trống và kiểm `no_dish` có `data: {}` đúng các tick 120, 1020. Chạy riêng với kho đủ món, kiểm `customer_arrived` tại tick 120 có `order_id`, `table_id`, `dish_id`. So `order_tick` và phần giữ chỗ trong snapshot với tick đến và công thức món. Chạy lại cùng seed và đầu vào, rồi so JSONL từng byte. | — | Chưa kiểm |
| AC-P1-08 | Dựng khách `waiting` giữ nguyên liệu và còn 1 tick kiên nhẫn, tắt khách tự sinh. Để qua một bước khi ca còn giờ. Kiểm `customer_left` có `order_id`, `table_id`, lý do `patience` và uy tín sau khi giảm 0.5. Kiểm danh sách khách và bàn trống, tồn vật lý giữ nguyên để nguyên liệu được dùng lại. | — | Chưa kiểm |
| AC-P1-09 | Chạy vòng nấu cá lóc nướng trui. Kiểm `cook_started` với `items: ["ca_loc"]`, rồi `dish_ready` → `dish_picked` → `served` → `paid`. Kiểm `paid` đúng 600 tick sau `served`. Tính tỷ lệ kiên nhẫn sau bước giảm timer. Kiểm boa 12 nghìn ở đúng ngưỡng 50% và 0 ngay dưới ngưỡng. Đối chiếu tiền, `earned`, uy tín và điểm. | — | Chưa kiểm |
| AC-P1-10 | Chạy các fixture ca còn 1 tick. Với khách còn ít nhất 2 tick ăn, kiểm `paid` lý do `closing`. Với khách đang chờ còn đúng 1 tick kiên nhẫn, kiểm `customer_left` lý do `closing` và uy tín giữ nguyên. Thử giao đúng món ở bước cuối cho khách đó trong ca riêng, kiểm `served` rồi `paid` lý do `closing`. Kiểm bàn được dọn trước `quan_end`. | — | Chưa kiểm |
| AC-P1-11 | Chơi cả hai mode bằng `chonoi.live` và chụp HUD khi có dữ liệu. Kiểm thời gian, oxy, Máu và giỏ ở gather. Ở quán, kiểm kho khả dụng khi khách có giữ chỗ, món gọi và kiên nhẫn tại bàn, trạng thái và tên món trên bếp, món trên tay, tiền và uy tín. | — | Chưa kiểm |
| AC-P1-12 | Làm theo README để chạy game từ clone sạch trong tối đa 3 lệnh trên macOS hoặc Linux. Đối chiếu phím điều khiển, công thức tính điểm và chạy bộ test bằng một lệnh ghi trong README. | — | Chưa kiểm |

## Đánh giá ngắn

- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
