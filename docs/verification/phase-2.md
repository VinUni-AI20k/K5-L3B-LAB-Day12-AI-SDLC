# Ma trận kiểm chứng Phase 2

Cập nhật trên `main` tại commit `90bd430` (tag `phase-2`; code giống bản tích hợp `fe3930f`).

| AC | Kiểm chứng / bằng chứng | Trạng thái |
|---|---|---|
| AC-P2-01 | Contract v1.1, số chuẩn, 6 nguyên liệu, 6 món, `day_plan`, `shop`: `chonoi/contract.py`, `tests/test_qa_phase2.py`, `tests/test_smoke_p1.py` | đạt |
| AC-P2-02 | Cá bơi 1.5 m/s, đổi hướng, phản xạ mép, sinh theo lịch, trần 12: `tests/test_gather_fish.py`, `tests/test_qa_phase2.py` | đạt |
| AC-P2-03 | Cá Sấu patrol/chase/recoil, hit/faint, bất tử, M2 từ Ngày 3: `tests/test_gather_monsters.py`, `tests/test_monsters_edges.py`, [day-multi.md](../proof/phase-2/day-multi.md) | đạt (cách hiểu bất tử t+90 chờ xác nhận ở `docs/clarify.md` #12) |
| AC-P2-04 | 2 bếp / 4 bàn / 6 món, lọc menu theo kế hoạch ngày: `tests/test_p2_quan_shop.py` | đạt |
| AC-P2-05 | Giá Shop, lỗi funds/max_level/unknown, thứ tự buy và `shop_done`, tự đóng 600 tick: `tests/test_day_p2.py`, `tests/test_p2_quan_shop.py`, [day-multi.md](../proof/phase-2/day-multi.md) | đạt |
| AC-P2-06 | Thứ tự pha, kế hoạch D1–D5, áp nâng cấp từ ngày kế và giới hạn 20s/ngày: `tests/test_day_p2.py`, [day-smoke.md](../proof/phase-2/day-smoke.md), [day-multi.md](../proof/phase-2/day-multi.md) | đạt |
| AC-P2-07 | Pause/resume dừng timer ở gather, quán và Shop: `tests/test_day_p2.py::Pause` | đạt |
| AC-P2-08 | Menu, màn hình ngày, HUD v1.1: [hud.md](../proof/phase-2/hud.md) — 56/57. Còn va chạm ở 480px, thiếu một số HUD v1.1 và chưa kiểm chơi tay trọn vòng ngày trên trình duyệt | một phần |
| AC-P2-09 | Regression P1/P2 108/108; smoke tích hợp [integration.md](../proof/phase-2/integration.md), [smoke.md](../proof/phase-2/smoke.md) 7/7 | đạt |

## Kết quả kiểm chứng bổ sung của Khoa

- Windows PowerShell: `$env:PYTHONPATH="tests;."`
- `python3 -m unittest discover -s tests -v` trên code `fe3930f`: **108/108 OK**.
- Smoke gather → quan và smoke ngày D1/D1–D5 chạy lại trên `fe3930f`; xem [integration.md](../proof/phase-2/integration.md) và [day-smoke.md](../proof/phase-2/day-smoke.md).
- HUD check chạy với `$env:PYTHONIOENCODING="utf-8"`: **56/57**; mục trượt là `♥♥♥` va chạm với `Độ sâu 5.5 m` ở 480px.

## Đánh giá ngắn

- Đạt: AC-P2-01–07, AC-P2-09. Một phần: AC-P2-08.
- Còn ngoài phạm vi Khoa #6: hoàn thiện HUD v1.1/chơi tay trọn vòng, retro Phase 2 và 2 mục mở rộng cho cả lab.
