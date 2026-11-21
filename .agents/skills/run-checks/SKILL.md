---
name: run-checks
description: Chạy toàn bộ kiểm chứng Phase 1 (unittest, tất định 2 lần so byte, smoke hai tiến trình gather→kho→quan, check_team) và ghi bằng chứng vào docs/proof/phase-1/. Dùng trước khi merge vào main, trước khi gắn tag phase-n, hoặc khi được hỏi "test có xanh không".
---

# run-checks — kiểm chứng trước khi merge / gắn tag

Chủ sở hữu: QA lead. Ai cũng chạy được.

## Khi nào dùng
- Trước khi merge PR / đẩy vào `main` (AGENTS.md: "trước khi đẩy, chạy test").
- Phút 45–55 của phase: chạy trên commit bàn giao rồi mới gắn tag.
- Sau khi một lát merge xong: chạy chế độ nghiêm để xem test `pending` của lát đó đã xanh chưa.

## Các bước

1. **Kiểm nhanh toàn bộ** (từ gốc repo):
   ```bash
   python3 tools/run_checks.py
   ```
   In 4 dòng `[ĐẠT]/[CHƯA ĐẠT]`: unittest · tất định · smoke hai tiến trình · check_team. Mã thoát 0 = tất cả đạt.

2. **Xem test đang chờ lát nào** (chạy cả test `@pending`, không skip):
   ```bash
   QA_STRICT=1 PYTHONPATH=tests:. python3 -m unittest test_gather_p1 test_quan_p1 -v
   ```
   Test của lát đã merge mà vẫn đỏ → báo người làm lát kèm tên test và dòng `AssertionError`. Không sửa test cho xanh khi luật sai.

3. **Lát đã xanh ở bước 2** → bỏ `@pending("lát N")` khỏi các test đó, chạy lại bước 1, commit `test: bật test AC-P1-xx cho lát N`.

4. **Ghi bằng chứng** (chỉ trên commit sẽ gắn tag):
   ```bash
   python3 tools/run_checks.py --proof
   ```
   Tạo `docs/proof/phase-1/checks-<commit>.txt`. Dẫn link file này trong cột "Bằng chứng" của `docs/verification/phase-1.md`, ghi kết quả trung thực (đạt / chưa đạt).

## Máy Windows
`python3` hay bị trỏ sai. Đặt lệnh headless và dùng `;` cho PYTHONPATH:
```bash
export CHONOI_HEADLESS_CMD="python -m chonoi.headless"
PYTHONPATH="tests;." python -m unittest discover -s tests -v
python tools/run_checks.py
```
CI và macOS/Linux không cần biến này.

## Không làm
- Không gắn tag khi bước 1 còn `[CHƯA ĐẠT]` mà chưa ghi lý do vào `docs/verification/phase-1.md`.
- Không xoá / sửa assert để test xanh; luật sai thì sửa luật hoặc ghi `docs/clarify.md`.
