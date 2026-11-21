# Bằng chứng P3-06: HUD độ tươi, hàng ươn, đơn bị ảnh hưởng (AC-P3-05)

Người làm: C (Cuongngucuteee), Claude Code hỗ trợ. Ngày 2026-11-21. Xây trên P3-02 (PR #43: kho cá thể, `tuning.freshness`, `chonoi/freshness.py`).

## Làm gì

- `chonoi/freshness_view.py` (chỉ đọc snapshot): gom cá thể đang hiển thị (giỏ khi Lặn, kho khi Quán hoặc Shop) với `fresh` và `spoiled` (ươn khi `fresh < spoil_below`, cùng quy tắc `Freshness.is_spoiled`), `spoiled_count`, `min_fresh`, và `affected_orders` ở quán: khách đang chờ có hàng giữ chỗ đã ươn (`spoiled_reserved`, kèm id cá thể) hoặc đơn không làm được (`unfulfillable`).
- `chonoi/live.py`: `GET /state` có `freshness_hud` khi snapshot có cá thể (contract 1.2); snapshot 1.1 thì không có trường này và HUD giữ nguyên cách hiển thị cũ.
- `chonoi/web/index.html`: ô giỏ có thanh độ tươi, cá thể ươn phủ tối và dấu ✕; dòng giỏ/kho ghi số ươn và độ tươi thấp nhất; nhãn "⚠ hàng ươn" / "⚠ thiếu hàng" cạnh khách bị ảnh hưởng và danh sách đơn bị ảnh hưởng ở góc trái dưới; chạy cả với chế độ tương phản cao của P4-04.

## Dạng snapshot mà HUD đọc (theo `docs/contracts/README.md` và `docs/plan/phase-3.md`)

`hold` (gather), `stock` (quán, Shop) là mảng `{id, kind, fresh}`; `customers[].reserved` là mảng cá thể hoặc mảng id. A (gather) và B (quán) chưa đổi sim sang cá thể nên các ảnh dưới dùng snapshot dựng bằng adapter của P3-02 (`hold_to_individuals`, `counts_to_individuals`) qua `p3-06-demo.py`.

## Kiểm bằng mắt (Chrome headless chụp máy chủ `chonoi.live` thật, snapshot cá thể giả lập)

```
python3 docs/proof/phase-3/p3-06-demo.py "$PWD"    # gather ở cổng 8781, quán ở 8782, chạy 60 s
```

| Ảnh | Thấy gì |
|---|---|
| `p3-06-gather.png`, `p3-06-gather-hc.png` | giỏ 5 cá thể: thanh độ tươi dưới ô, 2 ô ươn (28.9, 12) có ✕; dòng "tươi thấp nhất 12 · ✕ 2 ƯƠN (không nấu được)" |
| `p3-06-quan.png`, `p3-06-quan-hc.png` | kho "bông súng×2 (✕ 1 ươn)…"; C1 bàn T1 "⚠ hàng ươn" (giữ I4 đã ươn), C2 bàn T2 "⚠ thiếu hàng" (unfulfillable), C3 bàn T4 giữ I1 còn tươi nên không bị đánh dấu |

Lỗi tìm ra khi xem ảnh và đã sửa: nhãn "⚠ hàng ươn" của khách bàn T1 nằm ngay dưới bàn T3 nên đọc nhầm là của T3; nay đặt cạnh phải khách.

## Test

`tests/test_p3_hud_freshness.py` (9 test): ngưỡng ươn đúng biên (bằng `spoil_below` là chưa ươn, kém một đơn vị nhỏ nhất là ươn) và khớp `Freshness.is_spoiled` ở 4 mức đơn vị; đơn bị ảnh hưởng (giữ id ươn, giữ cá thể ươn, unfulfillable; khách đang ăn và khách giữ hàng tươi không tính); Shop không có đơn; snapshot 1.1 thật (gather, quán) không có HUD độ tươi; contract thiếu `freshness` thì không có; `GET /state` chỉ có `freshness_hud` khi có cá thể; trang đọc được cả hai dạng.

Phá thử `chonoi/freshness_view.py` 9 cách: **8 bị bắt**. Cách còn lại ("lấy `hold` cả khi ở quán") là đột biến tương đương: snapshot quán không có `hold` và snapshot gather không có `stock`, nên không đổi hành vi. Một cách ban đầu sống sót ("tính đơn bị ảnh hưởng cả ở Shop") đã được bắt sau khi thêm khách vào test Shop.

```
PYTHONPATH=tests:. python3 -m unittest discover -s tests   -> Ran 311 tests ... OK
```

## Chưa kiểm / phụ thuộc

- Chưa chạy với sim gather, quán thật ở contract 1.2 (chờ A, B và việc bật v1.2). Khi họ xong, cần mở `chonoi.live` xem lại; nếu tên trường snapshot khác hợp đồng thì sửa `freshness_view.py`.
