# NhMinh-2610 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - `M4.1` (`7a57f3b`): Lập kế hoạch, AC (`AC-M4-01`–`AC-M4-08`) và checklist tiến độ toàn dự án (`docs/plan/task-Minh.md`).
  - `M4.2` (`7f31375`): Viết bộ 11 test hộp đen & unit `tests/test_quan_m4.py` cho bếp, bàn, bưng, tiền, boa, uy tín và hết ca.
  - `M4.3` (`06d8ef5`): Cài đặt luật M4 trong `chonoi/sim/quan.py`, chạy xanh test và lưu bằng chứng `docs/proof/phase-1/m4-test-log.txt`.
  - `M4.4` (`b42538f`): Gộp `main` (`M3.3` + `M6`), xử lý xung đột `quan.py`/`standup.md`/`ai-usage-log.md`, bổ sung test ghép `M3 ↔ M4` đạt 68/68 test xanh.
- **Tôi đã review (kèm link):** Đã kiểm tra chéo `chonoi/sim/quan_customers.py` và `tests/test_quan_customers_m3.py` của `ththanh8888` khi ghép `M3 ↔ M4`.
- **AI sai ở đâu và tôi phát hiện thế nào:** Trên Windows, `python3` trỏ vào alias Microsoft Store gây `WinError 1920` khi chạy test hộp đen; giữ nguyên `game.contract.json` cho CI Linux và dùng shim `python3.exe` tạm ở `$env:TEMP`. Ngoài ra đã rà kỹ sai số float ở ngưỡng `tip` và `reputation` để không lệch `floor(reputation)`.
- **Điều tôi học được:** Tách rõ interface giữa M3 (`CustomerMixin`) và M4 trong `quan.py` cùng viết test TDD từ AC giúp ghép nhánh nhanh, không vỡ luật lõi.
