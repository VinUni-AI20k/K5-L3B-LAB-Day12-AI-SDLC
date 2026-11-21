# Hợp đồng tích hợp (nên chốt sớm; hình thức do nhóm chọn)

Điền trong 15 phút kickoff (hoặc thay bằng một mục trong README / một bảng trên giấy, miễn cả nhóm cùng thống nhất):
1. **Schema file kho** — khớp mục G của PRD-0 (kho ghi khi `gather_end`) + một file kho mẫu hợp lệ: `inventory.sample.json`.
2. **Giao diện giữa `sim/*` và `client/ui`** — trạng thái nào UI được đọc, lệnh nào UI gửi vào.
3. **Danh sách sự kiện** — tên, `data`, ai phát, ai nghe (gather: `gather`, `node_regrown`, `hold_full`, `fish_caught`, `gather_end`...; quan: theo mục E của PRD-0).

Khi đổi hợp đồng sau này: báo cả nhóm và ghi lại lý do (ADR hoặc ghi chú, tùy chọn).

## Kho v1.2 (P3-02)

File kho dùng `{"items":[{"id":"I1","kind":"ca_linh","fresh":100.0}]}`; `items` là mảng cá thể theo thứ tự, không còn object đếm. `id` là `I` + số nguyên dương duy nhất; `kind` thuộc sáu nguyên liệu; `fresh` hữu hạn trong `[0,100]`. Kho rỗng là `{"items":[]}`. File đếm v1.0 bị từ chối với mã 2. Ghi nguyên tử khi Gather kết thúc; Day chuyển nguyên `id/kind/fresh` sang Quán, không hao tươi ở ranh giới pha. Xem [mẫu](inventory.sample.json) và [AC P3-02](../plan/phase-3.md).
