# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Nguyễn Như Duy An (`K0heii` — M6) | Antigravity (Gemini) | Đọc dự án, chia 6 module, lập `TEAM.md`, chốt hợp đồng `docs/contracts/README.md`, viết validate `scenario.py` (`M6.3`) & test tích hợp (`M6.4`) | ~30k token | Trước khi đưa `PRD0.md`, AI giả định `hand` là `str`; đã đối chiếu PRD-0 mục D sửa thành payload object `{order_id, dish_id, base_price}`. |
| Phase 1 | Nguyễn Nhật Minh (`NhMinh-2610` — M4) | Antigravity / Gemini | Lên kế hoạch & AC (`M4.1`), viết bộ test `tests/test_quan_m4.py` (`M4.2`), cài đặt `chonoi/sim/quan.py` (`M4.3`), ghép M3 ↔ M4 (`M4.4`) | ~35k token | Chú ý shim `python3.exe` trên Windows khi chạy test hộp đen (không sửa `game.contract.json`); đã rà kỹ biên float cho `tip` và `reputation`. |
