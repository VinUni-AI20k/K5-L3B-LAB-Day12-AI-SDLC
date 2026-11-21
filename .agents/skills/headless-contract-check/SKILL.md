---
name: headless-contract-check
description: Chạy kiểm chứng hộp đen theo Test Contract (headless, JSONL, determinism, mã thoát). Dùng sau mỗi lần sửa chonoi/sim/* hoặc scenario.py, và trước khi push lên main.
---

# headless-contract-check

Mục tiêu: chứng minh luật chơi đúng Test Contract bằng output thật, không dựa vào lời agent.

## Khi nào dùng
- Vừa sửa `chonoi/sim/gather.py`, `chonoi/sim/quan.py`, `chonoi/scenario.py`.
- Trước khi push, trước khi gắn tag `phase-N`.

## Các bước
1. Chạy toàn bộ test:
   `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
   Đỏ thì dừng, sửa LUẬT (không sửa test cho xanh; nếu phải đổi test thì ghi lý do trong commit).
2. Chạy headless mỗi mode một lần, kiểm mã thoát = 0:
   `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out_gather.jsonl`
   `python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --out out_quan.jsonl`
3. Determinism: chạy lại cùng seed ra file khác, so byte:
   `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out_gather2.jsonl`
   PowerShell: `fc.exe /b out_gather.jsonl out_gather2.jsonl`; bash: `cmp out_gather.jsonl out_gather2.jsonl`
4. Đầu vào sai phải thoát mã 2 và KHÔNG tạo file output (ví dụ `--ticks -1`).
5. Lưu output thật vào `docs/proof/phase-N/` kèm lệnh đã chạy và ngày giờ. Cấm sửa tay output.

## Quy tắc
- Chỉ ghi "đạt" khi đã chạy thật và có file bằng chứng.
- Cùng seed phải cho output giống từng byte; không dùng `random` toàn cục hay đồng hồ hệ thống.
- Thực thể sáng tạo thêm phải tắt ở headless.
