# Kế hoạch & Checklist tiến độ — M4 (D): `sim/quan` (Phase 1)

- **Phụ trách:** Nguyễn Nhật Minh (`NhMinh-2610`) — Vai: Dev (dự phòng cho M3 `ththanh8888`)
- **Phạm vi:** Bếp, Bàn, Bưng, Tiền, Boa (Tip), Uy tín, Hết ca trong `chonoi/sim/quan.py`
- **Tài liệu chuẩn:** `PRD0.md` (mục D, E, F), `docs/contracts/README.md`, `docs/clarify.md`, `game.contract.json`

---

## 1. Thứ tự ưu tiên & sơ đồ phụ thuộc

> **Hiện trạng:** `M6.1`, `M6.2`, `M6.3` đã xong trên `main` → **M4.1 → M4.2 → M4.3 có thể làm liên tục ngay bây giờ** (chỉ chờ M3 ở bước ghép `M4.4`).

```mermaid
flowchart LR
    M61["M6.1 Hợp đồng (ĐÃ XONG)"] --> M42
    M63["M6.3 scenario.py (ĐÃ XONG)"] --> M42
    M41["P0: M4.1 Spec & AC"] --> M42["P0: M4.2 Tests & Scenarios"]
    M42 --> M43["P0: M4.3 Code quan.py (khách giả)"]
    M33["M3.3 Code khách (C)"] --> M44
    M43 --> M44["P1: M4.4 Ghép M3↔M4 & Bằng chứng"]
    M43 --> M34["M3.4 (C chờ)"]
    M43 --> M54["M5.4 HUD (E chờ)"]
    M43 --> M64["M6.4 Tích hợp (F chờ)"]
    M44 --> M65["M6.5 Duyệt & Tag phase-1 (F chờ)"]
```

| Ưu tiên | Mã task | Mục tiêu | Phụ thuộc (Chờ) | Ai chờ mình | Trạng thái |
|---|---|---|---|---|---|
| **P0 (Làm ngay)** | **M4.1** | Chốt Spec/AC + giao ước interface với M3 | Không | `M4.2` | Đã xong (chờ xác nhận nhanh với M3) |
| **P0 (Sau M4.1)** | **M4.2** | Viết bộ test `tests/test_quan_m4.py` | `M4.1`, `M6.1` ✅, `M6.3` ✅ | `M4.3` | Đã xong ✅ |
| **P0 (Trọng tâm)** | **M4.3** | Code phần M4 trong `chonoi/sim/quan.py` (chạy độc lập với khách từ scenario) | `M4.2` | `M3.4`, `M4.4`, `M5.4`, `M6.4` | Đã xong ✅ |
| **P1 (Trước 0:45)** | **M4.4** | Ghép M3 ↔ M4, chạy full test, lưu bằng chứng | `M4.3`, `M3.3` (C) ✅ | `M6.5` | Đã xong ✅ |
| **P2 (Xuyên suốt)** | **Quy trình** | ≥ 3 commit, review chéo C ↔ D, nhật ký AI & standup | Song song | DoD Phase 1 | Đang tiến hành |

---

## 2. Checklist chi tiết theo thứ tự làm

### Đợt 1 — `M4.1`: Spec, AC & chốt giao ước với M3 *(Ưu tiên P0 — làm đầu tiên)*
- [x] Đối chiếu lại toàn bộ số liệu trong `game.contract.json` (`interact_radius`, `eat_s`, `patience_s`, `burn_s`, `carry_limit`, `tip_rate`, `tip_min_patience_ratio`, `tip_reputation`, `left_reputation_delta`, `reputation_min/max`, `menu`).
- [x] Chốt danh sách `AC-M4-01` → `AC-M4-08` (xem mục 3 bên dưới).
- [ ] Nhắn trao đổi nhanh với **M3 (`ththanh8888`)** để thống nhất:
  - [x] Cấu trúc dict `customer` trong `self.customers` (đủ 11 trường theo `docs/contracts/README.md`).
  - [x] Tách vùng hàm trong `chonoi/sim/quan.py` để tránh conflict merge (M3 giữ khách/lịch/spawn; M4 giữ bếp/interact/tiền/tip/dọn cuối ca).
  - [x] Hàm dùng chung `_cleanup_order_artifacts(order_id)` và `_add_reputation(delta)` khi khách bỏ đi vì hết kiên nhẫn.
- [x] Commit 1 (`M4.1`): lưu spec/kế hoạch (`docs/plan/phase-1-Minh.md`).

---

### Đợt 2 — `M4.2`: Viết bộ test từ AC *(Ưu tiên P0 — làm ngay sau M4.1)*
- [x] Tạo file `tests/test_quan_m4.py` dùng `scenario` dựng sẵn khách (độc lập với M3).
- [x] Viết test cho `AC-M4-01`: chọn mục tiêu `interact` đúng mép `interact_radius`, thứ tự ưu tiên `(dist, bếp trước bàn, id_key)`, bỏ lượt khi đối tượng chọn không tương tác được.
- [x] Viết test cho `AC-M4-02`: `cook_started` chọn đơn `reserved` cũ nhất theo `(order_tick, id_key(table_id))`, trừ đúng kho, `items` sắp theo `kind`, cập nhật `reserved = {}`, `order_status = "assigned"`.
- [x] Viết test cho `AC-M4-03`: `dish_ready` sau đúng `cook_s * 60` tick, `ready_ticks == 0` ở tick vừa chín rồi mới tăng từ tick sau, `burn_s: null` không cháy.
- [x] Viết test cho `AC-M4-04`: `dish_picked` khi tay trống (`carry_limit == 1`), bếp về `idle`; bỏ qua khi tay đang cầm món.
- [x] Viết test cho `AC-M4-05`: `served` đúng `order_id`, sai `order_id` bỏ qua; tính tip đúng biên `patience_ticks_left / patience_max >= tip_min_patience_ratio` (cả trường hợp đạt biên và thiếu 1 tick); phục vụ đúng tick `patience_ticks_left == 0` vẫn hợp lệ.
- [x] Viết test cho `AC-M4-06`: ăn xong sau `eat_s * 60` tick → `paid` (`finished_eating`), cộng `money`/`earned`/`shift_earned`, tip > 0 mới cộng `tip_reputation` (kẹp `[0, 5]`), kiểm tra `score = earned + 100 * floor(reputation)`.
- [x] Viết test cho `AC-M4-07`: hết ca (`time_left_ticks == 0`) → khách `eating` (kể cả vừa được phục vụ ở tick cuối) trả tiền `paid` (`closing`), khách `waiting` rời đi `customer_left` (`closing`) không trừ uy tín và hủy món mồ côi, kết thúc bằng `quan_end`.
- [x] Viết test cho `AC-M4-08`: khách `assigned` bỏ đi do hết kiên nhẫn → hủy món trên bếp (`cooking`/`ready`) hoặc `hand`, không hoàn nguyên liệu.
- [x] Chạy thử `tests/test_quan_m4.py` xác nhận fail đúng chỗ (TDD) trước khi code.
- [x] Commit 2 (`M4.2`): commit & push `tests/test_quan_m4.py` lên nhánh.

---

### Đợt 3 — `M4.3`: Code phần M4 trong `chonoi/sim/quan.py` *(Ưu tiên P0 — chặn M3.4, M4.4, M5.4, M6.4)*
- [x] Khởi tạo đầy đủ mặc định cho `customers` dựng từ `scenario` (đảm bảo chạy độc lập trước khi ghép M3: `order_tick`, `state`, `patience_ticks_left`, `eat_ticks_left`, `order_status`, tự cấp `reserved` theo công thức nếu vắng).
- [x] **Bước 1 trong `step()`:** giảm `time_left_ticks`, tăng `ready_ticks` chỉ cho bếp đã `ready` từ đầu bước, giảm `cook_ticks_left`, giảm `eat_ticks_left`, giảm `patience_ticks_left`.
- [x] **Bước 2 trong `step()`:** duyệt `stoves` theo `sort_by_id`, bếp `cooking` có `cook_ticks_left == 0` → `ready` (`ready_ticks = 0`), phát `dish_ready`.
- [x] **Bước 3 trong `step()`:** sau `self._move(inp)`, xử lý tối đa 1 cạnh lên `inp.pressed("interact")`:
  - [x] Tìm ứng viên trong `interact_radius` (`<=`), chọn theo `(dist, 0 if stove else 1, id_key(id))`.
  - [x] Implement `_cook_on_stove(stove)` → trừ `stock`, `items` sắp theo `kind`, phát `cook_started`.
  - [x] Implement `_pick_from_stove(stove)` → chuyển sang `self.hand`, reset bếp về `idle`, phát `dish_picked`.
  - [x] Implement `_serve_table(table)` → kiểm `order_id`, tính `tip` theo `patience_ticks_left` sau Bước 1, chuyển khách sang `eating`/`served`, phát `served`.
- [x] **Bước 4 trong `step()`:** duyệt khách theo `id_key(table_id)`:
  - [x] Khách `eating` có `eat_ticks_left == 0` → cộng tiền, cộng `tip_reputation` nếu `tip > 0` (kẹp `[min, max]`), phát `paid` (`finished_eating`), xóa khách.
  - [x] Helper `_cleanup_order_artifacts(order_id)` dọn bếp/tay cho đơn bị hủy.
  - [x] Helper `_add_reputation(delta)` kẹp `[reputation_min, reputation_max]`.
  - [x] Khi `time_left_ticks > 0`: xử lý khách `waiting` có `patience_ticks_left == 0` → trừ `left_reputation_delta`, dọn món mồ côi, phát `customer_left` (`patience`), xóa khách.
  - [x] Khi `time_left_ticks == 0`: dọn toàn bộ khách theo `id_key(table_id)` (`eating` → `paid` `closing`; `waiting` → `customer_left` `closing` không trừ uy tín + dọn món mồ côi), rồi phát `quan_end`.
- [x] Kiểm tra không dùng `random` toàn cục, không dùng đồng hồ hệ thống, không hard-code số liệu tuning.
- [x] Chạy xanh toàn bộ `tests/test_quan_m4.py`, `tests/test_scenario_m6.py`, `tests/test_smoke_p1.py` và `tests/test_python_starter_units.py`.
- [x] Commit 3 (`M4.3`): commit & push `chonoi/sim/quan.py` lên nhánh và báo nhóm (M3, M5, M6).

---

### Đợt 4 — `M4.4`: Ghép M3 ↔ M4 & Bằng chứng *(Ưu tiên P1 — hoàn tất trước 0:50)*
- [x] Pull / merge phần `M3.3` của Phùng Văn Thanh Cao (`ththanh8888`) vào `chonoi/sim/quan.py` (kế thừa `CustomerMixin` từ `chonoi/sim/quan_customers.py`, xử lý sạch xung đột ở `quan.py`, `standup.md`, `ai-usage-log.md`).
- [x] Kiểm tra khớp vòng đời đầy đủ: khách tự sinh (`customer_arrived`) → giữ chỗ → nấu (`cook_started`) → chín (`dish_ready`) → bưng (`dish_picked`) → phục vụ (`served`) → ăn xong (`paid`) → hết ca (`quan_end`).
- [x] Kiểm tra tính tất định (chạy cùng seed 2 lần → file JSONL giống nhau từng byte — đã kiểm trong `test_full_kitchen_loop_and_determinism`).
- [x] Chạy toàn bộ test suite (`test_quan_m4`, `test_quan_customers_m3`, `test_integration_m6`, `test_scenario_m6`, `test_smoke_p1`, `test_python_starter_units`, `test_team_check`) xanh 100% sau khi ghép M3.
- [x] Xuất bằng chứng chạy thật phần M4 + ghép M3 vào `docs/proof/phase-1/m4-test-log.txt`.
- [x] Commit 4 (`M4.4`): commit merge & push bản ghép + bằng chứng cuối.

---

### Việc ngoài bảng bắt buộc *(Ưu tiên P2 — xuyên suốt Phase 1)*
- [x] Đủ **≥ 3 commit có nội dung** bằng tài khoản GitHub `NhMinh-2610`.
- [ ] Review chéo PR/diff với **C (`ththanh8888`)** (nhận xét bám diff).
- [x] Điền dòng của mình vào `docs/standup.md` (giữa phase ~0:30).
- [x] Điền dòng của mình vào `docs/ai-usage-log.md` (cuối phase).
- [x] Kiểm tra `python tools/check_team.py` xanh.

---

## 3. Bảng kiểm nhanh Acceptance Criteria (M4)

| Mã AC | Mô tả kiểm chứng | Test | Code | Đạt |
|---|---|---|---|---|
| `AC-M4-01` | Interact đúng mép bán kính, ưu tiên `(dist, bếp trước bàn, id)`, không fallback nếu bận | [x] | [x] | [x] |
| `AC-M4-02` | `cook_started` lấy đơn `reserved` cũ nhất `(order_tick, table_id)`, trừ kho, `items` sắp theo `kind` | [x] | [x] | [x] |
| `AC-M4-03` | `dish_ready` đúng `cook_s * 60` tick, `ready_ticks = 0` ở tick chín rồi mới tăng, không cháy | [x] | [x] | [x] |
| `AC-M4-04` | `dish_picked` tôn trọng `carry_limit = 1`, bếp về `idle` | [x] | [x] | [x] |
| `AC-M4-05` | `served` đúng `order_id`, tính `tip` theo tỷ lệ kiên nhẫn sau Bước 1, hợp lệ ở tick `patience == 0` | [x] | [x] | [x] |
| `AC-M4-06` | `paid` (`finished_eating`), cộng tiền, `tip > 0` mới cộng `tip_reputation` và kẹp `[0, 5]`, đúng `score` | [x] | [x] | [x] |
| `AC-M4-07` | Hết ca: `eating` trả tiền (`closing`), `waiting` rời đi (`closing`) không trừ uy tín + hủy món, phát `quan_end` | [x] | [x] | [x] |
| `AC-M4-08` | Khách bỏ đi vì hết kiên nhẫn hủy món mồ côi trên bếp/tay, không hoàn nguyên liệu | [x] | [x] | [x] |
