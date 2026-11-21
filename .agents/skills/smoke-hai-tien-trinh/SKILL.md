---
name: smoke-hai-tien-trinh
description: Chạy smoke hộp đen hai tiến trình gather → file kho → quan theo PRD-0 mục G (AC-P1-50), kèm kiểm kho sai trả mã 2 (AC-P1-52). Dùng trước khi gộp lát 2/3/4 vào main, trước khi gắn tag phase-n, và khi đổi hợp đồng kho.
---

# Smoke hai tiến trình (gather → kho → quan)

## Khi nào dùng
- Trước khi gộp nhánh đụng `chonoi/sim/gather.py`, `chonoi/sim/quan.py`, `chonoi/inventory.py` hoặc `chonoi/runner.py`.
- Trước khi Integrator gắn tag `phase-n`. Lưu output vào `docs/proof/phase-n/`.
- Sau khi sửa `docs/contracts/README.md` hoặc `game.contract.json`.

## Cách chạy
Từ gốc repo:

```bash
python3 .agents/skills/smoke-hai-tien-trinh/smoke.py                          # in kết quả
python3 .agents/skills/smoke-hai-tien-trinh/smoke.py --proof docs/proof/phase-1  # lưu bằng chứng
```

Script đọc `headless_cmd` từ `game.contract.json`, nên dùng được cả khi nhóm đổi ngôn ngữ.

## Script kiểm những gì
1. `dock.json` = `{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}`, inputs `interact` ở tick 0 → gather kết thúc `docked`, mã 0.
2. `kho.json` đúng `{"items":{"bong_sung":2,"ca_loc":1}}` và khớp `gather_end.data.inventory`.
3. `quan --inventory kho.json --ticks 0` → snapshot tick 0 có `stock:{"bong_sung":2,"ca_loc":1}`.
4. Chạm `--ticks` trước khi gather xong → **không** tạo file kho.
5. Bốn file kho sai (số âm, kind lạ, số thực, khóa gốc lạ) → mã 2.

Mã thoát của script: 0 nếu mọi mục đạt, 1 nếu có mục trượt.

## Agent làm gì với kết quả
- Mục trượt: **không** sửa test hay hợp đồng cho xanh. Báo lát sở hữu: kho thuộc lát 2, đọc kho thuộc lát 3/4, mã 2 thuộc QA (`inventory.py`/`scenario.py`).
- Khi gắn tag: dán bảng kết quả vào `docs/verification/phase-n.md` (cột bằng chứng trỏ tới `docs/proof/phase-n/smoke.txt`).
- Ghi một dòng vào `docs/ai-usage-log.md` nếu agent đã chạy skill này.
