---
name: phase-1-verification
description: Kiểm chứng Phase 1 của Chợ Nổi trước khi gắn tag/đẩy nhánh chính hoặc khi cần bằng chứng — chạy toàn bộ unittest, headless gather và quán (tất định, mã 2 cho đầu vào sai, quán nạp kho), ghi docs/proof/phase-1/verify-run.txt rồi cập nhật trung thực docs/verification/phase-1.md.
---

# Kiểm chứng Phase 1

Dùng khi: trước khi gắn tag `phase-1`, trước khi merge vào `main`, sau khi gộp nhiều lát, hoặc
khi giảng viên/QA cần bằng chứng. Lệnh chạy từ gốc repo.

## Bước 1. Chạy script kiểm chứng

```
python .agents/skills/phase-1-verification/scripts/verify_phase1.py
```

(macOS/Linux có thể dùng `python3`.) Script làm theo thứ tự:

| # | Bước | Lệnh tương đương |
|---|---|---|
| 0 | Bảo đảm `python3` chạy được (Windows: tạo shim venv ngoài repo, không sửa contract) | — |
| 1 | Toàn bộ unittest | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` |
| 2 | Headless gather, 2 lần, so sha256 | `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl` |
| 3 | Headless quán, 2 lần, so sha256 | `python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --out out.jsonl` |
| 4 | Quán nạp kho mẫu | `... --mode quan ... --inventory docs/contracts/inventory.sample.json` |
| 5 | Đầu vào sai → mã 2 và không ghi file | `--ticks -1`, `--mode river`, `--inventory` với gather |

Kết quả ghi vào `docs/proof/phase-1/verify-run.txt` (commit, nhánh, lệnh, mã thoát, số test,
sha256). Mã thoát script: 0 = mọi bước đạt, 1 = có bước chưa đạt.

Tùy chọn: `--no-proof` (không ghi file), `--only-tests -k <mẫu>` (chạy một nhóm test),
`--seed`, `--ticks`.

## Bước 2. Đọc kết quả, phân loại lỗi
- `CHƯA ĐẠT` kèm "9009" / "Python was not found": lỗi môi trường (python3 là lối tắt Store),
  không phải luật sai. Script đã tự xử lý; nếu vẫn gặp thì cài Python thật hoặc tắt
  App execution alias của python3.
- Test fail thật: ghi tên test và AC liên quan; báo chủ lát (xem `docs/plan/phan-chia-cong-viec.md`).
  **Không sửa test cho xanh.**
- Không tất định (sha256 khác): tìm `random`/đồng hồ/thứ tự dict-set không ổn định trong luật
  (`python .agents/skills/python-fact-grounded-coding/scripts/check_rules.py`).

## Bước 3. Cập nhật `docs/verification/phase-1.md`
Với mỗi dòng AC trong ma trận truy vết:
1. Cột **Cách kiểm chứng**: test/lệnh thực sự kiểm AC đó (tên `file::Lớp.test`).
2. Cột **Bằng chứng**: link `docs/proof/phase-1/verify-run.txt` và/hoặc tên test cụ thể.
3. Cột **Kết quả**: `đạt` chỉ khi test/lệnh tương ứng ĐẠT trong lần chạy vừa rồi; còn lại ghi
   `chưa đạt` + lý do. Ghi trung thực, kể cả lỗi môi trường.
4. Mục **Đánh giá ngắn**: cập nhật "chưa đạt" và "cần chỉnh cho phase sau" theo kết quả mới.

AC không có test nào kiểm: ghi rõ "chưa có test tự động", đừng đánh `đạt`.

## Bước 4. Commit bằng chứng
- Commit `docs/proof/phase-1/verify-run.txt` + `docs/verification/phase-1.md` cùng lúc.
- Mô tả commit: dòng "Tổng: x/y bước đạt", số test, commit đã kiểm.
- Không commit file `*.jsonl` tạm hay `kho.json` (đã có trong `.gitignore`).
- Nếu dùng AI để chạy/viết: thêm dòng vào `docs/ai-usage-log.md`.

## Phase sau
Khi có Phase 2/3, chép skill này thành `phase-N-verification` hoặc thêm cờ, đổi đường dẫn
proof/verification và thêm bước headless mới (ví dụ `--mode day` từ contract v1.1).
