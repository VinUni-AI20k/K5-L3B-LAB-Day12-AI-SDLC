# Changelog

Mọi thay đổi đáng chú ý của game ghi ở đây. Định dạng theo [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/); số phiên bản theo [SemVer](https://semver.org/). Số PR là PR trên repo của nhóm.

## [Unreleased]

Dự kiến phát hành thành **1.0.0** cùng tag `phase-4` (D gắn tag và tạo GitHub Release sau khi cả nhóm đồng ý).

### Phase 3 — contract 1.2 (Ticket-03), THAY ĐỔI PHÁ VỠ (P3-02 đến P3-08)
- **Kho là kho cá thể** `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}` thay cho kho đếm `{"items": {"ca_loc": 2}}` (#43). `game.contract.json` lên `contract_version` **1.2**, khối `tuning.freshness` đúng 4 khóa `initial`, `gather_decay_per_s`, `quan_decay_per_s`, `spoiled_below` (#43, #48).
- Hàng hao tươi theo thời gian (0.5 điểm/s khi lặn, 0.25 điểm/s trong quán), ươn khi `fresh < 30` (vẫn chiếm ô nhưng không nấu được), giữ chỗ theo id, giá món `floor(giá niêm yết × trung bình fresh / 100)` (#45, #46, #49).
- Headless ở 1.2: `--inventory` và `--inventory-out` là mảng cá thể; **file kho đếm của v1.1 hoặc sai schema thì mã 2**; scenario `gather.hold`, `quan.stock` là mảng cá thể, `customers[].reserved` là mảng id (P3-08).
- **Test cũ bị thay đổi vì breaking change:** (1) `tests/helpers.py` `run_headless` mặc định chạy với bản contract 1.1 sinh từ chính `game.contract.json` (biến `CHONOI_CONTRACT`), để các test hồi quy Phase 1-2 vẫn kiểm luật kho đếm không đổi; kiểm 1.2 dùng `run_headless(..., v12=True)` ở `tests/test_p3_v12_cli.py`. (2) `tools/smoke_phase1.py` và `tools/smoke_phase2.py` chạy cùng cách (27 và 15 mục giữ nguyên); đường 1.2 do `tools/smoke_phase3.py` kiểm. (3) `tests/test_contract_v11.py`: khẳng định `contract_version` đổi từ "1.1" sang "1.2", các số chuẩn giữ nguyên. (4) `tests/test_gather_prd.py`: `invuln_ticks` nhận từ v1.1 trở lên.
- Cách chuyển file kho cũ: dùng `counts_to_individuals` trong `chonoi/inventory.py` (cá thể `I1`, `I2`, ... độ tươi 100).

### HUD độ tươi (Phase 3, P3-06)
- Cửa sổ chơi hiển thị độ tươi từng cá thể (thanh dưới ô giỏ), hàng ươn (✕, số ươn, độ tươi thấp nhất) và đơn bị ảnh hưởng ở quán (hàng giữ chỗ đã ươn, đơn không làm được); tính ở `chonoi/freshness_view.py`, chỉ bật khi snapshot có kho cá thể (contract 1.2).

### Cảnh báo và tương phản cao (Phase 4, P4-04)
- Ba cảnh báo có biểu tượng và chữ trong cửa sổ chơi: oxy sắp hết (và hết oxy), Cá Sấu gần, khách sắp giận; tính ở `chonoi/alerts.py` từ snapshot, chỉ có ở `chonoi.live` (trường `alerts`).
- Chế độ tương phản cao: phím H hoặc `?hc=1`; nền đen, chữ trắng/vàng đậm, viền trắng quanh mọi hình.

### Soak headless (Phase 4, P4-04)
- `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` chạy 10 Ngày liền trong một tiến trình bằng chế độ `day` (Ngày 6–10 lặp lại kế hoạch D1–D5) với một bot tất định, ghi `soak.json` (`days`, `days_completed`, `crashes`, `results`, `duration_s`). Không ghi bảng xếp hạng.

### Đóng gói (Phase 4, P4-05)
- `README.md` của nhóm: chạy từ clone sạch bằng 3 lệnh, bảng phím, lệnh cho người phát triển. Hướng dẫn lab gốc chuyển sang `docs/LAB.md`.
- `LICENSE` (MIT), `CREDITS.md` (asset, khung starter, công cụ AI), `CHANGELOG.md` này.
- CI trên Ubuntu chạy thêm bước thử clone sạch theo README (3 lệnh, chế độ headless) và có thể chạy tay (`workflow_dispatch`).

## Phase 2 — contract 1.1 (Ticket-02)

### Thêm
- Cá bơi, đổi hướng, phản xạ ở mép và sinh đàn mới theo seed (#25).
- Cá Sấu: tuần tra, đuổi, cắn làm mất Máu và một phần giỏ, bất tử ngắn sau khi bị cắn, ngất khi Máu về 0 (#30).
- Quán theo kế hoạch Ngày: 2 bếp, 4 bàn, 6 món, chỉ phục vụ món có trong kế hoạch (#27).
- Shop cuối Ngày: mua nâng cấp bình oxy và Máu tối đa, có hiệu lực từ Ngày sau (#26).
- Chế độ `day` (`--mode day --days 1..5`): Lặn → Quán → Shop nối tiếp, tạm dừng (`pause`), lệnh `buy` và `shop_done` (#28).
- Cửa sổ chơi: menu chính, màn tạm dừng, HUD Ngày/pha/kế hoạch, màn Shop, cảnh báo Cá Sấu (#35).
- Smoke tích hợp Phase 2, hồi quy Phase 1, ma trận truy vết Phase 2 (#29, #31, #32).

### Đổi
- `game.contract.json` lên `contract_version` 1.1 với số chuẩn mới; thêm nguyên liệu `ca_keo`, `keo_neo` (#23).
- Kế hoạch Phase 2, 3, 4 (#22, #24); retro Phase 2 (#33, #34); ma trận Phase 2 cập nhật sau khi gộp giao diện (#36); nhật ký AI của A (#37).

## Phase 1 — contract 1.0 (PRD-0), tag `phase-1`

### Thêm
- Buổi sáng **Lặn & Hái**: bơi, oxy, ngạt, ngất, cập bến, hái rau, bắt cá, giỏ có sức chứa (#5, #7).
- Buổi tối **Mở Quán**: khách đến, giữ chỗ nguyên liệu, kiên nhẫn, nấu, phục vụ, tính tiền, boa, uy tín (#8, #10, #12, #13, #16).
- Bàn giao kho giữa hai buổi qua file kho; kiểm scenario và mâu thuẫn mức luật, mã thoát 2 khi sai (#2, #9, #11).
- Hợp đồng tích hợp, bảng sự kiện, câu hỏi PO (#1, #3, #6).
- Harness AI: skill kiểm tất định và kiểm số cứng, hook chặn sửa file khóa, hook pre-push chạy test (#4, #14, #15, #20).
- Smoke Phase 1 hộp đen và ma trận truy vết (#17, #18); nhật ký dùng AI và hồ sơ thành viên (#19, #21).
