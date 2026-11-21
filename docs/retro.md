# Retro nhóm

## Phase 2 (nhanh) — nháp của Integrator (s0ra1n0), cả nhóm bổ sung / sửa
- **Điều tốt:**
  - Lát 0 (nền v1.1) merge sớm, nên các lát khác code song song trên cùng contract.
  - Mỗi lát có test hộp đen riêng; `verify-phase` gom bằng chứng trong một lệnh.
  - Kết quả cuối phase: 11/12 AC đạt, 179 test xanh, `day` 5 Ngày tất định, 1 Ngày chạy dưới 1 s.
- **Điều tệ:**
  - Lát 0 và lát 5 cùng thêm `--days`/`pause`/`buy`/scenario `day`, nên phải giải 5 file xung đột.
  - Commit cá bơi vào thẳng `main` làm đỏ một test P1.
  - Tốc độ chéo của cá sai √2 lần mà test không bắt được; chỉ lộ ra khi đo trên lần chạy thật.
  - `contract.py` vẫn chặn `burn_s` sau khi nhóm đã chốt bật `burn`.
  - UI Phase 2 (AC-P2-08) chưa làm.
- **1 hành động cho Phase 3:** trước khi merge vào `main`, người merge chạy `python3 tools/run_checks.py` và đo ít nhất một lần chạy thật cho luật có số đo (tốc độ, thời gian).
  - Người nhận: Integrator (s0ra1n0) nhắc trong mỗi PR.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
