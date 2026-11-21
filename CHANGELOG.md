# Changelog
## Unreleased

### Phase 2 · TV5 (UI/QA)
- Cửa sổ chơi `python3 -m chonoi.live --mode day`: menu, DayIntro, HUD sáng/tối, EveningIntro, DayResult, Shop, Summary, pause (Esc/P), Cài đặt âm thanh lưu giữa các lần mở; chạy trên DaySim thật qua `chonoi/live_day.py`. Tùy chọn `--speed N` tua nhanh khi demo.
- Sáng tạo (chỉ client/live): Chợ Chú Sáu, thời tiết theo Ngày, chuyện Má Tư kể theo uy tín, khách quen có tên, Út Sen to hơn.
- `tools/qa_p2.py`: 7 checkpoint Phase 2 bằng CLI headless, ghi `docs/proof/phase-2/qa-report.md`.
- `tests/test_live_day.py`: màn chờ không bước sim, handover, Shop/nâng cấp, Summary, vendor, menu + pause qua HTTP.
