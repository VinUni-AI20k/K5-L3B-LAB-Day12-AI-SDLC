# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:** lõi `gather` + `quan` đúng PRD-0 mục F/G, headless tất định, smoke hai tiến trình qua file kho chạy trên `main`, tag `phase-1` trước 1:00.
- **Mốc:** 0–15 chia vai + chốt hợp đồng kho · phút 20 rà lát chậm · trước phút 25 xuất file kho thật · 45–55 smoke + ma trận + tag.

## Việc / người / phụ thuộc (repo tắt Issues nên theo dõi tại đây)

| Lát | Người | Tiêu chí chấp nhận | Phụ thuộc |
|---|---|---|---|
| 0 | nglngnguyen-gh | **AC-P1-01** `game.contract.json` đủ khóa preset v1.0, `team`=`stoneasterisk`, `team_size`=5 · **AC-P1-02** hợp đồng kho `{"items":{kind:int≥0}}` + ví dụ ở `docs/contracts/`, sự kiện + giao diện sim↔UI · **AC-P1-03** README chạy từ clone sạch ≤ 3 lệnh, điều khiển, cách tính điểm, lệnh test · ≥ 2 skill ở `.agents/skills/` | — (làm đầu tiên) |
| 1 | LyLe10 | **AC-P1-10** bơi ramp ≤ 6 tick, chặn biên, triệt vận tốc ra ngoài · **AC-P1-11** `dive`/`surface` khi đổi phía `d = 0.5` · **AC-P1-12** oxy theo `d` cuối bước: mặt nước +6 (kẹp, reset ngạt), dưới nước −1 (kẹp 0), `oxygen_empty` khi từ dương về 0 · **AC-P1-13** ngạt: chạm 0 ở t → `choke` ở t+59, −1 Máu; nổi đúng bước đó thì không ngạt · **AC-P1-14** Máu 0 → `faint` (`lost` LIFO) → `gather_end fainted`, kho rỗng · **AC-P1-15** giỏ LIFO, trần `hold_capacity` | Lát 0 (tên sự kiện) |
| 2 | BLong1501 | **AC-P1-20** `interact`: bến trước (đúng mép vẫn `docked`), rồi chỉ hái ở mặt nước, nút ready gần nhất hòa theo id, `regrow_ticks`=1200, `node_regrown` · **AC-P1-21** `catch` khi hết hồi + dưới nước: đàn gần nhất, thêm đủ yield, xóa đàn, hồi 30 tick; thiếu chỗ → `hold_full` (`required`,`free`), giữ đàn, không thử đàn khác · **AC-P1-22** hết giờ → `time`; hành động hợp lệ ở bước cuối vẫn vào kho · **AC-P1-23** `--inventory-out` ghi đúng một lần, nguyên tử, khớp `gather_end.inventory`; chạm `--ticks` trước khi xong thì không ghi | Lát 1 (`_at_surface`, giỏ) |
| 3 | minhtriet061203 | **AC-P1-30** khách theo lịch `first_customer_tick`=120 rồi mỗi 900 tick theo `phase_tick`; bàn trống id nhỏ nhất; không có bàn thì bỏ lượt · **AC-P1-31** chọn đều theo seed trong món đủ kho khả dụng (tồn − giữ), không có → `no_dish` · **AC-P1-32** giữ chỗ đúng công thức khi gọi; khách rời thì nhả giữ, bỏ món của đơn · **AC-P1-33** kiên nhẫn 3600 tick, về 0 → `customer_left patience`, uy tín −0.5, kẹp [0,5] · **AC-P1-34** fixture `quan.customers` + kiểm mâu thuẫn (mã 2) ở `scenario.py` | Lát 0 (kho mẫu) |
| 4 | len2412 | **AC-P1-40** tối đa một `interact`/bước, chọn theo (khoảng cách, bếp trước bàn, id) · **AC-P1-41** bếp idle lấy đơn reserved cũ nhất, tiêu nguyên liệu giữ, `cook_started` (`items` theo kind, `base_price`) → `dish_ready` · **AC-P1-42** bếp ready → tay trống (`carry_limit` 1), `dish_picked` · **AC-P1-43** giao đúng `order_id` → `served`, boa = floor(giá × 0.2) nếu kiên nhẫn ≥ 50%, ăn 600 tick → `paid finished_eating`, boa dương +0.2 uy tín · **AC-P1-44** hết ca: khách đang ăn trả ngay (`closing`), khách chờ rời không trừ uy tín, `quan_end` · **AC-P1-45** điểm = earned + 100 × floor(reputation) | Lát 3 (khách, đơn) |
| QA | nglngnguyen-gh | **AC-P1-50** smoke hai tiến trình: `dock.json` → snapshot quán tick 0 có `stock:{"bong_sung":2,"ca_loc":1}` · **AC-P1-51** cùng seed → JSONL + kho giống từng byte · **AC-P1-52** cờ/inputs/scenario sai → mã 2 trước khi ghi output · **AC-P1-53** HUD buổi sáng/tối đọc được (`chonoi.live`) — BLong1501 làm sau lát 2 | Lát 1–4 |
| Mọi người | cả nhóm | `docs/members/<handle>.md`, `docs/ai-usage-log.md`, một dòng `docs/standup.md`, ≥ 3 commit có nội dung | — |

## Rủi ro
- Nhóm 5 người phải xong **≥ 1 mục Mở rộng** trong cả buổi lab. Phần paste PRD chưa có danh sách mục mở rộng; PO xem trên lab board rồi chọn một mục gọn.
- Lát 4 phụ thuộc đơn của lát 3 → chốt trước cấu trúc `customer`/payload món (`order_id`,`dish_id`,`base_price`) để làm song song bằng fixture.
- Hai người cùng sửa `gather.py` và hai người cùng sửa `quan.py` → gộp lát 1/3 trước, lát 2/4 rebase; chỗ mơ hồ hỏi Anh Năm, ghi `docs/clarify.md`.
