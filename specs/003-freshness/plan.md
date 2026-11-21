# Implementation Plan: Phase 3 — kho cá thể + độ tươi (v1.2)

**Branch**: không tạo (`tv6/phase-1-team-ai`) | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

## Summary
Đổi kho đếm → kho cá thể `{id,kind,fresh}`, thêm hao tươi (giỏ 0.5/s, quán 0.25/s), `spoiled` ở ngưỡng 30, giữ chỗ theo id + thử giữ lại, giá chốt theo tươi; bàn giao qua file và trong `day`. Thứ tự tích hợp: **adapter/schema trước** → Lặn ∥ Quán ∥ HUD → day → bật v1.2 → regression.

## Technical Context
Python 3 stdlib · `unittest` · CLI headless 60 Hz + web tĩnh · Ràng buộc: tất định; số từ `freshness` trong contract; fresh nội bộ số nguyên (240 đơn vị/điểm); `sort_by_id`.
**Lịch đề**: 0–7 tác động + quyết định schema · 7–25 build song song, phút 20 smoke kho · 25–32 bật v1.2, smoke 2 tiến trình + day, regression, CHANGELOG, tag · 32–35 dự phòng (tag trước 2:30).

## Constitution Check
| Nguyên tắc | Đánh giá |
|---|---|
| I. Contract-First | ĐẠT — schema kho đổi có báo nhóm, ghi `docs/contracts/` + CHANGELOG (breaking change) |
| II. Deterministic | ĐẠT — số nguyên ở ngưỡng; chọn cá thể theo (units desc, id) |
| III. Headless-First | ĐẠT — mọi AC qua headless; HUD chỉ đọc |
| IV. Test-First & Evidence | ĐẠT — AC-P3-01…23, `docs/proof/phase-3/`, `docs/verification/phase-3.md` |
| V. No Invented Requirements | ĐẠT phần lớn — GIẢ ĐỊNH: tên `order_status`, làm tròn khi ghi file, id nạp không dạng `I<n>` |
| VI. Small Slices | CÓ ĐIỀU KIỆN — đụng file khung (`inventory, contract` TV1; `scenario, headless, runner` khung TV6) |

## Project Structure
```text
specs/003-freshness/ spec · plan · research · data-model · quickstart · tasks · analysis · contracts/{inventory-v1.2, events-v1.2}.md
chonoi/inventory.py   # TV1: read/write v1.2, chọn theo version, mã 2 kho đếm
chonoi/contract.py    # TV1: validate `freshness`, "1.2"
game.contract.json    # TV1: freshness + "1.2" (bật khi hai đầu sẵn sàng)
chonoi/scenario.py    # khung TV6: hold/stock cá thể, reserved mảng id, id duy nhất, reserved hợp lệ
chonoi/headless.py    # khung TV6: đọc kho theo version
chonoi/runner.py      # khung TV6: bộ cấp id cá thể toàn cục, bàn giao day cùng tick, ghi kho v1.2
chonoi/sim/gather.py  # TV2 (+TV1): Item, hao, spoiled, LIFO cá thể
chonoi/sim/quan.py    # TV3: giữ chỗ theo id, thử giữ lại; TV4: hao kho, base_price, cook_started.items
chonoi/web/index.html # Cursor (TV6): HUD độ tươi, nhãn ươn
tests/, docs/verification/phase-3.md, docs/proof/phase-3/, CHANGELOG.md   # TV5
```

## Thiết kế chính
- **Item nội bộ**: `{"id","kind","u"}` (u = units); snapshot/kho xuất `fresh = u/240`.
- **Hao (gather)**: đầu bước, sau đồng hồ: với mỗi item trong hold theo id: `u = max(0, u−2)`; nếu qua ngưỡng → `spoiled`. Item lấy trong bước hiện tại chưa hao (thêm sau bước hao).
- **Hao (quán)**: sau đồng hồ/timer: mọi item trong stock (kể cả đang giữ) `u−1`; phát `spoiled` theo id; rồi gom đơn có phần giữ vừa ươn, sắp `(order_tick, table_id)`, nhả + `_reserve` một lần → `unfulfillable` nếu thiếu.
- **Giữ chỗ** `_reserve(order)`: khả dụng = stock − đã giữ − ươn; mỗi kind lấy n item theo `(−u, id)`.
- **Nấu**: tiêu đúng `reserved`, `base_price = floor(price·Σu / (n·240·100))`, `cook_started.items` sắp (kind, id).
- **Adapter**: `read_inventory(path, version)`; v1.2 → list Item; v1.0/1.1 → đếm (giữ tương thích trong lúc chuyển). Ghi v1.2 sắp id, fresh float đầy đủ.
- **day**: runner giữ `ItemIds`; `gather_end` → `QuanSim(inventory=items)` cùng tick, không hao; Ngày kế cấp id mới cho mẫu `gather.hold`.

## Complexity Tracking
| Vi phạm | Vì sao | Thay thế bị loại |
|---|---|---|
| Sửa file khung `inventory, contract, scenario, headless, runner` | Schema kho và validate bị khung chặn trước sim | Không có đường vòng; chủ file theo bảng tác động (TV1, khung TV6), báo nhóm, ghi AGENTS.md/CHANGELOG |
