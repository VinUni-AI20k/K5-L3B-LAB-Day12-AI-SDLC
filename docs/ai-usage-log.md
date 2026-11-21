# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | A | Claude Code / Claude Opus 5.5 | Khung `step()` gather, lát 1 (`_dive_surface`, `_oxygen_and_choke`), 12 test `tests/test_gather_lat1.py`, điền `docs/contracts/README.md` | ~3,7M token: input ~3,68M (gần hết là cache read), output ~26k. Đếm từ transcript Claude Code | Không thấy lỗi luật sau khi đối chiếu mục F. Môi trường Windows không có `python3` nên AI phải dựng venv riêng để chạy test; không sửa `headless_cmd` |
