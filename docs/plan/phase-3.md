# Kế hoạch Phase 3 — Ticket-03 "Mùa Nước Nổi" (1:55–2:30, 35 phút)

Test Contract **v1.2** · hạn tag `phase-3` 2:30. Chia việc theo vai trong [`TEAM.md`](../../TEAM.md), dựa trên phần QA (tiepnnk01-10) đã làm ở nhánh `feat/p3-qa`.

> **Nguồn yêu cầu:** [`docs/prd/phase-3.md`](../prd/phase-3.md) (toàn văn Ticket-03, PO đã chép). Plan đã đối chiếu ticket; quyết định PO ở `docs/clarify.md` #15–#19.

## 0. Hiện trạng
| Ở đâu | Có gì |
|---|---|
| `main` (`66a0ad0`) | Phase 2: 178 test OK. Cá bơi/sinh xong, lỗi tốc độ chéo và fixture `test_lat2` đã sửa (`00668ec`) |
| `feat/p3-qa` (Tiệp, **chưa merge**) | 28 test hộp đen `tests/test_fresh_p3.py` (`@pending`, chạy thật bằng `QA_STRICT=1`, hiện 27/28 đỏ); ma trận `docs/verification/phase-3.md` (AC-P3-01…21); `CHANGELOG.md` nháp breaking change; HUD độ tươi đọc được cả v1.1 lẫn v1.2 |
| **Nợ Phase 2** | **chưa có tag `phase-2`**; burn (I-1) bị `contract.py` chặn; UI Phase 2 (AC-P2-08) chưa có; `docs/verification/phase-2.md` cần chạy lại ở commit gắn tag |
| **Chưa ai nhận** | schema/adapter v1.2 (`inventory.py`, `contract.py` khóa `freshness`, `scenario.py` mảng cá thể); chọn mở rộng Phase 3 (Khách đặt trước / Dòng nước lũ) |

## 1. Thay đổi cốt lõi v1.2 (tóm tắt — đối chiếu Ticket-03)
- Kho đếm theo loại → **kho cá thể** `{id, kind, fresh}`; id `I1, I2…` theo thứ tự vào giỏ, không tái dùng.
- `tuning.freshness = {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`. Ươn khi `fresh < 30` (so **trước** làm tròn), sự kiện `spoiled` đúng một lần.
- Giỏ hao 0.5/s (hàng mới hao từ bước sau); kho quán hao 0.25/s kể cả hàng đang giữ chỗ; Shop và lúc bàn giao không hao; pause dừng hao.
- Hàng ươn vẫn chiếm ô giỏ, quán vẫn nhận, nhưng **không dùng để nấu**.
- Giữ chỗ **theo id**: cá thể tươi nhất, hòa id nhỏ; giữ chỗ vừa ươn → nhả hết, thử giữ lại **một lần**, không đủ → `unfulfillable`, khách vẫn chờ.
- `base_price = floor(giá niêm yết × TB fresh các cá thể dùng / 100)` chốt khi bắt đầu nấu; boa tính trên giá đã chốt.
- File kho `{"items": [{id, kind, fresh}]}`, kho rỗng `{"items": []}`; kho đếm cũ / scenario đếm cũ → mã 2.

## 2. Hợp đồng v1.2 — chốt chung ở phút 0–5 (s0ra1n0 chép vào `docs/contracts/README.md` khi lát 0 merge)
**A. Một module dùng chung `chonoi/items.py` (s0ra1n0 viết ở lát 0)** — lát 2, 3, 4, 5 chỉ gọi, không tự viết lại:

| Hàm | Việc |
|---|---|
| `new_item(ids, kind, fresh)` | cấp `{"id": ids.new("I"), "kind", "fresh"}` |
| `is_spoiled(item, tuning)` | `item["fresh"] < tuning["freshness"]["spoiled_below"]` (không làm tròn) |
| `decay(items, per_tick, tuning)` | trừ độ tươi (kẹp 0), trả danh sách cá thể **vừa** chuyển sang ươn, sắp theo id |
| `usable_by_kind(items, exclude_ids, tuning)` | đếm theo loại, bỏ hàng ươn và id đã giữ — thay cho `_available()` cũ |
| `pick_freshest(items, kind, n, exclude_ids, tuning)` | chọn `n` id tươi nhất chưa ươn, hòa theo `id_key`; thiếu → `None` |
| `to_file(items)` / `from_file(obj)` | đọc/ghi `{"items": [...]}`, kiểm schema, mã 2 cho kho đếm cũ |

**B. Định dạng:** cá thể là dict `{id, kind, fresh}`. **Trong mô phỏng `fresh` là số nguyên đơn vị, 240 đơn vị = 1 điểm tươi** (gợi ý của Ticket-03, clarify #16): gather −2/tick, quán −1/tick, ngưỡng ươn `30 × 240`; chỉ đổi ra số thực `units / 240` khi xuất snapshot/event/file kho, đọc vào thì `round(fresh × 240)`. `items.py` lo việc đổi này; người khác không tự nhân/chia; `hold`, `stock`, `lost`, `cook_started.items`, `gather_end.inventory.items` là **mảng cá thể**; `customers[].reserved` là **mảng id**. Mảng sắp theo id, trừ `hold`/`lost` theo thứ tự nhặt (LIFO cho `lost`).

**C. Sự kiện mới:** `spoiled {item_id, kind, location}`, `location` là `hold` (giỏ) hoặc `stock` (kho quán/Shop); vỏ event mang pha đang chạy. Phát đúng một lần khi đi từ ≥ 30 xuống < 30, theo id khi nhiều cá thể cùng ươn (clarify #15).

**D. Thứ tự một bước (đã chốt theo Ticket-03 "Thứ tự trong tick", clarify #17):**
- Quán: đồng hồ + timer (kiên nhẫn, nấu, ăn) → **hao kho thô + phát hết `spoiled` theo id (lát 4, `_tick_freshness`)** → **giữ lại đơn có cá thể vừa ươn, theo `order_tick` rồi id bàn (lát 3, `_retry_spoiled`)** → món chín/cháy theo id bếp → di chuyển + tối đa một tương tác → thanh toán, kiên nhẫn/đóng ca → còn giờ thì khách mới. Món chín, món trên tay không hao.
- Gather: đồng hồ, cooldown, hồi nút **và hao giỏ** ở đầu bước (hàng mới hái/bắt hao từ bước sau) → bơi, oxy, ngạt → quái/hit → bến trước hái → bắt cá → hết giờ → cá bơi/sinh.

**F. Bảng tác động và thứ tự tích hợp (Ticket-03 mục 3 yêu cầu)**

| Module | File cần đổi | Test giữ / đổi / thêm | Người phụ trách |
|---|---|---|---|
| Adapter + schema | `game.contract.json`, `chonoi/items.py` (mới), `chonoi/inventory.py`, `chonoi/contract.py`, `chonoi/scenario.py` (phần chung + gather) | **đổi:** `test_smoke_p1.py`, `test_lat0_v11.py`, `test_python_starter_units.py` (kho đếm → kho cá thể, file kho đếm giờ là mã 2); **thêm:** unit test `items.py` | s0ra1n0 |
| Lặn | `chonoi/sim/gather.py` (`_add_to_hold`, hao giỏ, `spoiled`, `lost`) | **đổi:** `test_gather_p1.py`, `test_gather_lat1.py`, `test_gather_lat1_p2.py`, `test_lat2.py`, `test_p2_lat2_fish.py` (giỏ là mảng cá thể); **thêm:** bỏ `@pending` nhóm gather của `test_fresh_p3.py` | mhoo40 (giỏ, hao), s0ra1n0 (`lost`) |
| Quán — khách | `chonoi/sim/quan.py` (`_reserve`, `_spawn_customers`, `_retry_spoiled`, `_init_customers`) | **đổi:** `test_quan_lat3.py`, `test_quan_p2.py`, `test_quan_p1.py` (phần khách); **thêm:** bỏ `@pending` `ReserveById`, `SpoilRetry`, `SpoiledNotCookable` | trongnghia2304 |
| Quán — bếp | `chonoi/sim/quan.py` (`_tick_freshness`, `_interact`, `_pay`), `chonoi/scenario.py` (`_validate_quan`) | **đổi:** `test_quan_lat4.py`, `test_quan_p1.py` (phần bếp); **thêm:** bỏ `@pending` `QuanDecay`, `PriceByFreshness` | nguyenhung1901 |
| day + Shop | `chonoi/sim/day.py`, `chonoi/sim/shop.py` | **đổi:** `test_day_p2.py`; **thêm:** bỏ `@pending` `DayHandoff` | tiepnnk01-10 |
| HUD / QA | `chonoi/web/index.html`, `CHANGELOG.md`, `docs/verification/phase-3.md` | **giữ** các test không đụng kho (Cá Sấu, cá bơi, pause, live) | tiepnnk01-10 |

**Thứ tự tích hợp để `main` luôn chạy được:**
1. `feat/p3-qa` (test còn `@pending`, HUD đọc cả hai schema) — không phá gì.
2. `feat/p3-lat0`: `items.py` + adapter + bật v1.2 **cùng lúc với** sửa các test kho đếm cũ trong cùng PR (không để `main` đỏ). Trong PR này gather/quán chỉ cần **chuyển dạng** (đếm ↔ cá thể) cho test xanh, chưa cần hao tươi.
3. `feat/p3-gather` và `feat/p3-quan` song song: thêm hao tươi, `spoiled`, giữ theo id, giá theo tươi; mỗi PR tự bỏ `@pending` test của mình.
4. `day` v1.2 (Tiệp) sau khi gather + quán xong.
5. Phút 20: smoke bàn giao file v1.2 (mẫu ticket: `hold` fresh 100, cập bến frame 0, `quan --inventory --ticks 0`, so id/kind/fresh sau một lần hao).

**E. Sở hữu file** giữ như contracts mục A của Phase 2; thêm: `chonoi/items.py` — s0ra1n0; `_add_to_hold` (giỏ) — **mhoo40** từ Phase 3.

## 3. Việc từng người (đánh dấu `[x]`, ghi commit/PR) — mã AC theo `docs/verification/phase-3.md` của Tiệp

### s0ra1n0 — lát 1, Integrator → **lát 0 v1.2**
- [ ] **Ngay:** chạy lại `verify.py --phase 2` trên `main`, cập nhật `docs/verification/phase-2.md`, đẩy tag **`phase-2`** (đã trễ hạn 1:55 — ghi trung thực)
- [ ] **Lát 0 v1.2, merge chậm nhất phút 15** (nhánh `feat/p3-lat0`):
  - [ ] `game.contract.json`: `contract_version: "1.2"`, `tuning.freshness`
  - [ ] `chonoi/items.py` (mục 2A) + unit test
  - [ ] `inventory.py` đọc/ghi kho cá thể, kho đếm cũ → mã 2; `contract.py` kiểm `freshness`
  - [ ] `scenario.py`: `gather.hold`, `quan.stock` là mảng cá thể, `reserved` là mảng id; id trùng / trỏ hàng ươn / sai công thức / dùng chung → mã 2 (phần chung; phần khách để lát 3)
  - [ ] Sửa test cũ dùng kho đếm (danh sách ở AC-P3-19 của Tiệp), ghi lý do trong commit
- [ ] Sau lát 0: `lost` của `faint` / `monster_hit` là mảng cá thể (LIFO)
- [ ] Nợ P2 nếu còn thời gian: I-1 burn (`contract.py` nhận `burn_s` hữu hạn khi bật `burn`)
- AC: P3-05 (phần `lost`), P3-06, P3-07, P3-17 (phần adapter), P3-21. Cuối phase đẩy tag `phase-3`.

### mhoo40 — lát 2 (giỏ cá thể)
- Làm ngay: [ ] đọc `tests/test_fresh_p3.py` (`Threshold`, `SpoiledOnce`, `GatherDecay`, `GatherIds`, `PauseFresh`), code trước theo chữ ký `items.py` đã chốt
- Sau lát 0 (nhánh `feat/p3-gather`):
  - [ ] Hái / bắt tạo cá thể `fresh = initial` qua `new_item`, id `I…` theo thứ tự vào giỏ; `hold_full` tính cả hàng ươn
  - [ ] Hao giỏ 0.5/s mỗi bước (hàng mới hao từ bước sau), `spoiled` đúng một lần, theo id
  - [ ] `gather_end.inventory` là mảng cá thể; snapshot `hold` là mảng cá thể
  - [ ] Bỏ `@pending` các test gather khi xanh (báo Tiệp)
- AC: P3-01, 02, 03, 04, 10.

### trongnghia2304 — lát 3 (khách, giữ chỗ), PO
- Làm ngay:
  - [x] **PO:** chép Ticket-03 vào `docs/prd/phase-3.md`; đối chiếu và sửa plan (mục 2B, 2C, 2D, bảng tác động 2F)
  - [x] **PO:** chốt 2 giả định Tiệp nêu + thứ tự bước + id trong day theo ticket → `docs/clarify.md` #15–#17, #19
  - [ ] **PO:** nhóm xác nhận ở standup: **không** làm mở rộng Phase 3 (clarify #18)
- Sau lát 0 (nhánh `feat/p3-quan`, chung với Hùng như Phase 2):
  - [x] `_reserve` giữ theo id bằng `pick_freshest`; khách mới giữ cá thể tươi nhất; fixture thiếu `reserved` cấp theo `order_tick` rồi id bàn
  - [x] `_spawn_customers` chọn món bằng `usable_by_kind` (bỏ hàng ươn, hàng đã giữ) → `no_dish` khi không món nào đủ
  - [x] `_retry_spoiled`: đơn có cá thể giữ vừa ươn → nhả hết, giữ lại một lần, thiếu → `unfulfillable`, khách vẫn chờ
  - [x] `_init_customers` kiểm `reserved` mảng id (id lạ, trỏ hàng ươn, sai công thức, dùng chung, kiểu cũ → mã 2)
  - [x] Test v1.2 của lát 3: `test_fresh_p3` (ReserveById, SpoilRetry, SpoiledNotCookable, FixtureValidation) 7/7 + `tests/test_quan_p3.py` 7 test, bằng chứng `docs/proof/phase-3/lat3.txt`
  - [ ] Khi bật v1.2 trên `main`: chuyển `tests/test_quan_lat3.py`, `tests/test_quan_p2.py` sang kho cá thể (chạy cùng PR bật v1.2)
- AC: P3-12, 13, 16, 17 (phần khách).

### nguyenhung1901 — lát 4 (bếp, tiền)
- Làm ngay: [ ] đọc `QuanDecay`, `PriceByFreshness` trong `test_fresh_p3.py`; nợ P2: mục "Mở rộng: burn" trong README
- Sau lát 0 (nhánh `feat/p3-quan`):
  - [ ] `_tick_freshness`: kho quán hao 0.25/s kể cả hàng đang giữ, `spoiled` theo id
  - [ ] `cook_started` tiêu đúng các id đã giữ, `items` là mảng cá thể; `base_price = floor(giá × TB fresh / 100)`; boa trên giá đã chốt
  - [ ] Burn với kho cá thể: món cháy mất nguyên liệu, thử giữ lại bằng `pick_freshest`
  - [ ] `_validate_quan` (`scenario.py`) cho `stock` / `hand` / bếp v1.2; sửa `tests/test_quan_lat4.py`
- AC: P3-11, 14, 15, 17 (phần bếp/tay).

### tiepnnk01-10 — QA lead, UI, lát 5 (day/Shop)
- Làm ngay:
  - [ ] Merge `feat/p3-qa` vào `main` (test vẫn `@pending` nên `main` xanh) để mọi người chạy được `QA_STRICT=1`
  - [ ] Đưa `phase3.md` cho PO
- Sau lát 0:
  - [ ] `day.py`: bàn giao kho cá thể trong bộ nhớ cùng tick, không hao thêm; Ngày kế cấp id mới theo thứ tự mảng; Shop giữ kho cá thể, không hao (AC-P3-08, 09)
  - [ ] Bỏ `@pending` từng test khi lát tương ứng xanh; HUD độ tươi chơi thật với dữ liệu v1.2 (AC-P3-18)
  - [ ] Hoàn thiện `CHANGELOG.md` (AC-P3-20), bảng giữ/đổi/thêm test cũ (AC-P3-19), `docs/verification/phase-3.md`, `verify.py --phase 3`
  - [ ] Retro Phase 2 + 3 trong `docs/retro.md`
- AC: P3-08, 09, 18, 19, 20.

## 4. Mốc thời gian (35 phút)
| Phút | Việc |
|---|---|
| 0–5 | PO chép Ticket-03, chốt mục 2 với cả nhóm. s0ra1n0 gắn `phase-2`. Tiệp merge `feat/p3-qa` |
| 5–15 | s0ra1n0 làm lát 0 v1.2 + `items.py`, merge **chậm nhất phút 15**. Người khác code trước theo chữ ký `items.py` |
| 15–28 | Lát 2, 3+4, 5 song song; merge từng nhánh khi `QA_STRICT=1` cho phần mình xanh |
| 28–32 | Toàn bộ test + `QA_STRICT=1`, smoke hai tiến trình v1.2, `verify.py --phase 3`, ma trận |
| 32–35 | Dự phòng; s0ra1n0 đẩy `phase-3` trước 2:30 |

## 5. Rủi ro
- **Lát 0 v1.2 là nút thắt lớn nhất** (đổi schema ở mọi file) → s0ra1n0 chỉ làm lát 0 trong 15 phút đầu, nợ P2 để sau; `items.py` merge trước nếu adapter chậm.
- **Sửa ~10 file test cũ** sang kho cá thể dễ đụng nhau → mỗi người sửa test của vùng mình (contracts mục A), ghi lý do trong commit.
- **Thứ tự hao / giữ lại / nấu trong quán** lệch Ticket → PO chốt mục 2D ngay phút 0–5.
- **Không kịp** → ưu tiên AC đổi schema (P3-06, 07, 17) và hao/ươn (01–05, 11), sau đó giá theo độ tươi (14, 15), cuối cùng day (08, 09). Gắn tag đúng hạn, ghi trung thực phần chưa đạt.
