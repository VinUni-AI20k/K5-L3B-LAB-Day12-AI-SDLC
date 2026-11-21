# Giao diện tích hợp Phase 1

[PRD-0 và Test Contract v1.0](../../PHASE1.md) là nguồn cho luật, số liệu và định dạng đầu ra. Các chữ ký Python dưới đây là phương án chia việc nội bộ cho starter.

## Dữ liệu trao đổi

- **File kho** dùng schema và mẫu trong [README](../../README.md). Trong Python, `hold` là `list[str]` theo thứ tự nhặt, phần tử cuối mới nhất. `stock` là `dict[str, int]` đếm tồn vật lý, gồm phần khách đã giữ. `reserved` của mỗi khách là `dict[str, int]` đếm phần giữ riêng. Khả dụng của một nguyên liệu bằng tồn vật lý trừ tổng phần giữ của tất cả khách. Khi bắt đầu nấu, trừ tồn và xóa phần giữ của đơn trong cùng bước.
- **Gather** dùng `player.pos = [x,d]`, `nodes[] = {id,kind,pos,regrow_ticks}`, `fish[] = {id,kind,pos,heading_deg}`. Snapshot thêm `nodes[].ready`, `hold_count`, `hold_capacity` và các trường người chơi ở mục E của PRD. Giữ các thuộc tính hiện có của `GatherSim` khi truyền `sim` vào module tài nguyên.
- **Quán** dùng `player = {pos,vel}` với tọa độ `[x,z]`, `hand = null` hoặc `{order_id,dish_id,base_price}`. Bếp có `{id,pos,state,dish,cook_ticks_left,ready_ticks}`, trong đó `dish` cùng dạng với `hand`. Bàn snapshot có `{id,pos,customer_id}` với `null` khi trống. Khách có `{id,table_id,dish_id,order_tick,state,patience_ticks_left,eat_ticks_left,order_status,reserved,base_price,tip}` theo mục D. `order_id` trong món và sự kiện bằng `customers[].id`. `state` là `waiting` hoặc `eating`, còn `order_status` là `reserved`, `assigned`, `unfulfillable` hoặc `served`. Fixture dùng đúng giá trị mặc định và kiểm tra liên kết theo mục D.
- **Mọi bước** dùng tuning từ contract, thời gian gameplay bằng tick nguyên ở 60 Hz và tiền nguyên theo nghìn đồng. Dùng `sort_by_id` / `id_key`, cấp ID bằng `IdAllocator` và chọn món bằng `Streams.get("customer_order")` từ danh sách ID món đủ nguyên liệu đã sắp thứ tự Unicode. So khoảng cách trên dữ liệu gốc, runner lo định dạng đầu ra và điểm.

## Ranh giới hai cặp

### Gather

Người 1 giữ `GatherSim.step(inp)`, `_at_surface()` và thêm `_try_add_to_hold(kind, amount) -> bool`. Hàm giỏ thêm đủ số lượng hoặc trả `False` và giữ nguyên giỏ. Người 1 giữ `_finish(reason, events)` làm điểm kết thúc chung. Khi ngất, người 1 phát `faint` với `lost` theo LIFO, xóa giỏ rồi gọi `_finish("fainted", events)`.

Người 2 cung cấp ba hàm trong `gather_resources.py`:

| Chữ ký | Trách nhiệm |
|---|---|
| `tick_resources(sim, events)` | Giảm hồi bắt và timer nút, phát `node_regrown` theo ID. |
| `harvest(sim, events)` | Hái nút sẵn sàng gần nhất khi ở mặt nước. Dùng hàm giỏ, phát `gather` hoặc `hold_full`. |
| `catch_fish(sim, events)` | Xét độ sâu, hồi bắt và đàn gần nhất. Dùng hàm giỏ, phát `fish_caught` hoặc `hold_full`. |

Thứ tự trong `GatherSim.step`: giảm giờ → `tick_resources` → di chuyển, oxy và ngất → cạnh `interact` kiểm bến trước, ngoài bến mới gọi `harvest` → cạnh `catch` gọi `catch_fish` → xử lý hết giờ. Giữ đường ghi kho nguyên tử qua `Session.write_inventory_if_done()` và `inventory.py`. Kiểm fixture Gather ở `scenario.py` do người 3 sửa, người 1 cung cấp ca kiểm oxy và người 2 cung cấp ca kiểm tài nguyên.

### Quán

Người 3 cung cấp các hàm trong `quan_customers.py`:

| Chữ ký | Trách nhiệm |
|---|---|
| `load_customers(sim, scenario) -> list[dict]` | Dựng khách, mặc định, cấp giữ chỗ còn thiếu và kiểm mâu thuẫn với kho, bếp, bàn, tay. Bếp, bàn, kho và tay phải được dựng trước khi gọi. Ném `BadInput` lúc dựng sim cho fixture mâu thuẫn. Chủ `QuanSim` gán danh sách trả về và reserve ID fixture. |
| `tick_customers(sim)` | Giảm kiên nhẫn khách chờ và timer khách ăn. |
| `oldest_reserved(sim) -> dict \| None` | Trả đối tượng khách còn giữ chỗ cũ nhất theo `order_tick`, rồi ID bàn. Người 4 tiêu nguyên liệu và chuyển sang `assigned`. |
| `leave_waiting(sim, customer, reason, events)` | Nhả phần giữ thô, xóa khách đang chờ, cập nhật uy tín khi `reason == "patience"` và phát `customer_left`. Người 4 dọn món đã tiêu nguyên liệu trên bếp/tay của đơn này trước khi gọi. |
| `spawn_customer(sim, phase_tick, events)` | Xét lịch, bàn trống, kho khả dụng và `random_customers`. Tạo khách và giữ nguyên liệu, hoặc phát `no_dish` khi có bàn mà thiếu món. |

Người 4 giữ `QuanSim.step(inp)`, lưu `sim.random_customers` từ scenario (mặc định `True`) và giữ bộ đếm `phase_tick` nội bộ bắt đầu từ 0, tăng một lần mỗi bước, độc lập với giờ còn lại của fixture. Thứ tự là giảm giờ và timer → chuyển bếp chín → di chuyển và xét tối đa một tương tác → xử lý khách theo ID bàn → đóng ca hoặc gọi `spawn_customer`. Phục vụ diễn ra trước khi xét kiên nhẫn về 0. Người 4 xử lý khách ăn xong và thanh toán khi đóng ca, rồi phát `quan_end`. Người 4 xuất `player.vel` và giữ `snapshot.stock` là tồn vật lý.

## Sự kiện và giao diện chơi

Hàm mô phỏng thêm cặp `(name, data)` vào `events`. `Session` gắn tick và phase. Headless ghi event trước snapshot cùng tick, rồi dòng `end` cuối. Payload đầy đủ theo [mục E](../../PHASE1.md#e-output-jsonl).

| Phát từ | Tên sự kiện |
|---|---|
| Người 1 | `dive`, `surface`, `oxygen_empty`, `choke`, `faint`, `gather_end` |
| Người 2 | `node_regrown`, `gather`, `hold_full`, `fish_caught` |
| Người 3 | `customer_arrived`, `no_dish`, `customer_left` |
| Người 4 | `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, `quan_end` |

Client đọc `GET /state` từ `chonoi.live`, gồm snapshot và `meta`, `events`, `finished`, `reason`, `error`. Gửi trạng thái phím qua `POST /input` với `{move:[a,b],interact:boolean,catch:boolean}` và chơi lại qua `POST /restart`. Sim xử lý cạnh lên qua `inp.pressed(...)`. HUD Gather đọc giờ, oxy, máu và giỏ. HUD Quán đọc món gọi, kiên nhẫn, bếp, tay, tiền, uy tín và tính kho khả dụng từ `stock` và `customers[].reserved` để hiển thị. Các event gần nhất phục vụ phản hồi chơi. UI dùng cùng sim với headless.

## Kiểm chứng bàn giao

Chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` và lưu log thật trên commit bàn giao. Test `test_inv_01_gather_writes_inventory_quan_reads_it` đã có sẵn. Có thể lấy lệnh sau để lưu thêm kho và cả hai JSONL làm bằng chứng:

```bash
proof=docs/proof/phase-1/integration
mkdir -p "$proof"
printf '%s\n' '{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}' > "$proof/dock.json"
printf '%s\n' '{"frames":[{"tick":0,"interact":true}]}' > "$proof/dock-inputs.json"
python3 -m chonoi.headless --mode gather --seed 42 --scenario "$proof/dock.json" --inputs "$proof/dock-inputs.json" --ticks 1 --out "$proof/gather.jsonl" --inventory-out "$proof/catch.json"
python3 -m chonoi.headless --mode quan --seed 42 --inventory "$proof/catch.json" --ticks 0 --out "$proof/quan.jsonl"
```

Đối chiếu `gather_end.inventory` với `catch.json` và kiểm snapshot tick 0 của Quán có `stock: {"bong_sung":2,"ca_loc":1}`. Chạy thêm cùng đầu vào hai lần để so byte, thử ca chưa kết thúc để xác nhận file kho cũ được giữ và chơi thử cả hai HUD. Điền cách kiểm, bằng chứng và đạt/chưa đạt trong [ma trận Phase 1](../verification/phase-1.md).
