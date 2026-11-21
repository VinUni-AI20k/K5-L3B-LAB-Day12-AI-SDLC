# Kiểm thử Lát 4 Quán và luồng TV3 + TV4

Chạy trên nhánh `phase-1-tv3-tv4-coordination` sau khi gộp Lát 3 (`78ab793`) với Lát 4, ngày 2026-11-21, Windows, Python 3.12.

Máy Windows không có lệnh `python3` mà test gọi tới, nên lúc chạy có đặt một bản sao `py.exe` tên `python3.exe` vào `PATH` (ngoài repo). Trên Linux/macOS không cần.

## Lệnh

PowerShell, từ thư mục gốc của repo:

```powershell
$env:PYTHONPATH='tests;.'; $env:PYTHONIOENCODING='utf-8'
python3 -m unittest discover -s tests -v

# 1. Gather về bến -> file kho
'{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}' | Set-Content dock.json
'{"frames":[{"tick":0,"interact":true}]}' | Set-Content dock-inputs.json
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json

# 2. Quán tự lái (kiểm bất biến từng tick, ghi inputs)
'{"items":{"ca_loc":3,"ca_linh":6,"bong_sung":4,"bong_dien_dien":2}}' | Set-Content big.json
python3 docs/proof/phase-1/tv4-e2e_quan.py serve catch.json in_serve_catch.json
python3 docs/proof/phase-1/tv4-e2e_quan.py serve big.json in_serve_big.json
python3 docs/proof/phase-1/tv4-e2e_quan.py idle catch.json in_idle.json
python3 docs/proof/phase-1/tv4-e2e_quan.py late big.json in_late.json
python3 docs/proof/phase-1/tv4-e2e_quan.py abandon big.json in_abandon.json
python3 docs/proof/phase-1/tv4-e2e_quan.py orphan big.json in_orphan.json

# 3. Phát lại inputs qua headless hộp đen, hai lần
python3 -m chonoi.headless --mode quan --seed 42 --inventory big.json --inputs in_serve_big.json --ticks 10800 --snapshot-every 600 --out a.jsonl
python3 -m chonoi.headless --mode quan --seed 42 --inventory big.json --inputs in_serve_big.json --ticks 10800 --snapshot-every 600 --out b.jsonl
```

Script tự lái đọc trạng thái sau mỗi tick, đi tới bếp hoặc bàn và bấm `interact`. Ở mọi tick, script kiểm:
1. kho vật lý và kho khả dụng không âm;
2. kho chỉ giảm đúng công thức món và chỉ khi có `cook_started`;
3. chỉ khách `waiting` giữ nguyên liệu;
4. mỗi bàn tối đa một khách;
5. món trên tay thuộc một khách còn ngồi.

## Kết quả

| Kịch bản | Kết quả | Vi phạm bất biến |
|---|---|---|
| Unittest | `Ran 36 tests ... OK` | – |
| Gather về bến | `catch.json` = `{"items":{"bong_sung":2,"ca_loc":1}}`, khớp `gather_end.inventory` | – |
| `serve` + kho từ Gather | 2 khách nấu, bưng, phục vụ, trả tiền; tiền 120, uy tín 3.4; hết nguyên liệu thì `no_dish` | 0 |
| `serve` + kho lớn | 6 khách, đủ 3 món; tiền 552, uy tín 4.2; còn dư `bong_sung` 2 | 0 |
| `idle` | 3 khách đến, 2 khách rời (mỗi lần −0.5 uy tín, còn 2.0), kho giữ nguyên | 0 |
| `late` | Khách đầu phục vụ khi kiên nhẫn < 50%: `tip` 0, uy tín không cộng; các khách sau có boa | 0 |
| `abandon` | Bếp giữ món của C1 sau khi C1 rời; C2, C3 không được nấu | 0 |
| `orphan` | **Kẹt quán** (xem dưới) | 7000 tick vi phạm bất biến 5 |
| Phát lại headless | Kho Gather: 2 `paid`, tiền 120. Kho lớn: 6 `paid`, tiền 552. Khớp script tự lái; hai lần chạy trùng từng byte | – |

## Lỗi mở: món của khách đã rời (Q7 trong `docs/clarify.md`)

Kịch bản `orphan`: bếp nhận O1 lúc C1 đang chờ, C1 hết kiên nhẫn và rời ở t3720, người chơi bưng món O1 ở t3801. Từ đó `hand` giữ món O1 đến hết ca vì bàn chỉ nhận đúng `order_id`, nên không bưng được món khác. C2 và C3 đến rồi rời; cuối ca tiền 0, uy tín 2.0.

Chưa sửa vì cả ba phương án trong Q7 đều đổi luật, cần mục F quyết định.

## Ghi chú

- Uy tín trong sim có sai số dấu phẩy động (ví dụ `3.4000000000000004`); JSONL làm tròn đúng thành `3.4`, nên không ảnh hưởng output headless.
- Tên trường `data` của sự kiện Lát 4, định dạng `hand`, ngưỡng boa và cách kết ca vẫn là giả định, chờ mục F (Q1, Q4, Q5).
