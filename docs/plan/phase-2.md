# Kế hoạch Phase 2 (≤ 1 trang)

- Mục tiêu: chơi trọn vòng ngày D1–D5 theo Test Contract v1.1 (số chuẩn, cá bơi/sinh, Cá Sấu, 2 bếp/4 bàn, 6 món, `--mode day`, Shop, pause) có menu, HUD, bằng chứng tích hợp và tag `phase-2` trước 1:55.

- Việc / người / phụ thuộc:
  - TV1 · Cá Sấu, Máu, ngất; giữ `GatherSim.step` — nhận `day`/tuning nâng cấp từ TV4
  - TV2 · cá bơi/sinh, N5/N6, 6 loại ở bộ đọc kho — ghép vào bước của TV1
  - TV3 · 6 món, 2 bếp/4 bàn, day_plan D1–D5 — API kế hoạch cho TV4/TV5
  - TV4 · CLI `--mode day`, scenario, runner, pause, Shop — nhận kho từ TV1/2, kế hoạch từ TV3
  - **TV5 · UI/QA/Release** — làm màn hình từ snapshot mẫu (không chờ TV4), sau đó đổi sang `Session("day")`; sở hữu smoke liên tiến trình, đo hiệu năng, ma trận, tag

- Checkpoint TV5 (lệnh `python3 tools/qa_p2.py`):

| Phút | CP | Điều kiện đạt |
|---|---|---|
| 20 | CP1 smoke gather → quan | `gather_end.items` = file kho = stock quán tick 0, đủ 6 loại |
| 35–45 | CP2 day 1 ngày | ≤ 22.200 tick, ≤ 20 s, mở đầu `day_start → day_plan → phase_start` |
| 35–45 | CP3 day 2 ngày | money=earned=200 → mua oxygen + đóng Shop cùng frame → money 0, earned 200, oxy D2 2700 |
| 35–45 | CP4–CP6 | pause đứng timer · ngất mở quán kho rỗng · chạy lại giống từng byte |
| 45 | CP7 regression | toàn suite đạt; test đổi theo v1.1 có lý do |
| 45–55 | UI + tag | ảnh HUD 1280×720, FPS ≥ 30, ma trận `docs/verification/phase-2.md`, tag `phase-2` |

- Rủi ro: `--mode day` đến muộn → UI dùng bộ ghép tạm cùng tên trường snapshot v1.1; nhiều người sửa `chonoi/live.py` → TV5 gộp cuối, chạy lại test HTTP.
