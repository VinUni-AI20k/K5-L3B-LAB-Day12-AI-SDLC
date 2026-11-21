---
name: smoke-proof
description: Chạy smoke hai tiến trình gather → quan theo PRD-0 mục G bằng tools/smoke_proof.py, lưu bằng chứng thật vào docs/proof/<phase>/ và dẫn link vào docs/verification/<phase>.md. Dùng ở phút 25 (thử xuất kho thật), phút 45 (trước khi tag) và mỗi khi đổi hợp đồng file kho.
---

# smoke-proof — bằng chứng tích hợp sáng → tối

## Khi nào dùng
- Phút 25 của phase: thử xuất file kho thật từ gather rồi nạp vào quan.
- Phút 45–55: chạy trên `main` trước khi Integrator gắn tag `phase-n` (DoD: "smoke hai tiến trình trên main cho thấy quán nhận đúng file kho").
- Sau khi sửa `chonoi/inventory.py`, `runner.py`, `headless.py`, hoặc `docs/contracts/` (hợp đồng kho).

## Các bước
1. Đứng ở commit cần làm bằng chứng (thường là `main` mới nhất): `git pull --rebase`, `git status` sạch.
2. Chạy:
   ```bash
   python3 tools/smoke_proof.py --phase phase-1
   # máy không có python3: python tools/smoke_proof.py --phase phase-1 --cmd "python -m chonoi.headless"
   ```
   Script chạy đúng 2 lệnh smoke của PRD (`--seed 42`, `dock.json`, `dock-inputs.json`) bằng `headless_cmd` trong `game.contract.json`, rồi kiểm 7 mục:
   mã thoát 0 (cả hai) · `gather_end.reason = docked` · file kho = `{"items":{"bong_sung":2,"ca_loc":1}}` · file kho = `gather_end.inventory` · chạy lại cùng seed giống từng byte · snapshot quán tick 0 có `stock` đúng file kho.
3. Đọc kết quả: mã thoát 0 = ĐẠT, 1 = CHƯA ĐẠT; dòng `[FAIL]` cho biết mục hỏng.
4. Bằng chứng nằm ở `docs/proof/<phase>/`: `smoke.md` (thời điểm, commit, bảng kiểm, lệnh đã chạy) + `dock.json`, `dock-inputs.json`, `gather.jsonl`, `catch.json`, `quan.jsonl`.
5. Thêm/cập nhật dòng trong `docs/verification/<phase>.md`:
   `| AC-P1-04 smoke hai tiến trình | python3 tools/smoke_proof.py --phase phase-1 | [smoke.md](../proof/phase-1/smoke.md) | đạt / chưa đạt |`
6. Commit bằng chứng (`git add docs/proof/<phase>/ docs/verification/<phase>.md`).

## Quy tắc
- **Bằng chứng phải thật**: không sửa tay `smoke.md` hay file JSONL; CHƯA ĐẠT thì ghi CHƯA ĐẠT và lý do.
- `smoke.md` ghi "(có thay đổi chưa commit)" nghĩa là chưa chạy trên commit sạch → commit trước rồi chạy lại cho bằng chứng ở commit gắn tag.
- Không dùng smoke này thay cho bộ test (skill `run-tests`); đây là bằng chứng tích hợp, không phủ luật từng lát.
