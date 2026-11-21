# Hợp đồng tích hợp (nhóm NgheAn)

Người giữ file này: Võ Hồng Lương (Integrator). Đổi hợp đồng thì báo cả nhóm trong kênh chung và ghi lý do ở cuối file (mục "Lịch sử đổi").
Nguồn sự thật cho số liệu là `game.contract.json`. Luật chỉ đọc số từ đó.

## 1. Schema file kho

File kho do `gather` ghi một lần khi có `gather_end`, `quan` đọc khi mở quán.

```json
{"items": {"ca_loc": 1, "bong_sung": 2}}
```

- Khóa gốc duy nhất là `items`; thêm khóa khác thì bị từ chối (mã thoát 2).
- Khóa trong `items` chỉ được là `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
- Giá trị là số nguyên `>= 0`; mục bằng 0 không ghi ra file.
- Ghi qua file tạm rồi thay thế, khóa sắp theo thứ tự chữ cái, kết thúc bằng một dòng mới.
- Ngất (`gather_end` với `reason: "fainted"`) ghi kho rỗng `{"items": {}}`.
- Mẫu hợp lệ: `docs/contracts/inventory.sample.json`. Code: `chonoi/inventory.py`.

## 2. Giao diện giữa `sim/*` và `client/ui`

UI chỉ ĐỌC trạng thái và GỬI lệnh. UI không sửa trạng thái sim.

**UI đọc** (cùng một dạng với dòng `snapshot` của headless và `GET /state` của `chonoi.live`):

- Chung: `tick`, `mode` (`gather` hoặc `quan`), `state` (`playing` hoặc `finished`), `time_left_ticks`, `money`, `earned`, `reputation`, `score`.
- `gather`: `player` (`pos` `[x, d]`, `vel`, `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `invuln_ticks`, `catch_cd_ticks`, `at_surface`), `hold` (mảng, cuối mảng là món mới nhặt), `hold_count`, `hold_capacity`, `nodes` (`id`, `pos`, `kind`, `ready`, `regrow_ticks`), `fish` (`id`, `pos`, `kind`, `heading_deg`).
- `quan`: `player` (`pos` `[x, z]`), `stock`, `hand`, `stoves` (`id`, `pos`, `state`, `dish`, `cook_ticks_left`, `ready_ticks`), `tables` (`id`, `pos`, `customer_id`), `customers`.
- Trường nào chưa có thì UI bỏ qua, không báo lỗi. Sim thêm trường mới thì không được đổi tên hoặc ý nghĩa trường cũ.

**UI gửi** (qua `chonoi.inputs.InputState`, mỗi tick một lần):

- `move`: vector 2 chiều. `gather` là `[x, d]` (thành phần thứ hai dương là bơi xuống); `quan` là `[x, z]`.
- `interact` (phím E): cập bến, hái nút, thao tác bếp và bàn.
- `catch` (phím Space): bắt cá, chỉ có ở `gather`.

Quy ước thêm: mọi số ngẫu nhiên qua `Streams`; không dùng đồng hồ hệ thống; id sắp bằng `ids.sort_by_id`.

## 3. Danh sách sự kiện

Mỗi sự kiện là một dòng JSONL `{"type":"event","tick":…,"phase":…,"name":…,"data":{…}}`. "Phát" là module sinh sự kiện, "Nghe" là module đọc nó.

| Sự kiện | Chế độ | `data` | Phát | Nghe |
|---|---|---|---|---|
| `dive` | gather | vị trí lúc lặn | `sim/gather` | UI |
| `surface` | gather | vị trí lúc nổi | `sim/gather` | UI |
| `oxygen_empty` | gather | (trống) | `sim/gather` | UI |
| `choke` | gather | `hp` còn lại | `sim/gather` | UI |
| `faint` | gather | (trống) | `sim/gather` | UI, QA |
| `gather` | gather | `node_id`, nguyên liệu nhặt | `sim/gather` | UI, QA |
| `hold_full` | gather | nguồn bị từ chối (nút hoặc cá) | `sim/gather` | UI |
| `fish_caught` | gather | `fish_id`, loại cá | `sim/gather` | UI, QA |
| `node_regrown` | gather | `node_id` | `sim/gather` (khung đã có) | UI |
| `gather_end` | gather | `reason` (`docked`, `fainted`, `time`), `inventory.items` | `sim/gather` (khung đã có) | `sim/quan`, QA |
| `customer_left` | quan | `customer_id` | `sim/quan` | UI, QA |
| `no_dish` | quan | `customer_id` | `sim/quan` | UI, QA |
| `cook_started` | quan | `stove_id`, món | `sim/quan` | UI |
| `dish_ready` | quan | `stove_id`, món | `sim/quan` | UI |
| `dish_picked` | quan | `stove_id`, món | `sim/quan` | UI |
| `served` | quan | `customer_id`, món | `sim/quan` | UI, QA |
| `paid` | quan | `customer_id`, tiền, boa | `sim/quan` | UI, QA |
| `quan_end` | quan | `reason`, `money`, `earned`, `shift_earned`, `reputation` | `sim/quan` (khung đã có) | QA |

Cột `data` là đề xuất ban đầu của Integrator để A, B, C thống nhất; chỉ `node_regrown`, `gather_end` và `quan_end` đã có trong khung. Chưa chốt: tên sự kiện khi khách đến quán (PRD-0 mục E chưa có trong repo, ghi vào `docs/clarify.md` và hỏi PO).

## Lịch sử đổi

- Bản đầu do Integrator viết ở nhánh `p1-01-03-kickoff`, cần A, B, C đọc và đồng ý trước khi viết luật.
