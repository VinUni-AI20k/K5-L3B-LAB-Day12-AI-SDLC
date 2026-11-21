# TEAM — Spec triển khai Chợ Nổi

**Nhóm Ba Khi · 4 người · 4 module · mỗi người điều phối 1 agent.** Điền tên và GitHub handle thật vào bốn dòng dưới đây trước khi mở PR. `team_size` trong [game.contract.json](game.contract.json) đã là 4.

## Phân công

| **Thành viên** | **GitHub handle** | **Module chính** | **Vai quy trình** | **Dự phòng cho** |
|---|---|---|---|---|
| … | … | `sim/gather` | PO · hỏi giảng viên, ghi quyết định | `sim/quan` |
| … | … | `sim/quan` | Integrator · điều phối file chung, tích hợp, gắn tag | `sim/gather` |
| … | … | `client/ui` | Scrum/Release · giữ nhịp, chuẩn bị demo và release | `qa` |
| … | … | `qa` | QA lead · kiểm thử hộp đen, tổng hợp bằng chứng | `client/ui` |

## Phase 1

Trong 60 phút, làm hai mode chơi độc lập và nối chúng bằng file kho. `gather` là buổi sáng lặn bắt cá, hái rau và mang giỏ về bến. `quan` là buổi tối nấu và phục vụ với một bếp `B1`, một bàn `T1` và ba món. Dùng starter Python và preset hiện có. Ưu tiên lõi và HUD tối thiểu. Phần mở rộng là tùy chọn với nhóm 4 người. [PRD-0 và Test Contract v1.0](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg#phase-1)

### `sim/gather` · Lát 1 và 2 của PRD

Sửa [chonoi/sim/gather.py](chonoi/sim/gather.py). Giữ bơi, gia tốc và chặn biên của starter. Mỗi tick xử lý timer và nút mọc lại → bơi và oxy → E → Space → hết giờ.

1. **Bơi, oxy, Máu và giỏ.** Tính oxy theo độ sâu cuối bước, bắt đầu đếm ngạt ngay ở tick oxy chạm 0. Nổi lên đúng bước ngạt thì hồi oxy và xóa bộ đếm. Ngất làm rơi giỏ theo LIFO, phát `faint` rồi `gather_end` với kho rỗng.
2. **Hái, bắt cá và bàn giao kho.** Nút về 0 có thể hái ngay. E xét bến trước rồi mới xét hái ở mặt nước. Space bắt đàn gần nhất khi đang lặn và hết hồi chiêu. Khoảng cách hòa xử lý theo ID. Bắt đủ cả đàn hoặc phát `hold_full` và giữ nguyên đàn cùng hồi chiêu. Lượt hợp lệ ở bước cuối vẫn vào kho. Cập bến và hết giờ chốt giỏ qua giao diện runner hiện có.

**Bàn giao cho QA và Quán.** Fixture ngạt ở tick biên, giỏ đầy, hái hoặc bắt hợp lệ ở bước cuối và cập bến đúng mép. Trước phút 25, xuất một file kho thật và đối chiếu với `gather_end.data.inventory`.

### `sim/quan` · Lát 3 và 4 của PRD

Sửa [chonoi/sim/quan.py](chonoi/sim/quan.py). Bắt đầu bằng [kho mẫu](docs/contracts/inventory.sample.json) hoặc fixture `quan.stock`. Mỗi tick xử lý timer và bếp chín → di chuyển và E → thanh toán, khách rời hoặc đóng ca → khách mới nếu còn giờ. Đọc công thức, giá và timer từ `tuning.menu` và `tuning.quan`.

1. **Khách, giữ chỗ và kiên nhẫn.** Dựng khách fixture và phần giữ nguyên liệu theo mục D. Tính kho khả dụng từ tồn vật lý trừ phần giữ. Nếu còn giờ, xét khách cuối bước theo lịch `phase_tick`. Khách chọn đều theo seed trong các món đủ nguyên liệu và giữ đúng công thức ngay. Bàn bận bỏ lượt. Bàn trống mà thiếu món phát `no_dish`. Khách bỏ đi do hết kiên nhẫn làm giảm uy tín và nhả phần giữ chưa dùng.
2. **Bếp, phục vụ và tiền.** Mỗi cạnh E chọn tối đa một đối tượng theo khoảng cách, ưu tiên bếp rồi ID khi hòa. Bếp idle nhận đơn `reserved` cũ nhất và trừ nguyên liệu đã giữ. Nấu xong, bưng khi tay trống, giao đúng `order_id`. Xét phục vụ trước bỏ đi hoặc đóng ca để chấp nhận đúng tick biên. Chốt boa lúc giao, thu tiền và cộng uy tín khi khách trả. Đóng ca thu tiền của khách đang ăn, dọn khách chờ với lý do `closing`, rồi phát `quan_end`.

**Bàn giao cho QA và UI.** Fixture gọi món → nấu → bưng → phục vụ → trả tiền, thiếu món, hết kiên nhẫn và đóng ca. Phối hợp kiểm dữ liệu fixture mục D, gồm món ở bếp/tay phải khớp đơn và giữ chỗ không vượt tồn. Snapshot trả trạng thái kho, đơn, bếp, bàn và tay theo mục E.

### `client/ui` · Chơi thử, HUD và README

Sửa [chonoi/web/](chonoi/web/) dựa trên snapshot mẫu ngay từ kickoff. Dùng mặt cắt ngang cho sông và góc nhìn trên xuống cho quán. Kiểm WASD/mũi tên, E, Space và R. Khi sim có dữ liệu thật, chơi lại cả hai mode qua `chonoi.live`.

- Gather hiện thời gian, oxy, Máu và giỏ. Quán hiện kho khả dụng, món gọi, kiên nhẫn, trạng thái bếp, món trên tay, tiền và uy tín. `stock` trong snapshot là tồn vật lý. HUD hiển thị phần còn dùng được sau khi trừ `customers[].reserved`.
- Bàn giao demo hai mode và cập nhật [README.md](README.md) với đường chạy từ clone sạch trong tối đa 3 lệnh trên macOS/Linux, điều khiển, cách tính điểm và lệnh test. Ghi nguồn asset vào [CREDITS.md](CREDITS.md) nếu dùng asset ngoài.

### `qa` · Hộp đen và bằng chứng

Dùng [tests/](tests/), [ma trận Phase 1](docs/verification/phase-1.md) và [thư mục bằng chứng](docs/proof/phase-1/). Viết fixture từ lúc kickoff. Giữ smoke test công khai và bổ sung ca biên của hai sim theo mục D–G.

- **Test Contract.** Kiểm tick 0 và tick dừng, event trước snapshot cùng tick, hành động theo cạnh nhấn, JSONL và kho lặp lại giống từng byte. Fixture sai hoặc mâu thuẫn trả mã 2 trước khi ghi đầu ra. Kiểm thứ tự và tick của `faint`, phục vụ đúng deadline và dọn ca đúng lý do.
- **Smoke hai tiến trình.** Với seed 42, dựng giỏ `["ca_loc","bong_sung","bong_sung"]` và nhấn E ở input tick 0. Chạy gather tối đa 1 bước, dùng file nó ghi để chạy quan `--ticks 0`. `stock` ở snapshot đầu phải là `{"bong_sung":2,"ca_loc":1}`. Kiểm thêm giới hạn tick trước `gather_end` giữ nguyên file đích.
- **Bàn giao.** Chạy suite và smoke trên commit chuẩn bị gắn tag ở `main`. Lưu lệnh, SHA, kết quả và đường dẫn bằng chứng theo từng AC. Đánh dấu đạt hoặc chưa đạt sau khi chạy. Cùng Scrum/Release kiểm lại HUD và README theo DoD.

### Mốc bàn giao Phase 1

| **Phút** | **Việc chốt** |
|---|---|
| 0–15 | Điền tên, GitHub handle, kênh nhóm và giờ standup. Đọc mục D–G, thống nhất giao diện bên dưới. Quán dùng kho mẫu, UI dùng snapshot, QA dựng fixture để cả bốn agent bắt đầu ngay. |
| 15–45 | Triển khai song song. Phút 20 rà vướng mắc, phút 25 thử kho thật. Standup giữa phase vào phút 30 theo mặc định. |
| 45–55 | Gộp và chơi thử hai mode trên `main`. QA chạy smoke và cập nhật ma trận. Mỗi người cập nhật nhật ký AI và phản tư. Scrum/Release tổng hợp retro. |
| 55–60 | Integrator đẩy tag `phase-1` trỏ tới commit bàn giao trên `main` chậm nhất `1:00` tính từ đầu phase. |

## Giao diện dùng chung

- **Cấu hình và tất định.** Đọc số liệu từ [game.contract.json](game.contract.json) hoặc fixture hợp lệ. Dùng `Streams` cho ngẫu nhiên, `IdAllocator` để cấp ID và `ids.sort_by_id` để sắp danh sách thực thể. Luật chạy theo tick, độc lập với đồng hồ hệ thống. Tính năng sáng tạo phải tắt ở headless.
- **Sim → runner → headless/live.** Headless và live dùng `runner.Session` với nhịp 60 tick/s. Sim nhận `step(InputState)`, đọc `move`, `pressed("interact")` và `pressed("catch")`, rồi trả danh sách `(name, data)` theo thứ tự xử lý. Input ở tick `k` tạo kết quả ở tick `k+1`. Headless ghi `snapshot()` ở tick 0, rồi event trước snapshot cùng tick, và kết thúc bằng dòng `end`. Giữ nguyên tên trường, payload và thứ tự theo Test Contract.
- **Live ↔ UI.** UI đọc `GET /state` (snapshot + `meta` + `events`), gửi trạng thái phím qua `POST /input` với `move`, `interact`, `catch`, và gọi `POST /restart` để chơi lại. Tọa độ gather là `[x, d]` với `d` tăng xuống dưới. Tọa độ quan là `[x, z]`. Sim quyết định kết quả hành động, UI hiển thị kết quả đó.
- **Gather → kho → quan.** `gather_end` mang `data.reason` và `data.inventory.items`. Runner ghi `--inventory-out` một lần bằng thay thế nguyên tử khi buổi gather kết thúc. File có dạng `{"items":{"bong_sung":2,"ca_loc":1}}`, dùng mã nguyên liệu hợp lệ và số nguyên không âm, bỏ lượng 0. Quan nhận `--inventory` hoặc `quan.stock` trong file scenario. Khi giới hạn tick tới trước `gather_end`, runner giữ nguyên file đích. Dùng [schema và kho mẫu](docs/contracts/README.md) để phát triển độc lập.
- **Sự kiện và file chung.** Hai sim phát event với đúng `name`, `data` và thứ tự ở mục E–F. UI đọc phản hồi qua `/state`, QA đọc JSONL. Món ở bếp/tay dùng `{order_id,dish_id,base_price}`, `order_id` bằng ID khách. Điểm dùng `earned + reputation_multiplier × floor(reputation)`, tiền tính theo nghìn đồng. Integrator điều phối các thay đổi ở `runner`, `scenario`, `inputs`, `inventory`, CLI hoặc live adapter. Báo cả nhóm và ghi lý do trước khi sửa contract, payload, schema kho hoặc khung do giảng viên cấp.

## Thỏa thuận làm việc

- **Kênh chat nhóm** · … (điền khi kickoff). Vướng quá 10 phút thì gửi lệnh tái hiện và nhờ người dự phòng hỗ trợ. PO hỏi Anh Năm trên lab board hoặc giảng viên và ghi quyết định ở [docs/clarify.md](docs/clarify.md). Integrator chốt phương án kỹ thuật sau khi trao đổi với các module liên quan.
- Mỗi người mở nhánh ngắn `codex/<module>-<ticket>` từ `main`. Giao agent đúng ticket, phạm vi file, PRD phase, mục giao diện ở trên và [AGENTS.md](AGENTS.md). Ai cần file chung thì trao đổi với Integrator trước để tránh cùng sửa một file.
- Người phụ trách đọc diff của agent, chạy ca module và suite chung, ghi kết quả trong mô tả commit hoặc `docs/proof/`. Người dự phòng review PR trước khi Integrator gộp. Mỗi người có ít nhất 3 commit có nội dung trong lab. Ghi phần AI tham gia vào [docs/ai-usage-log.md](docs/ai-usage-log.md).
- Mỗi phase, QA cập nhật ma trận AC và kết quả thực tế trong `docs/verification/phase-N.md`. Integrator kiểm bản tích hợp rồi gắn tag từ `main` theo [lịch lab](README.md). Hạng mục chưa đạt ghi vào bằng chứng của phase. Chốt release `v1.0.0` cùng Phase 4.

## Lệnh kiểm tra chung

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
PYTHONPATH=tests:. python3 -m unittest tests.test_smoke_p1.Integration.test_inv_01_gather_writes_inventory_quan_reads_it -v
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out gather.jsonl
python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --inventory docs/contracts/inventory.sample.json --out quan.jsonl
python3 -m chonoi.live --mode gather  # đổi thành quan để thử buổi tối
python3 tools/check_team.py
```

Lệnh suite trên dùng cú pháp Bash. Trên PowerShell, đặt `$env:PYTHONPATH = 'tests;.'` trước khi chạy. Suite hộp đen gọi `python3` theo `headless_cmd`, nên môi trường chạy suite cần tìm được lệnh này trên `PATH`. Lệnh `check_team.py` cần bốn tên và handle thật.
