# Hợp đồng tích hợp Phase 1

Trưởng nhóm giữ hợp đồng, xử lý điểm chưa rõ và điều phối bàn giao. TV1–TV5 là các vai trong [bảng phân công](../phan-cong.md). Nhóm dùng starter Python, preset trong game.contract.json và Test Contract v1.0. Khi kickoff, trưởng nhóm điền danh sách thật vào TEAM.md và đặt team_size bằng 5. Quy tắc chi tiết và tên trường lấy theo [PRD-0, mục A–G](../../PHASE-1.md).

## 1. Kho bàn giao từ TV2 cho TV3, TV4 và TV5

Dùng ngay [file kho mẫu](inventory.sample.json) để làm quán và HUD độc lập.

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

- Gốc có đúng khóa items. Mỗi giá trị là số nguyên không âm. Bốn khóa nguyên liệu hợp lệ là ca_loc, ca_linh, bong_sung và bong_dien_dien. Đọc khóa vắng như 0, bỏ khóa bằng 0 khi ghi. Kho rỗng là `{"items":{}}`.
- TV2 tái sử dụng runner để ghi đúng một lần khi có gather_end. File phải khớp data.inventory của event. docked/time giữ phần giỏ cuối bước, fainted ghi kho rỗng. tick_limit đến trước khi kết thúc thì giữ nguyên file đích nếu đã có. Ghi file tạm cùng thư mục rồi thay thế nguyên tử.
- Quán nhận kho qua --inventory hoặc scenario.quan.stock. Khai cả hai hoặc sai schema thì thoát mã 2 trước khi ghi output. Thiếu cả hai thì bắt đầu với kho rỗng. Trần giỏ chỉ áp dụng cho gather.

## 2. Giao diện mô phỏng và HUD

TV1 sở hữu GatherSim.step, TV4 sở hữu QuanSim.step. TV5 dùng GET /state để đọc snapshot và events, gửi trạng thái phím qua POST /input. Ví dụ payload là `{"move":[0,1],"interact":false,"catch":true}`. Mô phỏng xử lý cạnh lên của nút. Trục thứ hai dương hướng xuống khi lặn và hướng bắc khi đi trong quán.

| HUD | Trường đọc |
|---|---|
| Cả hai ca | time_left_ticks ở 60 tick/s, state, player.pos |
| Sáng | player.oxygen_ticks, player.oxygen_max_ticks, player.hp, player.hp_max, hold, hold_count, hold_capacity |
| Tối | stock, customers[].reserved, dish_id và patience_ticks_left của từng khách, stoves, hand, money, reputation |

Kho khả dụng của từng loại bằng stock vật lý trừ tổng reserved của các đơn. UI tính giá trị hiển thị từ cùng snapshot. Luật đổi trạng thái, tiền và uy tín chạy trong sim dùng chung với headless.

## 3. Ai phát sự kiện và thời điểm bàn giao

Runner ghi event vào JSONL, TV5 dùng log để kiểm chứng và dùng snapshot để vẽ HUD. Các trường dưới đây thuộc data của event. Bước k đọc input tại tick k, phát sự kiện tại k+1 theo thứ tự mục F trước khi ghi snapshot.

| Chủ phần luật | Event và payload |
|---|---|
| TV1 · Sinh tồn | dive/surface(pos), oxygen_empty(oxygen_ticks), choke(hp), faint(cause, lost, hp). lost theo LIFO. |
| TV2 · Thu hoạch | gather(node_id, kind, amount), node_regrown(node_id), fish_caught(fish_id, kind, yield), hold_full(action, node_id hoặc fish_id, required, free). |
| TV1 + TV2 · Kết ca sáng | Dùng chung đường kết thúc gather_end(reason, inventory). TV1 gọi khi ngất, TV2 dùng khi cập bến hoặc hết giờ. |
| TV3 · Khách | customer_arrived(order_id, table_id, dish_id), no_dish({}), customer_left(order_id, table_id, reason, reputation). |
| TV4 · Bếp và thu tiền | cook_started(stove_id, order_id, dish_id, items, base_price), dish_ready/dish_picked(stove_id, order_id, dish_id), served(order_id, table_id, dish_id, patience_ticks_left, base_price, tip), paid(order_id, table_id, base_price, tip, amount, reason), quan_end(reason, money, earned, shift_earned, reputation). |

**TV1 ↔ TV2.** hold lưu theo thứ tự nhặt, món mới nhất ở cuối. TV1 điều phối timer → di chuyển và oxy → interact (bến trước hái) → catch → hết giờ. Ngất hoặc cập bến kết thúc bước ngay. TV2 viết phần thu hoạch độc lập bằng fixture đặt sẵn nhân vật và giỏ.

**TV3 ↔ TV4.** TV3 giữ chỗ khi khách gọi món. TV4 trừ stock đúng một lần khi bắt đầu nấu, xóa reserved, chuyển đơn sang assigned. Món trên bếp/tay dùng cùng order_id với id khách. Khi khách rời, TV3 nhả phần giữ và phối hợp dọn món của đơn ở bếp/tay. Nguyên liệu đã nấu không hoàn lại. TV4 xét tương tác trước khi xử lý khách hết kiên nhẫn, rồi xử lý thanh toán/đóng ca trước lượt sinh khách mới.

## 4. Trưởng nhóm nghiệm thu

1. Trước phút 25, TV2 và TV5 chạy smoke hai tiến trình ở mục G. Cập bến với giỏ gồm một cá lóc và hai bông súng. So ba giá trị gồm gather_end.data.inventory.items, items trong file thật và stock tại snapshot tick 0 của quán.
2. Phút 45–55, TV5 chạy lại trên main, kiểm tra cùng seed và input cho JSONL/kho giống từng byte, rồi chơi thử HUD hai ca. Mỗi chủ phần luật gửi test biên và kết quả thực tế vào [ma trận kiểm chứng](../verification/phase-1.md).
3. Trưởng nhóm chốt cùng TV5 commit bàn giao, ghi phần đạt/chưa đạt và đẩy tag phase-1 chậm nhất phút 60. Nếu phát hiện điểm mơ hồ trong PRD, trưởng nhóm hỏi trợ giảng và ghi quyết định vào [nhật ký làm rõ](../clarify.md); báo trực tiếp các thành viên dùng trường hoặc hành vi liên quan.
