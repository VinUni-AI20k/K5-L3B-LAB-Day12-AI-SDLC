# Smoke vòng ngày Phase 2

- Branch: `khoa-verification` (đổi tên từ `qa/khoa-phase1-verification`).
- Code được kiểm lần cuối: `fe3930f` (cá bơi/sinh, Cá Sấu, Shop/đa bếp và HUD đã tích hợp).
- Bộ test sau cập nhật: `$env:PYTHONPATH="tests;."` rồi `python3 -m unittest discover -s tests -v` — **108/108 OK**.

## Lệnh

```powershell
python3 -m chonoi.headless --mode day --seed 42 --days 1 --ticks 22200 --snapshot-every 600 --out docs\proof\phase-2\day-one.jsonl
python3 -m chonoi.headless --mode day --seed 42 --days 5 --ticks 111000 --snapshot-every 600 --out docs\proof\phase-2\day-five.jsonl
```

Hai lệnh đều thoát mã 0; end record lần chạy cuối trên `fe3930f` có `reason: days_complete`, `days_completed` lần lượt là 1 và 5. File JSONL bị `.gitignore` bỏ qua; các lệnh trên có thể chạy lại để tái tạo output.

## Kết quả

- D1: `day_start`/`day_plan`/`phase_start(gather)` ở tick 0; `gather_end` ở 10800; `quan_end` ở 21600; `shop_end` ở 22200. End record: `reason: days_complete`, `days_completed: 1`.
- D1–D5: kế hoạch ngày xuất hiện tại tick 0, 22200, 44400, 66600 và 88800; Shop D5 đóng ở tick 111000. End record: `reason: days_complete`, `days_completed: 5`.
- Kết quả: **đạt** cho chuyển pha, phát kế hoạch, timer Shop và điều kiện kết thúc ngày.

Smoke không gửi input gameplay và không cung cấp inventory; do đó không tự nó chứng minh cá bơi/sinh/bắt, Cá Sấu hay phục vụ món. Các hành vi cá, quái, đa bếp/bàn và menu filter được kiểm riêng trong regression. HUD có bằng chứng riêng tại [`hud.md`](./hud.md).
