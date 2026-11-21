# Kế hoạch Phase 3 — Ticket-03 "Mùa Nước Nổi" (1:55–2:30, 35 phút)

Test Contract **v1.2** · hạn tag `phase-3` 2:30. Chia việc theo vai trong [`TEAM.md`](../../TEAM.md), dựa trên phần QA (tiepnnk01-10) đã làm ở nhánh `feat/p3-qa`.

> **Nguồn yêu cầu:** Ticket-03 chưa có trong repo. Bản này dựa trên tóm tắt của Tiệp (`docs/verification/phase-3.md`, `CHANGELOG.md` ở `feat/p3-qa`, đọc từ file `phase3.md`). **PO chép toàn văn vào `docs/prd/phase-3.md` ngay phút 0–5**; chỗ nào lệch thì ticket thắng, PO sửa plan này.

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

**B. Định dạng:** cá thể là dict `{id, kind, fresh}`; `fresh` lưu số thực đầy đủ, chỉ làm tròn khi xuất JSONL (khung lo); `hold`, `stock`, `lost`, `cook_started.items`, `gather_end.inventory.items` là **mảng cá thể**; `customers[].reserved` là **mảng id**. Mảng sắp theo id, trừ `hold`/`lost` theo thứ tự nhặt (LIFO cho `lost`).

**C. Sự kiện mới:** `spoiled {item_id, kind, location}` (`location`: `hold` / `stock` — PO chốt theo Ticket). Phát theo id khi nhiều cá thể cùng ươn.

**D. Thứ tự bước quán v1.2 (PO chốt với Ticket-03):** đồng hồ → kiên nhẫn → **hao kho + `spoiled` (lát 4, `_tick_freshness`)** → **giữ lại đơn vừa ươn (lát 3, `_retry_spoiled`)** → nấu/ăn → di chuyển + một interact → trả tiền/rời bàn → đóng ca hoặc khách mới. Gather: hao giỏ ở bước đồng hồ (trước hái/bắt), nên hàng mới hái hao từ bước sau.

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
  - [ ] **PO:** chép Ticket-03 vào `docs/prd/phase-3.md` (xin `phase3.md` của Tiệp hoặc lưu từ lab board); sửa plan này nếu lệch
  - [ ] **PO:** chốt 2 giả định Tiệp nêu (`spoiled` mang `phase` của pha chứa cá thể; `fresh` trong file kho là số thực, so ±0.01) và thứ tự mục 2D; ghi `docs/clarify.md`
  - [ ] **PO:** chốt với nhóm có làm mở rộng Phase 3 hay không (gợi ý: **không**, 35 phút chỉ đủ lõi; burn đã là mở rộng của nhóm)
- Sau lát 0 (nhánh `feat/p3-quan`, chung với Hùng như Phase 2):
  - [ ] `_reserve` giữ theo id bằng `pick_freshest`; khách mới giữ cá thể tươi nhất; fixture thiếu `reserved` cấp theo `order_tick` rồi id bàn
  - [ ] `_spawn_customers` chọn món bằng `usable_by_kind` (bỏ hàng ươn, hàng đã giữ) → `no_dish` khi không món nào đủ
  - [ ] `_retry_spoiled`: đơn có cá thể giữ vừa ươn → nhả hết, giữ lại một lần, thiếu → `unfulfillable`, khách vẫn chờ
  - [ ] `_init_customers` kiểm `reserved` mảng id (id lạ, trỏ hàng ươn, sai công thức, dùng chung, kiểu cũ → mã 2)
  - [ ] Sửa `tests/test_quan_lat3.py`, `tests/test_quan_p2.py` sang kho cá thể
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
