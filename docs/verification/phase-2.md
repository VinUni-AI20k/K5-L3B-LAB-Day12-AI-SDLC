# Kiểm chứng Phase 2 — P2-05

## Phạm vi đã triển khai

UI vòng ngày có hai chế độ preview. `--real-scenes` chạy Gather và Quán bằng mô phỏng thật của Contract 1.0 đã tích hợp trên `main` (`14cb40f`), chuyển giỏ vào kho và lấy kết quả từ sim. Các màn chuyển ca được điều phối bởi adapter localhost; Pause giữ tick của sim. Shop, thực đơn theo ngày và các cơ chế mới của v1.1 vẫn chờ backend P2-03. Fixture riêng vẫn dùng để kiểm UI của các màn chưa có dữ liệu thật.

## Chạy thử

```powershell
$env:PYTHONPATH = 'tests;.'
python -m unittest discover -s tests -v
python docs/proof/phase-2/day_fixture.py --real-scenes --days 5 --port 8782
```

Mở [localhost:8782](http://127.0.0.1:8782/). Dùng **WASD/mũi tên** để di chuyển, **Space** để bắt cá, **E** để hái/cập bến/nấu/phục vụ, và **P/Esc** để tạm dừng. E chỉ tác động khi thực thể ở đúng tầm của sim; Quán đóng khi hết giờ. Shop hiện chưa cho mua.

Để xem fixture của Shop và hai bếp/bốn bàn, bỏ `--real-scenes` và dùng một cổng khác nếu cả hai mode chạy đồng thời. Fixture dùng **E** để chuyển ca theo kịch bản; P/Esc dùng để thử pause. Chạy với `--days 1` để đi thẳng đến tổng kết sau một ngày; thêm `--faint` để xem ca tối với kho rỗng. Mua bình oxy cấp 1 để kiểm hiệu lực ở ngày kế tiếp, hoặc thử mua Máu cấp 2 để xem lỗi. Giá và kết quả chỉ là dữ liệu kiểm giao diện. Fixture có chuyển màn khi hết đồng hồ Shop theo kịch bản; không mô phỏng luật đánh bắt, phục vụ hay nâng cấp.

## Giao diện web đề xuất cho P2-03

| Nguồn | Dữ liệu UI đang nhận |
|---|---|
| `GET /state` của Day | `mode: "day"`, `screen` nhận `menu`, `day_intro`, `gather`, `evening_intro`, `quan`, `day_result`, `shop`, hoặc `summary`, `day`, `days`, `tick_hz`, `paused`, `can_pause`, `events`. Khi chơi, `snapshot` chứa schema scene hiện có gồm `meta`, `tick`, thực thể; Gather có `monsters[]` với `id`, `pos`, `state` và `heading_deg` tùy chọn. |
| Dữ liệu từng màn | `menu[]` có `dish_id`, `servings`, `label` (nếu có); `needed` và `inventory` là map theo nguyên liệu; `cookable[]` là danh sách món. Khi ngất, `gather_reason: "fainted"`. `result` gồm `served`, `left`, `earned`, `tips`, `money`, `reputation`; Summary dùng tổng hợp có thẩm quyền của backend. |
| Shop | `shop` gồm `money`, `time_left_ticks`, `upgrades: {oxygen,hp}`, `options[]` với `id,label,level,price,enabled` (`enabled` tùy chọn) và `message` phản hồi mua. Trình duyệt gửi lại ID từ server. |
| Điều khiển | `POST /input` giữ `{move,interact,catch}`. `POST /action` nhận `{action,upgrade_id?}`, trong đó `action` là `start`, `continue`, `pause`, `resume`, `menu`, `buy`, hoặc `shop_done`; trả HTTP phù hợp và JSON `{ok}`. Sau lệnh, UI đọc lại snapshot trước khi đổi màn. |

Đây là lớp trình bày tạm để tích hợp, không phải phần mở rộng của JSONL headless. P2-03 cần chốt ánh xạ sang Ticket-02 trước khi nối `chonoi.live --mode day --days N`. Đồng thời chốt với P2-02 ánh xạ event trúng đòn (`crocodile_hit` trong fixture) và tên trường cá sấu. Việc pause/đóng Shop/chuyển ca/mua thuộc backend.

## Kết quả

| Kiểm tra | Kết quả |
|---|---|
| Hồi quy Phase 1 | 107 test Python qua, gồm 2 test adapter Day dùng mô phỏng thật. Headless thật cho Gather ngất, xuất `items: {}` và Quán nạp `stock: {}`. Chrome kiểm chuyển động bằng bàn phím ở cả hai mode `chonoi.live` thật. |
| Vòng 1 và 5 ngày | Chrome qua các màn từ Menu đến Summary trên fixture. Kiểm nhả phím khi blur, gửi lại input trung tính sau lỗi kết nối, P/Esc, giữ tick khi pause, phản hồi mua thất bại và nâng cấp có hiệu lực từ ngày sau. Fixture chuyển sang Summary khi Shop hết thời gian. |
| Cảnh và HUD | Fixture hiển thị 12 đàn cá, sáu loại nguyên liệu, M1/M2, hai bếp, bốn bàn, sáu món và kho rỗng khi ngất. Chrome kiểm bề ngang tại 390 px. |
| Hiệu năng | Đo số lần vẽ hoàn tất trên Chrome headless ở 1280×720, 15 giây mỗi cảnh. Gather và Quán đều đạt 60,1 FPS, vượt mốc 30 FPS. Số liệu trong [log](../proof/phase-2/browser-check.txt). |
| Adapter với sim v1.0 | Test kiểm cá lóc vào kho Quán, nấu–lấy món–phục vụ–thanh toán 72 nghìn, Pause và kho rỗng khi ngất. Chrome kiểm WASD, E hái thật, chốt giỏ tại bến và kho xuất hiện trong Quán. |
| Tích hợp v1.1 thật | Chưa chạy được `day --days 1/5` qua headless hoặc live. Khi backend có sẵn, chạy lại toàn bộ ca và xác nhận timer tự đóng Shop, thống kê cuối ngày, các giao dịch và pause. |

Ảnh từ fixture: [Gather](../proof/phase-2/gather-1280.png) · [Quán](../proof/phase-2/quan-1280.png) · [Shop](../proof/phase-2/shop-1280.png) · [Gather 390 px](../proof/phase-2/gather-390.png).

## Bộ ảnh món ăn và cá sấu

Fixture Day hiển thị đủ sáu ảnh món trong thực đơn, món có thể nấu, đơn hàng và bếp. Sprite Bà Út và cá sấu lấy từ Ảnh lab. UI vẽ cá sấu theo vị trí và trạng thái trong `snapshot.monsters`. Mô phỏng v1.0 vẫn cung cấp ba món theo contract.

```powershell
python docs/proof/phase-2/day_fixture.py --days 3 --port 8876
```

Mở [bản thử](http://127.0.0.1:8876/), chọn **Chơi** để xem thực đơn và **Ra bến** để gặp cá sấu. Nhấn **E** để chuyển sang màn chuẩn bị mở quán trong fixture.

- **108/108 test Python đạt**, gồm kiểm tra HTTP cho tám ảnh WebP. Copy lint trả 0 lỗi và 0 cảnh báo.
- Chrome kiểm thực đơn, Gather và Quán ở 1440, 1024, 820, 768, 390 và 320 px. Kiểm đủ sáu ảnh thực đơn, bốn ảnh đơn hàng và hai ảnh bếp, sprite Bà Út và cá sấu trên Canvas, chuyển ca và Pause. Nút **Ra bến** hiện ngay khi mở thực đơn ở cả sáu kích thước. Không ghi nhận tràn ngang, lỗi JavaScript hoặc HTTP.
- Design Taste Frontend báo `GATE: FAIL 20 (round 2 of 3)` cho các quy tắc trang giới thiệu như hero, section toàn màn hình và lưới `.wrap`. Kết quả màn chơi dựa trên phép kiểm Chrome trực tiếp ở trên.
- Ba món mới và hành vi cá sấu chạy theo dữ liệu fixture. Tích hợp gameplay v1.1 thật chờ backend P2.

## Giao diện màn chơi từ bản redesign

Gather và Quán dùng lại tranh nền, khung màn chơi và khay Bà Út của bản redesign. Hai bếp và bốn bàn ở fixture được đặt theo tranh quán. Tọa độ trong các ca chơi thật vẫn lấy từ snapshot.

Sau khi đổi giao diện, 108/108 test Python đạt. Chrome kiểm ảnh nền và Canvas đúng DPR, khay nằm cạnh cảnh trên desktop và xuống dưới ở màn hình hẹp. Đã kiểm thực đơn, cá sấu, hai bếp, bốn đơn, chuyển ca và Pause ở 1440, 1024, 820, 768, 390 và 320 px. Bản chạy mô phỏng thật qua kiểm di chuyển, hái, cập bến, chuyển kho sang Quán và Pause.
