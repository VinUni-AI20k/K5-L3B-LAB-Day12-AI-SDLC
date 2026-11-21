# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | Vũ Văn Chủ (`chur04`) | Codex (không đo model/token/chi phí trong repo) | Đọc toàn repo và PRD-0 do người dùng cung cấp; triển khai lát 4, test, bằng chứng, clarify và tài liệu bàn giao | Chưa đo | Helper test truyền trùng dish_id gây TypeError đã được sửa; alias python3 trên Windows làm test CLI không chạy, kiểm lại bằng sys.executable trong tiến trình. 28 test mới / 60 test toàn repo đạt; xem docs/proof/phase-1/chur04-service.md. |
| 2 | Vũ Văn Chủ (`chur04`) | Codex | Đọc trạng thái sau merge và TICKET-02; thực hiện day/Shop/pause/inputs/CLI, menu kế hoạch/ghế nhỏ nhất, burn, test và proof | Chưa đo | Tool proof ban đầu thiếu repo root trong sys.path, đã sửa. 104 test đạt; proof dùng bản sao với fixture v1.1, tắt cá tự động, không đổi manifest chung. Xem docs/proof/phase-2/chur04/README.md. |
