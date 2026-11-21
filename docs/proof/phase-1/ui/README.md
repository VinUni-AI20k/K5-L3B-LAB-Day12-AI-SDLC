# Bằng chứng HUD (client/ui, Nhài)

Chụp bằng Chrome headless, cửa sổ 1400×800, client `chonoi/web/index.html` ở commit `640d03e` (nhánh `p1/ui-nhai`, đã gộp lát 3 và 4 từ `main`).

## Buổi tối: số thật từ sim của lát 3 và 4
Cách tạo: chạy `runner.Session("quan", …, seed 3)` với kho `{ca_loc:2, ca_linh:3, bong_dien_dien:1, bong_sung:4}`. Một bot đơn giản lái Út Sen đi qua các bước nấu → bưng → dọn. Snapshot thật ở từng mốc được đưa vào client để vẽ.

Chuỗi sự kiện thật:
- t120 `customer_arrived`
- t214 `cook_started`
- t574 `dish_ready`
- t575 `dish_picked`
- t700 `served` (boa 12k)
- t1300 `paid` (72k)

| Ảnh | Tick | HUD cho thấy |
|---|---|---|
| [quan-1-khach-den.png](quan-1-khach-den.png) | 120 | Khách T1 gọi cá lóc nướng trui; kho khả dụng `cá lóc 1 (giữ 1)`; kiên nhẫn 60s; Má Tư mở đầu |
| [quan-2-dang-nau.png](quan-2-dang-nau.png) | 375 | Bếp B1 đang nấu, có vòng tiến độ và khói; đơn ở trạng thái "đang làm"; gợi ý "còn 4s" |
| [quan-3-bung-mon.png](quan-3-bung-mon.png) | 575 | Trên tay `Cá lóc nướng trui (đơn C1)`; thông báo "đã chín" và "Bưng…" |
| [quan-4-tra-tien.png](quan-4-tra-tien.png) | 1300 | Tiền 72k, uy tín 3.2, điểm 372; thông báo "Thu 72k (gồm boa 12k)" |

Ảnh 3 cho thấy lỗi gợi ý "B1: chưa có đơn để nấu" lúc đang bưng món. Lỗi đã sửa ở `640d03e`: gợi ý mới là "Đang bưng …, ra bàn T1 dọn cho khách".

## Buổi sáng: số thật từ sim của lát 1 và 2
Ảnh chụp sau khi Khang gộp `main` (lát 1 của Hưng, lát 2 của Phát) vào nhánh (`a18541f`). Cách tạo: chạy `runner.Session("gather", …, seed 5)` với preset mặc định. Một bot lái Út Sen lặn tới F1 và F2 bắt cá, ở dưới nước tới lúc hết oxy, rồi nổi lên hái N1 và về bến. Trước đó, ảnh buổi sáng dùng snapshot giả; nay đã thay bằng các ảnh dưới đây.

Chuỗi sự kiện thật:
- t26 `dive`
- t204 `fish_caught` (cá linh ×3)
- t441 `fish_caught` (cá lóc)
- t1825 `oxygen_empty`
- t1884 `choke`
- t1908 `surface`
- t1917 `gather` (điên điển)
- t2067 `gather_end` (docked)

| Ảnh | Tick | HUD cho thấy |
|---|---|---|
| [gather-1-bat-ca.png](gather-1-bat-ca.png) | 205 | Vừa bắt bầy cá linh: giỏ 3/12, đàn F1 biến mất, hồi chiêu bắt, thông báo + Má Tư |
| [gather-2-sap-het-oxy.png](gather-2-sap-het-oxy.png) | 1466 | Oxy 6/30 s chuyển đỏ, viền đỏ nhấp nháy, gợi ý "Sắp hết oxy, nổi lên thở!" |
| [gather-3-cap-ben.png](gather-3-cap-ben.png) | 2067 | Máu ♥♥♡ sau khi ngạt; màn kết thúc "cập bến" liệt kê đồ mang về quán; Má Tư khen |

Ảnh 3 cho thấy gợi ý "E: cập bến" vẫn hiện sau khi buổi đã kết thúc. Lỗi đã sửa: hết buổi thì ẩn gợi ý phím.
