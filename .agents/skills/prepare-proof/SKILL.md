
---
name: prepare-proof
description: Thu thập bằng chứng kiểm thử thật cho Phase 1.
---

# Skill: Prepare Proof — Phase 1

## Mục tiêu
Tạo bằng chứng kiểm thử để QA đối chiếu với PRD-0.

## Khi nào sử dụng
- Trước khi tích hợp code vào main.
- Khi QA cần kiểm tra lại kết quả.
- Trước khi gắn tag phase-1.

## Quy trình
1. Đọc AGENTS.md và game.contract.json.
2. Chạy toàn bộ unittest.
3. Lưu kết quả vào file test-output.txt.
4. Chạy headless 2 lần cho từng mode gather và quan.
5. Lưu các file JSONL đầu ra.
6. So sánh nội dung từng byte.
7. Ghi kết quả vào report.md.
8. Bàn giao đường dẫn bằng chứng cho QA.

## Lệnh chạy
python .agents/skills/prepare-proof/prepare_proof.py

## Đầu ra
docs/proof/phase-1/harness/

Mỗi lần chạy lưu bằng chứng trong thư mục riêng.

## Quy tắc
- Không tự đánh dấu test PASS khi test thất bại.
- Không sửa test để tạo kết quả PASS.
- Không tạo bằng chứng giả.
- Không tự ghi đè docs/verification/phase-1.md.
- Không tự động commit hoặc push.
- QA quyết định AC nào đã đạt dựa trên bằng chứng.

## Phase 2 — Prepare Proof cho Contract v1.1

### Mục tiêu

Thu thập bằng chứng kiểm thử thực tế cho Phase 2 để QA đối chiếu với PRD và Acceptance Criteria.

### Lệnh chạy

Trên môi trường có lệnh python3:

`python .agents/skills/prepare-proof/prepare_proof.py --phase2`

Trên Windows, sử dụng Python hiện tại:

`python .agents/skills/prepare-proof/prepare_proof.py --phase2 --local-python`

Lưu ý: `--local-python` chỉ thay launcher của headless trong Harness.
Các unit tests có thể vẫn gọi `python3`, nên máy chạy test phải hỗ trợ lệnh này.

### Những gì Skill kiểm tra

1. Đọc Test Contract và xác nhận phiên bản 1.1.
2. Chạy toàn bộ unit tests.
3. Chạy gather hai lần với cùng seed.
4. Chạy quan hai lần với cùng seed.
5. Chạy day hai lần với seed 11, days 1.
6. So sánh JSONL từng byte để kiểm tra determinism.
7. Kiểm tra day kết thúc với trạng thái finished và days_complete.
8. Kiểm tra thời gian mỗi lần chạy day không vượt quá 20 giây.

### Bằng chứng được tạo

Thư mục:

`docs/proof/phase-2/harness/<timestamp>/`

Bao gồm:

- test-output.txt: Kết quả unit tests.
- gather-run1.jsonl và gather-run2.jsonl.
- quan-run1.jsonl và quan-run2.jsonl.
- day-run1.jsonl và day-run2.jsonl.
- Các file .log ghi lệnh, thời gian chạy và exit code.
- report.md ghi kết quả PASS/FAIL và SHA-256.

### Quy tắc bàn giao

- Chỉ báo PASS khi tất cả kiểm tra bắt buộc đều thành công.
- Không chỉnh sửa test hoặc Test Contract để làm kết quả PASS.
- Không dùng bằng chứng FAIL để khẳng định đã hoàn thành.
- Không tự động commit hoặc push.
- Harness PASS không có nghĩa tất cả Acceptance Criteria đều đạt.
- QA chịu trách nhiệm đánh giá AC dựa trên bằng chứng thực tế.
