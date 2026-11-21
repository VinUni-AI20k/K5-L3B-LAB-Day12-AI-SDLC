# Hợp đồng kho cá thể Phase 3

Đề xuất triển khai Ticket-03 để Khôi review. Bắt đầu từ Test Contract v1.1 ở `5455042`. Khôi bật `contract_version: "1.2"` và thêm `tuning.freshness` ở PR cuối.

```json
{"initial":100,"gather_decay_per_s":0.5,"quan_decay_per_s":0.25,"spoiled_below":30}
```

## Schema và giao diện adapter

File v1.2 có đúng một khóa gốc `items`, là mảng bản ghi `{id,kind,fresh}`. ID duy nhất và khác rỗng. Kind giữ danh mục Phase 2. `fresh` là số hữu hạn trong [0,100]. Nhận cả hàng ươn. [Mẫu v1.1](inventory.sample.json) và [mẫu v1.2](inventory.v1.2.sample.json) có cùng số lượng theo loại. Ở v1.2 file kho đếm, ID trùng, loại lạ hoặc độ tươi sai trả mã 2. Kho rỗng là `{"items":[]}`.

| Giao diện | Trách nhiệm |
|---|---|
| `freshness.parse_items(raw, kinds)` | Diên. Kiểm mảng, trả danh sách bản ghi mới theo thứ tự vào. `fresh` nội bộ là `Fraction` từ giá trị thập phân đã đọc. |
| `freshness.new_item(ids, kind, initial)` | Diên. Dùng `IdAllocator.new("I")` và giá trị `initial` trong tuning. |
| `freshness.age_items(items, decay_per_s, tick_hz, spoiled_below, location)` | Diên. Hao và kẹp mỗi cá thể ở 0. Trả các cặp `("spoiled", data)` xếp theo ID với `item_id`, `kind`, `location`. Dùng chung cho Gather và Quán. |
| `freshness.view_items(items, spoiled_below)` | Diên. Trả bản sao để ghi JSON, giữ thứ tự đầu vào. Giữ đủ chữ số và cùng phía với ngưỡng ươn khi chuyển sang số JSON. Dùng cùng kết quả cho file và snapshot. |
| `read_inventory(path, kinds, *, contract_version="1.0")` và `write_inventory(path, items, *, contract_version="1.0")` | Diên. Giao diện cũ hoạt động khi không truyền version. v1.2 đọc số thập phân không qua làm tròn trước khi kiểm độ tươi và trả mảng cá thể nội bộ. Bên ghi nhận mảng đã chuyển sang số JSON, sắp theo ID và thay file nguyên tử. |

Gather dùng danh sách cá thể theo thứ tự nhặt. `inventory_items()` trong v1.2 trả bản sao kho cá thể nội bộ để `Day` đưa thẳng vào Quán, giữ độ tươi ở thời điểm chuyển ca. Khi ghi file, event hoặc snapshot, chuyển bằng `view_items`. CLI và live chọn schema bằng version khai trong manifest. Các lát dùng sự có mặt của `tuning.freshness` để test nhánh v1.2 trong unit test khi manifest chung còn v1.1.

## Thứ tự và tính giá

- **Gather.** Hao `0.5 / tick_hz` cho hàng có sẵn đầu tick, trước bơi, ngạt, quái và tương tác. Cấp ID theo thứ tự từng cá thể vào giỏ. Hàng mới bắt/hái hao từ tick kế. Hàng ươn vẫn chiếm ô. Rơi hàng theo LIFO, event giữ thứ tự rơi. Khi cập bến/hết giờ, `gather_end.data.inventory.items` khớp file đã xuất. Khi ngất, bàn giao mảng rỗng. Giới hạn tick tới trước `gather_end` giữ nguyên đường dẫn đích.
- **Quán.** Hao `0.25 / tick_hz` ở đầu tick cho kho thô, kể cả phần giữ. Phát toàn bộ `spoiled` theo ID rồi xử lý đơn bị ảnh hưởng theo `order_tick` và ID bàn. Mỗi đơn bị ươn nhả toàn bộ và thử giữ lại một lần. Chọn theo loại, độ tươi giảm dần rồi ID tăng dần. Thiếu nguyên liệu thì chuyển `unfulfillable`; khách tiếp tục chờ đến lúc hết kiên nhẫn hoặc đóng ca.
- **Nấu.** Lấy đúng cá thể đã giữ, rồi chốt `base_price = floor(giá niêm yết × trung bình độ tươi / 100)`. Tính với giá trị nội bộ. Bếp, tay và món chín giữ payload hiện có. Boa dùng giá đã chốt, tiền và uy tín vẫn theo quy tắc từ Phase 2. Dữ liệu `cook_started.items` sắp theo kind rồi ID.
- **Điểm biên.** Fresh bằng 30 còn dùng được. Chỉ phát `spoiled` khi đi từ ≥30 xuống <30. Kiểm ngưỡng và tính giá trước khi định dạng. Giữ riêng precision của `fresh` trong JSONL, bỏ qua phép làm tròn tọa độ áp cho các trường khác. Pause dừng hao, Shop và món chín giữ độ tươi.

## Scenario, ngày và HUD

- `gather.hold`, `quan.stock` và stock của Shop dùng mảng cá thể. `customers[].reserved` là mảng ID. Một ID giữ hàng phải có trong kho, chưa ươn, đúng công thức và chỉ thuộc một đơn. Khi fixture thiếu `reserved`, cấp lại theo `order_tick`, ID bàn và quy tắc chọn tươi nhất.
- Khi chạy `day`, Ngày đầu giữ ID fixture. Ngày sau dựng lại giỏ theo thứ tự mẫu với ID mới, giữ kind/fresh ban đầu. Cùng một allocator chạy xuyên lượt và đánh dấu ID fixture đã dùng trước khi cấp thêm. Bàn giao kho trong cùng tick chuyển pha, ca Quán hao tươi từ bước gameplay kế tiếp.
- HUD Gather đếm giỏ và mục tiêu theo loại. HUD Quán tính kho khả dụng từ cá thể còn tươi và chưa giữ. Cả hai hiển thị độ tươi hoặc nhãn ươn. Phần nhập kho và kiểm món nấu được trong màn giới thiệu ca tối dùng cùng cách đếm.

## Fixture và smoke

Fixture kiểm ngưỡng Gather, chạy đúng một bước:

```json
{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}
```

Kỳ vọng event `spoiled` tại tick 1 với `item_id:"I1"` và `location:"hold"`. Đổi fresh thành 100 và thêm `{"frames":[{"tick":0,"interact":true}]}` ở bến để kiểm file. Quán đọc file với `--ticks 0`. So đúng ID, kind và fresh với file. Fixture âm dùng [mẫu kho đếm](inventory.sample.json), kỳ vọng mã 2 ở manifest v1.2.

Fixture Quán dưới đây dựng ở bếp B1. Gửi cạnh tương tác tại frame 0 để kiểm hao, giữ lại và chốt giá trong cùng tick:

```json
{"quan":{"player":{"pos":[2,8]},"stock":[{"id":"I1","kind":"ca_loc","fresh":30},{"id":"I2","kind":"ca_loc","fresh":50}],"customers":[{"id":"C1","table_id":"T1","dish_id":"ca_loc_nuong_trui","reserved":["I1"]}],"random_customers":false}}
```

Kỳ vọng `spoiled` cho I1 trước `cook_started`, bếp dùng I2, giá chốt 29 nghìn từ độ tươi sau lần hao đầu. Bỏ I2 khỏi fixture thì đơn chuyển `unfulfillable`, I1 vẫn nằm trong kho và bếp giữ trạng thái rảnh. Trong hai PR đầu, dùng fixture để kiểm adapter và lớp sim trực tiếp với tuning v1.2. Kiểm qua CLI v1.2 khi PR cuối bật manifest.
