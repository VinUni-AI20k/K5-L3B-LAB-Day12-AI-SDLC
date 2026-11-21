# Research — Phase 1 lõi

PRD-0 không đọc được bằng AI; mọi quyết định dưới đây suy từ starter + contract. `GIẢ ĐỊNH` = chờ PO xác nhận.

| # | Quyết định | Lý do | Phương án loại |
|---|---|---|---|
| R1 | Giữ starter Python, chỉ viết luật trong `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (+ kiểm mức luật ở `scenario.py` nếu nhóm đồng ý) | Khung đã có CLI, JSONL, kho, live; smoke test xanh | Viết lại ngôn ngữ khác: tốn thời gian |
| R2 | Oxy/vùng theo `d` cuối bước; dưới nước khi `d > surface_depth` | Docstring + `_at_surface` của starter | `d ≥` |
| R3 | Ngạt đếm khi oxy 0 + dưới nước (tính cả bước chạm 0), reset khi oxy > 0 hoặc lên mặt nước — đã xác nhận bởi TICKET-02 | `scenario.py` ép `zero_oxy_ticks ∈ [0,59]` và >0 chỉ khi oxy 0 dưới nước | Đếm liên tục |
| R4 | Nhặt "tất cả hoặc không" khi giỏ thiếu chỗ — đã xác nhận bởi TICKET-02 | Giữ đơn giản, `hold_full` rõ nghĩa | Nhặt một phần |
| R5 | Đàn bị bắt bị loại (`GIẢ ĐỊNH`, clarify #14; đổi so với bản đầu) | P2 có cá bơi + sinh thêm, trần 12 | Giữ cá sau khi bắt |
| R6 | Chọn món đều theo seed (TICKET-02) qua `Streams.get("quan_order")` (tên luồng `GIẢ ĐỊNH`) | Tất định, tách luồng RNG | Món đầu theo id (mất đa dạng) |
| R7 | Thời gian: `ticks = round(x_s * tick_hz)` | Starter dùng `int(round(... * 60))` | — |
| R8 | Interact quan chọn theo khóa `(dist, 0 nếu bếp / 1 nếu bàn, id)` | `TODO(nhóm)` của starter | — |
| R9 | Không sửa `runner.py`: sim chỉ trả `(name, data)` và đặt `done/reason` | Runner đã lo thứ tự ghi, `end`, kho | — |
| R10 | Thứ tự bước theo FR-012 / FR-022 | Theo `TODO(nhóm)`; PRD 13.8 / F chưa đối chiếu | — |
