# Quán Ăn Chợ Nổi v1.0.0 — nhóm nhom6ae

Game 2D quản lý quán ăn miền Tây: sáng Út Sen lặn bắt cá, hái rau trên sông; tối nấu và phục vụ khách trên nhà bè
Má Tư; cuối ngày mua nâng cấp. Bản phát hành cuối của Lab Day 12 (Contract v1.3).

## Điểm mới
- **Vòng ngày đầy đủ** (`--mode day`, 5 Ngày): Lặn & Hái → Mở Quán → Shop nâng cấp (Bình oxy, Áo phao), kế hoạch món
  D1–D5 của Má Tư, menu chính, pause, màn hình đầu ngày / nhập kho / kết quả / tổng kết.
- **Mùa Nước Nổi — độ tươi:** mỗi nguyên liệu là một cá thể có độ tươi; giỏ hao 0.5/s, kho quán 0.25/s, dưới 30 là
  ươn; giữ chỗ theo từng cá thể, giá món theo độ tươi; kho bàn giao giữa hai buổi bằng file `{"items":[{id,kind,fresh}]}`.
- **Thế giới sống:** 8 đàn cá bơi và sinh theo seed, Cá Sấu Năm Chèo tuần tra / đuổi / lùi sau khi chạm.
- **Cảnh báo dễ nhận biết** (thủy quái gần, oxy sắp hết, khách sắp giận) và **chế độ tương phản cao**; HUD chữ ≥ 18 px.
- **Mở rộng:** Cháy món (`burn`) và Bảng xếp hạng cục bộ (`leaderboard`, top 10 bền vững).
- **Công cụ:** benchmark có render, soak 10 Ngày, kiểm HUD tự động, smoke bàn giao kho.

## Cách chạy (Python 3.9+, chỉ thư viện chuẩn, trình duyệt web)
Từ gói đính kèm (giải nén) hoặc clone sạch:
```bash
git clone https://github.com/NgChiVinh/K5-L3B-LAB-Day12-AI-SDLC-nhom6ae.git && cd K5-L3B-LAB-Day12-AI-SDLC-nhom6ae
python3 -m chonoi.live --mode day --days 5        # mở http://127.0.0.1:8000/
```
Điều khiển: WASD/mũi tên di chuyển · E tương tác · Space bắt cá · Esc/P tạm dừng · 1/2 mua nâng cấp · Enter đóng Shop.

| Việc | Lệnh |
|---|---|
| Test (1 lệnh) | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` |
| Headless | `python3 -m chonoi.headless --mode gather\|quan\|day --seed 1 --ticks 600 --out out.jsonl` |
| Benchmark | `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` |
| Soak | `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` |
| Xuất bảng xếp hạng | `python3 -m chonoi.live --mode gather --export-leaderboard out.json` |

Kết quả đo trên commit bàn giao: xem [`docs/verification/phase-4.md`](verification/phase-4.md) và `docs/proof/phase-4/`.

## Giới hạn đã biết
- **Benchmark render offscreen:** client chơi thật vẽ bằng canvas trên trình duyệt; `chonoi.bench` render cùng cảnh
  lặn vào framebuffer RGB 1280×720 bằng rasterizer phần mềm Python (không mở cửa sổ, không đo GPU/trình duyệt).
  `load_ms` tính từ lúc nạp module bench (không gồm thời gian khởi động trình thông dịch).
- **Soak dùng bot tối giản:** đi trọn gather → quan → shop mỗi Ngày một cách tất định, không chơi tối ưu nên
  `earned` thấp; mục đích là kiểm độ bền và tính lặp.
- **Bật `burn` thay đổi quán so với lõi** (món chín quá 20 s bị cháy); tắt bằng cách bỏ `burn` khỏi `extensions` và
  đặt `burn_s: null`.
- Phụ đề SFX và Lao xua / Vợt hút / Rắn Hổ Mây / Chợ / Sổ tay / Dòng nước lũ / Khách đặt trước: **chưa làm**.
- Màn hình menu / giới thiệu ngày / pause của client được kiểm bằng chơi tay; `tools/hud_check.py` chỉ kiểm phần vẽ HUD.
- Tag `phase-1`, `phase-3` gắn sau mốc giờ của phase tương ứng (ghi trong `docs/verification/`).

## Nhóm
NgChiVinh (Integrator) · TrungHieuPh (PO) · 22520160 · HoangQuan23112004 · truclamld (Scrum/Release) · khoa-asta (QA lead).
Phân công từng phase: [`TEAM.md`](../TEAM.md). Lịch sử thay đổi: [`CHANGELOG.md`](../CHANGELOG.md).
