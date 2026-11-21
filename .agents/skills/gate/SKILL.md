---
name: gate
description: Chạy cổng kiểm trước khi commit hoặc gắn tag phase-n. Dùng khi sắp tag, khi nghi main đỏ, khi cần kiểm tất định (cùng seed cùng byte) hoặc kiểm bàn giao gather → kho → quan.
---

# Gate

Một lệnh, bốn cổng, một quyết định: **đủ điều kiện chưa**.

## Chạy

```bash
python3 tools/run_checks.py
```

Bốn cổng, theo thứ tự: unittest, smoke `gather → kho → quan`, tất định cùng seed, bằng chứng dẫn đúng.
Mã thoát 0 là đủ điều kiện. Kết quả ghi vào `docs/proof/phase-1/checks-latest.md`.

## Kiểm riêng từng cổng

Tất định, hai lần chạy cùng seed phải giống từng byte:

```bash
python3 -m chonoi.headless --mode gather --seed 42 --ticks 180 --out a.jsonl
python3 -m chonoi.headless --mode gather --seed 42 --ticks 180 --out b.jsonl
cmp a.jsonl b.jsonl
```

Bàn giao kho — sản lượng buổi sáng phải sang đủ buổi tối:

```bash
python3 -m chonoi.headless --mode gather --seed 1 --ticks 120 --inventory-out inv.json --out g.jsonl
python3 -m chonoi.headless --mode quan --seed 1 --ticks 120 --inventory inv.json --out q.jsonl
```

Bằng chứng: `python3 tools/check_evidence.py` — dòng nào ghi "đạt" mà dẫn file `docs/proof/` không tồn tại thì lỗi.

## Trước khi tag

1. `git status` sạch, đang ở đúng commit trên `main`.
2. `run_checks.py` PASS; `python3 tools/check_team.py` OK.
3. `docs/verification/phase-n.md` cập nhật kết quả thật, kể cả phần chưa đạt.
4. `git tag -a phase-n -m "..."` rồi `git push origin phase-n`.

## Khi đỏ

Cổng nào đỏ thì đọc cổng đó trước. Test đỏ vì luật chưa có → xem ticket giữ lát đó. Test đỏ vì kỳ vọng sai → sửa test và ghi lý do trong commit. `run_checks.py` đỏ thì chưa tag.
