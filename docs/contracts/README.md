# Hợp đồng tích hợp Phase 1

## Kho từ Lặn & Hái sang Mở Quán

`items` là khóa gốc duy nhất. Giá trị là object ánh xạ bốn ID nguyên liệu `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung` sang số nguyên không âm. Loại vắng mặt có số lượng 0. Gather bỏ các khóa lượng 0, khớp [mẫu kho](inventory.sample.json) và ghi kho rỗng dạng `{"items":{}}`.

Gather bàn giao object này trong `gather_end.data.inventory` khi về bến, hết giờ hoặc ngất. Ngất cho kho rỗng. Với `--inventory-out`, runner thay thế file nguyên tử đúng một lần khi ca kết thúc. Khi chạm giới hạn tick trước khi kết thúc, runner giữ nguyên đường dẫn đích. Quan đọc bằng `--inventory` và snapshot tick 0 phản ánh đúng kho bàn giao. File sai schema, loại lạ, số lượng sai hoặc fixture khai cả kho scenario và file đều trả mã 2.

## Mô phỏng và giao diện trình duyệt

`Session` dùng chung cho headless và live. UI đọc `GET /state` với snapshot, `meta`, `events` và trạng thái kết thúc. Gather hiển thị timer, oxy, Máu và giỏ. Quan đọc kho vật lý, trừ phần `customers[].reserved` để hiện kho khả dụng, và đọc khách, bếp, món trên tay, tiền, uy tín. UI gửi `POST /input` với `move`, `interact` và `catch`. Sim quyết định cạnh lên, diễn biến và thứ tự tick. `POST /restart` dựng lại ca.

| Bên phát | Sự kiện Phase 1 | Bên dùng |
|---|---|---|
| Gather | `dive`, `surface`, `oxygen_empty`, `choke`, `faint`, `gather`, `node_regrown`, `hold_full`, `fish_caught`, `gather_end` | Runner ghi JSONL, UI hiển thị phản hồi, kiểm thử đọc payload theo PRD-0 mục E. |
| Quan | `customer_arrived`, `no_dish`, `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, `customer_left`, `quan_end` | Runner ghi JSONL, UI hiển thị phản hồi, kiểm thử đọc payload theo PRD-0 mục E. |

## Smoke bàn giao

Với seed 42, cho gather giữ `["ca_loc","bong_sung","bong_sung"]`, nhấn tương tác ở bến ngay frame 0, chạy một tick và lấy file kho. Dựng quan với chính file đó và `--ticks 0`. Kho snapshot phải là `{"bong_sung":2,"ca_loc":1}`. Bộ test starter có ca `test_inv_01_gather_writes_inventory_quan_reads_it`.
