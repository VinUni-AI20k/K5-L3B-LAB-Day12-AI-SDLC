# ADR-0001: Bảo quản món thừa khi chơi trực tiếp (Quán)

- Trạng thái: đề xuất, chờ cả nhóm xác nhận
- Ngày, người quyết: 2026-11-21, TV3 (daohiep2903) đề xuất cơ chế, TV4 (NTLam108) chỉnh cấu hình và thời gian

## Bối cảnh

Clarify Q7: khách hết kiên nhẫn và rời đi khi đơn của họ đang nấu hoặc đã chín. Ở headless, món đó làm kẹt bếp, hoặc làm kẹt tay người chơi tới hết ca (`docs/proof/phase-1/tv4-quan.md`, kịch bản `orphan`). Luật headless phải theo mục F nên chờ PO xác nhận. Trong lúc đó, chế độ chơi trực tiếp cần một cách gỡ để chơi thử được.

## Các lựa chọn đã cân nhắc

1. Bỏ món, bếp về `idle`.
2. Giữ món ở bếp để dùng lại cho khách sau gọi cùng món, quá hạn thì hủy.
3. Cho phép bỏ món trên tay.

## Quyết định

Chọn phương án 2, **chỉ bật khi chơi trực tiếp** (`chonoi.live`). Headless giữ nguyên hành vi cũ (`leftover_lifetime_ticks = None`) để không đổi output của Test Contract.

- Số liệu nằm trong `game.contract.json`, khối `tuning.live`:
  - `quan_shift_game_hours: 3`: một ca Quán `quan.duration_s` = 180 giây thật ứng với 3 giờ trong game.
  - `leftover_lifetime_game_minutes: 30`: món thừa sống 30 phút game.
- Quy đổi: 1 phút game = 180 / (3 × 60) = 1 giây thật. Vậy 30 phút game = 30 giây = 30 × 60 = **1800 tick**, tính từ lần bưng đầu.
  Bản đầu tiên tính 30 phút ngoài đời = 108 000 tick, dài hơn cả ca (10 800 tick), nên món không bao giờ hết hạn.
- Logic quy đổi đặt trong `QuanSim.enable_live_leftovers()`. `chonoi/live.py` chỉ thêm một lời gọi trong `_reset()`.

## Hệ quả

| File | Thay đổi |
|---|---|
| `game.contract.json` | thêm khối `tuning.live`; không đổi khóa cũ. `contract.validate_tuning` bỏ qua khóa này nên headless không đổi |
| `chonoi/live.py` (khung của giảng viên) | thêm một dòng gọi `enable_live_leftovers()` cho mode `quan`. Lý do: sim không biết mình chạy live hay headless |
| `chonoi/sim/quan.py` | `enable_live_leftovers()`, bảo quản, dùng lại và hủy món (`dish_stored`, `dish_discarded`) |
| `chonoi/quan-live.json` | xóa; số liệu chuyển vào contract |
| `tests/test_quan_leftovers.py` | thời hạn kỳ vọng tính theo quy đổi (1800 tick) và phải ngắn hơn một ca |

Khi mục F có câu trả lời cho Q7, nhóm quyết định có đưa phương án nào vào headless hay không; khi đó cập nhật ADR này.
