# Changelog

Định dạng theo Keep a Changelog, ghi theo từng phase và Test Contract. Bản mới nhất ở trên.

## [1.0.0] - 2026-11-21 · Phase 4 (Ticket-04, Test Contract v1.3)

> ⏳ Chốt trước khi phát hành: các dòng có dấu ⏳ cập nhật theo kết quả kiểm cuối.

### Thay đổi hợp đồng
- `contract_version: "1.3"`. Gameplay, tuning, kho cá thể và JSONL giữ như v1.2 (vẫn bắt buộc `freshness`).
- Gốc manifest thêm `bench_cmd: "python3 -m chonoi.bench"` và `soak_cmd: "python3 -m chonoi.soak"` (PR #27).

### Thêm mới
- `soak_cmd`: chạy N Ngày trong một tiến trình headless bằng bot tất định, ghi `soak.json` (`days`, `days_completed`, `crashes`, `results`, `duration_s`). `DaySession` chạy quá 5 Ngày, kế hoạch D1-D5 lặp ở Ngày 6-10 (PR #29). Soak 10 Ngày seed 7: `days_completed` 10, `crashes` 0.
- `bench_cmd`: khung đo cảnh lặn 1280×720, làm nóng 3 s, đo `duration` s, ghi `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`. ⏳ Phần vẽ (`chonoi/bench_render.py`).
- HUD: cảnh báo "Thủy quái!" kèm viền tím, "Hết hơi!", cảnh báo khách sắp giận. ⏳ Chế độ tương phản cao.
- Ma trận `docs/verification/phase-4.md`, retro Phase 4, phản tư cá nhân trong `docs/members/`.
- ⏳ Đóng gói: README chạy từ clone sạch trong ≤ 3 lệnh, `LICENSE`, file zip đính kèm Release v1.0.0.

## Phase 3 (Ticket-03 "Mùa Nước Nổi", Test Contract v1.2)

> Bật v1.2 ở PR #22 (`contract_version: "1.2"` + `freshness`), sau nền hai phiên bản ở PR #20 và ADR-0001 (`docs/adr/0001-kho-ca-the.md`). Giỏ, giữ chỗ, kho quán chuyển sang cá thể ở các PR #21, #24, #25, #26, #28 và nhánh `p3/baoduy2048/quan-fresh`.

### Breaking changes

Kho đếm `{"items": {"ca_loc": 1}}` đổi thành **kho cá thể** `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}]}`:

| Chỗ | Trước (v1.0 / v1.1) | Sau (v1.2) |
|---|---|---|
| File kho (`--inventory`, `--inventory-out`) | `{"items": {"kind": số}}` | `{"items": [{"id", "kind", "fresh"}]}`, sắp theo id. Kho đếm ở v1.2 trả mã thoát **2** |
| `scenario.gather.hold` | `["ca_loc", "bong_sung"]` | `[{"id": "I1", "kind": "ca_loc", "fresh": 100}]` |
| `scenario.quan.stock` | `{"ca_loc": 2}` | `[{"id": "I1", "kind": "ca_loc", "fresh": 100}]` |
| `customers[].reserved` (scenario và snapshot) | `{"ca_loc": 1}` | mảng **id** cá thể, ví dụ `["I1", "I4"]` |
| Snapshot `hold`, `stock` | chuỗi kind / số đếm | mảng cá thể `{id, kind, fresh}` |
| `cook_started.data.items` | mảng kind | mảng cá thể, sắp theo kind rồi id |
| `monster_hit.data.lost`, `faint.data.lost` | mảng kind | mảng cá thể theo thứ tự bỏ LIFO |
| Giá món | `base_price` = giá niêm yết | `floor(giá niêm yết × TB fresh / 100)` lúc bắt đầu nấu; boa tính trên giá đã chốt |

### Thêm mới
- Độ tươi: `freshness {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`; tính bằng 240 đơn vị/điểm (`chonoi/fresh.py`). Hàng `fresh < 30` là **ươn**: chiếm ô, không nấu được.
- Event `spoiled{item_id, kind, location}` (`location`: `hold` hoặc `stock`), phát đúng một lần khi đi từ ≥ 30 xuống < 30.
- Giữ chỗ theo id cá thể tươi nhất; hàng đang giữ mà ươn thì giữ lại một lần; không đủ thì đơn chuyển `unfulfillable`.
- HUD: thanh độ tươi trên từng ô giỏ, nhãn "ƯƠN", dòng "Độ tươi kho" ở quán, kho khả dụng chỉ tính hàng chưa ươn và chưa giữ. `?demo=fresh` (chỉ để QA xem HUD, mặc định tắt).
- Skill `smoke-day`, `smoke-p3`; test `tests/test_p3_hud_qa.py`, `tests/test_p3_fresh_schema.py`, `tests/test_p3_reserve.py`, `tests/test_p3_quan_fresh.py`.

### Cách cập nhật fixture và file kho
1. Đặt `contract_version` đúng bản đang chạy. Với v1.2 trở lên, thêm khối `freshness` (bắt buộc, cấm ở v1.1).
2. `gather.hold`: đổi từng chuỗi kind thành `{"id": "I<n>", "kind": "<kind>", "fresh": 100}`, id duy nhất, tăng dần theo thứ tự vào giỏ.
3. `quan.stock`: đổi `{"kind": n}` thành `n` cá thể cùng kind với id duy nhất giữa `hold` và `stock`.
4. `customers[].reserved`: đổi thành mảng id trỏ tới cá thể chưa ươn có trong `stock`, đủ công thức, không dùng chung giữa các đơn.
5. File kho cũ (`{"items": {...}}`) phải chạy lại gather ở v1.2 để sinh file mới, hoặc đổi tay theo bảng trên.
6. Id cá thể cấp theo thứ tự vào giỏ, **tăng xuyên pha và xuyên Ngày** (một `IdAllocator` cho cả lượt).

## Phase 2 (Ticket-02 "Một ngày ở chợ nổi", Test Contract v1.1)

### Breaking changes
- `contract_version: "1.1"` với số chuẩn của Ticket-02 (PR #8).
- `gather.fish_initial` đổi từ danh sách 6 đàn thành số `8`; đàn đầu ca chọn theo seed từ các điểm sinh chuẩn.
- 6 nguyên liệu (thêm `ca_keo`, `keo_neo`), 6 món, 2 bếp (`B1`, `B2`), 4 bàn (`T1`-`T4`), nút `N5`/`N6` kèo nèo.
- CLI thêm `--mode day` và `--days N`; nút `pause`, `shop_done` và lệnh `buy` trong file inputs.
- Snapshot thêm `state: "paused"`, `monsters[]`, `sim_tick` tách khỏi `tick`.

### Thêm mới
- Đàn cá bơi, phản xạ ở mép, đổi hướng theo seed và sinh theo lịch (PR #14, #17, #19).
- Cá Sấu Năm Chèo: tuần tra, đuổi, cắn làm mất Máu và rơi nửa giỏ, bất tử 90 tick, recoil, ngất do quái (PR #13).
- Mở rộng **Rắn Hổ Mây** (`snake`): `extensions: ["snake"]`, loài `ran`, M3 từ Ngày 1 (PR #13).
- Vòng ngày `DaySession`: gather → quan → Shop, kế hoạch D1-D5, nâng cấp oxy/áo phao có hiệu lực từ Ngày kế; lọc món theo kế hoạch (PR #10, #11, #15).
- Tạm dừng dùng chung cho mọi mode (`PauseGate`).
- 2 bếp, 4 bàn, 6 món ở quán (PR #18). UI vòng ngày, menu, pause (PR #23).

## Phase 1 (PRD-0, Test Contract v1.0)

### Thêm mới
- Buổi sáng: oxy, ngạt, Máu, ngất (PR #1); hái nút, bắt đàn cá, giỏ LIFO, cập bến và ghi file kho (PR #4).
- Buổi tối: khách đến theo lịch, giữ nguyên liệu, kiên nhẫn, bỏ đi; bếp, bưng, phục vụ, boa, trả tiền, uy tín, đóng ca (lát 3: commit `e15f865`; lát 4: PR #3).
- Hợp đồng tích hợp `docs/contracts/README.md` (file kho, sự kiện, dữ liệu khách).
- HUD pixel art, asset cá, smoke hai tiến trình, skill `smoke-p1`, `verify-ac` (PR #6).
