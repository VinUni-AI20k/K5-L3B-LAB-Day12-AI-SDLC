---
name: check-headless
description: Kiểm tra nhanh tính tất định (determinism) và quy trình chuyển giao file kho giữa Buổi sáng (Gather) và Buổi tối (Quán) qua chế độ headless.
---

# Skill: check-headless

Sử dụng skill này bất cứ khi nào cần kiểm tra lại simulation core sau khi sửa đổi mã nguồn luật chơi hoặc tích hợp giữa các lát.

## Lệnh kiểm tra tính tất định (Deterministic Check)
Chạy 2 lần cùng seed, cùng số tick và so sánh từng byte của file JSONL đầu ra:

```bash
python3 -m chonoi.headless --mode gather --seed 42 --ticks 180 --out out_run1.jsonl
python3 -m chonoi.headless --mode gather --seed 42 --ticks 180 --out out_run2.jsonl
cmp out_run1.jsonl out_run2.jsonl && echo "PASS: Byte-for-byte identical!"
```

## Lệnh kiểm tra chuyển giao Kho (Gather -> Kho -> Quán)
```bash
# 1. Thu hoạch buổi sáng và ghi kho
python3 -m chonoi.headless --mode gather --seed 1 --ticks 120 --inventory-out inventory.json --out gather.jsonl

# 2. Buổi tối mở quán và nạp file kho
python3 -m chonoi.headless --mode quan --seed 1 --ticks 120 --inventory inventory.json --out quan.jsonl
```

Tiêu chí đạt:
- Mã thoát bằng `0`.
- File JSONL sinh ra đúng cấu trúc contract schema.
- Toàn bộ sản lượng thu hoạch ở buổi sáng được chuyển đầy đủ vào kho buổi tối.
