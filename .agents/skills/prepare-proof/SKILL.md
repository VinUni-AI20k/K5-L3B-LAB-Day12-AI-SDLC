
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
