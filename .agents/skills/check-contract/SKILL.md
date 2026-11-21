
---
name: check-contract
description: Kiểm tra Test Contract và tính tất định của headless trong Day 12.
---

# Skill: Check Contract — Phase 1

## Mục tiêu
Kiểm tra chế độ headless của game có chạy được và
tạo kết quả giống nhau từng byte khi cùng seed và đầu vào.

## Khi nào sử dụng
- Sau khi thay đổi gather hoặc quan.
- Sau khi thay đổi scenario hoặc logic mô phỏng.
- Trước khi tích hợp code vào main.
- Trước khi gắn tag phase-1.

## Quy trình

### Bước 1: Kiểm tra môi trường
- Làm việc tại thư mục gốc repo.
- Đọc game.contract.json và AGENTS.md.
- Không tự ý sửa Test Contract.

### Bước 2: Chạy kiểm thử
Chạy trong PowerShell:

$env:PYTHONPATH = "tests;."
python -m unittest discover -s tests -v

Ghi kết quả PASS/FAIL thực tế.

### Bước 3: Kiểm tra determinism
Chạy:

python .agents/skills/check-contract/check_contract.py

Trên Windows chưa có lệnh python3, có thể thử:

python .agents/skills/check-contract/check_contract.py --local-python

Lưu ý: --local-python chỉ kiểm tra logic bằng Python hiện tại;
không xác nhận lệnh headless_cmd trong contract hoạt động.

### Bước 4: Đánh giá
- Cả gather và quan phải chạy thành công.
- Cùng seed phải tạo output giống từng byte.
- Nếu thất bại, ghi rõ mode, lệnh và lỗi.
- Không tự ý sửa test hoặc contract để làm kết quả PASS.

## Kết quả bàn giao
Báo cáo:
- Test PASS/FAIL.
- Determinism gather PASS/FAIL.
- Determinism quan PASS/FAIL.
- Chế độ chạy: contract hay local-python.
- Những lỗi còn tồn tại.

## Quy tắc
Không bịa kết quả kiểm thử.
Không commit API key hay .env.
Không tự đánh dấu PASS khi chưa chạy thành công.
Không tự động commit hoặc push.


## Phase 2 — Test Contract v1.1

### Kiểm thử Phase 2

Lệnh chuẩn:

`python .agents/skills/check-contract/check_contract.py --phase2`

Trên Windows khi lệnh python3 không hoạt động:

`python .agents/skills/check-contract/check_contract.py --phase2 --local-python`

### Nội dung kiểm tra

- Xác nhận contract_version = "1.1".
- Chạy gather và quan hai lần với cùng seed.
- Chạy day hai lần với seed 11, days 1 và tối đa 22200 ticks.
- So sánh JSONL theo từng byte để kiểm tra determinism.
- Kiểm tra day kết thúc với state = finished,
  reason = days_complete và days_completed = 1.
- Đo thời gian mỗi lần chạy day, yêu cầu <= 20 giây.

### Quy tắc

- Mã thoát 0: các kiểm tra được yêu cầu PASS.
- Mã thoát 1: có kiểm tra FAIL.
- Mã thoát 2: phiên bản Contract không phù hợp.
- --local-python chỉ kiểm chứng bằng Python hiện tại,
  không xác nhận nguyên trạng lệnh headless_cmd.
- Harness PASS không đồng nghĩa mọi AC của game đã đạt.
- Không tự sửa Contract, test hoặc kết quả để tạo PASS.
