# Bảng công việc Phase 3 (1:55–2:30 · Test Contract v1.2 — Change Request "Mùa Nước Nổi")

> **Lưu ý quan trọng:** Chỉ bắt đầu thực hiện bảng này **sau khi đã gắn tag `phase-2`**. Phase 3 có **Breaking Change** đổi kho đếm sang kho cá thể (file kho đếm v1.1 phải trả mã thoát `2`).

**Quy ước:** đợt 1 làm ngay lúc 1:55, đợt 4 làm cuối. Task nào ghi "Chờ" thì phải đợi task đó xong rồi mới làm. Trong lúc chờ, làm tiếp task khác của mình ở đợt thấp hơn.

**Danh sách thành viên:** Huy (`huyvu-03` — M1) · Quang (`QuangNEU` — M2) · Cao (`ththanh8888` — M3) · Minh (`NhMinh-2610` — M4) · Thanh (`thanhvu101` — M5) · An (`K0heii` — M6, kiêm PO/Integrator).

| Đợt | Mã task | Người | Module | Việc cần làm | Chờ ai / task nào | Ai chờ mình |
|---|---|---|---|---|---|---|
| **1** (1:55–2:02, 7 phút đầu) | M6.1 | An (M6) | M6 | Phân tích tác động (bảng module/file/test bị ảnh hưởng), chốt quyết định đổi schema kho đếm → kho cá thể `{id, kind, fresh}`, cập nhật `docs/contracts/README.md` v1.2 & `docs/clarify.md` | Tag `phase-2` | **Tất cả** (chặn mọi task .2) |
| 1 | M6.2 | An (M6) | M6 | Nâng `game.contract.json` (`freshness: {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}`), viết adapter `inventory.py` v1.2 (đọc/ghi mảng cá thể, từ chối kho đếm mã `2` khi bật `v1.2`) | M6.1 | **M1.3, M2.3, M3.3, M4.3** |
| 1 | M1.1 | Huy (M1) | M1 | Spec: AC hao tươi giỏ (`0.5/s`, đơn vị nguyên tránh sai số ngưỡng 30), `spoiled` (`location:"hold"`), `lost` cá thể LIFO trong `monster_hit`/`faint` | Không | M1.2 |
| 1 | M2.1 | Quang (M2) | M2 | Spec: AC giỏ `gather.hold` mảng cá thể `{id, kind, fresh}`, cấp id `I1, I2…` tăng xuyên pha/Ngày, xuất `gather_end.inventory` theo id | Không | M2.2 |
| 1 | M3.1 | Cao (M3) | M3 | Spec: AC hao tươi kho quán (`0.25/s`), `spoiled` (`location:"stock"`), giữ chỗ theo `id` cá thể tươi nhất (hòa theo id), nhả & giữ lại 1 lần khi ươn → `unfulfillable` | Không | M3.2 |
| 1 | M4.1 | Minh (M4) | M4 | Spec: AC giá chốt theo độ tươi `floor(giá × avg_fresh / 100)`, boa `floor(base_price × 0.2)`, `cook_started.items` mảng cá thể, chuyển kho cá thể trong `day`/Shop | Không | M4.2 |
| 1 | M5.1 | Thanh (M5) | M5 | Spec: cách hiển thị độ tươi & cảnh báo hàng ươn (`fresh < 30`) trong HUD giỏ sáng & kho quán trên `chonoi.live` | Không | M5.2 |
| **2** (~2:02–2:10) | M1.2 | Huy (M1) | M1 | Viết test ngưỡng `fresh: 30` → `spoiled` ở tick 1, pause dừng hao tươi, `lost` cá thể LIFO khi trúng quái/ngất | M1.1, M6.1 | M1.3 |
| 2 | M2.2 | Quang (M2) | M2 | Viết test cấp id `I1, I2…` xuyên ngày, `gather --inventory-out` xuất mảng cá thể đúng độ chính xác | M2.1, M6.1 | M2.3 |
| 2 | M3.2 | Cao (M3) | M3 | Viết test giữ chỗ cá thể tươi nhất, cá thể đang giữ vừa ươn → nhả & thử giữ lại theo `order_tick` rồi `table_id`, thiếu → `unfulfillable` | M3.1, M6.1 | M3.3 |
| 2 | M4.2 | Minh (M4) | M4 | Viết test chốt `base_price` theo `avg_fresh`, boa trên giá đã chốt, `cook_started.items` sắp theo `(kind, id)`, bàn giao kho cá thể trong `day` | M4.1, M6.1 | M4.3 |
| 2 | M5.2 | Thanh (M5) | M5 | Cập nhật `chonoi/web/` đọc `hold`/`stock` dạng mảng cá thể `{id, kind, fresh}` (không vỡ UI khi chuyển schema) | M5.1, M6.1 | M5.3 |
| 2 | M6.3 | An (M6) | M6 | Cập nhật `scenario.py` v1.2 (`gather.hold`, `quan.stock` mảng cá thể, `customers[].reserved` mảng id cá thể chưa ươn, không dùng chung, id vật lý duy nhất) + test | M6.1, M6.2 | Test của M1–M4 |
| **3** (~2:10–2:20) | M2.3 | Quang (M2) | M2 | Code `gather.py`: đổi `hold` sang mảng cá thể `{id, kind, fresh}` (dùng đơn vị nguyên 240/điểm hoặc tương đương), cấp `I1, I2…` xuyên pha/Ngày, xuất kho cá thể (**làm trước**) | M2.2, M6.2 | **M1.3 (Huy)**, M4.3 |
| 3 | M1.3 | Huy (M1) | M1 | Code `gather.py`: hao tươi đầu bước (`-0.5/s`), phát `spoiled` theo id khi đi từ `≥ 30` xuống `< 30`, cập nhật `lost` trong `monster_hit`/`faint` thành mảng cá thể LIFO | M1.2, M6.2, **M2.3 (Quang)** | M6.4 |
| 3 | M3.3 | Cao (M3) | M3 | Code `quan.py`: hao tươi kho thô (`-0.25/s`), phát hết `spoiled` theo id rồi xử lý giữ chỗ bị ươn (nhả & giữ lại 1 lần theo `order_tick`, `table_id`), chuyển `unfulfillable` nếu thiếu | M3.2, M6.2 | **M4.3 (Minh)**, M6.4 |
| 3 | M4.3 | Minh (M4) | M4 | Code `quan.py` & `day`/`Shop`: tiêu đúng id cá thể đang giữ khi nấu, chốt `base_price = floor(giá × avg_fresh / 100)`, `cook_started.items` sắp `(kind, id)`, bàn giao kho cá thể trong `day` (Shop không hao tươi) | M4.2, M6.2, **M3.3 (Cao)** | M5.3, M6.4 |
| 3 | M5.3 | Thanh (M5) | M5 | Hoàn thiện HUD độ tươi (thanh/số/nhãn/biểu tượng nhận biết hàng ươn `fresh < 30`) ở cả `gather` và `quan` | M5.2, M2.3, M4.3 | M5.4 |
| **Mốc 2:15** (phút 20) | M6.3b | An + cả nhóm | M6 | **Smoke bàn giao kho cá thể** (`gather` fresh=100 cập bến tick 0 → `quan --inventory` tick 0 khớp chính xác `id, kind, fresh`), standup 2–3 phút hỗ trợ lát trễ | M2.3, M3.3, M4.3 | M6.4 |
| **4** (~2:20–2:30, cuối phase) | M1.4–M4.4 | Huy, Quang, Cao, Minh | M1–M4 | Chạy unit test ngưỡng 30, giữ lại khi ươn, chốt giá theo fresh, kiểm `day`; lưu bằng chứng vào `docs/proof/phase-3/` | M1.3–M4.3 | M6.5 |
| 4 | M5.4 | Thanh (M5) | M5 | Chơi thử trên `chonoi.live`, chụp ảnh HUD hiển thị độ tươi & hàng ươn vào `docs/proof/phase-3/` | M5.3 | M6.5 |
| 4 | M6.4 | An (M6) | M6 | Bật `contract_version: "1.2"` trên `main` (kho đếm trả mã `2`), chạy smoke 2 tiến trình + `day` + **regression P1–P2** (cập nhật fixture cũ & ghi lý do) | M1.3–M4.3, M6.3b | M6.5 |
| 4 | M6.5 | An (M6, PO) | M6 | Ghi breaking change & hướng dẫn chuyển fixture vào `CHANGELOG.md`; điền `docs/verification/phase-3.md`; retro nhanh về lần đổi kho vào `docs/retro.md` | Bằng chứng M1.4–M5.4, M6.4 | M6.6 |
| 4 | M6.6 | An (M6) | M6 | Chạy `check_team.py` + toàn bộ `unittest`, **gắn tag `phase-3` trước 2:30** | M6.5 | — |

## Mở rộng (tùy chọn — chỉ làm khi lõi v1.2 đã xanh)
- **`current` (Dòng nước lũ)**: Huy (M1) — lịch `t = 1800·k`, cảnh báo trước 120t, đẩy `±1.5 m/s` ở `d ≥ 10` trong 480t (`current_warning`/`current_start`/`current_end`).
- **`reservations` (Khách đặt trước)**: Cao/Minh (M3/M4) — 2 đơn `R1, R2` mỗi Ngày, giữ bàn trước 1800t, giá `×1.5`, lỡ đơn uy tín `-1`.

## Việc ngoài bảng (mọi người, mọi phase)

| Việc | Khi nào |
|---|---|
| Mỗi người có commit thật (làm chung ghi `Co-authored-by:`) | Suốt phase |
| Review chéo: Huy↔Quang (M1↔M2), Cao↔Minh (M3↔M4), Thanh↔An (M5↔M6) | ~2:18–2:24 |
| Cập nhật `docs/ai-usage-log.md`, `docs/standup.md`, `docs/members/<handle>.md` | Cuối phase |
| Vướng quá 10 phút: báo ngay kênh nhóm để người dự phòng hỗ trợ | Bất cứ lúc nào |

## Ba điểm dễ nghẽn

1. **Sai số số thực ở ngưỡng `fresh = 30` và phép `floor` giá**: Cả M1, M2, M3, M4 phải dùng chung biểu diễn chính xác (ví dụ lưu `fresh_units` nguyên = `fresh × 240`, trừ `2` đơn vị/tick ở gather và `1` đơn vị/tick ở quán) để so ngưỡng `< 30` và `floor` chính xác 100%.
2. **Đổi schema kho làm gãy test P1–P2 đồng loạt**: Giữ adapter chuyển đổi trong lúc dev, chỉ bật `contract_version: "1.2"` (từ chối kho đếm mã `2`) ở `M6.4` khi cả đầu `gather` (M2) và đầu `quan` (M3/M4) đã sẵn sàng; cập nhật fixture cũ và ghi rõ lý do trong `CHANGELOG.md`.
3. **Thời gian Phase 3 chỉ có 35 phút**: Chốt code freeze ở **2:20** để M6 có đủ 10 phút bật v1.2, chạy regression, ghi `CHANGELOG.md`, `verification/phase-3.md` và đẩy tag `phase-3` trước **2:30**.
