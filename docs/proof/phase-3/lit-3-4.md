# Bằng chứng lát 3–4 — Quán và đơn đặt trước

- Contract: `quan.reservations` khai số đơn, thời gian giữ bàn, hệ số giá và mức trừ uy tín.
- Quán hao fresh theo Fraction, bỏ kho cá thể dưới ngưỡng 30 trước khi xét order; event `spoiled` theo ID.
- Customer giữ ID cá thể; món nấu chốt giá theo độ tươi trung bình, event `cook_started.items` gồm cá thể theo kind rồi ID.
- Day công bố hai đơn sau `phase_start(gather)`; Quán xử lý giữ bàn, arrival, stock, patience, burnt và closing; state cuối là served/failed.
- Fixture ngày sau tạo lại các loại hàng từ `gather.hold` với ID I mới và fresh đầu.
- HUD hiển thị độ tươi của giỏ/kho, đơn reservation và schema kho cá thể.
- Giả định công thức chốt giá được ghi ở `docs/clarify.md`, đang chờ PO xác nhận.
