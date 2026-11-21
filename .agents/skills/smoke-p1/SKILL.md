---
name: smoke-p1
description: Chạy smoke test hộp đen 2 tiến trình Phase 1 (gather xuất file kho -> quan đọc file kho) và lưu bằng chứng sạch vào docs/proof/phase-1/.
---

# Smoke Test 2 Tiến Trình Phase 1 (`smoke-p1`)

## Khi nào dùng
- Từ phút 25 của Phase 1 (khi có file kho từ B) để kiểm tra hợp đồng tích hợp Lặn & Hái → Mở Quán (PRD-0 mục G).
- Ngay trước khi gắn tag `phase-1` trên `main` để lấy bằng chứng bàn giao.

## Quy trình thực hiện

### Bước 1: Chuẩn bị đầu vào chuẩn (PRD-0 mục G)
Tạo thư mục `docs/proof/phase-1/` và 2 file fixture chuẩn:
- `docs/proof/phase-1/dock.json`:
  ```json
  {"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}
  ```
- `docs/proof/phase-1/dock-inputs.json`:
  ```json
  {"frames":[{"tick":0,"interact":true}]}
  ```

### Bước 2: Chạy 2 tiến trình headless
- **Linux / macOS:**
  ```bash
  python3 -m chonoi.headless --mode gather --seed 42 --scenario docs/proof/phase-1/dock.json --inputs docs/proof/phase-1/dock-inputs.json --ticks 1 --out /tmp/gather.jsonl --inventory-out docs/proof/phase-1/catch.json
  python3 -m chonoi.headless --mode quan --seed 42 --inventory docs/proof/phase-1/catch.json --ticks 0 --out /tmp/quan.jsonl
  ```
- **Windows PowerShell** *(nếu chưa có `python3`, chạy bằng `python` — không sửa `headless_cmd` trong `game.contract.json`)*:
  ```powershell
  python -m chonoi.headless --mode gather --seed 42 --scenario docs/proof/phase-1/dock.json --inputs docs/proof/phase-1/dock-inputs.json --ticks 1 --out $env:TEMP\gather.jsonl --inventory-out docs/proof/phase-1/catch.json
  python -m chonoi.headless --mode quan --seed 42 --inventory docs/proof/phase-1/catch.json --ticks 0 --out $env:TEMP\quan.jsonl
  ```

### Bước 3: Đối chiếu tiêu chí đạt
1. Cả hai tiến trình trả mã thoát `0`.
2. `docs/proof/phase-1/catch.json` có nội dung đúng `{"items":{"bong_sung":2,"ca_loc":1}}` và khớp với `gather_end.data.inventory` trong `gather.jsonl`.
3. Snapshot tick `0` trong `quan.jsonl` có `"stock":{"bong_sung":2,"ca_loc":1}`.

### Bước 4: Lưu log bằng chứng & dọn file tạm
- Trích lệnh đã chạy, mã thoát, dòng sự kiện `gather_end`, nội dung `catch.json` và dòng snapshot tick `0` của `quan` vào `docs/proof/phase-1/smoke-2proc-log.txt`.
- **Cấm:** Không bao giờ commit file `*.jsonl` vào repo (xuất vào thư mục tạm hoặc xóa ngay sau khi trích log).
