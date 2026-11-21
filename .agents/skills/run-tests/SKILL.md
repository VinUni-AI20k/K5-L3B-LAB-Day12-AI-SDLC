---
name: run-tests
description: Chạy toàn bộ test của repo Chợ Nổi (smoke hộp đen + test lát) trước khi commit/push, đọc kết quả và báo trung thực. Dùng sau mỗi thay đổi ở chonoi/ hoặc tests/, trước khi đẩy lên main, và trước khi Integrator gắn tag phase-n.
---

# run-tests — chạy test trước khi đẩy

## Khi nào dùng
- Vừa sửa `chonoi/**` hoặc `tests/**` (luật sim, scenario, contract, test).
- Trước `git push` lên `main`, và trước khi gắn tag `phase-n`.
- Khi người dùng hỏi "test có xanh không", "chạy test đi".

## Các bước
1. Lấy code mới nhất để test đúng thứ sẽ đẩy: `git pull --rebase`.
2. Chạy **cả bộ** test bằng một lệnh (đúng lệnh trong AGENTS.md):
   - macOS / Linux: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
   - Windows (Git Bash): `PYTHONPATH="tests;." python -m unittest discover -s tests -v` — dấu phân cách là `;`.
     Test hộp đen gọi `headless_cmd` trong `game.contract.json` (`python3 -m chonoi.headless`); máy không có `python3` thì tự tạo alias/WSL. **Không** sửa `headless_cmd` trong contract (máy chấm chạy Linux).
3. Chỉ chạy test của một lát khi đang làm dở (nhanh hơn), ví dụ: `PYTHONPATH=tests:. python3 -m unittest tests.test_gather_lat1 -v`. Trước khi đẩy vẫn phải chạy cả bộ (bước 2).
4. Đọc kết quả:
   - Dòng cuối `OK` và số `Ran N tests` → báo số test và kết quả.
   - `FAILED (failures=…, errors=…)` → liệt kê **từng** test hỏng kèm dòng `AssertionError`/traceback chính.
   - `FileNotFoundError` hàng loạt ở test smoke → thường là thiếu lệnh `python3`, không phải lỗi luật.
   - `ModuleNotFoundError: helpers` → sai `PYTHONPATH` (thiếu `tests`, hoặc dùng `:` trên Windows).

## Quy tắc
- **Không sửa test cho xanh khi luật sai.** Sửa luật; nếu test thật sự sai so với PRD thì ghi lý do trong commit và báo người giữ lát.
- Test đỏ do người khác (không phải thay đổi của mình) vẫn phải nêu tên trong báo cáo; không im lặng bỏ qua.
- Ghi kết quả (số test, OK/FAILED) vào mô tả commit hoặc `docs/proof/phase-n/`.
- Không đẩy lên `main` khi bộ test đỏ, trừ khi cả nhóm đồng ý và ghi lý do.

## Báo cáo mẫu
```
Test: 42/42 OK (PYTHONPATH=tests:. python3 -m unittest discover -s tests)
```
hoặc
```
Test: FAILED 2/44
- test_gather_lat2.Harvest.test_hold_full — AssertionError: [] != [(5, {...})]
- test_smoke_p1.Integration.test_inv_01_... — exit 2: "đầu vào sai: ..."
```
