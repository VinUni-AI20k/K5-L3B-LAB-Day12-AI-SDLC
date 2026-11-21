---
name: verify-phase
description: Điền ma trận truy vết docs/verification/phase-n.md (AC → cách kiểm chứng → bằng chứng → đạt/chưa đạt) từ danh sách AC-P{n}-xx trong docs/plan/phase-n.md và log chạy thật. Dùng ở mốc 45–55 phút của mỗi phase, trên commit sắp gắn tag.
---

# verify-phase — lập ma trận kiểm chứng cho phase n

Người giữ file: QA lead (`docs/verification/`, `docs/proof/`). Người khác chạy skill này thì gửi kết quả cho QA.

## Đầu vào

1. Danh sách AC: bảng "Tiêu chí chấp nhận" trong `docs/plan/phase-n.md`.
2. Quyết định PO: `docs/clarify.md` (chỗ PRD mơ hồ đã chốt thế nào).
3. Commit kiểm chứng: `git rev-parse --short HEAD` trên `main` sau khi Lead gộp.

## Các bước

1. Chạy skill `run-tests` trên đúng commit đó. Lưu log thật vào `docs/proof/phase-n/` (`unittest.txt`, `smoke.txt`, `determinism.txt`).
2. Với mỗi AC, tìm test chứng minh nó:
   ```bash
   grep -rn "AC-P1-05\|oxygen_empty" tests/
   ```
   Không có test → ghi "chưa kiểm chứng" hoặc kiểm bằng replay headless (scenario + inputs) và lưu JSONL/trích đoạn vào `docs/proof/phase-n/`.
3. Điền bảng, mỗi AC một dòng:

   | AC | Cách kiểm chứng | Bằng chứng | Kết quả |
   |---|---|---|---|
   | AC-P1-05 | `test_gather_oxy.Oxygen.*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |

4. Ghi dòng đầu file: ngày, mã commit, phiên bản Python, hệ điều hành.
5. Mục "Đánh giá ngắn": AC nào đạt / chưa đạt và điều cần chỉnh cho phase sau.

## Quy tắc

- **Trung thực:** chỉ ghi "Đạt" khi có log chạy thật trên commit đã ghi. Chưa xong thì ghi "chưa đạt" kèm lý do.
- Bằng chứng phải trỏ tới file trong repo, không dán ảnh chụp không rõ nguồn.
- Phase sau: giữ AC của phase trước trong `tests/test_regression.py` và trong ma trận (kiểm lại phase trước).
