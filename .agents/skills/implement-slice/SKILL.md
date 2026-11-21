---
name: implement-slice
description: Hướng dẫn agent cài đặt MỘT lát (1–4) của sim gather/quan đúng PRD-0, chỉ sửa hàm thuộc lát, chạy test hộp đen của lát rồi ghi kết quả. Dùng khi được giao "làm lát N", "viết _update_oxygen / _try_gather / _tick_customers / _interact..." hoặc sửa test pending của một lát.
---

# implement-slice — làm một lát luật chơi

## Đầu vào bắt buộc
Hỏi lại nếu thiếu: **số lát (1–4)**. Bảng sở hữu ở `docs/contracts/README.md`:

| Lát | File | Hàm được sửa | Test hộp đen (tìm `@pending("lát N")`) |
|---|---|---|---|
| 1 | `chonoi/sim/gather.py` | `_update_oxygen` | `tests/test_gather_p1.py` lớp `Oxygen` |
| 2 | `chonoi/sim/gather.py` | `_try_gather`, `_try_catch` | `tests/test_gather_p1.py` lớp `Gathering`, `Catching`, `DockAndInventory` |
| 3 | `chonoi/sim/quan.py` | `_tick_customers`, `_spawn_customers` | `tests/test_quan_p1.py` lớp `Customers`, `Closing` |
| 4 | `chonoi/sim/quan.py`, `chonoi/scenario.py` | `_tick_stoves_and_eating`, `_interact`, `_validate_quan` | `tests/test_quan_p1.py` lớp `Kitchen`, `ServeAndPay`, `Closing`, `FixtureValidation` |

## Các bước
1. **Đọc trước khi code** (không bỏ qua):
   - `docs/prd/phase-1.md` (PRD-0): mục F đúng pha (Gather / Quán), mục E (tên + `data` sự kiện), mục D (fixture).
   - `docs/contracts/README.md`: hàm sở hữu, hàm dùng chung, cấu trúc khách.
   - Các test `@pending` của lát → đó là đặc tả chạy được.
2. **Chạy test lát ở chế độ nghiêm để thấy đỏ** (RED):
   ```bash
   QA_STRICT=1 PYTHONPATH=tests:. python3 -m unittest test_gather_p1.Oxygen -v   # đổi lớp theo bảng
   ```
3. **Chỉ sửa hàm của lát mình.** Hàm dùng chung (`_add_to_hold`, `_change_reputation`, `_available`, `_reserve`, `_release`) và thứ tự gọi trong `step()` → báo cả nhóm / Integrator trước.
4. **Luật bắt buộc khi viết:**
   - Số chỉ đọc từ `self.t` / `self.menu` (game.contract.json), không hard-code 60, 1800, 0.5...
   - Ngẫu nhiên chỉ qua `self.rng` (Streams), không `random`, không đồng hồ.
   - Duyệt thực thể bằng `sort_by_id`, id mới qua `self.ids`.
   - Sự kiện: `events.append((name, data))` đúng tên và khóa `data` ở mục E.
5. **Chạy lại tới khi xanh** (GREEN), rồi chạy toàn bộ: `python3 tools/run_checks.py`.
6. **Chỗ PRD mơ hồ** → không tự bịa: ghi câu hỏi + giả định vào `docs/clarify.md`, báo PO.
7. **Commit** trên nhánh `feat/<lát>`: `feat(lat-N): <việc>` + dòng "QA_STRICT test lớp X: n/n xanh". Báo QA để bỏ `@pending`.
8. Ghi một dòng vào `docs/ai-usage-log.md` (người, phase, agent đã làm gì).

## Không làm
- Không sửa test hộp đen cho xanh; nếu nghĩ test sai so với PRD thì báo QA kèm trích dẫn PRD.
- Không đụng hàm của lát khác, không sửa khung giảng viên (`chonoi/{headless,inputs,runner,...}.py`).
