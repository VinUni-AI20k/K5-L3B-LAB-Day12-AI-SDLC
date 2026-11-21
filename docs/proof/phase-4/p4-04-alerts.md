# Bằng chứng P4-04: ba cảnh báo dễ nhận biết và chế độ tương phản cao

Người làm: C (Cuongngucuteee), Claude Code hỗ trợ. Ngày 2026-11-21. AC-P4-04 trong `docs/plan/phase-4.md`.

## Cảnh báo (tính ở `chonoi/alerts.py`, chỉ đọc snapshot)

| id | Khi nào bật | Mức | Hiện gì (biểu tượng + chữ, không chỉ màu) |
|---|---|---|---|
| `monster_near` | dưới nước và Cá Sấu cách `<= detect_radius` của loài (contract), hoặc đang đuổi | danger | ⛔ 🐊 CÁ SẤU GẦN — M1 cách 4 m, tránh xa! |
| `oxygen_low` | dưới nước và oxy `<= 25%` oxy tối đa; oxy 0 là mức danger (đang ngạt) | warning / danger | ⚠ 🫁 OXY SẮP HẾT — còn 7 s, nổi lên! |
| `customer_angry` | khách đang chờ món còn `<= 25%` kiên nhẫn | warning | ⚠ 😠 KHÁCH SẮP GIẬN — C1 bàn T2 còn 12 s |

Hai mốc 25% là giả định (`docs/clarify.md` #14, chờ PO). Cảnh báo chỉ có trong `GET /state` của `chonoi.live` (trường `alerts`), không đổi JSONL headless.

## Tương phản cao

Phím **H** (cả ở menu) hoặc mở `http://127.0.0.1:8000/?hc=1`; nhớ lựa chọn trong trình duyệt nếu cho phép. Nền đen, nước xanh đen, chữ trắng đậm cỡ tối thiểu 13, chữ nhấn màu vàng, mọi hình tô có viền trắng 2 px, băng cảnh báo nền đen viền vàng 3 px.

## Kiểm bằng mắt (Chrome headless chụp máy chủ `chonoi.live` thật)

| Ảnh | Lệnh | Thấy gì |
|---|---|---|
| `p4-04-gather.png` | `python3 -m chonoi.live --mode gather --scenario docs/proof/phase-4/p4-04-gather.scenario.json` | 2 băng: Cá Sấu gần (danger, trên) và oxy sắp hết (warning) |
| `p4-04-gather-hc.png` | như trên, mở `/?hc=1` | cùng 2 cảnh báo ở chế độ tương phản cao |
| `p4-04-quan-hc.png` | `python3 -m chonoi.live --mode quan --scenario docs/proof/phase-4/p4-04-quan.scenario.json`, mở `/?hc=1` | khách sắp giận ở bàn T2 |

Lỗi tìm ra khi xem ảnh và đã sửa: dòng nhắc "H: tương phản cao" đè lên ô giỏ ở góc trái dưới, nay chuyển sang góc phải.

## Test

`tests/test_p4_alerts.py` (14 test): mốc đúng biên của từng cảnh báo (bằng mốc thì bật, quá 1 tick thì không), oxy 0 là danger, không cảnh báo khi ở mặt nước, Cá Sấu đang đuổi ở xa vẫn bật, danger xếp trước; chạy thật một lần lặn (bật đúng lúc oxy = mốc) và một ca quán có hàng (khách C1 chạm mốc 900 tick ở tick 2820); không có cảnh báo ở Shop hay khi đã kết thúc; `GET /state` có `alerts` còn snapshot headless thì không; trang có phím H, `?hc=1`, băng cảnh báo.

Phá thử `chonoi/alerts.py` 9 cách (đổi `<=` thành `<` ở 3 mốc, bỏ kiểm mặt nước, bỏ điều kiện đang đuổi, bỏ lọc khách đang chờ, oxy 0 không thành danger, đảo thứ tự danger, không tắt khi kết thúc): **cả 9 bị test bắt**.

```
PYTHONPATH=tests:. python3 -m unittest discover -s tests   -> Ran 278 tests ... OK
```

## Chưa kiểm

- Chưa bấm phím H bằng bàn phím thật (ảnh dùng `?hc=1`); phím đọc trong code và `node --check`.
- Chưa đo độ tương phản theo WCAG bằng công cụ; chọn màu đen/trắng/vàng là cặp tương phản cao nhất.
