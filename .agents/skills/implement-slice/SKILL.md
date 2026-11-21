---
name: implement-slice
description: Quy trình cho agent khi viết một lát luật chơi (gather lát 1/2, quán lát 3/4 hoặc lát của phase sau) — đọc PRD đúng phase và hợp đồng, viết test hộp đen trước, chỉ sửa hàm mình sở hữu, chạy test, ghi nhật ký AI. Dùng khi được giao "làm lát N", "implement oxy/hái/bắt cá/khách/bếp", hoặc bất kỳ TODO(nhóm) nào trong chonoi/sim/.
---

# implement-slice — làm một lát luật

## 0. Đầu vào bắt buộc (hỏi người giao nếu thiếu)
- Số lát + phase, đoạn PRD tương ứng (dán nguyên văn AC), tên người sở hữu.
- Không có PRD thì **dừng**, không đoán luật. Chỗ mơ hồ ghi vào `docs/clarify.md` (câu hỏi, giả định tạm, ai quyết) và báo PO.

## 1. Đọc trước khi viết
- `AGENTS.md` (quy ước), `docs/contracts/README.md` (bảng chia hàm theo lát, cấu trúc khách, danh sách sự kiện).
- `game.contract.json` → khóa số liệu lát này cần.
- File sim của lát và các hàm dùng chung đã có:
  - gather: `_add_to_hold`, `_at_surface`, `_in_dock`, `_finish` (`chonoi/sim/gather.py`)
  - quán: `_change_reputation`, `_available`, `_reserve`, `_release` (`chonoi/sim/quan.py`)
  - `ids.sort_by_id`, `IdAllocator`, `Streams` (`chonoi/ids.py`, `chonoi/rng.py`)

## 2. Viết test trước (hộp đen)
- Thêm vào `tests/test_gather_p<n>.py` hoặc `tests/test_quan_p<n>.py`, mỗi AC ít nhất một test.
- Dùng `tests/helpers.py`: `Workdir`, `write_json`, `frames`, `run_headless`, `read_jsonl`, `events`, `snapshots`, `close`.
- Dựng tình huống bằng `--scenario` (đặt sẵn vị trí, oxy, giỏ, khách...) để test ngắn và rõ; số liệu đọc từ `game.contract.json`, không hard-code.
- Chạy và xác nhận test **đỏ** đúng lý do trước khi sửa luật.
- QA đã viết sẵn test hộp đen theo AC (ma trận `docs/verification/phase-1.md`). Test của lát chưa xong mang `@pending("lát N")`: skip mặc định, chạy thật bằng `QA_STRICT=1`:

  | Lát | Lớp test có sẵn |
  |---|---|
  | 1 | `test_gather_p1.Oxygen` |
  | 2 | `test_gather_p1.Gathering`, `Catching`, `DockAndInventory` |
  | 3 | `test_quan_p1.Customers`, `Closing` |
  | 4 | `test_quan_p1.Kitchen`, `ServeAndPay`, `Closing`, `FixtureValidation` |

  ```
  QA_STRICT=1 PYTHONPATH=tests:. python3 -m unittest test_gather_p1.Oxygen -v
  ```
  Lát xanh hết thì báo QA bỏ `@pending`. Thấy test lệch PRD thì báo QA kèm trích dẫn, không sửa assert.

## 3. Sửa luật
- Chỉ sửa **hàm mình sở hữu** trong bảng chia hàm. Cần đổi hàm dùng chung, thứ tự trong `step()`, schema kho, `game.contract.json` hay khung giảng viên → dừng, báo nhóm, ghi lý do (ADR `docs/adr/` hoặc `clarify.md`).
- Số liệu chỉ từ `self.t` / `self.menu`; ngẫu nhiên chỉ qua `self.rng`; duyệt thực thể bằng `sort_by_id`; không dùng `random`, `time`, duyệt `set`/dict không sắp.
- Sự kiện: `events.append((tên, data))` đúng tên và `data` như hợp đồng.
- Sáng tạo thêm phải tắt ở headless.

## 4. Kiểm tra
```
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```
(PowerShell: `$env:PYTHONPATH = "tests;."; py -m unittest discover -s tests -v`)
- Toàn bộ test phải xanh, kể cả smoke test và test của phase trước.
- Chơi thử nhanh: `python3 -m chonoi.live --mode gather|quan`.

## 5. Bàn giao
- Commit nhỏ trên nhánh `feat/<lát>`; mô tả commit ghi AC đã làm + kết quả test (số test, OK).
- Thêm một dòng `docs/ai-usage-log.md`: phase, người, công cụ/model, việc, AI sai ở đâu.
- Người sở hữu đọc lại diff trước khi mở PR; người dự phòng review.
