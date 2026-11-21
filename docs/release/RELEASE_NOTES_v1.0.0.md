# Quán Ăn Chợ Nổi — v1.0.0

Nhom001 · K5-L3B Lab Day 12 (AI SDLC) · Test Contract v1.3

Út Sen lặn sông bắt cá bằng lao móc, hái rau trên mặt nước, tối mở quán trên nhà bè và phục vụ khách theo kế hoạch 5 Ngày của Má Tư.

## Có gì mới

**Hợp đồng v1.3 (TICKET-04)**
- Khóa gốc `bench_cmd` và `soak_cmd` trong `game.contract.json`; thiếu một trong hai thì hợp đồng bị từ chối.
- Bench: đo FPS bản GUI (1280×720, Chrome headless) → `{avg_fps,p1_low_fps,frames,measured_s,load_ms}`.
- Soak: một tiến trình chạy 10+ Ngày liên tiếp, Ngày > 5 lặp kế hoạch D1–D5; tiền, uy tín, nâng cấp và id vật phẩm giữ xuyên suốt.
- Không đổi schema kho/scenario/event so với v1.2.

**Bản chơi GUI (trình duyệt, không cần backend)**
- Video mở đầu, màn hình tiêu đề với ảnh bìa của nhóm, vòng Ngày có bến làm trung tâm.
- Lặn: lao móc, săn cá có máu, Cá Sấu và boss Cá Tra Dầu, radar cá, độ tươi, địa hình đáy sông và dòng nước.
- Quán nhà bè: bảng thực đơn (chọn món, số suất), 2 bếp / 4 bàn, nhân viên, trò chuyện với khách, Bà Tư.
- Điện thoại (phím T), Chợ Chú Sáu mua/bán, tổng kết 5 Ngày.
- Chế độ tương phản cao (phím H), tắt tiếng (M), tạm dừng (Esc/P).

Danh sách đầy đủ theo phase: `CHANGELOG.md`.

## Cách chạy

**Từ file zip của Release** (macOS/Linux, Python ≥ 3.9):

```bash
unzip quan-an-cho-noi-v1.0.0.zip && cd quan-an-cho-noi-v1.0.0
./run.sh            # mở http://127.0.0.1:8099/client/index.html; Ctrl+C để dừng
```

Trên macOS có thể bấm đúp `run.command` (lần đầu: chuột phải → Open). Đổi cổng: `PORT=8100 ./run.sh`.

**Từ mã nguồn** (3 lệnh):

```bash
git clone https://github.com/workcaominh-gif/K5-L3B-LAB-Day12-AI-SDLC-Nhom001.git
cd K5-L3B-LAB-Day12-AI-SDLC-Nhom001
python3 -m http.server 8099 --bind 127.0.0.1    # rồi mở http://127.0.0.1:8099/client/index.html
```

**Test và headless** (từ mã nguồn; zip không kèm `tests/`):

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests
python3 -m chonoi.headless --mode day --days 5 --seed 7 --ticks 120000 --out week.jsonl
python3 tools/bench.py --seed 42 --duration 30 --out bench.json   # cần Chrome/Chromium
python3 tools/soak.py --seed 7 --days 10 --out soak.json
```

Điều khiển: WASD/mũi tên di chuyển · Shift bơi nhanh · Space/chuột bắn lao · E tương tác · I túi đồ · T điện thoại · C đóng quán sớm · Esc/P tạm dừng · M tắt tiếng · H tương phản cao.

## Hạn chế đã biết

- Bản GUI `client/` là phần sáng tạo của nhóm, viết lại luật bằng JavaScript; **nguồn đúng cho chấm tự động là sim headless** `chonoi/`. Một số số liệu (giá, thời gian, khách) trên GUI có thể lệch so với headless.
- GUI chỉ chơi bằng bàn phím + chuột trên máy tính; chưa hỗ trợ màn hình cảm ứng hay tay cầm. Màn hình nhỏ hơn 1280×720 có chữ HUD nhỏ.
- Phải mở qua HTTP (`run.sh` hoặc `http.server`); mở trực tiếp `index.html` bằng `file://` sẽ trắng màn hình.
- Tiến trình và cài đặt (tương phản cao, tắt tiếng) lưu trong `localStorage` của trình duyệt; xóa dữ liệu trang là mất.
- Cửa sổ khung `python3 -m chonoi.live` của starter chưa có mode `day` và chưa map Esc/P.
- Một số giả định trong `docs/clarify.md` (C-P2-B02/B04/B05) chưa được giảng viên xác nhận; test ẩn có thể hiểu khác.
- Video mở đầu tạo bằng Meta AI và còn watermark; giấy phép asset chi tiết ở `CREDITS.md`.

## Ghi công

Asset CC0 / CC-BY 4.0 / MIT từ OpenGameArt và Kenney, ảnh bìa của nhóm, video Meta AI — xem `CREDITS.md` và `client/assets/manifest.json`. Mã nguồn: MIT (`LICENSE`).
