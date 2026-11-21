---
name: check-determinism
description: Kiểm game Chợ Nổi tất định (cùng seed thì output headless giống từng byte). Dùng sau khi sửa luật trong chonoi/sim/, trước khi mở PR hoặc gắn tag.
---

# check-determinism

Bài chấm tự động chạy headless với cùng seed và so output từng byte. Skill này chạy lại đúng phép thử đó trước khi bạn đẩy code.

## Khi nào dùng
- Vừa sửa `chonoi/sim/gather.py`, `chonoi/sim/quan.py`, `chonoi/scenario.py` hoặc `game.contract.json`.
- Trước khi mở PR, và trước khi gắn tag `phase-n`.
- Khi thấy hai lần chạy cho kết quả khác nhau.

## Cách chạy
```
python3 tools/check_determinism.py                      # gather, quan (600 tick) và day (2 Ngày đầy đủ), seed 1
python3 tools/check_determinism.py --mode quan --seed 7 --ticks 3600
python3 tools/check_determinism.py --inputs path/to/inputs.json
```
Windows không có `python3` thì lệnh trên vẫn chạy (script tự dùng python đang chạy nó); gõ `python tools/check_determinism.py`.

## Đọc kết quả
- `OK: ...` (thoát 0): hai lần chạy giống hệt.
- `KHÔNG TẤT ĐỊNH` (thoát 1): in chế độ và số dòng đầu tiên khác nhau. Mở hai file JSONL được in ra, so dòng đó.

## Nếu lệch, kiểm theo thứ tự
1. Có dùng `random` toàn cục hay đồng hồ hệ thống không? Chỉ được dùng `Streams` (`chonoi/rng.py`).
2. Có duyệt `dict`/`set` rồi ghi ra theo thứ tự không ổn định không? Sắp bằng `ids.sort_by_id` hoặc `sorted`.
3. Có làm tròn số thực không nhất quán không? Xem `chonoi/jsonl.py` (làm tròn 3 chữ số).
4. Id có cấp ngoài `IdAllocator` không?

Không sửa test hay bộ input cho "xanh" khi luật sai: sửa luật. Ghi kết quả chạy vào mô tả PR hoặc `docs/proof/`.
