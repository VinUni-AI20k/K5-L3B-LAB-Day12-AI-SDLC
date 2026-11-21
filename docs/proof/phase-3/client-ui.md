# Bằng chứng UI TICKET-03

Nhánh `codex/client-ui-phase-3`, nền `881c4c4`. Dùng `MockSimV12Adapter` để phát các tình huống trong vòng 5 ngày, với cấu hình độ tươi từ `chonoi/web/phase3.preview.json`. Checkout hiện khai v1.1 và chưa khai báo mở rộng `current` hoặc `reservations`.

## Phạm vi thay đổi

| Tệp | Ảnh hưởng |
|---|---|
| `inventory-view.js`, `app.js` | Đọc kho đếm hoặc kho cá thể, lọc ID giữ chỗ, hiển thị giỏ và kho, giá chốt và toast. |
| `campaign.js`, `index.html`, `styles.css` | Hiển thị kho khi chuyển ca và trong Shop. Giữ bố cục của các màn hình còn lại. |
| `art.js`, `scenes.js` | Vẽ phù sa, bọt nước và nhãn đơn thiếu hàng tươi. |
| `phase3-preview.js`, `phase3.preview.json`, các adapter mẫu cũ | Tình huống v1.2, dữ liệu biên 30%, độ tươi lẻ, tương thích các bản xem trước. |
| `live.py` | Phục vụ module UI và đưa thông tin phiên bản, độ tươi nếu có vào `/config`. |

## Kết quả

- Chrome headless ở 1280×720 đi hết 5 ngày mẫu. Kiểm ca có cá linh 28,5% trong giỏ, bông súng đang giữ chỗ từ 30% xuống 29,75%, menu lọc hàng ươn, giá đã chốt 103k và Pause. Đếm Canvas trong 1,4 giây mỗi cảnh cho kết quả khoảng 60 FPS.
- Node kiểm ngưỡng 60%, 30%, 29,99%, ID giữ chỗ bị lặp, số lượng ở cả hai schema, thống kê và dãy ID đã sắp. Snapshot đóng băng vẫn được đọc mà không bị sửa.
- Chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -q` trên Python 3.12 với `python3.exe` tạm và localhost. Cả nền và bản UI chạy 54 test, cùng đạt 51. Ba lỗi đã có ở nền gồm fixture `hold` của ca quái đánh, CLI từ chối `--days 2` và input headless từ chối `pause`.
- Smoke bàn giao kho qua `python3 tools/phase1.py smoke` đạt 1/1.
- Chạy `python -m chonoi.live --mode gather` rồi chọn **Chơi**. Để chạy bản xem riêng, dùng `python -m http.server 8000 --bind 127.0.0.1` tại gốc repo và mở `http://127.0.0.1:8000/chonoi/web/?preview=3`.

## Đoạn CHANGELOG sẵn dán

> **Phase 3 · UI:** Giỏ và kho cá thể dùng `{id, kind, fresh}`, còn đơn giữ chỗ tham chiếu ID. HUD tách hàng tươi, giữ chỗ và hàng ươn. Bếp, món trên tay và bàn hiển thị `base_price` đã chốt. UI vẫn đọc được kho đếm v1.1.
