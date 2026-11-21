# Kiểm chứng P3-07 và P3-08: bàn giao kho cá thể và bật contract 1.2

Chạy ngày 2026-11-21 trên Windows (Python 3.13) với `game.contract.json` ở `contract_version` 1.2. Chỉ gọi `headless_cmd` thật (hộp đen).

## Lệnh

```
PYTHONPATH=tests:. python -m unittest discover -s tests   # 352 test, OK
python tools/smoke_phase1.py                              # 27/27 (chạy contract 1.1 sinh từ game.contract.json)
python tools/smoke_phase2.py                              # 15/15 (như trên)
python tools/smoke_phase3.py                              # 13/13, bảng dưới đây (contract 1.2 thật)
python tools/check_determinism.py                         # gather, quan, day giống từng byte (contract 1.2)
python tools/check_no_hardcode.py                         # OK
```

## Kết quả `tools/smoke_phase3.py`

```
OK   game.contract.json là 1.2 và có khối freshness 4 khóa                              
OK   bàn giao: snapshot tick 0 của quán = file kho (id, kind, fresh)                    mã 0/0, kho [{'id': 'I1', 'kind': 'ca_loc', 'fresh': 99.992}, {'id': 'I2', 'kind': 'bong_sung', 'fresh': 29.992}, {'id': 'I3', 'kind': 'bong_sung', 'fresh': 99.992}]
OK   bàn giao: id và loại giữ nguyên, độ tươi 100 và 30 chỉ hao đúng 1 tick của gather  [{'id': 'I1', 'kind': 'ca_loc', 'fresh': 99.992}, {'id': 'I2', 'kind': 'bong_sung', 'fresh': 29.992}, {'id': 'I3', 'kind': 'bong_sung', 'fresh': 99.992}]
OK   gather_end.inventory là kho cá thể đúng file                                       
OK   cá thể fresh 30 ươn ở tick đầu (xuống dưới ngưỡng), cá thể fresh 100 thì chưa      [{'id': 'I2', 'kind': 'bong_sung', 'fresh': 29.992}]
OK   bàn giao: file kho và JSONL quán giống từng byte qua 2 lần                         
OK   quan --inventory --ticks 0: fresh 100 và fresh 30 đọc đúng                         
OK   quan v1.2: file kho đếm (v1.1) bị từ chối -> mã 2, không ghi output                mã 2
OK   quan v1.2: file kho cá thể trùng id bị từ chối -> mã 2, không ghi output           mã 2
OK   quan v1.2: file kho cá thể fresh vượt 100 bị từ chối -> mã 2, không ghi output     mã 2
OK   gather v1.2: hold dạng danh sách loại (v1.1) bị từ chối -> mã 2                    mã 2
OK   ca gather đủ giờ rồi ca quán đủ giờ (v1.2): mã 0                                   
OK   day --days 2 (v1.2): days_complete, tất định từng byte                             {'type': 'end', 'ticks': 44400, 'sim_tick': 44400, 'mode': 'day', 'state': 'finished', 'reason': 'days_complete', 'money': 0, 'earned': 0, 'reputation': 3.0, 'score': 300, 'days_completed': 2}

13/13 mục đạt
```

## Ghi chú
- Cá thể độ tươi 100 và 30 sau khi cập bến ở tick 1 là 99.992 và 29.992: đúng một tick hao của gather (2 đơn vị trên 240 đơn vị mỗi điểm). Quán đọc đúng giá trị file kho ở tick 0 (không hao trước khi chạy).
- Test cũ phải đổi và lý do ghi ở `CHANGELOG.md` (mục Phase 3, thay đổi phá vỡ) và `docs/clarify.md` dòng P3-08: test hồi quy Phase 1-2 chạy headless với bản 1.1 sinh từ `game.contract.json` (`CHONOI_CONTRACT`); kiểm 1.2 ở `tests/test_p3_v12_cli.py` (24 test) và `tools/smoke_phase3.py`.
- Phá thử 8 cách ở phần nối v1.2 (runner ghi kho đếm, headless không truyền version hoặc đọc kho theo 1.1, scenario không kiểm cá thể, cho phép hai khách giữ cùng id, giữ chỗ id không có trong kho, giữ chỗ khác công thức): cả 8 bị test bắt.
- Chưa kiểm: payload sự kiện `spoiled` của gather (`id, kind, fresh`) và quán (`item_id, kind, location`) khác nhau, chờ đối chiếu Ticket-03.
