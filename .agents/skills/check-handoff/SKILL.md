---
name: check-handoff
description: Kiểm bàn giao kho gather -> quan (PRD-0 mục G). Dùng sau mỗi lượt gather có --inventory-out, trước khi gửi file kho cho người làm quán/QA, và trước khi gắn tag.
---

# Kiểm bàn giao kho

1. Chạy gather có ghi kho:
   `python3 -m chonoi.headless --mode gather --seed 1 --ticks 3000 --inputs <inputs.json> --inventory-out <kho.json> --out <gather.jsonl>`
2. Kiểm: `python3 tools/check_handoff.py <gather.jsonl> <kho.json>`
   - schema kho đúng, khớp `gather_end.data.inventory`, quán đọc được và `stock` ở tick 0 khớp.
   - Mã 0 = KHỚP, 1 = LỆCH (in dòng `<-- LỆCH` và `LỖI:` ra stderr).
3. Lưu output vào `docs/proof/phase-n/handoff.txt`, dẫn link từ `docs/verification/phase-n.md`.
4. LỆCH thì không sửa tay file kho: tìm lỗi ở luật gather hoặc quán đọc kho.

Lượt mẫu có sẵn: `docs/proof/phase-1/inputs-thu.json`.
