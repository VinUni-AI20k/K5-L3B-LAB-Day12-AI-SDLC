# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | TV2 | Claude Code (Claude Opus 5.5) | Lát 3 quán (`chonoi/sim/quan.py`), kiểm fixture/contract mã 2, 19 test, `docs/contracts/quan.md`, `docs/clarify.md`, `docs/plan/phase-1.md`, chép PRD-0 vào `docs/prd/` | chưa đo | AI code khi chưa có PRD → đoán sai 9/13 chỗ (lịch khách theo `duration − time_left` thay vì phase_tick; rời bàn ở đầu bước thay vì sau interact; data sự kiện dùng `customer_id` thay `order_id`; `no_dish` có `table_id`; thiếu `order_status`, `closing`...). Phát hiện khi PO dán PRD-0 và đối chiếu từng dòng (bảng trong `docs/clarify.md`), sửa code + test. Bài học: đọc PRD trước khi cho AI code. |
