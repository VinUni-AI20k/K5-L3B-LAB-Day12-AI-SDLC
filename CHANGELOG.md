# Changelog
## Unreleased

### Phase 3 · Schema kho cá thể v1.2 & Adapter (TV1)
- **Breaking change (Test Contract v1.2):** File kho và cấu trúc `hold`/`stock` chuyển từ dạng đếm (`{"items":{"ca_loc":1}}`) sang mảng cá thể `{"items":[{"id":"I1","kind":"ca_loc","fresh":100}]}`; `customers[].reserved` chuyển sang mảng ID cá thể.
- Thêm `tuning.freshness` (`initial: 100`, `gather_decay_per_s: 0.5`, `quan_decay_per_s: 0.25`, `spoiled_below: 30`) vào `game.contract.json` và kiểm tra trong `chonoi/contract.py`.
- `chonoi/inventory.py` và `chonoi/ids.py`: thêm helper v1.2 dùng `Fraction` (chính xác trên lưới `1/240` và thập phân bất kỳ), đọc/ghi nguyên tử chọn schema theo `contract_version` (v1.2 từ chối kho đếm bằng mã `2`), lọc tươi nhất, tính giá theo độ tươi trung bình.
- Lộ trình chuyển tiếp: `game.contract.json` tạm giữ `contract_version: "1.1"` trong khi TV2–TV4 tích hợp để bộ test P1–P2 trên `main` không đứt gãy; khi đủ các đầu sẽ bật `"1.2"`. Khi nâng lên v1.2, các fixture `hold`/`stock` dạng đếm và `reserved` dạng dict số lượng cần chuyển sang mảng cá thể/ID (mẫu tại `docs/contracts/inventory.v12.sample.json`).

### Phase 2 · TV5 (UI/QA)
- Cửa sổ chơi `python3 -m chonoi.live --mode day`: menu, DayIntro, HUD sáng/tối, EveningIntro, DayResult, Shop, Summary, pause (Esc/P), Cài đặt âm thanh lưu giữa các lần mở; chạy trên DaySim thật qua `chonoi/live_day.py`. Tùy chọn `--speed N` tua nhanh khi demo.
- Sáng tạo (chỉ client/live): Chợ Chú Sáu, thời tiết theo Ngày, chuyện Má Tư kể theo uy tín, khách quen có tên, Út Sen to hơn.
- `tools/qa_p2.py`: 7 checkpoint Phase 2 bằng CLI headless, ghi `docs/proof/phase-2/qa-report.md`.
- `tests/test_live_day.py`: màn chờ không bước sim, handover, Shop/nâng cấp, Summary, vendor, menu + pause qua HTTP.
