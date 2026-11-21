# T461 — SFX WebAudio + phụ đề SFX

- Thời điểm: 2026-11-21T14:10:00+07:00
- File: `chonoi/web/index.html` (OscillatorNode/GainNode, không asset; `pixi.min.js` local)
- Phím: **M** bật/tắt âm · **N** bật/tắt phụ đề (mặc định phụ đề bật; lưu `localStorage` `chonoi_sfx_sound` / `chonoi_sfx_captions`)

## Bảng SFX ↔ event ↔ phụ đề

| Event / cờ | Phụ đề | Ghi chú âm (≤400 ms) |
|---|---|---|
| `fish_caught` | `[♪ tõm] bắt cá` | 2 tone sine/triangle |
| `gather` | `[♪ xột] hái rau` | square ngắn |
| `monster_hit` / `choke` | `[♪ rầm] Cá Sấu cắn!` | sawtooth trầm |
| `spoiled` | `[♪ ực] hàng ươn` | triangle thấp |
| `served` | `[♪ chát] phục vụ` | square cao |
| `paid` (+ tip) | `[♪ leng] tiền vào` / `tiền + boa Xk` | 2 chirp |
| `bought` | `[♪ keng] mua nâng cấp` | sine |
| `buy_failed` | `[♪ bụp] mua lỗi` | sawtooth |
| `day_start` | `[♪ ting] ngày mới` | 2 note |
| `oxygen_empty` | `[♪ ục] hết hơi` | sine dài |
| `faint` | `[♪ ịch] ngất!` | sawtooth |
| `customer_left` | `[♪ hự] khách bỏ đi` | triangle |
| cờ thủy quái gần | `[♪ ù] thủy quái gần!` | edge (không lặp frame) |
| cờ khách sắp giận | `[♪ hứ] khách sắp giận` | edge |

Quy tắc: dedupe theo `tick|name|id`; lần poll đầu (live) chỉ **prime** — không phát event cũ khi tải trang; **pause** → đánh dấu seen, không phát; phụ đề vẫn hiện khi âm tắt.

## Cách kiểm

```bash
python3 -m chonoi.live --mode gather --port 8793
# Âm tắt + phụ đề: demo tuần tự
open 'http://127.0.0.1:8793/?demo=sfx'
# hoặc freshness (có spoiled/fish_caught sẵn)
open 'http://127.0.0.1:8793/?demo=fresh'
# Phím M tắt âm, N bật phụ đề; dải phụ đề đáy giữa, chữ ≥ 18 px (HC: nền đen + chữ #ffe600)
```

`?demo=sfx` buộc `soundOn=false` (không ghi localStorage) và phát lần lượt ~14 event mẫu mỗi 0.9 s.

## Kết quả kiểm (worker)

- `node --check` (script trong index.html): **OK**
- `PYTHONPATH=tests:. python3 -m unittest discover -s tests`: **171 OK** (4 skipped); `tests.test_live` **OK**
- Grep: không `size` < 18; không URL ngoài
- Live: `GET http://127.0.0.1:8793/?demo=sfx` → **200**; HTML có `processSfxFromEvents`, `drawSfxCaptions`, `[♪ tõm]`, `AudioContext`
- Ảnh chụp: không (Playwright thiếu browser binary trên máy) — kiểm tay bằng `?demo=sfx` với âm tắt: phụ đề lần lượt hiện ở đáy giữa
- Server đã tắt sau khi thử

## Kiểm tay bởi lead (TV6)
- Mở `?demo=sfx` với "Âm: TẮT": dải phụ đề đáy hiện đúng lúc ("[♪ ục] hết hơi", "[♪ ịch] ngất!"), nhật ký sự kiện cùng lúc; nút "Âm" và "CC" ở góc trên phải.
- Đã sửa lỗi demo: `startSfxDemo` gán nhầm biến `sound` thay vì `snap` nên màn demo kẹt "Đang tải dữ liệu…".
- Lưu ý nhỏ: dòng nhật ký sự kiện trên cùng bên phải hơi chạm nút CC khi có sự kiện mới nhất.
